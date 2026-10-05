"""Overnight: evaluate candidates on the band panel (W3's real ladder opponents, tape family, 2,200-2,800,
replayed as recorded tapes on their original seed/seat). Objective = points (win 1, tie .5), paired with W3.
Stages: (1) PR63 and W4 on the full panel; (2) random constant search on half A; (3) top 4 on half B;
(4) finalists on the ranks-7-12 panel. Resumable: skips (ep, cand) pairs already in the results files."""
import json, os, random, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
BAND = json.load(open('band_panel.json'))            # [ep, opp_seat, sub, rating, team]
RB = '/mnt/user-data/uploads/KagricultureLocalData/episodes/20260924T161358Z_washamba_0924b/replays/'
R7 = json.load(open('/mnt/user-data/uploads/KagricultureLocalData/review_fable/r7to12_panel.json'))  # [ep, seat, team, fam]
RR = '/mnt/user-data/uploads/KagricultureLocalData/episodes/20260924T161358Z_ranks7to12/replays/'
eps = sorted(p[0] for p in BAND)
HALF_A = set(eps[0::2]); HALF_B = set(eps[1::2])
WORKERS = 2
def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)
def done_pairs(fn):
    s = set()
    if os.path.exists(fn):
        for l in open(fn):
            try: r = json.loads(l); s.add((r['ep'], r['cand']))
            except Exception: pass
    return s
def run_panel(items, replay_dir, cands, out):
    seen = done_pairs(out)
    jobs = [(it, c) for c in cands for it in items if (it[0], c) not in seen]
    def one(job):
        it, c = job
        r = subprocess.run([sys.executable, 'tapeopp.py', replay_dir + it[0] + '.json.gz', str(it[1]), cands[c]],
                           capture_output=True, text=True, timeout=1500)
        try: res = json.loads(r.stdout.strip().splitlines()[-1])
        except Exception: return dict(ep=it[0], cand=c, error=r.stderr[-300:])
        res.update(ep=it[0], cand=c); return res
    with open(out, 'a') as f, ThreadPoolExecutor(WORKERS) as pool:
        for res in pool.map(one, jobs):
            f.write(json.dumps(res) + '\n'); f.flush()
SPACE = {
    "V9_CARROT_RATIO": [1.4, 1.6, 2.0, 2.4], "V9_CARROT_FIRST_DAY": [8, 12], "V9_CARROT_LAST_DAY": [20, 26],
    "V9_CARROT_WHEAT_RESERVE": [25, 60], "V9_HERD_MIN_WOOL": [120, 180], "V9_HERD_MIN_MILK": [120, 180],
    "V9_FERT_FIRST_DAY": [10, 18], "_HD2_RATIO": [1.15, 1.5], "_HD2_MIN_GAIN": [300.0, 1000.0],
    "_CS_RATIO": [1.15, 1.5], "_CA_MARGIN": [-25.0, -5.0], "_CA_CASH": [400, 1500], "_OR2_SLOT_MARGIN": [4.0, 12.0],
    "_SR_MARGIN": [4, 12], "_CXTB_MIN_REVENUE": [6000, 12000], "_Y_MARGIN": [-10, -2], "_HP_WINDOW": [6],
    "V9_RACE_DEFAULT": [40, 48], "_V92_P_K": [3, 5], "V9_COURIER_FROM_HOUR": [10, 14],
}
def patch(src, params):
    lines = src.split('\n')
    for k, v in params.items():
        idx = [i for i, l in enumerate(lines) if re.match(r'^%s\s*=\s*-?[0-9.]+' % re.escape(k), l)]
        i = idx[-1]
        lines[i] = re.sub(r'^(%s\s*=\s*)-?[0-9.]+' % re.escape(k), r'\g<1>%s' % v, lines[i])
    return '\n'.join(lines)
def score(out, cand, subset):
    R = {}
    for l in open(out):
        r = json.loads(l)
        if 'error' not in r and r['ep'] in subset: R[(r['ep'], r['cand'])] = r
    base = {}
    for l in open('band_results.jsonl'):
        r = json.loads(l)
        if r.get('cand') == 'w3' and 'error' not in r and r['ep'] in subset: base[r['ep']] = r
    def pts(r): d = r['ours_bank'] - r['tape_bank']; return 1 if d > 0 else .5 if d == 0 else 0
    def fa(r): return abs(r['tape_bank'] - r['orig_tape_bank']) <= 0.05 * r['orig_tape_bank']
    n = pc = pb = up = dn = 0; dm = 0.0
    for ep, b in base.items():
        c = R.get((ep, cand))
        if not c or not (fa(b) and fa(c)): continue
        n += 1; pc += pts(c); pb += pts(b); up += pts(c) > pts(b); dn += pts(c) < pts(b)
        dm += (c['ours_bank'] - c['tape_bank']) - (b['ours_bank'] - b['tape_bank'])
    errs = sum(1 for l in open(out) if '"error"' in l and ('"cand": "%s"' % cand) in l)
    return dict(cand=cand, n=n, cand_pts=pc, w3_pts=pb, diff=pc - pb, up=up, down=dn, mean_margin_change=round(dm / max(n, 1)), errors=errs)
def main():
    os.makedirs('cands', exist_ok=True)
    src = open('w3.py').read()
    # stage 1
    log('stage 1: PR63 and W4 on the full band panel')
    run_panel(BAND, RB, {'pr63': 'pr63.py', 'combo': 'combo.py'}, 'band_results2.jsonl')
    s1 = [score('band_results2.jsonl', c, set(eps)) for c in ('pr63', 'w4', 'combo')]
    s1.append(score('band_results.jsonl', 'hf_early', set(eps)))
    json.dump(s1, open('stage1_summary.json', 'w'), indent=1); log('stage 1', s1)
    # stage 2
    rng = random.Random(20260926); params = {}
    N = int(os.environ.get('N_CANDS', '26'))
    while len(params) < N:
        k = rng.choice([1, 1, 2, 2, 3])
        p = {n: rng.choice(SPACE[n]) for n in rng.sample(sorted(SPACE), k)}
        key = json.dumps(p, sort_keys=True)
        if key in [json.dumps(v, sort_keys=True) for v in params.values()]: continue
        name = 's%02d' % len(params); params[name] = p
        open('cands/%s.py' % name, 'w').write(patch(src, p))
    json.dump(params, open('stage2_params.json', 'w'), indent=1)
    A = [b for b in BAND if b[0] in HALF_A]
    for name in params:
        log('stage 2', name, params[name])
        run_panel(A, RB, {name: 'cands/%s.py' % name}, 'search_A.jsonl')
        sc = score('search_A.jsonl', name, HALF_A); sc['params'] = params[name]
        with open('stage2_summary.jsonl', 'a') as f: f.write(json.dumps(sc) + '\n')
        log('   ', sc)
    S2 = [json.loads(l) for l in open('stage2_summary.jsonl')]
    top = sorted(S2, key=lambda s: (-s['diff'], -s['mean_margin_change']))[:4]
    # stage 3
    B = [b for b in BAND if b[0] in HALF_B]
    for s in top:
        log('stage 3', s['cand'])
        run_panel(B, RB, {s['cand']: 'cands/%s.py' % s['cand']}, 'search_B.jsonl')
        sc = score('search_B.jsonl', s['cand'], HALF_B); sc['params'] = s['params']; sc['half_A'] = s
        with open('stage3_summary.jsonl', 'a') as f: f.write(json.dumps(sc) + '\n')
        log('   ', sc)
    # stage 4: ranks-7-12 panel for any candidate not worse on both halves, plus PR63/W4 already known
    S3 = [json.loads(l) for l in open('stage3_summary.jsonl')]
    fin = {s['cand']: 'cands/%s.py' % s['cand'] for s in S3 if s['diff'] >= 0 and s['half_A']['diff'] > 0}
    log('stage 4 finalists', list(fin))
    if fin: run_panel(R7, RR, fin, 'r7_results.jsonl')
    log('all done')
if __name__ == '__main__':
    main()
