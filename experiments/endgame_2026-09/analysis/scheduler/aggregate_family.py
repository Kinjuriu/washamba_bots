import sys, os, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aggregate import load_games, team_summary, FAMILY, FEAT_DIR, ROOT

by_family = {'DSM': [], 'Boey': [], 'other': [], 'W3': []}
for path in sorted(glob.glob(os.path.join(FEAT_DIR, '*.jsonl'))):
    games = load_games(path)
    if not games:
        continue
    team = games[0]['team']
    fam = FAMILY.get(team, 'other')
    by_family[fam].extend(games)

out = []
for fam, games in by_family.items():
    if not games:
        continue
    s = team_summary(fam, games)
    s['n_games'] = len(games)
    s['n_teams'] = len(set(g['team'] for g in games))
    out.append(s)

json.dump(out, open(os.path.join(ROOT, 'analysis/scheduler/family_summaries.json'), 'w'), indent=2, default=str)
for s in out:
    print(s['team'], 'n_games=', s['n_games'], 'n_teams=', s['n_teams'])
