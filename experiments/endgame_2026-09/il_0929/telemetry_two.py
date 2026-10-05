import sys, json
from kaggle_environments import make
from kaggle_environments.agent import get_last_callable
cand, opp, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
fn = get_last_callable(open(cand).read()); g = fn.__globals__
# instrument: count steps where a dump was predicted within K and how much stock we held
stats = {"pred_steps": 0, "pred_units": 0, "stock_at_pred": 0, "fam": None}
orig = g["_wb_fr_qty"]
def probe(dp, obs, item, n, inv, shops, step):
    dumps = [(s, q) for s, q in (dp.upcoming(obs, item, g["WB_FRONTRUN_K"]) or ()) if q > 0]
    if dumps: stats["pred_steps"] += 1; stats["pred_units"] += sum(q for _, q in dumps); stats["stock_at_pred"] += n
    return orig(dp, obs, item, n, inv, shops, step)
g["_wb_fr_qty"] = probe
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}); env.run([fn, opp])
dp = g["_WB_FR"].get(0)
stats["fam"] = dp.active_family() if dp else None
stats["families"] = sorted(g["WB_DP_TAPE_FAMILIES"]) if isinstance(g.get("WB_DP_TAPE_FAMILIES"), (set, list, tuple, dict)) else str(g.get("WB_DP_TAPE_FAMILIES"))[:200]
print(json.dumps(dict(seed=seed, margin=env.steps[-1][0].reward-env.steps[-1][1].reward, frontrun=g["_WB_FR_REPORT"], probe=stats)))
