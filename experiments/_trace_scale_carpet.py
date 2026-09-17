"""Diagnose SW carpet on unlock day."""
import importlib.util
import sys
from collections import Counter

from kaggle_environments import make

spec = importlib.util.spec_from_file_location("t", "experiments/_facts_v20.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def q(x, y, bs=10):
    h = bs // 2
    return ("N" if y < h else "S") + ("W" if x < h else "E")


seeds = [int(x) for x in sys.argv[1:]] or [0, 8]
for seed in seeds:
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([mod.agent, "starter"])
    steps = env.steps
    prev = None
    plant_sw = Counter()
    straw_buy = Counter()
    for i, step in enumerate(steps):
        obs = step[0].observation
        src = prev if prev is not None else obs
        day, hour = src.get("day", 0), src.get("hour", 0)
        act = step[0].get("action") or {}
        farm = src["farms"][0]
        priv = src.get("private") or {}
        if day == 11 and hour == 0:
            print(
                f"seed{seed} d11h0 money={farm['money']:.0f} "
                f"unlocked={farm.get('unlocked_quadrants')} "
                f"seedsSTRAW={priv.get('seeds', {}).get('STRAWBERRY', 0)} "
                f"shedM={(priv.get('shed') or {}).get('MELON', 0)} "
                f"carpet={mod.is_sw_carpet_day(farm, day, 10)} "
                f"unlock_morn={mod.is_sw_unlock_morning(farm, day, hour)}"
            )
            # market that will run
            act0 = step[0].get("action") or {}
            print(f"  market={act0.get('market')}")
        if i > 0:
            for o in act.get("market") or []:
                if o and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY":
                    straw_buy[day] += o[2] if len(o) > 2 else 1
            positions = [farm.get("farmer") or [0, 0]] + list(farm.get("hands") or [])
            units = [act.get("farmer") or []] + list(act.get("hands") or [])
            for idx, u in enumerate(units):
                if not u or u[0] != "PLANT" or len(u) < 2:
                    continue
                if idx >= len(positions):
                    continue
                pos = positions[idx]
                if isinstance(pos, (list, tuple)) and len(pos) == 2 and q(pos[0], pos[1]) == "SW":
                    plant_sw[(day, u[1])] += 1
        if day == 11 and hour == 23:
            farm_e = obs["farms"][0]
            sws = sum(
                1
                for y, row in enumerate(farm_e["tiles"])
                for x, t in enumerate(row)
                if q(x, y) == "SW"
                and isinstance(t, dict)
                and t.get("crop") == "STRAWBERRY"
            )
            print(f"  EOD d11 SW STRAW={sws} money={farm_e['money']:.0f}")
        prev = obs
    print(f"  STRAW buys by day {dict(sorted(straw_buy.items()))}")
    print(f"  SW plants {dict(sorted(plant_sw.items()))}")
