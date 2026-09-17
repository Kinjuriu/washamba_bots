"""Compare early money / field MELON / escapes: throwaway vs v20."""
import os
import sys
import importlib.util
from kaggle_environments import make

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 0


def load_agent(path):
    if path.endswith(".py") and "route_v20" not in path and ".v20" not in path:
        spec = importlib.util.spec_from_file_location("m", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.agent
    return path


def summarize(label, agent):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": SEED},
        debug=False,
    )
    env.run([agent, "starter"])
    steps = env.steps
    prev = None
    occupied = {}
    escapes = 0
    rows = []
    for step in steps:
        obs = step[0].observation
        src = prev if prev is not None else obs
        day, hour = src.get("day", 0), src.get("hour", 0)
        farm = obs["farms"][0]
        for y, row in enumerate(farm.get("tiles") or []):
            for x, tile in enumerate(row):
                key = (x, y)
                if isinstance(tile, dict) and "animal" in tile:
                    occupied[key] = True
                elif (
                    key in occupied
                    and isinstance(tile, dict)
                    and tile.get("kind") in ("COOP", "PASTURE")
                    and "animal" not in tile
                ):
                    escapes += 1
                    del occupied[key]
        if hour == 23 and day <= 12:
            mel = sum(
                1
                for row in farm["tiles"]
                for t in row
                if isinstance(t, dict) and t.get("crop") == "MELON"
            )
            herd = sum(
                1
                for row in farm["tiles"]
                for t in row
                if isinstance(t, dict) and t.get("animal")
            )
            rows.append((day, farm["money"], mel, herd))
        prev = obs
    print(f"=== {label} seed={SEED} escapes={escapes} bank={steps[-1][0].reward} ===")
    for day, money, mel, herd in rows:
        print(f"  EOD d{day}: money={money:.0f} fieldM={mel} herd={herd}")


v20 = "experiments/.v20_agent.py"
if not os.path.exists(v20):
    v20 = "agents/route_v20.py"

summarize("throwaway", load_agent("experiments/_facts_v20.py"))
summarize("v20", load_agent(v20))
