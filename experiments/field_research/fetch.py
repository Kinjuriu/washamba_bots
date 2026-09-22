import json, os, sys, time, urllib.request
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),"data","eps"); os.makedirs(D,exist_ok=True)
URL="https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
def episodes(sub, refresh=False):
    p=os.path.join(D,f"{sub}.json")
    if os.path.exists(p) and not refresh: return json.load(open(p))
    req=urllib.request.Request(URL,data=json.dumps({"submissionId":int(sub)}).encode(),headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=90) as r: d=json.load(r)
    json.dump(d,open(p,"w")); time.sleep(4); return d
if __name__=="__main__":
    for s in sys.argv[1:]:
        d=episodes(s); print(s,len(d.get("episodes",[])),list(d.keys()))
