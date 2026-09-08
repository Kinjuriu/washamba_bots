"""Judge rewrite 15/44: shop + post-sell emit the calendar.

Usage:
    .venv/Scripts/python.exe experiments/_judge_shop_calendar.py
"""
from collections import Counter
from kaggle_environments import make

AGENT = "experiments/_facts_v20.py"
V20 = "agents/route_v20.py"
SEEDS = (0, 8)
LIVE = {0: 40236, 8: 55411}


def _obs(raw):
    return dict(raw) if not isinstance(raw, dict) else raw


def units(act):
    return [act.get("farmer") or []] + list(act.get("hands") or [])


def plants(act, crop):
    return sum(
        1 for u in units(act)
        if u and u[0] == "PLANT" and len(u) > 1 and u[1] == crop
    )


def species_placed(farm):
    counts = {"COW": 0, "SHEEP": 0}
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict) and t.get("animal") in counts:
                counts[t["animal"]] += 1
    return counts


def herd_placed(farm):
    c = species_placed(farm)
    return c["COW"] + c["SHEEP"]


def main():
    for seed in SEEDS:
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": seed},
            debug=False,
        )
        env.run([AGENT, V20])
        prev = None
        land = []
        straw = Counter()
        wheat_d0 = 0
        melon_after = 0
        herd = {}
        end_species = {"COW": 0, "SHEEP": 0}
        buy_sheep_after_d0 = 0
        buy_cow_d13plus = 0
        yarn_day = None
        shops_end = []
        for step in env.steps:
            raw = step[0]
            obs = _obs(raw.observation)
            act = raw.get("action") if hasattr(raw, "get") else None
            act = act or getattr(raw, "action", None) or {}
            if prev is None:
                prev = obs
                continue
            day = prev.get("day", 0)
            hour = prev.get("hour", 0)
            farm = (prev.get("farms") or [{}])[0]
            shops = list((prev.get("town") or {}).get("unlocked_shops") or [])
            if yarn_day is None and "YARN_STORE" in shops:
                yarn_day = (day, hour, tuple(shops))
            straw[day] += plants(act, "STRAWBERRY")
            if day == 0:
                wheat_d0 += plants(act, "WHEAT")
            if day > 0:
                melon_after += plants(act, "MELON")
            for o in act.get("market") or []:
                if o and o[0] == "BUY_LAND":
                    land.append(day)
                if o and o[0] == "BUY_ANIMAL":
                    species = o[1] if len(o) > 1 else None
                    qty = o[2] if len(o) > 2 else 1
                    if species == "SHEEP" and day > 0:
                        buy_sheep_after_d0 += qty
                    if species == "COW" and day >= 13:
                        buy_cow_d13plus += qty
            if hour == 23:
                herd[day] = herd_placed(farm)
            prev = obs
        last = _obs(env.steps[-1][0].observation)
        farm = (last.get("farms") or [{}])[0]
        bank = int(farm.get("money") or 0)
        end_species = species_placed(farm)
        shops_end = list((last.get("town") or {}).get("unlocked_shops") or [])
        dips = 0
        prev_h = None
        for d in range(30):
            h = herd.get(d)
            if prev_h is not None and h is not None and h < prev_h:
                dips += prev_h - h
            if h is not None:
                prev_h = h
        live = LIVE[seed]
        yarn = "YARN" if any(s == "YARN_STORE" for s in shops_end) else "no-yarn"
        print(
            f"seed {seed} bank={bank} live={live} d={bank - live:+d} "
            f"land={land} straw_d5-8={straw[5]}/{straw[6]}/{straw[7]}/{straw[8]} "
            f"wheat_d0={wheat_d0} melon_after={melon_after} "
            f"herd_d0={herd.get(0)} herd_d6-13={[herd.get(d) for d in range(6, 14)]} "
            f"end={end_species} total={end_species['COW'] + end_species['SHEEP']} "
            f"sheep_after_d0={buy_sheep_after_d0} cow_d13plus={buy_cow_d13plus} "
            f"dips={dips} {yarn} yarn_at={yarn_day} shops={shops_end}"
        )


if __name__ == "__main__":
    main()
