"""Side-by-side early market: throwaway vs v20."""
import os
import importlib.util
from kaggle_environments import make

SEED = 0


def load(path):
    if path.endswith("_facts_v20.py"):
        spec = importlib.util.spec_from_file_location("m", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.agent
    return path


def dump(label, agent):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 120, "seed": SEED},
        debug=False,
    )
    env.run([agent, "starter"])
    print(f"=== {label} ===")
    prev = None
    for step in env.steps:
        obs = step[0].observation
        src = prev if prev is not None else obs
        day, hour = src.get("day", 0), src.get("hour", 0)
        if day > 3:
            break
        act = step[0].get("action") or {}
        market = [o for o in (act.get("market") or []) if o]
        farm = obs["farms"][0]
        if market or (hour in (0, 23)):
            print(f"d{day}h{hour} ${farm['money']:.0f} {market}")
        prev = obs


v20 = "experiments/.v20_agent.py"
if not os.path.exists(v20):
    v20 = "agents/route_v20.py"
dump("throwaway", load("experiments/_facts_v20.py"))
dump("v20", load(v20))
