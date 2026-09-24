"""T4: copyability analysis for today's top-10 teams.

Reads downloaded replays in experiments/endgame/rep/<episode>.json, extracts
each team's own seat's action tape (canonical form), computes pairwise
agreement within same-key episode groups over windows 0-71 / 72-143 /
144-400 / 400-718, and compares the opening (0-71) against our own
router_yuan_nf_trim opening tape.

clade.py (referenced by experiments/tapes/harvest_lineage.py) does not exist
in this repo/checkout, so canon()/norm_action() are reimplemented here,
matching the inline `c()` helper in experiments/tapes/make_whole.py
(json.dumps(action, sort_keys=True, separators=(",", ":"))).
"""
import json
import os

S = os.path.dirname(os.path.abspath(__file__))
REP = os.path.join(S, "rep")
PANEL = os.path.join(S, "panel")


def norm_action(a):
    return a if a is not None else {"farmer": [], "hands": [], "market": []}


def canon(a):
    return json.dumps(norm_action(a), sort_keys=True, separators=(",", ":"))


def load_replay(episode_id):
    p = os.path.join(REP, f"{episode_id}.json")
    rep = json.load(open(p, encoding="utf-8"))
    if isinstance(rep.get("replay"), str):
        rep = json.loads(rep["replay"])
    elif isinstance(rep.get("replay"), dict):
        rep = rep["replay"]
    return rep


def find_seat(rep, team_name):
    """Seat index (0/1) whose info.TeamNames matches team_name, else None."""
    names = (rep.get("info", {}) or {}).get("TeamNames") or []
    for i, n in enumerate(names):
        if n == team_name:
            return i
    return None


def shop_key(rep, step):
    obs = (rep["steps"][step][0].get("observation") or {})
    return (obs.get("town") or {}).get("unlocked_shops") or []


def extract_tape(rep, seat):
    steps = rep["steps"]
    return [canon(steps[i][seat].get("action")) for i in range(1, len(steps))]


def agreement(a, b, lo, hi):
    hi = min(hi, len(a), len(b))
    if hi <= lo:
        return None
    return sum(1 for i in range(lo, hi) if a[i] == b[i]) / (hi - lo)


def key72(rep):
    s = shop_key(rep, 72)
    return s[0] if s else ""


def key144(rep):
    s = shop_key(rep, 144)
    return "__".join(s[:2]) if len(s) >= 2 else (s[0] if s else "")
