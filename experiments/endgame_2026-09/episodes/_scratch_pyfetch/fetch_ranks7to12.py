import sys, os, json, csv, gzip, glob, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_lib import client, list_submission_episodes, get_replay_bytes
from leaderboard_lookup import load_leaderboard, band
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]
os.makedirs(os.path.join(ROOT, OUT, 'replays'), exist_ok=True)

# Resolved 2026-09-24 ~16:13 UTC from the full leaderboard CSV download, cross-checked against
# ListTeamPublicSubmissions (matching each candidate submission's public_score to the leaderboard score).
TARGETS = [
    dict(rank=7,  name='Kaggledew Valley', team_id=16633132, submission_id=56478393, lb_score=2964.1),
    dict(rank=8,  name='Azat Akhtyamov',   team_id=16743356, submission_id=56491144, lb_score=2943.5),
    dict(rank=9,  name='THIRD FARM CLUB',  team_id=16730524, submission_id=56520754, lb_score=2933.5),
    dict(rank=10, name='Arda Ceylan',      team_id=16673205, submission_id=56508756, lb_score=2930.9),
    dict(rank=11, name='mtmr_s1',          team_id=16758882, submission_id=56488920, lb_score=2926.7),
    dict(rank=12, name='TheEggman',        team_id=16887437, submission_id=56498825, lb_score=2914.4),
]

lb = load_leaderboard(os.path.join(ROOT, 'episodes/_scratch_pyfetch/kaggriculture-publicleaderboard-2026-09-24T16:13:50.csv'))

existing_replay_dirs = [
    os.path.join(ROOT, 'episodes/20260923T153431Z_top6/replays'),
    os.path.join(ROOT, 'episodes/20260923T161855Z_washamba_vs_top6/replays'),
    os.path.join(ROOT, 'episodes/20260924T161358Z_washamba_0924b/replays'),
]

def find_existing_replay(eid):
    for d in existing_replay_dirs:
        p = os.path.join(d, f'{eid}.json.gz')
        if os.path.exists(p):
            return p
    return None

c = client()

all_rows = []
per_team_meta = {}
for t in TARGETS:
    sid = t['submission_id']
    eps = list_submission_episodes(c, sid)
    non_val_completed = [e for e in eps if e['type'] != 'EPISODE_TYPE_VALIDATION' and e['state'] == 'COMPLETED']
    non_val_completed.sort(key=lambda e: e['end_time'], reverse=True)
    sample = non_val_completed[:60]
    per_team_meta[t['name']] = dict(sid=sid, total_api=len(eps), non_val_completed=len(non_val_completed),
                                     sampled=len(sample),
                                     newest=non_val_completed[0]['end_time'] if non_val_completed else None,
                                     oldest=sample[-1]['end_time'] if sample else None)
    for e in sample:
        me = next((a for a in e['agents'] if a['submission_id'] == sid), None)
        opp = next((a for a in e['agents'] if a['submission_id'] != sid), None)
        if me is None:
            continue
        row = dict(
            team_rank=t['rank'], team_name=t['name'], team_id=t['team_id'],
            player_submission=sid, episode_id=e['episode_id'],
            end_time=e['end_time'], state=e['state'], type=e['type'],
            player_seat=me['index'], player_bank=me['reward'],
            opponent_name=opp['team_name'] if opp else None,
            opponent_team=opp['team_id'] if opp else None,
            opponent_submission=opp['submission_id'] if opp else None,
            opponent_seat=opp['index'] if opp else None,
            opponent_bank=opp['reward'] if opp else None,
            won=(1 if (opp and me['reward'] is not None and opp['reward'] is not None and me['reward'] > opp['reward'])
                 else (0.5 if (opp and me['reward'] == opp['reward']) else 0)),
        )
        oppinfo = lb.get(row['opponent_team']) if row['opponent_team'] else None
        row['opponent_rating_snapshot'] = oppinfo['score'] if oppinfo else None
        row['opponent_band'] = band(oppinfo['score'] if oppinfo else None)
        all_rows.append(row)

print(json.dumps(per_team_meta, indent=2))
json.dump(per_team_meta, open(os.path.join(ROOT, OUT, 'team_episode_counts.json'), 'w'), indent=2)
json.dump(dict(targets=TARGETS, retrieved_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
               source='kaggle competitions leaderboard kaggriculture -d (full CSV download), cross-checked '
                      'against ListTeamPublicSubmissions public_score match'),
          open(os.path.join(ROOT, OUT, 'leaderboard_snapshot.json'), 'w'), indent=2)

manifest_path = os.path.join(ROOT, OUT, 'manifest.csv')
cols = ['team_rank','team_name','team_id','player_submission','episode_id','end_time','state','type',
        'player_seat','player_bank','opponent_name','opponent_team','opponent_submission','opponent_seat',
        'opponent_bank','won','opponent_rating_snapshot','opponent_band']
with open(manifest_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for row in all_rows:
        w.writerow(row)
print(f"Wrote frozen manifest: {manifest_path} ({len(all_rows)} rows)")

distinct_eids = sorted({r['episode_id'] for r in all_rows})
print(f"distinct episodes to ensure on disk: {len(distinct_eids)}")

download_results = {}
def ensure_replay(eid):
    dest = os.path.join(ROOT, OUT, 'replays', f'{eid}.json.gz')
    if os.path.exists(dest):
        return eid, 'already_in_out'
    src = find_existing_replay(eid)
    if src:
        import shutil
        shutil.copy2(src, dest)
        return eid, 'copied_from_cache'
    try:
        b = get_replay_bytes(c, eid)
        gz = gzip.compress(b, compresslevel=6)
        with open(dest, 'wb') as f:
            f.write(gz)
        return eid, f'downloaded_{len(gz)}b'
    except Exception as ex:
        return eid, f'error:{ex}'

t0 = time.time()
with ThreadPoolExecutor(max_workers=4) as pool:
    futs = {pool.submit(ensure_replay, eid): eid for eid in distinct_eids}
    done_n = 0
    for fut in as_completed(futs):
        eid, res = fut.result()
        download_results[eid] = res
        done_n += 1
        if done_n % 25 == 0:
            print(f"  replays: {done_n}/{len(distinct_eids)} ({time.time()-t0:.0f}s)")
            json.dump(download_results, open(os.path.join(ROOT, OUT, 'download_results.json'), 'w'), indent=2)
print(f"Replay download phase done in {time.time()-t0:.0f}s")
json.dump(download_results, open(os.path.join(ROOT, OUT, 'download_results.json'), 'w'), indent=2)
print("DONE fetch_ranks7to12.py")
