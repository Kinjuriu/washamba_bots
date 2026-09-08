"""Did cap=target cost the yarn-seed $570 vs live's uncapped mix?

Usage:
    .venv/Scripts/python.exe experiments/_isolate_mixcap.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "experiments" / "_facts_v20.py"
V20 = str(ROOT / "agents" / "route_v20.py")
SEEDS = (0, 8)
LIVE = {0: 40806, 8: 34567}

# mix_lock, use_cap
ARMS = (
    ("current", True, True),
    ("lock_nocap", True, False),
    ("nolock_nocap", False, False),
)


def write_arm(name, mix, cap):
    dest = ROOT / "experiments" / f"_iso_mixcap_{name}.py"
    text = SRC.read_text(encoding="utf-8")
    text = text.replace("SHOP_AWARE_MIX = True", f"SHOP_AWARE_MIX = {mix}", 1)
    text = text.replace("USE_MIX_CAP = True", f"USE_MIX_CAP = {cap}", 1)
    dest.write_text(text, encoding="utf-8")
    return dest


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


def run_one(agent_path, seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([str(agent_path), V20])
    buy_sheep_after_d0 = 0
    buy_sheep_days = []
    herd10 = None
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
        if hour == 23 and day == 10:
            herd10 = herd_on_board(farm)
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
    return {
        "bank": bank,
        "end_c": end_c,
        "end_s": end_s,
        "escapes": int(farm.get("escaped_animals", 0) or 0),
        "buy_sheep_after_d0": buy_sheep_after_d0,
        "buy_sheep_days": buy_sheep_days,
        "herd10": herd10,
    }


def main():
    print("arm           seed     bank  sheep+  herd10  endC/S  esc  vs live")
    print("-" * 76)
    for name, mix, cap in ARMS:
        path = write_arm(name, mix, cap)
        try:
            for seed in SEEDS:
                r = run_one(path, seed)
                h10 = r["herd10"] or (0, 0)
                print(
                    f"{name:<13} {seed:4d} {r['bank']:8.0f}  "
                    f"{r['buy_sheep_after_d0']:5d}  {h10[0]}+{h10[1]}   "
                    f"{r['end_c']}/{r['end_s']:<4} {r['escapes']:3d}  "
                    f"{r['bank'] - LIVE[seed]:+.0f}"
                )
                if seed == 0:
                    print(f"              sheep days: {r['buy_sheep_days'] or 'none'}")
                sys.stdout.flush()
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
