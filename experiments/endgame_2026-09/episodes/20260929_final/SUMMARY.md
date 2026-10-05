# Final scan, 2026-09-29 night: ladder games since 2026-09-28 18:30 UTC

Both submissions run byte-identical Step1009 code; they're tracked separately only because
they're separate Kaggle submission IDs with independent episode pools.

## nikaangukia_meroni.py (submission 56681229)
- 45 completed episodes, all DONE/DONE (no non-DONE statuses)
- W-L-T: 21-14-10
- Mean opponent rating: 1704.3

## tetsu_step1009_full.py (submission 56645467)
- 89 completed episodes, W-L-T: 43-29-17
- Mean opponent rating: 1820.4
- 2 non-DONE episodes (episode-level state ERRORED, not counted above):
  - 115091156 (vs stochar, seat 1) and 115114335 (vs Andrey Chankin, seat 1) -- both
    ended within ~1 min of each other (2026-09-29 08:07-08:09 UTC) with reward 0.0 for
    **both** agents, not just ours. Replay (403) and agent logs (400) aren't retrievable
    for either -- Kaggle doesn't expose them for ERRORED episodes. The shared 0-0 result
    and clustered timing point to a platform-side episode failure around that minute,
    not a Step1009 defect; can't confirm root cause without deeper access.

## Combined
- 134 completed episodes, 64-43-27 (W-L-T), overall win rate ~0.72 (wins+0.5*ties)/n
- No sign of degradation vs. the 2026-09-28 ladder check baseline; both submissions
  remain solidly above their opponent pool's mean rating.

Full data: `episodes.csv` (134 rows), `non_done_agents.json`, `replays/` (134 gzip files),
`top20/manifest.csv` + `top20/*.json.gz` (81 replays, ranks 1-20 x 5 most recent each).
