"""Does the yarn-seed -$570 come from the two d13 sheep?

Usage:
    .venv/Scripts/python.exe experiments/_isolate_hold2.py
"""
from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "experiments" / "_facts_v20.py"
V20 = str(ROOT / "agents" / "route_v20.py")
SEEDS = (0, 8)
LIVE = {0: 40806, 8: 34567}

ARMS = (
    ("current", False),
    ("hold2", True),
)


def load_cashflow():
    spec = importlib.util.spec_from_file_location(
        "trace_cashflow_v20", ROOT / "experiments" / "_trace_cashflow_v20.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_arm(name, hold2):
    dest = ROOT / "experiments" / f"_iso_hold2_{name}.py"
    text = SRC.read_text(encoding="utf-8")
    text = text.replace("HOLD_SHEEP_AT_2 = False", f"HOLD_SHEEP_AT_2 = {hold2}", 1)
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
            if t.get("animal") == "COW":
                cows += 1
            elif t.get("animal") == "SHEEP":
                sheep += 1
    return cows, sheep


def run_one(agent_path, seed, cashflow):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([str(agent_path), V20])
    buy_sheep_after_d0 = 0
    buy_sheep_days = []
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
        if hour == 23:
            herd_eod[day] = herd_on_board(farm)
        if day > 0:
            n_s = buys(act, "BUY_ANIMAL", "SHEEP")
            buy_sheep_after_d0 += n_s
            if n_s:
                buy_sheep_days.append((day, hour, n_s))
        prev = obs
    last_obs = env.steps[-1][0].observation
    if not isinstance(last_obs, dict):
        last_obs = dict(last_obs)
    farm = (last_obs.get("farms") or [{}])[0]
    bank = float(farm.get("money", 0))
    end_c, end_s = herd_on_board(farm)
    rep = cashflow.analyze_episode(env.steps, us_seat=0)
    return {
        "bank": bank,
        "end_c": end_c,
        "end_s": end_s,
        "escapes": int(farm.get("escaped_animals", 0) or 0),
        "buy_sheep_after_d0": buy_sheep_after_d0,
        "buy_sheep_days": buy_sheep_days,
        "herd_eod": herd_eod,
        "season": dict(rep["season_us"]),
    }


def main():
    cashflow = load_cashflow()
    results = {}
    print("arm      seed     bank  sheep+  endC/S  esc  vs live")
    print("-" * 64)
    for name, hold2 in ARMS:
        path = write_arm(name, hold2)
        try:
            for seed in SEEDS:
                r = run_one(path, seed, cashflow)
                results[(name, seed)] = r
                print(
                    f"{name:<8} {seed:4d} {r['bank']:8.0f}  "
                    f"{r['buy_sheep_after_d0']:5d}  {r['end_c']}/{r['end_s']:<4} "
                    f"{r['escapes']:3d}  {r['bank'] - LIVE[seed]:+.0f}"
                )
                sys.stdout.flush()
        finally:
            path.unlink(missing_ok=True)

    print()
    print("current extra sheep days seed 0:", results[("current", 0)]["buy_sheep_days"])
    print("hold2 extra sheep days seed 0:", results[("hold2", 0)]["buy_sheep_days"])
    print(
        "herd eod current d10/12/20:",
        {d: results[("current", 0)]["herd_eod"].get(d) for d in (10, 12, 20)},
    )
    print(
        "herd eod hold2   d10/12/20:",
        {d: results[("hold2", 0)]["herd_eod"].get(d) for d in (10, 12, 20)},
    )

    print()
    print("--- seed 0 executed $ current vs hold2 ---")
    a = results[("current", 0)]["season"]
    b = results[("hold2", 0)]["season"]
    cats = sorted(set(a) | set(b), key=lambda c: abs(a.get(c, 0) - b.get(c, 0)), reverse=True)
    print(f"  {'category':<22} {'current':>8} {'hold2':>8} {'cur-hold2':>10}")
    for cat in cats:
        va, vb = a.get(cat, 0), b.get(cat, 0)
        if abs(va - vb) < 1:
            continue
        print(f"  {cat:<22} {va:8.0f} {vb:8.0f} {va - vb:10.0f}")


if __name__ == "__main__":
    main()
