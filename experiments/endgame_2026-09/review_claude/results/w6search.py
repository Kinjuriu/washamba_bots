import json, re, os, overnight as o
src = open('subs/w6_herdsafe_frontrun.py').read()
V = {'k4': {'WB_FRONTRUN_K': 4}, 'k9': {'WB_FRONTRUN_K': 9}, 'k12': {'WB_FRONTRUN_K': 12},
     'q2': {'WB_FRONTRUN_MIN_QTY': 2}, 'q7': {'WB_FRONTRUN_MIN_QTY': 7}, 'd01': {'WB_FRONTRUN_MIN_DROP': 0.01}}
def patch(s, p):
    for k, v in p.items():
        s, n = re.subn(r'^(%s\s*=\s*)[-0-9.]+' % k, r'\g<1>%s' % v, s, flags=re.M); assert n == 1, k
    return s
for n, p in V.items(): open('v6/%s.py' % n, 'w').write(patch(src, p))
# w6 itself on the band panel = pr63 results (same body); copy those rows under name w6
A = [b for b in o.BAND if b[0] in o.HALF_A]; B = [b for b in o.BAND if b[0] in o.HALF_B]
for n in V:
    o.run_panel(A, o.RB, {n: 'v6/%s.py' % n}, 'v6_A.jsonl')
    s = o.score('v6_A.jsonl', n, o.HALF_A); s['params'] = V[n]
    s['pr63_same_half'] = o.score('band_results2.jsonl', 'pr63', o.HALF_A)['diff']
    open('v6_A_summary.jsonl', 'a').write(json.dumps(s) + '\n'); o.log(s)
S = sorted([json.loads(l) for l in open('v6_A_summary.jsonl')], key=lambda s: -s['diff'])[:2]
for s in S:
    o.run_panel(B, o.RB, {s['cand']: 'v6/%s.py' % s['cand']}, 'v6_B.jsonl')
    t = o.score('v6_B.jsonl', s['cand'], o.HALF_B); t['pr63_same_half'] = o.score('band_results2.jsonl', 'pr63', o.HALF_B)['diff']
    open('v6_B_summary.jsonl', 'a').write(json.dumps(t) + '\n'); o.log(t)
o.log('w6search done')
