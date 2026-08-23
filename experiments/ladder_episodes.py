"""Read our actual ladder episodes, not just the rating.

The public score is a rating that starts at ~600 and converges slowly, so two
submissions are only comparable at the SAME episode count. Worse, the rating
folds in opponent strength: a submission that banks more money can still show a
lower score because it drew harder opponents. This pulls the per-episode record
so both can be read directly.

Usage:
    python experiments/ladder_episodes.py                 # two most recent submissions
    python experiments/ladder_episodes.py 55578910 55591700
"""

import json
import os
import statistics as st
import sys
import urllib.request

EPISODES_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
COMPETITION = "kaggriculture"


def _auth_header():
    """Kaggle writes either an OAuth token or a legacy api key to ~/.kaggle."""
    home = os.path.expanduser("~/.kaggle")
    creds = os.path.join(home, "credentials.json")
    if os.path.exists(creds):
        c = json.load(open(creds))
        if c.get("access_token"):
            return {"Authorization": "Bearer " + c["access_token"]}
    legacy = os.path.join(home, "kaggle.json")
    if os.path.exists(legacy):
        import base64

        c = json.load(open(legacy))
        raw = f"{c['username']}:{c['key']}".encode()
        return {"Authorization": "Basic " + base64.b64encode(raw).decode()}
    raise SystemExit("no kaggle credentials found in ~/.kaggle")


def fetch_episodes(submission_id):
    body = json.dumps({"submissionId": int(submission_id)}).encode()
    headers = {"Content-Type": "application/json", **_auth_header()}
    req = urllib.request.Request(EPISODES_URL, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r).get("episodes", [])


def rows_for(submission_id):
    """(end_time, our_score_after, our_bank, opponent_bank, opponent_rating)."""
    out = []
    for ep in fetch_episodes(submission_id):
        if ep.get("state") != "COMPLETED":
            continue
        mine = [a for a in ep["agents"] if a.get("submissionId") == int(submission_id)]
        opp = [a for a in ep["agents"] if a.get("submissionId") != int(submission_id)]
        if not mine or not opp:
            continue
        m, o = mine[0], opp[0]
        if m.get("reward") is None or o.get("reward") is None:
            continue
        out.append((ep["endTime"], m.get("updatedScore"), m["reward"], o["reward"], o.get("initialScore")))
    out.sort()
    return out


def recent_submissions(limit=2):
    import csv
    import io
    import subprocess

    exe = os.path.join(".venv", "Scripts", "kaggle.exe")
    if not os.path.exists(exe):
        exe = "kaggle"
    out = subprocess.run(
        [exe, "competitions", "submissions", COMPETITION, "-v"],
        capture_output=True, text=True,
    ).stdout
    rows = list(csv.DictReader(io.StringIO(out)))
    return [r["ref"] for r in rows[:limit]]


def summarise(submission_id, rows):
    print(f"== {submission_id} ==")
    if not rows:
        print("  no completed episodes yet")
        return
    ours = [r[2] for r in rows]
    opps = [r[3] for r in rows]
    wins = sum(1 for r in rows if r[2] > r[3])
    print(f"  episodes      {len(rows)}   wins {wins}/{len(rows)}")
    print(f"  our bank      mean {st.mean(ours):8.0f}  min {min(ours):7.0f}  max {max(ours):7.0f}")
    print(f"  opponent bank mean {st.mean(opps):8.0f}  min {min(opps):7.0f}  max {max(opps):7.0f}")
    scored = [r[1] for r in rows if r[1] is not None]
    if scored:
        print(f"  score         {scored[0]:.1f} -> {scored[-1]:.1f}")


def main(argv):
    ids = argv[1:] or recent_submissions()
    table = {sid: rows_for(sid) for sid in ids}
    for sid, rows in table.items():
        summarise(sid, rows)

    if len(table) > 1:
        # Equal episode count is NECESSARY but not SUFFICIENT. Two submissions
        # can play their first N episodes against fields hundreds of rating
        # points apart, and beating a 1,200 opponent moves the rating far less
        # than beating an 1,800 one. Measured: 55650592's first 52 episodes
        # averaged an opponent rating of 1,684 (41 of them 1700+) while
        # 55687852's averaged 1,211 (none 1700+) - so their ratings at n=52
        # read 1,774 against 1,443 on near-identical banks. That is a
        # difference in draw, not in agent. Read both lines together.
        n = min(len(r) for r in table.values())
        print(f"{chr(10)}== score at equal episode count (n={n}) ==")
        strengths = []
        for sid, rows in table.items():
            s = [r[1] for r in rows[:n] if r[1] is not None]
            opps = [r[4] for r in rows[:n] if len(r) > 4 and r[4] is not None]
            score = f"{s[-1]:8.1f}" if s else " " * 8
            if opps:
                strengths.append(st.mean(opps))
                hard = sum(1 for o in opps if o >= 1700)
                print(f"  {sid}  {score}   opponents: mean "
                      f"{st.mean(opps):6.0f}, {hard}/{len(opps)} rated 1700+")
            else:
                print(f"  {sid}  {score}")
        if len(strengths) > 1 and max(strengths) - min(strengths) > 150:
            print(f"  !! fields differ by {max(strengths) - min(strengths):.0f}"
                  f" rating points - these scores are NOT comparable")
        print("\n== per-episode score trace ==")
        print("  ep  " + "  ".join(f"{sid:>10}" for sid in table))
        for i in range(max(len(r) for r in table.values())):
            cells = []
            for rows in table.values():
                v = rows[i][1] if i < len(rows) and rows[i][1] is not None else None
                cells.append(f"{v:>10.1f}" if v is not None else f"{'':>10}")
            print(f"  {i + 1:>3}  " + "  ".join(cells))


if __name__ == "__main__":
    main(sys.argv)
