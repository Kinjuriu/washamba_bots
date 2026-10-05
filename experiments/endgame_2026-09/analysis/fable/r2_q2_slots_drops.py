"""Round 2, Q2(b,c): premium sell slot indices (top6 seat vs opponent seat),
same-turn same-product collisions, and DROP-action hour timing. Sample: first
3 replays per team from the top6 manifest."""
import gzip, json, csv, collections, statistics as st
BASE='/Users/stephanengugi/KagricultureLocalData/episodes/20260923T153431Z_top6/'
PREM=('WOOL','MILK','STRAWBERRY')
rows=list(csv.DictReader(open(BASE+'manifest.csv')))
sample={}
for r in rows:
    sample.setdefault(r['player'],[])
    if len(sample[r['player']])<3: sample[r['player']].append((r['episode_id'],int(r['player_seat'])))
slot=collections.defaultdict(list); coll=[]; drophr=collections.Counter(); drophr_opp=collections.Counter()
sellhr=collections.Counter()
for team,eps in sample.items():
    for ep,seat in eps:
        d=json.load(gzip.open(f'{BASE}replays/{ep}.json.gz'))
        for t in range(1,len(d['steps'])):
            per={}
            for s in (0,1):
                a=d['steps'][t][s]['action']
                m=a.get('market') or []
                for i,o in enumerate(m):
                    if isinstance(o,list) and o and o[0]=='SELL' and len(o)>=2 and o[1] in PREM:
                        slot['top6' if s==seat else 'opp'].append(i)
                        per.setdefault(o[1],{})[s]=i
                        if s==seat: sellhr[t%24]+=1
                fa=[a.get('farmer')]+ (a.get('hands') or [])
                nd=sum(1 for u in fa if isinstance(u,list) and u and u[0]=='DROP')
                if nd: (drophr if s==seat else drophr_opp)[t%24]+=nd
            for item,d2 in per.items():
                if len(d2)==2: coll.append((d2[seat],d2[1-seat]))
for k,v in slot.items():
    print(k,'premium sell slots: median',st.median(v),'mean',round(st.mean(v),2),
          'slot0 %',round(100*sum(1 for x in v if x==0)/len(v)),'n',len(v))
print('same-turn same-premium collisions:',len(coll),
      'top6 earlier slot:',sum(1 for a,b in coll if a<b),
      'equal:',sum(1 for a,b in coll if a==b),
      'later:',sum(1 for a,b in coll if a>b))
def h4(c): 
    tot=sum(c.values()); return {m: round(100*sum(v for h,v in c.items() if h%4==m)/tot) for m in range(4)}
print('top6 DROP actions by hour mod 4 (%):',h4(drophr),'n=',sum(drophr.values()))
print('opp  DROP actions by hour mod 4 (%):',h4(drophr_opp),'n=',sum(drophr_opp.values()))
print('top6 premium SELL by hour mod 4 (%):',h4(sellhr),'n=',sum(sellhr.values()))
