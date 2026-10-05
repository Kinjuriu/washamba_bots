"""Play a candidate against recorded ranks-7-12 trajectories on their original seed and seat.
Usage: python r7to12panel.py name path/to/agent.py out.jsonl [workers]"""
import json, sys, os, subprocess
from concurrent.futures import ThreadPoolExecutor
HERE=os.path.dirname(os.path.abspath(__file__))
PANEL = json.load(open(os.path.join(HERE,'r7to12_panel.json')))
U = os.path.expanduser('~/KagricultureLocalData/episodes/20260924T161358Z_ranks7to12/replays/')
TAPEOPP = os.path.expanduser('~/KagricultureLocalData/harness/tapeopp.py')
def one(item):
    ep, seat, team, oppfam = item
    r = subprocess.run([sys.executable, TAPEOPP, U + ep + '.json.gz', str(seat), sys.argv[2]], capture_output=True, text=True, timeout=900)
    try: res = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: return dict(ep=ep, error=r.stderr[-300:])
    res.update(ep=ep, team=team, oppfam=oppfam, cand=sys.argv[1]); return res
with open(sys.argv[3], 'a') as f, ThreadPoolExecutor(int(sys.argv[4]) if len(sys.argv) > 4 else 2) as pool:
    for res in pool.map(one, PANEL):
        f.write(json.dumps(res) + '\n'); f.flush()
