"""HORIZON S2 snapshot: S2 throwaway vs route_v20, seeds 0 and 8.

Prints S2 picture (d0 wheat / 4/4 / d3 cow / land) and the d10 handoff
window: EOD cash, herd, melon $, d11+ BUY_ANIMAL, STRAW/WOOL sell path.

Usage:
    .venv/Scripts/python.exe experiments/_trace_horizon_s2.py
    .venv/Scripts/python.exe experiments/_trace_horizon_s2.py 0 8
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import V20, _obs, analyze_episode  # noqa: E402

S2 = str(ROOT / "experiments" / "_facts_v20_s2.py")
S2H = str(ROOT / "experiments" / "_facts_v20_s2h.py")
S3 = str(ROOT / "experiments" / "_facts_v20_s3.py")
S3HOME = str(ROOT / "experiments" / "_facts_v20_s3_home.py")
ANIMAL_KEYS = ("COW", "SHEEP", "GOOSE")


def _tile_animals(farm):
    placed = Counter()
    pens = 0
    escaped = 0
    wheat = straw = melon = 0
    for row in farm.get("tiles") or []:
        for t in row:
            if not isinstance(t, dict):
                continue
            if t.get("kind") in ("PASTURE", "COOP"):
                pens += 1
            if t.get("kind") == "ESCAPED":
                escaped += 1
            if t.get("animal"):
                placed[t["animal"]] += 1
            if t.get("kind") == "PLANT":
                crop = t.get("crop")
                if crop == "WHEAT":
                    wheat += 1
                elif crop == "STRAWBERRY":
                    straw += 1
                elif crop == "MELON":
                    melon += 1
    return placed, pens, escaped, wheat, straw, melon


def _owned(farm, private, placed):
    shed = private.get("shed") or {}
    n = sum(placed.values())
    n += sum(int(shed.get(k, 0) or 0) for k in ANIMAL_KEYS)
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            n += sum(int(inv.get(k, 0) or 0) for k in ANIMAL_KEYS)
    return n


def _unit_actions(act):
    farmer = act.get("farmer") or ["PASS"]
    hands = act.get("hands") or []
    if not isinstance(hands, list):
        hands = []
    return [farmer, *hands]


def run_seed(seed, agent=S2):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([agent, V20])
    steps = env.steps
    cash = analyze_episode(steps, us_seat=0)

    eod = [{}, {}]
    land_days = [set(), set()]
    buys = [defaultdict(Counter), defaultdict(Counter)]
    plants = [defaultdict(Counter), defaultdict(Counter)]
    hires = [Counter(), Counter()]
    max_hands = [Counter(), Counter()]
    escapes = [0, 0]

    for step in steps:
        for p in (0, 1):
            obs = _obs(step[p].observation)
            act = step[p].action or {}
            day = int(obs.get("day", 0))
            hour = int(obs.get("hour", 0))
            farm = (obs.get("farms") or [{}])[p]
            priv = obs.get("private") or {}
            market = act.get("market") or []
            hands = act.get("hands") or []
            n_hands = len(hands) if isinstance(hands, list) else 0
            if n_hands > max_hands[p][day]:
                max_hands[p][day] = n_hands
            for order in market:
                if not order:
                    continue
                if order[0] == "HIRE":
                    hires[p][day] += 1
                elif order[0] == "BUY_LAND":
                    land_days[p].add(day)
                elif order[0] == "BUY_ANIMAL" and len(order) > 1:
                    buys[p][day][order[1]] += int(order[2] if len(order) > 2 else 1)
            for a in _unit_actions(act):
                if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT":
                    plants[p][a[1]][day] += 1
            placed, pens, escaped, wheat, straw, melon = _tile_animals(farm)
            escapes[p] = max(escapes[p], escaped)
            if hour == 23:
                eod[p][day] = {
                    "money": float(farm.get("money", 0)),
                    "placed": sum(placed.values()),
                    "owned": _owned(farm, priv, placed),
                    "cows": placed["COW"],
                    "sheep": placed["SHEEP"],
                    "pens": pens,
                    "wheat": wheat,
                    "straw": straw,
                    "melon": melon,
                    "unlocked": list(farm.get("unlocked_quadrants") or ["NW"]),
                    "shed_wheat": int((priv.get("shed") or {}).get("WHEAT", 0) or 0),
                    "shed_straw": int((priv.get("shed") or {}).get("STRAWBERRY", 0) or 0),
                    "shed_melon": int((priv.get("shed") or {}).get("MELON", 0) or 0),
                    "shed_wool": int((priv.get("shed") or {}).get("WOOL", 0) or 0),
                }

    return {
        "seed": seed,
        "cash": cash,
        "eod": eod,
        "land": [min(land_days[p]) if land_days[p] else None for p in (0, 1)],
        "buys": buys,
        "plants": plants,
        "hires": hires,
        "max_hands": max_hands,
        "escapes": escapes,
    }


def _usd(cash, seat_key, day, cat):
    src = cash["by_day_us"] if seat_key == "us" else cash["by_day_v20"]
    return src[day].get(cat, 0)


def _units(cash, seat_key, day, cat):
    # analyze_episode stores season units only; day $ is in by_day.
    return None


def print_seed(rep, label="S2"):
    seed = rep["seed"]
    cash = rep["cash"]
    print("\n" + "#" * 88)
    print(
        f"# HORIZON {label}  seed={seed}  seat=0  "
        f"bank us={cash['bank_us']:.0f}  v20={cash['bank_v20']:.0f}  "
        f"escapes us={rep['escapes'][0]} v20={rep['escapes'][1]}"
    )
    print("#" * 88)
    print(f"  first BUY_LAND  us={rep['land'][0]}  v20={rep['land'][1]}")

    print("\n--- S2 picture (EOD) ---")
    for day in (0, 3, 5, 7):
        u = rep["eod"][0].get(day, {})
        v = rep["eod"][1].get(day, {})
        print(
            f"  d{day} us $={u.get('money', 0):7.0f} herd={u.get('owned', 0)}"
            f" placed={u.get('placed', 0)} {u.get('cows', 0)}C{u.get('sheep', 0)}S"
            f" pens={u.get('pens', 0)} wheatF={u.get('wheat', 0)}"
            f" straw={u.get('straw', 0)} melon={u.get('melon', 0)}"
            f" land={'+'.join(u.get('unlocked') or [])}"
            f"  | v20 $={v.get('money', 0):7.0f} herd={v.get('owned', 0)}"
            f" wheatF={v.get('wheat', 0)} straw={v.get('straw', 0)}"
        )
        print(
            f"       PLANT WHEAT us={rep['plants'][0]['WHEAT'].get(day, 0)}"
            f" v20={rep['plants'][1]['WHEAT'].get(day, 0)}"
            f"  PLANT STRAW us={rep['plants'][0]['STRAWBERRY'].get(day, 0)}"
            f" v20={rep['plants'][1]['STRAWBERRY'].get(day, 0)}"
            f"  PLANT MELON us={rep['plants'][0]['MELON'].get(day, 0)}"
            f" v20={rep['plants'][1]['MELON'].get(day, 0)}"
        )

    print("\n--- d9-d12 handoff window ---")
    print(
        f"  {'day':>3} {'$us':>7} {'$v20':>7} {'herd':>7} {'pens':>5} "
        f"{'melonF':>6} {'SELL_M $':>16} {'BUY_A':>12} {'HIRE':>8}"
    )
    for day in range(9, 13):
        u = rep["eod"][0].get(day, {})
        v = rep["eod"][1].get(day, {})
        bu = "+".join(f"{sp}{n}" for sp, n in sorted(rep["buys"][0][day].items()) if n) or "-"
        sm_u = _usd(cash, "us", day, "SELL_MELON")
        sm_v = _usd(cash, "v20", day, "SELL_MELON")
        print(
            f"  {day:3d} {u.get('money', 0):7.0f} {v.get('money', 0):7.0f} "
            f"{u.get('owned', 0):2d}/{v.get('owned', 0):<2d}  "
            f"{u.get('pens', 0):2d}/{v.get('pens', 0):<2d} "
            f"{u.get('melon', 0):3d}/{v.get('melon', 0):<2d} "
            f"{sm_u:7.0f}/{sm_v:<7.0f}  {bu:<12} "
            f"{rep['hires'][0][day]:2d}/{rep['hires'][1][day]:<2d}"
        )

    print("\n--- BUY_ANIMAL by day (us / v20 order qty) ---")
    print(f"  {'day':>3}  {'us':<20} {'v20':<20}  {'herd us/v20':>12}")
    for day in range(30):
        bu = dict(rep["buys"][0][day])
        bv = dict(rep["buys"][1][day])
        if not bu and not bv:
            continue
        su = "+".join(f"{sp}{n}" for sp, n in sorted(bu.items()) if n) or "-"
        sv = "+".join(f"{sp}{n}" for sp, n in sorted(bv.items()) if n) or "-"
        u = rep["eod"][0].get(day, {})
        v = rep["eod"][1].get(day, {})
        print(
            f"  {day:3d}  {su:<20} {sv:<20}  "
            f"{u.get('owned', '-'):>3}/{v.get('owned', '-'):<3}"
        )

    print("\n--- STRAW/WOOL sell path by day (executed $ / units if $) ---")
    print(
        f"  {'day':>3}  {'STRAW $ us/v20':>18}  {'WOOL $ us/v20':>16}  "
        f"{'strawF':>9}  {'shedS/W':>9}  {'herd':>7}"
    )
    for day in range(0, 30):
        ss_u = _usd(cash, "us", day, "SELL_STRAWBERRY")
        ss_v = _usd(cash, "v20", day, "SELL_STRAWBERRY")
        sw_u = _usd(cash, "us", day, "SELL_WOOL")
        sw_v = _usd(cash, "v20", day, "SELL_WOOL")
        if ss_u == 0 and ss_v == 0 and sw_u == 0 and sw_v == 0 and day not in (10, 11, 15, 21):
            continue
        u = rep["eod"][0].get(day, {})
        v = rep["eod"][1].get(day, {})
        print(
            f"  {day:3d}  {ss_u:7.0f}/{ss_v:<7.0f}  {sw_u:7.0f}/{sw_v:<7.0f}  "
            f"{u.get('straw', 0):3d}/{v.get('straw', 0):<3d}  "
            f"{u.get('shed_straw', 0):3d}/{u.get('shed_wool', 0):<3d}  "
            f"{u.get('owned', 0):2d}/{v.get('owned', 0):<2d}"
        )

    print("\n--- season executed $ ---")
    cats = (
        "SELL_STRAWBERRY", "SELL_WOOL", "SELL_MELON", "SELL_WHEAT", "SELL_MILK",
        "BUY_PRODUCT_WHEAT", "BUY_ANIMAL_SHEEP", "BUY_ANIMAL_COW", "BUY_LAND",
        "BUY_SEED_WHEAT", "BUY_SEED_STRAWBERRY", "BUY_SEED_MELON",
    )
    print(f"  {'cat':<24} {'us':>10} {'v20':>10} {'gap':>10}")
    for cat in cats:
        a = cash["season_us"].get(cat, 0)
        b = cash["season_v20"].get(cat, 0)
        print(f"  {cat:<24} {a:10.0f} {b:10.0f} {a - b:10.0f}")
    print("  units:")
    for cat in (
        "SELL_STRAWBERRY", "SELL_WOOL", "SELL_MELON", "SELL_WHEAT",
        "BUY_ANIMAL_SHEEP", "BUY_ANIMAL_COW",
    ):
        a = cash["units_us"].get(cat, 0)
        b = cash["units_v20"].get(cat, 0)
        print(f"    {cat:<22} {a:6.0f} {b:6.0f}")
    print(
        f"  PLANT STRAW d5-8 us={sum(rep['plants'][0]['STRAWBERRY'].get(d, 0) for d in range(5, 9))}"
        f" v20={sum(rep['plants'][1]['STRAWBERRY'].get(d, 0) for d in range(5, 9))}"
        f"  d11 us={rep['plants'][0]['STRAWBERRY'].get(11, 0)}"
        f" v20={rep['plants'][1]['STRAWBERRY'].get(11, 0)}"
    )
    print(
        f"  PLANT WHEAT d0 us={rep['plants'][0]['WHEAT'].get(0, 0)}"
        f" v20={rep['plants'][1]['WHEAT'].get(0, 0)}"
        f"  PLANT MELON after d0 us={sum(v for d, v in rep['plants'][0]['MELON'].items() if d > 0)}"
        f" v20={sum(v for d, v in rep['plants'][1]['MELON'].items() if d > 0)}"
    )


def main():
    args = sys.argv[1:]
    agent = (
        S3HOME if "--s3home" in args else
        S3 if "--s3" in args else
        S2H if "--s2h" in args else
        S2
    )
    label = (
        "S3home" if agent == S3HOME else
        "S3" if agent == S3 else
        "S2h" if agent == S2H else
        "S2"
    )
    seeds = [int(x) for x in args if x.lstrip("-").isdigit()] or [0, 8]
    for seed in seeds:
        print(f"running {label} seed {seed}...", flush=True)
        print_seed(run_seed(seed, agent=agent), label=label)


if __name__ == "__main__":
    main()
