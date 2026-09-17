"""Debug: why animal buys stop after d9."""
import importlib.util
from kaggle_environments import make

spec = importlib.util.spec_from_file_location("f", "experiments/_facts_v20.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 0}, debug=False)
env.run(["experiments/_facts_v20.py", "starter"])
prev = None
for step in env.steps:
    obs = step[0].observation
    src = prev if prev is not None else obs
    day, hour = src.get("day"), src.get("hour")
    if day in (9, 10, 11, 12, 15, 20, 25) and hour == 0:
        farm = src["farms"][0]
        priv = src.get("private") or {}
        owned = m.count_owned_animals(farm, priv, 10)
        target = m.calendar_owned_target(day)
        held = m.species_owned_counts(farm, priv, 10)
        shops = list((src.get("town") or {}).get("unlocked_shops") or [])
        mix = m.shop_mix_target(shops)
        money = farm["money"] + m._credit_fert_sell(priv, src.get("market"))
        acts = m.decide_animal_market_actions(
            farm, priv, 10, day, hour=hour,
            unlocked_shops=shops, market_state=src.get("market"),
        )
        pending = m.pending_second_land(farm)
        print(
            f"d{day}h{hour} money={farm['money']:.0f} pay={money:.0f} "
            f"owned={owned} target={target} held={dict(held)} mix={mix} "
            f"pending_land={pending} acts={acts}"
        )
    prev = obs
