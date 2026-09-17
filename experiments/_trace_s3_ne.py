"""S3ne counters vs route_v20, seeds 0 and 8.

Usage:
    .venv/Scripts/python.exe experiments/_trace_s3_ne.py
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
BASELINE = (45154, 53578)


def _tile_animals(farm):
    escaped = 0
    ne_empty = ne_straw = nw_straw = 0
    wheat = straw = melon = 0
    board = len(farm.get("tiles") or []) or 10
    half = board // 2
    for y, row in enumerate(farm.get("tiles") or []):
        for x, t in enumerate(row):
            q = ("N" if y < half else "S") + ("W" if x < half else "E")
            if t is None:
                if q == "NE":
                    ne_empty += 1
                continue
            if not isinstance(t, dict):
                continue
            if t.get("kind") == "ESCAPED":
                escaped += 1
            if t.get("kind") == "PLANT":
                crop = t.get("crop")
                if crop == "WHEAT":
                    wheat += 1
                elif crop == "STRAWBERRY":
                    straw += 1
                    if q == "NE":
                        ne_straw += 1
                    elif q == "NW":
                        nw_straw += 1
                elif crop == "MELON":
                    melon += 1
    return escaped, wheat, straw, melon, ne_empty, ne_straw, nw_straw


def run_seed(seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([AGENT, V20])
    plants = defaultdict(Counter)
    land = []
    eod = {}
    escapes = 0
    bank_us = env.steps[-1][0].reward
    bank_v20 = env.steps[-1][1].reward
    for step in env.steps:
        obs = _obs(step[0].observation)
        act = step[0].action or {}
        day = int(obs.get("day", 0))
        hour = int(obs.get("hour", 0))
        farm = (obs.get("farms") or [{}])[0]
        for order in act.get("market") or []:
            if order and order[0] == "BUY_LAND":
                land.append((day, hour))
        farmer = act.get("farmer") or ["PASS"]
        hands = act.get("hands") or []
        for a in [farmer, *hands]:
            if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT":
                plants[a[1]][day] += 1
        escaped, wheat, straw, melon, ne_empty, ne_straw, nw_straw = _tile_animals(farm)
        escapes = max(escapes, escaped)
        if hour == 23:
            eod[day] = {
                "money": float(farm.get("money", 0)),
                "wheat": wheat,
                "straw": straw,
                "melon": melon,
                "ne_empty": ne_empty,
                "ne_straw": ne_straw,
                "nw_straw": nw_straw,
            }
    melon_after_d0 = sum(plants["MELON"][d] for d in range(1, 30))
    return {
        "seed": seed,
        "bank_us": bank_us,
        "bank_v20": bank_v20,
        "escapes": escapes,
        "land": land,
        "plants": plants,
        "eod": eod,
        "melon_after_d0": melon_after_d0,
    }


def main():
    seeds = [int(a) for a in sys.argv[1:]] or [0, 8]
    for seed in seeds:
        r = run_seed(seed)
        base = BASELINE[0] if seed == 0 else BASELINE[1] if seed == 8 else None
        d0 = r["eod"].get(0, {})
        d6 = r["eod"].get(6, {})
        straw = r["plants"]["STRAWBERRY"]
        wheat = r["plants"]["WHEAT"]
        melon = r["plants"]["MELON"]
        print("=" * 72)
        print(
            f"S3ne seed={seed} bank={r['bank_us']:.0f} v20={r['bank_v20']:.0f} "
            f"escapes={r['escapes']}"
        )
        if base is not None:
            delta = r["bank_us"] - base
            print(f"  vs S3roles {base}: {delta:+.0f}")
        print(f"  first land={r['land'][:1]} all={r['land']}")
        print(
            f"  d0 wheatF={d0.get('wheat')} straw={d0.get('straw')} "
            f"melon={d0.get('melon')}  PLANT WHEAT d0={wheat[0]} MELON d0={melon[0]}"
        )
        print(f"  PLANT MELON after d0={r['melon_after_d0']}")
        print(
            f"  PLANT STRAW d5-8={straw[5]}/{straw[6]}/{straw[7]}/{straw[8]} "
            f"d11={straw[11]}"
        )
        print(
            f"  EOD d6 $={d6.get('money', 0):.0f} NE straw={d6.get('ne_straw')} "
            f"empty={d6.get('ne_empty')} NW straw={d6.get('nw_straw')} "
            f"field straw={d6.get('straw')}"
        )
        ok_d6 = straw[6] >= 4
        ok_ne = (d6.get("ne_straw") or 0) > 0
        ok_esc = r["escapes"] == 0
        ok_melon = r["melon_after_d0"] == 0
        ok_land = bool(r["land"]) and r["land"][0][0] == 6
        ok_bank = base is None or r["bank_us"] >= base
        print(
            f"  counters: d6STRAW>=4={ok_d6} NEd6>0={ok_ne} "
            f"esc0={ok_esc} melon0={ok_melon} land_d6={ok_land} "
            f"bank_not_down={ok_bank}"
        )


if __name__ == "__main__":
    main()
