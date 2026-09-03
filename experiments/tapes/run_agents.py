"""Agent files vs router_yhay on a seed range, both seats, 8 workers."""
import sys, os, json, statistics as st
from multiprocessing import Pool
sys.path.insert(0, "C:/Users/HP/Spidey-Hub/washamba_bots/experiments")
ROUTER = "C:/Users/HP/Spidey-Hub/washamba_bots/agents/router_yhay.py"
def job(args):
    from kaggle_environments import make
    cand, opp, seed = args
    def play(a, b):
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}); env.run([a, b])
        l, r = env.steps[-1]
        if l.status != "DONE" or r.status != "DONE" or l.reward == 3000 or r.reward == 3000:
            print("NON-DONE/INERT:", a, b, seed, l.status, r.status, l.reward, r.reward, flush=True)
        return l.reward, r.reward
    a0, b1 = play(cand, opp); b0, a1 = play(opp, cand)
    return cand, seed, a0, b1, a1, b0
if __name__ == "__main__":
    cands = [os.path.abspath(p) for p in sys.argv[1].split(",")]
    seeds = [int(x) for x in sys.argv[2].split(",")] if "," in sys.argv[2] else list(range(int(sys.argv[2]), int(sys.argv[3])))
    opp = os.path.abspath(sys.argv[4]) if len(sys.argv) > 4 else ROUTER
    out = sys.argv[5] if len(sys.argv) > 5 else "fam/agents_results.jsonl"
    jobs = [(c, opp, s) for c in cands for s in seeds]
    with Pool(8) as pool: res = pool.map(job, jobs)
    with open(out, "a") as f:
        for c, s, a0, b1, a1, b0 in res: f.write(json.dumps({"cand": os.path.basename(c), "opp": os.path.basename(opp), "seed": s, "seat0": [a0, b1], "seat1": [a1, b0]}) + "\n")
    for c in cands:
        rs = [r for r in res if r[0] == c]
        diffs = [r[2] - r[3] for r in rs] + [r[4] - r[5] for r in rs]
        w = sum(d > 0 for d in diffs); l = sum(d < 0 for d in diffs)
        print(f"{os.path.basename(c):28} vs {os.path.basename(opp):16} {w}-{l} of {len(diffs)}  mean {st.mean(diffs):+8,.0f}  median {st.median(diffs):+8,.0f}  min bank {min(min(r[2], r[4]) for r in rs):,.0f}  worst {min(diffs):+,.0f}")
        print("   per-seed:", " ".join(f"{r[1]}:{(r[2]-r[3]+r[4]-r[5])/2:+.0f}" for r in rs))
