"""Top-12 recording panel: replay each recorded top-12 winner (tape) on its original seed and seat,
and play a candidate in the other seat. Usage (from ~/KagricultureLocalData):
  .venv313/bin/python harness/toppanel_mac.py out.jsonl 2 tetsu=tonight_0928/tetsu_step1009_full.py w6=submissions/w6_herdsafe_frontrun.py
Appends one JSON line per game; rerunning skips games already in out.jsonl."""
import json, sys, os, csv, subprocess
from concurrent.futures import ThreadPoolExecutor
D = 'episodes/20260927T124109Z_top12_strat/'
M = list(csv.DictReader(open(D + 'nn_manifest.csv')))
cands = dict(a.split('=', 1) for a in sys.argv[3:])
done = set()
if os.path.exists(sys.argv[1]):
    for l in open(sys.argv[1]):
        r = json.loads(l); done.add((r['ep'], r['cand']))
jobs = [(m, c) for m in M for c in cands if (m['file'], c) not in done]
print(len(jobs), 'games to run', flush=True)
def one(job):
    m, c = job
    r = subprocess.run([sys.executable, 'harness/tapeopp.py', D + m['file'], m['seat'], cands[c]], capture_output=True, text=True, timeout=1200)
    try: res = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: return dict(ep=m['file'], cand=c, error=r.stderr[-300:])
    res.update(ep=m['file'], cand=c, tape_team=m['team'], tape_rank=m['rank']); return res
with open(sys.argv[1], 'a') as f, ThreadPoolExecutor(int(sys.argv[2])) as pool:
    for res in pool.map(one, jobs):
        f.write(json.dumps(res) + '\n'); f.flush()
