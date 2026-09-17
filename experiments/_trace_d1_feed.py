"""HORIZON S4-lead: which hours can hold wheat without extra h0 buy.

v20 leftover 3 is overnight product wheat after sells, then d1h18 x5
after more sales — not a morning BUY. Not leftover-2 at h0. Not d1h0 x4.
d0h15 BUY_SEED WHEAT x9 ($114->$24) is the spend that empties the trough.

Snapshot only. Do not edit the throwaway from this file.

Usage:
    .venv/Scripts/python.exe experiments/_trace_d1_feed.py
    .venv/Scripts/python.exe experiments/_trace_d1_feed.py 0 8
"""
from __future__ import annotations

import sys
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
    seed = int((priv.get("seeds") or {}).get("WHEAT", 0) or 0)
    return shed, carried, shed + carried, seed


def _buy_price(obs):
    market = obs.get("market") or {}
    inv = (market.get("inventory") or {}).get("WHEAT", 10000)
    params = market.get("params")
    return float(market_price("WHEAT", inv - 1, params))


def _afford(money, price):
    if price <= 0:
        return 0
    return int(money // price)


def _sum_orders(act, op, item=None):
    n = 0
    for o in act.get("market") or []:
        if not o or o[0] != op:
            continue
        if item is not None and (len(o) < 2 or o[1] != item):
            continue
        n += int(o[2]) if len(o) > 2 else 1
    return n


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


def _fmt_market(act):
    out = []
    for o in act.get("market") or []:
        if o:
            out.append(tuple(o[:3] if len(o) >= 3 else o))
    return out


def run_seed(seed, agent=S4_LEAD):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([str(agent), V20])
    steps = env.steps
    hours = [[], []]
    extras = [
        {
            "land_day": None,
            "d1_sheep_feed": set(),
            "d6h0_yield": [],
            "ne_straw_d6": 0,
            "escapes": 0,
            "plant_wheat_d0": 0,
        }
        for _ in range(2)
    ]
    prev = [None, None]
    for step in steps:
        obs_list = [_obs(step[p].observation) for p in (0, 1)]
        acts = [_act(step[p]) for p in (0, 1)]
        if prev[0] is None:
            prev = obs_list
            continue
        src = prev
        day = int(src[0].get("day", 0))
        hour = int(src[0].get("hour", 0))
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
                money_after = float(farm_after.get("money", 0) or 0)
                px = _buy_price(src[p])
                shed, carried, held, seed = _wheat_held(priv)
                shed_a, carried_a, held_a, seed_a = _wheat_held(priv_after)
                buy_q = _sum_orders(act, "BUY_PRODUCT", "WHEAT")
                buy_seed = _sum_orders(act, "BUY_SEED", "WHEAT")
                sell_q = _sum_orders(act, "SELL", "WHEAT")
                sell_fert = _sum_orders(act, "SELL", "FERTILIZER")
                pickup_n, pickup_q = _unit_qty(actions, "PICKUP", "WHEAT")
                drop_n, drop_q = _unit_qty(actions, "DROP", "WHEAT")
                feed_n, _ = _unit_qty(actions, "FEED")
                harv_n, harv_q = _unit_qty(actions, "HARVEST", "WHEAT")
                fill = 0
                if buy_q:
                    # Engine fills shed from BUY_PRODUCT; pickup/drop muddies
                    # the delta, so clip to the order.
                    fill = max(0, min(buy_q, shed_a - shed + pickup_q - drop_q))
                hours[p].append({
                    "day": day,
                    "hour": hour,
                    "money": money,
                    "money_after": money_after,
                    "px": px,
                    "aff": _afford(money, px),
                    "aff_after": _afford(money_after, px),
                    "shed": shed,
                    "carried": carried,
                    "held": held,
                    "held_after": held_a,
                    "seed": seed,
                    "seed_after": seed_a,
                    "buy_q": buy_q,
                    "fill": fill,
                    "buy_seed": buy_seed,
                    "sell_q": sell_q,
                    "sell_fert": sell_fert,
                    "pickup_q": pickup_q,
                    "drop_q": drop_q,
                    "feed": feed_n,
                    "harvest": harv_n,
                    "market": _fmt_market(act),
                })
            extras[p]["plant_wheat_d0"] += sum(
                1 for a in actions
                if day == 0 and a and a[0] == "PLANT" and len(a) > 1 and a[1] == "WHEAT"
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
                        sheep.append((x, y))
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
                        extras[p]["d1_sheep_feed"].add(spots[i])
            if day == 6 and hour == 0:
                extras[p]["d6h0_yield"] = [
                    int(t.get("yield_units", 0) or 0)
                    for row in (farm.get("tiles") or [])
                    for t in row
                    if isinstance(t, dict) and t.get("animal") == "SHEEP"
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


def _interesting(r, prev_held=None):
    return (
        r["hour"] in (0, 23)
        or r["buy_q"]
        or r["fill"]
        or r["buy_seed"]
        or r["sell_q"]
        or r["feed"]
        or r["harvest"]
        or r["sell_fert"]
        or r["held"] > 0
        or r["held_after"] > 0
        or r["aff"] >= 1
        or (prev_held is not None and r["held"] != prev_held)
    )


def print_hours(rep):
    print("\n" + "#" * 96)
    print(
        f"# D1 FEED HOURS  agent={rep['agent']}  seed={rep['seed']}  "
        f"bank us={rep['bank_us']:.0f}  v20={rep['bank_v20']:.0f}"
    )
    print("#" * 96)
    for p, label in ((0, "us"), (1, "v20")):
        rows = rep["hours"][p]
        print(f"\n--- {label} ---")
        print(
            f"  {'d':>1} {'h':>2} {'$':>5} {'$a':>5} {'px':>5} {'aff':>3} "
            f"{'held':>4} {'ha':>3} {'seed':>4} "
            f"{'bP':>3} {'fil':>3} {'bS':>3} {'sel':>3} "
            f"{'FEED':>4} {'HAR':>3}  note"
        )
        prev_held = None
        for r in rows:
            notes = []
            if r["buy_q"]:
                notes.append(f"BUY×{r['buy_q']}")
                if r["fill"] == 0:
                    notes.append("NO-OP")
                elif r["fill"] < r["buy_q"]:
                    notes.append(f"partial {r['fill']}/{r['buy_q']}")
            if r["buy_seed"]:
                notes.append(f"SEED×{r['buy_seed']}")
            if r["sell_q"]:
                notes.append(f"SELL×{r['sell_q']}")
            if r["sell_fert"]:
                notes.append(f"FERT×{r['sell_fert']}")
            if r["feed"]:
                notes.append(f"FEED {r['feed']}")
            if r["harvest"]:
                notes.append(f"HAR {r['harvest']}")
            if not _interesting(r, prev_held):
                prev_held = r["held"]
                continue
            print(
                f"  {r['day']:1d} {r['hour']:2d} {r['money']:5.0f} "
                f"{r['money_after']:5.0f} {r['px']:5.1f} {r['aff']:3d} "
                f"{r['held']:4d} {r['held_after']:3d} {r['seed']:4d} "
                f"{r['buy_q']:3d} {r['fill']:3d} {r['buy_seed']:3d} {r['sell_q']:3d} "
                f"{r['feed']:4d} {r['harvest']:3d}  {' '.join(notes)}"
            )
            prev_held = r["held"]


def print_payable(rep):
    print("\n--- payable product-wheat hours (aff>=1, no extra h0 buy) ---")
    for p, label in ((0, "us"), (1, "v20")):
        rows = rep["hours"][p]
        print(f"  {label}:")
        for r in rows:
            skip_h0_extra = r["day"] == 0 and r["hour"] == 0
            if r["aff"] < 1 and r["aff_after"] < 1:
                continue
            # Skip the opening buy hour itself — that is already owned=4.
            tag = "h0-open" if skip_h0_extra else "later"
            if r["buy_seed"]:
                recovered = r["money"]  # cash before seed spend
                recovered_aff = _afford(recovered, r["px"])
                tag += f" skip-seed would aff={recovered_aff} at ${recovered:.0f}"
            print(
                f"    d{r['day']}h{r['hour']:02d} ${r['money']:.0f}->${r['money_after']:.0f} "
                f"px={r['px']:.1f} aff={r['aff']}/{r['aff_after']} "
                f"held {r['held']}->{r['held_after']} "
                f"buyP={r['buy_q']} fill={r['fill']} seed={r['buy_seed']} "
                f"sell={r['sell_q']} FEED={r['feed']} {tag}"
            )
        overnight = next(
            (r for r in rows if r["day"] == 0 and r["hour"] == 23), None
        )
        d1h0 = next((r for r in rows if r["day"] == 1 and r["hour"] == 0), None)
        d1_feeds = [r for r in rows if r["day"] == 1 and r["feed"]]
        d1_buys = [r for r in rows if r["day"] == 1 and r["buy_q"]]
        d1_sells = [r for r in rows if r["day"] == 1 and r["sell_q"]]
        seed_spends = [r for r in rows if r["buy_seed"]]
        print(
            f"    overnight d0h23 held={overnight['held'] if overnight else '?'} "
            f"$={overnight['money'] if overnight else '?'}  "
            f"d1h0 held={d1h0['held'] if d1h0 else '?'} "
            f"$={d1h0['money'] if d1h0 else '?'} "
            f"px={d1h0['px'] if d1h0 else '?'} "
            f"aff={d1h0['aff'] if d1h0 else '?'}"
        )
        if seed_spends:
            for r in seed_spends:
                print(
                    f"    seed spend d{r['day']}h{r['hour']:02d} "
                    f"${r['money']:.0f}->${r['money_after']:.0f} "
                    f"SEED×{r['buy_seed']}  market={r['market']}"
                )
        print(
            f"    d1 FEED hours={[f'h{r['hour']}:n{r['feed']}' for r in d1_feeds] or 'none'}  "
            f"d1 BUY_PRODUCT={[f'h{r['hour']}×{r['buy_q']} fill={r['fill']}' for r in d1_buys] or 'none'}  "
            f"d1 SELL_WHEAT={[f'h{r['hour']}×{r['sell_q']}' for r in d1_sells] or 'none'}"
        )


def print_gap(rep):
    us = rep["hours"][0]
    v20 = rep["hours"][1]
    ex = rep["extras"][0]
    us_d1h0 = next(r for r in us if r["day"] == 1 and r["hour"] == 0)
    v20_d1h0 = next(r for r in v20 if r["day"] == 1 and r["hour"] == 0)
    us_d0h23 = next(r for r in us if r["day"] == 0 and r["hour"] == 23)
    v20_d0h23 = next(r for r in v20 if r["day"] == 0 and r["hour"] == 23)
    # Hours after d0h0 where us aff>=1 without counting the opening buy.
    us_later = [
        r for r in us
        if not (r["day"] == 0 and r["hour"] == 0) and r["aff"] >= 1
    ]
    us_later_aff4 = [r for r in us_later if r["aff"] >= 4]
    us_seed = [r for r in us if r["buy_seed"]]
    v20_buys = [r for r in v20 if r["buy_q"]]
    v20_sells = [r for r in v20 if r["sell_q"]]
    ys = ex["d6h0_yield"]
    print("\n--- gap ---")
    print(
        f"  us overnight held={us_d0h23['held']} ${us_d0h23['money']:.0f}  "
        f"d1h0 held={us_d1h0['held']} ${us_d1h0['money']:.0f} "
        f"px={us_d1h0['px']:.1f} aff={us_d1h0['aff']} "
        f"buy={us_d1h0['buy_q']} fill={us_d1h0['fill']}"
    )
    print(
        f"  v20 overnight held={v20_d0h23['held']} ${v20_d0h23['money']:.0f}  "
        f"d1h0 held={v20_d1h0['held']} ${v20_d1h0['money']:.0f} "
        f"px={v20_d1h0['px']:.1f} aff={v20_d1h0['aff']} "
        f"buy={v20_d1h0['buy_q']} fill={v20_d1h0['fill']}"
    )
    print(
        f"  us later hours aff>=1: "
        + (
            ", ".join(f"d{r['day']}h{r['hour']:02d} aff={r['aff']} ${r['money']:.0f}" for r in us_later)
            or "none"
        )
    )
    print(
        f"  us later hours aff>=4: "
        + (
            ", ".join(f"d{r['day']}h{r['hour']:02d} aff={r['aff']} ${r['money']:.0f}" for r in us_later_aff4)
            or "none"
        )
    )
    print(
        f"  v20 BUY_PRODUCT: "
        + ", ".join(
            f"d{r['day']}h{r['hour']:02d}×{r['buy_q']} fill={r['fill']} held {r['held']}->{r['held_after']}"
            for r in v20_buys
        )
    )
    print(
        f"  v20 SELL_WHEAT: "
        + (
            ", ".join(f"d{r['day']}h{r['hour']:02d}×{r['sell_q']} held {r['held']}->{r['held_after']}" for r in v20_sells)
            or "none"
        )
    )
    print(
        f"  us d1 sheep FEED {sorted(ex['d1_sheep_feed'])} n={len(ex['d1_sheep_feed'])}  "
        f"d0 PLANT WHEAT={ex['plant_wheat_d0']}  d6h0 {ys} sum={sum(ys)}  "
        f"land={ex['land_day']} NE_STRAW_d6={ex['ne_straw_d6']} "
        f"escapes={ex['escapes']} bank={rep['bank_us']:.0f} "
        f"(base 67325/72410)"
    )
    if not us_later:
        print("  NO later hour can buy even 1 product wheat from live cash.")
    if us_seed:
        r = us_seed[0]
        print(
            f"  seed trough: d{r['day']}h{r['hour']:02d} "
            f"${r['money']:.0f}->${r['money_after']:.0f} SEED×{r['buy_seed']}; "
            f"skip-seed counterfactual aff at that hour={_afford(r['money'], r['px'])}"
        )


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
        print_hours(rep)
        print_payable(rep)
        print_gap(rep)


if __name__ == "__main__":
    main()
