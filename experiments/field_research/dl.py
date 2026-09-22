import json, os, sys, subprocess, time
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),"data","replays")
def get(ep):
    p=f"{D}/{ep}.json"
    if os.path.exists(p) and os.path.getsize(p)>100000: return p
    subprocess.run(["curl","-sL","-m","300","--compressed","-o",p,f"https://www.kaggleusercontent.com/episodes/{ep}.json"]); time.sleep(1); return p
if __name__=="__main__":
    for e in sys.argv[1:]: get(e); print(e,flush=True)
