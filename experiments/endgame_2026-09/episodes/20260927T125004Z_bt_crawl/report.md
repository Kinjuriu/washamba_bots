# Results-only crawl for a local Bradley-Terry fit, 27 September 2026

Read-only. No replays or logs downloaded, only episode results (episode_id, end_time, and
per-seat submission_id/team_id/team_name/reward/status), filtered to completed, non-validation
public episodes, capped at 400 per submission (most recent first), deduplicated by episode_id.

## Seed set
798 distinct submissions: both sides of every game in the manifests of
`episodes/20260924T161358Z_washamba_0924b/`, `episodes/20260924T161358Z_ranks7to12/`, and the
fresh `episodes/20260927T124109Z_top12_strat/` corpus, plus our two active submissions
(`w6_herdsafe_frontrun.py` = 56601524, Peter's `w3_frontrun.py` = 56596297, resolved from our own
`ListSubmissions` call).

## Note on the run
The first pass hit Kaggle's rate limit at submission 139/798; a bug in the error-handling path
(a bare `continue` that skipped the pacing sleep) then fired the remaining 660 calls back-to-back
with no delay, so they all failed with HTTP 429. That pass alone still yielded 51,314 episodes
from the 138 submissions that got through before the limit hit.

Fixed and retried the 660 failed submissions only, with a 45s cooldown, real exponential backoff
on 429/503, and a steady 1.2s pace on every call regardless of outcome. All 660 succeeded on
retry with 0 still failing.

## Totals (final)
- Seed submissions: 798
- Distinct episodes: 186,348
- Distinct teams: 7,337
- `episodes.jsonl` size: 65.6 MB

## Files
- `episodes.jsonl`: one JSON line per episode.
- `leaderboard.csv`: full live leaderboard snapshot (10,079 teams), reused from the
  `top12_strat` run taken minutes earlier in the same session (2026-09-27T12:41:09Z) rather than
  re-paging ~10k rows a second time.
- `seed_submissions.json`, `per_submission_counts.json`, `report.json`: resolution detail.

Stopped here; fitting the Bradley-Terry model itself is the next (analysis) step, not part of
this crawl.
