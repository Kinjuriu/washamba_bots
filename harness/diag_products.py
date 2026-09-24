import sys, os, json, collections
import kaggle_environments.envs.kaggriculture.kaggriculture as K
from kaggle_environments import make
LOG=[]; CUR={'farms':None,'step':0}
_pm=K._process_market; _cu=K._commit_unit; _eod=K._end_of_day
def pm(state, env):
    CUR['farms']=[id(f) for f in state[0].observation.farms]; CUR['step']=state[0].observation.step; return _pm(state, env)
def cu(op,item,price,farm,private,market,shed_capacity=100):
    ok=_cu(op,item,price,farm,private,market,shed_capacity)
    if ok and op=='SELL': LOG.append((CUR['step'], CUR['farms'].index(id(farm)), item, price))
    return ok
K._process_market=pm; K._commit_unit=cu
def agentpath(n):
    p='variants/%s/main.py'%n if os.path.exists('variants/%s/main.py'%n) else 'agents/%s/main.py'%n
    return os.path.abspath(p)
a,b,seed=sys.argv[1],sys.argv[2],int(sys.argv[3])
env=make('kaggriculture',configuration={'seed':seed},debug=False); env.run([agentpath(a),agentpath(b)])
print('banks',[env.steps[-1][i].reward for i in (0,1)])
agg=collections.defaultdict(lambda:[0,0]); late=collections.defaultdict(int)
for t,p,item,price in LOG:
    agg[(p,item)][0]+=1; agg[(p,item)][1]+=price
for item in ['WOOL','STRAWBERRY','MILK','EGG','MELON','TOMATO','CARROT','WHEAT','FERTILIZER']:
    x=agg[(0,item)]; y=agg[(1,item)]
    print(f"{item:10s} {a}: {x[0]:4d}u ${x[1]:6d} @{x[1]/max(1,x[0]):6.1f} | {b}: {y[0]:4d}u ${y[1]:6d} @{y[1]/max(1,y[0]):6.1f}")
