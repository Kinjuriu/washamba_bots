import sys, os, csv, json, statistics as S, collections
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
        r['team_family'] = 'MISSING_REPLAY'
        r['opp_family'] = 'MISSING_REPLAY'
        out_rows.append(r)
        continue
    try:
        rep = load_replay(path)
    except Exception:
        missing += 1
        r['team_family'] = 'LOAD_ERROR'
        r['opp_family'] = 'LOAD_ERROR'
        out_rows.append(r)
        continue
    my_seat = int(r['player_seat'])
    opp_seat = int(r['opponent_seat'])
    fam_me, m1_me, m2_me = classify(rep, my_seat)
    fam_opp, m1_opp, m2_opp = classify(rep, opp_seat)
    r['team_family'] = fam_me
    r['team_row1'] = json.dumps(m1_me)
    r['team_row2'] = json.dumps(m2_me)
    r['opp_family'] = fam_opp
    out_rows.append(r)

print(f"missing/unreadable replays: {missing} / {len(rows)}")

cols = list(out_rows[0].keys())
with open(os.path.join(ROOT, OUT, 'manifest_classified.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in out_rows:
        w.writerow(r)

by_team = collections.defaultdict(list)
for r in out_rows:
    by_team[r['team_name']].append(r)

summary = {}
for team, rs in by_team.items():
    n = len(rs)
    wins = sum(1 for r in rs if r['won'] == '1')
    losses = sum(1 for r in rs if r['won'] == '0')
    ties = sum(1 for r in rs if r['won'] == '0.5')
    fams = collections.Counter(r['team_family'] for r in rs)
    vs_tape = [r for r in rs if r['opp_family'] == 'tape']
    vs_nontape = [r for r in rs if r['opp_family'] not in ('tape', 'MISSING_REPLAY', 'LOAD_ERROR')]
    def winrate(rs2):
        if not rs2: return None
        w = sum(1 for r in rs2 if r['won'] == '1')
        t = sum(1 for r in rs2 if r['won'] == '0.5')
        return (w + 0.5 * t) / len(rs2)
    def median_margin(rs2):
        ms = []
        for r in rs2:
            try:
                ms.append(float(r['player_bank']) - float(r['opponent_bank']))
            except Exception:
                pass
        return S.median(ms) if ms else None
    banks = []
    for r in rs:
        try:
            banks.append(float(r['player_bank']))
        except Exception:
            pass
    summary[team] = dict(
        n=n, wins=wins, losses=losses, ties=ties,
        own_family_counts=dict(fams),
        n_vs_tape=len(vs_tape), winrate_vs_tape=winrate(vs_tape), median_margin_vs_tape=median_margin(vs_tape),
        n_vs_nontape=len(vs_nontape), winrate_vs_nontape=winrate(vs_nontape), median_margin_vs_nontape=median_margin(vs_nontape),
        median_final_bank=(S.median(banks) if banks else None),
    )

print(json.dumps(summary, indent=2, default=str))
json.dump(summary, open(os.path.join(ROOT, OUT, 'summary_by_team.json'), 'w'), indent=2, default=str)
