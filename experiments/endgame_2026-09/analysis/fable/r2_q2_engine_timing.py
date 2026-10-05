"""Round 2, Q2(a): when does consumption hit the recorded observations?
Engine: interpreter call with step_var=s runs unit actions, then market, then
_town_consume if s%4==0 (shops) / s%24==0 (town center); recorded row s+1.
Prediction: consumption-only inventory drops appear at rows t with (t-1)%4==0
(shops) and (t-1)%24==0 (town); earliest sell quoted on drained inventory is row t+1 (t+1 ≡ 2 mod 4).
Empirical check on one replay using early rows before either side can sell/buy the product."""
import gzip, json, collections, sys
ep = sys.argv[1] if len(sys.argv)>1 else '112194936'
d = json.load(gzip.open(f'/Users/stephanengugi/KagricultureLocalData/episodes/20260923T153431Z_top6/replays/{ep}.json.gz'))
steps = d['steps']
def inv(t, item): return steps[t][0]['observation']['market']['inventory'][item] if t>0 else 10000
# rows where each product's inventory DROPS, restricted to rows where neither player traded it
def traded(t, item):
    for seat in (0,1):
        for o in steps[t][seat]['action'].get('market',[]) or []:
            if isinstance(o,list) and len(o)>=2 and o[1]==item and o[0] in ('SELL','BUY_PRODUCT'):
                return True
    return False
for item in ('MELON','TOMATO','STRAWBERRY','WOOL'):
    drops = collections.Counter()
    n=0
    for t in range(2, 400):
        if traded(t,item): continue
        delta = inv(t,item)-inv(t-1,item)
        if delta < 0:
            drops[(t-1)%4 if item!='MELON' else (t-1)%24] += 1; n+=1
    print(item, 'drop rows, (t-1) mod', 4 if item!='MELON' else 24, ':', dict(drops), 'n=',n)
print('shops:', steps[300][0]['observation']['town']['unlocked_shops'])
