"""experiments/splice/dev_agent.py -- local dev/test rig for the splice build.

Contract: docs/ENDGAME/splice_build.md ("Shape"). NOT the submission -- that is
the single concatenated file `experiments/splice/build.py` produces at
agents/washamba_splice_v1.py. This file exists so Builder A's price_model.py /
sell_engine.py and Builder B's controller.py have something runnable in
`env.run([...])` before that build exists, and so the plumbing (base load,
handover, controller construction, per-turn safety net) can be gated on its
own, independent of the three modules' own progress.

Dispatch:
  obs["step"] <  WB_HANDOVER_STEP (192, day 8 hour 0) -> the base agent, untouched.
  obs["step"] >= WB_HANDOVER_STEP                     -> WB_Controller.act(obs).

Two distinct fallbacks, matching splice_build.md:
  - price_model.py / sell_engine.py / controller.py not importable yet (or
    WB_Controller() cannot be constructed): play the BASE AGENT FOR THE WHOLE
    GAME and print exactly one warning. This is the "test the plumbing now"
    mode the harness needs before the builders land -- there is no handover to
    honor yet because nothing has taken over.
  - WB_Controller.act(obs) raises at runtime, post-handover: fall back that
    turn only to a minimal safe action (water/feed whatever is due on the
    tile the unit is standing on, else PASS; no market orders, no movement).
    NEVER the base agent's own tape here -- per the Shape note, the base's
    internal schedule is out of sync with reality once the controller has
    been acting, so replaying it would be worse than doing nothing.

Usage:
    .venv/Scripts/python.exe -c "
    from kaggle_environments import make
    env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 0})
    env.run(['experiments/splice/dev_agent.py', 'experiments/splice/dev_agent.py'])
    print([s.status for s in env.steps[-1]], [s.reward for s in env.steps[-1]])
    "
Works the same run as an absolute path, from any cwd, or `python -m
experiments.splice.dev_agent` style import -- see _wb_this_dir() below.
"""
import importlib.util
import os
import sys

WB_HANDOVER_STEP = 192
WB_BASE_RELPATH = os.path.join("agents", "w3_herdsafe2700.py")


def _wb_this_dir():
    """This file's own directory, without relying on `__file__`.

    kaggle_environments loads a file-path agent by reading its source and
    exec'ing it against a **fresh, empty globals dict**
    (kaggle_environments/agent.py, get_last_callable: `env = {}; ...;
    exec(code_object, env)`) -- `__file__` is never injected, so referencing
    it raises NameError there (verified locally: a probe script run through
    `env.run([...])` has no `__file__`, only `__builtins__`). That same
    function gives us two things instead:
      - `compile(raw, path_str, "exec")` compiles with our path as the code
        object's filename, so this frame's `co_filename` is it.
      - it appends `os.path.dirname(path)` to `sys.path` for the duration of
        the exec call, so `sys.path[-1]` is our own directory while our
        top-level code (this call included) is running.
    `__file__` is tried first so this also works under a normal import
    (unit tests, `python -m experiments.splice.dev_agent`, etc).
    """
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        pass
    co_filename = sys._getframe().f_code.co_filename
    if co_filename and co_filename != "<string>" and os.path.exists(os.path.abspath(co_filename)):
        return os.path.dirname(os.path.abspath(co_filename))
    return os.path.abspath(sys.path[-1])


_WB_SPLICE_DIR = _wb_this_dir()
_WB_REPO_ROOT = os.path.dirname(os.path.dirname(_WB_SPLICE_DIR))
for _wb_p in (_WB_REPO_ROOT, _WB_SPLICE_DIR):
    if _wb_p not in sys.path:
        sys.path.insert(0, _wb_p)


def _wb_load_base_agent(path):
    """Load the base agent file in its OWN module namespace (importlib from
    path, never `exec`'d into ours), so none of its globals can collide with
    anything here -- then take the LAST CALLABLE bound in that namespace,
    exactly kaggle_environments' own rule (agent.py:64:
    `[v for v in env.values() if callable(v)][-1]`) -- NOT a name literally
    called `agent`.

    This is not hypothetical for our base: in agents/w3_herdsafe2700.py the
    name `agent` is bound six separate times to progressively-wrapped
    intermediate layers, and the real entrypoint, `herdsafe_forecast_agent`,
    is defined after the last of those and never reassigned to `agent`.
    Reading `module.agent` here would silently run the wrong function -- the
    exact CLAUDE.md "Agent I/O contract" gotcha, reproduced inside our own
    base file (confirmed independently by Builder B and the coordinator).
    """
    spec = importlib.util.spec_from_file_location("_wb_base_module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    callables = [v for v in vars(module).values() if callable(v)]
    if not callables:
        raise RuntimeError(f"washamba dev_agent: no callable found in base agent {path!r}")
    return callables[-1]


def _wb_call(fn, obs, config):
    """Call fn(obs) or fn(obs, config), matching whatever arity it declares --
    the identical truncation kaggle_environments itself applies
    (kaggle_environments/agent.py: `args = [observation, configuration];
    if hasattr(agent, "__code__") ...: args = args[: agent.__code__.co_argcount]`).
    Bases in this repo use both `def agent(obs)` and `def agent(obs, config=None)`."""
    args = [obs, config]
    if hasattr(fn, "__code__") and hasattr(fn.__code__, "co_argcount"):
        args = args[: fn.__code__.co_argcount]
    return fn(*args)


_WB_BASE = _wb_load_base_agent(os.path.join(_WB_REPO_ROOT, WB_BASE_RELPATH))

_WB_CONTROLLER = None
_WB_CONTROLLER_ERROR = None
try:
    # Bare, top-level module names -- NOT `experiments.splice.*`. price_model.py
    # / sell_engine.py / controller.py import each other the same bare way
    # (e.g. `from price_model import ...`), matching how build.py will later
    # concatenate all three into one flat file with no package at all
    # (splice_build.md "Shape"). Importing them here under the dotted package
    # path as well as bare would create two distinct copies of the same
    # classes (dotted vs. bare each get their own entry in sys.modules), which
    # risks isinstance/identity mismatches between the instances this file
    # constructs and the classes controller.py itself references. Resolved
    # via _WB_SPLICE_DIR having been put on sys.path above; the bare imports
    # from inside sell_engine.py/controller.py resolve the same way, so
    # everyone shares one copy of each module within a single process.
    import price_model as _wb_price_model_mod
    import sell_engine as _wb_sell_engine_mod
    import controller as _wb_controller_mod

    _wb_pm = _wb_price_model_mod.WB_PriceModel()
    _wb_se = _wb_sell_engine_mod.WB_SellEngine(_wb_pm)
    _WB_CONTROLLER = _wb_controller_mod.WB_Controller(_wb_pm, _wb_se)
except Exception as _wb_exc:  # ImportError before the builders land; anything else after
    _WB_CONTROLLER_ERROR = _wb_exc

_WB_WARNED_MISSING = False


def _wb_safe_action(obs):
    """Minimal per-turn safety net for a controller that raised at runtime,
    post-handover. Waters or feeds whatever the farmer/each hand is standing
    on and is due for, else PASS. No market orders, no movement -- the
    smallest action that cannot make anything worse. NEVER the base agent's
    tape here (see module docstring)."""
    farm = obs["farms"][obs["player"]]
    tiles = farm["tiles"]

    def act_for(pos):
        x, y = pos
        tile = tiles[y][x]
        if isinstance(tile, dict):
            if tile.get("kind") == "PLANT" and not tile.get("watered_today"):
                return ["WATER"]
            if "animal" in tile and not tile.get("fed_today"):
                return ["FEED"]
        return ["PASS"]

    farmer_action = act_for(farm["farmer"])
    hand_actions = [act_for(h) for h in farm["hands"]]
    return {"farmer": farmer_action, "hands": hand_actions, "market": []}


def washamba_dev_agent(obs, config=None):
    global _WB_WARNED_MISSING
    if _WB_CONTROLLER is None:
        if not _WB_WARNED_MISSING:
            print(
                f"WB dev_agent: splice controller not importable yet ({_WB_CONTROLLER_ERROR!r}); "
                f"playing the base agent for the whole game so the plumbing can still be tested",
                file=sys.stderr,
            )
            _WB_WARNED_MISSING = True
        return _wb_call(_WB_BASE, obs, config)

    if obs["step"] < WB_HANDOVER_STEP:
        return _wb_call(_WB_BASE, obs, config)

    try:
        return _WB_CONTROLLER.act(obs)
    except Exception as exc:
        print(
            f"WB dev_agent: WB_Controller.act raised at step {obs.get('step')} ({exc!r}); "
            f"using the safe action this turn",
            file=sys.stderr,
        )
        return _wb_safe_action(obs)


# The framework picks the LAST CALLABLE in this module's namespace, not a
# function named `agent` (kaggle_environments/agent.py:64; CLAUDE.md "Agent
# I/O contract"). Keep this binding last.
agent = washamba_dev_agent
