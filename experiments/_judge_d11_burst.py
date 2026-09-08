"""Judge fact 44's d11-burst hold: banks, species, buy hours.

Usage:
    .venv/Scripts/python.exe experiments/_judge_d11_burst.py
"""
from collections import Counter
from kaggle_environments import make

V20 = "agents/route_v20.py"
AGENT = "experiments/_facts_v20.py"
SEEDS = (0, 8)
LIVE = {0: 40806, 8: 34567}
FACT44 = {0: 40236, 8: 55411}


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


def owned_total(farm, private):
    cows, sheep = herd(farm)
    shed = private.get("shed") or {}
    invs = private.get("inventories") or []
    extra = shed.get("COW", 0) + shed.get("SHEEP", 0)
    extra += sum(
        (inv or {}).get("COW", 0) + (inv or {}).get("SHEEP", 0)
        for inv in invs
        if isinstance(inv, dict)
    )
    return cows + sheep + extra, cows, sheep


def main():
    for seed in SEEDS:
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": seed},
            debug=False,
        )
        env.run([AGENT, V20])
        last = env.steps[-1][0]
        obs = last.observation
        if not isinstance(obs, dict):
            obs = dict(obs)
        farm = (obs.get("farms") or [{}])[0]
        bank = int(farm.get("money") or 0)
        end_c, end_s = herd(farm)

        prev = None
        yarn_first = None
        buys = []
        herd_eod = {}
        sheep_after_d0 = 0
        escapes = 0
        plants = Counter()
        for step in env.steps:
            raw = step[0]
            cur = raw.observation
            if not isinstance(cur, dict):
                cur = dict(cur)
            act = raw.get("action") if hasattr(raw, "get") else None
            act = act or getattr(raw, "action", None) or {}
            if prev is None:
                prev = cur
                continue
            day = prev.get("day", 0)
            hour = prev.get("hour", 0)
            shops = list((prev.get("town") or {}).get("unlocked_shops") or [])
            if yarn_first is None and "YARN_STORE" in shops:
                yarn_first = (day, hour, shops)
            farm_p = (prev.get("farms") or [{}])[0]
            priv = prev.get("private") or {}
            total, cows, sheep = owned_total(farm_p, priv)
            if hour == 23:
                herd_eod[day] = (total, cows, sheep)
            for o in act.get("market") or []:
                if o and o[0] == "BUY_ANIMAL":
                    kind = o[1] if len(o) > 1 else "?"
                    qty = int(o[2]) if len(o) > 2 else 1
                    buys.append((day, hour, kind, qty, shops, total, farm_p.get("money")))
                    if kind == "SHEEP" and day > 0:
                        sheep_after_d0 += qty
            units = [act.get("farmer") or []] + list(act.get("hands") or [])
            for u in units:
                if u and u[0] == "PLANT" and len(u) > 1:
                    plants[u[1]] += 1
            prev = cur

        print(f"=== seed {seed} bank={bank} vs live {LIVE[seed]} "
              f"({bank - LIVE[seed]:+d}) vs fact44 {FACT44[seed]} "
              f"({bank - FACT44[seed]:+d})")
        print(f"  end mix C/S={end_c}/{end_s} sheep_after_d0={sheep_after_d0} "
              f"yarn_first={yarn_first}")
        print(f"  herd eod d10={herd_eod.get(10)} d11={herd_eod.get(11)} "
              f"d12={herd_eod.get(12)} d13={herd_eod.get(13)}")
        print(f"  plants tomato={plants['TOMATO']} melon={plants['MELON']} "
              f"straw={plants['STRAWBERRY']} carrot={plants['CARROT']}")
        for row in buys:
            if row[0] >= 10 or row[2] == "SHEEP":
                print(f"  BUY d{row[0]}h{row[1]:02d} {row[2]}x{row[3]} "
                      f"owned={row[5]} $={int(row[6] or 0)} shops={row[4]}")
        print()


if __name__ == "__main__":
    main()
