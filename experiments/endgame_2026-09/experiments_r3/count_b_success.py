"""Count engine-successful actions in one W0-vs-W0 vs one B-vs-W0 game (seed 101, seat 0)."""
import os, sys, json, collections
from kaggle_environments import make
def run(pa):
    env = make('kaggriculture', configuration={'seed': 101}, debug=False)
    env.run([os.path.abspath(pa), os.path.abspath('../submissions/w0_v15stack_control.py')])
    steps = env.steps
    tot = collections.Counter()
    for t in range(1, len(steps)):
        farm = steps[t-1][0].observation.farms[0]
        a = steps[t][0].action
        units = [a.get('farmer')] + (a.get('hands') or [])
        poss = [farm['farmer']] + farm['hands']
        cared = set(); done = set()
        for i, u in enumerate(units):
            if not (isinstance(u, list) and u) or i >= len(poss): continue
            op = u[0]; x, y = poss[i]; tile = farm['tiles'][y][x]
            isani = isinstance(tile, dict) and 'animal' in tile
            if op == 'CARE':
                tot['care_issued'] += 1
                if isani and not tile.get('cared_today') and (x,y) not in cared:
                    cared.add((x,y)); tot['care_success'] += 1
            elif op == 'COLLECT_FERTILIZER':
                tot['collect_issued'] += 1
                if isani and tile.get('fertilizer_available') and (x,y,'f') not in done:
                    done.add((x,y,'f')); tot['collect_success'] += 1
            elif op == 'HARVEST':
                tot['harvest_issued'] += 1
                if isinstance(tile, dict) and tile.get('yield_units',0) > 0 and (x,y,'h') not in done:
                    done.add((x,y,'h')); tot['harvest_success'] += 1
    return tot, [steps[-1][i].reward for i in (0,1)]
base, rb = run('../submissions/w0_v15stack_control.py')
bvar, rv = run('B/main.py')
print('w0 :', dict(base), rb)
print('B  :', dict(bvar), rv)
for k in ('care_success','collect_success','harvest_success'):
    print(k, 'delta', bvar[k]-base[k])
