import sys, json
from kaggle_environments import make
from kaggle_environments.agent import get_last_callable
cand, opp, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
fn = get_last_callable(open(cand).read())
g = fn.__globals__
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}); env.run([fn, opp])
r = [s.reward for s in env.steps[-1]]
print(json.dumps(dict(seed=seed, opp=opp.split('/')[-2], cand=r[0], opp_bank=r[1], margin=r[0]-r[1], latch=fn.telemetry, frontrun=g.get("_WB_FR_REPORT"), lead758=g.get("_S758_REPORT"))))
