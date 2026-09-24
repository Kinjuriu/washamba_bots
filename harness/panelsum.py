import json,sys,statistics as S,collections
for f in sys.argv[1:]:
    R=[json.loads(l) for l in open(f) if l.strip()]; R=[r for r in R if 'error' not in r]
    m=[r['ours_bank']-r['tape_bank'] for r in R]; drift=[r['tape_bank']-r['orig_tape_bank'] for r in R]
    w=sum(x>0 for x in m); by=collections.defaultdict(list)
    for r in R: by[r['team']].append(r['ours_bank']-r['tape_bank'])
    print(f"{f}: n={len(R)} wins {w} mean margin {S.mean(m):+.0f} median {S.median(m):+.0f} | ours mean {S.mean(r['ours_bank'] for r in R):.0f} | tape drift median {S.median(drift):+.0f} | "+' '.join(f"{k}:{S.mean(v):+.0f}" for k,v in by.items()))
