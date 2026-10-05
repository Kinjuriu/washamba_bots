import sys, os, csv, json, statistics as S, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fingerprint import classify, load_replay

ROOT = '/Users/stephanengugi/KagricultureLocalData'
CORPUS = os.path.join(ROOT, 'episodes/20260923T153431Z_top6')
manifest = os.path.join(CORPUS, 'manifest.csv')
replays_dir = os.path.join(CORPUS, 'replays')

rows = list(csv.DictReader(open(manifest)))
out_rows = []
missing = 0
cache = {}
for r in rows:
    eid = r['episode_id']
    if eid not in cache:
        path = os.path.join(replays_dir, f'{eid}.json.gz')
        if not os.path.exists(path):
            cache[eid] = None
        else:
            try:
                cache[eid] = load_replay(path)
            except Exception:
                cache[eid] = None
    rep = cache[eid]
    if rep is None:
        missing += 1
        r['team_family'] = 'MISSING'
        r['opp_family'] = 'MISSING'
        out_rows.append(r)
        continue
    my_seat = int(r['player_seat'])
    opp_seat = int(r['opponent_seat'])
    fam_me, m1, m2 = classify(rep, my_seat)
    fam_opp, _, _ = classify(rep, opp_seat)
    r['team_family'] = fam_me
    r['opp_family'] = fam_opp
    out_rows.append(r)

print(f"missing: {missing}/{len(rows)}")
cols = list(out_rows[0].keys())
with open(os.path.join(CORPUS, 'manifest_classified.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in out_rows:
        w.writerow(r)

by_team = collections.defaultdict(list)
for r in out_rows:
    by_team[r['player']].append(r)

summary = {}
for team, rs in by_team.items():
    n = len(rs)
    wins = sum(1 for r in rs if r['won'] == '1')
    fams = collections.Counter(r['team_family'] for r in rs)
    vs_tape = [r for r in rs if r['opp_family'] == 'tape']
    w_tape = sum(1 for r in vs_tape if r['won'] == '1')
    margins = []
    for r in rs:
        try:
            margins.append(float(r['player_bank']) - float(r['opponent_bank']))
        except Exception:
            pass
    banks = []
    for r in rs:
        try:
            banks.append(float(r['player_bank']))
        except Exception:
            pass
    summary[team] = dict(
        n=n, wins=wins, losses=n - wins,
        own_family_counts=dict(fams),
        n_vs_tape=len(vs_tape), wins_vs_tape=w_tape,
        median_margin=(S.median(margins) if margins else None),
        median_final_bank=(S.median(banks) if banks else None),
    )
print(json.dumps(summary, indent=2, default=str))
json.dump(summary, open(os.path.join(CORPUS, 'summary_by_team_family.json'), 'w'), indent=2, default=str)
