import json, collections, statistics as S, math
R=[json.loads(l) for l in open('band_results.jsonl') if 'error' not in l]
by=collections.defaultdict(dict)
for r in R: by[r['ep']][r['cand']]=r
def faithful(r): return abs(r['tape_bank']-r['orig_tape_bank'])<=0.05*r['orig_tape_bank']
def pts(r): d=r['ours_bank']-r['tape_bank']; return 1 if d>0 else .5 if d==0 else 0
pairs=[(e,v['w3'],v['hf_early']) for e,v in by.items() if 'w3' in v and 'hf_early' in v]
fp=[(e,a,b) for e,a,b in pairs if faithful(a) and faithful(b)]
print('pairs',len(pairs),'faithful under both',len(fp))
for name,sub in [('all',fp),('W3 originals',[x for x in fp if 'W3' in x[1]['orig_sub']]),('W0/W1 originals',[x for x in fp if 'W3' not in x[1]['orig_sub']]),
                 ('opp<2500',[x for x in fp if x[1]['opp_rating']<2500]),('opp>=2500',[x for x in fp if x[1]['opp_rating']>=2500])]:
    if not sub: continue
    w3=sum(pts(a) for e,a,b in sub); hf=sum(pts(b) for e,a,b in sub)
    flips_up=sum(pts(b)>pts(a) for e,a,b in sub); flips_dn=sum(pts(b)<pts(a) for e,a,b in sub)
    dm=[(b['ours_bank']-b['tape_bank'])-(a['ours_bank']-a['tape_bank']) for e,a,b in sub]
    near=sum(abs(a['ours_bank']-a['tape_bank'])<500 for e,a,b in sub)
    print(f"{name:16s} n={len(sub):3d} W3 pts {w3:5.1f} ({w3/len(sub):.3f})  hf_early pts {hf:5.1f} ({hf/len(sub):.3f})  flips +{flips_up}/-{flips_dn}  margin change mean {S.mean(dm):+.0f} median {S.median(dm):+.0f}  W3 near-ties {near}")
# W3 fidelity: games originally played by W3 should reproduce exactly
ex=[a for e,a,b in pairs if 'W3' in a['orig_sub']]
print('W3-original games reproduced exactly:', sum(abs(a['ours_bank']-a['orig_opp_bank'])<1 for a in ex), 'of', len(ex))
