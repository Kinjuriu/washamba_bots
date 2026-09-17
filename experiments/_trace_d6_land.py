"""S3 d6 first-land afford + empties vs route_v20. Contested, not starter.

Prints hourly d5–d7 cash / wool / post-sell vs $1500 / BUY_LAND emit,
EOD occupancy d5–d8, and STRAW sell path (executed $ / order qty / implied).

Usage:
    .venv/Scripts/python.exe experiments/_trace_d6_land.py
    .venv/Scripts/python.exe experiments/_trace_d6_land.py 0 8
"""
from __future__ import annotations

import importlib.util
import sys
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import V20, analyze_episode  # noqa: E402

S3 = ROOT / "experiments" / "_facts_v20_s3.py"
NEED_FIRST = 1500  # LAND_PRICES[0] + MIN_CASH_RESERVE_FOR_LAND_BUYING


def _agent_path(argv):
    for a in argv:
        p = Path(a)
        if p.suffix == ".py" and p.exists():
            return p.resolve()
        cand = ROOT / "experiments" / a
        if cand.suffix == ".py" and cand.exists():
            return cand.resolve()
        cand = ROOT / a
        if cand.suffix == ".py" and cand.exists():
            return cand.resolve()
    return S3


def load_mod(path):
    spec = importlib.util.spec_from_file_location("facts_throwaway", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _act(raw):
    act = raw.get("action") if hasattr(raw, "get") else None
    return act or getattr(raw, "action", None) or {}


def _obs(raw):
    obs = raw.observation
    if isinstance(obs, dict):
        return obs
    try:
        return dict(obs)
    except Exception:
        return obs


def held(private, product):
    n = int((private.get("shed") or {}).get(product, 0) or 0)
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            n += int(inv.get(product, 0) or 0)
    return n


def occupancy(farm, board=10):
    half = board // 2
    by_q = defaultdict(Counter)
    empty_unlocked = Counter()
    for y, row in enumerate(farm.get("tiles") or []):
        for x, t in enumerate(row):
            q = ("N" if y < half else "S") + ("W" if x < half else "E")
            if t is None:
                empty_unlocked[q] += 1
                by_q[q]["empty"] += 1
            elif t == "LOCKED" or (isinstance(t, dict) and t.get("kind") == "LOCKED"):
                by_q[q]["locked"] += 1
            elif isinstance(t, dict):
                kind = t.get("kind")
                if kind == "PLANT":
                    by_q[q][t.get("crop") or "plant"] += 1
                elif kind in ("PASTURE", "COOP"):
                    by_q[q]["pen"] += 1
                    if t.get("animal"):
                        by_q[q]["animal"] += 1
                elif kind == "WEED":
                    by_q[q]["weed"] += 1
                else:
                    by_q[q][kind or "other"] += 1
    return by_q, empty_unlocked


def sell_qty(act, product):
    n = 0
    for o in act.get("market") or []:
        if o and o[0] == "SELL" and len(o) > 1 and o[1] == product:
            n += int(o[2] or 1) if len(o) > 2 else 1
    return n


def plant_of(act, crop):
    units = [act.get("farmer") or []] + list(act.get("hands") or [])
    return sum(1 for u in units if u and u[0] == "PLANT" and len(u) > 1 and u[1] == crop)


def run_seed(seed, agent=S3):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([str(agent), V20])
    steps = env.steps
    cash = analyze_episode(steps, us_seat=0)
    mod = load_mod(agent)

    first_land = [None, None]
    eod = {0: {}, 1: {}}
    hourly = []
    straw_q = defaultdict(lambda: [0, 0])
    plant_straw = defaultdict(lambda: [0, 0])

    prev = [None, None]
    for step in steps:
        obs_list = [_obs(step[p]) for p in (0, 1)]
        acts = [_act(step[p]) for p in (0, 1)]
        if prev[0] is None:
            prev = obs_list
            continue
        src = prev
        day = src[0].get("day", 0)
        hour = src[0].get("hour", 0)
        farm0 = (src[0].get("farms") or [{}])[0]
        priv0 = src[0].get("private") or {}
        board = len(farm0.get("tiles") or []) or 10
        market_state = src[0].get("market") or {}

        for p in (0, 1):
            if first_land[p] is None:
                if any(o and o[0] == "BUY_LAND" for o in (acts[p].get("market") or [])):
                    first_land[p] = (day, hour)
            plant_straw[day][p] += plant_of(acts[p], "STRAWBERRY")
            straw_q[day][p] += sell_qty(acts[p], "STRAWBERRY")

        if 5 <= day <= 7:
            owned = mod.count_owned_animals(farm0, priv0, board)
            reserved = owned * mod.MIN_WHEAT_RESERVE_FOR_FEEDING
            shops = (src[0].get("town") or {}).get("unlocked_shops") or ()
            post = mod._estimated_post_sell_cash(
                farm0, priv0, market_state, day,
                reserved_wheat=reserved, unlocked_shops=shops,
                sell_fert_for_buy=True, board_size=board,
            )
            emit = mod.decide_land_orders(
                farm0, day, private=priv0, market_state=market_state,
                reserved_wheat=reserved, unlocked_shops=shops,
                sell_fert_for_buy=True, board_size=board,
            )
            emit_raw = mod.decide_land_orders(farm0, day)
            market = acts[0].get("market") or []
            land_i = next((i for i, o in enumerate(market) if o and o[0] == "BUY_LAND"), None)
            wool_sell = any(o and o[0] == "SELL" and len(o) > 1 and o[1] == "WOOL" for o in market)
            by_q, empty_u = occupancy(farm0, board)
            wool_px = (market_state.get("prices") or {}).get("WOOL", 0)
            straw_px = (market_state.get("prices") or {}).get("STRAWBERRY", 0)
            interesting = (
                hour in (0, 6, 12, 23)
                or land_i is not None
                or bool(emit)
                or wool_sell
                or post >= NEED_FIRST
            )
            if interesting:
                hourly.append({
                    "day": day, "hour": hour,
                    "pre": float(farm0.get("money", 0)),
                    "post": post,
                    "emit": bool(emit),
                    "emit_raw": bool(emit_raw),
                    "land_i": land_i,
                    "unlocked": list(farm0.get("unlocked_quadrants") or []),
                    "shed_wool": int((priv0.get("shed") or {}).get("WOOL", 0) or 0),
                    "held_wool": held(priv0, "WOOL"),
                    "shed_straw": int((priv0.get("shed") or {}).get("STRAWBERRY", 0) or 0),
                    "held_straw": held(priv0, "STRAWBERRY"),
                    "wool_px": wool_px,
                    "straw_px": straw_px,
                    "wool_sell": wool_sell,
                    "empty": dict(empty_u),
                    "nw": dict(by_q["NW"]),
                    "ne": dict(by_q["NE"]),
                    "market_head": [
                        (o[0], o[1] if len(o) > 1 else None)
                        for o in market[:8]
                    ],
                })

        if hour == 23:
            for p in (0, 1):
                farm = (src[p].get("farms") or [{}])[p]
                by_q, empty_u = occupancy(farm, board)
                eod[p][day] = {
                    "money": float(farm.get("money", 0)),
                    "unlocked": list(farm.get("unlocked_quadrants") or []),
                    "empty": dict(empty_u),
                    "nw": dict(by_q["NW"]),
                    "ne": dict(by_q["NE"]),
                    "sw": dict(by_q["SW"]),
                }
        prev = obs_list

    final = steps[-1]
    bank_us = final[0].reward
    bank_v20 = final[1].reward

    print("\n" + "#" * 88)
    print(f"# d6 land  agent={Path(agent).name}  seed={seed}  bank us={bank_us:.0f}  v20={bank_v20:.0f}")
    print("#" * 88)
    print(f"  first BUY_LAND  us={first_land[0]}  v20={first_land[1]}")
    print(f"  NEED first land = {NEED_FIRST}  (1000 + reserve 500)")

    print("\n--- EOD occupancy d5–d8 (us) ---")
    for day in range(5, 9):
        u = eod[0].get(day, {})
        print(
            f"  d{day} $={u.get('money', 0):7.0f} land={'+'.join(u.get('unlocked') or [])}"
            f" empty={u.get('empty')} NW={u.get('nw')} NE={u.get('ne')}"
        )

    print("\n--- hourly d5–d7 (interesting hours) ---")
    print(
        f"  {'d':>3} {'h':>3} {'pre':>6} {'post':>6} {'need?':>5} "
        f"{'emit':>4} {'raw':>4} {'m_i':>4} {'woolS/H':>8} "
        f"{'wpx':>5} {'wS':>2} {'empty':>18} land"
    )
    for r in hourly:
        need = "Y" if r["post"] >= NEED_FIRST else "n"
        print(
            f"  {r['day']:3d} {r['hour']:3d} {r['pre']:6.0f} {r['post']:6.0f} {need:>5} "
            f"{int(r['emit']):4d} {int(r['emit_raw']):4d} "
            f"{str(r['land_i']):>4} {r['shed_wool']:3d}/{r['held_wool']:<3d} "
            f"{r['wool_px']:5.0f} {int(r['wool_sell']):2d} "
            f"{str(r['empty']):>18} {r['unlocked']}"
        )
        if r["land_i"] is not None or r["wool_sell"] or r["post"] >= NEED_FIRST:
            print(f"       market_head={r['market_head']}  straw_px={r['straw_px']:.0f}")

    print("\n--- STRAW path by day (executed $ / order qty / implied) ---")
    print(
        f"  {'day':>3}  {'STRAW $ us/v20':>16}  {'qty us/v20':>12}  "
        f"{'$/u us':>7}  {'plant us/v20':>12}"
    )
    for day in range(30):
        su = cash["by_day_us"].get(day, Counter()).get("SELL_STRAWBERRY", 0)
        sv = cash["by_day_v20"].get(day, Counter()).get("SELL_STRAWBERRY", 0)
        qu, qv = straw_q[day]
        pu, pv = plant_straw[day]
        if abs(su) + abs(sv) + qu + qv + pu + pv < 1:
            continue
        implied = (su / qu) if qu else 0
        print(
            f"  {day:3d}  {su:7.0f}/{sv:<7.0f}  {qu:5d}/{qv:<5d}  "
            f"{implied:7.1f}  {pu:5d}/{pv:<5d}"
        )

    print("\n--- season STRAW/WOOL/MELON $ ---")
    for cat in ("SELL_STRAWBERRY", "SELL_WOOL", "SELL_MELON", "SELL_WHEAT", "BUY_LAND"):
        a = cash["season_us"].get(cat, 0)
        b = cash["season_v20"].get(cat, 0)
        ua = cash["units_us"].get(cat, 0)
        ub = cash["units_v20"].get(cat, 0)
        print(f"  {cat:<22} $ {a:8.0f}/{b:<8.0f}  u {ua:6.0f}/{ub:<6.0f}")
    print(f"  bank {bank_us:.0f} / {bank_v20:.0f}")
    return cash, bank_us, bank_v20


def main():
    agent = _agent_path(sys.argv[1:])
    seeds = [int(x) for x in sys.argv[1:] if x.lstrip("-").isdigit()] or [0, 8]
    for seed in seeds:
        print(f"running {agent.name} seed {seed}...", flush=True)
        run_seed(seed, agent=agent)


if __name__ == "__main__":
    main()
