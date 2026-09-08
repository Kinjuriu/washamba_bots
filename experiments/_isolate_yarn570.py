"""Isolate fact 44's yarn-seed -$570: mix vs leftover.

Writes gitignored copies of experiments/_facts_v20.py with SHOP_AWARE_MIX
and SHOP_AWARE_CROP flipped, then runs contested vs agents/route_v20.py
on seeds 0 and 8. Prints bank, species counters, shop timeline, and
executed-$ stream deltas vs the live-supplement arm (neither).

Usage:
    .venv/Scripts/python.exe experiments/_isolate_yarn570.py
"""
from __future__ import annotations

import importlib.util
import sys
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "experiments" / "_facts_v20.py"
V20 = str(ROOT / "agents" / "route_v20.py")
SEEDS = (0, 8)

ARMS = (
    ("both", True, True),
    ("mix_only", True, False),
    ("crop_only", False, True),
    ("neither", False, False),
)

LIVE = {0: 40806, 8: 34567}
FACT44 = {0: 40236, 8: 55411}


def load_cashflow():
    spec = importlib.util.spec_from_file_location(
        "trace_cashflow_v20", ROOT / "experiments" / "_trace_cashflow_v20.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_arm(name, mix, crop):
    dest = ROOT / "experiments" / f"_iso_yarn_{name}.py"
    text = SRC.read_text(encoding="utf-8")
    text = text.replace("SHOP_AWARE_MIX = True", f"SHOP_AWARE_MIX = {mix}", 1)
    text = text.replace("SHOP_AWARE_CROP = True", f"SHOP_AWARE_CROP = {crop}", 1)
    dest.write_text(text, encoding="utf-8")
    return dest


def plants(act, crop):
    units = [act.get("farmer") or []] + list(act.get("hands") or [])
    return sum(1 for u in units if u and u[0] == "PLANT" and len(u) > 1 and u[1] == crop)


def buys(act, kind, product):
    total = 0
    for o in act.get("market") or []:
        if o and o[0] == kind and len(o) > 1 and o[1] == product:
            total += int(o[2]) if len(o) > 2 else 1
    return total


def herd_on_board(farm):
    cows = sheep = 0
    for row in farm.get("tiles") or []:
        for t in row:
            if not isinstance(t, dict):
                continue
            animal = t.get("animal")
            if animal == "COW":
                cows += 1
            elif animal == "SHEEP":
                sheep += 1
    return cows, sheep


def run_one(agent_path, seed, cashflow):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([str(agent_path), V20])

    plt = {c: Counter() for c in ("WHEAT", "STRAWBERRY", "CARROT", "MELON", "TOMATO")}
    buy_sheep_after_d0 = 0
    buy_cow_after_d0 = 0
    buy_sheep_days = []
    shop_first = {}
    herd_eod = {}
    prev = None
    for step in env.steps:
        raw = step[0]
        obs = raw.observation
        if not isinstance(obs, dict):
            obs = dict(obs)
        act = raw.get("action") if hasattr(raw, "get") else None
        act = act or getattr(raw, "action", None) or {}
        if prev is None:
            prev = obs
            continue
        day = prev.get("day", 0)
        hour = prev.get("hour", 0)
        farm = (prev.get("farms") or [{}])[0]
        shops = list((prev.get("town") or {}).get("unlocked_shops") or [])
        for name in shops:
            shop_first.setdefault(name, day)
        if hour == 23:
            herd_eod[day] = herd_on_board(farm)
        for crop in plt:
            plt[crop][day] += plants(act, crop)
        if day > 0:
            n_s = buys(act, "BUY_ANIMAL", "SHEEP")
            n_c = buys(act, "BUY_ANIMAL", "COW")
            buy_sheep_after_d0 += n_s
            buy_cow_after_d0 += n_c
            if n_s:
                buy_sheep_days.append((day, hour, n_s))
        prev = obs

    last = env.steps[-1][0]
    last_obs = last.observation
    if not isinstance(last_obs, dict):
        last_obs = dict(last_obs)
    farm = (last_obs.get("farms") or [{}])[0]
    bank = float(farm.get("money", 0))
    end_c, end_s = herd_on_board(farm)
    end_herd = end_c + end_s
    escapes = int(farm.get("escaped_animals", 0) or 0)

    rep = cashflow.analyze_episode(env.steps, us_seat=0)
    return {
        "bank": bank,
        "end_c": end_c,
        "end_s": end_s,
        "end_herd": end_herd,
        "escapes": escapes,
        "buy_sheep_after_d0": buy_sheep_after_d0,
        "buy_cow_after_d0": buy_cow_after_d0,
        "buy_sheep_days": buy_sheep_days,
        "shops": shop_first,
        "herd_eod": herd_eod,
        "straw_d58": [plt["STRAWBERRY"][d] for d in range(5, 9)],
        "straw_d11": plt["STRAWBERRY"][11],
        "wheat_d0": plt["WHEAT"][0],
        "melon_after_d0": sum(plt["MELON"][d] for d in range(1, 30)),
        "carrot": sum(plt["CARROT"].values()),
        "tomato": sum(plt["TOMATO"].values()),
        "season": dict(rep["season_us"]),
        "d10_herd": (herd_eod.get(10) or (0, 0)),
    }


def fmt_shops(shops):
    if not shops:
        return "-"
    return " ".join(f"{n}@{d}" for n, d in sorted(shops.items(), key=lambda kv: kv[1]))


def main():
    cashflow = load_cashflow()
    results = {}
    print(
        "arm        seed     bank  d0W  S5-8         S11  "
        "sheep+  cow+  endC/S  herd10  carrot  esc"
    )
    print("-" * 108)
    for name, mix, crop in ARMS:
        path = write_arm(name, mix, crop)
        try:
            for seed in SEEDS:
                r = run_one(path, seed, cashflow)
                results[(name, seed)] = r
                straw = "/".join(str(x) for x in r["straw_d58"])
                c10, s10 = r["d10_herd"]
                print(
                    f"{name:<10} {seed:4d} {r['bank']:8.0f}  {r['wheat_d0']:3d}  "
                    f"{straw:<12} {r['straw_d11']:3d}  "
                    f"{r['buy_sheep_after_d0']:5d}  {r['buy_cow_after_d0']:4d}  "
                    f"{r['end_c']}/{r['end_s']:<4}  {c10}+{s10}    "
                    f"{r['carrot']:5d}  {r['escapes']:3d}"
                )
                sys.stdout.flush()
        finally:
            path.unlink(missing_ok=True)

    print()
    print("baselines: live supplement 40806 / 34567   fact 44 40236 / 55411")
    print()
    for seed in SEEDS:
        print(f"--- shops seed {seed} (both) ---")
        r = results[("both", seed)]
        print(" ", fmt_shops(r["shops"]))
        print("  extra sheep days:", r["buy_sheep_days"] or "none")
        print(
            "  herd eod d0/5/10/12/20/29:",
            {d: r["herd_eod"].get(d) for d in (0, 5, 10, 12, 20, 29)},
        )

    neither0 = results[("neither", 0)]["season"]
    print()
    print("--- seed 0 executed $ vs neither (live supplement) ---")
    print(f"  {'category':<22} {'both':>8} {'mix':>8} {'crop':>8} {'neither':>8}")
    cats = set()
    for name in ("both", "mix_only", "crop_only", "neither"):
        cats |= set(results[(name, 0)]["season"])
    rows = []
    for cat in cats:
        vals = [results[(name, 0)]["season"].get(cat, 0) for name, _, _ in ARMS]
        rows.append((cat, vals))
    rows.sort(key=lambda r: abs(r[1][0] - r[1][3]), reverse=True)
    for cat, vals in rows:
        if max(abs(v - vals[3]) for v in vals) < 1:
            continue
        print(f"  {cat:<22} {vals[0]:8.0f} {vals[1]:8.0f} {vals[2]:8.0f} {vals[3]:8.0f}")

    print()
    print("--- seed 0 bank vs live ---")
    for name, _, _ in ARMS:
        b = results[(name, 0)]["bank"]
        print(f"  {name:<10} {b:8.0f}  vs live {b - LIVE[0]:+.0f}")


if __name__ == "__main__":
    main()
