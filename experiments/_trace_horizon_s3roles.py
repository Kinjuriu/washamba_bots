"""HORIZON S3roles snapshot: d9–d10 S4 window vs route_v20, seeds 0 and 8.

Fill HORIZON Actual before coding S4 (facts 15/17 herd ladder). Do not
reconcile calendar_owned_target until this print says the farm can fund
8 by d6.

Usage:
    .venv/Scripts/python.exe experiments/_trace_horizon_s3roles.py
    .venv/Scripts/python.exe experiments/_trace_horizon_s3roles.py 0 8
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import V20, _obs, analyze_episode  # noqa: E402

S3ROLES = str(ROOT / "experiments" / "_facts_v20_s3_roles.py")
ANIMAL_KEYS = ("COW", "SHEEP", "GOOSE")
COW_COST = 400
SHEEP_COST = 500
LAND1_COST = 1000
LAND_FLOOR = 500
# Fact 15 S4 ladder: 8 by d6. Two extra head vs the hold-6 calendar.
EXTRA_HEAD_TO_8 = 2


def _tile_animals(farm):
    placed = Counter()
    pens = 0
    escaped = 0
    wheat = straw = melon = 0
    ne_empty = ne_straw = nw_straw = 0
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
                    if q == "NE":
                        ne_straw += 1
                    elif q == "NW":
                        nw_straw += 1
                elif crop == "MELON":
                    melon += 1
            elif t is None or t.get("kind") in (None,):
                pass
    return placed, pens, escaped, wheat, straw, melon, ne_empty, ne_straw, nw_straw


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


def _held(private, product):
    n = int((private.get("shed") or {}).get(product, 0) or 0)
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            n += int(inv.get(product, 0) or 0)
    return n


def run_seed(seed, agent=S3ROLES):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([agent, V20])
    steps = env.steps
    cash = analyze_episode(steps, us_seat=0)

    eod = [{}, {}]
    land_events = [[], []]
    buys = [defaultdict(Counter), defaultdict(Counter)]
    plants = [defaultdict(Counter), defaultdict(Counter)]
    hires = [Counter(), Counter()]
    max_hands = [Counter(), Counter()]
    escapes = [0, 0]
    d6_hours = []
    d5_buys = []
    d9_d10_hours = []

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
            buy_a = []
            land_now = False
            for order in market:
                if not order:
                    continue
                if order[0] == "HIRE":
                    hires[p][day] += 1
                elif order[0] == "BUY_LAND":
                    land_events[p].append((day, hour))
                    land_now = True
                elif order[0] == "BUY_ANIMAL" and len(order) > 1:
                    qty = int(order[2] if len(order) > 2 else 1)
                    buys[p][day][order[1]] += qty
                    buy_a.append((order[1], qty))
            for a in _unit_actions(act):
                if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT":
                    plants[p][a[1]][day] += 1
            placed, pens, escaped, wheat, straw, melon, ne_empty, ne_straw, nw_straw = (
                _tile_animals(farm)
            )
            escapes[p] = max(escapes[p], escaped)
            owned = _owned(farm, priv, placed)
            row = {
                "money": float(farm.get("money", 0)),
                "placed": sum(placed.values()),
                "owned": owned,
                "cows": placed["COW"],
                "sheep": placed["SHEEP"],
                "pens": pens,
                "wheat": wheat,
                "straw": straw,
                "melon": melon,
                "ne_empty": ne_empty,
                "ne_straw": ne_straw,
                "nw_straw": nw_straw,
                "unlocked": list(farm.get("unlocked_quadrants") or ["NW"]),
                "shed_wheat": int((priv.get("shed") or {}).get("WHEAT", 0) or 0),
                "held_wheat": _held(priv, "WHEAT"),
                "shed_straw": int((priv.get("shed") or {}).get("STRAWBERRY", 0) or 0),
                "shed_melon": int((priv.get("shed") or {}).get("MELON", 0) or 0),
                "held_melon": _held(priv, "MELON"),
                "shed_wool": int((priv.get("shed") or {}).get("WOOL", 0) or 0),
                "held_wool": _held(priv, "WOOL"),
                "shed_fert": int((priv.get("shed") or {}).get("FERTILIZER", 0) or 0),
                "hands": n_hands,
            }
            if hour == 23:
                eod[p][day] = row
            if p == 0 and day == 5 and buy_a:
                d5_buys.append((hour, buy_a))
            if p == 0 and day == 6:
                d6_hours.append({
                    "hour": hour,
                    **row,
                    "buy_a": buy_a,
                    "land": land_now,
                    "hire": sum(1 for o in market if o and o[0] == "HIRE"),
                })
            if p == 0 and day in (9, 10) and (
                hour in (0, 4, 8, 12, 16, 20, 23) or land_now or buy_a
            ):
                d9_d10_hours.append({
                    "day": day,
                    "hour": hour,
                    **row,
                    "buy_a": buy_a,
                    "land": land_now,
                    "hire": sum(1 for o in market if o and o[0] == "HIRE"),
                })

    return {
        "seed": seed,
        "cash": cash,
        "eod": eod,
        "land": land_events,
        "buys": buys,
        "plants": plants,
        "hires": hires,
        "max_hands": max_hands,
        "escapes": escapes,
        "d6_hours": d6_hours,
        "d5_buys": d5_buys,
        "d9_d10_hours": d9_d10_hours,
    }


def _usd(cash, seat_key, day, cat):
    src = cash["by_day_us"] if seat_key == "us" else cash["by_day_v20"]
    return src[day].get(cat, 0)


def _units(cash, seat_key, day, cat):
    key = "by_day_units_us" if seat_key == "us" else "by_day_units_v20"
    src = cash.get(key) or {}
    return src.get(day, {}).get(cat, 0)


def _first_land(events):
    return events[0] if events else None


def print_seed(rep):
    seed = rep["seed"]
    cash = rep["cash"]
    print("\n" + "#" * 88)
    print(
        f"# HORIZON S3roles  seed={seed}  seat=0  "
        f"bank us={cash['bank_us']:.0f}  v20={cash['bank_v20']:.0f}  "
        f"escapes us={rep['escapes'][0]} v20={rep['escapes'][1]}"
    )
    print("#" * 88)
    print(
        f"  first BUY_LAND  us={_first_land(rep['land'][0])}  "
        f"v20={_first_land(rep['land'][1])}"
    )
    print(f"  all BUY_LAND us={rep['land'][0]}  v20={rep['land'][1]}")
    print(f"  d5 BUY_ANIMAL us={rep['d5_buys'] or 'none'}")

    print("\n--- S3roles pictures (EOD) ---")
    for day in (0, 3, 5, 6, 7, 8):
        u = rep["eod"][0].get(day, {})
        v = rep["eod"][1].get(day, {})
        print(
            f"  d{day} us $={u.get('money', 0):7.0f} herd={u.get('owned', 0)}"
            f" placed={u.get('placed', 0)} {u.get('cows', 0)}C{u.get('sheep', 0)}S"
            f" pens={u.get('pens', 0)} wheatF={u.get('wheat', 0)}"
            f" straw={u.get('straw', 0)} melon={u.get('melon', 0)}"
            f" land={'+'.join(u.get('unlocked') or [])}"
            f"  | v20 $={v.get('money', 0):7.0f} herd={v.get('owned', 0)}"
            f" placed={v.get('placed', 0)} wheatF={v.get('wheat', 0)}"
            f" straw={v.get('straw', 0)} melon={v.get('melon', 0)}"
        )
        print(
            f"       PLANT WHEAT us={rep['plants'][0]['WHEAT'].get(day, 0)}"
            f" v20={rep['plants'][1]['WHEAT'].get(day, 0)}"
            f"  PLANT STRAW us={rep['plants'][0]['STRAWBERRY'].get(day, 0)}"
            f" v20={rep['plants'][1]['STRAWBERRY'].get(day, 0)}"
            f"  PLANT MELON us={rep['plants'][0]['MELON'].get(day, 0)}"
            f" v20={rep['plants'][1]['MELON'].get(day, 0)}"
            f"  NE empty/straw us={u.get('ne_empty', '-')}/{u.get('ne_straw', '-')}"
            f" NW straw={u.get('nw_straw', '-')}"
            f"  shedW us={u.get('shed_wheat', 0)} heldW={u.get('held_wheat', 0)}"
            f"  crew maxH={rep['max_hands'][0][day]}/{rep['max_hands'][1][day]}"
        )

    print("\n--- d6 hourly (fund 8-by-d6?) ---")
    print(
        f"  {'h':>3} {'$':>6} {'own/pl':>7} {'pens':>4} {'shedW':>5} "
        f"{'heldW':>5} {'woolS/H':>8} land buyA hire unlocked"
    )
    land_cash = None
    after_land = None
    for r in rep["d6_hours"]:
        mark = ""
        if r["land"]:
            mark = " LAND"
            land_cash = r["money"]
        if land_cash is not None and after_land is None and not r["land"] and r["hour"] > 0:
            after_land = r
        if r["hour"] % 2 == 0 or r["land"] or r["buy_a"] or r["hour"] in (10, 11, 23):
            bu = "+".join(f"{sp}{n}" for sp, n in r["buy_a"]) if r["buy_a"] else "-"
            print(
                f"  {r['hour']:3d} {r['money']:6.0f} {r['owned']:2d}/{r['placed']:<2d} "
                f"{r['pens']:4d} {r['shed_wheat']:5d} {r['held_wheat']:5d} "
                f"{r['shed_wool']:3d}/{r['held_wool']:<3d} "
                f"{int(r['land']):4d} {bu:<8} {r['hire']:3d} "
                f"{'+'.join(r['unlocked'])}{mark}"
            )

    print("\n--- can Actual fund fact 15's 8-by-d6? ---")
    d6e = rep["eod"][0].get(6, {})
    owned_d6 = d6e.get("owned", 0)
    need = max(0, 8 - owned_d6)
    # Conservative: two extra cows after land (S4 wants 8; we sit at ~6).
    extra_cost = need * COW_COST
    wheat_need = need * 2
    eod_cash = d6e.get("money", 0)
    print(f"  EOD d6 owned={owned_d6} placed={d6e.get('placed')} cash={eod_cash:.0f}")
    print(f"  first land us={_first_land(rep['land'][0])}  cash at emit={land_cash}")
    print(
        f"  to hit 8: need {need} more head  (~${extra_cost} if cows, "
        f"${need * SHEEP_COST} if sheep) + wheat buffer {wheat_need}"
    )
    print(
        f"  land spend ${LAND1_COST} with floor ${LAND_FLOOR} so emit needs "
        f">=${LAND1_COST + LAND_FLOOR}; leftover after land cannot also "
        f"cover {need} head unless cash is far above that."
    )
    if land_cash is not None:
        leftover_if_land = land_cash - LAND1_COST
        print(
            f"  cash at land emit ${land_cash:.0f} - ${LAND1_COST} = "
            f"${leftover_if_land:.0f} leftover; 8-by-d6 extra ${extra_cost} "
            f"{'FITS' if leftover_if_land - LAND_FLOOR >= extra_cost else 'DOES NOT FIT'} "
            f"(need leftover-floor >= extra, i.e. "
            f"{leftover_if_land - LAND_FLOOR:.0f} vs {extra_cost})"
        )
    print(
        f"  EOD d6 cash ${eod_cash:.0f} vs extra ${extra_cost} + floor "
        f"${LAND_FLOOR}: "
        f"{'could buy next morning' if eod_cash >= extra_cost + 50 else 'still short overnight'}"
    )

    print("\n--- d6 executed $ / units (us vs v20) ---")
    d6_cats = (
        "SELL_WOOL", "SELL_FERTILIZER", "SELL_WHEAT", "SELL_MILK",
        "BUY_LAND", "BUY_ANIMAL_COW", "BUY_ANIMAL_SHEEP",
        "BUY_SEED_STRAWBERRY", "BUY_PRODUCT_WHEAT", "BUY_PRODUCT_FERTILIZER",
        "HIRE",
    )
    print(f"  {'cat':<24} {'$us':>8} {'$v20':>8} {'gap$':>8}  {'u us':>5} {'u v20':>6}")
    in_us = in_v20 = out_us = out_v20 = 0.0
    for cat in d6_cats:
        a = _usd(cash, "us", 6, cat)
        b = _usd(cash, "v20", 6, cat)
        ua = _units(cash, "us", 6, cat)
        ub = _units(cash, "v20", 6, cat)
        if a == 0 and b == 0 and ua == 0 and ub == 0:
            continue
        print(f"  {cat:<24} {a:8.0f} {b:8.0f} {a - b:8.0f}  {ua:5.0f} {ub:6.0f}")
        if cat.startswith("SELL_"):
            in_us += a
            in_v20 += b
        else:
            out_us += a
            out_v20 += b
    d5e = rep["eod"][0].get(5, {})
    d5v = rep["eod"][1].get(5, {})
    d6v = rep["eod"][1].get(6, {})
    print(f"  {'d6 SELL total':<24} {in_us:8.0f} {in_v20:8.0f} {in_us - in_v20:8.0f}")
    print(f"  {'d6 spend total':<24} {out_us:8.0f} {out_v20:8.0f} {out_us - out_v20:8.0f}")
    print(
        f"  EOD d5->d6 us ${d5e.get('money', 0):.0f}->{eod_cash:.0f} "
        f"(net {eod_cash - d5e.get('money', 0):+.0f})  "
        f"v20 ${d5v.get('money', 0):.0f}->{d6v.get('money', 0):.0f} "
        f"(net {d6v.get('money', 0) - d5v.get('money', 0):+.0f})"
    )
    print(
        "  identity: v20 leftover is wool/fert minus land, no extra animal; "
        "us delays land then spends deferred cow + seed/wheat."
    )

    print("\n--- d9-d10 S4 window (EOD) ---")
    print(
        f"  {'day':>3} {'$us':>7} {'$v20':>7} {'herd':>7} {'pens':>5} "
        f"{'melonF':>6} {'heldM':>6} {'SELL_M $':>16} {'BUY_A':>12} "
        f"{'HIRE':>8} {'maxH':>7} {'wheatF':>7} {'shedW':>5}"
    )
    for day in range(9, 13):
        u = rep["eod"][0].get(day, {})
        v = rep["eod"][1].get(day, {})
        bu = "+".join(
            f"{sp}{n}" for sp, n in sorted(rep["buys"][0][day].items()) if n
        ) or "-"
        sm_u = _usd(cash, "us", day, "SELL_MELON")
        sm_v = _usd(cash, "v20", day, "SELL_MELON")
        print(
            f"  {day:3d} {u.get('money', 0):7.0f} {v.get('money', 0):7.0f} "
            f"{u.get('owned', 0):2d}/{v.get('owned', 0):<2d}  "
            f"{u.get('pens', 0):2d}/{v.get('pens', 0):<2d} "
            f"{u.get('melon', 0):3d}/{v.get('melon', 0):<2d} "
            f"{u.get('held_melon', 0):5d} "
            f"{sm_u:7.0f}/{sm_v:<7.0f}  {bu:<12} "
            f"{rep['hires'][0][day]:2d}/{rep['hires'][1][day]:<2d} "
            f"{rep['max_hands'][0][day]:2d}/{rep['max_hands'][1][day]:<2d} "
            f"{u.get('wheat', 0):3d}/{v.get('wheat', 0):<2d} "
            f"{u.get('shed_wheat', 0):5d}"
        )

    print("\n--- d9-d10 selected hours (us) ---")
    print(
        f"  {'d':>2} {'h':>3} {'$':>6} {'own/pl':>7} {'melonF':>6} "
        f"{'heldM':>5} {'shedM':>5} {'shedW':>5} buyA hire land"
    )
    for r in rep["d9_d10_hours"]:
        bu = "+".join(f"{sp}{n}" for sp, n in r["buy_a"]) if r["buy_a"] else "-"
        print(
            f"  {r['day']:2d} {r['hour']:3d} {r['money']:6.0f} "
            f"{r['owned']:2d}/{r['placed']:<2d} {r['melon']:6d} "
            f"{r['held_melon']:5d} {r['shed_melon']:5d} {r['shed_wheat']:5d} "
            f"{bu:<8} {r['hire']:3d} {int(r['land'])}"
        )

    print("\n--- BUY_ANIMAL by day (us / v20 order qty) ---")
    print(f"  {'day':>3}  {'us':<20} {'v20':<20}  {'herd us/v20':>12}  tape")
    tape = {0: 4, 2: 5, 3: 6, 6: 8, 7: 10, 8: 12, 9: 13, 10: 14}
    for day in range(30):
        bu = dict(rep["buys"][0][day])
        bv = dict(rep["buys"][1][day])
        if not bu and not bv:
            continue
        su = "+".join(f"{sp}{n}" for sp, n in sorted(bu.items()) if n) or "-"
        sv = "+".join(f"{sp}{n}" for sp, n in sorted(bv.items()) if n) or "-"
        u = rep["eod"][0].get(day, {})
        v = rep["eod"][1].get(day, {})
        t = tape.get(day, "")
        print(
            f"  {day:3d}  {su:<20} {sv:<20}  "
            f"{u.get('owned', '-'):>3}/{v.get('owned', '-'):<3}  {t}"
        )

    print("\n--- crew (hires / max hands) d0-d12 ---")
    print(f"  {'day':>3}  {'HIRE us/v20':>12}  {'maxH us/v20':>12}")
    for day in range(0, 13):
        print(
            f"  {day:3d}  {rep['hires'][0][day]:3d}/{rep['hires'][1][day]:<3d}      "
            f"{rep['max_hands'][0][day]:3d}/{rep['max_hands'][1][day]:<3d}"
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
    print(
        f"  d0 4/4 check owned={rep['eod'][0].get(0, {}).get('owned')} "
        f"placed={rep['eod'][0].get(0, {}).get('placed')} "
        f"wheatF={rep['eod'][0].get(0, {}).get('wheat')} "
        f"melonF={rep['eod'][0].get(0, {}).get('melon')}"
    )


def main():
    args = sys.argv[1:]
    seeds = [int(x) for x in args if x.lstrip("-").isdigit()] or [0, 8]
    for seed in seeds:
        print(f"running S3roles seed {seed}...", flush=True)
        print_seed(run_seed(seed, agent=S3ROLES))


if __name__ == "__main__":
    main()
