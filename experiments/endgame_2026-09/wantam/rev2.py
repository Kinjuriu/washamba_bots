import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fills, h14
from kaggle_environments import make
seed = int(sys.argv[1]); kind = sys.argv[2]; base_kind = sys.argv[3] if len(sys.argv) > 3 else None; seat = seed % 2
res = {}
for k in (base_kind, kind):
    fills.LEDGER.clear()
    a = [h14.load_last_callable(h14.BASE), h14.load_last_callable(h14.BASE)]
    if k: a[seat] = h14.hybrid(k)
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}); env.run(a)
    res[k or "W3"] = (fills.by_product(seat), env.steps[-1][seat].reward)
keys = sorted(set(res[base_kind or "W3"][0]) | set(res[kind][0]))
print(f"{'':14s} {'W3 n':>6} {'W3 $':>8} {kind+' n':>8} {kind+' $':>8} {'diff':>8}")
for k in keys:
    a = res[base_kind or "W3"][0].get(k, (0, 0)); b = res[kind][0].get(k, (0, 0))
    print(f"{k:14s} {a[0]:6d} {a[1]:8d} {b[0]:8d} {b[1]:8d} {b[1]-a[1]:8d}")
print("final", res[base_kind or "W3"][1], res[kind][1])
