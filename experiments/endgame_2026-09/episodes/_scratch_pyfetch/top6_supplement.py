import sys, os, csv, json, random, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from resim_runner import run_resim
from farm_state import snapshot_at_days

ROOT = '/Users/stephanengugi/KagricultureLocalData'
CORPUS = os.path.join(ROOT, 'episodes/20260923T153431Z_top6')
manifest = os.path.join(CORPUS, 'manifest_classified.csv')
replays_dir = os.path.join(CORPUS, 'replays')

rows = list(csv.DictReader(open(manifest)))
by_team = collections.defaultdict(list)
for r in rows:
    by_team[r['player']].append(r)

random.seed(0)
N = 4
selection = {}
for team, rs in by_team.items():
    random.shuffle(rs)
    selection[team] = rs[:N]

all_paths = []
meta = {}
for team, picked in selection.items():
    for r in picked:
        eid = r['episode_id']
        p = os.path.join(replays_dir, f'{eid}.json.gz')
        if os.path.exists(p):
            all_paths.append(p)
            meta[eid] = r

print(f"resim on {len(all_paths)} games", flush=True)
resim_out = run_resim(all_paths)
json.dump(resim_out, open(os.path.join(CORPUS, 'supplement_resim.json'), 'w'), indent=2)

states = {}
for team, picked in selection.items():
    states[team] = {}
    for r in picked:
        eid = r['episode_id']
        seat = int(r['player_seat'])
        path = os.path.join(replays_dir, f'{eid}.json.gz')
        if not os.path.exists(path):
            continue
        try:
            states[team][eid] = snapshot_at_days(path, seat, days=(12,))
        except Exception as ex:
            states[team][eid] = dict(error=str(ex))
json.dump(states, open(os.path.join(CORPUS, 'supplement_states.json'), 'w'), indent=2, default=str)
print("TOP6_SUPPLEMENT_DONE")
