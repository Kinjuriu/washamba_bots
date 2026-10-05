"""Replay W3-band ladder opponents (tape family, 2,200-2,800) as recorded tapes on their original seed and seat,
and play each candidate in our seat. Usage: python bandpanel.py out.jsonl workers name=path ..."""
import json, sys, os, subprocess
from concurrent.futures import ThreadPoolExecutor
P = json.load(open('band_panel.json'))   # [ep, opp_seat, our_submission, opp_rating, opp_team]
R = '/mnt/user-data/uploads/KagricultureLocalData/episodes/20260924T161358Z_washamba_0924b/replays/'
cands = dict(a.split('=', 1) for a in sys.argv[3:])
jobs = [(p, c) for p in P for c in cands]
def one(job):
    (ep, seat, sub, rating, team), c = job
    r = subprocess.run([sys.executable, 'tapeopp.py', R + ep + '.json.gz', str(seat), cands[c]], capture_output=True, text=True, timeout=1200)
    try: res = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: return dict(ep=ep, cand=c, error=r.stderr[-300:])
    res.update(ep=ep, cand=c, orig_sub=sub, opp_rating=rating, opp_team=team); return res
with open(sys.argv[1], 'a') as f, ThreadPoolExecutor(int(sys.argv[2])) as pool:
    for res in pool.map(one, jobs):
        f.write(json.dumps(res) + '\n'); f.flush()
