import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fills, h14
from kaggle_environments import make
from collections import Counter
seed = int(sys.argv[1]); kind = sys.argv[2]; seat = seed % 2
for k in (None, kind):
    fills.LEDGER.clear()
    a = [h14.load_last_callable(h14.BASE), h14.load_last_callable(h14.BASE)]
    if k: a[seat] = h14.hybrid(k)
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}); env.run(a)
    st = env.steps
    print("=====", k or "W3", "final", st[-1][seat].reward)
    print(" money d29 by hour", [int(st[min(719, 29*24+h)][seat].observation.farms[seat]["money"]) for h in range(0, 24, 2)])
    print(" d29 sales", fills.by_product(seat, 696, 720))
    print(" d28 sales", fills.by_product(seat, 672, 696))
    o = st[-1][seat].observation
    left = {k2: v for k2, v in o.private["shed"].items() if v}
    inv = Counter()
    for i in o.private["inventories"]:
        for k2, v in i.items(): inv[k2] += v
    farm = Counter()
    for row in o.farms[seat]["tiles"]:
        for t in row:
            if isinstance(t, dict) and t.get("yield_units"): farm[t.get("crop") or t.get("animal")] += t["yield_units"]
    print(" left: shed", left, "carried", dict(inv), "on farm", dict(farm))
