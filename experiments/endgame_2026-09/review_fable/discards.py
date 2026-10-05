"""Exact count of units discarded at the midnight shed drop (shed cap 100), per seat. Usage: discards.py out.jsonl files..."""
import gzip,json,sys,os,collections
import kaggle_environments.envs.kaggriculture.kaggriculture as K
from kaggle_environments import make
LOG=collections.Counter(); PRICE={}
_drop=K._drop_inventories_to_shed; CUR={'privs':None,'prices':None}
def drop(private,capacity):
    before=sum(private['shed'].values())+sum(sum(i.values()) for i in private['inventories'])
    items=collections.Counter()
    for inv in private['inventories']:
        for k,v in inv.items(): items[k]+=v
    _drop(private,capacity)
    after=sum(private['shed'].values())
    lost=before-after
    if lost>0:
        seat=CUR['privs'].index(id(private)); LOG[(seat,'units')]+=lost
        # value lost approx at current prices, attribute proportionally to inventory items
        tot=sum(items.values()) or 1
        for k,v in items.items():
            LOG[(seat,'value')]+=lost*v/tot*CUR['prices'].get(k,0)
K._drop_inventories_to_shed=drop
_eod=K._end_of_day
def eod(state,env,day):
    CUR['privs']=[id(s.observation.private) for s in state]; CUR['prices']=dict(state[0].observation.market['prices']); return _eod(state,env,day)
K._end_of_day=eod
with open(sys.argv[1],'a') as f:
    for path in sys.argv[2:]:
        d=json.load(gzip.open(path)); st=d['steps']
        acts=[[st[t][s]['action'] for t in range(len(st))] for s in (0,1)]
        def mk(s):
            def a(obs,cfg): return acts[s][obs['step']+1] if obs['step']+1<len(acts[s]) else {'farmer':['PASS'],'hands':[],'market':[]}
            return a
        LOG.clear(); env=make('kaggriculture',configuration={'seed':d['info']['seed']},debug=False); env.run([mk(0),mk(1)])
        ok=[env.steps[-1][0].reward,env.steps[-1][1].reward]==d['rewards']
        for s in (0,1):
            f.write(json.dumps(dict(ep=os.path.basename(path).split('.')[0],seat=s,name=d['info']['TeamNames'][s],exact=ok,lost_units=LOG[(s,'units')],lost_value=round(LOG[(s,'value')])))+'\n')
        f.flush()
