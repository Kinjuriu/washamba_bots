import sys, os, json

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]  # e.g. episodes/20260924T161358Z_ranks7to12
d = os.path.join(ROOT, OUT)

team_counts = json.load(open(os.path.join(d, 'team_episode_counts.json')))
team_summary = json.load(open(os.path.join(d, 'summary_by_team.json')))
lb_snapshot = json.load(open(os.path.join(d, 'leaderboard_snapshot.json')))

top6_summary_path = os.path.join(ROOT, 'episodes/20260923T153431Z_top6/summary_by_team_family.json')
top6_summary = json.load(open(top6_summary_path)) if os.path.exists(top6_summary_path) else {}
top6_agg_path = os.path.join(ROOT, 'episodes/20260923T153431Z_top6/aggregate_stats.json')
top6_agg = json.load(open(top6_agg_path)) if os.path.exists(top6_agg_path) else {}

print(json.dumps(team_summary, indent=2, default=str))
print("---top6---")
print(json.dumps(top6_summary, indent=2, default=str))
