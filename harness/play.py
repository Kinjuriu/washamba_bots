import sys, json, time, os
sys.path.insert(0, os.path.abspath('agents/fieldcraft'))
from kaggle_environments import make
from kaggle_environments.agent import get_last_callable
A = {'v15stack':'agents/v15stack/main.py','v57':'agents/v57/main.py','k0013':'agents/k0013/main.py','fieldcraft':'agents/fieldcraft/main.py'}
def load(name):
    if name in ('starter','pass','random'): return name
    return os.path.abspath(A[name])
a, b, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
env = make('kaggriculture', configuration={'seed': seed}, debug=False)
t = time.time()
env.run([load(a), load(b)])
r = [s.reward for s in env.steps[-1]]; st = [s.status for s in env.steps[-1]]
print(json.dumps(dict(a=a, b=b, seed=seed, ra=r[0], rb=r[1], sa=st[0], sb=st[1], secs=round(time.time()-t,1))))
