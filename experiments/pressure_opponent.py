"""A front-running pressure opponent for the animal-buy starvation harness.

Neither a captured real ladder-loss tape (agents/router_surge.py) nor a
tuned, real-farming aggressive main.py opponent (experiments/aggressive_
opponent.py) could push agents/router_yuan_nf_trim.py's scheduled
BUY_ANIMAL orders into a *sustained* cash trough (see
experiments/animal_buy_starvation_harness.py + docs/MARGIN_LEVERS.md for
both harnesses and their results: individual buy-events do genuinely fail
against both, confirmed via before/after shed counts, but a later
redundant scheduled buy always fills the same pasture slot before day 10).

This is the harness's third and most surgical attempt (task option 1b):
play OUR OWN agent's recorded tape, SHIFTED a few steps EARLY. Since the
tape is deterministic and keyed only on step/unlocked_shops (both visible
to any agent watching the shared `obs`), this opponent knows in advance
exactly which SELL/BUY orders router_yuan_nf_trim.py is about to place and
fires the identical orders a few steps sooner - directly front-running our
own sells (depressing the price we'll sell into) and our own buys
(inflating the price we'll buy into), concentrated on exactly the products
our schedule depends on, rather than a generic "sell everything" opponent.

Usage (as a harness opponent):
    .venv/Scripts/python.exe experiments/animal_buy_starvation_harness.py \\
        agents/router_yuan_nf_trim.py experiments/pressure_opponent.py 12
"""

import copy
import importlib.util

# No `__file__` here: kaggle_environments loads a file-path agent by exec()'ing
# its source in a bare namespace (kaggle_environments/agent.py's
# get_last_callable), so `__file__` is undefined. Assume the repo root as cwd
# instead, same as every other experiments/ script's relative paths.
_SPEC = importlib.util.spec_from_file_location(
    "_pressure_base", "agents/router_yuan_nf_trim.py"
)
_BASE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_BASE)

SHIFT = 3  # steps to front-run our own tape by


def _get(v, k, d=None):
    if isinstance(v, dict):
        return v.get(k, d)
    g = getattr(v, "get", None)
    return g(k, d) if callable(g) else getattr(v, k, d)


def agent(observation, configuration=None):
    del configuration
    try:
        step = int(_get(observation, "day", 0) or 0) * 24 + int(_get(observation, "hour", 0) or 0)
        shifted = min(max(step + SHIFT, 0), 719)
        shops = list(_get(_get(observation, "town", {}) or {}, "unlocked_shops", []) or [])
        tape_name = _BASE._which(shifted, shops)
        tape = _BASE._TAPES[tape_name]
        action = copy.deepcopy(tape[min(shifted, len(tape) - 1)] or {})

        farms = list(_get(observation, "farms", []) or [])
        p = int(_get(observation, "player", 0) or 0)
        expected = len(_get(farms[p], "hands", []) or []) if p < len(farms) else 0
        hands = list(action.get("hands") or [])
        hands.extend([["PASS"] for _ in range(max(0, expected - len(hands)))])
        action["hands"] = hands[:expected]
        action.setdefault("farmer", ["PASS"])
        action.setdefault("market", [])
        return action
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}
