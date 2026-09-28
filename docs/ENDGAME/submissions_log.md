# Submissions log - endgame

| when (UTC) | id | file | evicted | hypothesis | read at |
|---|---|---|---|---|---|
| 2026-09-21 13:35 | 56431632 | agents/washamba_base_v1.py | 56202213 (nf) | verbatim public 2945 Farm base; expect ~2,900 converged; control for every later experiment | n>=40 on Sept 22 evening: `experiments/ladder_episodes.py 56431632 56202203` |
| 2026-09-21 23:01 | 56442571 | agents/washamba_base_v1_fork.py | 56202203 (nf_trim) | base + _CA_FEED_DAYS 1 + (2,4) wheat cycle; mirror 28-4 vs base, self-play -3,180 on seed 300 only | equal n vs 56431632, Sept 22 evening |
| 2026-09-22 05:41 | 56450651 | agents/washamba_base_v1.py | 56441221 (teammate atlas_profile, 464 - had evicted 56431632) | restore the base slot; active pair = fork 56442571 + this | equal n vs 56442571 |
| 2026-09-23 08:16 | 56483603 | agents/washamba_base_v1_fork.py | teammate router | restore; pair = V56 + fork | equal n |
| 2026-09-23 08:16 | 56483595 | agents/washamba_base_v2.py (public V56 verbatim) | teammate router | 16-0 vs base and fork locally; author live ~2,751 | n>=40, Sept 24 |
| 2026-09-25 05:10 UTC | 56540669 | agents/w3_herdsafe2700.py (second W3 draw) | 56521297 (W1) | W1 adds nothing (W3 contains race44 and beats W1 52-28, PR #62); team score = the better of two W3 draws | active pair = W3 56532456 + W3 56540669 |
| 2026-09-26 19:34 UTC | 56587398 | W3 again (`main.py`, "re-submitting w3_herdsafe2700") | 56532456 (W3) | third W3 draw; uploaded during the freeze, before front-running went up | active pair = W3 56540669 + W3 56587398 |
| 2026-09-27 03:15 UTC | 56596297 | agents/w3_frontrun.py (PR #63) | 56540669 (W3) | W3 + market-only front-running of tape dumps, K=6; gate 32-0 / 26-6 vs W3 | active pair = W3 56587398 + front-running 56596297 |
| 2026-09-27 07:07 UTC | 56601524 | `w6_herdsafe_frontrun.py` (not in the repo; uploaded by a teammate, description matches front-running's PR #63 summary) | 56587398 (W3) | presumed re-upload of front-running under another name; file not verified | active pair = front-running 56596297 + w6 56601524 |
| 2026-09-27 10:20 UTC | 56605799 | agents/w3_dp_saletiming.py (tetsutani demand-preserving sale timing, Apache-2.0) | 56596297 (front-running) | holdout gate: 26-6 vs W3, 28-4 vs front-running, 28-4 vs W1 and W0, 30-2 vs 2945, 32-0 vs reactive v7; timing safe (docs/ENDGAME/dp_gate_timing_2026-09-27.md) | active pair = w6 56601524 + DP 56605799 |
| 2026-09-27 19:31 UTC | 56617705 | `w3_dp_rebuild.py` (teammate upload, not in the repo) | 56601524 (w6) | rival-sale inference + lookahead; settled ~1,805 vs DP ~2,218 after 19h | active pair = DP 56605799 + rebuild 56617705 |
| 2026-09-28 14:53 UTC | 56644360 | agents/w3_dp_saletiming.py (final pair A) | 56605799 (DP) | re-upload so the rebuild can be replaced; public screen of Sept 27 found nothing that beats DP | active pair = rebuild 56617705 + DP-A 56644360 |
| 2026-09-28 14:53 UTC | 56644371 | agents/w3_dp_saletiming.py (final pair B) | 56617705 (rebuild) | second DP draw; team score = the better slot | **final pair = DP-A 56644360 + DP-B 56644371** |

**Pre-registered decision rule for the W3 + front-running ladder read (written 2026-09-25, before the upload):** `agents/w3_frontrun.py` goes in with W3 `56540669` in the other slot. Read both once each has n ≥ 60 total (≥ 40 after the first 20 burst games), at equal n, with mean opponent ratings within 150 points (`experiments/ladder_episodes.py <frontrun_id> 56540669`). If front-running's post-burst win rate is ≥ W3's, the final pair is W3 + front-running. Otherwise front-running is replaced by a second W3. Decided now, not after seeing the data.

**Amendment (2026-09-27, after the upload, before any front-running games):** the W3 re-upload `56587398` evicted `56532456`, so front-running's upload evicted `56540669` instead of the older W3. The control slot is now `56587398`, the only W3 still active. Everything else in the rule stands: `experiments/ladder_episodes.py 56596297 56587398`.

**Superseded (2026-09-27):** the W3 + front-running rule above no longer applies; no plain W3 is active. New rule: once both active slots have n >= 60 at equal n with opponent means within 150 (`experiments/ladder_episodes.py 56605799 56601524`), the lower post-burst win rate is replaced before Sept 30 20:00 UTC, by DP if w6 is lower, else by front-running.

**Final pair (2026-09-28 14:53 UTC):** two copies of DP, 56644360 and 56644371. Every alternative rated lower on the ladder (W3 ~1,975-1,993, front-running ~1,955, w6 ~1,871, rebuild ~1,805). No further uploads unless one of the pair fails validation.
