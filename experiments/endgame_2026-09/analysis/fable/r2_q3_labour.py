"""Round 2, Q3: executor targets from replays — waters per worker-turn, idle
worker-turns/day, action mix. Top-six seats (2 replays/team) vs W0 seats (6 replays)."""
import gzip, json, csv, collections
def analyze(base, pairs, label):
    agg=collections.Counter(); unit_turns=0; days=0; waters_day=collections.Counter()
    for ep,seat in pairs:
        d=json.load(gzip.open(f'{base}replays/{ep}.json.gz'))
        steps=d['steps']; days+=30
        for t in range(1,len(steps)):
            present=1+len(steps[t-1][seat]['observation']['farms'][seat]['hands'])
            unit_turns+=present
            a=steps[t][seat]['action']
            units=[a.get('farmer')]+(a.get('hands') or [])
            acted=0
            for u in units[:present]:
                if not (isinstance(u,list) and u): continue
                acted+=1
                op=u[0]
                if op in ('NORTH','SOUTH','EAST','WEST'): agg['MOVE']+=1
                elif op=='PASS': agg['PASS']+=1
                else:
                    agg[op]+=1
                    if op=='WATER': waters_day[(ep,seat,(t-1)//24)]+=1
            agg['NOSUBMIT']+=max(0,present-acted)
    idle=agg['PASS']+agg['NOSUBMIT']
    work=sum(v for k,v in agg.items() if k not in ('MOVE','PASS','NOSUBMIT'))
    print(f"\n== {label}: {len(pairs)} games, {unit_turns} unit-turns ==")
    print(f"waters/unit-turn {agg['WATER']/unit_turns:.3f} | waters/day {agg['WATER']/days:.1f}")
    print(f"idle% {100*idle/unit_turns:.1f} (PASS {100*agg['PASS']/unit_turns:.1f} + nosubmit {100*agg['NOSUBMIT']/unit_turns:.1f}) | move% {100*agg['MOVE']/unit_turns:.1f} | work% {100*work/unit_turns:.1f}")
    top=collections.Counter({k:v for k,v in agg.items() if k not in('MOVE','PASS','NOSUBMIT')})
    print('work mix/day:', {k: round(v/days,1) for k,v in top.most_common(10)})
B6='/Users/stephanengugi/KagricultureLocalData/episodes/20260923T153431Z_top6/'
rows=list(csv.DictReader(open(B6+'manifest.csv')))
sample={}
for r in rows:
    sample.setdefault(r['player'],[])
    if len(sample[r['player']])<2: sample[r['player']].append((r['episode_id'],int(r['player_seat'])))
for team,eps in sample.items(): analyze(B6, eps, team)
BW='/Users/stephanengugi/KagricultureLocalData/episodes/20260923T161855Z_washamba_vs_top6/'
w=[(r['episode_id'],int(r['player_seat'])) for r in csv.DictReader(open(BW+'manifest.csv'))
   if r['player']=='w0_v15stack_control.py' and r['category']=='competitive'][:6]
analyze(BW, w, 'W0 v15stack')
