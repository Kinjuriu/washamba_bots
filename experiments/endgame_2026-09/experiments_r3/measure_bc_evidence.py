"""R3 evidence: (B) CARE actions that are no-ops in W0 replays; (C) W0 goose count per day.
A CARE at row t by a unit standing on tile X succeeds iff X is an animal tile and
cared_today was False in obs[t-1] and no earlier unit this turn already cared X."""
import gzip, json, csv, collections
BW='/Users/stephanengugi/KagricultureLocalData/episodes/20260923T161855Z_washamba_vs_top6/'
eps=[(r['episode_id'],int(r['player_seat'])) for r in csv.DictReader(open(BW+'manifest.csv'))
     if r['player']=='w0_v15stack_control.py' and r['category']=='competitive'][:5]
tot=collections.Counter(); goose_days=collections.Counter(); gd_n=collections.Counter()
esc=0
for ep,seat in eps:
    d=json.load(gzip.open(f'{BW}replays/{ep}.json.gz'))
    steps=d['steps']
    prev_animals=set()
    for t in range(1,len(steps)):
        obs=steps[t-1][seat]['observation'] if seat==0 else steps[t-1][0]['observation']
        # farms are shared on obs[0]; private is per seat but we don't need it
        farm=steps[t-1][0]['observation']['farms'][seat]
        a=steps[t][seat]['action']
        units=[a.get('farmer')]+(a.get('hands') or [])
        poss=[farm['farmer']]+farm['hands']
        cared_this_turn=set()
        for i,u in enumerate(units):
            if not(isinstance(u,list) and u and u[0]=='CARE'): continue
            tot['issued']+=1
            if i>=len(poss): tot['noop_nounit']+=1; continue
            x,y=poss[i]
            tile=farm['tiles'][y][x]
            if not(isinstance(tile,dict) and 'animal' in tile): tot['noop_notanimal']+=1; continue
            if tile.get('cared_today') or (x,y) in cared_this_turn: tot['noop_dup']+=1; continue
            cared_this_turn.add((x,y)); tot['success']+=1
        # goose census + escapes at day boundaries
        if t%24==0:
            day=t//24-1
            cur=set()
            for y in range(10):
                for x in range(10):
                    tl=farm['tiles'][y][x]
                    if isinstance(tl,dict) and tl.get('animal')=='GOOSE': cur.add((x,y))
            goose_days[day]+=len(cur); gd_n[day]+=1
for k,v in sorted(tot.items()): print(k,v)
print('noop rate of issued:', round(100*(tot['issued']-tot['success'])/tot['issued'],1),'%')
print('W0 geese by day (mean over 5 games):', {d: round(goose_days[d]/gd_n[d],1) for d in sorted(goose_days) if d in (2,5,8,11,14,17,20,23,26,28)})
