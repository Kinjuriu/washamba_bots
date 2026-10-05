# W3 black-box constant search — report, 24 Sep 2026 evening

Engine: kaggle-environments 1.32.7. 7 workers. One game (W3 vs W1, seed 5001) measured at
**T = 3.47s**. Formula `n = 5*3600*workers/(24*T) - 1` gave n ≈ 1512, capped at 60. **n = 60**
was used. Actual wall time came in well under the 5-hour target the formula assumed — screen
took roughly 30 minutes and confirm roughly 15, not the ~12/~6 minutes I predicted before
starting, because subprocess spawn overhead (a fresh Python interpreter per game) dominates
over the raw in-process game time I used for T. Both stages finished clean: **0 errors, 0
`ok=false`** across all 2,184 screen+confirm games.

## Screen stage (seeds 5001-5004, both seats, vs w3/w1/hsv3)

Base (unmodified W3) scored 0.625 points share. Top 5 of 60 random candidates:

| candidate | points share | params |
|---|---|---|
| c042 | 0.917 | `V9_RACE_DEFAULT=48, _HP_WINDOW=6` |
| c059 | 0.833 | `_HP_WINDOW=5, V9_RACE_DEFAULT=48, V9_RACE_GAP=4` |
| c026 | 0.792 | `V9_RACEGATE_MARGIN=-5` |
| c036 | 0.750 | `_HP_WINDOW=6, V9_RACEGATE_MARGIN=-10` |
| c055 | 0.750 | `_HP_WINDOW=6, V9_COURIER_FROM_HOUR=14` |

## Confirm stage (fresh seeds 6001-6020, both seats)

| candidate | points | Δ vs base | mean margin | vs w3 | vs w1 | vs hsv3 | params |
|---|---|---|---|---|---|---|---|
| **base** | 0.600 | — | 83 | 0.50 | 0.55 | 0.75 | `{}` |
| c042 | 0.783 | **+0.183** | 579 | 0.90 | 0.60 | 0.85 | `V9_RACE_DEFAULT=48, _HP_WINDOW=6` |
| c059 | 0.767 | +0.167 | 581 | 0.85 | 0.60 | 0.85 | `_HP_WINDOW=5, V9_RACE_DEFAULT=48, V9_RACE_GAP=4` |
| c026 | 0.592 | −0.008 | 67 | 0.55 | 0.50 | 0.725 | `V9_RACEGATE_MARGIN=-5` |
| c036 | 0.700 | +0.100 | 501 | 0.75 | 0.55 | 0.80 | `_HP_WINDOW=6, V9_RACEGATE_MARGIN=-10` |
| c055 | 0.783 | +0.183 | 562 | 0.90 | 0.55 | 0.90 | `_HP_WINDOW=6, V9_COURIER_FROM_HOUR=14` |

**4 of 5** confirm-stage candidates beat base by the ≥0.06-points-share bar, and none of the four
is worse than base against any single opponent by more than 0.10 (the largest single-opponent
drop among them is c042/c059 at −0.05 vs w1, well inside the bar). Only c026 (screen rank 3,
confirm rank 5) failed to hold up — screen selection inflated it, exactly the noisy-filter
behavior the harness's own docstring warns about.

**Pattern worth flagging as inference, not measured:** all four winners carry `_HP_WINDOW` raised
to 5 or 6; the one loser (c026) is the only top-5 candidate that does *not* touch `_HP_WINDOW`.
This is 4-for-4 on a 5-candidate sample, not a controlled single-constant test, but it points at
`_HP_WINDOW` as a promising isolated lever for a future narrower sweep.

## Second confirm: base vs c042, fresh seeds 7001-7030 (measured)

c042 (`V9_RACE_DEFAULT=48, _HP_WINDOW=6`) cleared the ≥0.06-points-share bar in the first confirm
(+0.183) without exceeding the −0.10 per-opponent guard, so it qualified for a second confirm on
30 more fresh seeds, run directly via `es_search.py`'s own `run()` function (same game harness,
same 3 opponents, both seats — 360 games, 0 errors, 0 `ok=false`):

| candidate | points | mean margin | vs w3 | vs w1 | vs hsv3 |
|---|---|---|---|---|---|
| base | 0.650 | 163 | 0.500 | 0.667 | 0.783 |
| c042 | 0.778 | 461 | 0.800 | 0.633 | 0.900 |

c042 beats base again on an independent seed block: **+0.128 points share, mean margin +298**
(163 → 461). Direction and magnitude are consistent with the first confirm (+0.183 there). The
only softening is vs w1 (0.667 → 0.633, a −0.034 dip), well inside the −0.10 guard and inside
normal seed-to-seed noise.

## Bottom line

`V9_RACE_DEFAULT` 40 → 48 combined with `_HP_WINDOW` raised to 6 (candidate c042) beats
unmodified W3 on two independent fresh-seed confirm blocks (60 games then 360 games), against
all three opponents in the pool, with no single-opponent regression exceeding the guard. This is
not yet submitted or merged into any agent file — per the task's hard limits, this run only
produced local search results and this report; it did not edit W3 or any other agent, and made
no Kaggle submission.
