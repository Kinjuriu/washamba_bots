"""Diff S2 throwaway vs restored baseline, both contested vs route_v20.

Compares OUR executed $ between two episodes. Do not subtract against
v20 from a different episode — the order book moves.

Usage:
    .venv/Scripts/python.exe experiments/_trace_s2_vs_base.py
    .venv/Scripts/python.exe experiments/_trace_s2_vs_base.py 0
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import V20, _obs, analyze_episode  # noqa: E402

BASE = str(ROOT / "experiments" / "_facts_v20.py")
S2 = str(ROOT / "experiments" / "_facts_v20_s2.py")


def _tally_episode(steps, us_seat=0):
    plants = defaultdict(lambda: Counter())
    hires = Counter()
    max_hands = Counter()
    escapes = 0
    eod_money = {}
    eod_wheat = {}
    eod_straw = {}
    eod_melon = {}
    eod_herd = {}
    for step in steps:
        obs = _obs(step[us_seat].observation)
        day = int(obs.get("day", 0))
        hour = int(obs.get("hour", 0))
        farm = (obs.get("farms") or [{}])[us_seat]
        act = step[us_seat].action or {}
        farmer = act.get("farmer") or ["PASS"]
        hands = act.get("hands") or []
        market = act.get("market") or []
        n_hands = len(hands) if isinstance(hands, list) else 0
        if n_hands > max_hands[day]:
            max_hands[day] = n_hands
        for order in market:
            if order and order[0] == "HIRE":
                hires[day] += 1
        unit_acts = [farmer, *(hands if isinstance(hands, list) else [])]
        for a in unit_acts:
            if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT":
                plants[a[1]][day] += 1
        if hour == 23:
            eod_money[day] = farm.get("money", 0)
            wheat = straw = melon = herd = 0
            for row in farm.get("tiles") or []:
                for t in row:
                    if not isinstance(t, dict):
                        continue
                    if t.get("kind") == "PLANT":
                        crop = t.get("crop")
                        if crop == "WHEAT":
                            wheat += 1
                        elif crop == "STRAWBERRY":
                            straw += 1
                        elif crop == "MELON":
                            melon += 1
                    if t.get("animal"):
                        herd += 1
            eod_wheat[day] = wheat
            eod_straw[day] = straw
            eod_melon[day] = melon
            eod_herd[day] = herd
        for row in farm.get("tiles") or []:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "ESCAPED":
                    escapes += 1
    return {
        "plants": plants,
        "hires": hires,
        "max_hands": max_hands,
        "escapes": escapes,
        "eod_money": eod_money,
        "eod_wheat": eod_wheat,
        "eod_straw": eod_straw,
        "eod_melon": eod_melon,
        "eod_herd": eod_herd,
    }


def _run(agent, seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([agent, V20])
    cash = analyze_episode(env.steps, us_seat=0)
    tall = _tally_episode(env.steps, us_seat=0)
    return cash, tall


def _print_seed(seed, base_cash, base_t, s2_cash, s2_t):
    print("\n" + "#" * 88)
    print(f"# S2 vs restored baseline  seed={seed}  both vs route_v20 seat 1")
    print("#" * 88)
    print(
        f"  bank  base={base_cash['bank_us']:.0f}  s2={s2_cash['bank_us']:.0f}  "
        f"delta={s2_cash['bank_us'] - base_cash['bank_us']:+.0f}  "
        f"v20_base={base_cash['bank_v20']:.0f}  v20_s2={s2_cash['bank_v20']:.0f}"
    )
    print(f"  escapes  base={base_t['escapes']}  s2={s2_t['escapes']}")
    print("  executed units (cashflow):")
    ucats = set(base_cash["units_us"]) | set(s2_cash["units_us"])
    for c in sorted(ucats):
        b = base_cash["units_us"].get(c, 0)
        s = s2_cash["units_us"].get(c, 0)
        if b == s:
            continue
        print(f"    {c:<28} {b:6.0f} -> {s:6.0f}  {s - b:+.0f}")

    cats = set(base_cash["season_us"]) | set(s2_cash["season_us"])
    rows = []
    for c in cats:
        b = base_cash["season_us"].get(c, 0)
        s = s2_cash["season_us"].get(c, 0)
        rows.append((s - b, c, b, s))
    rows.sort(key=lambda x: abs(x[0]), reverse=True)
    print("\n--- our executed $  (s2 - base) ---")
    print(f"  {'category':<24} {'base':>10} {'s2':>10} {'delta':>10}")
    for d, c, b, s in rows:
        if abs(d) < 1:
            continue
        print(f"  {c:<24} {b:10.0f} {s:10.0f} {d:+10.0f}")

    print("\n--- EOD $ / field  (base -> s2) ---")
    print("  day    $base     $s2     d$   wheat  straw  melon  herd  hands")
    for day in range(30):
        b_m = base_t["eod_money"].get(day)
        s_m = s2_t["eod_money"].get(day)
        if b_m is None or s_m is None:
            continue
        print(
            f"  {day:3d} {b_m:8.0f} {s_m:8.0f} {s_m - b_m:+6.0f}  "
            f"{base_t['eod_wheat'].get(day, 0):2d}->{s2_t['eod_wheat'].get(day, 0):<2d}  "
            f"{base_t['eod_straw'].get(day, 0):2d}->{s2_t['eod_straw'].get(day, 0):<2d}  "
            f"{base_t['eod_melon'].get(day, 0):2d}->{s2_t['eod_melon'].get(day, 0):<2d}  "
            f"{base_t['eod_herd'].get(day, 0):2d}->{s2_t['eod_herd'].get(day, 0):<2d}  "
            f"{base_t['max_hands'].get(day, 0):2d}->{s2_t['max_hands'].get(day, 0):<2d}"
        )

    print("\n--- PLANT counts (season / after d0 melon / d5-8 straw) ---")
    for crop in ("WHEAT", "MELON", "STRAWBERRY"):
        b = sum(base_t["plants"][crop].values())
        s = sum(s2_t["plants"][crop].values())
        b_after = sum(v for d, v in base_t["plants"][crop].items() if d > 0)
        s_after = sum(v for d, v in s2_t["plants"][crop].items() if d > 0)
        extra = ""
        if crop == "MELON":
            extra = f"  after_d0 base={b_after} s2={s_after}"
        if crop == "STRAWBERRY":
            b58 = sum(base_t["plants"][crop].get(d, 0) for d in range(5, 9))
            s58 = sum(s2_t["plants"][crop].get(d, 0) for d in range(5, 9))
            extra = f"  d5-8 base={b58} s2={s58}  d11 base={base_t['plants'][crop].get(11, 0)} s2={s2_t['plants'][crop].get(11, 0)}"
        print(f"  {crop:<12} base={b:4d} s2={s:4d} delta={s - b:+4d}{extra}")


def main():
    seeds = [int(x) for x in sys.argv[1:]] or [0]
    for seed in seeds:
        print(f"running seed {seed} baseline...", flush=True)
        base_cash, base_t = _run(BASE, seed)
        print(f"running seed {seed} s2...", flush=True)
        s2_cash, s2_t = _run(S2, seed)
        _print_seed(seed, base_cash, base_t, s2_cash, s2_t)


if __name__ == "__main__":
    main()
