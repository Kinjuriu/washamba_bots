"""HORIZON S4-lead d6 leftover snapshot vs route_v20.

Fill Actual at the leftover window before coding seed 10->~3 or wool 9->12.
Not a mix recode. Not 8-by-d6.

Prints, seeds 0 and 8, both seats:
  wool shed vs held, STRAW seed held, BUY_SEED STRAW hour/qty,
  cash at h5 vs land hour (pre/post), deferred cow emit, NE STRAW.

Usage:
    .venv/Scripts/python.exe experiments/_trace_horizon_s4_lead_d6.py
    .venv/Scripts/python.exe experiments/_trace_horizon_s4_lead_d6.py 0 8
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import V20, _obs, analyze_episode  # noqa: E402

S4_LEAD = str(ROOT / "experiments" / "_facts_v20_s4_lead.py")
ANIMAL_KEYS = ("COW", "SHEEP", "GOOSE")
LAND1_COST = 1000
LAND_FLOOR = 500


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


def _seed(private, crop):
    return int((private.get("seeds") or {}).get(crop, 0) or 0)


def _orders(market, kind, item=None):
    out = []
    for o in market or []:
        if not o or o[0] != kind:
            continue
        if item is not None and (len(o) < 2 or o[1] != item):
            continue
        qty = int(o[2] if len(o) > 2 else 1)
        name = o[1] if len(o) > 1 else None
        out.append((name, qty))
    return out


def _unit_ops(act, op, item=None):
    n = 0
    for a in _unit_actions(act):
        if not isinstance(a, list) or not a:
            continue
        if a[0] != op:
            continue
        if item is not None and (len(a) < 2 or a[1] != item):
            continue
        n += 1
    return n


def run_seed(seed, agent=S4_LEAD):
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
    cow_events = [[], []]
    straw_seed_buys = [[], []]
    wool_sells = [[], []]
    plants = [defaultdict(Counter), defaultdict(Counter)]
    escapes = [0, 0]
    d6_hours = [[], []]
    d5_hours = [[], []]
    d7_buys = [[], []]

    prev = [None, None]
    for step in steps:
        obs_list = [_obs(step[p].observation) for p in (0, 1)]
        acts = [step[p].action or {} for p in (0, 1)]
        if prev[0] is None:
            prev = obs_list
            continue
        src = prev
        day = int(src[0].get("day", 0))
        hour = int(src[0].get("hour", 0))

        for p in (0, 1):
            farm = (src[p].get("farms") or [{}])[p]
            priv = src[p].get("private") or {}
            farm_after = (obs_list[p].get("farms") or [{}])[p]
            priv_after = obs_list[p].get("private") or {}
            act = acts[p]
            market = act.get("market") or []

            placed, pens, escaped, wheat, straw, melon, ne_empty, ne_straw, nw_straw = (
                _tile_animals(farm)
            )
            escapes[p] = max(escapes[p], escaped)
            owned = _owned(farm, priv, placed)

            buy_a = _orders(market, "BUY_ANIMAL")
            land_now = bool(_orders(market, "BUY_LAND"))
            straw_buy = _orders(market, "BUY_SEED", "STRAWBERRY")
            wool_sell = _orders(market, "SELL", "WOOL")
            hire_n = sum(q for _, q in _orders(market, "HIRE") or [(None, 0)])
            if land_now:
                land_events[p].append((day, hour))
            for name, qty in buy_a:
                if name == "COW":
                    cow_events[p].append((day, hour, qty))
            if straw_buy:
                straw_seed_buys[p].append(
                    (day, hour, sum(q for _, q in straw_buy))
                )
            if wool_sell:
                wool_sells[p].append((day, hour, sum(q for _, q in wool_sell)))
            for a in _unit_actions(act):
                if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT":
                    plants[p][a[1]][day] += 1

            row = {
                "day": day,
                "hour": hour,
                "pre": float(farm.get("money", 0)),
                "post": float(farm_after.get("money", 0)),
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
                "unlocked_after": list(farm_after.get("unlocked_quadrants") or ["NW"]),
                "shed_wheat": int((priv.get("shed") or {}).get("WHEAT", 0) or 0),
                "shed_wool": int((priv.get("shed") or {}).get("WOOL", 0) or 0),
                "held_wool": _held(priv, "WOOL"),
                "shed_wool_after": int((priv_after.get("shed") or {}).get("WOOL", 0) or 0),
                "held_wool_after": _held(priv_after, "WOOL"),
                "straw_seed": _seed(priv, "STRAWBERRY"),
                "straw_seed_after": _seed(priv_after, "STRAWBERRY"),
                "shed_fert": int((priv.get("shed") or {}).get("FERTILIZER", 0) or 0),
                "buy_a": buy_a,
                "land": land_now,
                "straw_buy": straw_buy,
                "wool_sell": wool_sell,
                "hire": hire_n,
                "place_wool": _unit_ops(act, "PLACE", "WOOL"),
                "plant_straw": _unit_ops(act, "PLANT", "STRAWBERRY"),
            }
            if hour == 23:
                eod[p][day] = row
            if day == 6:
                d6_hours[p].append(row)
            if day == 5 and (
                hour in (0, 5, 10, 12, 16, 20, 23)
                or land_now
                or buy_a
                or straw_buy
                or wool_sell
            ):
                d5_hours[p].append(row)
            if day == 7 and buy_a:
                d7_buys[p].append((hour, buy_a, float(farm.get("money", 0))))

        prev = obs_list

    return {
        "seed": seed,
        "cash": cash,
        "eod": eod,
        "land": land_events,
        "cow": cow_events,
        "straw_seed_buys": straw_seed_buys,
        "wool_sells": wool_sells,
        "plants": plants,
        "escapes": escapes,
        "d6_hours": d6_hours,
        "d5_hours": d5_hours,
        "d7_buys": d7_buys,
    }


def _usd(cash, seat_key, day, cat):
    src = cash["by_day_us"] if seat_key == "us" else cash["by_day_v20"]
    return src[day].get(cat, 0)


def _units(cash, seat_key, day, cat):
    key = "by_day_units_us" if seat_key == "us" else "by_day_units_v20"
    src = cash.get(key) or {}
    return src.get(day, {}).get(cat, 0)


def _first(events):
    return events[0] if events else None


def _print_d6_table(label, rows):
    print(f"\n--- d6 hourly {label} ---")
    print(
        f"  {'h':>3} {'pre':>6} {'post':>6} {'own/pl':>7} "
        f"{'woolS/H':>8} {'sSeed':>5} {'neE/S':>6} "
        f"land seedA cow sellW plantS unlocked"
    )
    for r in rows:
        interesting = (
            r["hour"] in (0, 5, 10, 11, 12, 16, 20, 23)
            or r["land"]
            or r["buy_a"]
            or r["straw_buy"]
            or r["wool_sell"]
            or r["place_wool"]
            or r["plant_straw"]
        )
        if not interesting:
            continue
        bu = "+".join(f"{sp}{n}" for sp, n in r["buy_a"]) if r["buy_a"] else "-"
        sb = sum(q for _, q in r["straw_buy"]) if r["straw_buy"] else 0
        ws = sum(q for _, q in r["wool_sell"]) if r["wool_sell"] else 0
        mark = []
        if r["land"]:
            mark.append("LAND")
        if r["hour"] == 5:
            mark.append("H5")
        print(
            f"  {r['hour']:3d} {r['pre']:6.0f} {r['post']:6.0f} "
            f"{r['owned']:2d}/{r['placed']:<2d} "
            f"{r['shed_wool']:3d}/{r['held_wool']:<3d} "
            f"{r['straw_seed']:5d} "
            f"{r['ne_empty']:2d}/{r['ne_straw']:<2d} "
            f"{int(r['land']):4d} {sb:5d} {bu:<7} {ws:5d} {r['plant_straw']:6d} "
            f"{'+'.join(r['unlocked'])} {' '.join(mark)}"
        )
        if r["land"] or r["straw_buy"] or r["buy_a"] or r["wool_sell"]:
            print(
                f"       after $={r['post']:.0f} land={'+'.join(r['unlocked_after'])} "
                f"woolS/H {r['shed_wool_after']}/{r['held_wool_after']} "
                f"sSeed {r['straw_seed_after']} "
                f"placeWOOL={r['place_wool']} fert={r['shed_fert']}"
            )


def print_seed(rep):
    seed = rep["seed"]
    cash = rep["cash"]
    print("\n" + "#" * 88)
    print(
        f"# HORIZON S4-lead d6 leftover  seed={seed}  seat=0  "
        f"bank us={cash['bank_us']:.0f}  v20={cash['bank_v20']:.0f}  "
        f"escapes us={rep['escapes'][0]} v20={rep['escapes'][1]}"
    )
    print("#" * 88)
    print(
        f"  first BUY_LAND  us={_first(rep['land'][0])}  "
        f"v20={_first(rep['land'][1])}"
    )
    print(f"  all BUY_LAND us={rep['land'][0]}  v20={rep['land'][1]}")
    print(f"  BUY_ANIMAL COW us={rep['cow'][0] or 'none'}  v20={rep['cow'][1] or 'none'}")
    print(
        f"  BUY_SEED STRAW d0-8 us={[(d, h, q) for d, h, q in rep['straw_seed_buys'][0] if d <= 8]}"
    )
    print(
        f"  BUY_SEED STRAW d0-8 v20={[(d, h, q) for d, h, q in rep['straw_seed_buys'][1] if d <= 8]}"
    )
    print(
        f"  SELL WOOL d5-6 us={[(d, h, q) for d, h, q in rep['wool_sells'][0] if 5 <= d <= 6]}"
    )
    print(
        f"  SELL WOOL d5-6 v20={[(d, h, q) for d, h, q in rep['wool_sells'][1] if 5 <= d <= 6]}"
    )
    print(f"  d7 BUY_ANIMAL us={rep['d7_buys'][0] or 'none'}  v20={rep['d7_buys'][1] or 'none'}")

    print("\n--- EOD pictures d5-d7 ---")
    for day in (5, 6, 7):
        u = rep["eod"][0].get(day, {})
        v = rep["eod"][1].get(day, {})
        print(
            f"  d{day} us $={u.get('post', 0):7.0f} herd={u.get('owned', 0)}"
            f" placed={u.get('placed', 0)} {u.get('cows', 0)}C{u.get('sheep', 0)}S"
            f" strawF={u.get('straw', 0)} NE={u.get('ne_empty', '-')}/{u.get('ne_straw', '-')}"
            f" land={'+'.join(u.get('unlocked_after') or u.get('unlocked') or [])}"
            f" woolS/H={u.get('shed_wool', 0)}/{u.get('held_wool', 0)}"
            f" sSeed={u.get('straw_seed_after', u.get('straw_seed', 0))}"
            f"  | v20 $={v.get('post', 0):7.0f} herd={v.get('owned', 0)}"
            f" placed={v.get('placed', 0)} strawF={v.get('straw', 0)}"
            f" NE={v.get('ne_empty', '-')}/{v.get('ne_straw', '-')}"
            f" woolS/H={v.get('shed_wool', 0)}/{v.get('held_wool', 0)}"
            f" sSeed={v.get('straw_seed_after', v.get('straw_seed', 0))}"
        )
        print(
            f"       PLANT STRAW us={rep['plants'][0]['STRAWBERRY'].get(day, 0)}"
            f" v20={rep['plants'][1]['STRAWBERRY'].get(day, 0)}"
            f"  PLANT MELON us={rep['plants'][0]['MELON'].get(day, 0)}"
            f" v20={rep['plants'][1]['MELON'].get(day, 0)}"
        )

    print("\n--- d5 interesting (us) ---")
    for r in rep["d5_hours"][0]:
        bu = "+".join(f"{sp}{n}" for sp, n in r["buy_a"]) if r["buy_a"] else "-"
        sb = sum(q for _, q in r["straw_buy"]) if r["straw_buy"] else 0
        ws = sum(q for _, q in r["wool_sell"]) if r["wool_sell"] else 0
        print(
            f"  h{r['hour']:02d} pre={r['pre']:6.0f} post={r['post']:6.0f} "
            f"woolS/H {r['shed_wool']}/{r['held_wool']} "
            f"sSeed {r['straw_seed']}->{r['straw_seed_after']} "
            f"seedBuy={sb} cow={bu} sellW={ws} "
            f"NE {r['ne_empty']}/{r['ne_straw']}"
        )

    _print_d6_table("us", rep["d6_hours"][0])
    _print_d6_table("v20", rep["d6_hours"][1])

    print("\n--- land-hour / h5 cash (pre-action) ---")
    for seat, label in ((0, "us"), (1, "v20")):
        rows = rep["d6_hours"][seat]
        h5 = next((r for r in rows if r["hour"] == 5), None)
        land = next((r for r in rows if r["land"]), None)
        print(
            f"  {label} h5 pre=${h5['pre']:.0f} post=${h5['post']:.0f} "
            f"woolS/H {h5['shed_wool']}/{h5['held_wool']} sSeed={h5['straw_seed']}"
            if h5
            else f"  {label} h5 missing"
        )
        if land:
            leftover = land["pre"] - LAND1_COST
            print(
                f"  {label} LAND d6h{land['hour']} pre=${land['pre']:.0f} "
                f"post=${land['post']:.0f} "
                f"pre-1000=${leftover:.0f} "
                f"(floor ${LAND_FLOOR}: "
                f"{'holds' if leftover >= LAND_FLOOR else 'BREAKS'}) "
                f"woolS/H {land['shed_wool']}/{land['held_wool']} "
                f"sSeed={land['straw_seed']}->{land['straw_seed_after']} "
                f"seedBuy={sum(q for _, q in land['straw_buy']) if land['straw_buy'] else 0} "
                f"cow={land['buy_a'] or '-'} sellW={land['wool_sell'] or '-'}"
            )
        else:
            print(f"  {label} no d6 BUY_LAND")

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
    d6e = rep["eod"][0].get(6, {})
    d5v = rep["eod"][1].get(5, {})
    d6v = rep["eod"][1].get(6, {})
    print(f"  {'d6 SELL total':<24} {in_us:8.0f} {in_v20:8.0f} {in_us - in_v20:8.0f}")
    print(f"  {'d6 spend total':<24} {out_us:8.0f} {out_v20:8.0f} {out_us - out_v20:8.0f}")
    print(
        f"  EOD d5->d6 us ${d5e.get('post', 0):.0f}->{d6e.get('post', 0):.0f} "
        f"(net {d6e.get('post', 0) - d5e.get('post', 0):+.0f})  "
        f"v20 ${d5v.get('post', 0):.0f}->{d6v.get('post', 0):.0f} "
        f"(net {d6v.get('post', 0) - d5v.get('post', 0):+.0f})"
    )
    wool_gap = _usd(cash, "us", 6, "SELL_WOOL") - _usd(cash, "v20", 6, "SELL_WOOL")
    seed_gap = _usd(cash, "us", 6, "BUY_SEED_STRAWBERRY") - _usd(
        cash, "v20", 6, "BUY_SEED_STRAWBERRY"
    )
    cow_gap = _usd(cash, "us", 6, "BUY_ANIMAL_COW") - _usd(cash, "v20", 6, "BUY_ANIMAL_COW")
    print(
        f"  leftover identity gaps: wool ${wool_gap:.0f}  "
        f"STRAW seed ${-seed_gap:.0f} extra spend  "
        f"cow ${-cow_gap:.0f} extra spend"
    )
    d7u = rep["eod"][0].get(7, {})
    print(
        f"  d7 buy can exist? EOD d6 ${d6e.get('post', 0):.0f}  "
        f"EOD d7 ${d7u.get('post', 0):.0f} herd d6={d6e.get('owned')} "
        f"d7={d7u.get('owned')}  d7 BUY_ANIMAL={rep['d7_buys'][0] or 'none'}"
    )
    print(
        f"  NE STRAW EOD d6 us={d6e.get('ne_straw')} v20={d6v.get('ne_straw')}  "
        f"d0 melon plants us={rep['plants'][0]['MELON'].get(0, 0)} "
        f"after-d0={sum(rep['plants'][0]['MELON'].get(d, 0) for d in range(1, 30))}"
    )


def _agent_path(argv):
    for a in argv:
        p = Path(a)
        if p.suffix == ".py" and p.exists():
            return str(p.resolve())
        cand = ROOT / "experiments" / a
        if cand.suffix == ".py" and cand.exists():
            return str(cand.resolve())
    return S4_LEAD


def main():
    agent = _agent_path(sys.argv[1:])
    seeds = [int(x) for x in sys.argv[1:] if x.lstrip("-").isdigit()] or [0, 8]
    for seed in seeds:
        print(f"running {Path(agent).name} seed {seed}...", flush=True)
        print_seed(run_seed(seed, agent=agent))


if __name__ == "__main__":
    main()
