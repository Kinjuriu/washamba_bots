import json,glob,collections,statistics as st,sys
rows=[]
for p in glob.glob('corpus_summary_*.jsonl'):
    for l in open(p):
        r=json.loads(l)
        if "error" not in r: rows.append(r)
games=collections.defaultdict(list)
for r in rows: games[r['ep']].append(r)
full=[g for g in games.values() if len(g)==2]
print("games",len(full),"exact",sum(1 for g in full if g[0]['exact']))
TOP=['Boey','M & M & P & Q','DSM','Unknown Mother-Goose','DECEM','吃白饭的大肥鱼']
R712=['Kaggledew Valley 🏆','Kaggledew Valley','Azat Akhtyamov','THIRD FARM CLUB','Arda Ceylan','mtmr_s1','TheEggman']
def grp(name):
    if name=='washamba_bots': return 'washamba'
    if name in TOP: return 'top6'
    if name in R712: return 'r7-12'
    return 'opp'
# seat-0 win rate
s0=[1 if g[0]['bank']>g[0]['opp_bank'] else 0 for g in full if g[0]['bank']!=g[0]['opp_bank']]
print("seat0 win rate %.3f n=%d, exact ties %d"%(sum(s0)/len(s0),len(s0),sum(1 for g in full if g[0]['bank']==g[0]['opp_bank'])))
def med(xs): return round(st.median(xs)) if xs else None
def summarize(rs,label):
    n=len(rs); 
    if n==0: return
    banks=[r['bank'] for r in rs]; wins=sum(1 for r in rs if r['bank']>r['opp_bank'])
    land2=[r['land_days'][1] if len(r['land_days'])>1 else None for r in rs]; land3=sum(1 for r in rs if len(r['land_days'])>=3)
    def tiles(day,key): return [r[day].get(key,0) for r in rs]
    rev=collections.defaultdict(list); units=collections.defaultdict(list)
    for r in rs:
        for k in ['WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL','FERTILIZER']:
            v=r['sold'].get(k,[0,0]); rev[k].append(v[1]); units[k].append(v[0])
    wb=[r['bought'].get('WHEAT',[0,0]) for r in rs]
    anim_d10=[sum(r['tiles_d10'].get(a,0) for a in ('GOOSE','COW','SHEEP')) for r in rs]
    anim_d20=[sum(r['tiles_d20'].get(a,0) for a in ('GOOSE','COW','SHEEP')) for r in rs]
    feed_per=[r['feed_actions']/max(1,(sum(r['tiles_d10'].get(a,0) for a in ('GOOSE','COW','SHEEP'))+sum(r['tiles_d20'].get(a,0) for a in ('GOOSE','COW','SHEEP')))/2*26) for r in rs]
    care_per=[r['care_actions']/max(1,(sum(r['tiles_d10'].get(a,0) for a in ('GOOSE','COW','SHEEP'))+sum(r['tiles_d20'].get(a,0) for a in ('GOOSE','COW','SHEEP')))/2*26) for r in rs]
    early=[sum(r['rev_by_day'][:10]) for r in rs]
    print(f"\n== {label}: n={n} win%={wins/n:.2f} bank med={med(banks)} | land2 day med={med([x for x in land2 if x is not None])} 3rd-quadrant {land3}/{n} | peak hands med={med([r['peak_hands'] for r in rs])} hires/season med={med([r['hires_total'] for r in rs])}")
    print(f"   geese d10/d20 med={med(tiles('tiles_d10','GOOSE'))}/{med(tiles('tiles_d20','GOOSE'))} cows {med(tiles('tiles_d10','COW'))}/{med(tiles('tiles_d20','COW'))} sheep {med(tiles('tiles_d10','SHEEP'))}/{med(tiles('tiles_d20','SHEEP'))} animals d10/d20 {med(anim_d10)}/{med(anim_d20)}")
    print(f"   plants req med: "+" ".join(f"{k}={med([r['plants_req'].get(k,0) for r in rs])}" for k in ['WHEAT','CARROT','TOMATO','STRAWBERRY','MELON']))
    print(f"   revenue med: "+" ".join(f"{k}={med(rev[k])}" for k in rev))
    print(f"   units med:   "+" ".join(f"{k}={med(units[k])}" for k in units))
    print(f"   avg price: "+" ".join(f"{k}={round(sum(rev[k])/max(1,sum(units[k])))}" for k in rev))
    print(f"   wheat bought med units={med([w[0] for w in wb])} spend={med([w[1] for w in wb])} | fert actions med={med([r['fert_actions'] for r in rs])} feed/animal-day~{st.median(feed_per):.2f} care/animal-day~{st.median(care_per):.2f} | rev d0-9 med={med(early)}")
for label,pred in [('top6 seats',lambda r:grp(r['name'])=='top6'),('ranks7-12 seats',lambda r:grp(r['name'])=='r7-12'),('washamba seats',lambda r:grp(r['name'])=='washamba'),('opponents of washamba',lambda r:grp(r['opp'])=='washamba'),('opponents of top6 (non-top)',lambda r:grp(r['opp'])=='top6' and grp(r['name'])=='opp')]:
    summarize([r for r in rows if pred(r)],label)
# top6 vs tape-family-like opponents? can't know family here; use per-team
for t in TOP+R712:
    rs=[r for r in rows if r['name']==t]
    if rs: summarize(rs,t)
