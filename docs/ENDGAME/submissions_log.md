# Submissions log - endgame

| when (UTC) | id | file | evicted | hypothesis | read at |
|---|---|---|---|---|---|
| 2026-09-21 13:35 | 56431632 | agents/washamba_base_v1.py | 56202213 (nf) | verbatim public 2945 Farm base; expect ~2,900 converged; control for every later experiment | n>=40 on Sept 22 evening: `experiments/ladder_episodes.py 56431632 56202203` |
| 2026-09-21 23:01 | 56442571 | agents/washamba_base_v1_fork.py | 56202203 (nf_trim) | base + _CA_FEED_DAYS 1 + (2,4) wheat cycle; mirror 28-4 vs base, self-play -3,180 on seed 300 only | equal n vs 56431632, Sept 22 evening |
| 2026-09-22 05:41 | 56450651 | agents/washamba_base_v1.py | 56441221 (teammate atlas_profile, 464 - had evicted 56431632) | restore the base slot; active pair = fork 56442571 + this | equal n vs 56442571 |
| 2026-09-23 08:16 | 56483603 | agents/washamba_base_v1_fork.py | teammate router | restore; pair = V56 + fork | equal n |
| 2026-09-23 08:16 | 56483595 | agents/washamba_base_v2.py (public V56 verbatim) | teammate router | 16-0 vs base and fork locally; author live ~2,751 | n>=40, Sept 24 |
