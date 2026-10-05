"""Run the per-game extractor over the top-12 stratified corpus (30 games/team, using
the manifest's seat column) and a 30-game sample of our own W3 seats from
episodes/20260924T161358Z_washamba_0924b/. Streams one replay at a time. Writes one
JSONL file of per-game summaries per team into analysis/scheduler/features/.
"""
import sys, os, csv, json, random

ROOT = '/Users/stephanengugi/KagricultureLocalData'
sys.path.insert(0, os.path.join(ROOT, 'analysis/scheduler'))
from extract import load_replay, analyze_game

FEAT_DIR = os.path.join(ROOT, 'analysis/scheduler/features')
os.makedirs(FEAT_DIR, exist_ok=True)

TOP12_DIR = os.path.join(ROOT, 'episodes/20260927T124109Z_top12_strat')
W3_DIR = os.path.join(ROOT, 'episodes/20260924T161358Z_washamba_0924b')
W3_SUBMISSION = '56518334'


def slugify(name):
    return ''.join(c if c.isalnum() else '_' for c in name).strip('_').lower()


def run_top12():
    with open(os.path.join(TOP12_DIR, 'manifest.csv')) as f:
        rows = list(csv.DictReader(f))
    by_team = {}
    for r in rows:
        by_team.setdefault(r['team_name'], []).append(r)

    for team, trows in by_team.items():
        out_path = os.path.join(FEAT_DIR, f'top12_{slugify(team)}.jsonl')
        n_ok, n_err = 0, 0
        with open(out_path, 'w') as out_f:
            for r in trows:
                path = os.path.join(TOP12_DIR, 'replays', f"{r['episode_id']}.json.gz")
                if not os.path.exists(path):
                    n_err += 1
                    continue
                try:
                    d = load_replay(path)
                    seat = int(r['seat'])
                    feats = analyze_game(d, seat, team)
                    feats['group'] = 'top12'
                    out_f.write(json.dumps(feats) + '\n')
                    n_ok += 1
                except Exception as ex:
                    out_f.write(json.dumps(dict(episode_id=r['episode_id'], error=repr(ex))) + '\n')
                    n_err += 1
                del d  # release the replay before the next iteration
        print(f"{team}: {n_ok} ok, {n_err} err -> {out_path}", flush=True)


def run_w3():
    with open(os.path.join(W3_DIR, 'manifest.csv')) as f:
        rows = [r for r in csv.DictReader(f) if r['player_submission'] == W3_SUBMISSION
                and r['state'] == 'COMPLETED' and r['type'] == 'EPISODE_TYPE_PUBLIC']
    random.seed(20260927)
    random.shuffle(rows)
    chosen = []
    for r in rows:
        path = os.path.join(W3_DIR, 'replays', f"{r['episode_id']}.json.gz")
        if os.path.exists(path):
            chosen.append(r)
        if len(chosen) == 30:
            break
    print(f"W3: {len(chosen)} games chosen (from {len(rows)} candidates)", flush=True)

    out_path = os.path.join(FEAT_DIR, 'w3.jsonl')
    n_ok, n_err = 0, 0
    with open(out_path, 'w') as out_f:
        for r in chosen:
            path = os.path.join(W3_DIR, 'replays', f"{r['episode_id']}.json.gz")
            try:
                d = load_replay(path)
                seat = int(r['player_seat'])
                feats = analyze_game(d, seat, 'W3')
                feats['group'] = 'w3'
                out_f.write(json.dumps(feats) + '\n')
                n_ok += 1
            except Exception as ex:
                out_f.write(json.dumps(dict(episode_id=r['episode_id'], error=repr(ex))) + '\n')
                n_err += 1
            del d
    print(f"W3: {n_ok} ok, {n_err} err -> {out_path}", flush=True)


if __name__ == '__main__':
    run_top12()
    run_w3()
    print("DONE run_extract.py")
