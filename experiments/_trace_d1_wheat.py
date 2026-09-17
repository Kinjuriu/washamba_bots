"""HORIZON S4-lead d0 leftover vs d1 buy/fill/pickup vs route_v20.

Snapshot before a d1-wheat fact. Engine BUY_PRODUCT is unit-by-unit;
money < first-unit price aborts the rest (kaggriculture.py _commit_unit).

Usage:
    .venv/Scripts/python.exe experiments/_trace_d1_wheat.py
    .venv/Scripts/python.exe experiments/_trace_d1_wheat.py 0 8
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

from kaggle_environments import make
from kaggle_environments.envs.kaggriculture.kaggriculture import market_price

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import V20, _obs  # noqa: E402

S4_LEAD = ROOT / "experiments" / "_facts_v20_s4_lead.py"


def _act(raw):
    return (raw.get("action") if hasattr(raw, "get") else None) or getattr(
        raw, "action", None
    ) or {}


def _unit_actions(act):
    farmer = act.get("farmer") or ["PASS"]
    hands = act.get("hands") or []
    if not isinstance(hands, list):
        hands = []
    return [farmer, *hands]


def _wheat_held(priv):
    shed = int((priv.get("shed") or {}).get("WHEAT", 0) or 0)
    carried = 0
    for inv in priv.get("inventories") or []:
        if isinstance(inv, dict):
            carried += int(inv.get("WHEAT", 0) or 0)
    return shed, carried, shed + carried


def _buy_price(obs):
    market = obs.get("market") or {}
    inv = (market.get("inventory") or {}).get("WHEAT", 10000)
    params = market.get("params")
    return float(market_price("WHEAT", inv - 1, params))


def _afford(money, price):
    if price <= 0:
        return 0
    return int(money // price)


def _orders(act, op, item=None):
    out = []
    for o in act.get("market") or []:
        if not o:
            continue
        if o[0] != op:
            continue
        if item is not None and (len(o) < 2 or o[1] != item):
            continue
        qty = int(o[2]) if len(o) > 2 else 1
        out.append(qty)
    return out


def _unit_qty(actions, op, item=None):
    n = 0
    q = 0
    for a in actions:
        if not a or a[0] != op:
            continue
        if item is not None and (len(a) < 2 or a[1] != item):
            continue
        n += 1
        q += int(a[2]) if len(a) > 2 else 1
    return n, q


def print_seed(rep):
    print("\n" + "#" * 92)
    print(
        f"# HORIZON D1 WHEAT  agent={rep['agent']}  seed={rep['seed']}  "
        f"bank us={rep['bank_us']:.0f}  v20={rep['bank_v20']:.0f}"
    )
    print("#" * 92)
    for p, label in ((0, "us"), (1, "v20")):
        rows = rep["hours"][p]
        print(f"\n--- {label} ---")
        print(
            f"  {'d':>2} {'h':>2} {'$':>5} {'px':>5} {'aff':>3} "
            f"{'shed':>4} {'car':>3} {'held':>4} "
            f"{'buyQ':>4} {'fill':>4} {'pkN':>3} {'pkQ':>3} "
            f"{'FEED':>4} {'sell':>4}  note"
        )
        d0_eod = None
        d1_h0 = None
        for r in rows:
            note = []
            if r["buy_q"]:
                note.append(f"BUY×{r['buy_q']}")
            if r["fill"] == 0 and r["buy_q"] > 0:
                note.append("NO-OP")
            if r["fill"] and r["fill"] < r["buy_q"]:
                note.append(f"partial {r['fill']}/{r['buy_q']}")
            if r["feed"]:
                note.append(f"FEED {r['feed']}")
            if r["pickup_n"]:
                note.append(f"PK {r['pickup_q']}")
            if r["sell_q"]:
                note.append(f"SELL {r['sell_q']}")
            if r["day"] == 0 and r["hour"] == 23:
                d0_eod = r
            if r["day"] == 1 and r["hour"] == 0:
                d1_h0 = r
            interesting = (
                r["hour"] in (0, 23)
                or r["buy_q"]
                or r["fill"]
                or r["pickup_n"]
                or r["feed"]
                or r["sell_q"]
                or (r["day"] == 1 and r["held"] != (rows[r["_idx"] - 1]["held"] if r["_idx"] else -1))
            )
            if not interesting:
                continue
            print(
                f"  {r['day']:2d} {r['hour']:2d} {r['money']:5.0f} {r['px']:5.1f} {r['aff']:3d} "
                f"{r['shed']:4d} {r['carried']:3d} {r['held']:4d} "
                f"{r['buy_q']:4d} {r['fill']:4d} {r['pickup_n']:3d} {r['pickup_q']:3d} "
                f"{r['feed']:4d} {r['sell_q']:4d}  {' '.join(note)}"
            )
        print(
            f"  d0 EOD held={d0_eod['held'] if d0_eod else '?'} "
            f"$={d0_eod['money'] if d0_eod else '?'}  "
            f"d1h0 held={d1_h0['held'] if d1_h0 else '?'} "
            f"$={d1_h0['money'] if d1_h0 else '?'} "
            f"px={d1_h0['px'] if d1_h0 else '?'} "
            f"aff={d1_h0['aff'] if d1_h0 else '?'} "
            f"buy={d1_h0['buy_q'] if d1_h0 else '?'} "
            f"fill={d1_h0['fill'] if d1_h0 else '?'}"
        )
        first_feed_d1 = next((r for r in rows if r["day"] == 1 and r["feed"]), None)
        first_shed_d1 = next((r for r in rows if r["day"] == 1 and r["shed"] > 0), None)
        print(
            f"  d1 first shed>0 h={first_shed_d1['hour'] if first_shed_d1 else 'never'}  "
            f"d1 first FEED h={first_feed_d1['hour'] if first_feed_d1 else 'never'} "
            f"qty={first_feed_d1['feed'] if first_feed_d1 else 0}"
        )
        d1_feed = sum(r["feed"] for r in rows if r["day"] == 1)
        d1_buy = sum(r["buy_q"] for r in rows if r["day"] == 1)
        d1_fill = sum(r["fill"] for r in rows if r["day"] == 1)
        d0_buy = sum(r["buy_q"] for r in rows if r["day"] == 0)
        d0_fill = sum(r["fill"] for r in rows if r["day"] == 0)
        d0_feed = sum(r["feed"] for r in rows if r["day"] == 0)
        print(
            f"  totals d0 buy/fill/FEED={d0_buy}/{d0_fill}/{d0_feed}  "
            f"d1 buy/fill/FEED={d1_buy}/{d1_fill}/{d1_feed}"
        )
        print("  d0 market after h10 (cash $114 → $24):")
        for r in rows:
            if r["day"] != 0 or r["hour"] < 10 or not r.get("market"):
                continue
            print(f"    h{r['hour']:02d} ${r['money']:.0f}→{r['money_after']:.0f} {r['market']}")


def run_seed(seed, agent=S4_LEAD):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([str(agent), V20])
    steps = env.steps
    hours = [[], []]
    extras = [{
        "plant_wheat": defaultdict(int),
        "plant_melon": defaultdict(int),
        "escapes": 0,
        "land_day": None,
        "d1_sheep_feed": set(),
        "d6h0_yield": [],
        "ne_straw_d6": 0,
    } for _ in range(2)]
    prev = [None, None]
    idx = [0, 0]
    for step in steps:
        obs_list = [_obs(step[p].observation) for p in (0, 1)]
        acts = [_act(step[p]) for p in (0, 1)]
        if prev[0] is None:
            prev = obs_list
            continue
        src = prev
        day = int(src[0].get("day", 0))
        hour = int(src[0].get("hour", 0))
        nxt_day = int(obs_list[0].get("day", 0))
        if day > 6:
            break
        for p in (0, 1):
            farm = (src[p].get("farms") or [{}])[p]
            farm_after = (obs_list[p].get("farms") or [{}])[p]
            priv = src[p].get("private") or {}
            priv_after = obs_list[p].get("private") or {}
            act = acts[p]
            actions = _unit_actions(act)
            if day <= 1:
                money = float(farm.get("money", 0) or 0)
                px = _buy_price(src[p])
                shed, carried, held = _wheat_held(priv)
                shed_a, carried_a, held_a = _wheat_held(priv_after)
                buy_q = sum(_orders(act, "BUY_PRODUCT", "WHEAT"))
                sell_q = sum(_orders(act, "SELL", "WHEAT"))
                pickup_n, pickup_q = _unit_qty(actions, "PICKUP", "WHEAT")
                feed_n, _ = _unit_qty(actions, "FEED")
                drop_n, drop_q = _unit_qty(actions, "DROP", "WHEAT")
                fill = max(0, shed_a - shed + pickup_q - drop_q)
                if buy_q == 0:
                    fill = 0
                else:
                    fill = min(buy_q, fill)
                mk = []
                for o in act.get("market") or []:
                    if o:
                        mk.append(tuple(o[:3] if len(o) >= 3 else o))
                hours[p].append({
                    "_idx": idx[p],
                    "day": day,
                    "hour": hour,
                    "money": money,
                    "px": px,
                    "aff": _afford(money, px),
                    "shed": shed,
                    "carried": carried,
                    "held": held,
                    "held_after": held_a,
                    "buy_q": buy_q,
                    "fill": fill,
                    "pickup_n": pickup_n,
                    "pickup_q": pickup_q,
                    "feed": feed_n,
                    "sell_q": sell_q,
                    "money_after": float(farm_after.get("money", 0) or 0),
                    "market": mk,
                })
                idx[p] += 1
            extras[p]["plant_wheat"][day] += sum(
                1 for a in actions
                if a and a[0] == "PLANT" and len(a) > 1 and a[1] == "WHEAT"
            )
            extras[p]["plant_melon"][day] += sum(
                1 for a in actions
                if a and a[0] == "PLANT" and len(a) > 1 and a[1] == "MELON"
            )
            extras[p]["escapes"] = max(
                extras[p]["escapes"],
                sum(
                    1 for row in (farm.get("tiles") or [])
                    for t in row
                    if isinstance(t, dict) and t.get("kind") == "ESCAPED"
                ),
            )
            for o in act.get("market") or []:
                if o and o[0] == "BUY_LAND" and extras[p]["land_day"] is None:
                    extras[p]["land_day"] = day
            sheep = []
            board = len(farm.get("tiles") or []) or 10
            half = board // 2
            ne_straw = 0
            for y, row in enumerate(farm.get("tiles") or []):
                for x, t in enumerate(row):
                    if not isinstance(t, dict):
                        continue
                    if t.get("animal") == "SHEEP":
                        sheep.append((x, y, t))
                    if (
                        t.get("kind") == "PLANT"
                        and t.get("crop") == "STRAWBERRY"
                        and y < half
                        and x >= half
                    ):
                        ne_straw += 1
            farmer = farm.get("farmer") or [0, 0]
            spots = [(int(farmer[0]), int(farmer[1]))]
            for hand in farm.get("hands") or []:
                if isinstance(hand, (list, tuple)) and len(hand) == 2:
                    spots.append((int(hand[0]), int(hand[1])))
            if day == 1:
                for i, a in enumerate(actions):
                    if a and a[0] == "FEED" and i < len(spots):
                        ux, uy = spots[i]
                        for sx, sy, _ in sheep:
                            if (ux, uy) == (sx, sy):
                                extras[p]["d1_sheep_feed"].add((sx, sy))
            if day == 6 and hour == 0:
                extras[p]["d6h0_yield"] = [
                    (xy, int(t.get("yield_units", 0) or 0))
                    for xy, t in (((x, y), t) for x, y, t in sheep)
                ]
            if day == 6 and hour == 23:
                extras[p]["ne_straw_d6"] = ne_straw
        prev = obs_list
    return {
        "agent": Path(agent).name,
        "seed": seed,
        "bank_us": steps[-1][0].reward,
        "bank_v20": steps[-1][1].reward,
        "hours": hours,
        "extras": extras,
    }


def print_compare(rep):
    print("\n--- drawer ---")
    for p, label in ((0, "us"), (1, "v20")):
        rows = [r for r in rep["hours"][p] if r["day"] == 1 and r["hour"] == 0]
        r = rows[0] if rows else None
        if not r:
            print(f"  {label} missing d1h0")
            continue
        can4 = r["aff"] >= 4
        can1 = r["aff"] >= 1
        leftover = r["held"]
        print(
            f"  {label} d1h0 ${r['money']:.0f} px={r['px']:.1f} aff={r['aff']} "
            f"held={leftover} buy={r['buy_q']} fill={r['fill']} "
            f"can_buy_1={can1} can_buy_4={can4}"
        )
    us = next(r for r in rep["hours"][0] if r["day"] == 1 and r["hour"] == 0)
    ex = rep["extras"][0]
    ys = [y for _, y in ex["d6h0_yield"]]
    print(
        f"  us leftover d1h0 held={us['held']}  d0 PLANT WHEAT={ex['plant_wheat'][0]} "
        f"MELON={ex['plant_melon'][0]}  d1 sheep FEED {sorted(ex['d1_sheep_feed'])} "
        f"n={len(ex['d1_sheep_feed'])}  d6h0 yield {ys} sum={sum(ys)}  "
        f"land={ex['land_day']} NE_STRAW_d6={ex['ne_straw_d6']} "
        f"escapes={ex['escapes']} bank={rep['bank_us']:.0f} "
        f"(base 67325/72410)"
    )
    if us["held"] < 2:
        print("  FAIL leftover < 2")
    if len(ex["d1_sheep_feed"]) < 2:
        print("  FAIL d1 FEED both sheep")
    if ex["plant_wheat"][0] < 4:
        print("  FAIL d0 PLANT WHEAT outside ±3 of 7")
    if ex["land_day"] != 6:
        print("  FAIL land not d6")
    if ex["ne_straw_d6"] <= 0:
        print("  FAIL NE STRAW EOD d6")
    if ex["escapes"]:
        print("  FAIL escapes")
    if rep["bank_us"] < (67325 if rep["seed"] == 0 else 72410):
        print("  FAIL bank down")


def main():
    args = sys.argv[1:]
    seeds = [int(x) for x in args if x.lstrip("-").isdigit()] or [0, 8]
    paths = [x for x in args if not x.lstrip("-").isdigit()]
    agent = Path(paths[0]) if paths else S4_LEAD
    if not agent.is_absolute():
        agent = (ROOT / agent).resolve() if not agent.exists() else agent.resolve()
    for seed in seeds:
        print(f"running {agent.name} seed {seed}...", flush=True)
        rep = run_seed(seed, agent=agent)
        print_seed(rep)
        print_compare(rep)


if __name__ == "__main__":
    main()
