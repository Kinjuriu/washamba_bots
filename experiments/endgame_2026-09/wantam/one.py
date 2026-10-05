import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h14
from kaggle_environments import make
seed = int(sys.argv[1]); kind = sys.argv[2]; seat = seed % 2
a = [h14.load_last_callable(h14.BASE), h14.load_last_callable(h14.BASE)]
a[seat] = h14.hybrid(kind)
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}); env.run(a)
c = a[seat].state["ctrl"]
for l in c.log:
    if not l.startswith("d") or "h23" in l: 
        if "h23" in l: print(l)
        continue
    print(l)
print("final", env.steps[-1][seat].reward, "err", c.errors, c.last_error)
