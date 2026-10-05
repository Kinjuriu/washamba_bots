import sys, os, json, gzip, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_lib import client, get_replay_bytes, get_agent_logs_bytes

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]
KIND = sys.argv[2]  # 'replays' or 'logs'

c = client()

if KIND == 'replays':
    res_path = os.path.join(ROOT, OUT, 'download_results.json')
    res = json.load(open(res_path))
    todo = [eid for eid, v in res.items() if not v.startswith('downloaded') and not v.startswith('copied') and not v.startswith('already')]
    print(f"retrying {len(todo)} replay downloads")
    for i, eid in enumerate(todo):
        dest = os.path.join(ROOT, OUT, 'replays', f'{eid}.json.gz')
        if os.path.exists(dest):
            res[eid] = 'already_in_out'
            continue
        backoff = 3.0
        for attempt in range(6):
            try:
                b = get_replay_bytes(c, int(eid))
                gz = gzip.compress(b, compresslevel=6)
                with open(dest, 'wb') as f:
                    f.write(gz)
                res[eid] = f'downloaded_{len(gz)}b'
                break
            except Exception as ex:
                res[eid] = f'error:{ex}'
                if '429' in str(ex) or '503' in str(ex):
                    time.sleep(backoff + random.uniform(0, 1))
                    backoff *= 1.7
                else:
                    time.sleep(1.0)
        if i % 10 == 0:
            print(f"  {i}/{len(todo)}")
            json.dump(res, open(res_path, 'w'), indent=2)
        time.sleep(0.4)  # gentle pacing between requests
    json.dump(res, open(res_path, 'w'), indent=2)
    print("done replays retry")

elif KIND == 'logs':
    res_path = os.path.join(ROOT, OUT, 'log_download_results.json')
    res = json.load(open(res_path))
    # need seat info from manifest to know agent_index per episode
    import csv
    seat_by_eid = {}
    with open(os.path.join(ROOT, OUT, 'manifest.csv')) as f:
        for row in csv.DictReader(f):
            seat_by_eid[row['episode_id']] = int(row['player_seat'])
    todo = [eid for eid, v in res.items() if not v.startswith('downloaded') and not v.startswith('copied') and not v.startswith('already')]
    print(f"retrying {len(todo)} log downloads")
    for i, eid in enumerate(todo):
        seat = seat_by_eid.get(eid)
        if seat is None:
            continue
        dest = os.path.join(ROOT, OUT, 'logs', f'episode-{eid}-agent-{seat}-logs.json')
        if os.path.exists(dest):
            res[eid] = 'already_in_out'
            continue
        backoff = 3.0
        for attempt in range(6):
            try:
                b = get_agent_logs_bytes(c, int(eid), seat)
                with open(dest, 'wb') as f:
                    f.write(b)
                res[eid] = f'downloaded_{len(b)}b'
                break
            except Exception as ex:
                res[eid] = f'error:{ex}'
                if '429' in str(ex) or '503' in str(ex):
                    time.sleep(backoff + random.uniform(0, 1))
                    backoff *= 1.7
                else:
                    time.sleep(1.0)
        if i % 20 == 0:
            print(f"  {i}/{len(todo)}")
            json.dump(res, open(res_path, 'w'), indent=2)
        time.sleep(0.3)
    json.dump(res, open(res_path, 'w'), indent=2)
    print("done logs retry")
