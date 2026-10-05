import sys, os, csv, json, gzip, statistics as S, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fingerprint import classify, load_replay

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]
manifest = os.path.join(ROOT, OUT, 'manifest.csv')
replays_dir = os.path.join(ROOT, OUT, 'replays')

rows = list(csv.DictReader(open(manifest)))
out_rows = []
missing = 0
for r in rows:
    eid = r['episode_id']
    path = os.path.join(replays_dir, f'{eid}.json.gz')
    if not os.path.exists(path):
        missing += 1
        r['opp_family'] = 'MISSING_REPLAY'
        out_rows.append(r)
        continue
    try:
        rep = load_replay(path)
    except Exception:
        missing += 1
        r['opp_family'] = 'LOAD_ERROR'
        out_rows.append(r)
        continue
    opp_seat = int(r['opponent_seat'])
    fam, m1, m2 = classify(rep, opp_seat)
    r['opp_family'] = fam
    r['opp_row1'] = json.dumps(m1)
    r['opp_row2'] = json.dumps(m2)
    out_rows.append(r)

print(f"missing/unreadable replays: {missing} / {len(rows)}")

cols = list(out_rows[0].keys())
with open(os.path.join(ROOT, OUT, 'manifest_classified.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in out_rows:
        w.writerow(r)

# ---- per-submission summary ----
by_sub = collections.defaultdict(list)
for r in out_rows:
    by_sub[r['display']].append(r)

def band_name(b):
    return b

summary = {}
for disp, rs in by_sub.items():
    n = len(rs)
    wins = sum(1 for r in rs if r['won'] == '1')
    losses = sum(1 for r in rs if r['won'] == '0')
    ties = sum(1 for r in rs if r['won'] == '0.5')
    by_band = collections.defaultdict(lambda: [0, 0, 0])
    for r in rs:
        b = r['opponent_band']
        if r['won'] == '1': by_band[b][0] += 1
        elif r['won'] == '0.5': by_band[b][1] += 1
        else: by_band[b][2] += 1
    by_fam = collections.defaultdict(lambda: [0, 0, 0])
    for r in rs:
        fm = r['opp_family']
        if r['won'] == '1': by_fam[fm][0] += 1
        elif r['won'] == '0.5': by_fam[fm][1] += 1
        else: by_fam[fm][2] += 1
    tape_margins = []
    near_ties_tape = 0
    for r in rs:
        if r['opp_family'] == 'tape':
            try:
                m = float(r['player_bank']) - float(r['opponent_bank'])
                tape_margins.append(m)
                if abs(m) < 500:
                    near_ties_tape += 1
            except Exception:
                pass
    summary[disp] = dict(
        n=n, wins=wins, losses=losses, ties=ties,
        by_band={k: v for k, v in by_band.items()},
        by_family={k: v for k, v in by_fam.items()},
        tape_n=len(tape_margins),
        tape_near_ties_lt500=near_ties_tape,
        tape_median_margin=(S.median(tape_margins) if tape_margins else None),
    )

print(json.dumps(summary, indent=2, default=str))
json.dump(summary, open(os.path.join(ROOT, OUT, 'summary_by_submission.json'), 'w'), indent=2, default=str)
