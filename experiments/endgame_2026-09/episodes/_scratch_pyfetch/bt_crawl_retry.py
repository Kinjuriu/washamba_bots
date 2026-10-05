"""Retry the submissions that got 429'd in the first bt_crawl.py pass (the bug: the
error path used `continue`, which skipped the pacing sleep, so once one 429 hit it
fired the rest of the calls back-to-back with no delay). This version retries only
the submissions marked as errors, with a real exponential backoff on 429/503, a
cooldown before starting, and a steady pace between every call whether it succeeds
or fails.
"""
import sys, os, json, time, random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_lib import client, list_submission_episodes

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]  # e.g. episodes/20260927T125004Z_bt_crawl
OUT_ABS = os.path.join(ROOT, OUT)

counts_path = os.path.join(OUT_ABS, 'per_submission_counts.json')
per_sub_counts = json.load(open(counts_path))
failed_ids = [int(k) for k, v in per_sub_counts.items() if isinstance(v, str)]
print(f"{len(failed_ids)} submissions to retry", flush=True)

jsonl_path = os.path.join(OUT_ABS, 'episodes.jsonl')
seen_eids = set()
for line in open(jsonl_path):
    seen_eids.add(json.loads(line)['episode_id'])
print(f"{len(seen_eids)} episodes already recorded from the first pass", flush=True)

c = client()
print("Cooling down 45s to let the rate-limit window reset...", flush=True)
time.sleep(45)

n_written = 0
consecutive_429 = 0
with open(jsonl_path, 'a') as out_f:
    for i, sid in enumerate(failed_ids):
        eps, err = None, None
        backoff = 4.0
        for attempt in range(6):
            try:
                eps = list_submission_episodes(c, sid)
                consecutive_429 = 0
                break
            except Exception as ex:
                err = str(ex)
                if '429' in err or '503' in err:
                    consecutive_429 += 1
                    wait = min(90, backoff + random.uniform(0, 2))
                    time.sleep(wait)
                    backoff *= 1.6
                else:
                    time.sleep(2.0)
        if eps is None:
            per_sub_counts[str(sid)] = f'error_after_retry:{err}'
            print(f"  [{i+1}/{len(failed_ids)}] submission {sid}: STILL FAILING {err}", flush=True)
            time.sleep(2.0)
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
        per_sub_counts[str(sid)] = dict(total_api=len(eps), completed_nonval=len(completed),
                                         capped_at=len(capped), new_unique=new_n)
        if (i + 1) % 20 == 0 or i == len(failed_ids) - 1:
            print(f"  [{i+1}/{len(failed_ids)}] submission {sid}: {len(completed)} completed, "
                  f"{new_n} new (running new total {n_written})", flush=True)
            json.dump(per_sub_counts, open(counts_path, 'w'), indent=2)
        time.sleep(1.2)  # steady pace on EVERY iteration, success or failure

json.dump(per_sub_counts, open(counts_path, 'w'), indent=2)

still_failed = [k for k, v in per_sub_counts.items() if isinstance(v, str)]
print(f"Retry done. {n_written} newly written episodes. {len(still_failed)} submissions still failing.",
      flush=True)

teams = set()
for line in open(jsonl_path):
    row = json.loads(line)
    for a in row['agents']:
        if a.get('team_id'):
            teams.add(a['team_id'])

report = dict(seed_submissions=len(per_sub_counts), episodes=sum(1 for _ in open(jsonl_path)),
              distinct_teams=len(teams), still_failed=len(still_failed),
              episodes_jsonl_mb=round(os.path.getsize(jsonl_path) / 1e6, 2), out_dir=OUT_ABS)
json.dump(report, open(os.path.join(OUT_ABS, 'report.json'), 'w'), indent=2)
print(json.dumps(report, indent=2))
print("DONE bt_crawl_retry.py")
