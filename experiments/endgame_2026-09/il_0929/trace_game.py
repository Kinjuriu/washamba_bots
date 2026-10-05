"""Trace a game: per step, both players' market SELL orders, money, market inventory/prices, sheds.
Usage: trace_game.py A B seed out.json"""
import sys, json, collections
from kaggle_environments import make
A, B, seed, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
env.run([A, B])
rows = []
sales = [collections.Counter(), collections.Counter()]
buys = [collections.Counter(), collections.Counter()]
for t in range(1, len(env.steps)):
    prev = env.steps[t-1]; cur = env.steps[t]
    obs0 = prev[0].observation
    step = obs0["step"]
    r = dict(step=step, money=[f["money"] for f in obs0["farms"]],
             inv={k: obs0["market"]["inventory"][k] for k in ("WOOL","MILK","STRAWBERRY","EGG","TOMATO","MELON","WHEAT","CARROT")},
             price={k: obs0["market"]["prices"][k] for k in ("WOOL","MILK","STRAWBERRY","EGG","TOMATO","MELON")},
             shed=[dict(prev[i].observation["private"]["shed"]) for i in (0,1)],
             orders=[[o for o in (cur[i].action or {}).get("market", []) if isinstance(o, list) and o] for i in (0,1)])
    for i in (0,1):
        for o in r["orders"][i]:
            if o[0] == "SELL": sales[i][o[1]] += int(o[2])
            elif o[0].startswith("BUY") or o[0] in ("HIRE","BUY_LAND"): buys[i][o[0]+":"+(o[1] if len(o)>1 else "")] += int(o[2]) if len(o)>2 else 1
    rows.append(r)
last = env.steps[-1]
json.dump(dict(seed=seed, rewards=[s.reward for s in last], status=[s.status for s in last], rows=rows,
               sales=[dict(c) for c in sales], buys=[dict(c) for c in buys], shops=env.steps[-1][0].observation["town"]["unlocked_shops"]), open(out, "w"))
print("rewards", [s.reward for s in last], "shops", env.steps[-1][0].observation["town"]["unlocked_shops"])
print("sales", [dict(c) for c in sales]); print("buys", [dict(c) for c in buys])
print("final sheds", [dict(last[i].observation["private"]["shed"]) for i in (0,1)])
