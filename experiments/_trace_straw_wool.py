"""Contested STRAW/WOOL revenue diagnosis vs v20, seeds 0+8.

Stages: field occupancy → harvest → shed/held → SELL_$ (+ herd for WOOL).
Reuses lockstep $ from _trace_cashflow_v20.

Usage:
    .venv/Scripts/python.exe experiments/_trace_straw_wool.py
    .venv/Scripts/python.exe experiments/_trace_straw_wool.py 0 8
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import analyze_episode  # noqa: E402

THROWAWAY = str(ROOT / "experiments" / "_facts_v20.py")
V20 = str(ROOT / "agents" / "route_v20.py")
SEEDS = (0, 8)


def quadrant(x, y, board=10):
    half = board // 2
    return ("N" if y < half else "S") + ("W" if x < half else "E")


def scan_field(farm, crop):
    n = 0
    by_q = Counter()
    for y, row in enumerate(farm.get("tiles") or []):
        for x, t in enumerate(row):
            if isinstance(t, dict) and t.get("crop") == crop:
                n += 1
                by_q[quadrant(x, y)] += 1
    return n, by_q


def scan_animals(farm):
    n = 0
    species = Counter()
    unfed = 0
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict) and t.get("animal"):
                n += 1
                species[t["animal"]] += 1
                if not t.get("fed_today"):
                    unfed += 1
    return n, species, unfed


def held_product(private, product):
    total = 0
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            total += int(inv.get(product, 0) or 0)
    return total


def harvest_of(act, crop_hint=None):
    """Count HARVEST actions (crop unknown from action alone)."""
    units = [act.get("farmer") or []] + list(act.get("hands") or [])
    return sum(1 for u in units if u and u[0] == "HARVEST")


def plant_of(act, crop):
    units = [act.get("farmer") or []] + list(act.get("hands") or [])
    return sum(1 for u in units if u and u[0] == "PLANT" and len(u) > 1 and u[1] == crop)


def sell_qty(act, product):
    total = 0
    for o in act.get("market") or []:
        if o and o[0] == "SELL" and len(o) > 2 and o[1] == product:
            total += int(o[2] or 0)
    return total


def run_seed(seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([THROWAWAY, V20])
    cash = analyze_episode(env.steps, us_seat=0)

    day_agg = {
        0: defaultdict(lambda: Counter()),
        1: defaultdict(lambda: Counter()),
    }
    # track EOD field/herd snapshots
    eod = {0: {}, 1: {}}

    prev = [None, None]
    for step in env.steps:
        obs_list = []
        acts = []
        for p in (0, 1):
            raw = step[p]
            obs = raw.observation
            if not isinstance(obs, dict):
                try:
                    obs = dict(obs)
                except Exception:
                    pass
            act = raw.get("action") if hasattr(raw, "get") else None
            act = act or getattr(raw, "action", None) or {}
            obs_list.append(obs)
            acts.append(act)

        if prev[0] is None:
            prev = obs_list
            continue

        src = prev
        day = src[0].get("day", 0)
        hour = src[0].get("hour", 0)

        for p in (0, 1):
            farm = (src[p].get("farms") or [{}])[p]
            priv = src[p].get("private") or {}
            agg = day_agg[p][day]
            agg["plant_straw"] += plant_of(acts[p], "STRAWBERRY")
            agg["plant_wheat"] += plant_of(acts[p], "WHEAT")
            agg["harvest"] += harvest_of(acts[p])
            agg["sell_straw_q"] += sell_qty(acts[p], "STRAWBERRY")
            agg["sell_wool_q"] += sell_qty(acts[p], "WOOL")
            agg["sell_milk_q"] += sell_qty(acts[p], "MILK")
            if hour == 23:
                straw_n, straw_q = scan_field(farm, "STRAWBERRY")
                herd, species, unfed = scan_animals(farm)
                eod[p][day] = {
                    "straw": straw_n,
                    "straw_q": dict(straw_q),
                    "herd": herd,
                    "species": dict(species),
                    "shed_straw": int((priv.get("shed") or {}).get("STRAWBERRY", 0) or 0),
                    "shed_wool": int((priv.get("shed") or {}).get("WOOL", 0) or 0),
                    "held_straw": held_product(priv, "STRAWBERRY"),
                    "held_wool": held_product(priv, "WOOL"),
                    "money": float(farm.get("money", 0)),
                }
        prev = obs_list

    print("\n" + "=" * 88)
    print(
        f"# STRAW/WOOL path  seed={seed}  "
        f"bank us={cash['bank_us']:.0f}  v20={cash['bank_v20']:.0f}"
    )
    print("=" * 88)

    # Season $
    cats = ("SELL_STRAWBERRY", "SELL_WOOL", "SELL_MILK", "SELL_MELON", "SELL_WHEAT")
    print("\n--- season $ ---")
    print(f"  {'cat':<22} {'us':>10} {'v20':>10} {'gap':>10}")
    for c in cats:
        a = cash["season_us"].get(c, 0)
        b = cash["season_v20"].get(c, 0)
        print(f"  {c:<22} {a:10.0f} {b:10.0f} {a - b:10.0f}")

    # Day rollup for STRAW/WOOL $ and field
    print("\n--- day rollup (STRAW/WOOL $ + EOD field/herd) ---")
    print(
        f"  {'day':>3}  {'SELL_STRAW $':>16}  {'SELL_WOOL $':>14}  "
        f"{'straw_EOD':>12}  {'herd_EOD':>10}  {'plant_straw':>12}  "
        f"{'sell_straw_q':>12}  {'sell_wool_q':>11}  {'widen':>8}"
    )
    prev_gap = None
    for day in range(0, 30):
        sm_u = cash["by_day_us"].get(day, Counter()).get("SELL_STRAWBERRY", 0)
        sm_v = cash["by_day_v20"].get(day, Counter()).get("SELL_STRAWBERRY", 0)
        wo_u = cash["by_day_us"].get(day, Counter()).get("SELL_WOOL", 0)
        wo_v = cash["by_day_v20"].get(day, Counter()).get("SELL_WOOL", 0)
        if (
            abs(sm_u) + abs(sm_v) + abs(wo_u) + abs(wo_v) < 1
            and day not in (11, 12, 15, 18, 20, 25)
        ):
            # still show unlock / mid / late samples
            if day not in eod[0] and day not in eod[1]:
                continue

        eu = eod[0].get(day, {})
        ev = eod[1].get(day, {})
        au = day_agg[0][day]
        av = day_agg[1][day]
        mu = eu.get("money")
        mv = ev.get("money")
        gap = (mu - mv) if mu is not None and mv is not None else None
        widen = (gap - prev_gap) if gap is not None and prev_gap is not None else None
        if gap is not None:
            prev_gap = gap

        def pair(a, b):
            aa = "-" if a is None else str(a)
            bb = "-" if b is None else str(b)
            return f"{aa}|{bb}"

        def pairf(a, b):
            def fmt(x):
                if x is None:
                    return "-"
                return f"{x:.0f}"
            return f"{fmt(a)}|{fmt(b)}"

        print(
            f"  d{day:<2}  {pairf(sm_u, sm_v):>16}  {pairf(wo_u, wo_v):>14}  "
            f"{pair(eu.get('straw'), ev.get('straw')):>12}  "
            f"{pair(eu.get('herd'), ev.get('herd')):>10}  "
            f"{pair(au['plant_straw'], av['plant_straw']):>12}  "
            f"{pair(au['sell_straw_q'], av['sell_straw_q']):>12}  "
            f"{pair(au['sell_wool_q'], av['sell_wool_q']):>11}  "
            f"{(f'{widen:.0f}' if widen is not None else '-'):>8}"
        )
        if day in (11, 12, 15, 18, 22, 25) or (widen is not None and abs(widen) > 2000):
            print(
                f"       strawQ us={eu.get('straw_q')} v20={ev.get('straw_q')}  "
                f"species us={eu.get('species')} v20={ev.get('species')}  "
                f"shedS={pair(eu.get('shed_straw'), ev.get('shed_straw'))}  "
                f"shedW={pair(eu.get('shed_wool'), ev.get('shed_wool'))}  "
                f"heldS={pair(eu.get('held_straw'), ev.get('held_straw'))}"
            )

    # Window totals d11-29
    print("\n--- post-d10 window $ (d11–29) ---")
    for label, by in (("us", cash["by_day_us"]), ("v20", cash["by_day_v20"])):
        straw = wool = milk = 0.0
        for d in range(11, 30):
            straw += by.get(d, Counter()).get("SELL_STRAWBERRY", 0)
            wool += by.get(d, Counter()).get("SELL_WOOL", 0)
            milk += by.get(d, Counter()).get("SELL_MILK", 0)
        print(f"  {label}: STRAW={straw:.0f}  WOOL={wool:.0f}  MILK={milk:.0f}")

    # Bind hint
    su = cash["season_us"].get("SELL_STRAWBERRY", 0)
    sv = cash["season_v20"].get("SELL_STRAWBERRY", 0)
    wu = cash["season_us"].get("SELL_WOOL", 0)
    wv = cash["season_v20"].get("SELL_WOOL", 0)
    print("\n--- bind hint ---")
    straw_gap = su - sv
    wool_gap = wu - wv
    print(f"  season STRAW gap={straw_gap:.0f}  WOOL gap={wool_gap:.0f}")
    # peak straw field
    peak_u = max((eod[0].get(d, {}).get("straw") or 0) for d in range(30))
    peak_v = max((eod[1].get(d, {}).get("straw") or 0) for d in range(30))
    print(f"  peak STRAW field us={peak_u} v20={peak_v}")
    end_hu = eod[0].get(29, {}).get("herd") or eod[0].get(28, {}).get("herd")
    end_hv = eod[1].get(29, {}).get("herd") or eod[1].get(28, {}).get("herd")
    print(f"  late herd us={end_hu} v20={end_hv}")
    if straw_gap < -5000 and peak_u < 0.6 * max(peak_v, 1):
        print("  likely STRAW acreage/carpet (facts 30–32)")
    elif straw_gap < -5000:
        print("  likely STRAW harvest/sell path (fruit planted but $ missing)")
    elif wool_gap < -5000 and (end_hu or 0) < 0.6 * max(end_hv or 1, 1):
        print("  likely WOOL via herd scale (facts 15/17)")
    elif wool_gap < -5000:
        print("  likely WOOL sell/care path (herd ok, $ missing)")
    else:
        print("  neither STRAW nor WOOL dominates alone — inspect day rollup")

    return cash


def main():
    seeds = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(SEEDS)
    for seed in seeds:
        run_seed(seed)


if __name__ == "__main__":
    main()
