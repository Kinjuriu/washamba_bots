# Generation-2 black-box constant search (base = W4) — report, 25 Sep 2026

Engine: kaggle-environments 1.32.7. Base = W4 (`V9_RACE_DEFAULT=48, _HP_WINDOW=6`), opponents =
w4 (self), w3, w1, hsv3, v57. Space = `es_space_gen2.json`, `--max-changes 3`, `n=80` random
candidates. Ran with 4 workers (split with the concurrent W4 gate on this 8-core Mac) for the
screen/halving/confirm stages; the second confirm below used all 8 cores once both prior jobs
finished. **5,480 screen+halving+confirm games plus 1,500 second-confirm games (6,980 total): 0
errors, 0 `ok=false`** across every stage.

## Screen stage (seeds 5101-5104, both seats, vs w4/w3/w1/hsv3/v57)

Base (W4 unmodified) scored 0.800 points share. Top 5 of 80 random candidates:

| candidate | points share | params |
|---|---|---|
| c080 | 0.900 | `_HP_WINDOW=7, _V92_P_TOP=2` |
| c020 | 0.900 | `_HP_WINDOW=8` |
| c076 | 0.900 | `_V92_P_TOP=2, _HP_WINDOW=8` |
| c029 | 0.900 | `_HP_WINDOW=7` |
| c059 | 0.900 | `_HP_WINDOW=7, V9_RACE_MAX=60` |

## Halving stage (12 candidates, seeds 5105-5112, both seats) and confirm (seeds 6101-6120)

Base scored 0.8625 in the halving stage (80 games) and combined screen+halving re-ranked the top 12
as below (points weighted by games played in each stage):

| candidate | combined points | halving points | params |
|---|---|---|---|
| c080 | 0.925 | 0.938 | `_HP_WINDOW=7, _V92_P_TOP=2` |
| c020 | 0.925 | 0.938 | `_HP_WINDOW=8` |
| c076 | 0.925 | 0.938 | `_V92_P_TOP=2, _HP_WINDOW=8` |
| c029 | 0.908 | 0.912 | `_HP_WINDOW=7` |
| c059 | 0.908 | 0.912 | `_HP_WINDOW=7, V9_RACE_MAX=60` |
| c060 | 0.908 | 0.912 | `V9_RACE_MARGIN=8, _HP_WINDOW=7` |
| c075 | 0.908 | 0.912 | `_HP_WINDOW=8, V9_RACE_MARGIN=8, V9_COURIER_FROM_HOUR=15` |
| c010 | 0.892 | 0.912 | `V9_RACE_DEFAULT=52, _HP_WINDOW=7, V9_RACE_MAX=52` |
| c021 | 0.858 | 0.838 | `_HP_WINDOW=12, _V92_P_H=72, V9_RACE_MARGIN=8` |
| c063 | 0.858 | 0.838 | `_V92_P_H=72, _HP_WINDOW=12` |
| c065 | 0.858 | 0.838 | `_HP_WINDOW=12` |
| c072 | 0.842 | 0.838 | `V9_RACE_MARGIN=16, _HP_WINDOW=10` |

The top 5 by combined ranking (c080, c020, c076, c029, c059) went on to the confirm stage on fresh
seeds 6101-6120:

| candidate | points | Δ vs base | mean margin | vs w4 | vs w3 | vs w1 | vs hsv3 | vs v57 | params |
|---|---|---|---|---|---|---|---|---|---|
| **base** | 0.710 | — | 426 | 0.50 | 0.85 | 0.55 | 0.85 | 0.80 | `{}` |
| c080 | 0.795 | **+0.085** | 502 | 0.975 | 0.90 | 0.50 | 0.85 | 0.75 | `_HP_WINDOW=7, _V92_P_TOP=2` |
| c020 | 0.775 | +0.065 | 518 | 0.875 | 0.90 | 0.50 | 0.80 | 0.80 | `_HP_WINDOW=8` |
| c076 | 0.765 | +0.055 | 531 | 0.875 | 0.90 | 0.50 | 0.75 | 0.80 | `_V92_P_TOP=2, _HP_WINDOW=8` |
| c029 | 0.795 | **+0.085** | 493 | 0.975 | 0.90 | 0.50 | 0.85 | 0.75 | `_HP_WINDOW=7` |
| c059 | 0.795 | **+0.085** | 493 | 0.975 | 0.90 | 0.50 | 0.85 | 0.75 | `_HP_WINDOW=7, V9_RACE_MAX=60` |

**4 of 5** confirm-stage candidates (c080, c020, c029, c059) clear the ≥0.06-points-share bar over
base; c076 does not (+0.055, just under). Among the four qualifiers, no per-opponent Δ is worse
than -0.10 (the largest drop is -0.05 vs w1 or v57), so all four qualified for a second confirm.

## Constants in the halving-top-12 — inference

Counting how often each constant is *changed* (vs. base) across the 12 halving-stage survivors
above:

| constant | count / 12 |
|---|---|
| `_HP_WINDOW` | **12** |
| `V9_RACE_MARGIN` | 4 |
| `_V92_P_TOP` | 2 |
| `V9_RACE_MAX` | 2 |
| `_V92_P_H` | 2 |
| `V9_COURIER_FROM_HOUR` | 1 |
| `V9_RACE_DEFAULT` | 1 |

**Inference**: `_HP_WINDOW` is touched in every single one of the 12 halving survivors — it is by
far the dominant lever in this generation's space, continuing the pattern the W3 search flagged
(there, all 4 confirmed winners also raised `_HP_WINDOW`). The values chosen here (7 or 8, vs W4's
existing 6) suggest the useful range extends a little further past W4's own tuned value, but the
12/12 candidates that pushed it all the way to 10 or 12 (c021, c063, c065, c072) rank lowest of the
12 — so "higher is better" does not hold indefinitely; 7-8 looks like the sweet spot, not the
ceiling. `V9_RACE_MARGIN=8` (down from base's 12) appears in 4 of 12, a distant second lever. This
is pattern-reading across a 12-candidate sample, not a controlled single-constant sweep.

## Second confirm: base vs {c080, c020, c029, c059}, fresh seeds 7101-7130 (measured)

All four confirm-stage qualifiers cleared the ≥0.06-points-share bar without exceeding the -0.10
per-opponent guard, so all four went to a second confirm — 30 more fresh seeds, both seats, same 5
opponents, run directly via `es_search.py`'s own `run()` function once both concurrent jobs had
finished (all 8 cores). **1,500 games, 0 errors, 0 `ok=false`.**

| candidate | points | Δ vs base | mean margin | vs w4 | vs w3 | vs w1 | vs hsv3 | vs v57 | params |
|---|---|---|---|---|---|---|---|---|---|
| **base** | 0.787 | — | 430 | 0.50 | 0.85 | 0.833 | 0.883 | 0.867 | `{}` |
| c080 | 0.830 | **+0.043** | 496 | 0.883 | 0.85 | 0.733 | 0.85 | 0.833 | `_HP_WINDOW=7, _V92_P_TOP=2` |
| c020 | 0.830 | **+0.043** | 498 | 0.85 | 0.817 | 0.80 | 0.817 | 0.867 | `_HP_WINDOW=8` |
| c029 | 0.830 | **+0.043** | 490 | 0.883 | 0.85 | 0.733 | 0.85 | 0.833 | `_HP_WINDOW=7` |
| c059 | 0.830 | **+0.043** | 490 | 0.883 | 0.85 | 0.733 | 0.85 | 0.833 | `_HP_WINDOW=7, V9_RACE_MAX=60` |

All four beat base again on this independent seed block, all landing at the *same* +0.043 points
share (0.830 vs 0.787) — a smaller margin than the first confirm's +0.085/+0.065, but consistent in
direction across three independent seed blocks (screen, confirm, second confirm) for every
qualifier. c080, c029 and c059 post identical per-opponent numbers in both confirm stages (c059
differs from c029 only by also setting `V9_RACE_MAX=60`, which empirically made no measurable
difference on these seeds); all three sit at exactly -0.10 vs w1, right at the guard boundary.
c020 (`_HP_WINDOW=8` alone) is the gentler change, never worse than -0.066 vs any opponent.

## Bottom line

Raising W4's `_HP_WINDOW` from 6 to 7 (or 8) beats unmodified W4 on three independent fresh-seed
blocks (screen, confirm, second confirm — 6,980 total games, 0 errors), against the same 5-opponent
pool, with per-opponent regressions never worse than -0.10 (w1, and only for the `_HP_WINDOW=7`
variants). The effect is real but modest and shrinking with more/fresher seeds (+0.085 first
confirm → +0.043 second confirm) — consistent with the usual pattern of screen/confirm selection
inflating early estimates. `_HP_WINDOW` continues to be the dominant lever in this constant family,
as it was in the W3-generation search. This run only produced local search results and this report;
it did not edit W4 or any other agent file, and made no Kaggle submission.
