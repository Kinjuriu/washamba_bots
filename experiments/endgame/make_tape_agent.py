"""Write a fixed-tape agent file from a recorded action list.

The output is the `agents/router_surge.py` shape: a zlib+base85 blob of the
720-entry tape plus a tiny replayer that indexes it by `day*24 + hour` and
pads/truncates the `hands` list to the hand count the engine actually reports
this step. Nothing observation-driven - the recorded schedule is the whole
agent. That is exactly what a replay harness needs: seat the opponent's
recorded tape, and the only free variable left is our own agent.

Actions are embedded *verbatim*. No canonicalisation: market orders settle in
list-index lockstep (`_process_market`), so sorting or de-duplicating them
would change the episode. The only normalisation is `None -> PASS`.
"""

from __future__ import annotations

import base64
import json
import os
import zlib

TEMPLATE = '''# {name} - generated fixed-tape agent (experiments/endgame/make_tape_agent.py).
{header}
import base64, copy, json, zlib

_TAPE_DATA = "{blob}"
_TAPE = json.loads(zlib.decompress(base64.b85decode(_TAPE_DATA)).decode("utf-8"))


def _get(v, k, d=None):
    if isinstance(v, dict):
        return v.get(k, d)
    g = getattr(v, "get", None)
    return g(k, d) if callable(g) else getattr(v, k, d)


def _pass(obs):
    try:
        farms = list(_get(obs, "farms", []) or [])
        p = int(_get(obs, "player", 0) or 0)
        n = len(_get(farms[p], "hands", []) or []) if p < len(farms) else 0
    except Exception:
        n = 0
    return {{"farmer": ["PASS"], "hands": [["PASS"] for _ in range(n)], "market": []}}


def agent(observation, configuration=None):
    del configuration
    try:
        step = int(_get(observation, "day", 0) or 0) * 24 + int(_get(observation, "hour", 0) or 0)
        step = min(max(step, 0), len(_TAPE) - 1)
        action = copy.deepcopy(_TAPE[step] or {{}})
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
        return _pass(observation)
'''


def normalise(action):
    """`None` -> an explicit PASS. Everything else is left byte-identical."""
    if not isinstance(action, dict):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    out = dict(action)
    out.setdefault("farmer", ["PASS"])
    out["hands"] = list(out.get("hands") or [])
    out["market"] = list(out.get("market") or [])
    return out


def encode(tape: list) -> str:
    raw = json.dumps([normalise(a) for a in tape], separators=(",", ":")).encode("utf-8")
    return base64.b85encode(zlib.compress(raw, 9)).decode("ascii")


def write(tape: list, out_path: str, header: str = "") -> None:
    """Write a replayer for `tape` to `out_path`. `header` is comment text."""
    lines = [("# " + ln).rstrip() for ln in (header or "").splitlines()]
    body = ("\n".join(lines) + "\n") if lines else ""
    src = TEMPLATE.format(
        name=os.path.basename(out_path),
        header=body,
        blob=encode(tape),
    )
    d = os.path.dirname(os.path.abspath(out_path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(src)
