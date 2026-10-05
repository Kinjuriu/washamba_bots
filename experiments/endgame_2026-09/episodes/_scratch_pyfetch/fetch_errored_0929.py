"""Follow-up: pull agent logs (and replay, if any) for the two ERRORED episodes found
on tetsu_step1009_full.py (56645467) in the 2026-09-29 final scan. Read-only."""
import sys, os, json, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_lib import client, list_submission_episodes, get_replay_bytes, get_agent_logs_bytes

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = os.path.join(ROOT, 'episodes/20260929_final/error_episodes')
os.makedirs(OUT, exist_ok=True)

SID = 56645467
TARGET_EIDS = {115091156, 115114335}

c = client()
eps = list_submission_episodes(c, SID)
targets = [e for e in eps if e['episode_id'] in TARGET_EIDS]
print(f"found {len(targets)}/{len(TARGET_EIDS)} target episodes in API listing")

for e in targets:
    eid = e['episode_id']
    print(f"\n=== episode {eid} state={e['state']} end_time={e['end_time']} ===")
    print(json.dumps(e, indent=2, default=str))

    me = next((a for a in e['agents'] if a['submission_id'] == SID), None)
    our_idx = me['index'] if me else None
    print(f"our agent index: {our_idx}")

    # try replay
    try:
        b = get_replay_bytes(c, eid)
        dest = os.path.join(OUT, f'{eid}.json.gz')
        with open(dest, 'wb') as f:
            f.write(gzip.compress(b, compresslevel=6))
        print(f"replay: downloaded {len(b)}b -> {dest}")
    except Exception as ex:
        print(f"replay: error: {ex}")

    # try our own agent logs only (opponent logs expect 403, don't bother)
    if our_idx is not None:
        try:
            b = get_agent_logs_bytes(c, eid, our_idx)
            dest = os.path.join(OUT, f'episode-{eid}-agent-{our_idx}-logs.json')
            with open(dest, 'wb') as f:
                f.write(b)
            print(f"our logs: downloaded {len(b)}b -> {dest}")
        except Exception as ex:
            print(f"our logs: error: {ex}")

print("\nDONE fetch_errored_0929.py")
