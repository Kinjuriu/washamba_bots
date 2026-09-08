"""d0–d8 STRAW/WHEAT miss diagnosis vs v20, seed 0 (then 8).

Prints per-day: cash, seed held/bought, plants, empty leftover, field
occupancy by quadrant. Stops being useful after d8.

Usage:
    .venv/Scripts/python.exe experiments/_trace_d5_straw.py
    .venv/Scripts/python.exe experiments/_trace_d5_straw.py 0 8
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
THROWAWAY = str(ROOT / "experiments" / "_facts_v20.py")
V20 = str(ROOT / "agents" / "route_v20.py")
SEEDS = (0, 8)
DAYS = 9
STRAW_SHOPS = ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET")
LAND_NEED = 1500  # first BUY_LAND 1000 + MIN_CASH_RESERVE_FOR_LAND_BUYING 500


def quadrant(x, y, board=10):
    half = board // 2
    return ("N" if y < half else "S") + ("W" if x < half else "E")


def scan_field(farm):
    crops = Counter()
    by_q = Counter()
    empty = Counter()
    pens = 0
    for y, row in enumerate(farm.get("tiles") or []):
        for x, t in enumerate(row):
            q = quadrant(x, y)
            if t is None:
                empty[q] += 1
                continue
            if not isinstance(t, dict):
                continue
            if t.get("kind") in ("COOP", "PASTURE") or t.get("animal"):
                pens += 1
                continue
            crop = t.get("crop")
            if crop:
                crops[crop] += 1
                by_q[(crop, q)] += 1
    return crops, by_q, empty, pens


def units(act):
    return [act.get("farmer") or []] + list(act.get("hands") or [])


def plants(act, crop):
    return sum(1 for u in units(act) if u and u[0] == "PLANT" and len(u) > 1 and u[1] == crop)


def buys(act, kind, product):
    total = 0
    for o in act.get("market") or []:
        if o and o[0] == kind and len(o) > 1 and o[1] == product:
            total += int(o[2]) if len(o) > 2 else 1
    return total


def buy_animal(act):
    total = 0
    for o in act.get("market") or []:
        if o and o[0] == "BUY_ANIMAL":
            total += int(o[2]) if len(o) > 2 else 1
    return total


def buy_land(act):
    return sum(1 for o in act.get("market") or [] if o and o[0] == "BUY_LAND")


def straw_sink(shops):
    return any(s in STRAW_SHOPS for s in (shops or []))


def run_seed(seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([THROWAWAY, V20])

    print("\n" + "=" * 96)
    print(f"# d0-d8 STRAW/WHEAT  seed={seed}")
    print("=" * 96)
    print(
        f"  {'day':>3} {'$h0':>6} {'vsLand':>6} {'heldS':>5} {'buyS':>4} {'pltS':>4} "
        f"{'heldW':>5} {'buyW':>4} {'pltW':>4} {'pltM':>4} {'buyA':>4} {'land':>4} "
        f"{'sinkS':>5} {'empty':>10} {'field':>22} {'pens':>4}"
    )

    prev = None
    day_buy_s = Counter()
    day_buy_w = Counter()
    day_plt_s = Counter()
    day_plt_w = Counter()
    day_plt_m = Counter()
    day_buy_a = Counter()
    day_land = Counter()
    money_h0 = {}
    held_h0 = {}
    shops_h0 = {}
    unlocked_h0 = {}
    eod = {}

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
        if day >= DAYS:
            prev = obs
            continue
        farm = (prev.get("farms") or [{}])[0]
        priv = prev.get("private") or {}
        seeds = priv.get("seeds") or {}
        if hour == 0:
            money_h0[day] = float(farm.get("money", 0))
            held_h0[day] = (
                int(seeds.get("STRAWBERRY", 0) or 0),
                int(seeds.get("WHEAT", 0) or 0),
                int(seeds.get("MELON", 0) or 0),
            )
            shops_h0[day] = list((prev.get("town") or {}).get("unlocked_shops") or [])
            unlocked_h0[day] = list(farm.get("unlocked_quadrants") or [])
        day_buy_s[day] += buys(act, "BUY_SEED", "STRAWBERRY")
        day_buy_w[day] += buys(act, "BUY_SEED", "WHEAT")
        day_plt_s[day] += plants(act, "STRAWBERRY")
        day_plt_w[day] += plants(act, "WHEAT")
        day_plt_m[day] += plants(act, "MELON")
        day_buy_a[day] += buy_animal(act)
        day_land[day] += buy_land(act)
        if hour == 23:
            crops, by_q, empty, pens = scan_field(farm)
            eod[day] = (crops, by_q, empty, pens, float(farm.get("money", 0)))
        prev = obs

    for day in range(DAYS):
        hs, hw, hm = held_h0.get(day, (0, 0, 0))
        crops, by_q, empty, pens, _ = eod.get(day, (Counter(), Counter(), Counter(), 0, 0))
        empty_s = ",".join(f"{q}{empty[q]}" for q in ("NW", "NE", "SW") if empty.get(q))
        field_s = (
            f"M{crops.get('MELON', 0)} W{crops.get('WHEAT', 0)} "
            f"S{crops.get('STRAWBERRY', 0)}"
        )
        nw_s = by_q.get(("STRAWBERRY", "NW"), 0)
        ne_s = by_q.get(("STRAWBERRY", "NE"), 0)
        cash = money_h0.get(day, 0)
        shops = shops_h0.get(day, [])
        print(
            f"  d{day:<2} {cash:6.0f} {cash - LAND_NEED:6.0f} {hs:5d} {day_buy_s[day]:4d} "
            f"{day_plt_s[day]:4d} {hw:5d} {day_buy_w[day]:4d} {day_plt_w[day]:4d} "
            f"{day_plt_m[day]:4d} {day_buy_a[day]:4d} {day_land[day]:4d} "
            f"{'Y' if straw_sink(shops) else 'n':>5} {empty_s or '-':>10} "
            f"{field_s:>22} {pens:4d}  NWs={nw_s} NEs={ne_s} "
            f"quad={unlocked_h0.get(day, [])} shops={shops}"
        )

    last = env.steps[-1][0]
    last_obs = last.observation
    if not isinstance(last_obs, dict):
        last_obs = dict(last_obs)
    bank = float((last_obs.get("farms") or [{}])[0].get("money", 0))
    print(f"  season bank us={bank:.0f}")

    print("\n  --- hour dump d5-d8 (cash / seed / plant / empty / field) ---")
    print(
        f"  {'dh':>6} {'$':>6} {'heldS':>5} {'buyS':>4} {'pltS':>4} {'pltW':>4} "
        f"{'land':>4} {'empty':>10} {'field':>16}  actions"
    )
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
        if day < 5 or day > 8:
            prev = obs
            continue
        farm = (prev.get("farms") or [{}])[0]
        priv = prev.get("private") or {}
        seeds = priv.get("seeds") or {}
        hs = int(seeds.get("STRAWBERRY", 0) or 0)
        bs = buys(act, "BUY_SEED", "STRAWBERRY")
        ps = plants(act, "STRAWBERRY")
        pw = plants(act, "WHEAT")
        ld = buy_land(act)
        crops, by_q, empty, pens = scan_field(farm)
        empty_s = ",".join(f"{q}{empty[q]}" for q in ("NW", "NE", "SW") if empty.get(q))
        field_s = (
            f"M{crops.get('MELON', 0)} W{crops.get('WHEAT', 0)} "
            f"S{crops.get('STRAWBERRY', 0)}"
        )
        notable = bs or ps or pw or ld or hour in (0, 12, 23)
        if notable:
            bits = []
            for o in act.get("market") or []:
                if o and o[0] in ("BUY_SEED", "BUY_LAND", "BUY_ANIMAL", "SELL"):
                    bits.append(" ".join(str(x) for x in o[:3]))
            n_plant_s = 0
            n_walk = 0
            for u in units(act):
                if not u:
                    continue
                if u[0] == "PLANT" and len(u) > 1 and u[1] == "STRAWBERRY":
                    n_plant_s += 1
                elif u[0] in ("MOVE_UP", "MOVE_DOWN", "MOVE_LEFT", "MOVE_RIGHT"):
                    n_walk += 1
            extra = f" walk={n_walk}" if n_walk else ""
            print(
                f"  d{day}h{hour:02d} {float(farm.get('money', 0)):6.0f} {hs:5d} "
                f"{bs:4d} {ps:4d} {pw:4d} {ld:4d} {empty_s or '-':>10} "
                f"{field_s:>16}  {' | '.join(bits) or '-'}{extra}"
            )
        prev = obs


def main():
    seeds = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [0]
    for seed in seeds:
        run_seed(seed)


if __name__ == "__main__":
    main()
