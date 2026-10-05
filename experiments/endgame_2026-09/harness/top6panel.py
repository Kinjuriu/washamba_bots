"""Play a candidate against recorded top-6 trajectories (their original seed and seat).
Usage: python top6panel.py name path/to/main.py out.jsonl [workers]"""
import json, sys, os, subprocess
from concurrent.futures import ThreadPoolExecutor
PANEL = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'top6_panel.json')))
U = os.path.expanduser('~/KagricultureLocalData/episodes/20260923T153431Z_top6/replays/')
def one(item):
    ep, seat, team = item
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tapeopp.py'), U + ep + '.json.gz', str(seat), sys.argv[2]], capture_output=True, text=True, timeout=900)
    try: res = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: return dict(ep=ep, error=r.stderr[-300:])
    res.update(ep=ep, team=team, cand=sys.argv[1]); return res
with open(sys.argv[3], 'a') as f, ThreadPoolExecutor(int(sys.argv[4]) if len(sys.argv) > 4 else 2) as pool:
    for res in pool.map(one, PANEL):
        f.write(json.dumps(res) + '\n'); f.flush()
