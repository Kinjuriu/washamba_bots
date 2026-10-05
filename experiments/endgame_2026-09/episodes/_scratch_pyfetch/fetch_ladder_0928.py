"""Ladder check, 28 Sep night: list every completed episode for the three named
submissions (tetsu_step1009_full.py by Stephane, w3_dp_saletiming.py Final pair A/B by
Peter), write episodes.csv, and note any non-DONE agent status. Read-only."""
import sys, os, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_lib import client
from leaderboard_lookup import load_leaderboard, band
from kagglesdk.competitions.types.competition_api_service import ApiListSubmissionEpisodesRequest

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]  # episodes/20260928_ladder_check
OUT_ABS = os.path.join(ROOT, OUT)

SUBS = {
    56645467: 'tetsu_step1009_full.py (Stephane, Step1009)',
    56644360: 'w3_dp_saletiming.py (Peter, Final pair A)',
    56644371: 'w3_dp_saletiming.py (Peter, Final pair B)',
}

lb_glob = [f for f in os.listdir(OUT_ABS) if f.startswith('kaggriculture-publicleaderboard') and f.endswith('.csv')]
assert lb_glob, "no leaderboard csv found in OUT"
lb = load_leaderboard(os.path.join(OUT_ABS, lb_glob[0]))
print("leaderboard snapshot:", lb_glob[0], f"({len(lb)} teams)")

def list_episodes_with_state(c, submission_id):
    # NOTE: ApiEpisodeAgent.state is always EPISODE_AGENT_STATE_UNSPECIFIED on this
    # list endpoint (checked across all 115 episodes below) -- it is not a usable
    # per-agent DONE/ERROR/TIMEOUT signal here. The real signals are the episode-level
    # `state` (COMPLETED/ERRORED/CREATED/NEVER_STARTED) and whether reward is None.
    req = ApiListSubmissionEpisodesRequest(); req.submission_id = submission_id
    resp = c.competitions.competition_api_client.list_submission_episodes(req)
    out = []
    for e in resp.episodes:
        row = dict(episode_id=e.id, create_time=str(e.create_time), end_time=str(e.end_time),
                   state=str(e.state).split('.')[-1], type=str(e.type).split('.')[-1], agents=[])
        for a in e.agents:
            row['agents'].append(dict(submission_id=a.submission_id, index=a.index, reward=a.reward,
                                       team_name=a.team_name, team_id=a.team_id))
        out.append(row)
    return out

c = client()
all_rows = []
non_done = []
per_sub_meta = {}

for sid, label in SUBS.items():
    eps = list_episodes_with_state(c, sid)
    non_val = [e for e in eps if e['type'] != 'EPISODE_TYPE_VALIDATION']
    non_val_completed = [e for e in non_val if e['state'] == 'COMPLETED']
    non_val_other_state = [e for e in non_val if e['state'] != 'COMPLETED']
    per_sub_meta[label] = dict(sid=sid, total_api=len(eps), non_val=len(non_val),
                                non_val_completed=len(non_val_completed),
                                non_val_other_episode_state=[(e['episode_id'], e['state']) for e in non_val_other_state])
    for e in non_val_other_state:
        non_done.append(dict(submission=label, episode_id=e['episode_id'], episode_state=e['state']))
    for e in non_val_completed:
        me = next((a for a in e['agents'] if a['submission_id'] == sid), None)
        opp = next((a for a in e['agents'] if a['submission_id'] != sid), None)
        if me is None:
            continue
        won = None
        if opp and me['reward'] is not None and opp['reward'] is not None:
            if me['reward'] > opp['reward']:
                won = 1
            elif me['reward'] == opp['reward']:
                won = 0.5
            else:
                won = 0
        oppinfo = lb.get(opp['team_id']) if opp else None
        row = dict(
            submission=label, submission_id=sid, episode_id=e['episode_id'], end_time=e['end_time'],
            seat=me['index'], our_bank=me['reward'],
            opp_bank=opp['reward'] if opp else None,
            margin=(me['reward'] - opp['reward']) if (opp and me['reward'] is not None and opp['reward'] is not None) else None,
            won=won,
            opp_team=opp['team_name'] if opp else None,
            opp_submission=opp['submission_id'] if opp else None,
            opp_rating_at_the_time=oppinfo['score'] if oppinfo else None,
            opp_band=band(oppinfo['score'] if oppinfo else None),
        )
        all_rows.append(row)
        if me['reward'] is None or (opp and opp['reward'] is None):
            non_done.append(dict(row, reason='reward_none'))

print("=== per-submission episode counts (API) ===")
print(json.dumps(per_sub_meta, indent=2))
print(f"non-DONE agent statuses found: {len(non_done)}")
for r in non_done:
    print(" ", r['submission'], r['episode_id'], 'our:', r['our_agent_status'], 'opp:', r['opp_agent_status'])

cols = ['submission','submission_id','episode_id','end_time','seat','our_bank','opp_bank','margin','won',
        'opp_team','opp_submission','opp_rating_at_the_time','opp_band']
with open(os.path.join(OUT_ABS, 'episodes.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in all_rows:
        w.writerow(r)
print(f"Wrote {os.path.join(OUT, 'episodes.csv')} ({len(all_rows)} rows)")

json.dump(per_sub_meta, open(os.path.join(OUT_ABS, 'sub_episode_counts.json'), 'w'), indent=2)
json.dump(non_done, open(os.path.join(OUT_ABS, 'non_done_agents.json'), 'w'), indent=2, default=str)
print("DONE fetch_ladder_0928.py")
