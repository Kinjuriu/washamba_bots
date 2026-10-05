import sys, os, json, gzip, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_lib import client, get_replay_bytes

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]

c = client()
res_path = os.path.join(ROOT, OUT, 'download_results.json')
res = json.load(open(res_path))
todo = [eid for eid, v in res.items() if not v.startswith('downloaded') and not v.startswith('copied') and not v.startswith('already')]
print(f"slow-retrying {len(todo)} replay downloads", flush=True)

# initial cooldown to let any rate-limit window reset
time.sleep(30)

consecutive_429 = 0
for i, eid in enumerate(todo):
    dest = os.path.join(ROOT, OUT, 'replays', f'{eid}.json.gz')
    if os.path.exists(dest):
        res[eid] = 'already_in_out'
        continue
    ok = False
    for attempt in range(4):
        try:
            b = get_replay_bytes(c, int(eid))
            gz = gzip.compress(b, compresslevel=6)
            with open(dest, 'wb') as f:
                f.write(gz)
            res[eid] = f'downloaded_{len(gz)}b'
            ok = True
            consecutive_429 = 0
            break
        except Exception as ex:
            res[eid] = f'error:{ex}'
            if '429' in str(ex):
                consecutive_429 += 1
                wait = min(60, 5 * consecutive_429)
                time.sleep(wait)
            else:
                time.sleep(2)
    if i % 5 == 0:
        print(f"  {i}/{len(todo)} consecutive_429={consecutive_429}", flush=True)
        json.dump(res, open(res_path, 'w'), indent=2)
    time.sleep(1.5)  # gentle steady pace

json.dump(res, open(res_path, 'w'), indent=2)
print("SLOW_RETRY_DONE", flush=True)
