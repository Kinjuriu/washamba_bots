"""When does YARN_STORE first appear on seed 0, and what do we buy that day?"""
from collections import Counter
from kaggle_environments import make

V20 = "agents/route_v20.py"
AGENT = "experiments/_facts_v20.py"


def herd(farm):
    c = s = 0
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict):
                if t.get("animal") == "COW":
                    c += 1
                elif t.get("animal") == "SHEEP":
                    s += 1
    return c, s


def main():
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 0}, debug=False)
    env.run([AGENT, V20])
    prev = None
    yarn_first = None
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
        shops = list((prev.get("town") or {}).get("unlocked_shops") or [])
        if yarn_first is None and "YARN_STORE" in shops:
            yarn_first = (day, hour, shops)
            farm = (prev.get("farms") or [{}])[0]
            print("yarn first visible", yarn_first, "herd", herd(farm), "money", farm.get("money"))
        if 10 <= day <= 14:
            buys = [
                o for o in (act.get("market") or [])
                if o and o[0] == "BUY_ANIMAL"
            ]
            if buys or (hour == 0 and day in (11, 12, 13)):
                farm = (prev.get("farms") or [{}])[0]
                print(
                    f"d{day}h{hour:02d} shops={shops} herd={herd(farm)} "
                    f"$={farm.get('money')} buys={buys}"
                )
        prev = obs
    print("yarn_first", yarn_first)


if __name__ == "__main__":
    main()
