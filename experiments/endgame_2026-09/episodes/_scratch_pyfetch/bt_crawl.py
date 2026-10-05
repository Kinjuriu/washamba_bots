"""Phase B: results-only crawl (no replays, no logs) for a local Bradley-Terry fit.
Seed submissions come from the manifests of the two 24 Sept corpora, the fresh top12_strat
corpus, and our own active submissions (w6_herdsafe_frontrun.py, w3_frontrun.py). For each
seed submission, page ListEpisodes and record every completed, non-validation public episode
(episode_id, end_time, and per-seat submission_id/team_id/team_name/reward/status), capped at
400 per submission (most recent first), deduped by episode_id.
"""
import sys, os, csv, json, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_lib import client, list_submission_episodes

ROOT = '/Users/stephanengugi/KagricultureLocalData'
TS = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
OUT = os.path.join(ROOT, 'episodes', f'{TS}_bt_crawl')
os.makedirs(OUT, exist_ok=True)

MANIFESTS = [
    'episodes/20260924T161358Z_washamba_0924b/manifest.csv',
    'episodes/20260924T161358Z_ranks7to12/manifest.csv',
    'episodes/20260927T124109Z_top12_strat/manifest.csv',
]

seed_ids = set()
for rel in MANIFESTS:
    path = os.path.join(ROOT, rel)
    with open(path) as f:
        for row in csv.DictReader(f):
            if row.get('player_submission'):
                seed_ids.add(int(row['player_submission']))
            opp_col = 'opponent_submission' if 'opponent_submission' in row else 'opp_submission'
            if row.get(opp_col):
                seed_ids.add(int(row[opp_col]))

OUR_SUBS = {
    'w6_herdsafe_frontrun.py': 56601524,
    'w3_frontrun.py (Peter)': 56596297,
}
for name, sid in OUR_SUBS.items():
    seed_ids.add(sid)

seed_ids = sorted(seed_ids)
print(f"{len(seed_ids)} distinct seed submissions "
      f"(from 3 manifests both sides + our 2 active submissions)", flush=True)
json.dump(dict(seed_submissions=seed_ids, our_subs=OUR_SUBS, manifests_used=MANIFESTS),
          open(os.path.join(OUT, 'seed_submissions.json'), 'w'), indent=2)

c = client()
seen_eids = set()
n_written = 0
per_sub_counts = {}
jsonl_path = os.path.join(OUT, 'episodes.jsonl')

with open(jsonl_path, 'w') as out_f:
    for i, sid in enumerate(seed_ids):
        try:
            eps = list_submission_episodes(c, sid)
        except Exception as ex:
            print(f"  [{i+1}/{len(seed_ids)}] submission {sid}: ERROR {ex}", flush=True)
            per_sub_counts[sid] = f'error:{ex}'
            continue
        completed = [e for e in eps if e['type'] != 'EPISODE_TYPE_VALIDATION' and e['state'] == 'COMPLETED']
        completed.sort(key=lambda e: e['end_time'], reverse=True)
        capped = completed[:400]
        new_n = 0
        for e in capped:
            if e['episode_id'] in seen_eids:
                continue
            seen_eids.add(e['episode_id'])
            row = dict(episode_id=e['episode_id'], end_time=e['end_time'], status=e['state'],
                       type=e['type'], agents=e['agents'])
            out_f.write(json.dumps(row) + '\n')
            n_written += 1
            new_n += 1
        per_sub_counts[sid] = dict(total_api=len(eps), completed_nonval=len(completed),
                                    capped_at=len(capped), new_unique=new_n)
        if (i + 1) % 10 == 0 or i == len(seed_ids) - 1:
            print(f"  [{i+1}/{len(seed_ids)}] submission {sid}: "
                  f"{len(completed)} completed, {new_n} new unique episodes "
                  f"(running total {n_written})", flush=True)
        time.sleep(0.1)

json.dump(per_sub_counts, open(os.path.join(OUT, 'per_submission_counts.json'), 'w'), indent=2)
print(f"Wrote {jsonl_path}: {n_written} unique episodes", flush=True)

# distinct teams seen
teams = set()
for line in open(jsonl_path):
    row = json.loads(line)
    for a in row['agents']:
        if a.get('team_id'):
            teams.add(a['team_id'])
print(f"distinct teams: {len(teams)}", flush=True)

# leaderboard snapshot: reuse the full leaderboard just paged for the top12_strat run
# (same session, minutes old) rather than re-paging ~10k rows again.
src_lb = os.path.join(ROOT, 'episodes/20260927T124109Z_top12_strat/leaderboard_full_snapshot.csv')
dst_lb = os.path.join(OUT, 'leaderboard.csv')
import shutil
shutil.copy2(src_lb, dst_lb)
print(f"Copied leaderboard snapshot -> {dst_lb} (reused from top12_strat run, same session)", flush=True)

file_size_mb = os.path.getsize(jsonl_path) / 1e6
report = dict(
    seed_submissions=len(seed_ids), episodes=n_written, distinct_teams=len(teams),
    episodes_jsonl_mb=round(file_size_mb, 2), out_dir=OUT,
)
json.dump(report, open(os.path.join(OUT, 'report.json'), 'w'), indent=2)
print(json.dumps(report, indent=2))
print(f"OUT={OUT}")
print("DONE bt_crawl.py")
