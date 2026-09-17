"""Trace day-0 MELON opening cash impact. Throwaway."""
import importlib.util
import sys
from kaggle_environments import make

AGENT = sys.argv[1] if len(sys.argv) > 1 else "experiments/_facts_v20.py"
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 0

spec = importlib.util.spec_from_file_location("agent_mod", AGENT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 720, "seed": SEED},
    debug=False,
)
env.run([mod.agent, "starter"])
steps = env.steps
prev = None
escapes = 0
occupied = {}
for step in steps:
    obs = step[0].observation
    src = prev if prev is not None else obs
    day, hour = src.get("day", 0), src.get("hour", 0)
    act = step[0].get("action") or {}
    market = act.get("market") or []
    farm = obs["farms"][0]
    for y, row in enumerate(farm.get("tiles") or []):
        for x, tile in enumerate(row):
            key = (x, y)
            if isinstance(tile, dict) and "animal" in tile:
                occupied[key] = tile["animal"]
            elif (
                key in occupied
                and isinstance(tile, dict)
                and tile.get("kind") in ("COOP", "PASTURE")
                and "animal" not in tile
            ):
                escapes += 1
                del occupied[key]
    mel = sum(
        1
        for row in farm["tiles"]
        for t in row
        if isinstance(t, dict) and t.get("crop") == "MELON"
    )
    seeds = (src.get("private") or {}).get("seeds") or {}
    interesting = (
        (day == 0 and hour <= 3)
        or hour == 23 and day <= 12
        or any(
            o and o[0] in ("BUY_LAND", "BUY_ANIMAL", "BUY_SEED")
            for o in market
        )
    )
    if interesting:
        buys = [
            o
            for o in market
            if o and o[0] in ("BUY_LAND", "BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT", "HIRE", "SELL")
        ]
        print(
            f"d{day}h{hour} money={farm['money']:.0f} fieldM={mel} "
            f"seedM={seeds.get('MELON', 0)} orders={buys}"
        )
    prev = obs

print(f"escapes={escapes} bank={steps[-1][0].reward}")
