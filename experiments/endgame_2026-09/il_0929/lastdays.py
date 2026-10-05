import sys, json, collections
from kaggle_environments import make
A = sys.argv[1]; seed = int(sys.argv[2])
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}); env.run([A, A])
ops = collections.defaultdict(collections.Counter); mk = collections.defaultdict(collections.Counter)
inv_hist = {}
for t in range(1, len(env.steps)):
    step = env.steps[t-1][0].observation["step"]; day = step // 24
    if day < 26: continue
    act = env.steps[t][0].action or {}
    for a in [act.get("farmer")] + list(act.get("hands") or []):
        if isinstance(a, list) and a:
            key = a[0] + ("_" + a[1] if a[0] in ("PICKUP", "DROP", "PLACE", "PLANT", "SELL") and len(a) > 1 else "")
            ops[day][key] += 1
    for o in act.get("market") or []:
        if isinstance(o, list) and o: mk[day][o[0] + "_" + (o[1] if len(o) > 1 else "") + ("x%s" % o[2] if len(o) > 2 else "")] += 1
    if step % 24 == 0:
        p = env.steps[t-1][0].observation["private"]
        inv_hist[day] = dict(shed={k: v for k, v in p["shed"].items() if v}, carried=[{k: v for k, v in i.items() if v} for i in p["inventories"]])
for day in sorted(ops):
    print(f"day {day}: unit ops", dict(ops[day]))
    print(f"   market", dict(mk[day]))
    print(f"   dawn shed", inv_hist.get(day))
print("final", [s.reward for s in env.steps[-1]])
