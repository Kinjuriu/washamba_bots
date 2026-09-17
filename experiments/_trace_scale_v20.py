"""Measure v20 owned-by-day + land_days for scale fact card B.

Usage:
    .venv/Scripts/python.exe experiments/_trace_scale_v20.py
    .venv/Scripts/python.exe experiments/_trace_scale_v20.py 0 8
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
V20 = str(ROOT / "experiments" / ".v20_agent.py")
if not os.path.exists(V20):
    V20 = str(ROOT / "agents" / "route_v20.py")

ANIMAL_KINDS = {"COOP", "PASTURE", "BARN", "STABLE"}
WATCH_DAYS = {0, 3, 5, 7, 8, 9, 11, 12, 14, 18, 24, 29}


def board_animals(farm):
    pens = herd = 0
    mix = Counter()
    shed_wait = 0  # filled pens only counted below
    for row in farm.get("tiles") or []:
        for t in row:
            if not isinstance(t, dict):
                continue
            if t.get("kind") in ANIMAL_KINDS:
                pens += 1
                if t.get("animal"):
                    herd += 1
                    mix[t["animal"]] += 1
    return pens, herd, mix


def measure(seed: int):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([V20, "starter"])
    steps = env.steps
    land_days = []
    buy_by_day = Counter()
    eod = {}
    prev = None
    for step in steps:
        obs0 = step[0].observation
        src = prev if prev is not None else obs0
        day = src.get("day", 0)
        hour = src.get("hour", 0)
        # actions that produced this observation came from prev turn
        if prev is not None:
            act = step[0].get("action") or {}
            if not act and hasattr(step[0], "action"):
                act = step[0].action or {}
            # framework: actions are on the step that submitted them
        farm = obs0["farms"][0]
        unlocked = list(farm.get("unlocked_quadrants") or [])
        pens, herd, mix = board_animals(farm)
        if hour == 23 and day in WATCH_DAYS:
            eod[day] = {
                "money": farm.get("money", 0),
                "pens": pens,
                "herd": herd,
                "mix": dict(mix),
                "unlocked": unlocked,
                "n_quad": len(unlocked),
            }
        prev = obs0

    # Rescan with action logs from env.info / step actions
    land_days = []
    buy_animals = []
    prev = None
    for i, step in enumerate(steps):
        obs0 = step[0].observation
        src = prev if prev is not None else obs0
        day = src.get("day", 0)
        hour = src.get("hour", 0)
        # actions that led INTO this step are stored on this step
        action = None
        try:
            action = step[0]["action"]
        except Exception:
            action = getattr(step[0], "action", None)
        if action and i > 0:
            for order in action.get("market") or []:
                if not order:
                    continue
                op = order[0]
                if op == "BUY_LAND":
                    land_days.append((day, hour, len(obs0["farms"][0].get("unlocked_quadrants") or [])))
                elif op == "BUY_ANIMAL":
                    sp = order[1] if len(order) > 1 else "?"
                    qty = order[2] if len(order) > 2 else 1
                    buy_animals.append((day, hour, sp, qty))
                    buy_by_day[day] += qty
        prev = obs0

    bank = steps[-1][0].reward
    print(f"=== v20 vs starter seed={seed} bank={bank} ===")
    print(f"  land_days (engine day,hour,unlocked_after): {land_days}")
    print(f"  BUY_ANIMAL qty by day: {dict(sorted(buy_by_day.items()))}")
    cum = 0
    for d in sorted(buy_by_day):
        cum += buy_by_day[d]
        print(f"    d{d}: +{buy_by_day[d]} (cum {cum})")
    print("  EOD snapshots:")
    for d in sorted(eod):
        r = eod[d]
        print(
            f"    d{d}: herd={r['herd']} pens={r['pens']} mix={r['mix']} "
            f"quad={r['n_quad']}{r['unlocked']} money={r['money']:.0f}"
        )
    return {
        "seed": seed,
        "bank": bank,
        "land_days": land_days,
        "buy_by_day": dict(buy_by_day),
        "eod": eod,
    }


def main():
    seeds = [int(x) for x in sys.argv[1:]] or [0, 8]
    for s in seeds:
        measure(s)


if __name__ == "__main__":
    main()
