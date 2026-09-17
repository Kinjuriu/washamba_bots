"""Probe land afford + MELON wave after scale card B."""
import importlib.util
import sys

from kaggle_environments import make

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 0
spec = importlib.util.spec_from_file_location("t", "experiments/_facts_v20.py")
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
print(f"=== seed {SEED} bank={steps[-1][0].reward} ===")
for i, step in enumerate(steps):
    obs = step[0].observation
    src = prev if prev is not None else obs
    day, hour = src.get("day", 0), src.get("hour", 0)
    if day in (7, 10, 11, 12) and hour in (0, 1, 23):
        farm = src["farms"][0]
        priv = src.get("private") or {}
        market = src.get("market") or {}
        shops = (src.get("town") or {}).get("unlocked_shops") or ()
        unlocked = list(farm.get("unlocked_quadrants") or [])
        n_extra = len(unlocked) - 1
        owned = mod.count_owned_animals(farm, priv, 10)
        land = mod.decide_land_orders(
            farm,
            day,
            private=priv,
            market_state=market,
            reserved_wheat=owned * 2,
            unlocked_shops=shops,
            board_size=10,
        )
        post = mod._estimated_post_sell_cash(
            farm,
            priv,
            market,
            day,
            reserved_wheat=owned * 2,
            unlocked_shops=shops,
            board_size=10,
        )
        shed = priv.get("shed") or {}
        field_m = sum(
            1
            for row in farm["tiles"]
            for t in row
            if isinstance(t, dict) and t.get("crop") == "MELON"
        )
        cost = mod.LAND_PRICES[n_extra] if n_extra < 3 else None
        print(
            f"d{day}h{hour} unlocked={unlocked} money={farm['money']:.0f} "
            f"post~{post:.0f} cost={cost} land={land} "
            f"shedM={shed.get('MELON', 0)} fieldM={field_m} owned={owned}"
        )
    prev = obs

prev = None
lands, mel, harv_m = [], [], 0
for i, step in enumerate(steps):
    obs = step[0].observation
    src = prev if prev is not None else obs
    day, hour = src.get("day", 0), src.get("hour", 0)
    act = step[0].get("action") or {}
    farm0 = (src.get("farms") or [{}])[0]
    if i > 0:
        for o in act.get("market") or []:
            if o and o[0] == "BUY_LAND":
                lands.append((day, hour, list(obs["farms"][0].get("unlocked_quadrants") or [])))
            if o and o[0] == "SELL" and len(o) > 1 and o[1] == "MELON":
                mel.append((day, o[2] if len(o) > 2 else 1))
        units = [act.get("farmer") or []] + list(act.get("hands") or [])
        positions = [farm0.get("farmer") or [0, 0]] + list(farm0.get("hands") or [])
        for idx, u in enumerate(units):
            if not u or u[0] != "HARVEST":
                continue
            if idx < len(positions):
                pos = positions[idx]
                if isinstance(pos, (list, tuple)) and len(pos) == 2:
                    tiles = farm0.get("tiles") or []
                    y, x = pos[1], pos[0]
                    if y < len(tiles) and x < len(tiles[y]):
                        t = tiles[y][x]
                        if isinstance(t, dict) and t.get("crop") == "MELON":
                            harv_m += 1
    prev = obs
print("BUY_LAND", lands)
print("SELL MELON", mel)
print("MELON HARVEST actions", harv_m)
