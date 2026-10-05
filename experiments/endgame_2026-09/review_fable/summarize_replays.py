"""Exact re-simulation summarizer (review_fable). For each replay: per-player revenue by product,
units, purchases, land days, animals placed, peak hands, plant counts, first-sale steps.
Usage: python summarize_replays.py out.jsonl file1.json.gz file2.json.gz ..."""
import gzip, json, sys, collections, os
import kaggle_environments.envs.kaggriculture.kaggriculture as K
from kaggle_environments import make
LOG=[]; CUR={'step':0,'farms':None}
_pm=K._process_market; _cu=K._commit_unit
def pm(state, env):
    CUR['farms']=[id(f) for f in state[0].observation.farms]; return _pm(state, env)
def cu(op,item,price,farm,private,market,shed_capacity=100):
    ok=_cu(op,item,price,farm,private,market,shed_capacity)
    if ok: LOG.append((CUR['step'], CUR['farms'].index(id(farm)), op, item, price))
    return ok
K._process_market=pm; K._commit_unit=cu
def summarize(path):
    ep=os.path.basename(path).split('.')[0]
    d=json.load(gzip.open(path)); st=d['steps']
    acts=[[st[t][s]['action'] for t in range(len(st))] for s in (0,1)]
    def mk(s):
        def a(obs,cfg):
            CUR['step']=obs['step']+1
            return acts[s][obs['step']+1] if obs['step']+1<len(acts[s]) else {'farmer':['PASS'],'hands':[],'market':[]}
        return a
    LOG.clear(); env=make('kaggriculture',configuration={'seed':d['info']['seed']},debug=False); env.run([mk(0),mk(1)])
    exact=[env.steps[-1][0].reward, env.steps[-1][1].reward]==d['rewards']
    shops=env.steps[-1][0].observation['town']['unlocked_shops']
    out=[]
    for s in (0,1):
        rec=dict(ep=ep,seat=s,name=d['info']['TeamNames'][s],opp=d['info']['TeamNames'][1-s],bank=d['rewards'][s],opp_bank=d['rewards'][1-s],exact=exact,seed=d['info']['seed'],shops=shops)
        items=collections.defaultdict(lambda:[0,0]); buys=collections.defaultdict(lambda:[0,0]); spend=collections.Counter(); first={}; rev_by_day=collections.Counter()
        for (t,p,op,item,price) in LOG:
            if p!=s: continue
            if op=='SELL':
                items[item][0]+=1; items[item][1]+=price; rev_by_day[t//24]+=price
                first.setdefault(item,t)
            elif op=='BUY_PRODUCT': buys[item][0]+=1; buys[item][1]+=price
            else: spend[op+'_'+item]+=price
        rec['sold']={k:v for k,v in items.items()}; rec['bought']={k:v for k,v in buys.items()}; rec['spend']=dict(spend); rec['first_sale']=first
        rec['rev_by_day']=[rev_by_day.get(i,0) for i in range(30)]
        # land, hands, animals, plants from recorded observations
        land=[]; prevq=1; peak=0; hires=collections.Counter(); plants=collections.Counter(); anim_placed=collections.Counter(); wheat_fed=0; fert_used=0; care=0
        anim_by_day={}
        for t in range(len(st)):
            o=st[t][s]['observation'] if 'farms' in st[t][s]['observation'] else st[t][0]['observation']
            f=o['farms'][s]
            q=len(f['unlocked_quadrants'])
            if q>prevq: land.append(o['day']); prevq=q
            peak=max(peak,len(f['hands']))
            a=st[t][s]['action'] or {}
            for u in [a.get('farmer')]+list(a.get('hands') or []):
                if not isinstance(u,list) or not u: continue
                if u[0]=='PLANT' and len(u)>1: plants[u[1]]+=1
                if u[0]=='PLACE' and len(u)>1 and u[1] in K.ANIMALS: anim_placed[u[1]]+=1
                if u[0]=='FEED': wheat_fed+=1
                if u[0]=='FERTILIZE': fert_used+=1
                if u[0]=='CARE': care+=1
            for m in (a.get('market') or []):
                if isinstance(m,list) and m and m[0]=='HIRE': hires[o['day']]+=1
            if o['hour']==23 or t==len(st)-1:
                cnt=collections.Counter()
                for row in f['tiles']:
                    for tile in row:
                        if isinstance(tile,dict):
                            if 'animal' in tile: cnt[tile['animal']]+=1
                            elif tile.get('kind')=='PLANT': cnt['P_'+tile['crop']]+=1
                            elif tile.get('kind') in ('COOP','PASTURE'): cnt['empty_'+tile['kind']]+=1
                            elif tile.get('kind')=='WEED': cnt['WEED']+=1
                anim_by_day[o['day']]=dict(cnt)
        rec.update(land_days=land,peak_hands=peak,hires_total=sum(hires.values()),plants_req=dict(plants),anim_placed=dict(anim_placed),feed_actions=wheat_fed,fert_actions=fert_used,care_actions=care,
                   tiles_d5=anim_by_day.get(5,{}),tiles_d10=anim_by_day.get(10,{}),tiles_d20=anim_by_day.get(20,{}),tiles_end=anim_by_day.get(29,{}))
        out.append(rec)
    return out
if __name__=='__main__':
    outp=sys.argv[1]
    with open(outp,'a') as f:
        for p in sys.argv[2:]:
            try:
                for rec in summarize(p): f.write(json.dumps(rec)+'\n')
            except Exception as e:
                f.write(json.dumps(dict(ep=os.path.basename(p),error=repr(e)))+'\n')
            f.flush()
