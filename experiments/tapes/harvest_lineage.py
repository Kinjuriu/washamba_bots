"""Harvest the wool-route lineage: ListEpisodes for 5 submissions, download the
episodes they banked >= 95k in, extract their seat's tape, route key, and
agreement with our fam opening. Output yarn2/manifest.jsonl."""
import json, sys, os, time, urllib.request, base64, zlib, re
S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "C:/Users/HP/Spidey-Hub/washamba_bots/experiments"); sys.path.insert(0, S + "/harvest")
from ladder_episodes import fetch_episodes
from clade import canon, norm_action
SUBS = [55949244, 55959351, 55956879, 55958200, 55958920]
src = open("C:/Users/HP/Spidey-Hub/washamba_bots/agents/router_fam_keys.py", encoding="utf-8").read()
tapes = json.loads(zlib.decompress(base64.b85decode(re.search(r"_TAPES_DATA = '([^']*)'", src).group(1))).decode())
fam = [canon(a) for a in tapes["fam"]]
done = set()
mp = S + "/yarn2/manifest.jsonl"
if os.path.exists(mp):
    for l in open(mp): done.add(json.loads(l)["episode"])
todo = []
for sid in SUBS:
    try:
        eps = fetch_episodes(sid)
    except Exception as e:
        print("list fail", sid, e, flush=True); time.sleep(60); continue
    for e in eps:
        if e.get("state") != "COMPLETED": continue
        me = [a for a in e["agents"] if a.get("submissionId") == sid]
        if not me or (me[0].get("reward") or 0) < 95000: continue
        todo.append((e["id"], sid, me[0]["reward"], e["endTime"]))
    print("listed", sid, len(eps), "kept", sum(1 for t in todo if t[1] == sid), flush=True)
    time.sleep(30)
todo.sort(key=lambda t: -t[2])
print("todo", len(todo), flush=True)
n = 0
for eid, sid, rw, t in todo:
    if eid in done: continue
    if n >= 200: break
    p = f"{S}/yarn2/rep/{eid}.json"
    if not os.path.exists(p):
        try:
            req = urllib.request.Request(f"https://www.kaggleusercontent.com/episodes/{eid}.json", headers={"User-Agent": "washamba-harvest/1.0"})
            with urllib.request.urlopen(req, timeout=180) as h: open(p, "wb").write(h.read())
        except Exception as e:
            print("dl fail", eid, e, flush=True); continue
    rep = json.load(open(p))
    if isinstance(rep.get("replay"), str): rep = json.loads(rep["replay"])
    st = rep["steps"]
    seat = 0 if abs((st[-1][0].get("reward") or 0) - rw) < 2 else 1
    acts = [norm_action(st[i][seat].get("action")) for i in range(1, len(st))]
    c = [canon(a) for a in acts]
    ag = lambda lo, hi: sum(1 for i in range(lo, hi) if c[i] == fam[i]) / (hi - lo)
    shops = lambda i: (st[i][0].get("observation") or {}).get("town", {}).get("unlocked_shops") or []
    s72, s144 = shops(72), shops(144)[:2]
    key = "__".join(s144) if len(s144) == 2 else (s144[0] if s144 else "")
    json.dump(acts, open(f"{S}/yarn2/tapes/{eid}_{seat}.json", "w"))
    row = dict(episode=eid, seat=seat, sub=sid, reward=rw, opp_reward=st[-1][1 - seat].get("reward"), first=s72[0] if s72 else "", key=key, ag71=ag(0, 72), ag143=ag(72, 144), ag400=ag(144, 400), t=t)
    open(mp, "a").write(json.dumps(row) + "\n"); n += 1
    print(json.dumps(row), flush=True)
    os.remove(p)
print("HARVEST_DONE", n, flush=True)
