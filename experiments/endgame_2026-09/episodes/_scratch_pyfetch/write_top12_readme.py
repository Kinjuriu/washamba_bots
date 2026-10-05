import sys, os, json, csv

ROOT = '/Users/stephanengugi/KagricultureLocalData'
OUT = sys.argv[1]
OUT_ABS = os.path.join(ROOT, OUT)

team_meta = json.load(open(os.path.join(OUT_ABS, 'team_meta.json')))
snap = json.load(open(os.path.join(OUT_ABS, 'leaderboard_snapshot.json')))
dl = json.load(open(os.path.join(OUT_ABS, 'download_summary.json')))

lines = []
lines.append(f"# Fresh stratified top-12 corpus, {snap['snapshot_time_utc']}\n")
lines.append(f"Leaderboard snapshot taken {snap['snapshot_time_utc']}. 30 games per team, stratified "
              "by seat, opponent rating band (current leaderboard rating), and 6-hour time window. "
              "Read-only: replays only, no agent logs.\n")

lines.append("## Team table\n")
lines.append("| rank | team | rating | submission used | other active sub | completed eps available | sampled |")
lines.append("|---|---|---|---|---|---|---|")
for m in team_meta:
    others = [a for a in m['all_active_submissions'] if a['id'] != m['primary_submission']]
    other_str = ', '.join(f"{a['id']} (score {a['public_score']}, {a['completed_episodes']} completed)"
                           for a in others) if others else '—'
    lines.append(f"| {m['rank']} | {m['name']} | {m['rating']} | {m['primary_submission']} "
                 f"(score {m['primary_public_score']}) | {other_str} | "
                 f"{m['completed_episodes_available']} | {m['episodes_sampled']}/30 |")

lines.append("\n## Stratum cell counts (seat x opponent-rating-band), per team\n")
for m in team_meta:
    lines.append(f"- **{m['name']}**: " + ', '.join(f"{k}={v}" for k, v in m['cell_counts'].items()))

lines.append("\n## Download errors\n")
if dl['errors']:
    for eid, err in dl['errors'].items():
        lines.append(f"- {eid}: {err}")
else:
    lines.append("None.")

lines.append(f"\n## Total size\n\nTotal replay bytes on disk for this corpus: {dl['total_mb']:.1f} MB.\n")
lines.append("Analysis beyond this report is out of scope for this download step.\n")

readme_path = os.path.join(OUT_ABS, 'README.md')
open(readme_path, 'w').write('\n'.join(lines))
print(f"Wrote {readme_path}")
