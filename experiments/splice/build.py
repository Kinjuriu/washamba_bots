"""experiments/splice/build.py [--base agents/w3_herdsafe2700.py] [--output agents/washamba_splice_v1.py]

Produces the single-file submission agents/washamba_splice_v1.py per
docs/ENDGAME/splice_build.md ("Shape"):

    <base agent, byte-verbatim>
    _WB_BASE = <base's own last-callable entrypoint>
    <price_model.py, package imports stripped>
    <sell_engine.py, package imports stripped>
    <controller.py, package imports stripped>
    def washamba_agent(obs, config=None): ...   # base for step < 192, controller after
    agent = washamba_agent                       # must stay the last callable binding

Deviation from the contract's literal pseudocode, verified necessary and
confirmed independently by Builder B and the coordinator: the contract shows
`_WB_BASE = agent`, but in agents/w3_herdsafe2700.py the name `agent` is
reassigned six times to intermediate wrapper layers, and the real entrypoint
(`herdsafe_forecast_agent`) is defined after the last of those and never
reassigned to `agent`. Reading `agent` directly would silently capture the
wrong function -- exactly the CLAUDE.md "Agent I/O contract" gotcha,
reproduced inside our own base file. So this build instead emits, immediately
after the base text and before any WB_ code:

    _WB_BASE = [v for v in list(globals().values()) if callable(v)][-1]

which is kaggle_environments' own rule (agent.py:64) applied to "everything
defined so far" -- i.e. exactly the base's real entrypoint, whatever it is
named, for whichever base file is passed in.

Similarly, `agent = washamba_agent` at the very end is NOT what makes
washamba_agent the winning entrypoint -- `agent` already exists as a key in
the namespace (from the base file's own code), so reassigning it does not
move its position in iteration order. What actually wins is that
`washamba_agent` is a NEW name, inserted after everything else, with nothing
callable defined after it; `agent = washamba_agent` is kept only because the
contract asks for it and because it is harmless (a plain reassignment of an
existing key touches no ordering). This is why every helper this build emits
(`_wb_call`, `_wb_safe_action`) is placed BEFORE `def washamba_agent`, never
after.

Until price_model.py / sell_engine.py / controller.py all exist, the build
still succeeds: whichever of the three are missing are simply left out, the
controller is never constructed, and the generated `washamba_agent` plays the
base agent for the whole game (one warning, first call) -- so this pipeline
can be proven, and re-proven on every commit, before Builder A/B are done.

After writing the file, runs three checks and exits non-zero if any fail:
    1. seed-0 self-play: ['DONE', 'DONE'], no reward == 3000.
    2. the module's actual last callable (found the same way
       kaggle_environments finds it: compile + exec into a fresh namespace)
       is named 'washamba_agent'.
    3. max per-turn duration across that same full episode, both seats,
       INCLUDING the first call (which pays for compiling/exec'ing the whole
       file) -- read from env.logs[i][seat]['duration'], which is exactly the
       number kaggle_environments/agent.py:207 measures for actTimeout
       accounting. Limit 1000 ms (actTimeout); flagged (not failed) above 500.

Usage:
    .venv/Scripts/python.exe experiments/splice/build.py
    .venv/Scripts/python.exe experiments/splice/build.py --base agents/w0_v15stack_control.py
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(THIS_DIR))
AGENTS_DIR = os.path.join(REPO_ROOT, "agents")
DEFAULT_BASE = os.path.join(AGENTS_DIR, "w3_herdsafe2700.py")
DEFAULT_OUTPUT = os.path.join(AGENTS_DIR, "washamba_splice_v1.py")

# Must match dev_agent.py's WB_HANDOVER_STEP (duplicated, not imported --
# see gate.py for why: each of these files should be gateable/buildable even
# when the others are broken).
WB_HANDOVER_STEP = 192

SPLICE_MODULES = ["price_model.py", "sell_engine.py", "controller.py"]

# Cross-splice imports that only matter for standalone-importing/testing a
# module before the build exists (e.g. Builder A's sell_engine.py:
# `from price_model import WB_PriceModel  # noqa: F401  (dropped by build.py)`).
# Once concatenated, the names they'd import are already defined earlier in
# the same file. Not a blanket import-stripper: price_model.py's own
# `import math as _wb_math` (stdlib) must survive.
_STRIP_IMPORT_RE = re.compile(r"^\s*(from|import)\s+(price_model|sell_engine|controller)\b")


def _git_hash():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    except Exception:
        return "unknown (git rev-parse failed)"


def _git_branch():
    try:
        return subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO_ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _extract_header_lines(base_text):
    """The base file's leading '#'-comment block naming its own origin and
    licence, stopping before an embedded full licence text if the header
    continues into one (e.g. a pasted Apache-2.0 grant). The full text, if
    present, does not need a second copy here -- the base is embedded
    byte-verbatim a few lines below regardless, so nothing is lost, only not
    duplicated in this identifying header."""
    header = []
    for line in base_text.splitlines():
        if not line.startswith("#"):
            break
        if re.search(r"Apache License|TERMS AND CONDITIONS", line, re.IGNORECASE):
            break
        header.append(line)
    return header


def _strip_cross_splice_imports(text):
    kept, dropped = [], []
    for line in text.splitlines():
        if _STRIP_IMPORT_RE.match(line):
            dropped.append(line)
        else:
            kept.append(line)
    return "\n".join(kept) + "\n", dropped


def _dispatcher_source(all_three):
    lines = [
        "",
        "# ---- washamba splice: dispatcher (experiments/splice/build.py) ----",
        f"WB_HANDOVER_STEP = {WB_HANDOVER_STEP}",
        "_WB_CONTROLLER = None",
        "_WB_CONTROLLER_ERROR = None",
    ]
    if all_three:
        lines += [
            "try:",
            "    _wb_pm = WB_PriceModel()",
            "    _wb_se = WB_SellEngine(_wb_pm)",
            "    _WB_CONTROLLER = WB_Controller(_wb_pm, _wb_se)",
            "except Exception as _wb_construct_exc:",
            "    _WB_CONTROLLER_ERROR = _wb_construct_exc",
        ]
    else:
        lines += [
            "# price_model.py / sell_engine.py / controller.py were not all present at build",
            "# time -- _WB_CONTROLLER stays None and washamba_agent plays the base for the",
            "# whole game (one warning), so the rest of this pipeline stays provable.",
        ]
    lines += [
        "",
        "_WB_WARNED_MISSING = False",
        "",
        "",
        "def _wb_call(fn, obs, config):",
        '    """fn(obs) or fn(obs, config), matching whatever arity the base declares --',
        "    the same truncation kaggle_environments itself applies (agent.py: args =",
        "    [observation, configuration][: agent.__code__.co_argcount]).\"\"\"",
        "    args = [obs, config]",
        '    if hasattr(fn, "__code__") and hasattr(fn.__code__, "co_argcount"):',
        "        args = args[: fn.__code__.co_argcount]",
        "    return fn(*args)",
        "",
        "",
        "def _wb_safe_action(obs):",
        '    """Per-turn safety net for a controller that raised at runtime, post-handover.',
        "    Waters/feeds whatever the unit is standing on and is due for, else PASS. No",
        "    market orders, no movement. NEVER the base agent here -- its own schedule is",
        '    out of sync with reality once the controller has been acting."""',
        '    farm = obs["farms"][obs["player"]]',
        '    tiles = farm["tiles"]',
        "",
        "    def _wb_act_for(pos):",
        "        x, y = pos",
        "        tile = tiles[y][x]",
        "        if isinstance(tile, dict):",
        '            if tile.get("kind") == "PLANT" and not tile.get("watered_today"):',
        '                return ["WATER"]',
        '            if "animal" in tile and not tile.get("fed_today"):',
        '                return ["FEED"]',
        '        return ["PASS"]',
        "",
        '    return {"farmer": _wb_act_for(farm["farmer"]),',
        '            "hands": [_wb_act_for(h) for h in farm["hands"]],',
        '            "market": []}',
        "",
        "",
        "def washamba_agent(obs, config=None):",
        "    global _WB_WARNED_MISSING",
        "    if _WB_CONTROLLER is None:",
        "        if not _WB_WARNED_MISSING:",
        '            print(f"washamba_splice_v1: controller not available '
        '({_WB_CONTROLLER_ERROR!r}); playing the base agent for the whole game")',
        "            _WB_WARNED_MISSING = True",
        "        return _wb_call(_WB_BASE, obs, config)",
        '    if obs["step"] < WB_HANDOVER_STEP:',
        "        return _wb_call(_WB_BASE, obs, config)",
        "    try:",
        "        return _WB_CONTROLLER.act(obs)",
        "    except Exception as _wb_runtime_exc:",
        '        print(f"washamba_splice_v1: WB_Controller.act raised at step '
        '{obs.get(\'step\')} ({_wb_runtime_exc!r}); using the safe action this turn")',
        "        return _wb_safe_action(obs)",
        "",
        "",
        "# The framework picks the LAST CALLABLE in this module's namespace, not a function",
        "# named `agent` (kaggle_environments/agent.py:64; CLAUDE.md \"Agent I/O contract\").",
        "# `washamba_agent` above -- a NEW name, nothing callable defined after it -- is what",
        "# actually wins; `agent` already existed as a key from the base file's own code, so",
        "# rebinding it below does not change the namespace's iteration order. Kept for the",
        "# contract's sake and because it is harmless. Keep this binding last regardless.",
        "agent = washamba_agent",
        "",
    ]
    return "\n".join(lines)


def build(base_path, output_path):
    with open(base_path, "rb") as f:
        base_bytes = f.read()
    base_text_for_header = base_bytes.decode("utf-8", errors="replace")
    header_lines = _extract_header_lines(base_text_for_header)

    present = {}
    for mod in SPLICE_MODULES:
        p = os.path.join(THIS_DIR, mod)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                text = f.read()
            stripped, dropped = _strip_cross_splice_imports(text)
            present[mod] = stripped
            if dropped:
                print(f"build.py: stripped from {mod}: {dropped}")
        else:
            print(f"build.py: {mod} not present yet.")
    all_three = all(m in present for m in SPLICE_MODULES)

    git_hash, git_branch = _git_hash(), _git_branch()
    build_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    header = [
        f"# agents/{os.path.basename(output_path)} -- GENERATED by experiments/splice/build.py. DO NOT EDIT BY HAND.",
        "# Regenerate: .venv/Scripts/python.exe experiments/splice/build.py",
        '# Contract: docs/ENDGAME/splice_build.md ("Shape").',
        f"# Built from git {git_hash} (branch {git_branch}) at {build_time}.",
        f"# Base agent origin and licence, copied verbatim from {os.path.relpath(base_path, REPO_ROOT)}'s own header:",
    ]
    header += header_lines
    header.append("#")
    status_line = ("controller wired (price_model + sell_engine + controller all present at build time)"
                   if all_three else
                   "PLUMBING ONLY -- one or more of price_model.py/sell_engine.py/controller.py missing; "
                   "dispatcher falls back to the base agent for the whole game.")
    header.append(f"# Splice status at build time: {status_line}")
    header.append("")
    header_text = "\n".join(header) + "\n"

    glue_pre = "\n".join([
        "",
        "# ---- washamba splice: base entrypoint capture (experiments/splice/build.py) ----",
        "# The LAST CALLABLE bound above this line, exactly kaggle_environments' own rule",
        "# (kaggle_environments/agent.py:64) -- NOT a name literally called `agent`, which the",
        "# base file above may reassign several times to intermediate wrapper layers before",
        '# its real entrypoint (see CLAUDE.md "Agent I/O contract", and this file\'s own',
        "# module docstring for why agents/w3_herdsafe2700.py specifically needs this).",
        "_WB_BASE = [_wb_v for _wb_v in list(globals().values()) if callable(_wb_v)][-1]",
        "",
    ]) + "\n"

    chunks = [header_text.encode("utf-8")]
    chunks.append(base_bytes if base_bytes.endswith(b"\n") else base_bytes + b"\n")
    chunks.append(glue_pre.encode("utf-8"))
    for mod in SPLICE_MODULES:
        if mod in present:
            chunks.append(f"\n# ---- washamba splice: {mod} (package imports stripped by build.py) ----\n".encode("utf-8"))
            chunks.append(present[mod].encode("utf-8"))
    chunks.append(("\n" + _dispatcher_source(all_three)).encode("utf-8"))

    output_bytes = b"".join(chunks)
    with open(output_path, "wb") as f:
        f.write(output_bytes)

    return output_path, all_three


def _check_last_callable_is(path, expected_name):
    with open(path, "rb") as f:
        source = f.read().decode("utf-8")
    code = compile(source, path, "exec")
    ns = {}
    exec(code, ns)
    callables = [v for v in ns.values() if callable(v)]
    if not callables:
        return False, "(no callable found)"
    name = getattr(callables[-1], "__name__", repr(callables[-1]))
    return name == expected_name, name


def _validate(output_path):
    ok = True

    name_ok, name = _check_last_callable_is(output_path, "washamba_agent")
    print(f"check: last callable is 'washamba_agent'      -> {'PASS' if name_ok else 'FAIL'} (found: {name})")
    ok = ok and name_ok

    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 0}, debug=False)
    env.run([output_path, output_path])
    final = env.steps[-1]
    statuses = [s.status for s in final]
    rewards = [s.reward for s in final]
    done_ok = statuses == ["DONE", "DONE"]
    inert_ok = 3000 not in rewards
    print(f"check: seed-0 self-play status                 -> {'PASS' if done_ok else 'FAIL'} ({statuses})")
    print(f"check: seed-0 self-play reward != 3000          -> {'PASS' if inert_ok else 'FAIL'} ({rewards})")
    ok = ok and done_ok and inert_ok

    durations = [entry.get("duration", 0.0) for step_logs in env.logs for entry in (step_logs or []) if entry]
    max_ms = max(durations) * 1000 if durations else 0.0
    timing_ok = max_ms <= 1000.0
    flag = "  FLAG (> 500 ms)" if max_ms > 500.0 else ""
    print(f"check: max per-turn time, full episode, both    -> {'PASS' if timing_ok else 'FAIL'} "
          f"({max_ms:.1f} ms, limit 1000 ms){flag}")
    ok = ok and timing_ok

    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=DEFAULT_BASE,
                     help="base agent file, byte-verbatim (default: agents/w3_herdsafe2700.py; "
                          "see experiments/splice/base_choice.md)")
    ap.add_argument("--output", default=DEFAULT_OUTPUT)
    args = ap.parse_args()

    base_path = os.path.abspath(args.base)
    output_path = os.path.abspath(args.output)
    if not os.path.exists(base_path):
        sys.exit(f"build.py: base agent not found: {base_path}")

    output_path, all_three = build(base_path, output_path)
    size_kb = os.path.getsize(output_path) / 1024.0
    print(f"built {os.path.relpath(output_path, REPO_ROOT)} ({size_kb:.0f} KB) "
          f"from base {os.path.relpath(base_path, REPO_ROOT)}")
    print(f"controller wired: {all_three}\n")

    ok = _validate(output_path)
    print("\nBUILD " + ("OK" if ok else "FAILED VALIDATION -- see checks above"))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
