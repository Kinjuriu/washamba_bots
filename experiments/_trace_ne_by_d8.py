"""Why NE is not carpeted by d8: occupancy, seed, cash vs v20.

Usage:
    .venv/Scripts/python.exe experiments/_trace_ne_by_d8.py
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import V20, _obs  # noqa: E402

AGENT = str(ROOT / "experiments" / "_facts_v20_s3_ne.py")


def _quad(farm):
    escaped = 0
    ne = {"empty": 0, "straw": 0, "wheat": 0, "melon": 0, "weed": 0, "other": 0}
    nw_straw = field_straw = 0
    board = len(farm.get("tiles") or []) or 10
    half = board // 2
    for y, row in enumerate(farm.get("tiles") or []):
        for x, t in enumerate(row):
            q = ("N" if y < half else "S") + ("W" if x < half else "E")
            if t is None:
                if q == "NE":
                    ne["empty"] += 1
                continue
            if not isinstance(t, dict):
                if q == "NE":
                    ne["other"] += 1
                continue
            kind = t.get("kind")
            crop = t.get("crop")
            if kind == "ESCAPED":
                escaped += 1
            if kind == "WEED" and q == "NE":
                ne["weed"] += 1
            if kind == "PLANT":
                if crop == "STRAWBERRY":
                    field_straw += 1
                    if q == "NE":
                        ne["straw"] += 1
                    elif q == "NW":
                        nw_straw += 1
                elif q == "NE":
                    if crop == "WHEAT":
                        ne["wheat"] += 1
                    elif crop == "MELON":
                        ne["melon"] += 1
                    else:
                        ne["other"] += 1
            elif q == "NE" and kind not in ("WEED",):
                ne["other"] += 1
    return escaped, ne, nw_straw, field_straw


def run_seed(seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([AGENT, V20])
    plants = [defaultdict(Counter), defaultdict(Counter)]
    buys = [defaultdict(Counter), defaultdict(Counter)]
    eod = [{}, {}]
    peak = [0, 0]
    for step in env.steps:
        for p in (0, 1):
            obs = _obs(step[p].observation)
            act = step[p].action or {}
            day = int(obs.get("day", 0))
            hour = int(obs.get("hour", 0))
            farm = (obs.get("farms") or [{}])[p]
            priv = obs.get("private") or {}
            for order in act.get("market") or []:
                if order and order[0] == "BUY_SEED" and len(order) > 1:
                    qty = int(order[2]) if len(order) > 2 else 1
                    buys[p][order[1]][day] += qty
            farmer = act.get("farmer") or ["PASS"]
            hands = act.get("hands") or []
            for a in [farmer, *hands]:
                if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT":
                    plants[p][a[1]][day] += 1
            escaped, ne, nw_straw, field_straw = _quad(farm)
            peak[p] = max(peak[p], field_straw)
            if hour == 23:
                eod[p][day] = {
                    "money": float(farm.get("money", 0)),
                    "held_straw": int((priv.get("seeds") or {}).get("STRAWBERRY", 0) or 0),
                    "ne": ne,
                    "nw_straw": nw_straw,
                    "field_straw": field_straw,
                    "escaped": escaped,
                    "hands": len(act.get("hands") or []),
                }
    return {
        "seed": seed,
        "bank": (env.steps[-1][0].reward, env.steps[-1][1].reward),
        "plants": plants,
        "buys": buys,
        "eod": eod,
        "peak": peak,
    }


def main():
    seeds = [int(a) for a in sys.argv[1:]] or [0, 8]
    for seed in seeds:
        r = run_seed(seed)
        print("=" * 78)
        print(
            f"seed={seed} bank us={r['bank'][0]:.0f} v20={r['bank'][1]:.0f} "
            f"peak STRAW field us={r['peak'][0]} v20={r['peak'][1]}"
        )
        print(
            f"  BUY_SEED STRAW d5-8 us="
            f"{[r['buys'][0]['STRAWBERRY'][d] for d in range(5, 9)]} "
            f"v20={[r['buys'][1]['STRAWBERRY'][d] for d in range(5, 9)]}"
        )
        print(
            f"  PLANT STRAW   d5-8 us="
            f"{[r['plants'][0]['STRAWBERRY'][d] for d in range(5, 9)]} "
            f"v20={[r['plants'][1]['STRAWBERRY'][d] for d in range(5, 9)]}"
        )
        print(
            "  day  who   $  seed  plant  NEstraw NEempty NEweed NWstraw field hands"
        )
        for day in range(5, 9):
            for p, name in ((0, "us"), (1, "v20")):
                e = r["eod"][p].get(day, {})
                ne = e.get("ne") or {}
                print(
                    f"  d{day}  {name:<3} {e.get('money', 0):5.0f} "
                    f"{e.get('held_straw', 0):5d} "
                    f"{r['plants'][p]['STRAWBERRY'][day]:6d} "
                    f"{ne.get('straw', 0):7d} {ne.get('empty', 0):7d} "
                    f"{ne.get('weed', 0):6d} {e.get('nw_straw', 0):7d} "
                    f"{e.get('field_straw', 0):5d} {e.get('hands', 0):5d}"
                )


if __name__ == "__main__":
    main()
