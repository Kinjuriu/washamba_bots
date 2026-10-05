# W4 wide gate — report, 25 Sep 2026

**Verdict: FAIL** — W4's overall points share across the 7 shared opponents (0.871) is below
W3's (0.886), driven mainly by **w1** (W4 0.700 vs W3 0.800, Δ **-0.100**) and, to a lesser
extent, v57 (W4 0.900 vs W3 0.950, Δ -0.050). No single opponent breaches the -0.10 guard on its
own — w1's Δ sits exactly at, not past, the bar — but the second condition (overall points share
must be at least W3's) is what this gate fails on.

Engine: kaggle-environments 1.32.7. 4 workers (split with the concurrently-running gen-2 search on
this 8-core Mac). Seeds 8001-8020, both seats, against opponents the black-box search never
trained on: w0, w1, v57, k0013, fieldcraft, hsv3, farm2945. **640/640 games completed clean: 0
errors, 0 non-DONE statuses.**

## Per-opponent points share (win=1, tie=0.5, loss=0)

| Opponent | W4 points | W3 points | Δ (w4−w3) | W4 mean margin | W3 mean margin | Games |
|---|---:|---:|---:|---:|---:|---:|
| farm2945 | 0.950 | 0.950 | 0.000 | +1758 | +1691 | 40 |
| fieldcraft | 0.900 | 0.900 | 0.000 | +2097 | +2239 | 40 |
| hsv3 | 0.950 | 0.900 | +0.050 | +801 | +426 | 40 |
| k0013 | 0.950 | 0.950 | 0.000 | +4089 | +4153 | 40 |
| v57 | 0.900 | 0.950 | -0.050 | +710 | +1133 | 40 |
| w0 | 0.750 | 0.750 | 0.000 | +485 | +635 | 40 |
| w1 | 0.700 | 0.800 | **-0.100** | +383 | +638 | 40 |
| **Overall (7 opponents)** | **0.871** | **0.886** | **-0.014** | — | — | 280 |

## Mirror match (the two candidates head-to-head)

| | Points | W-L-T | mean margin | games |
|---|---:|---|---:|---:|
| w4 vs w3 | 0.950 | 38-2-0 | +623 | 40 |

W4 beats W3 head-to-head decisively (0.950) — expected, since W4 *is* c042's constants applied to
W3. This does not by itself pass the gate: the gate's question is whether W4 holds up against the
*wider* pool the search never trained on, not just against W3.

## Self-play sanity check

`w3 vs w3` (same file, both seats): 1-1-38, points 0.500, mean margin +0. Confirms no systematic
first/second-seat scoring bias in the harness for this matchup (a byproduct of listing w3 as both
a candidate and an opponent in one invocation; not part of the gate comparison above).

## Timing (W4 only — not captured by `pool_harness.py`, measured separately)

`pool_harness.py` doesn't record per-turn timing, so a small supplementary run timed W4's own
decision function directly: 4 games (2 seeds × 2 opponents: w0, hsv3), 2,876 of W4's turns.

| mean | p95 | p99 | slowest (max) |
|---:|---:|---:|---:|
| 1.3 ms | 2.9 ms | 5.6 ms | 99.2 ms |

No turn came remotely close to a competition time budget; W4's wider race window and larger
`_HP_WINDOW` are not a performance concern.

## Bottom line

W4 does not clear this gate. Against the two candidates' shared 7-opponent pool, W4's overall
points share (0.871) comes in below W3's (0.886) — a real, if modest, regression. w1 accounts for
most of the gap by itself (the single largest Δ, exactly at the -0.10 guard), with v57 contributing
a smaller Δ in the same direction; every other shared opponent is a tie or a small win for W4
(hsv3 +0.050). W4 also beats W3 head-to-head decisively (0.950). But the letter of this gate's
rule — overall points share at least W3's, with no single-opponent Δ worse than -0.10 — fails on
the overall-share condition, naming **w1** as the opponent responsible. This run produced only
local gate results and this report; no submission file was edited or submitted.
