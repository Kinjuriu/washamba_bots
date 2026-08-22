"""Stratify our ladder episodes by how strong the opponent was.

The rating alone cannot tell you WHY you are behind. Two very different
stories produce the same score: you bank the same money as the field and
lose on matchups, or you bank far less and lose on economy. Splitting our
own episodes by the opponent's rating going in separates them - if the
teams rated 800 points above us bank roughly what we bank, the gap is not
economic.

Usage:
    python experiments/opponent_strata.py 55650592 55638404
"""

import statistics as st
import sys

from ladder_episodes import fetch_episodes

BANDS = [(0, 1200), (1200, 1500), (1500, 1700), (1700, 1900),
         (1900, 2200), (2200, 2500), (2500, 9999)]


def rows_for(submission_id):
    """(our_bank, opp_bank, opp_rating_before) per completed episode."""
    sid = int(submission_id)
    out = []
    for ep in fetch_episodes(sid):
        if ep.get("state") != "COMPLETED":
            continue
        mine = [a for a in ep["agents"] if a.get("submissionId") == sid]
        opp = [a for a in ep["agents"] if a.get("submissionId") != sid]
        if not mine or not opp:
            continue
        m, o = mine[0], opp[0]
        if m.get("reward") is None or o.get("reward") is None:
            continue
        if o.get("initialScore") is None:
            continue
        out.append((m["reward"], o["reward"], o["initialScore"]))
    return out


def report(label, rows):
    print(f"\n== {label}  ({len(rows)} episodes) ==")
    print(f"  {'opp rating':>12}  {'n':>4}  {'our bank':>9}  {'opp bank':>9}  "
          f"{'margin':>8}  {'wins':>7}")
    for lo, hi in BANDS:
        band = [r for r in rows if lo <= r[2] < hi]
        if not band:
            continue
        ours = st.mean(r[0] for r in band)
        opps = st.mean(r[1] for r in band)
        wins = sum(1 for r in band if r[0] > r[1])
        name = f"{lo}-{hi}" if hi < 9999 else f"{lo}+"
        print(f"  {name:>12}  {len(band):>4}  {ours:>9.0f}  {opps:>9.0f}  "
              f"{ours - opps:>+8.0f}  {wins:>3}/{len(band):<3}")


def main(argv):
    ids = argv[1:]
    if not ids:
        raise SystemExit(__doc__)
    pooled = []
    for sid in ids:
        rows = rows_for(sid)
        report(sid, rows)
        pooled += rows
    if len(ids) > 1:
        report("POOLED", pooled)


if __name__ == "__main__":
    main(sys.argv)
