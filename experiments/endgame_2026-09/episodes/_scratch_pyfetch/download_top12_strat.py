"""Phase A, step 3 (download-only) and step 4 support: download replay files listed in
manifest.csv into <OUT>/replays/, reusing any replay already on disk, at most 2 parallel
requests, with backoff on 429/503, and validate-gzip-revalidate (write gz, then immediately
decompress it back to confirm it is not truncated/corrupt before accepting it).
"""
import sys, os, csv, json, gzip, time, random
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_lib import client, get_replay_bytes

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]  # e.g. episodes/20260927T153000Z_top12_strat  (relative to ROOT)
OUT_ABS = os.path.join(ROOT, OUT)
os.makedirs(os.path.join(OUT_ABS, 'replays'), exist_ok=True)

# Reuse replays already fetched for earlier corpora on this disk (dedup by episode id).
EXISTING_DIRS = [
    os.path.join(ROOT, 'episodes/20260923T153431Z_top6/replays'),
    os.path.join(ROOT, 'episodes/20260924T161358Z_ranks7to12/replays'),
    os.path.join(ROOT, 'episodes/20260924T161358Z_washamba_0924b/replays'),
]

def find_existing(eid):
    for d in EXISTING_DIRS:
        p = os.path.join(d, f'{eid}.json.gz')
        if os.path.exists(p):
            return p
    return None

with open(os.path.join(OUT_ABS, 'manifest.csv')) as f:
    eids = sorted({row['episode_id'] for row in csv.DictReader(f)})
print(f"{len(eids)} distinct episodes in manifest", flush=True)

c = client()
results_path = os.path.join(OUT_ABS, 'download_results.json')
results = json.load(open(results_path)) if os.path.exists(results_path) else {}
lock_write_every = 10

def validate_gzip(path):
    """Revalidate: reopen the just-written gz file and confirm it decompresses cleanly."""
    try:
        with gzip.open(path, 'rb') as f:
            data = f.read()
        return len(data) > 0
    except Exception:
        return False

def ensure_replay(eid):
    dest = os.path.join(OUT_ABS, 'replays', f'{eid}.json.gz')
    if os.path.exists(dest):
        if validate_gzip(dest):
            return eid, 'already_in_out'
        os.remove(dest)  # corrupt leftover, refetch below

    src = find_existing(eid)
    if src:
        import shutil
        shutil.copy2(src, dest)
        if validate_gzip(dest):
            return eid, 'copied_from_cache'
        os.remove(dest)
        return eid, 'error:cached_copy_failed_revalidate'

    backoff = 3.0
    for attempt in range(6):
        try:
            b = get_replay_bytes(c, int(eid))
            gz = gzip.compress(b, compresslevel=6)
            with open(dest, 'wb') as f:
                f.write(gz)
            if validate_gzip(dest):
                return eid, f'downloaded_{len(gz)}b'
            os.remove(dest)
            return eid, 'error:failed_revalidate_after_download'
        except Exception as ex:
            msg = str(ex)
            if '429' in msg or '503' in msg:
                time.sleep(backoff + random.uniform(0, 1))
                backoff = min(backoff * 1.7, 60)
            else:
                time.sleep(1.0)
    return eid, f'error:exhausted_retries'

todo = [e for e in eids if results.get(e, '').startswith('error') or e not in results]
print(f"{len(todo)} to fetch/verify (others already recorded ok)", flush=True)

t0 = time.time()
with ThreadPoolExecutor(max_workers=2) as pool:  # at most 2 parallel downloads, per instructions
    futs = {pool.submit(ensure_replay, eid): eid for eid in todo}
    done_n = 0
    for fut in as_completed(futs):
        eid, res = fut.result()
        results[eid] = res
        done_n += 1
        if done_n % 10 == 0 or done_n == len(todo):
            print(f"  {done_n}/{len(todo)} ({time.time()-t0:.0f}s)", flush=True)
            json.dump(results, open(results_path, 'w'), indent=2)

json.dump(results, open(results_path, 'w'), indent=2)

errors = {k: v for k, v in results.items() if v.startswith('error')}
total_bytes = 0
for eid in eids:
    p = os.path.join(OUT_ABS, 'replays', f'{eid}.json.gz')
    if os.path.exists(p):
        total_bytes += os.path.getsize(p)
print(f"Done. {len(errors)} errors. Total replay bytes on disk for this corpus: {total_bytes/1e6:.1f} MB")
json.dump(dict(errors=errors, total_mb=total_bytes/1e6), open(os.path.join(OUT_ABS, 'download_summary.json'), 'w'), indent=2)
print("DONE download_top12_strat.py")
