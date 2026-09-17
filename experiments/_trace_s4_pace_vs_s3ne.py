"""Compare S4 lead vs S3ne on seeds 0 and 8: bank, herd, pens, milk.

Usage:
    .venv/Scripts/python.exe experiments/_trace_s4_pace_vs_s3ne.py
    .venv/Scripts/python.exe experiments/_trace_s4_pace_vs_s3ne.py 0 8
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import V20, _obs, analyze_episode  # noqa: E402

S3NE = str(ROOT / "experiments" / "_facts_v20_s3_ne.py")
S4P = str(ROOT / "experiments" / "_facts_v20_s4_lead.py")
ANIMAL_KEYS = ("COW", "SHEEP", "GOOSE")


def _tile(farm):
    placed = Counter()
    pens = 0
    for row in farm.get("tiles") or []:
        for t in row:
            if not isinstance(t, dict):
                continue
            if t.get("kind") in ("PASTURE", "COOP"):
                pens += 1
            if t.get("animal"):
                placed[t["animal"]] += 1
    return placed, pens


def _owned(private, placed):
    n = sum(placed.values())
    shed = private.get("shed") or {}
    n += sum(int(shed.get(k, 0) or 0) for k in ANIMAL_KEYS)
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            n += sum(int(inv.get(k, 0) or 0) for k in ANIMAL_KEYS)
    return n


def run(agent, seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([agent, V20])
    cash = analyze_episode(env.steps, us_seat=0)
    eod = {}
    buys = []
    for step in env.steps:
        obs = _obs(step[0].observation)
        day = int(obs.get("day", 0))
        hour = int(obs.get("hour", 0))
        farm = (obs.get("farms") or [{}])[0]
        priv = obs.get("private") or {}
        placed, pens = _tile(farm)
        if hour == 23:
            eod[day] = {
                "money": float(farm.get("money", 0)),
                "owned": _owned(priv, placed),
                "placed": sum(placed.values()),
                "cows": placed["COW"],
                "sheep": placed["SHEEP"],
                "pens": pens,
            }
        for order in step[0].action.get("market") or []:
            if order and order[0] == "BUY_ANIMAL":
                buys.append((day, hour, order[1], int(order[2] if len(order) > 2 else 1)))
    bank = env.steps[-1][0].reward
    return bank, eod, buys, cash


def main():
    seeds = [int(x) for x in sys.argv[1:] if x.lstrip("-").isdigit()] or [8]
    for seed in seeds:
        print(f"\n==== seed {seed} ====")
        for name, path in (("s3ne", S3NE), ("s4lead", S4P)):
            print(f"running {name}...")
            bank, eod, buys, cash = run(path, seed)
            milk = cash["season_us"].get("SELL_MILK", 0)
            wool = cash["season_us"].get("SELL_WOOL", 0)
            straw = cash["season_us"].get("SELL_STRAWBERRY", 0)
            print(f"  bank={bank:.0f}  MILK={milk:.0f}  WOOL={wool:.0f}  STRAW={straw:.0f}")
            print("  BUY_ANIMAL", buys)
            print("  EOD d10-d20, d29 owned/placed/pens cows/sheep $")
            for d in list(range(10, 21)) + [29]:
                r = eod.get(d, {})
                print(
                    f"    d{d:02d} ${r.get('money', 0):7.0f} "
                    f"{r.get('owned', 0):2d}/{r.get('placed', 0):<2d} "
                    f"pens={r.get('pens', 0):2d} "
                    f"{r.get('cows', 0)}C{r.get('sheep', 0)}S"
                )


if __name__ == "__main__":
    main()
