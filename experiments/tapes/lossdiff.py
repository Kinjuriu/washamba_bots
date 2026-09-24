"""Download recent episodes of 55916283, compare our seat vs opponent seat:
agreement by window, bank trajectory gap by day, and end-state (shed value)."""
import json, sys, os, urllib.request
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
from clade import canon
rows = json.load(open(S + "/yarn2_last40.json"))
os.makedirs(S + "/loss", exist_ok=True)
out = []
for r in rows[-24:]:
    eid = r["ep"]; p = f"{S}/loss/{eid}.json"
    if not os.path.exists(p):
        req = urllib.request.Request(f"https://www.kaggleusercontent.com/episodes/{eid}.json", headers={"User-Agent": "washamba-harvest/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=180) as h: open(p, "wb").write(h.read())
        except Exception as e:
            print(eid, "fail", e); continue
    rep = json.load(open(p))
    if isinstance(rep.get("replay"), str): rep = json.loads(rep["replay"])
    elif isinstance(rep.get("replay"), dict): rep = rep["replay"]
    steps = rep["steps"]
    # which seat is ours: match final reward
    rw = [steps[-1][s].get("reward") for s in (0, 1)]
    me = 0 if abs((rw[0] or 0) - r["my"]) < 2 else 1
    op = 1 - me
    acts = {s: [canon(steps[i][s].get("action") or {}) for i in range(1, len(steps))] for s in (0, 1)}
    def agree(a, b):
        return sum(1 for i in range(a, b) if acts[me][i] == acts[op][i]) / (b - a)
    win = {"0-71": agree(0, 72), "72-143": agree(72, 144), "144-399": agree(144, 400), "400-599": agree(400, 600), "600-718": agree(600, 719)}
    # bank by day (money from observation of seat 0, farms[player])
    gap = {}
    for d in (5, 10, 15, 20, 25, 28, 29):
        i = min(d * 24, len(steps) - 1)
        obs = steps[i][0].get("observation") or {}
        farms = obs.get("farms") or []
        if len(farms) == 2:
            gap[d] = (farms[me].get("money") or 0) - (farms[op].get("money") or 0)
    last = steps[-1]
    shed = {}
    for s in (0, 1):
        o = last[s].get("observation") or {}
        pr = (o.get("market") or {}).get("prices") or {}
        sh = (o.get("private") or {}).get("shed") or {}
        shed[s] = sum((sh.get(k, 0) or 0) * (pr.get(k, 0) or 0) for k in sh)
    # first divergence step
    first_div = next((i for i in range(len(acts[me])) if acts[me][i] != acts[op][i]), None)
    rec = dict(ep=eid, win=r["win"], my=r["my"], opp=r["opp"], oppsub=r["oppsub"], oppteam=r["oppteam"], seat=me, agree=win, first_div=first_div, gap_by_day=gap, my_shed=shed[me], opp_shed=shed[op],
               shops=(steps[144][0].get("observation") or {}).get("town", {}).get("unlocked_shops"))
    out.append(rec)
    print(json.dumps(rec))
json.dump(out, open(S + "/lossdiff.json", "w"), indent=1)
print("DONE", len(out))
