import gzip, json, sys, os
from kaggle_environments import make
def tape_agent(path, seat):
    d=json.load(gzip.open(path)); acts=[d['steps'][t][seat]['action'] for t in range(len(d['steps']))]
    def a(obs,cfg):
        t=obs['step']+1
        return acts[t] if t<len(acts) else {'farmer':['PASS'],'hands':[],'market':[]}
    return a, d
def play(replay, seat, ours):
    ag,d=tape_agent(replay, seat)
    agents=[None,None]; agents[seat]=ag; agents[1-seat]=os.path.abspath(ours)
    env=make('kaggriculture',configuration={'seed':d['info']['seed']},debug=False); env.run(agents)
    r=[env.steps[-1][i].reward for i in (0,1)]
    return dict(tape=d['info']['TeamNames'][seat], orig_tape_bank=d['rewards'][seat], orig_opp_bank=d['rewards'][1-seat], tape_bank=r[seat], ours_bank=r[1-seat])
if __name__=='__main__':
    print(json.dumps(play(sys.argv[1], int(sys.argv[2]), sys.argv[3])))
