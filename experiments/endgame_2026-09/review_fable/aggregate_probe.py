import json,glob,collections,statistics as st,itertools,random
def load(p): return [json.loads(l) for l in open(p) if l.strip() and '"error"' not in l]
G={'top six':load('probe_top6.jsonl'),'ranks 7-12':load('probe_r712.jsonl'),'W3 (ladder)':load('probe_w3.jsonl')}
med=lambda xs: st.median(xs) if xs else None
print("=== 1. Stranded value curve: median cash | value in shed+hands+on-tile | stranded share of (cash+stranded)")
for g,rs in G.items():
    line=[]
    for d in ('6','12','18','24','29'):
        cash=med([r['cps'][d]['cash'] for r in rs]); strand=med([r['cps'][d]['shed']+r['cps'][d]['inv']+r['cps'][d]['tile'] for r in rs])
        share=med([(r['cps'][d]['shed']+r['cps'][d]['inv']+r['cps'][d]['tile'])/max(1,r['cps'][d]['cash']+r['cps'][d]['shed']+r['cps'][d]['inv']+r['cps'][d]['tile']) for r in rs])
        line.append(f"d{d}: {cash/1000:5.1f}k|{strand/1000:4.1f}k|{share:4.0%}")
    print(f"{g:12s} n={len(rs):3d} "+"  ".join(line)+f"  terminal unsold med ${med([r['terminal_unsold'] for r in rs]):.0f}")
print("\n=== 2. Shed-to-sale lag (steps, FIFO) per premium product: median | share sold within 6 | within 24")
for p in ('WOOL','MILK','STRAWBERRY','MELON'):
    for g,rs in G.items():
        L=[r['lags'][p] for r in rs if r['lags'][p][0] is not None]
        if L: print(f"  {p:10s} {g:12s} median {med([x[0] for x in L]):4.0f}  <=6: {med([x[1] for x in L]):.2f}  <=24: {med([x[2] for x in L]):.2f}  (units/game med {med([x[3] for x in L]):.0f})")
print("\n=== 3. Sale-order structure per premium product (medians over games): events/game | fraction of shed sold per event | share of full dumps | price/base at sale | share at post-drain hour | share within 2 steps AFTER opp sale | BEFORE opp sale | same step")
for p in ('WOOL','MILK','STRAWBERRY','MELON'):
    for g,rs in G.items():
        S=[r['struct'][p] for r in rs if p in r['struct']]
        if S: print(f"  {p:10s} {g:12s} n_ev {med([s['n'] for s in S]):4.0f} frac {med([s['frac_med'] for s in S]):.2f} full {med([s['full'] for s in S]):.2f} p/b {med([s['pb_med'] for s in S]):.2f} h2 {med([s['h2'] for s in S]):.2f} after {med([s['after_opp'] for s in S]):.2f} before {med([s['before_opp'] for s in S]):.2f} same {med([s['same_step'] for s in S]):.2f}")
print("\n=== 4. Price sensitivity: P(sell this step | holding stock) when price>=base vs price<0.6*base (pooled steps)")
for p in ('WOOL','MILK','STRAWBERRY'):
    for g,rs in G.items():
        hi=[0,0]; lo=[0,0]
        for r in rs:
            s=r['struct'].get(p)
            if not s: continue
            if s['p_sell_hi'][0] is not None: hi[0]+=s['p_sell_hi'][1]; hi[1]+=s['p_sell_hi'][0]*s['p_sell_hi'][1]
            if s['p_sell_lo'][0] is not None: lo[0]+=s['p_sell_lo'][1]; lo[1]+=s['p_sell_lo'][0]*s['p_sell_lo'][1]
        print(f"  {p:10s} {g:12s} P(sell|>=base)={hi[1]/max(1,hi[0]):.3f} (steps {hi[0]})  P(sell|<0.6 base)={lo[1]/max(1,lo[0]):.3f} (steps {lo[0]})")
print("\n=== 5. Herd at day 12 vs shops unlocked by day 9 (per team: mean count when shop count is 0 vs >=1)")
def cond(rs,animal,shopkey):
    a=[r['herd12'].get(animal,0) for r in rs if r['shops9'][shopkey]==0]; b=[r['herd12'].get(animal,0) for r in rs if r['shops9'][shopkey]>=1]
    return (f"{st.mean(a):.1f}(n{len(a)})" if a else "-", f"{st.mean(b):.1f}(n{len(b)})" if b else "-")
teams=collections.defaultdict(list)
for g,rs in G.items():
    for r in rs: teams[r['name']].append(r)
for t,rs in teams.items():
    if len(rs)<20: continue
    print(f"  {t[:22]:22s} sheep|yarn0/1 {cond(rs,'SHEEP','yarn')}  cows|milk0/1 {cond(rs,'COW','milk')}  geese|egg0/1 {cond(rs,'GOOSE','egg')}")
print("\n=== 6. Land purchases: day of 1st/2nd/3rd purchase (median, IQR) and money just before")
for t,rs in teams.items():
    if len(rs)<20: continue
    for i in range(3):
        L=[r['land'][i] for r in rs if len(r['land'])>i]
        if len(L)>=5:
            days=sorted(x['day']*24+x['hour'] for x in L); mb=sorted(x['money_before'] for x in L)
            print(f"  {t[:22]:22s} purchase {i+1}: n={len(L)} step med {days[len(days)//2]} (q1 {days[len(days)//4]}, q3 {days[3*len(days)//4]})  money_before med {mb[len(mb)//2]:.0f} (q1 {mb[len(mb)//4]:.0f}, q3 {mb[3*len(mb)//4]:.0f})")
print("\n=== 7. Within-team labour-action agreement across games (pairs of games; same first shop vs different), windows 0-71 / 72-143 / 144-400 / 400-718")
random.seed(3)
for t,rs in teams.items():
    if len(rs)<20: continue
    pairs=list(itertools.combinations(range(len(rs)),2)); random.shuffle(pairs); pairs=pairs[:150]
    agg={'same':collections.defaultdict(list),'diff':collections.defaultdict(list)}
    for i,j in pairs:
        a,b=rs[i],rs[j]
        if a['ep']==b['ep']: continue
        key='same' if a['first_shop']==b['first_shop'] else 'diff'
        for w,(lo,hi) in {'0-71':(0,71),'72-143':(71,143),'144-400':(143,400),'400-718':(400,718)}.items():
            ha=a['labour_hash'][lo:hi]; hb=b['labour_hash'][lo:hi]
            agg[key][w].append(sum(1 for x,y in zip(ha,hb) if x==y)/len(ha))
    print(f"  {t[:22]:22s} same-shop pairs n={len(agg['same']['0-71'])}: "+" ".join(f"{w}={st.mean(v):.2f}" for w,v in agg['same'].items())+f" | diff-shop n={len(agg['diff']['0-71'])}: "+" ".join(f"{w}={st.mean(v):.2f}" for w,v in agg['diff'].items()))
