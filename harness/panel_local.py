"""Play candidates against the recorded top-6 trajectories (original seed and seat), with
the replay directory passed in rather than hardcoded as in top6panel.py.

Usage: python harness/panel_local.py REPLAY_DIR out.jsonl name=path/to/main.py [name=path ...]
REPLAY_DIR holds <episode>.json.gz for every episode in harness/top6_panel.json, fetched from
https://www.kaggleusercontent.com/episodes/<episode>.json (public, no auth). Check the harness
first: W0 on harness/faithful_eps.json must give 6 wins of 38, median -21,744."""
import json, sys, subprocess, os
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(sys.argv[1], '')
P = json.load(open(os.path.join(HERE, 'top6_panel.json')))
C = dict(a.split('=', 1) for a in sys.argv[3:])
jobs = [(n, p, ep, seat, team) for n, p in C.items() for ep, seat, team in P]
def one(j):
    n, p, ep, seat, team = j
    r = subprocess.run([sys.executable, os.path.join(HERE, 'tapeopp.py'), R + ep + '.json.gz', str(seat), p], capture_output=True, text=True, timeout=900)
    try: res = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: return dict(ep=ep, cand=n, error=r.stderr[-300:])
    res.update(ep=ep, seat=seat, team=team, cand=n); return res
with open(sys.argv[2], 'a') as f, ThreadPoolExecutor(3) as ex:
    for res in ex.map(one, jobs):
        f.write(json.dumps(res) + '\n'); f.flush()
