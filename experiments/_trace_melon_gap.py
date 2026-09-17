"""One-off: MELON plant/harvest/sell detail vs v20."""
from collections import Counter, defaultdict

from kaggle_environments import make

env = make(
    "kaggriculture",
    configuration={"episodeSteps": 720, "seed": 0},
    debug=False,
)
env.run(["experiments/_facts_v20.py", "agents/route_v20.py"])

for pid, label in [(0, "us"), (1, "v20")]:
    print("===", label, "reward", env.steps[-1][pid].reward)
    prev = None
    plant = defaultdict(Counter)
    for step in env.steps:
        obs = step[pid].observation
        act = step[pid].get("action") or {}
        src = prev if prev is not None else obs
        day = src.get("day", 0)
        hour = src.get("hour", 0)
        farm = (src.get("farms") or [{}])[pid]
        board = len(farm.get("tiles") or []) or 10
        half = board // 2
        positions = [farm.get("farmer") or [0, 0]] + list(farm.get("hands") or [])
        units = [act.get("farmer") or []] + list(act.get("hands") or [])
        for idx, u in enumerate(units):
            if u and u[0] == "PLANT" and len(u) > 1 and idx < len(positions):
                pos = positions[idx]
                if isinstance(pos, (list, tuple)) and len(pos) == 2:
                    x, y = pos[0], pos[1]
                    q = ("N" if y < half else "S") + ("W" if x < half else "E")
                    plant[day][(q, u[1])] += 1
        sells = []
        harv = 0
        for o in (act.get("market") or []):
            if o and o[0] == "SELL" and o[1] == "MELON":
                sells.append(o[2])
        for u in units:
            if u and u[0] == "HARVEST":
                harv += 1
        if 9 <= day <= 12 and (sells or harv):
            priv = src.get("private") or {}
            shed = (priv.get("shed") or {}).get("MELON", 0)
            money = farm.get("money", 0)
            print(
                f"  d{day}h{hour:02d} harv={harv} sell={sells} "
                f"shed={shed} money={money:.0f}"
            )
        prev = obs
    print("  PLANT by day (q,crop) d0-11:")
    for d in range(12):
        if plant[d]:
            print(f"    d{d}: {dict(plant[d])}")
