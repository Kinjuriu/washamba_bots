"""HORIZON S4-lead branch-window snapshot vs route_v20.

Shops, C/S mix, opponent goose, egg shops at EOD d11 / d13 / d29.
Headcount stays 14. Names, not mix code.

Usage:
    .venv/Scripts/python.exe experiments/_trace_horizon_s4_lead.py
    .venv/Scripts/python.exe experiments/_trace_horizon_s4_lead.py 0 8
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
EGG_SHOPS = {"BAKERY", "BRUNCH_SPOT"}
MILK_SHOPS = {"PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"}
OWNED_CAP = 14


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


def _owned_mix(private, placed):
    counts = Counter()
    for k in ANIMAL_KEYS:
        counts[k] = int(placed.get(k, 0) or 0)
    shed = private.get("shed") or {}
    for k in ANIMAL_KEYS:
        counts[k] += int(shed.get(k, 0) or 0)
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            for k in ANIMAL_KEYS:
                counts[k] += int(inv.get(k, 0) or 0)
    return counts


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


def _route_label(shops):
    shops = list(shops or [])
    first3 = shops[:3]
    if shops[:1] == ["YARN_STORE"] or "YARN_STORE" in shops[:2]:
        return "yarn-first 6c12s", {"COW": 6, "SHEEP": 12}, first3
    if "YARN_STORE" in shops[:3]:
        return "yarn-in-3 6c8s", {"COW": 6, "SHEEP": 8}, first3
    if MILK_SHOPS.intersection(first3):
        return "milk 10c4s", {"COW": 10, "SHEEP": 4}, first3
    return "default 8c6s", {"COW": 8, "SHEEP": 6}, first3


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
    buys = [defaultdict(Counter), defaultdict(Counter)]
    plants = [defaultdict(Counter), defaultdict(Counter)]
    hires = [Counter(), Counter()]
    max_hands = [Counter(), Counter()]
    escapes = [0, 0]
    d11_hours = []
    d13_hours = []

    for step in steps:
        for p in (0, 1):
            obs = _obs(step[p].observation)
            act = step[p].action or {}
            day = int(obs.get("day", 0))
            hour = int(obs.get("hour", 0))
            farm = (obs.get("farms") or [{}])[p]
            priv = obs.get("private") or {}
            town = obs.get("town") or {}
            shops = list(town.get("unlocked_shops") or [])
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
            mix = _owned_mix(priv, placed)
            owned = sum(mix.values())
            label, target, first3 = _route_label(shops)
            row = {
                "money": float(farm.get("money", 0)),
                "placed": sum(placed.values()),
                "owned": owned,
                "cows": mix["COW"],
                "sheep": mix["SHEEP"],
                "geese": mix["GOOSE"],
                "placed_cows": placed["COW"],
                "placed_sheep": placed["SHEEP"],
                "placed_geese": placed["GOOSE"],
                "pens": pens,
                "wheat": wheat,
                "straw": straw,
                "melon": melon,
                "ne_empty": ne_empty,
                "ne_straw": ne_straw,
                "nw_straw": nw_straw,
                "unlocked": list(farm.get("unlocked_quadrants") or ["NW"]),
                "shops": shops,
                "first3": first3,
                "route": label,
                "mix_target": target,
                "egg_in_first3": bool(EGG_SHOPS.intersection(first3)),
                "shed_wheat": int((priv.get("shed") or {}).get("WHEAT", 0) or 0),
                "held_wheat": _held(priv, "WHEAT"),
                "shed_fert": int((priv.get("shed") or {}).get("FERTILIZER", 0) or 0),
                "hands": n_hands,
            }
            if hour == 23:
                eod[p][day] = row
            if p == 0 and day == 11 and (
                hour in (0, 1, 11, 15, 16, 20, 23) or land_now or buy_a
            ):
                d11_hours.append({
                    "hour": hour,
                    **row,
                    "buy_a": buy_a,
                    "land": land_now,
                })
            if p == 0 and day == 13 and (hour in (0, 1, 8, 12, 16, 23) or buy_a):
                d13_hours.append({
                    "hour": hour,
                    **row,
                    "buy_a": buy_a,
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
        "d11_hours": d11_hours,
        "d13_hours": d13_hours,
    }


def _usd(cash, seat_key, day, cat):
    src = cash["by_day_us"] if seat_key == "us" else cash["by_day_v20"]
    return src[day].get(cat, 0)


def _fmt_mix(row):
    return (
        f"{row.get('cows', 0)}C{row.get('sheep', 0)}S"
        f"{row.get('geese', 0)}G"
    )


def _fmt_buys(day_buys):
    bu = dict(day_buys)
    if not bu:
        return "-"
    return "+".join(f"{sp}{n}" for sp, n in sorted(bu.items()) if n) or "-"


def print_seed(rep):
    seed = rep["seed"]
    cash = rep["cash"]
    u0 = rep["eod"][0]
    v0 = rep["eod"][1]
    print("\n" + "#" * 88)
    print(
        f"# HORIZON S4-lead branch  seed={seed}  seat=0  "
        f"bank us={cash['bank_us']:.0f}  v20={cash['bank_v20']:.0f}  "
        f"escapes us={rep['escapes'][0]} v20={rep['escapes'][1]}"
    )
    print("#" * 88)
    print(f"  BUY_LAND us={rep['land'][0]}  v20={rep['land'][1]}")

    print("\n--- S0 / S3ne pictures (EOD us) ---")
    for day in (0, 5, 6, 10):
        u = u0.get(day, {})
        print(
            f"  d{day} ${u.get('money', 0):.0f} owned={u.get('owned')} "
            f"placed={u.get('placed')} {_fmt_mix(u)} pens={u.get('pens')} "
            f"straw={u.get('straw')} melon={u.get('melon')} "
            f"NE straw={u.get('ne_straw')} land={'+'.join(u.get('unlocked') or [])}"
        )

    print("\n--- BUY_ANIMAL by day (us / v20) ---")
    print(f"  {'day':>3}  {'us':<22} {'v20':<22}  herd us  mix us")
    for day in range(30):
        bu = dict(rep["buys"][0][day])
        bv = dict(rep["buys"][1][day])
        if not bu and not bv:
            continue
        u = u0.get(day, {})
        print(
            f"  {day:3d}  {_fmt_buys(bu):<22} {_fmt_buys(bv):<22}  "
            f"{u.get('owned', '-'):>3}/{u.get('placed', '-'):<3}  {_fmt_mix(u)}"
        )

    print("\n--- branch window EOD (us | v20) ---")
    print(
        f"  {'day':>3} {'$us':>7} {'own/pl/pn':>11} {'mix':>10} "
        f"{'route':<18} {'first3':<40} egg  oppG  shedW/F"
    )
    for day in (10, 11, 12, 13, 17, 29):
        u = u0.get(day, {})
        v = v0.get(day, {})
        first3 = ",".join(u.get("first3") or []) or "-"
        print(
            f"  {day:3d} {u.get('money', 0):7.0f} "
            f"{u.get('owned', 0):2d}/{u.get('placed', 0):<2d}/{u.get('pens', 0):<2d} "
            f"{_fmt_mix(u):>10} {u.get('route', '-'):<18} {first3:<40} "
            f"{int(u.get('egg_in_first3', False))}    "
            f"{v.get('geese', 0):3d}  "
            f"{u.get('shed_wheat', 0)}/{u.get('shed_fert', 0)}"
        )
        print(
            f"       v20 ${v.get('money', 0):.0f} "
            f"{v.get('owned', 0)}/{v.get('placed', 0)}/{v.get('pens', 0)} "
            f"{_fmt_mix(v)} route={v.get('route')} "
            f"first3={','.join(v.get('first3') or []) or '-'}"
        )

    print("\n--- d11 hours (us scale buy) ---")
    for r in rep["d11_hours"]:
        bu = "+".join(f"{sp}{n}" for sp, n in r["buy_a"]) if r["buy_a"] else "-"
        mark = " LAND2" if r["land"] else ""
        print(
            f"  h{r['hour']:02d} ${r['money']:.0f} {r['owned']}/{r['placed']} "
            f"{_fmt_mix(r)} pens={r['pens']} buy={bu} "
            f"shops={','.join((r.get('first3') or [])[:3])}{mark}"
        )

    print("\n--- d13 hours (us to 14) ---")
    for r in rep["d13_hours"]:
        bu = "+".join(f"{sp}{n}" for sp, n in r["buy_a"]) if r["buy_a"] else "-"
        print(
            f"  h{r['hour']:02d} ${r['money']:.0f} {r['owned']}/{r['placed']} "
            f"{_fmt_mix(r)} pens={r['pens']} buy={bu}"
        )

    d11 = u0.get(11, {})
    d13 = u0.get(13, {})
    d29 = u0.get(29, {})
    v13 = v0.get(13, {})
    v29 = v0.get(29, {})
    label, target, first3 = d13.get("route"), d13.get("mix_target") or {}, d13.get("first3") or []
    owned13 = int(d13.get("owned") or 0)
    cows13 = int(d13.get("cows") or 0)
    sheep13 = int(d13.get("sheep") or 0)
    geese13 = int(d13.get("geese") or 0)
    opp_g = int(v13.get("geese") or 0)
    egg = bool(d13.get("egg_in_first3"))
    target_total = int(target.get("COW", 0)) + int(target.get("SHEEP", 0))

    print("\n--- named branch fund check (owned cap 14) ---")
    print(f"  first3 as of EOD d13: {first3 or '-'}  label={label}")
    print(
        f"  mix EOD d11 {_fmt_mix(d11)} owned={d11.get('owned')} "
        f"pens={d11.get('pens')} ${d11.get('money', 0):.0f}"
    )
    print(
        f"  mix EOD d13 {_fmt_mix(d13)} owned={owned13} "
        f"pens={d13.get('pens')} ${d13.get('money', 0):.0f}"
    )
    print(
        f"  mix EOD d29 {_fmt_mix(d29)} owned={d29.get('owned')} "
        f"placed={d29.get('placed')} pens={d29.get('pens')}"
    )
    print(
        f"  shop_mix_target raw={target} total={target_total} "
        f"(>14 cannot land without raising the buy cap)"
    )
    print(
        f"  actual vs 10c4s: {cows13}C{sheep13}S "
        f"{'LANDS' if (cows13, sheep13) == (10, 4) else 'does not land'}"
    )
    print(
        f"  actual vs 6c8s: {cows13}C{sheep13}S "
        f"{'LANDS' if (cows13, sheep13) == (6, 8) else 'does not land'}"
    )
    print(
        f"  actual vs 6c12s: totals 18; at owned={owned13} "
        f"{'CANNOT FUND' if OWNED_CAP < 18 else 'fits'}"
    )
    print(
        f"  goose pair: egg_in_first3={int(egg)} opp_geese_d13={opp_g} "
        f"us_geese={geese13}  "
        f"{'FUNDED' if egg and opp_g == 0 else 'NOT FUNDED'}"
    )
    already = False
    if label == "milk 10c4s" and (cows13, sheep13) == (10, 4):
        already = True
        print("  existing shop_mix_target already landed milk 10c4s")
    elif label == "yarn-in-3 6c8s" and (cows13, sheep13) == (6, 8):
        already = True
        print("  existing shop_mix_target already landed yarn-in-3 6c8s")
    elif label == "default 8c6s" and (cows13, sheep13) == (8, 6):
        already = True
        print("  existing shop_mix_target already landed default 8c6s")
    elif label == "yarn-first 6c12s":
        print(
            "  yarn-first wants 6c12s (18). Do not raise owned. "
            "At 14 this is a truncated 6c12s, not a landed branch."
        )
    if already:
        print("  recoding this table is not a fact")

    print("\n--- season executed $ ---")
    cats = (
        "SELL_STRAWBERRY", "SELL_WOOL", "SELL_MELON", "SELL_WHEAT", "SELL_MILK",
        "BUY_PRODUCT_WHEAT", "BUY_ANIMAL_SHEEP", "BUY_ANIMAL_COW", "BUY_LAND",
    )
    print(f"  {'cat':<24} {'us':>10} {'v20':>10} {'gap':>10}")
    for cat in cats:
        a = cash["season_us"].get(cat, 0)
        b = cash["season_v20"].get(cat, 0)
        print(f"  {cat:<24} {a:10.0f} {b:10.0f} {a - b:10.0f}")
    print(
        f"  PLANT MELON after d0 us="
        f"{sum(v for d, v in rep['plants'][0]['MELON'].items() if d > 0)} "
        f"d0 4/4 owned={u0.get(0, {}).get('owned')} "
        f"placed={u0.get(0, {}).get('placed')} "
        f"d6 STRAW={u0.get(6, {}).get('straw')} NE={u0.get(6, {}).get('ne_straw')}"
    )
    print(
        f"  opp goose EOD d13={v13.get('geese', 0)} d29={v29.get('geese', 0)}"
    )


def main():
    args = sys.argv[1:]
    seeds = [int(x) for x in args if x.lstrip("-").isdigit()] or [0, 8]
    for seed in seeds:
        print(f"running S4-lead seed {seed}...", flush=True)
        print_seed(run_seed(seed, agent=S4_LEAD))


if __name__ == "__main__":
    main()
