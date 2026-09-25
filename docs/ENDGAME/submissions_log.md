# Submissions log - endgame

| when (UTC) | id | file | evicted | hypothesis | read at |
|---|---|---|---|---|---|
| 2026-09-21 13:35 | 56431632 | agents/washamba_base_v1.py | 56202213 (nf) | verbatim public 2945 Farm base; expect ~2,900 converged; control for every later experiment | n>=40 on Sept 22 evening: `experiments/ladder_episodes.py 56431632 56202203` |
| 2026-09-21 23:01 | 56442571 | agents/washamba_base_v1_fork.py | 56202203 (nf_trim) | base + _CA_FEED_DAYS 1 + (2,4) wheat cycle; mirror 28-4 vs base, self-play -3,180 on seed 300 only | equal n vs 56431632, Sept 22 evening |
| 2026-09-22 05:41 | 56450651 | agents/washamba_base_v1.py | 56441221 (teammate atlas_profile, 464 - had evicted 56431632) | restore the base slot; active pair = fork 56442571 + this | equal n vs 56442571 |
| 2026-09-23 08:16 | 56483603 | agents/washamba_base_v1_fork.py | teammate router | restore; pair = V56 + fork | equal n |
| 2026-09-23 08:16 | 56483595 | agents/washamba_base_v2.py (public V56 verbatim) | teammate router | 16-0 vs base and fork locally; author live ~2,751 | n>=40, Sept 24 |
| 2026-09-25 05:10 UTC | 56540669 | agents/w3_herdsafe2700.py (second W3 draw) | 56521297 (W1) | W1 adds nothing (W3 contains race44 and beats W1 52-28, PR #62); team score = the better of two W3 draws | active pair = W3 56532456 + W3 56540669 |

**Pre-registered decision rule for the W3 + front-running ladder read (written 2026-09-25, before the upload):** `agents/w3_frontrun.py` goes in with W3 `56540669` in the other slot. Read both once each has n ≥ 60 total (≥ 40 after the first 20 burst games), at equal n, with mean opponent ratings within 150 points (`experiments/ladder_episodes.py <frontrun_id> 56540669`). If front-running's post-burst win rate is ≥ W3's, the final pair is W3 + front-running. Otherwise front-running is replaced by a second W3. Decided now, not after seeing the data.
