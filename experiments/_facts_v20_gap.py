"""Contested gap diagnostic: throwaway vs agents/route_v20.py.

Shape-clear throwaway still loses hard to v20. This prints day-by-day and
season totals so the largest divergence is named — not a slogan.

**Caveat (2026-09-04):** season `sold` counts are **order quantities**, not
executed fills. v20 issues oversized `SELL FERTILIZER` orders (order qty
~2k while collect ~346). `sold_exec` caps each SELL at shed stock that
turn (running). Prefer `sold_exec` for WHEAT/FERT fact-38 judgements.

Usage:
    .venv/Scripts/python.exe experiments/_facts_v20_gap.py
    .venv/Scripts/python.exe experiments/_facts_v20_gap.py 0
    .venv/Scripts/python.exe experiments/_facts_v20_gap.py 0 8
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
THROWAWAY = str(ROOT / "experiments" / "_facts_v20.py")
V20 = str(ROOT / "agents" / "route_v20.py")

ANIMAL_KINDS = {"COOP", "PASTURE", "BARN", "STABLE"}
SELL_WATCH = ("MELON", "STRAWBERRY", "WOOL", "MILK", "WHEAT", "CARROT", "FERTILIZER")
PRICE_WATCH = ("MELON", "STRAWBERRY", "WOOL", "MILK", "WHEAT", "CARROT")


def tile_quadrant(x, y, board_size):
    half = board_size // 2
    return ("N" if y < half else "S") + ("W" if x < half else "E")


def _is_locked(tile):
    return tile == "LOCKED" or (isinstance(tile, dict) and tile.get("kind") == "LOCKED")


def board_scan(farm):
    board_size = len(farm.get("tiles") or []) or 10
    crops = Counter()
    q_crops = {q: Counter() for q in ("NW", "NE", "SW", "SE")}
    q_empty = Counter()
    q_weeds = Counter()
    weeds = empty = pens = herd = 0
    mix = Counter()
    for y, row in enumerate(farm.get("tiles") or []):
        for x, t in enumerate(row):
            q = tile_quadrant(x, y, board_size)
            if t is None:
                empty += 1
                q_empty[q] += 1
            elif _is_locked(t):
                continue
            elif isinstance(t, dict):
                kind = t.get("kind")
                if kind == "PLANT":
                    crop = t.get("crop") or "?"
                    crops[crop] += 1
                    q_crops[q][crop] += 1
                elif kind == "WEED":
                    weeds += 1
                    q_weeds[q] += 1
                elif kind in ANIMAL_KINDS:
                    pens += 1
                    if t.get("animal"):
                        herd += 1
                        mix[t["animal"]] += 1
    leftover = empty + sum(crops.values()) + weeds
    unlocked = leftover + pens
    return {
        "crops": crops,
        "weeds": weeds,
        "empty": empty,
        "pens": pens,
        "herd": herd,
        "mix": mix,
        "leftover": leftover,
        "unlocked": unlocked,
        "board_size": board_size,
        "q_crops": q_crops,
        "q_empty": dict(q_empty),
        "q_weeds": dict(q_weeds),
    }


def sw_new_plants(farm, day):
    landed = watered = unwatered = 0
    board_size = len(farm.get("tiles") or []) or 10
    for y, row in enumerate(farm.get("tiles") or []):
        for x, t in enumerate(row):
            if tile_quadrant(x, y, board_size) != "SW":
                continue
            if not isinstance(t, dict) or t.get("kind") != "PLANT":
                continue
            if t.get("planted_day") != day:
                continue
            landed += 1
            if t.get("watered_today"):
                watered += 1
            else:
                unwatered += 1
    return landed, watered, unwatered


def _obs_dict(obs):
    if isinstance(obs, dict):
        return obs
    # kaggle Observation is mapping-like
    try:
        return dict(obs)
    except Exception:
        return obs


def collect_player(steps, player):
    """Aggregate one seat across a contested episode."""
    eod = []
    money_h0 = {}
    land_days = set()
    sold = Counter()
    sold_exec = Counter()
    sold_by_day = defaultdict(Counter)
    hire_by_day = Counter()
    max_hands = 0
    plant_q = defaultdict(lambda: defaultdict(Counter))
    sw_landed_by_day = Counter()
    buy_animal = Counter()
    prev_unlocked = None
    prev = None

    for step in steps:
        raw = step[player]
        obs = _obs_dict(raw.observation)
        act = raw.get("action") if hasattr(raw, "get") else None
        if not act:
            act = getattr(raw, "action", None) or {}
        src = prev if prev is not None else obs
        day = src.get("day", 0)
        hour = src.get("hour", 0)
        # Board state for EOD uses current obs; actions attributed to src day
        farm_now = (obs.get("farms") or [{}])[player]
        farm_src = (src.get("farms") or [{}])[player]
        money = farm_now.get("money", 0)
        hands = farm_now.get("hands") or []
        max_hands = max(max_hands, len(hands))

        obs_day = obs.get("day", 0)
        obs_hour = obs.get("hour", 0)
        if obs_hour == 0:
            money_h0[obs_day] = money

        scan = board_scan(farm_now)
        if prev_unlocked is not None and scan["unlocked"] > prev_unlocked:
            land_days.add(obs_day)
        prev_unlocked = scan["unlocked"]

        landed, watered, unwatered = sw_new_plants(farm_now, obs_day)

        market = act.get("market") or []
        hands_src = farm_src.get("hands") or []
        positions = [farm_src.get("farmer") or [0, 0]]
        positions.extend(hands_src)
        unit_acts = [act.get("farmer") or []] + list(act.get("hands") or [])
        board_size = scan["board_size"]
        for idx, unit in enumerate(unit_acts):
            if not unit:
                continue
            if unit[0] == "PLANT" and len(unit) > 1 and idx < len(positions):
                pos = positions[idx]
                if isinstance(pos, (list, tuple)) and len(pos) == 2:
                    q = tile_quadrant(pos[0], pos[1], board_size)
                    plant_q[day][q][unit[1]] += 1

        # Cap SELL at shed stock this turn (running) — order qty ≠ fills.
        priv_src = src.get("private") or {}
        shed_left = dict((priv_src.get("shed") or {}))
        for order in market:
            if not order:
                continue
            op = order[0]
            if op == "SELL" and len(order) >= 3:
                prod, qty = order[1], int(order[2] or 0)
                sold[prod] += qty
                sold_by_day[day][prod] += qty
                held = int(shed_left.get(prod, 0) or 0)
                executed = min(qty, held) if qty > 0 else 0
                sold_exec[prod] += executed
                shed_left[prod] = held - executed
            elif op == "HIRE":
                hire_by_day[day] += 1
            elif op == "BUY_ANIMAL" and len(order) >= 2:
                buy_animal[order[1]] += 1
            elif op == "BUY_LAND":
                land_days.add(day)

        if obs_hour == 23:
            sw_landed_by_day[obs_day] = landed
            eod.append({
                "day": obs_day,
                "money": money,
                "pens": scan["pens"],
                "herd": scan["herd"],
                "mix": dict(scan["mix"]),
                "unlocked": scan["unlocked"],
                "empty": scan["empty"],
                "weeds": scan["weeds"],
                "crops": dict(scan["crops"]),
                "q_empty": scan["q_empty"],
                "q_crops": {q: dict(c) for q, c in scan["q_crops"].items()},
                "q_weeds": scan["q_weeds"],
                "hands": len(hands),
                "sw_landed": landed,
                "sw_watered": watered,
                "sw_unwatered": unwatered,
            })
        prev = obs

    final = _obs_dict(steps[-1][player].observation)
    prices = (final.get("market") or {}).get("prices") or {}
    end_prices = {p: prices.get(p) for p in PRICE_WATCH}
    final_money = (final.get("farms") or [{}])[player].get("money", 0)
    reward = steps[-1][player].reward

    sw_straw = sum(plant_q[d]["SW"].get("STRAWBERRY", 0) for d in plant_q)
    sw_carrot = sum(plant_q[d]["SW"].get("CARROT", 0) for d in plant_q)
    ne_melon = sum(plant_q[d]["NE"].get("MELON", 0) for d in plant_q)
    nw_wheat = sum(plant_q[d]["NW"].get("WHEAT", 0) for d in plant_q)
    sw_wheat = sum(plant_q[d]["SW"].get("WHEAT", 0) for d in plant_q)
    nw_straw_d13_20 = sum(
        plant_q[d]["NW"].get("STRAWBERRY", 0) for d in range(13, 21)
    )
    sw_carrot_d21_25 = sum(
        plant_q[d]["SW"].get("CARROT", 0) for d in range(21, 26)
    )

    return {
        "reward": reward,
        "final_money": final_money,
        "money_h0": money_h0,
        "eod": eod,
        "land_days": sorted(land_days),
        "sold": dict(sold),
        "sold_exec": dict(sold_exec),
        "sold_by_day": {d: dict(c) for d, c in sold_by_day.items()},
        "hire_by_day": dict(hire_by_day),
        "hires_total": sum(hire_by_day.values()),
        "max_hands": max_hands,
        "buy_animal": dict(buy_animal),
        "end_prices": end_prices,
        "sw_straw_plants": sw_straw,
        "sw_carrot_plants": sw_carrot,
        "ne_melon_plants": ne_melon,
        "nw_wheat_plants": nw_wheat,
        "sw_wheat_plants": sw_wheat,
        "nw_straw_d13_20": nw_straw_d13_20,
        "sw_carrot_d21_25": sw_carrot_d21_25,
        "sw_landed_by_day": dict(sw_landed_by_day),
        "plant_q": plant_q,
    }


def run_episode(seed, throwaway_seat=0):
    """throwaway_seat 0 => throwaway is P0; 1 => throwaway is P1."""
    agents = [THROWAWAY, V20] if throwaway_seat == 0 else [V20, THROWAWAY]
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run(agents)
    steps = env.steps
    us = collect_player(steps, throwaway_seat)
    them = collect_player(steps, 1 - throwaway_seat)
    us["label"] = "throwaway"
    them["label"] = "v20"
    return {
        "seed": seed,
        "throwaway_seat": throwaway_seat,
        "us": us,
        "them": them,
        "delta": us["reward"] - them["reward"],
    }


def print_episode(ep):
    seed = ep["seed"]
    seat = ep["throwaway_seat"]
    us, them = ep["us"], ep["them"]
    print()
    print("=" * 88)
    print(
        f"seed={seed} throwaway_seat={seat}  "
        f"throwaway={us['reward']:.0f}  v20={them['reward']:.0f}  "
        f"delta={ep['delta']:+.0f}"
    )
    print("=" * 88)

    print("\n--- season totals ---")
    rows = [
        ("bank", us["reward"], them["reward"]),
        ("hires", us["hires_total"], them["hires_total"]),
        ("max_hands", us["max_hands"], them["max_hands"]),
        ("land_days", us["land_days"], them["land_days"]),
        ("BUY_ANIMAL", us["buy_animal"], them["buy_animal"]),
        ("SW STRAW plants", us["sw_straw_plants"], them["sw_straw_plants"]),
        ("NE MELON plants", us["ne_melon_plants"], them["ne_melon_plants"]),
        ("NW WHEAT plants", us["nw_wheat_plants"], them["nw_wheat_plants"]),
        ("SW WHEAT plants", us["sw_wheat_plants"], them["sw_wheat_plants"]),
        ("NW STRAW d13-20", us["nw_straw_d13_20"], them["nw_straw_d13_20"]),
        ("SW CARROT d21-25", us["sw_carrot_d21_25"], them["sw_carrot_d21_25"]),
    ]
    for name, a, b in rows:
        print(f"  {name:<22} throwaway={a!s:<28} v20={b!s}")

    print("\n  sold units (order qty):")
    for p in SELL_WATCH:
        a = us["sold"].get(p, 0)
        b = them["sold"].get(p, 0)
        if a or b:
            print(f"    {p:<14} throwaway={a:5d}  v20={b:5d}  gap={a - b:+d}")

    print("\n  sold_exec (min order, shed that turn):")
    for p in SELL_WATCH:
        a = us["sold_exec"].get(p, 0)
        b = them["sold_exec"].get(p, 0)
        if a or b:
            print(f"    {p:<14} throwaway={a:5d}  v20={b:5d}  gap={a - b:+d}")

    print("\n  end prices:")
    for p in PRICE_WATCH:
        print(
            f"    {p:<14} throwaway={us['end_prices'].get(p)}  "
            f"v20={them['end_prices'].get(p)}"
        )

    # Day table: money + herd + SW + key crops
    print(
        f"\n--- day table (EOD)  "
        f"{'day':>3} {'$us':>7} {'$v20':>7} {'d$':>7} "
        f"{'hUs':>3} {'hV':>3} {'pUs':>3} {'pV':>3} "
        f"{'swS_us':>6} {'swS_v':>6} {'nwS_us':>6} {'mel_us':>5} {'mel_v':>5} "
        f"{'hireU':>5} {'hireV':>5}"
    )
    eod_us = {e["day"]: e for e in us["eod"]}
    eod_them = {e["day"]: e for e in them["eod"]}
    widest_day = None
    widest_gap = 0
    prev_gap = 0
    day_widen = []
    for day in range(30):
        eu = eod_us.get(day)
        ev = eod_them.get(day)
        if not eu or not ev:
            continue
        d_money = eu["money"] - ev["money"]
        widen = d_money - prev_gap
        day_widen.append((day, widen, d_money, eu["money"], ev["money"]))
        if abs(d_money) > abs(widest_gap):
            widest_gap = d_money
            widest_day = day
        prev_gap = d_money
        sw_us = (eu.get("q_crops") or {}).get("SW", {}).get("STRAWBERRY", 0)
        sw_v = (ev.get("q_crops") or {}).get("SW", {}).get("STRAWBERRY", 0)
        nw_us = (eu.get("q_crops") or {}).get("NW", {}).get("STRAWBERRY", 0)
        mel_us = eu.get("crops", {}).get("MELON", 0)
        mel_v = ev.get("crops", {}).get("MELON", 0)
        print(
            f"  {day:3d} {eu['money']:7.0f} {ev['money']:7.0f} {d_money:7.0f} "
            f"{eu['herd']:3d} {ev['herd']:3d} {eu['pens']:3d} {ev['pens']:3d} "
            f"{sw_us:6d} {sw_v:6d} {nw_us:6d} {mel_us:5d} {mel_v:5d} "
            f"{us['hire_by_day'].get(day, 0):5d} {them['hire_by_day'].get(day, 0):5d}"
        )

    # Where the gap opens fastest
    day_widen.sort(key=lambda t: t[1])  # most negative widen first
    print("\n--- gap open (most negative day-over-day delta change) ---")
    for day, widen, gap, mu, mv in day_widen[:8]:
        print(
            f"  d{day}: widen={widen:+.0f}  gap_now={gap:+.0f}  "
            f"us={mu:.0f} v20={mv:.0f}"
        )
    print(f"  widest absolute gap at EOD d{widest_day}: {widest_gap:+.0f}")

    # Sold by day for premium goods
    print("\n--- sold by day (MELON / STRAW / WOOL / MILK) ---")
    print(
        f"  {'d':>3} {'M_us':>5} {'M_v':>5} {'S_us':>5} {'S_v':>5} "
        f"{'W_us':>5} {'W_v':>5} {'K_us':>5} {'K_v':>5}"
    )
    for day in range(30):
        su = us["sold_by_day"].get(day, {})
        sv = them["sold_by_day"].get(day, {})
        vals = [
            su.get("MELON", 0), sv.get("MELON", 0),
            su.get("STRAWBERRY", 0), sv.get("STRAWBERRY", 0),
            su.get("WOOL", 0), sv.get("WOOL", 0),
            su.get("MILK", 0), sv.get("MILK", 0),
        ]
        if any(vals):
            print(
                f"  {day:3d} {vals[0]:5d} {vals[1]:5d} {vals[2]:5d} {vals[3]:5d} "
                f"{vals[4]:5d} {vals[5]:5d} {vals[6]:5d} {vals[7]:5d}"
            )

    # Home leftover d13-20 / SW carrot window occupancy at EOD
    print("\n--- open-hole windows (EOD occupancy) ---")
    print(
        f"  {'d':>3} {'nwEmp_u':>7} {'nwS_u':>5} {'nwEmp_v':>7} {'nwS_v':>5} "
        f"{'swEmp_u':>7} {'swC_u':>5} {'swEmp_v':>7} {'swC_v':>5}"
    )
    for day in list(range(13, 21)) + list(range(21, 26)):
        eu = eod_us.get(day)
        ev = eod_them.get(day)
        if not eu or not ev:
            continue
        print(
            f"  {day:3d} "
            f"{(eu.get('q_empty') or {}).get('NW', 0):7d} "
            f"{(eu.get('q_crops') or {}).get('NW', {}).get('STRAWBERRY', 0):5d} "
            f"{(ev.get('q_empty') or {}).get('NW', 0):7d} "
            f"{(ev.get('q_crops') or {}).get('NW', {}).get('STRAWBERRY', 0):5d} "
            f"{(eu.get('q_empty') or {}).get('SW', 0):7d} "
            f"{(eu.get('q_crops') or {}).get('SW', {}).get('CARROT', 0):5d} "
            f"{(ev.get('q_empty') or {}).get('SW', 0):7d} "
            f"{(ev.get('q_crops') or {}).get('SW', {}).get('CARROT', 0):5d}"
        )


def main():
    seeds = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [0, 8]
    print(f"THROWAWAY={THROWAWAY}")
    print(f"V20={V20}")
    print(f"seeds={seeds}")
    episodes = []
    for seed in seeds:
        print(f"\nrunning seed={seed} seat=0 ...", flush=True)
        ep = run_episode(seed, throwaway_seat=0)
        episodes.append(ep)
        print_episode(ep)

    print("\n" + "#" * 88)
    print("SUMMARY")
    print("#" * 88)
    for ep in episodes:
        print(
            f"  seed={ep['seed']} seat={ep['throwaway_seat']}: "
            f"delta={ep['delta']:+.0f}  "
            f"(us={ep['us']['reward']:.0f} v20={ep['them']['reward']:.0f})"
        )
        us, them = ep["us"], ep["them"]
        print(
            f"    sold MELON {us['sold'].get('MELON', 0)} vs {them['sold'].get('MELON', 0)} | "
            f"STRAW {us['sold'].get('STRAWBERRY', 0)} vs {them['sold'].get('STRAWBERRY', 0)} | "
            f"WOOL {us['sold'].get('WOOL', 0)} vs {them['sold'].get('WOOL', 0)} | "
            f"MILK {us['sold'].get('MILK', 0)} vs {them['sold'].get('MILK', 0)}"
        )
        print(
            f"    WHEAT order {us['sold'].get('WHEAT', 0)} vs {them['sold'].get('WHEAT', 0)} | "
            f"exec {us['sold_exec'].get('WHEAT', 0)} vs {them['sold_exec'].get('WHEAT', 0)} | "
            f"NW plant {us['nw_wheat_plants']} vs {them['nw_wheat_plants']} | "
            f"SW plant {us['sw_wheat_plants']} vs {them['sw_wheat_plants']}"
        )
        print(
            f"    SW STRAW plants {us['sw_straw_plants']} vs {them['sw_straw_plants']} | "
            f"hires {us['hires_total']} vs {them['hires_total']} | "
            f"land {us['land_days']} vs {them['land_days']}"
        )


if __name__ == "__main__":
    main()
