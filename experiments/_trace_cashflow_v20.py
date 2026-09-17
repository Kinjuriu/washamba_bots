"""Contested cash-flow diagnosis: throwaway vs route_v20.

Attributes exact $ inflows/outflows by replaying the engine's per-unit
market lockstep each turn (not order qty / sold_exec unit counts).

Usage:
    .venv/Scripts/python.exe experiments/_trace_cashflow_v20.py
    .venv/Scripts/python.exe experiments/_trace_cashflow_v20.py 0 8
"""
from __future__ import annotations

import copy
import sys
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make
from kaggle_environments.envs.kaggriculture.kaggriculture import (
    ANIMALS,
    CROPS,
    FARM_HAND_COST_MULT,
    LAND_ORDER,
    LAND_PRICES,
    PRODUCTS,
    _apply_unit_action,
    _hire_cost,
    _parse_order,
    market_price,
)

ROOT = Path(__file__).resolve().parent.parent
THROWAWAY = str(ROOT / "experiments" / "_facts_v20.py")
V20 = str(ROOT / "agents" / "route_v20.py")

MAX_ORDERS = 10
SELL_KEYS = (
    "MELON", "STRAWBERRY", "WOOL", "MILK", "WHEAT", "CARROT",
    "FERTILIZER", "EGG", "TOMATO",
)
BUY_SEED_KEYS = ("MELON", "STRAWBERRY", "WHEAT", "CARROT", "TOMATO")
BUY_PRODUCT_KEYS = ("WHEAT", "FERTILIZER")
BUY_ANIMAL_KEYS = ("COW", "SHEEP", "GOOSE")


def _obs(raw):
    if isinstance(raw, dict):
        return raw
    try:
        return dict(raw)
    except Exception:
        return raw


def _cat_sell(item):
    return f"SELL_{item}"


def _cat_buy_seed(item):
    return f"BUY_SEED_{item}"


def _cat_buy_product(item):
    return f"BUY_PRODUCT_{item}"


def _cat_buy_animal(item):
    return f"BUY_ANIMAL_{item}"


def replay_turn_cash(market_inv, params, farms, privates, queues, board_size=10):
    """Replay one turn of _process_market; return (ledgers, units) per seat.

    ledgers[p][category] = dollars (positive = money in for SELL, positive
    spend magnitude for buys — we store SELL as +, spends as + out separately
    via sign in category type; net uses signed_flow).
    """
    inv = {k: int(v) for k, v in market_inv.items()}
    money = [float(farms[0]["money"]), float(farms[1]["money"])]
    hires_today = [int(farms[0].get("hires_today", 0)), int(farms[1].get("hires_today", 0))]
    unlocked = [
        list(farms[0].get("unlocked_quadrants") or ["NW"]),
        list(farms[1].get("unlocked_quadrants") or ["NW"]),
    ]
    shed = [
        Counter(privates[0].get("shed") or {}),
        Counter(privates[1].get("shed") or {}),
    ]
    seeds = [
        Counter(privates[0].get("seeds") or {}),
        Counter(privates[1].get("seeds") or {}),
    ]
    shed_cap = 100

    ledgers = [Counter(), Counter()]
    units = [Counter(), Counter()]
    signed = [0.0, 0.0]

    qcopy = [list(q[:MAX_ORDERS]) for q in queues]
    max_len = max((len(q) for q in qcopy), default=0)

    def commit_sell(pid, item, price):
        if shed[pid][item] <= 0:
            return False
        shed[pid][item] -= 1
        money[pid] += price
        if price > 1:
            inv[item] = inv.get(item, 0) + 1
        cat = _cat_sell(item)
        ledgers[pid][cat] += price
        units[pid][cat] += 1
        signed[pid] += price
        return True

    def commit_buy_product(pid, item, price):
        if money[pid] < price:
            return False
        if sum(shed[pid].values()) >= shed_cap:
            return False
        money[pid] -= price
        shed[pid][item] += 1
        inv[item] = inv.get(item, 0) - 1
        cat = _cat_buy_product(item)
        ledgers[pid][cat] += price
        units[pid][cat] += 1
        signed[pid] -= price
        return True

    def commit_buy_seed(pid, item, price):
        if money[pid] < price:
            return False
        money[pid] -= price
        seeds[pid][item] += 1
        cat = _cat_buy_seed(item)
        ledgers[pid][cat] += price
        units[pid][cat] += 1
        signed[pid] -= price
        return True

    def commit_buy_animal(pid, item, price):
        if money[pid] < price:
            return False
        if sum(shed[pid].values()) >= shed_cap:
            return False
        money[pid] -= price
        shed[pid][item] += 1
        cat = _cat_buy_animal(item)
        ledgers[pid][cat] += price
        units[pid][cat] += 1
        signed[pid] -= price
        return True

    def do_hire(pid):
        cost = _hire_cost(hires_today[pid], FARM_HAND_COST_MULT)
        if money[pid] < cost:
            return
        money[pid] -= cost
        hires_today[pid] += 1
        ledgers[pid]["HIRE"] += cost
        units[pid]["HIRE"] += 1
        signed[pid] -= cost

    def do_buy_land(pid):
        n_extra = len(unlocked[pid]) - 1
        if n_extra >= len(LAND_ORDER):
            return
        cost = LAND_PRICES[n_extra]
        if money[pid] < cost:
            return
        money[pid] -= cost
        unlocked[pid].append(LAND_ORDER[n_extra])
        ledgers[pid]["BUY_LAND"] += cost
        units[pid]["BUY_LAND"] += 1
        signed[pid] -= cost

    for i in range(max_len):
        order_states = []
        for pid in (0, 1):
            ostate = None
            if i < len(qcopy[pid]):
                ostate = _parse_order(qcopy[pid][i])
            order_states.append(ostate)

        for pid, ostate in enumerate(order_states):
            if ostate is None:
                continue
            op = ostate["type"]
            if op == "HIRE":
                do_hire(pid)
                order_states[pid] = None
            elif op == "BUY_LAND":
                do_buy_land(pid)
                order_states[pid] = None

        idx_esc = 0
        while True:
            idx_esc += 1
            if idx_esc >= 100_000:
                break
            quoted = [None, None]
            for pid, ostate in enumerate(order_states):
                if ostate is None or ostate.get("remaining", 0) <= 0:
                    continue
                op = ostate["type"]
                item = ostate["item"]
                if op == "SELL" and item in PRODUCTS:
                    price = market_price(item, inv.get(item, 10000), params)
                    quoted[pid] = ("SELL", item, price, ostate)
                elif op == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):
                    price = market_price(item, inv.get(item, 10000) - 1, params)
                    quoted[pid] = ("BUY_PRODUCT", item, price, ostate)
                elif op == "BUY_SEED" and item in CROPS:
                    quoted[pid] = ("BUY_SEED", item, CROPS[item]["seed"], ostate)
                elif op == "BUY_ANIMAL" and item in ANIMALS:
                    quoted[pid] = ("BUY_ANIMAL", item, ANIMALS[item]["cost"], ostate)
                else:
                    order_states[pid] = None

            if all(q is None for q in quoted):
                break

            committed_any = False
            for pid, q in enumerate(quoted):
                if q is None:
                    continue
                op, item, price, ostate = q
                if op == "SELL":
                    ok = commit_sell(pid, item, price)
                elif op == "BUY_PRODUCT":
                    ok = commit_buy_product(pid, item, price)
                elif op == "BUY_SEED":
                    ok = commit_buy_seed(pid, item, price)
                elif op == "BUY_ANIMAL":
                    ok = commit_buy_animal(pid, item, price)
                else:
                    ok = False
                if ok:
                    ostate["remaining"] -= 1
                    committed_any = True
                else:
                    order_states[pid] = None

            if not committed_any:
                break

    return ledgers, units, signed, money


def _apply_units_before_market(farm, private, act, day, board_size, turns_per_day=24):
    """Mirror interpreter: unit actions (incl. PICKUP/DROP) run before market."""
    farmer_action = act.get("farmer") or ["PASS"]
    hands_actions = act.get("hands") or []
    if not isinstance(hands_actions, list):
        hands_actions = []
    unit_actions = [farmer_action, *hands_actions]
    plant_demand = {}
    for a in unit_actions:
        if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT":
            plant_demand[a[1]] = plant_demand.get(a[1], 0) + 1
    seeds = private.get("seeds") or {}
    blocked = {crop for crop, n in plant_demand.items() if n > seeds.get(crop, 0)}

    def _allowed(a):
        if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT" and a[1] in blocked:
            return ["PASS"]
        return a

    _apply_unit_action(
        farm, private, 0, _allowed(farmer_action),
        board_size, day, turns_per_day, 100,
    )
    for h_idx, hand_action in enumerate(hands_actions):
        _apply_unit_action(
            farm, private, h_idx + 1, _allowed(hand_action),
            board_size, day, turns_per_day, 100,
        )


def analyze_episode(steps, us_seat=0):
    them_seat = 1 - us_seat
    season = [Counter(), Counter()]
    season_units = [Counter(), Counter()]
    by_day = [defaultdict(Counter), defaultdict(Counter)]
    by_day_units = [defaultdict(Counter), defaultdict(Counter)]
    turns = []
    max_err = [0.0, 0.0]
    err_count = [0, 0]

    prev_obs = [None, None]

    for si in range(len(steps)):
        step = steps[si]
        acts = []
        obs_list = []
        for p in (0, 1):
            raw = step[p]
            obs = _obs(raw.observation)
            act = raw.get("action") if hasattr(raw, "get") else None
            act = act or getattr(raw, "action", None) or {}
            obs_list.append(obs)
            acts.append(act)

        # Framework stores the action that *produced* this observation on this
        # step (same pairing as _facts_v20_gap.py: src=prev, act=current).
        if prev_obs[0] is None:
            prev_obs = obs_list
            continue

        src = prev_obs
        day = src[0].get("day", 0)
        hour = src[0].get("hour", 0)
        board_size = len(((src[0].get("farms") or [{}])[0].get("tiles") or [])) or 10

        market = src[0].get("market") or {}
        inv = dict(market.get("inventory") or {})
        params = market.get("params")

        farms = []
        privates = []
        queues = []
        money_before = []
        for p in (0, 1):
            farm_raw = (src[p].get("farms") or [{}])[p]
            priv_raw = src[p].get("private") or {}
            farm = copy.deepcopy(farm_raw)
            priv = copy.deepcopy(priv_raw)
            if not isinstance(priv.get("shed"), dict):
                priv["shed"] = dict(priv.get("shed") or {})
            if not isinstance(priv.get("seeds"), dict):
                priv["seeds"] = dict(priv.get("seeds") or {})
            if not isinstance(priv.get("inventories"), list):
                priv["inventories"] = list(priv.get("inventories") or [])
            money_before.append(float(farm.get("money", 0)))
            _apply_units_before_market(farm, priv, acts[p], day, board_size)
            farms.append(farm)
            privates.append(priv)
            queues.append(list(acts[p].get("market") or []))

        farm_stubs = [
            {
                "money": float(farms[p]["money"]),
                "hires_today": int(farms[p].get("hires_today", 0)),
                "unlocked_quadrants": list(farms[p].get("unlocked_quadrants") or ["NW"]),
            }
            for p in (0, 1)
        ]
        priv_stubs = [
            {
                "shed": Counter(privates[p].get("shed") or {}),
                "seeds": Counter(privates[p].get("seeds") or {}),
            }
            for p in (0, 1)
        ]

        ledgers, units, signed, _money_after_replay = replay_turn_cash(
            inv, params, farm_stubs, priv_stubs, queues, board_size=board_size,
        )

        # Post-action money is on *this* step's observation.
        money_after_obs = []
        for p in (0, 1):
            farm_n = (obs_list[p].get("farms") or [{}])[p]
            money_after_obs.append(float(farm_n.get("money", 0)))

        delta_obs = [money_after_obs[p] - money_before[p] for p in (0, 1)]

        for p in (0, 1):
            err = abs(signed[p] - delta_obs[p])
            if err > max_err[p]:
                max_err[p] = err
            if err > 1.0:
                err_count[p] += 1
            season[p].update(ledgers[p])
            season_units[p].update(units[p])
            for cat, dollars in ledgers[p].items():
                by_day[p][day][cat] += dollars
            for cat, n in units[p].items():
                by_day_units[p][day][cat] += n

        turns.append({
            "day": day,
            "hour": hour,
            "step": si,
            "delta_obs": delta_obs,
            "signed": signed,
            "ledgers": [Counter(ledgers[0]), Counter(ledgers[1])],
            "money_before": money_before,
            "money_after": money_after_obs,
        })

        prev_obs = obs_list

    # Remap seats so index 0 = throwaway, 1 = v20
    if us_seat == 0:
        us_i, them_i = 0, 1
    else:
        us_i, them_i = 1, 0

    final = _obs(steps[-1][us_seat].observation)
    final_them = _obs(steps[-1][them_seat].observation)

    return {
        "us_seat": us_seat,
        "bank_us": steps[-1][us_seat].reward,
        "bank_v20": steps[-1][them_seat].reward,
        "season_us": season[us_i],
        "season_v20": season[them_i],
        "units_us": season_units[us_i],
        "units_v20": season_units[them_i],
        "by_day_us": by_day[us_i],
        "by_day_v20": by_day[them_i],
        "by_day_units_us": by_day_units[us_i],
        "by_day_units_v20": by_day_units[them_i],
        "turns": [
            {
                **t,
                "delta_obs_us": t["delta_obs"][us_i],
                "delta_obs_v20": t["delta_obs"][them_i],
                "signed_us": t["signed"][us_i],
                "signed_v20": t["signed"][them_i],
                "ledger_us": t["ledgers"][us_i],
                "ledger_v20": t["ledgers"][them_i],
                "money_us": t["money_after"][us_i],
                "money_v20": t["money_after"][them_i],
                "gap_delta": t["delta_obs"][us_i] - t["delta_obs"][them_i],
            }
            for t in turns
        ],
        "max_err_us": max_err[us_i],
        "max_err_v20": max_err[them_i],
        "err_count_us": err_count[us_i],
        "err_count_v20": err_count[them_i],
        "end_money_us": (final.get("farms") or [{}])[us_seat].get("money"),
        "end_money_v20": (final_them.get("farms") or [{}])[them_seat].get("money"),
    }


def _inflow_cats(ledger):
    return {k: v for k, v in ledger.items() if k.startswith("SELL_")}


def _outflow_cats(ledger):
    return {k: v for k, v in ledger.items() if not k.startswith("SELL_")}


def print_season_table(rep):
    us, v20 = rep["season_us"], rep["season_v20"]
    cats = sorted(set(us) | set(v20))
    print("\n--- season $ (executed) ---")
    print(f"  {'category':<22} {'us':>10} {'v20':>10} {'gap us-v20':>12}")
    inflow_us = inflow_v20 = out_us = out_v20 = 0.0
    rows = []
    for cat in cats:
        a, b = us.get(cat, 0), v20.get(cat, 0)
        rows.append((cat, a, b, a - b))
        if cat.startswith("SELL_"):
            inflow_us += a
            inflow_v20 += b
        else:
            out_us += a
            out_v20 += b
    # Sort by absolute gap descending
    rows.sort(key=lambda r: abs(r[3]), reverse=True)
    for cat, a, b, g in rows:
        print(f"  {cat:<22} {a:10.0f} {b:10.0f} {g:12.0f}")
    print(
        f"  {'TOTAL_IN (SELL)':<22} {inflow_us:10.0f} {inflow_v20:10.0f} "
        f"{inflow_us - inflow_v20:12.0f}"
    )
    print(
        f"  {'TOTAL_OUT (spend)':<22} {out_us:10.0f} {out_v20:10.0f} "
        f"{out_us - out_v20:12.0f}"
    )
    net_us = inflow_us - out_us
    net_v20 = inflow_v20 - out_v20
    print(
        f"  {'NET (in-out)':<22} {net_us:10.0f} {net_v20:10.0f} "
        f"{net_us - net_v20:12.0f}"
    )
    print(
        f"  bank reward={rep['bank_us']:.0f} v20={rep['bank_v20']:.0f} "
        f"delta={rep['bank_us'] - rep['bank_v20']:+.0f}"
    )
    print(
        f"  replay check max|err| us={rep['max_err_us']:.2f} "
        f"v20={rep['max_err_v20']:.2f}  "
        f"turns|>$1| us={rep['err_count_us']} v20={rep['err_count_v20']}"
    )


def print_day_widen(rep):
    print("\n--- day rollup: gap widen + category gaps (us-v20 $) ---")
    print(
        f"  {'day':>3} {'$us':>8} {'$v20':>8} {'gap':>8} {'widen':>8}  "
        f"top category gaps that day"
    )
    prev_gap = 0.0
    # EOD money from last hour of each day
    eod_us = {}
    eod_v20 = {}
    for t in rep["turns"]:
        if t["hour"] == 23:
            eod_us[t["day"]] = t["money_us"]
            eod_v20[t["day"]] = t["money_v20"]

    day_cat_gap = defaultdict(Counter)
    for d, cats in rep["by_day_us"].items():
        for c, v in cats.items():
            day_cat_gap[d][c] += v
    for d, cats in rep["by_day_v20"].items():
        for c, v in cats.items():
            day_cat_gap[d][c] -= v

    for day in range(30):
        if day not in eod_us or day not in eod_v20:
            continue
        gap = eod_us[day] - eod_v20[day]
        widen = gap - prev_gap
        tops = sorted(day_cat_gap[day].items(), key=lambda x: abs(x[1]), reverse=True)[:4]
        tops_s = "  ".join(f"{c}={g:+.0f}" for c, g in tops if abs(g) >= 1)
        print(
            f"  {day:3d} {eod_us[day]:8.0f} {eod_v20[day]:8.0f} {gap:8.0f} "
            f"{widen:8.0f}  {tops_s}"
        )
        prev_gap = gap


def print_top_turns(rep, n=20):
    print(f"\n--- top {n} turns by worst gap_delta (us delta - v20 delta) ---")
    ranked = sorted(rep["turns"], key=lambda t: t["gap_delta"])[:n]
    for t in ranked:
        # category gaps this turn
        cats = set(t["ledger_us"]) | set(t["ledger_v20"])
        gaps = sorted(
            ((c, t["ledger_us"].get(c, 0) - t["ledger_v20"].get(c, 0)) for c in cats),
            key=lambda x: abs(x[1]),
            reverse=True,
        )[:5]
        gaps_s = " ".join(f"{c}={g:+.0f}" for c, g in gaps if abs(g) >= 1)
        print(
            f"  d{t['day']}h{t['hour']:02d} "
            f"d$us={t['delta_obs_us']:+7.0f} d$v20={t['delta_obs_v20']:+7.0f} "
            f"gap_d={t['gap_delta']:+7.0f}  "
            f"$us={t['money_us']:.0f} $v20={t['money_v20']:.0f}  {gaps_s}"
        )


def print_inflow_outflow_summary(rep):
    print("\n--- inflow / outflow summary ---")
    for label, led in (("us", rep["season_us"]), ("v20", rep["season_v20"])):
        sells = _inflow_cats(led)
        spends = _outflow_cats(led)
        print(f"  {label} SELL $:")
        for k, v in sorted(sells.items(), key=lambda x: -x[1]):
            print(f"    {k:<22} {v:10.0f}")
        print(f"  {label} SPEND $:")
        for k, v in sorted(spends.items(), key=lambda x: -x[1]):
            print(f"    {k:<22} {v:10.0f}")


def run_seed(seed, us_seat=0):
    agents = [THROWAWAY, V20] if us_seat == 0 else [V20, THROWAWAY]
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run(agents)
    return analyze_episode(env.steps, us_seat=us_seat)


def main():
    seeds = [int(x) for x in sys.argv[1:]] or [0, 8]
    for seed in seeds:
        print("\n" + "#" * 88)
        print(f"# cashflow vs v20  seed={seed}  throwaway_seat=0")
        print("#" * 88)
        rep = run_seed(seed, us_seat=0)
        print_season_table(rep)
        print_inflow_outflow_summary(rep)
        print_day_widen(rep)
        print_top_turns(rep, n=20)


if __name__ == "__main__":
    main()
