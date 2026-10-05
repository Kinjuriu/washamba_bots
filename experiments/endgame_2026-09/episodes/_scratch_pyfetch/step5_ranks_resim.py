import sys, os, csv, json, collections, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from resim_runner import run_resim

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]  # ranks7to12 dir name
manifest = os.path.join(ROOT, OUT, 'manifest_classified.csv')
replays_dir = os.path.join(ROOT, OUT, 'replays')

rows = list(csv.DictReader(open(manifest)))
by_team = collections.defaultdict(list)
for r in rows:
    by_team[r['team_name']].append(r)

random.seed(0)
selection = {}
for team, rs in by_team.items():
    tape_games = [r for r in rs if r['opp_family'] == 'tape']
    other_games = [r for r in rs if r['opp_family'] != 'tape']
    random.shuffle(tape_games)
    random.shuffle(other_games)
    picked = tape_games[:4] + other_games[:max(0, 8 - min(4, len(tape_games)))]
    picked = picked[:8]
    selection[team] = picked

all_paths = []
meta = {}
for team, picked in selection.items():
    for r in picked:
        eid = r['episode_id']
        p = os.path.join(replays_dir, f'{eid}.json.gz')
        if os.path.exists(p):
            all_paths.append(p)
            meta[eid] = r
        else:
            print(f"WARNING missing replay for selected game {eid} ({team})")

print(f"running resim on {len(all_paths)} games across {len(selection)} teams")
resim_out = run_resim(all_paths)
json.dump(resim_out, open(os.path.join(ROOT, OUT, 'ranks_resim.json'), 'w'), indent=2)

sel_export = {team: [r['episode_id'] for r in picked] for team, picked in selection.items()}
json.dump(sel_export, open(os.path.join(ROOT, OUT, 'ranks_resim_selection.json'), 'w'), indent=2)
print("done")
