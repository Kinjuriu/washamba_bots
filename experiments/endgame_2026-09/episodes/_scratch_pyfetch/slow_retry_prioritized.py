import sys, os, json, gzip, time, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_lib import client, get_replay_bytes

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]
PRIORITY_TEAM = sys.argv[2] if len(sys.argv) > 2 else None

c = client()
res_path = os.path.join(ROOT, OUT, 'download_results.json')
res = json.load(open(res_path))
todo = [eid for eid, v in res.items() if not v.startswith('downloaded') and not v.startswith('copied') and not v.startswith('already')]

# reorder: priority team's episodes first
if PRIORITY_TEAM:
    eid_team = {}
    with open(os.path.join(ROOT, OUT, 'manifest.csv')) as f:
        for row in csv.DictReader(f):
            eid_team[row['episode_id']] = row['team_name']
    todo.sort(key=lambda eid: 0 if eid_team.get(eid) == PRIORITY_TEAM else 1)

print(f"retrying {len(todo)} (priority={PRIORITY_TEAM})", flush=True)
consecutive_429 = 0
for i, eid in enumerate(todo):
    dest = os.path.join(ROOT, OUT, 'replays', f'{eid}.json.gz')
    if os.path.exists(dest):
        res[eid] = 'already_in_out'
        continue
    for attempt in range(4):
        try:
            b = get_replay_bytes(c, int(eid))
            gz = gzip.compress(b, compresslevel=6)
            with open(dest, 'wb') as f:
                f.write(gz)
            res[eid] = f'downloaded_{len(gz)}b'
            consecutive_429 = 0
            break
        except Exception as ex:
            res[eid] = f'error:{ex}'
            if '429' in str(ex):
                consecutive_429 += 1
                time.sleep(min(45, 4 * consecutive_429))
            else:
                time.sleep(2)
    if i % 5 == 0:
        print(f"  {i}/{len(todo)} consecutive_429={consecutive_429}", flush=True)
        json.dump(res, open(res_path, 'w'), indent=2)
    time.sleep(1.2)

json.dump(res, open(res_path, 'w'), indent=2)
print("PRIORITIZED_RETRY_DONE", flush=True)
