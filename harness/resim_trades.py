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
for path in sys.argv[1:]:
    ep=os.path.basename(path).split('.')[0]
    d=json.load(gzip.open(path)); st=d['steps']
    acts=[[st[t][s]['action'] for t in range(len(st))] for s in (0,1)]
    def mk(s):
        def a(obs,cfg):
            CUR['step']=obs['step']+1
            return acts[s][obs['step']+1] if obs['step']+1<len(acts[s]) else {'farmer':['PASS'],'hands':[],'market':[]}
        return a
    LOG.clear(); env=make('kaggriculture',configuration={'seed':d['info']['seed']},debug=False); env.run([mk(0),mk(1)])
    ok=[env.steps[-1][0].reward, env.steps[-1][1].reward]==d['rewards']
    for s in (0,1):
        rec=dict(ep=ep,seat=s,name=d['info']['TeamNames'][s],opp=d['info']['TeamNames'][1-s],bank=d['rewards'][s],opp_bank=d['rewards'][1-s],exact=ok)
        items=collections.defaultdict(lambda:[0,0,0,0]); phase=collections.Counter(); spend=collections.Counter()
        for (t,p,op,item,price) in LOG:
            if p!=s: continue
            if op=='SELL': items[item][0]+=1; items[item][1]+=price; phase['sell_d%02d'%(10*(t//240))]+=price
            elif op=='BUY_PRODUCT': items[item][2]+=1; items[item][3]+=price
            else: spend[op+'_'+item]+=price
        rec['items']=dict(items); rec['phase']=dict(phase); rec['spend']=dict(spend)
        print(json.dumps(rec), flush=True)
