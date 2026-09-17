"""HORIZON S0 snapshot: restored throwaway vs route_v20, seeds 0 and 8.

Prints EOD d0-d3 cash / shed / herd / fert-use, first BUY_LAND, and
enough STRAW/FERTILIZE trail to name why seed 8 keeps the existence-hold.
Executed SELL FERT units/$ via cashflow lockstep (not order qty).

Usage:
    .venv/Scripts/python.exe experiments/_trace_horizon_s0.py
    .venv/Scripts/python.exe experiments/_trace_horizon_s0.py 0 8
"""
from __future__ import annotations

import copy
import sys
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import (  # noqa: E402
    THROWAWAY,
    V20,
    _apply_units_before_market,
    _obs,
    replay_turn_cash,
)

ANIMAL_KEYS = ("COW", "SHEEP", "GOOSE")
SNAP_DAYS = range(0, 4)
TRAIL_DAYS = range(0, 16)


def _tile_animals(farm):
    placed = Counter()
    pens = 0
    for row in farm.get("tiles") or []:
        for t in row:
            if not isinstance(t, dict):
                continue
            if t.get("kind") in ("PASTURE", "COOP"):
                pens += 1
            if t.get("animal"):
                placed[t["animal"]] += 1
    return placed, pens


def _live_crop(farm, crop):
    n = 0
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict) and t.get("crop") == crop:
                n += 1
    return n


def _shed_animals(private):
    shed = private.get("shed") or {}
    return sum(int(shed.get(k, 0) or 0) for k in ANIMAL_KEYS)


def _carried_animals(private):
    n = 0
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            n += sum(int(inv.get(k, 0) or 0) for k in ANIMAL_KEYS)
    return n


def _held(private, product):
    n = int((private.get("shed") or {}).get(product, 0) or 0)
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            n += int(inv.get(product, 0) or 0)
    return n


def _unit_actions(act):
    farmer = act.get("farmer") or ["PASS"]
    hands = act.get("hands") or []
    if not isinstance(hands, list):
        hands = []
    return [farmer, *hands]


def _count_op(act, op):
    return sum(1 for a in _unit_actions(act) if a and a[0] == op)


def _first_land_day(land_days):
    return min(land_days) if land_days else None


def run_seed(seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([THROWAWAY, V20])
    steps = env.steps

    by_day_usd = [defaultdict(Counter), defaultdict(Counter)]
    by_day_units = [defaultdict(Counter), defaultdict(Counter)]
    eod = [{}, {}]
    land_days = [set(), set()]
    daily_fertilize = [Counter(), Counter()]
    daily_collect = [Counter(), Counter()]
    daily_plant_straw = [Counter(), Counter()]
    prev = [None, None]

    for step in steps:
        obs_list = []
        acts = []
        for p in (0, 1):
            raw = step[p]
            obs = _obs(raw.observation)
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
        board_size = len(((src[0].get("farms") or [{}])[0].get("tiles") or [])) or 10
        market = src[0].get("market") or {}
        inv = dict(market.get("inventory") or {})
        params = market.get("params")

        farms = []
        privates = []
        queues = []
        for p in (0, 1):
            farm = copy.deepcopy((src[p].get("farms") or [{}])[p])
            priv = copy.deepcopy(src[p].get("private") or {})
            if not isinstance(priv.get("shed"), dict):
                priv["shed"] = dict(priv.get("shed") or {})
            if not isinstance(priv.get("seeds"), dict):
                priv["seeds"] = dict(priv.get("seeds") or {})
            if not isinstance(priv.get("inventories"), list):
                priv["inventories"] = list(priv.get("inventories") or [])
            _apply_units_before_market(farm, priv, acts[p], day, board_size)
            farms.append(farm)
            privates.append(priv)
            queues.append(list(acts[p].get("market") or []))
            daily_fertilize[p][day] += _count_op(acts[p], "FERTILIZE")
            daily_collect[p][day] += _count_op(acts[p], "COLLECT_FERTILIZER")
            daily_plant_straw[p][day] += sum(
                1
                for a in _unit_actions(acts[p])
                if a and a[0] == "PLANT" and len(a) > 1 and a[1] == "STRAWBERRY"
            )
            if any(o and o[0] == "BUY_LAND" for o in (acts[p].get("market") or [])):
                land_days[p].add(day)

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
        ledgers, units, _signed, _money = replay_turn_cash(
            inv, params, farm_stubs, priv_stubs, queues, board_size=board_size,
        )
        for p in (0, 1):
            by_day_usd[p][day].update(ledgers[p])
            by_day_units[p][day].update(units[p])

        if hour == 23:
            for p in (0, 1):
                farm_n = (obs_list[p].get("farms") or [{}])[p]
                priv_n = obs_list[p].get("private") or {}
                placed, pens = _tile_animals(farm_n)
                eod[p][day] = {
                    "money": float(farm_n.get("money", 0)),
                    "shed_fert": int((priv_n.get("shed") or {}).get("FERTILIZER", 0) or 0),
                    "shed_wheat": int((priv_n.get("shed") or {}).get("WHEAT", 0) or 0),
                    "held_fert": _held(priv_n, "FERTILIZER"),
                    "placed": sum(placed.values()),
                    "cows": placed["COW"],
                    "sheep": placed["SHEEP"],
                    "pens": pens,
                    "owned": (
                        sum(placed.values())
                        + _shed_animals(priv_n)
                        + _carried_animals(priv_n)
                    ),
                    "straw": _live_crop(farm_n, "STRAWBERRY"),
                    "melon": _live_crop(farm_n, "MELON"),
                    "wheat_field": _live_crop(farm_n, "WHEAT"),
                    "unlocked": list(farm_n.get("unlocked_quadrants") or ["NW"]),
                }
        prev = obs_list

    bank_us = steps[-1][0].reward
    bank_v20 = steps[-1][1].reward
    return {
        "seed": seed,
        "bank": (bank_us, bank_v20),
        "by_day_usd": by_day_usd,
        "by_day_units": by_day_units,
        "eod": eod,
        "land": [_first_land_day(land_days[0]), _first_land_day(land_days[1])],
        "fertilize": daily_fertilize,
        "collect": daily_collect,
        "plant_straw": daily_plant_straw,
    }


def _row_eod(snap, usd, units, fert, collect, plant):
    if snap is None:
        return "  (no EOD snap)"
    sell_u = units.get("SELL_FERTILIZER", 0)
    sell_d = usd.get("SELL_FERTILIZER", 0)
    buy_f = units.get("BUY_PRODUCT_FERTILIZER", 0)
    buy_a = {k: units.get(k, 0) for k in ("BUY_ANIMAL_COW", "BUY_ANIMAL_SHEEP", "BUY_ANIMAL_GOOSE")}
    buys = ",".join(f"{k.split('_')[-1]}x{v}" for k, v in buy_a.items() if v)
    return (
        f"  $={snap['money']:7.0f}  shedF/W={snap['shed_fert']}/{snap['shed_wheat']}"
        f"  heldF={snap['held_fert']}"
        f"  herd placed={snap['placed']} owned={snap['owned']}"
        f"  {snap['cows']}C{snap['sheep']}S  pens={snap['pens']}"
        f"  straw={snap['straw']} melon={snap['melon']} wheatF={snap['wheat_field']}"
        f"  SELL_FERT {sell_u}u/${sell_d:.0f}  BUY_FERT {buy_f}u"
        f"  FERTILIZE={fert} COLLECT={collect} PLANT_STRAW={plant}"
        f"  animals=[{buys or '-'}]  land={'+'.join(snap['unlocked'])}"
    )


def print_seed(rep):
    seed = rep["seed"]
    bu, bv = rep["bank"]
    print("\n" + "#" * 88)
    print(f"# HORIZON S0  seed={seed}  throwaway_seat=0  bank us={bu:.0f}  v20={bv:.0f}")
    print("#" * 88)
    print(f"  first BUY_LAND  us={rep['land'][0]}  v20={rep['land'][1]}")

    print("\n--- EOD d0-d3 (post hour-23) ---")
    for label, p in (("us", 0), ("v20", 1)):
        print(f"  [{label}]")
        for day in SNAP_DAYS:
            snap = rep["eod"][p].get(day)
            print(
                f"  d{day}"
                + _row_eod(
                    snap,
                    rep["by_day_usd"][p][day],
                    rep["by_day_units"][p][day],
                    rep["fertilize"][p][day],
                    rep["collect"][p][day],
                    rep["plant_straw"][p][day],
                )
            )

    print("\n--- d1-d3 executed SELL/BUY FERT ---")
    print(
        f"  {'day':>3}  {'us u/$':>14}  {'v20 u/$':>14}  "
        f"{'us BUY_F':>8}  {'v20 BUY_F':>9}"
    )
    for day in (1, 2, 3):
        u_u = rep["by_day_units"][0][day].get("SELL_FERTILIZER", 0)
        u_d = rep["by_day_usd"][0][day].get("SELL_FERTILIZER", 0)
        v_u = rep["by_day_units"][1][day].get("SELL_FERTILIZER", 0)
        v_d = rep["by_day_usd"][1][day].get("SELL_FERTILIZER", 0)
        u_b = rep["by_day_units"][0][day].get("BUY_PRODUCT_FERTILIZER", 0)
        v_b = rep["by_day_units"][1][day].get("BUY_PRODUCT_FERTILIZER", 0)
        print(
            f"  {day:3d}  {u_u:4d}/{u_d:8.0f}  {v_u:4d}/{v_d:8.0f}  "
            f"{u_b:8d}  {v_b:9d}"
        )

    print("\n--- trail d0-d15: live STRAW, FERTILIZE, shedF, SELL_STRAW $ ---")
    print(
        f"  {'day':>3}  {'straw us/v20':>14}  {'fertz us/v20':>14}  "
        f"{'shedF us/v20':>14}  {'SELL_STRAW $ us/v20':>22}  {'FERT $ us/v20':>16}"
    )
    for day in TRAIL_DAYS:
        su = rep["eod"][0].get(day, {}).get("straw", 0)
        sv = rep["eod"][1].get(day, {}).get("straw", 0)
        fu = rep["fertilize"][0][day]
        fv = rep["fertilize"][1][day]
        hu = rep["eod"][0].get(day, {}).get("shed_fert", 0)
        hv = rep["eod"][1].get(day, {}).get("shed_fert", 0)
        ss_u = rep["by_day_usd"][0][day].get("SELL_STRAWBERRY", 0)
        ss_v = rep["by_day_usd"][1][day].get("SELL_STRAWBERRY", 0)
        sf_u = rep["by_day_usd"][0][day].get("SELL_FERTILIZER", 0)
        sf_v = rep["by_day_usd"][1][day].get("SELL_FERTILIZER", 0)
        print(
            f"  {day:3d}  {su:6d}/{sv:<6d}  {fu:6d}/{fv:<6d}  "
            f"{hu:6d}/{hv:<6d}  {ss_u:9.0f}/{ss_v:<9.0f}  "
            f"{sf_u:7.0f}/{sf_v:<7.0f}"
        )

    print("\n--- season executed $ (gap-relevant) ---")
    cats = (
        "SELL_STRAWBERRY", "SELL_FERTILIZER", "SELL_WOOL", "SELL_MELON",
        "SELL_WHEAT", "BUY_PRODUCT_FERTILIZER", "BUY_PRODUCT_WHEAT",
        "BUY_ANIMAL_COW", "BUY_LAND",
    )
    print(f"  {'cat':<24} {'us':>10} {'v20':>10} {'gap':>10}")
    for cat in cats:
        a = sum(rep["by_day_usd"][0][d].get(cat, 0) for d in range(30))
        b = sum(rep["by_day_usd"][1][d].get(cat, 0) for d in range(30))
        print(f"  {cat:<24} {a:10.0f} {b:10.0f} {a - b:10.0f}")


def main():
    seeds = [int(x) for x in sys.argv[1:]] or [0, 8]
    for seed in seeds:
        print_seed(run_seed(seed))


if __name__ == "__main__":
    main()
