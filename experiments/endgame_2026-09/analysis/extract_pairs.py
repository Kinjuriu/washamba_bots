"""Per episode and seat: estimated sell revenue by product and phase, plus asset snapshots at day 6/12/18/24.
Revenue estimate = min(requested, shed+worker inventories) * quoted price that turn (upper bound)."""
import gzip, json, csv, os, collections, glob
BASE=os.path.expanduser('~/mnt/KagricultureLocalData/episodes'); OUT=os.path.expanduser('~/mnt/KagricultureLocalData/analysis')
P=['WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL','FERTILIZER']
names={}
for r in csv.DictReader(open(BASE+'/manifest.csv')):
    names[(r['episode_id'],int(r['player_seat']))]=r['player']; names[(r['episode_id'],int(r['opponent_seat']))]=r['opponent_name']
SN=(143,287,431,575)
keys=['episode','seat','name','bank','opp_bank','won','tie','shops']+['rev_'+p for p in P]+['units_'+p for p in P]+['first_'+p for p in P]+['rev_d00','rev_d10','rev_d20']
keys+=['%s_t%d'%(a,t+1) for t in SN for a in ['crop_WHEAT','crop_CARROT','crop_TOMATO','crop_STRAWBERRY','crop_MELON','ani_COW','ani_SHEEP','ani_GOOSE','hands','money','quads']]
f=open(OUT+'/pairs.csv','w',newline=''); w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore',restval=0); w.writeheader()
for path in sorted(glob.glob(BASE+'/replays/*.json.gz')):
    ep=os.path.basename(path).split('.')[0]; d=json.load(gzip.open(path)); st=d['steps']; rw=d['rewards']
    for s in (0,1):
        rev=collections.Counter(); units=collections.Counter(); ph=collections.Counter(); first={}; rec={}
        for t in range(720):
            ob=st[t][s]['observation']; act=st[t][s].get('action') or {}
            shed=ob['private']['shed']; inv=collections.Counter()
            for x in ob['private'].get('inventories',[]):
                for k,v in x.items(): inv[k]+=v
            pr=ob['market']['prices']
            for od in (act.get('market') or []):
                if od and od[0]=='SELL' and len(od)>1 and od[1] in P:
                    q=od[2] if len(od)>2 else 1; e=min(q,shed.get(od[1],0)+inv.get(od[1],0))
                    if e>0:
                        rev[od[1]]+=e*pr[od[1]]; units[od[1]]+=e; ph['rev_d%02d'%(10*(t//240))]+=e*pr[od[1]]; first.setdefault(od[1],t)
            if t in SN:
                farm=ob['farms'][s]
                for row in farm['tiles']:
                    for tl in row:
                        if isinstance(tl,dict):
                            if tl.get('crop'): rec['crop_%s_t%d'%(tl['crop'],t+1)]=rec.get('crop_%s_t%d'%(tl['crop'],t+1),0)+1
                            if tl.get('animal'): rec['ani_%s_t%d'%(tl['animal'],t+1)]=rec.get('ani_%s_t%d'%(tl['animal'],t+1),0)+1
                rec['hands_t%d'%(t+1)]=farm.get('hires_today'); rec['money_t%d'%(t+1)]=farm['money']; rec['quads_t%d'%(t+1)]=len(farm['unlocked_quadrants'])
        rec.update(episode=ep,seat=s,name=names.get((ep,s),'?'),bank=rw[s],opp_bank=rw[1-s],won=int(rw[s]>rw[1-s]),tie=int(rw[s]==rw[1-s]),
                   shops='|'.join(st[719][s]['observation']['town']['unlocked_shops']))
        for p in P: rec['rev_'+p]=rev[p]; rec['units_'+p]=units[p]; rec['first_'+p]=first.get(p,-1)
        rec.update(ph); w.writerow(rec)
f.close(); print('done')
