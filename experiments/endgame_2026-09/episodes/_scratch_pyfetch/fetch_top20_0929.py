"""Final scan, 29 Sep night, Part B step 6: for leaderboard ranks 1-20, download the
5 most recent completed episodes each into episodes/20260929_final/top20/, with a
manifest.csv. Read-only."""
import sys, os, csv, json, gzip, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_lib import client, list_submission_episodes, list_team_public_submissions, get_replay_bytes
from leaderboard_lookup import load_leaderboard
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT_ABS = os.path.join(ROOT, 'episodes/20260929_final')
TOP20_DIR = os.path.join(OUT_ABS, 'top20')
os.makedirs(TOP20_DIR, exist_ok=True)

lb_glob = [f for f in os.listdir(OUT_ABS) if f.startswith('kaggriculture-publicleaderboard') and f.endswith('.csv')]
lb_csv = os.path.join(OUT_ABS, lb_glob[0])

rows = list(csv.DictReader(open(lb_csv, encoding='utf-8-sig')))
top20 = sorted(rows, key=lambda r: int(r['Rank']))[:20]

c = client()
manifest_rows = []
team_meta = {}

for r in top20:
    rank = int(r['Rank'])
    team_id = int(r['TeamId'])
    team_name = r['TeamName']
    rating = float(r['Score'])
    print(f"rank {rank} {team_name} (team {team_id})...", flush=True)

    subs = list_team_public_submissions(c, team_id)
    for s in subs:
        try:
            s['public_score'] = float(s['public_score'])
        except (TypeError, ValueError):
            s['public_score'] = None
    subs_sorted = sorted(subs, key=lambda s: (s['public_score'] is None, -(s['public_score'] or 0)))

    picked = None
    picked_completed = []
    for s in subs_sorted:
        eps = list_submission_episodes(c, s['id'])
        completed = [e for e in eps if e['type'] != 'EPISODE_TYPE_VALIDATION' and e['state'] == 'COMPLETED']
        if completed:
            picked = s
            picked_completed = completed
            break
        time.sleep(0.1)

    if picked is None:
        team_meta[team_name] = dict(rank=rank, team_id=team_id, rating=rating, error='no completed episodes found')
        continue

    picked_completed.sort(key=lambda e: e['end_time'], reverse=True)
    top5 = picked_completed[:5]
    team_meta[team_name] = dict(rank=rank, team_id=team_id, rating=rating, submission_id=picked['id'],
                                 total_completed=len(picked_completed), sampled=len(top5))

    for e in top5:
        me = next((a for a in e['agents'] if a['submission_id'] == picked['id']), None)
        opp = next((a for a in e['agents'] if a['submission_id'] != picked['id']), None)
        if me is None:
            continue
        won = None
        if opp and me['reward'] is not None and opp['reward'] is not None:
            won = 1 if me['reward'] > opp['reward'] else (0.5 if me['reward'] == opp['reward'] else 0)
        opp_rating = None
        opp_row = next((x for x in rows if int(x['TeamId']) == opp['team_id']), None) if opp else None
        if opp_row:
            opp_rating = float(opp_row['Score'])
        manifest_rows.append(dict(
            team=team_name, rank=rank, rating=rating, episode_id=e['episode_id'],
            seat=me['index'], won=won, opp_team=opp['team_name'] if opp else None,
            opp_rating=opp_rating,
        ))

cols = ['team', 'rank', 'rating', 'episode_id', 'seat', 'won', 'opp_team', 'opp_rating']
with open(os.path.join(TOP20_DIR, 'manifest.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for row in manifest_rows:
        w.writerow(row)
print(f"Wrote manifest.csv ({len(manifest_rows)} rows)")

json.dump(team_meta, open(os.path.join(TOP20_DIR, 'team_meta.json'), 'w'), indent=2)

# ---- download replays ----
distinct_eids = sorted({r['episode_id'] for r in manifest_rows})
print(f"distinct episodes to download: {len(distinct_eids)}")

download_results = {}
def ensure_replay(eid):
    dest = os.path.join(TOP20_DIR, f'{eid}.json.gz')
    if os.path.exists(dest):
        return eid, 'already_in_out'
    try:
        b = get_replay_bytes(c, eid)
        gz = gzip.compress(b, compresslevel=6)
        with open(dest, 'wb') as f:
            f.write(gz)
        return eid, f'downloaded_{len(gz)}b'
    except Exception as ex:
        return eid, f'error:{ex}'

t0 = time.time()
with ThreadPoolExecutor(max_workers=2) as pool:
    futs = {pool.submit(ensure_replay, eid): eid for eid in distinct_eids}
    done_n = 0
    for fut in as_completed(futs):
        eid, res = fut.result()
        download_results[eid] = res
        done_n += 1
        if done_n % 25 == 0:
            print(f"  replays: {done_n}/{len(distinct_eids)} ({time.time()-t0:.0f}s)")
print(f"Replay download phase done in {time.time()-t0:.0f}s")
json.dump(download_results, open(os.path.join(TOP20_DIR, 'download_results.json'), 'w'), indent=2)
print("DONE fetch_top20_0929.py")
