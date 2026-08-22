"""Stratify our ladder episodes by how strong the opponent was.

The rating alone cannot tell you WHY you are behind. Two very different
stories produce the same score: you bank the same money as the field and
lose on matchups, or you bank far less and lose on economy. Splitting our
own episodes by the opponent's rating going in separates them - if the
teams rated 800 points above us bank roughly what we bank, the gap is not
economic.

It also reports the near-tie figures, because in a mirror-heavy field the
mean margin is the wrong statistic: it is dragged by a tail of blowout
losses to agents on a different route, and can sit flat while the win rate
doubles. NEAR_TIE_BAND is the margin below which a match was decided by a
rounding error on a ~90,000 economy.

Usage:
    python experiments/opponent_strata.py 55650592 55638404
"""

import statistics as st
import sys

from ladder_episodes import fetch_episodes

BANDS = [(0, 1200), (1200, 1500), (1500, 1700), (1700, 1900),
         (1900, 2200), (2200, 2500), (2500, 9999)]

# The band we actually live in, and the margin below which a match is a
# coin flip rather than a real defeat. Both read off our own record; see
# docs/PUBLIC_META.md.
CONTESTED_BAND = (1700, 1900)
NEAR_TIE_BAND = 5000


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


def report_near_ties(label, rows):
    """The statistic that separates two agents running the same route."""
    lo, hi = CONTESTED_BAND
    band = [r for r in rows if lo <= r[2] < hi]
    if not band:
        return
    margins = sorted(r[0] - r[1] for r in band)
    wins = [m for m in margins if m > 0]
    losses = [m for m in margins if m <= 0]
    close = [m for m in margins if abs(m) < NEAR_TIE_BAND]
    close_won = sum(1 for m in close if m > 0)
    mid = len(margins) // 2
    median = (margins[mid] if len(margins) % 2
              else (margins[mid - 1] + margins[mid]) / 2)
    print("")
    print(f"== {label}: inside the contested band {lo}-{hi} ==")
    print(f"  episodes            {len(band)}")
    print(f"  mean margin         {st.mean(margins):+.0f}")
    print(f"  median margin       {median:+.0f}")
    print(f"  won  {len(wins):>4}   mean win margin  {st.mean(wins) if wins else 0:+.0f}")
    print(f"  lost {len(losses):>4}   mean loss margin {st.mean(losses) if losses else 0:+.0f}")
    pct = 100.0 * len(close) / len(band)
    print(f"  decided by under {NEAR_TIE_BAND}: {len(close)} of {len(band)} ({pct:.0f}%)")
    if close:
        print(f"  NEAR-TIE WIN RATE   {close_won}/{len(close)} "
              f"({100.0 * close_won / len(close):.0f}%)")


def main(argv):
    ids = argv[1:]
    if not ids:
        raise SystemExit(__doc__)
    pooled = []
    for sid in ids:
        rows = rows_for(sid)
        report(sid, rows)
        report_near_ties(sid, rows)
        pooled += rows
    if len(ids) > 1:
        report("POOLED", pooled)


if __name__ == "__main__":
    main(sys.argv)
