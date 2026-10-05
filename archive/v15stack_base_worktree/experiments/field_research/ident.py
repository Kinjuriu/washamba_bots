import json, sys, glob
from kaggle_environments import make
rp=sys.argv[1]; seat=int(sys.argv[2])
d=json.load(open(rp)); seed=d["info"]["seed"]
ref=[s[seat]["action"] for s in d["steps"]]
def agree(a,b,lo,hi):
    n=sum(1 for i in range(lo,hi) if json.dumps(a[i],sort_keys=True)==json.dumps(b[i],sort_keys=True)); return n/(hi-lo)
for ag in sorted(glob.glob("agents/router_*.py"))+["agents/route_moon_md_floor_deficit.py"]:
    env=make("kaggriculture",configuration={"episodeSteps":720,"seed":seed})
    env.run([ag,ag] )
    mine=[s[seat]["action"] for s in env.steps]
    print(f"{ag:45s} 0-72 {agree(ref,mine,1,72):.2f} 72-144 {agree(ref,mine,72,144):.2f} 144-400 {agree(ref,mine,144,400):.2f} 400-719 {agree(ref,mine,400,719):.2f}",flush=True)
