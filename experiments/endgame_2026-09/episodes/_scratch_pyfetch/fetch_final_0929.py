"""Final scan, 29 Sep night, Part B step 5: list every completed episode since
2026-09-28 18:30 UTC for our two active submissions (nikaangukia_meroni.py,
tetsu_step1009_full.py) and download every replay. Read-only."""
import sys, os, csv, json, gzip, time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_lib import client, list_submission_episodes, get_replay_bytes
from leaderboard_lookup import load_leaderboard, band
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = 'episodes/20260929_final'
OUT_ABS = os.path.join(ROOT, OUT)
os.makedirs(os.path.join(OUT_ABS, 'replays'), exist_ok=True)

CUTOFF = datetime(2026, 9, 28, 18, 30, 0)

SUBS = {
    56681229: 'nikaangukia_meroni.py (Stephane, Step1009)',
    56645467: 'tetsu_step1009_full.py (Stephane, Step1009)',
}

lb_glob = [f for f in os.listdir(OUT_ABS) if f.startswith('kaggriculture-publicleaderboard') and f.endswith('.csv')]
assert lb_glob, "no leaderboard csv found in OUT"
lb = load_leaderboard(os.path.join(OUT_ABS, lb_glob[0]))
print("leaderboard snapshot:", lb_glob[0], f"({len(lb)} teams)")

c = client()
all_rows = []
non_done = []
per_sub_meta = {}

for sid, label in SUBS.items():
    eps = list_submission_episodes(c, sid)
    non_val = [e for e in eps if e['type'] != 'EPISODE_TYPE_VALIDATION']
    recent = []
    for e in non_val:
        et = e['end_time']
        try:
            dt = datetime.fromisoformat(et.replace('Z', '').split('+')[0][:26])
        except Exception:
            dt = None
        if dt and dt >= CUTOFF:
            recent.append(e)
    recent_completed = [e for e in recent if e['state'] == 'COMPLETED']
    recent_other_state = [e for e in recent if e['state'] != 'COMPLETED']
    per_sub_meta[label] = dict(sid=sid, total_api=len(eps), since_cutoff=len(recent),
                                since_cutoff_completed=len(recent_completed),
                                since_cutoff_other_state=[(e['episode_id'], e['state']) for e in recent_other_state])
    for e in recent_other_state:
        non_done.append(dict(submission=label, episode_id=e['episode_id'], episode_state=e['state']))
    for e in recent_completed:
        me = next((a for a in e['agents'] if a['submission_id'] == sid), None)
        opp = next((a for a in e['agents'] if a['submission_id'] != sid), None)
        if me is None:
            continue
        won = None
        if opp and me['reward'] is not None and opp['reward'] is not None:
            won = 1 if me['reward'] > opp['reward'] else (0.5 if me['reward'] == opp['reward'] else 0)
        oppinfo = lb.get(opp['team_id']) if opp else None
        row = dict(
            submission=label, submission_id=sid, episode_id=e['episode_id'], end_time=e['end_time'],
            seat=me['index'], our_bank=me['reward'],
            opp_bank=opp['reward'] if opp else None,
            margin=(me['reward'] - opp['reward']) if (opp and me['reward'] is not None and opp['reward'] is not None) else None,
            won=won,
            opp_team=opp['team_name'] if opp else None,
            opp_submission=opp['submission_id'] if opp else None,
            opp_rating_at_the_time=oppinfo['score'] if oppinfo else None,
            opp_band=band(oppinfo['score'] if oppinfo else None),
        )
        all_rows.append(row)
        if me['reward'] is None or (opp and opp['reward'] is None):
            non_done.append(dict(row, reason='reward_none'))

print("=== per-submission episode counts (API, since cutoff) ===")
print(json.dumps(per_sub_meta, indent=2))
print(f"non-DONE agent statuses found: {len(non_done)}")

cols = ['submission','submission_id','episode_id','end_time','seat','our_bank','opp_bank','margin','won',
        'opp_team','opp_submission','opp_rating_at_the_time','opp_band']
with open(os.path.join(OUT_ABS, 'episodes.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in all_rows:
        w.writerow(r)
print(f"Wrote {os.path.join(OUT, 'episodes.csv')} ({len(all_rows)} rows)")

json.dump(per_sub_meta, open(os.path.join(OUT_ABS, 'sub_episode_counts.json'), 'w'), indent=2)
json.dump(non_done, open(os.path.join(OUT_ABS, 'non_done_agents.json'), 'w'), indent=2, default=str)

# ---- download every replay ----
distinct_eids = sorted({r['episode_id'] for r in all_rows})
print(f"distinct episodes to download: {len(distinct_eids)}")

download_results = {}
def ensure_replay(eid):
    dest = os.path.join(OUT_ABS, 'replays', f'{eid}.json.gz')
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
json.dump(download_results, open(os.path.join(OUT_ABS, 'download_results.json'), 'w'), indent=2)
print("DONE fetch_final_0929.py")
