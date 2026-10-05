import sys, os, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from farm_state import snapshot_at_days

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]
sel_path = os.path.join(ROOT, OUT, 'ranks_resim_selection.json')
manifest_path = os.path.join(ROOT, OUT, 'manifest_classified.csv')
replays_dir = os.path.join(ROOT, OUT, 'replays')

selection = json.load(open(sel_path))
rows = list(csv.DictReader(open(manifest_path)))
row_by_eid_team = {}
for r in rows:
    row_by_eid_team[(r['team_name'], r['episode_id'])] = r

out = {}
for team, eids in selection.items():
    out[team] = {}
    for eid in eids:
        r = row_by_eid_team.get((team, eid))
        if r is None:
            continue
        seat = int(r['player_seat'])
        path = os.path.join(replays_dir, f'{eid}.json.gz')
        if not os.path.exists(path):
            continue
        try:
            snap = snapshot_at_days(path, seat)
            out[team][eid] = snap
        except Exception as ex:
            out[team][eid] = dict(error=str(ex))
    print(team, "done", len(out[team]), flush=True)

json.dump(out, open(os.path.join(ROOT, OUT, 'farm_states.json'), 'w'), indent=2, default=str)
print("EXTRACT_STATES_DONE")
