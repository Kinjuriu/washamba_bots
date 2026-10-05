import sys, os, json, csv, gzip, glob, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_lib import client, list_submission_episodes, get_replay_bytes, get_agent_logs_bytes
from leaderboard_lookup import load_leaderboard, band
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]  # output dir, e.g. episodes/20260924T161358Z_washamba_0924b
os.makedirs(os.path.join(ROOT, OUT, 'replays'), exist_ok=True)
os.makedirs(os.path.join(ROOT, OUT, 'logs'), exist_ok=True)

SUBS = {
    'w1_v15stack_race44.py (W1 re-upload)': dict(sid=56521297, label='W1_reupload'),
    'w3_herdsafe2700.py (W3, main.py)': dict(sid=56518334, label='W3'),
    'w0_v15stack_control.py (W0, retired)': dict(sid=56487592, label='W0_retired'),
    'w1_v15stack_race44.py (W1, first upload)': dict(sid=56491123, label='W1_first'),
}

lb = load_leaderboard(os.path.join(ROOT, 'episodes/_scratch_pyfetch/kaggriculture-publicleaderboard-2026-09-24T16:13:50.csv'))

# existing replay/log caches to avoid re-downloading
existing_replay_dirs = [
    os.path.join(ROOT, 'episodes/20260923T153431Z_top6/replays'),
    os.path.join(ROOT, 'episodes/20260923T161855Z_washamba_vs_top6/replays'),
]
existing_log_dirs = [
    os.path.join(ROOT, 'episodes/20260923T161855Z_washamba_vs_top6/logs'),
]

def find_existing_replay(eid):
    for d in existing_replay_dirs:
        p = os.path.join(d, f'{eid}.json.gz')
        if os.path.exists(p):
            return p
    return None

def find_existing_log(eid):
    # filenames like episode-<id>-agent-<n>-logs.json ; return dict {agent_index: path}
    out = {}
    for d in existing_log_dirs:
        for p in glob.glob(os.path.join(d, f'episode-{eid}-agent-*-logs.json')):
            idx = int(p.split('-agent-')[1].split('-logs')[0])
            out[idx] = p
    return out

c = client()

all_rows = []
per_sub_meta = {}
for display, meta in SUBS.items():
    sid = meta['sid']
    eps = list_submission_episodes(c, sid)
    non_val_completed = [e for e in eps if e['type'] != 'EPISODE_TYPE_VALIDATION' and e['state'] == 'COMPLETED']
    per_sub_meta[display] = dict(sid=sid, total_api=len(eps), non_val_completed=len(non_val_completed))
    for e in non_val_completed:
        # find our agent + opponent agent
        me = next((a for a in e['agents'] if a['submission_id'] == sid), None)
        opp = next((a for a in e['agents'] if a['submission_id'] != sid), None)
        if me is None:
            continue
        row = dict(
            display=display, player_submission=sid, episode_id=e['episode_id'],
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
        row['opponent_rank_snapshot'] = oppinfo['rank'] if oppinfo else None
        row['opponent_band'] = band(oppinfo['score'] if oppinfo else None)
        all_rows.append(row)

print("=== per-submission episode counts ===")
print(json.dumps(per_sub_meta, indent=2))

# freeze manifest BEFORE downloading
manifest_path = os.path.join(ROOT, OUT, 'manifest.csv')
cols = ['display','player_submission','episode_id','end_time','state','type','player_seat','player_bank',
        'opponent_name','opponent_team','opponent_submission','opponent_seat','opponent_bank','won',
        'opponent_rating_snapshot','opponent_rank_snapshot','opponent_band']
with open(manifest_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for row in all_rows:
        w.writerow(row)
print(f"Wrote frozen manifest: {manifest_path} ({len(all_rows)} rows)")

json.dump(per_sub_meta, open(os.path.join(ROOT, OUT, 'sub_episode_counts.json'), 'w'), indent=2)

# ---- download phase ----
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
with ThreadPoolExecutor(max_workers=6) as pool:
    futs = {pool.submit(ensure_replay, eid): eid for eid in distinct_eids}
    done_n = 0
    for fut in as_completed(futs):
        eid, res = fut.result()
        download_results[eid] = res
        done_n += 1
        if done_n % 25 == 0:
            print(f"  replays: {done_n}/{len(distinct_eids)} ({time.time()-t0:.0f}s)")
print(f"Replay download phase done in {time.time()-t0:.0f}s")
json.dump(download_results, open(os.path.join(ROOT, OUT, 'download_results.json'), 'w'), indent=2)

# ---- our own logs (skip opponent logs; 403 expected there, don't retry) ----
# only fetch logs for our own submission's agent index, per episode, and only for the 4 our-submissions rows
log_results = {}
def ensure_log(eid, agent_idx, sid_label):
    dest = os.path.join(ROOT, OUT, 'logs', f'episode-{eid}-agent-{agent_idx}-logs.json')
    if os.path.exists(dest):
        return eid, 'already_in_out'
    existing = find_existing_log(eid)
    if agent_idx in existing:
        import shutil
        shutil.copy2(existing[agent_idx], dest)
        return eid, 'copied_from_cache'
    try:
        b = get_agent_logs_bytes(c, eid, agent_idx)
        with open(dest, 'wb') as f:
            f.write(b)
        return eid, f'downloaded_{len(b)}b'
    except Exception as ex:
        return eid, f'error:{ex}'

log_jobs = [(r['episode_id'], r['player_seat']) for r in all_rows]
log_jobs = sorted(set(log_jobs))
t1 = time.time()
with ThreadPoolExecutor(max_workers=6) as pool:
    futs = {pool.submit(ensure_log, eid, seat, None): (eid, seat) for eid, seat in log_jobs}
    done_n = 0
    for fut in as_completed(futs):
        eid, res = fut.result()
        log_results[eid] = res
        done_n += 1
        if done_n % 50 == 0:
            print(f"  logs: {done_n}/{len(log_jobs)} ({time.time()-t1:.0f}s)")
print(f"Log download phase done in {time.time()-t1:.0f}s")
json.dump(log_results, open(os.path.join(ROOT, OUT, 'log_download_results.json'), 'w'), indent=2)

print("DONE fetch_our_subs.py")
