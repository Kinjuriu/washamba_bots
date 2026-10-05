"""Recorded-opponent panels with fidelity check. Usage: panel.py {ladder|band} out.jsonl workers name=path ...
ladder: Step1009's own 48 ladder games (tonight_0928/lad.jsonl), tape = the non-washamba seat.
band:   review_claude/results/band_panel.json (221+ tape-family games rated 2,200-2,800).
Resumable; faithful = tape bank within 5% of its original bank."""
import json, sys, os, gzip, subprocess
from concurrent.futures import ThreadPoolExecutor
kind, out, workers = sys.argv[1], sys.argv[2], int(sys.argv[3])
cands = dict(a.split('=', 1) for a in sys.argv[4:])
jobs = []
if kind == 'ladder':
    R = 'episodes/20260928_ladder_check/replays/'
    eps = sorted({json.loads(l)['ep'] for l in open('tonight_0928/lad.jsonl')})
    for ep in eps:
        d = json.load(gzip.open(R + ep + '.json.gz'))
        names = d['info']['TeamNames']; seat = 0 if names[1].lower().startswith('washamba') else 1
        jobs.append((R + ep + '.json.gz', seat, ep, names[seat]))
else:
    R = 'episodes/20260924T161358Z_washamba_0924b/replays/'
    for ep, seat, sub, rating, team in json.load(open('review_claude/results/band_panel.json')):
        jobs.append((R + ep + '.json.gz', seat, ep, f'{team}@{rating}'))
done = set()
if os.path.exists(out):
    for l in open(out):
        r = json.loads(l); done.add((r['ep'], r['cand']))
todo = [(j, c) for j in jobs for c in cands if (j[2], c) not in done]
print(len(todo), 'games to run', flush=True)
def one(job):
    (path, seat, ep, team), c = job
    r = subprocess.run([sys.executable, 'harness/tapeopp.py', path, str(seat), cands[c]], capture_output=True, text=True, timeout=1200)
    try: res = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: return dict(ep=ep, cand=c, error=r.stderr[-300:])
    res.update(ep=ep, cand=c, team=team); return res
with open(out, 'a') as f, ThreadPoolExecutor(workers) as pool:
    for res in pool.map(one, todo):
        f.write(json.dumps(res) + '\n'); f.flush()
# summary: per candidate W-L-T on faithful games, and paired flips vs the first candidate listed
rows = [json.loads(l) for l in open(out)]
by = {}
for r in rows:
    if 'error' in r: continue
    by.setdefault(r['cand'], {})[r['ep']] = r
def faithful(r): return abs(r['tape_bank'] - r['orig_tape_bank']) <= 0.05 * max(1, abs(r['orig_tape_bank']))
for c, m in by.items():
    fw = [r for r in m.values() if faithful(r)]
    w = sum(r['ours_bank'] > r['tape_bank'] for r in fw); l = sum(r['ours_bank'] < r['tape_bank'] for r in fw); t = len(fw) - w - l
    exact = sum(r['tape_bank'] == r['orig_tape_bank'] for r in m.values())
    print(f"{c}: faithful {len(fw)}/{len(m)} (exact {exact}) W-L-T {w}-{l}-{t} points {(w+0.5*t)/max(1,len(fw)):.3f} mean margin {sum(r['ours_bank']-r['tape_bank'] for r in fw)/max(1,len(fw)):+.0f}")
names = list(by)
for c in names[1:]:
    base = by[names[0]]; up = down = same = 0; dm = 0; n = 0
    for ep, r in by[c].items():
        if ep not in base or not (faithful(r) and faithful(base[ep])): continue
        pb = (base[ep]['ours_bank'] > base[ep]['tape_bank']) + 0.5 * (base[ep]['ours_bank'] == base[ep]['tape_bank'])
        pc = (r['ours_bank'] > r['tape_bank']) + 0.5 * (r['ours_bank'] == r['tape_bank'])
        up += pc > pb; down += pc < pb; same += pc == pb; dm += (r['ours_bank'] - r['tape_bank']) - (base[ep]['ours_bank'] - base[ep]['tape_bank']); n += 1
    print(f"  {c} vs {names[0]} on {n} paired faithful games: better {up} worse {down} same {same}, mean margin change {dm/max(1,n):+.0f}")
