import sys, os, json, collections, time
import kaggle_environments.envs.kaggriculture.kaggriculture as K
from kaggle_environments import make
LOG=[]; CUR={'farms':None,'step':0}
_pm=K._process_market; _cu=K._commit_unit
def pm(state, env):
    CUR['farms']=[id(f) for f in state[0].observation.farms]; CUR['step']=state[0].observation.step; return _pm(state, env)
def cu(op,item,price,farm,private,market,shed_capacity=100):
    ok=_cu(op,item,price,farm,private,market,shed_capacity)
    if ok and op in ('SELL','BUY_PRODUCT'): LOG.append((CUR['step'], CUR['farms'].index(id(farm)), op, item, price))
    return ok
K._process_market=pm; K._commit_unit=cu
a,b,seed=os.path.abspath(sys.argv[1]),os.path.abspath(sys.argv[2]),int(sys.argv[3])
t0=time.time()
env=make('kaggriculture',configuration={'seed':seed},debug=False); env.run([a,b])
wall=time.time()-t0
print('banks',[env.steps[-1][i].reward for i in (0,1)],'wall_s',round(wall,1),'per-agent-turn_ms',round(1000*wall/1440,1))
agg=collections.defaultdict(lambda:[0,0])
for t,p,op,item,price in LOG:
    key=(p,op,item); agg[key][0]+=1; agg[key][1]+=price
for item in ['WOOL','STRAWBERRY','MILK','EGG','MELON','TOMATO','CARROT','WHEAT','FERTILIZER']:
    row=[]
    for p in (0,1):
        s=agg[(p,'SELL',item)]; bq=agg[(p,'BUY_PRODUCT',item)]
        row.append(f"s{p}: {s[0]:3d}u@{s[1]/max(1,s[0]):5.1f} buy {bq[0]:3d}u")
    print(f"{item:10s} "+" | ".join(row))
