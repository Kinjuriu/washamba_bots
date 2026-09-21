import json, time, urllib.error
from fetch import episodes
lb=json.load(open("data/lb.json"))["publicLeaderboard"]
for r in lb[:40]:
    for attempt in range(4):
        try:
            d=episodes(r["submissionId"]); print(r["rank"],r["submissionId"],len(d.get("episodes",[])),flush=True); break
        except urllib.error.HTTPError as e:
            print(r["rank"],"HTTP",e.code,"sleep",flush=True); time.sleep(120*(attempt+1))
    time.sleep(12)
