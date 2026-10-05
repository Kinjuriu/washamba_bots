"""Paired match: A vs B on seeds, both seats, one subprocess per game. Resumable JSONL + summary.
Usage: run_match.py A B seeds(e.g. 900-915 or 1,2,3) workers out.jsonl"""
import sys, json, os, subprocess, collections
from concurrent.futures import ThreadPoolExecutor
GAME = r"""
import sys, json
from kaggle_environments import make
env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': int(sys.argv[3])}, debug=False)
env.run([sys.argv[1], sys.argv[2]])
last = env.steps[-1]
print(json.dumps([last[0].reward, last[1].reward, last[0].status, last[1].status]))
"""
def seeds_from(t):
    out = []
    for p in t.split(","):
        if "-" in p: a, b = p.split("-"); out += list(range(int(a), int(b) + 1))
        else: out.append(int(p))
    return out
A, B, seeds, workers, out = sys.argv[1], sys.argv[2], seeds_from(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
done = set()
if os.path.exists(out):
    for l in open(out):
        r = json.loads(l); done.add((r["seed"], r["seat"]))
jobs = [(s, t) for s in seeds for t in (0, 1) if (s, t) not in done]
def play(job):
    seed, seat = job
    pa, pb = (A, B) if seat == 0 else (B, A)
    r = subprocess.run([sys.executable, "-c", GAME, os.path.abspath(pa), os.path.abspath(pb), str(seed)], capture_output=True, text=True, timeout=900)
    try:
        ra, rb, sa, sb = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return dict(seed=seed, seat=seat, error=r.stderr[-300:])
    mine, theirs = (ra, rb) if seat == 0 else (rb, ra)
    return dict(seed=seed, seat=seat, a=mine, b=theirs, sa=sa if seat == 0 else sb, sb=sb if seat == 0 else sa)
with open(out, "a") as f, ThreadPoolExecutor(workers) as pool:
    for r in pool.map(play, jobs):
        f.write(json.dumps(r) + "\n"); f.flush()
rows = [json.loads(l) for l in open(out)]
w = l = t = 0; tot = 0; err = 0; bad = 0
for r in rows:
    if "error" in r: err += 1; continue
    if r["sa"] != "DONE" or r["sb"] != "DONE": bad += 1
    m = r["a"] - r["b"]; tot += m; w += m > 0; l += m < 0; t += m == 0
n = len(rows) - err
print(f"{os.path.basename(A)} vs {os.path.basename(B)}: W-L-T {w}-{l}-{t} points {(w+0.5*t)/max(1,n):.3f} mean margin {tot/max(1,n):+.0f} n={n} errors={err} non-DONE={bad}")
