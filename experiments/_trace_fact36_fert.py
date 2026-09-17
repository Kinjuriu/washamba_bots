"""Why no cash recovery d1-d6 after MELON opening."""
import importlib.util
from collections import Counter
from kaggle_environments import make

spec = importlib.util.spec_from_file_location("m", "experiments/_facts_v20.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

env = make("kaggriculture", configuration={"episodeSteps": 200, "seed": 0}, debug=False)
env.run([mod.agent, "starter"])
prev = None
for step in env.steps:
    obs = step[0].observation
    src = prev if prev is not None else obs
    day, hour = src.get("day", 0), src.get("hour", 0)
    if day > 7:
        break
    act = step[0].get("action") or {}
    market = act.get("market") or []
    farm = obs["farms"][0]
    priv = src.get("private") or {}
    shed = priv.get("shed") or {}
    sells = [o for o in market if o and o[0] == "SELL"]
    buys = [o for o in market if o and o[0] in ("BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL", "BUY_LAND", "HIRE")]
    if sells or (hour == 0 and day <= 7) or (hour == 23 and day <= 7):
        print(
            f"d{day}h{hour} money={farm['money']:.0f} "
            f"shedF={shed.get('FERTILIZER', 0)} shedW={shed.get('WHEAT', 0)} "
            f"sells={sells} buys={buys}"
        )
    prev = obs
