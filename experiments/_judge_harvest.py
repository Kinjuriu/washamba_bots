"""Judge fact-20 harvest-before-collect vs live 40,236 / 55,411.

Usage:
    .venv/Scripts/python.exe experiments/_judge_harvest.py
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
    return sum(1 for u in units(act) if u and u[0] == "PLANT" and len(u) > 1 and u[1] == crop)


def sheep_yield(farm):
    out = []
    for y, row in enumerate(farm.get("tiles") or []):
        for x, t in enumerate(row):
            if isinstance(t, dict) and t.get("animal") == "SHEEP":
                out.append((x, y, int(t.get("yield_units") or 0)))
    return out


def herd_placed(farm):
    n = 0
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict) and t.get("animal"):
                n += 1
    return n


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
        escapes = 0
        sheep_d6 = None
        d7h00_cash = None
        d7h01_cash = None
        d7h00_shed_wool = None
        wool_d6 = 0
        wool_d7 = 0
        yarn = None
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
            if shops:
                shops_end = shops
            if yarn is None and "YARN_STORE" in shops:
                yarn = (day, hour, tuple(shops[:4]))
            if hour == 0 and day == 7:
                d7h00_cash = float(farm.get("money") or 0)
                priv = prev.get("private") or {}
                d7h00_shed_wool = int((priv.get("shed") or {}).get("WOOL") or 0)
            if hour == 1 and day == 7:
                d7h01_cash = float(farm.get("money") or 0)
            straw[day] += plants(act, "STRAWBERRY")
            if day == 0:
                wheat_d0 += plants(act, "WHEAT")
            if day > 0:
                melon_after += plants(act, "MELON")
            for o in act.get("market") or []:
                if o and o[0] == "BUY_LAND":
                    land.append((day, hour))
                if o and o[0] == "SELL" and o[1] == "WOOL":
                    qty = o[2] if len(o) > 2 else 1
                    if day == 6:
                        wool_d6 += qty
                    if day == 7:
                        wool_d7 += qty
            if hour == 23:
                herd[day] = herd_placed(farm)
                if day == 6:
                    sheep_d6 = sheep_yield(farm)
                placed = herd[day]
                priv = prev.get("private") or {}
                # crude escape: owned dropped vs prior eod after d0
            prev = obs
        last = _obs(env.steps[-1][0].observation)
        farm = (last.get("farms") or [{}])[0]
        bank = int(farm.get("money") or 0)
        end_h = herd_placed(farm)
        mix = {"COW": 0, "SHEEP": 0}
        for row in farm.get("tiles") or []:
            for t in row:
                if isinstance(t, dict) and t.get("animal") in mix:
                    mix[t["animal"]] += 1
        # escapes: scan empty pastures vs bought — use eod herd dips
        dips = 0
        prev_h = None
        for d in range(30):
            h = herd.get(d)
            if prev_h is not None and h is not None and h < prev_h:
                dips += prev_h - h
            if h is not None:
                prev_h = h
        live = LIVE[seed]
        print(
            f"seed {seed} bank={bank} live={live} d={bank - live:+d} "
            f"land={land} straw_d5-8={straw[5]}/{straw[6]}/{straw[7]}/{straw[8]} "
            f"wheat_d0={wheat_d0} melon_after={melon_after} "
            f"herd_d6-13={[herd.get(d) for d in range(6, 14)]} end={end_h} "
            f"mix={mix['COW']}C{mix['SHEEP']}S "
            f"dips={dips} sheep_d6EOD={sheep_d6} "
            f"d7h00=${d7h00_cash:.0f} d7h01=${d7h01_cash:.0f} "
            f"d7h00_shed_wool={d7h00_shed_wool} "
            f"wool_d6={wool_d6} wool_d7={wool_d7} "
            f"yarn={yarn} shops0={tuple(shops_end[:4])}"
        )


if __name__ == "__main__":
    main()
