"""Isolate the seed-8 bank drop: wheat-d0 vs K-bounded NE walk.

Writes gitignored copies of experiments/_facts_v20.py with isolation
flags flipped, then runs contested vs agents/route_v20.py on seeds 0
and 8. Prints bank + the named-day counters only.

Usage:
    .venv/Scripts/python.exe experiments/_isolate_seed8.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "experiments" / "_facts_v20.py"
V20 = str(ROOT / "agents" / "route_v20.py")
SEEDS = (0, 8)

ARMS = (
    ("both", True, True),
    ("wheat_only", True, False),
    ("walk_only", False, True),
)

BASELINE = {
    "both": {0: 40806, 8: 34567},
    "funding": {0: 16628, 8: 65296},
    "pre_t1": {0: 26429, 8: 8269},
}


def write_arm(name, wheat_d0, ne_walk):
    dest = ROOT / "experiments" / f"_iso_{name}.py"
    text = SRC.read_text(encoding="utf-8")
    text = text.replace(
        "ISOLATE_WHEAT_D0 = True",
        f"ISOLATE_WHEAT_D0 = {wheat_d0}",
        1,
    )
    text = text.replace(
        "ISOLATE_NE_WALK = True",
        f"ISOLATE_NE_WALK = {ne_walk}",
        1,
    )
    dest.write_text(text, encoding="utf-8")
    return dest


def plants(act, crop):
    units = [act.get("farmer") or []] + list(act.get("hands") or [])
    return sum(1 for u in units if u and u[0] == "PLANT" and len(u) > 1 and u[1] == crop)


def buys(act, kind, product):
    total = 0
    for o in act.get("market") or []:
        if o and o[0] == kind and len(o) > 1 and o[1] == product:
            total += int(o[2]) if len(o) > 2 else 1
    return total


def land_days(act, day, seen):
    for o in act.get("market") or []:
        if o and o[0] == "BUY_LAND" and day not in seen:
            seen.append(day)


def run_one(agent_path, seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([str(agent_path), V20])

    plt_w = Counter()
    plt_s = Counter()
    buy_s = Counter()
    money_h0 = {}
    lands = []
    prev = None
    for step in env.steps:
        raw = step[0]
        obs = raw.observation
        if not isinstance(obs, dict):
            obs = dict(obs)
        act = raw.get("action") if hasattr(raw, "get") else None
        act = act or getattr(raw, "action", None) or {}
        if prev is None:
            prev = obs
            continue
        day = prev.get("day", 0)
        hour = prev.get("hour", 0)
        farm = (prev.get("farms") or [{}])[0]
        if hour == 0:
            money_h0[day] = float(farm.get("money", 0))
        plt_w[day] += plants(act, "WHEAT")
        plt_s[day] += plants(act, "STRAWBERRY")
        buy_s[day] += buys(act, "BUY_SEED", "STRAWBERRY")
        land_days(act, day, lands)
        prev = obs

    last = env.steps[-1][0]
    last_obs = last.observation
    if not isinstance(last_obs, dict):
        last_obs = dict(last_obs)
    bank = float((last_obs.get("farms") or [{}])[0].get("money", 0))
    return {
        "bank": bank,
        "wheat_d0": plt_w[0],
        "straw": [plt_s[d] for d in range(5, 9)],
        "buy_s_d5": buy_s[5],
        "land": lands,
        "money": {d: money_h0.get(d, 0) for d in (0, 5, 6)},
    }


def main():
    print("arm         seed     bank   d0W  S5-8          buyS5  land     $d0   $d5   $d6")
    print("-" * 88)
    for name, wheat, walk in ARMS:
        path = write_arm(name, wheat, walk)
        for seed in SEEDS:
            r = run_one(path, seed)
            straw = "/".join(str(x) for x in r["straw"])
            land = ",".join(str(x) for x in r["land"]) or "-"
            print(
                f"{name:<11} {seed:4d} {r['bank']:8.0f}  {r['wheat_d0']:3d}  "
                f"{straw:<13} {r['buy_s_d5']:5d}  {land:<7} "
                f"{r['money'][0]:5.0f} {r['money'][5]:5.0f} {r['money'][6]:5.0f}"
            )
            sys.stdout.flush()
        path.unlink(missing_ok=True)
    print()
    print("baselines: both 40806/34567  funding 16628/65296  pre-T1 26429/8269")
    print("tape: wheat d0=7  STRAW d5-8 = 4/8/4/4")


if __name__ == "__main__":
    main()
