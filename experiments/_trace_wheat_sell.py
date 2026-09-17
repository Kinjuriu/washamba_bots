"""Diagnose fact-38 WHEAT sell path: shed vs reserve vs orders vs price.

Hypotheses to separate:
  H1 reserve floor — owned*2 pegs shed; sellable rarely > 0
  H2 price gate — sellable > 0 but price < threshold and day < liquidation
  H3 no harvest — plants exist but HARVEST WHEAT ≈ 0 (crew/timing)
  H4 order≠exec — SELL qty large, sold_exec tiny (shed empty at order time)
  H5 opponent glut — price collapsed contested-only

Usage:
  .venv/Scripts/python.exe experiments/_trace_wheat_sell.py
  .venv/Scripts/python.exe experiments/_trace_wheat_sell.py 0 8
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
THROWAWAY = str(ROOT / "experiments" / "_facts_v20.py")
V20 = str(ROOT / "agents" / "route_v20.py")

ANIMAL_KINDS = {"COOP", "PASTURE", "BARN", "STABLE"}
MIN_WHEAT_RESERVE_FOR_FEEDING = 2  # matches throwaway
WHEAT_THRESHOLD = 20
LIQUIDATION_START_DAY = 19


def _obs(raw):
    if isinstance(raw, dict):
        return raw
    try:
        return dict(raw)
    except Exception:
        return raw


def count_owned(farm, private):
    shed = private.get("shed") or {}
    owned = 0
    for kind in ("COW", "SHEEP", "GOOSE", "PIG", "CHICKEN"):
        owned += int(shed.get(kind, 0) or 0)
    for unit in [farm.get("farmer")] + list(farm.get("hands") or []):
        if not isinstance(unit, dict):
            continue
        inv = unit.get("inventory") or {}
        for kind in ("COW", "SHEEP", "GOOSE", "PIG", "CHICKEN"):
            owned += int(inv.get(kind, 0) or 0)
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict) and t.get("kind") in ANIMAL_KINDS and t.get("animal"):
                owned += 1
    return owned


def field_wheat(farm):
    n = 0
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") == "WHEAT":
                n += 1
    return n


def unit_wheat(farm, private):
    """WHEAT in shed + carried inventories."""
    n = int((private.get("shed") or {}).get("WHEAT", 0) or 0)
    for unit in [farm.get("farmer")] + list(farm.get("hands") or []):
        if not isinstance(unit, dict):
            continue
        inv = unit.get("inventory") or {}
        n += int(inv.get("WHEAT", 0) or 0)
    return n


def analyze(steps, player, label):
    prev = None
    harvest = 0
    plant = 0
    buy_product = 0
    sell_order = 0
    sell_exec = 0
    feed = 0
    days_sellable_no_sell = 0
    days_sellable_sold = 0
    days_held_by_price = 0
    max_sellable = 0
    max_shed = 0
    eod_rows = []
    sell_days = []
    price_samples = []

    for step in steps:
        raw = step[player]
        obs = _obs(raw.observation)
        act = raw.get("action") if hasattr(raw, "get") else None
        if not act:
            act = getattr(raw, "action", None) or {}
        src = prev if prev is not None else obs
        day = src.get("day", 0)
        hour = src.get("hour", 0)
        farm_src = (src.get("farms") or [{}])[player]
        priv_src = src.get("private") or {}
        market_src = src.get("market") or {}
        farm_now = (obs.get("farms") or [{}])[player]
        priv_now = obs.get("private") or {}

        owned = count_owned(farm_src, priv_src)
        reserved = owned * MIN_WHEAT_RESERVE_FOR_FEEDING
        shed_w = int((priv_src.get("shed") or {}).get("WHEAT", 0) or 0)
        sellable = max(0, shed_w - reserved)
        price = float((market_src.get("prices") or {}).get("WHEAT", 0) or 0)
        liquidating = day >= LIQUIDATION_START_DAY
        would_price_ok = liquidating or price >= WHEAT_THRESHOLD

        market = act.get("market") or []
        shed_left = shed_w
        sold_this = 0
        ordered_this = 0
        for order in market:
            if not order:
                continue
            op = order[0]
            if op == "SELL" and len(order) >= 3 and order[1] == "WHEAT":
                qty = int(order[2] or 0)
                ordered_this += qty
                sell_order += qty
                ex = min(qty, shed_left) if qty > 0 else 0
                sell_exec += ex
                sold_this += ex
                shed_left -= ex
            elif op == "BUY_PRODUCT" and len(order) >= 3 and order[1] == "WHEAT":
                buy_product += int(order[2] or 0)

        unit_acts = [act.get("farmer") or []] + list(act.get("hands") or [])
        positions = [farm_src.get("farmer") or [0, 0]]
        positions.extend(farm_src.get("hands") or [])
        tiles = farm_src.get("tiles") or []
        for idx, unit in enumerate(unit_acts):
            if not unit:
                continue
            if unit[0] == "PLANT" and len(unit) > 1 and unit[1] == "WHEAT":
                plant += 1
            elif unit[0] == "FEED":
                feed += 1
            elif unit[0] == "HARVEST" and idx < len(positions):
                pos = positions[idx]
                if not isinstance(pos, (list, tuple)) or len(pos) < 2:
                    continue
                x, y = int(pos[0]), int(pos[1])
                if y < 0 or y >= len(tiles) or x < 0 or x >= len(tiles[y]):
                    continue
                t = tiles[y][x]
                if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") == "WHEAT":
                    harvest += 1

        if sellable > max_sellable:
            max_sellable = sellable
        if shed_w > max_shed:
            max_shed = shed_w

        if hour == 0 or ordered_this or (hour == 12 and day % 3 == 0):
            price_samples.append((day, hour, price, shed_w, reserved, sellable, owned))

        if ordered_this:
            sell_days.append({
                "day": day, "hour": hour, "order": ordered_this,
                "exec": sold_this, "shed": shed_w, "reserved": reserved,
                "sellable": sellable, "price": price, "owned": owned,
            })
            if sellable > 0:
                days_sellable_sold += 1
        elif sellable > 0 and hour == 0:
            # morning snapshot: could have sold but didn't order
            days_sellable_no_sell += 1
            if not would_price_ok:
                days_held_by_price += 1

        obs_day = obs.get("day", 0)
        obs_hour = obs.get("hour", 0)
        if obs_hour == 23:
            shed_eod = int((priv_now.get("shed") or {}).get("WHEAT", 0) or 0)
            owned_eod = count_owned(farm_now, priv_now)
            reserved_eod = owned_eod * MIN_WHEAT_RESERVE_FOR_FEEDING
            eod_rows.append({
                "day": obs_day,
                "money": farm_now.get("money", 0),
                "shed_w": shed_eod,
                "owned": owned_eod,
                "reserved": reserved_eod,
                "sellable": max(0, shed_eod - reserved_eod),
                "field_w": field_wheat(farm_now),
                "price": float((obs.get("market") or {}).get("prices", {}).get("WHEAT", 0) or 0),
            })
        prev = obs

    final = _obs(steps[-1][player].observation)
    return {
        "label": label,
        "bank": steps[-1][player].reward,
        "plant": plant,
        "harvest_wheat": harvest,
        "buy_product": buy_product,
        "sell_order": sell_order,
        "sell_exec": sell_exec,
        "feed": feed,
        "max_sellable": max_sellable,
        "max_shed": max_shed,
        "mornings_sellable_no_sell": days_sellable_no_sell,
        "mornings_held_by_price": days_held_by_price,
        "sell_events": len(sell_days),
        "sell_days": sell_days,
        "eod": eod_rows,
        "end_price": float((final.get("market") or {}).get("prices", {}).get("WHEAT", 0) or 0),
        "end_shed": int(((final.get("private") or {}).get("shed") or {}).get("WHEAT", 0) or 0),
    }


def print_report(r):
    print(f"\n=== {r['label']} bank={r['bank']:.0f} ===")
    print(
        f"  PLANT WHEAT={r['plant']}  HARVEST_WHEAT={r['harvest_wheat']}  "
        f"BUY_PRODUCT WHEAT={r['buy_product']}  FEED={r['feed']}"
    )
    print(
        f"  SELL order={r['sell_order']}  exec={r['sell_exec']}  "
        f"events={r['sell_events']}  max_shed={r['max_shed']}  "
        f"max_sellable={r['max_sellable']}"
    )
    print(
        f"  mornings sellable>0 no SELL={r['mornings_sellable_no_sell']}  "
        f"(price-held={r['mornings_held_by_price']})  "
        f"end_shed={r['end_shed']} end_price={r['end_price']:.1f}"
    )
    print("  EOD (d13+ or sellable>0 or field_w>0):")
    for row in r["eod"]:
        if row["day"] < 13 and row["sellable"] == 0 and row["field_w"] == 0:
            continue
        print(
            f"    d{row['day']:02d} money={row['money']:6.0f} "
            f"shed={row['shed_w']:3d} res={row['reserved']:3d} "
            f"sellable={row['sellable']:3d} field={row['field_w']:2d} "
            f"price={row['price']:5.1f} owned={row['owned']}"
        )
    if r["sell_days"]:
        print("  SELL events:")
        for s in r["sell_days"][:20]:
            print(
                f"    d{s['day']}h{s['hour']:02d} order={s['order']} exec={s['exec']} "
                f"shed={s['shed']} res={s['reserved']} sellable={s['sellable']} "
                f"price={s['price']:.1f} owned={s['owned']}"
            )
        if len(r["sell_days"]) > 20:
            print(f"    ... +{len(r['sell_days']) - 20} more")


def run_contested(seed, seat=0):
    agents = [THROWAWAY, V20] if seat == 0 else [V20, THROWAWAY]
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run(agents)
    return analyze(env.steps, seat, f"contested seed={seed} seat={seat}")


def run_starter(seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([THROWAWAY, "starter"])
    return analyze(env.steps, 0, f"starter seed={seed}")


def main():
    seeds = [int(x) for x in sys.argv[1:]] or [0, 8]
    for seed in seeds:
        print("\n" + "#" * 72)
        print(f"# seed {seed}")
        print("#" * 72)
        s = run_starter(seed)
        print_report(s)
        c = run_contested(seed, seat=0)
        print_report(c)
        print("\n  --- contrast starter vs contested ---")
        print(
            f"  plants {s['plant']}->{c['plant']}  "
            f"harvest {s['harvest_wheat']}->{c['harvest_wheat']}  "
            f"buy_prod {s['buy_product']}->{c['buy_product']}  "
            f"exec {s['sell_exec']}->{c['sell_exec']}  "
            f"max_sellable {s['max_sellable']}->{c['max_sellable']}"
        )


if __name__ == "__main__":
    main()
