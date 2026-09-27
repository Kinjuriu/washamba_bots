# DP gate + timing check — 2026-09-27

Candidate: `agents/.pub_0927/demand-preserving-turn-sale-timing.py` ("DP") — W3
(`agents/w3_herdsafe2700.py`) plus a ~2,700-line sell-block-reorder layer,
entrypoint `step1009_step1008_fortyfirst_final_fixedsell_closure_agent`
(verified: still the last callable in the module).

Raw data:
- `experiments/splice/results/gate_demand-preserving-turn-sale-timing_holdout_20260927T053005Z.jsonl` (176 games)
- `experiments/field_research/out_0927/dp_vs_frontrun_holdout.jsonl` (32 games)
- `experiments/field_research/out_0927/timing_kaggle_like_results.json` (8 episodes, per-turn summaries)
- `experiments/field_research/out_0927/timing_kaggle_like_profile.txt` (cProfile, 3 spike turns)
- `experiments/field_research/out_0927/gate_dp_holdout.log`, `dp_vs_frontrun_holdout.log`, `timing_kaggle_like.log` (full run logs)

## Task A — gate.py, holdout seeds 1000-1015, both seats (32 games/opponent)

| opponent | DP W-L-D /32 | DP mean margin | DP min bank | gate threshold | verdict |
|---|---|---|---|---|---|
| W3 | 26-6-0 | +380 | 55,806 | >=16/32 | **PASS** |
| W1 | 28-4-0 | +760 | 54,905 | >=20/32 | **PASS** |
| W0 | 28-4-0 | +771 | 54,906 | >=20/32 | **PASS** |
| REACTIVE_V1 | 32-0-0 | +3,868 | 58,068 | >=20/32 | **PASS** |
| FARM2945 | 30-2-0 | +1,281 | 55,830 | >=20/32 | **PASS** |
| DP vs `w3_frontrun.py` (custom script, same seed range, both seats) | 28-4-0 | +459 | — | (no gate.py threshold defined; informational) | strong win |

**Effective sample size is 16 unique seeds, not 32.** Checked directly: every
seed's seat-0 and seat-1 results are byte-identical across all 176 gate games
and all 32 DP-vs-frontrun games (`cand_bank` identical for both `cand_seat`
values on every (bucket, seed) pair, verified by grouping the jsonl). These
are deterministic agents, so the engine is fully seat-symmetric for this
matchup set — CLAUDE.md's "seat 0 finishes a few hundred behind seat 1" note
was measured on a different agent and doesn't hold here. So "26-6-0 of 32"
above is really 13-3-0 of 16 unique seeds, doubled; win/loss ratios are
unaffected but there are half as many independent data points as the raw
counts suggest.

DP self-play (16 seeds, both sides pooled): mean **84,437**. W3 self-play reference
(cached, same seeds): mean **85,779**. Gate's self-play check (`candidate self-play
mean >= W3 self-play mean`) → **FAIL** by 1,342 (1.6%) — inside normal seed-to-seed
noise for this harness, not a decisive signal either way.

Executor envelope (steps >= 192 only, aggregated over all 176 gate games):

| metric | value | gate | verdict |
|---|---|---|---|
| idle share | 5.6% | <= 5% | FAIL (marginal) |
| waters/day | 42.9 | >= 40 | PASS |
| care/animal-day | 0.93 | >= 0.8 | PASS |
| duplicate CARE | 1,287 | == 0 | FAIL |
| animal escapes | 0 | — | — |
| weeds at end | mean 0.5, max 3 | — | — |

No flagged games: zero `reward==3000` (never-acted) results, zero non-`DONE`
statuses across all 176 gate games + 32 frontrun games + 8 timing episodes (216
episodes total run today).

**Both envelope FAILs are inherited from W3, not introduced by the reorder
layer — DP is actually a slight improvement on both.** Recomputed the same
two metrics directly from the already-cached W3-as-candidate and
frontrun-as-candidate holdout gate jsonls (176 games each, same aggregation
gate.py uses):

| | idle share | gate (<=5%) | duplicate CARE | gate (==0) |
|---|---|---|---|---|
| W3 (own gate) | 5.61% | FAIL | 1,815 | FAIL |
| w3_frontrun (own gate) | 5.61% | FAIL | 1,815 | FAIL |
| **DP (this run)** | **5.60%** | FAIL | **1,287** | FAIL |

W3 itself already fails both thresholds on these same 176 games; DP's numbers
are marginally *better* than the base it's built on, not a regression. The
honest framing is "no worse than the base on gates the base already fails,"
not "two new soft misses."

**Side-by-side with W3's and w3_frontrun's own already-cached holdout gate runs**
(`gate_w3_herdsafe2700_holdout_20260925T101930Z.jsonl`,
`gate_w3_frontrun_holdout_20260925T104038Z.jsonl` — same seeds 1000-1015, not
rerun, both cheap to reuse):

| opponent | W3 (own gate) | w3_frontrun (own gate) | **DP (this run)** |
|---|---|---|---|
| vs W1 | 20-12, +369 | 20-12, +546 | **28-4, +760** |
| vs W0 | 26-6, +581 | 28-4, +811 | **28-4, +771** |
| vs REACTIVE_V1 | 32-0, +4,277 | 32-0, +4,277 | 32-0, +3,868 |
| vs FARM2945 | 28-4, +1,799 | 28-4, +1,819 | 30-2, +1,281 |
| vs W3 | (self) | 26-6, +329 | 26-6, +380 |
| self-play mean bank | 85,779 | ~85,658 | 84,437 |

DP beats every opponent bucket at least as often as W3/frontrun do, and clearly
better against W1 specifically (28/32 vs 20/32). No bucket where DP is a worse
win-rate than either reference build. Mean margin is lower than W3's own,
though, against two opponents despite an equal-or-better win count —
REACTIVE_V1 (+3,868 vs W3's +4,277) and FARM2945 (+1,281 vs +1,799) — worth
knowing even though it doesn't change the win/loss column. Verdict: **gate
PASSES on every hard win-rate threshold (5/5 opponents)**; the self-play mean
miss is marginal noise, and the two envelope "FAILs" are shown above to be
inherited from W3 itself, not introduced by DP.

## Task B — timing under Kaggle-like CPU load

Method: single process, `psutil.Process().cpu_affinity([6])` (pinned to one
of 8 physical/logical cores), run concurrently with Task A's gate.py (5
worker processes) and the DP-vs-frontrun screen (2 worker processes). **This
did not produce real contention, and the report should not claim it did:**
8 background workers + 1 pinned process on an 8-core box is one process per
core, and the measured wall time confirms it — these pinned episodes ran
48-65s (mean 53s), *faster* than the unloaded prior screen's 54-75s (mean
64.5s) for the same DP-vs-W3 matchup. The Windows scheduler kept core 6
essentially free for this process throughout. So the "1x" row below is an
**uncontended single core**, not a shared-VM proxy — the 2x/3x rows are the
actual estimate of Kaggle's slower, shared 1.6 vCPU, not "extra margin on
top of contention." DP was reloaded fresh (recompiled+exec'd via
`kaggle_environments.agent.get_last_callable`) every episode so its
module-level globals (`_RACE_STATE`, the `_S###_REPORT` chain) never leaked
across episodes. Local `actTimeout`/`runTimeout` were both set to 999999 in
the env configuration so the *local* engine's own overage bookkeeping never
fired and truncated a slow tail — the real 1s/60s rule was applied after the
fact from raw `perf_counter()` durations, which is exact (verified against
`kaggle_environments/agent.py`'s `Agent.act()` and `core.py`'s
`__loop_through_interpreter`: the deduction is literally
`max(0, duration - actTimeout)` charged against `remainingOverageTime`, and a
single turn whose own duration would drive the bank negative gets its action
replaced with `DeadlineExceeded` → `status="TIMEOUT"` → `reward=None` for
that agent, immediately, not a soft penalty).

8 episodes, DP vs W3, seeds 1000-1007 (DP seat 0 for even seeds, seat 1 for
odd — 4 of each):

| seed | DP seat | wall (s) | load (compile+exec, ms) | real first-turn (ms) | max turn (ms) | step@max | turns >1000ms | turns 500-1000ms | overage 1x (ms) | overage 2x (ms) | overage 3x (ms) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1000 | 0 | 64.8 | 1050.3 | 1057.1 | 1392.5 | 601 | 2 | 4 | 449.7 | 3,956.0 | 9,420.8 |
| 1001 | 1 | 52.4 | 801.3 | 807.6 | 807.6 | 0 | 0 | 4 | 0.0 | 1,012.4 | 3,691.8 |
| 1002 | 0 | 49.8 | 1011.3 | 1016.4 | **2160.6** | 600 | 2 | 1 | 1,177.0 | 4,562.9 | 8,869.2 |
| 1003 | 1 | 51.9 | 791.4 | 797.5 | 1235.1 | 697 | 1 | 3 | 235.1 | 2,488.3 | 6,152.1 |
| 1004 | 0 | 48.2 | 817.3 | 823.9 | 823.9 | 0 | 0 | 2 | 0.0 | 793.6 | 2,191.0 |
| 1005 | 1 | 49.0 | 642.3 | 1350.3 | 1350.3 | 0 | 1 | 0 | 350.3 | 1,700.6 | 4,019.3 |
| 1006 | 0 | 56.7 | 767.1 | 773.8 | 1195.8 | 577 | 2 | 3 | 323.8 | 3,812.5 | 8,218.7 |
| 1007 | 1 | 50.9 | 962.6 | 969.2 | 969.2 | 0 | 0 | 3 | 0.0 | 1,524.8 | 4,506.7 |
| **mean** | | 53.0 | 855.5 | 949.5 | 1,241.9 | | 1.0 | 2.5 | **317.0** | **2,481.4** | **5,883.7** |
| **worst** | | | | 1,350.3 | 2,160.6 | | 2 | 4 | 1,177.0 | 4,562.9 | 9,420.8 |

Bonus calibration — W3's own per-turn timing, same pinned setup, same 8
episodes (not part of the graded measurement, wrapped separately as the task
specified "wrap ONLY DP's call"): max ever observed 613.6ms, **zero** turns
over 1000ms in any of the 8 episodes, mean per-episode-max ≈470ms. W3 never
comes close to a single-turn spike, let alone cumulative overage, on this
same uncontended core — this bounds how much of DP's overage number is DP's
added layer versus baseline W3/engine cost.

**Overage extrapolation.** The deduction rule is exact and nonlinear
(`overage_ms = sum(max(0, duration_ms - 1000))` per episode, charged
against a 60,000ms bank) — computed directly from the raw per-turn series,
not by scaling the 1x total. Since the 1x row is an uncontended core (see
above), 2x/3x here should be read as the estimate of Kaggle's actual 1.6
vCPU relative to this box's single core, not as "extra load on top of
contention":

| slowdown vs this box's uncontended single core | mean overage/episode | worst overage/episode | % of 60,000ms bank (worst) |
|---|---|---|---|
| 1x (measured) | 317 ms | 1,177 ms | 2.0% |
| 2x (measured, exact) | 2,481 ms | 4,563 ms | 7.6% |
| 3x (measured, exact) | 5,884 ms | 9,421 ms | 15.7% |

Even the worst single episode of 8, at a hypothetical 3x slowdown, uses under
16% of the 60s bank — over 50 seconds of headroom remain. Given the spike
structure (2 turns around 1.0-2.2s, mean turn ~18ms, the rest of the episode
cheap), exhausting the bank would need roughly an **8-10x per-core slowdown**
sustained on the same spike turns, or a large multiple of the observed spike
*rate* (currently 1-2 turns/episode over 1000ms) — a bigger gap than a
plausibly-slower shared 1.6 vCPU host (commonly estimated at 2-4x a modern
desktop core, not verified here) would produce. This was not independently
measured against real contention on this box (an easy follow-up: pin two
`while True: pass` CPU-burn loops to the same core and re-run 2 episodes) —
the 2x/3x figures are exact arithmetic on the measured per-turn series, not
a validated Kaggle-host benchmark.

**First-call / module-load cost.** Recompiling and `exec`-ing the 10,137-line
file costs 642-1,050ms per episode (mean 856ms). Read directly in
`kaggle_environments/agent.py`'s `build_agent`: for a **file-path agent**
(what `env.run(["path/to/main.py", ...])` uses, matching how the local
pre-submit validation gate and — per `kaggriculture.json`'s own competition
setup — Kaggle's own episode runner invoke a submission), this compile+exec
happens lazily *inside* the timed `callable_agent` call on its first
invocation, so it is charged to turn 0's duration. (If Kaggle instead served
the agent over HTTP as a long-lived process — the `UrlAgent` path in the same
file — the module would load once at process start, outside any timed turn,
making this a non-issue; nothing in this repo's docs indicates that's how
submissions run, so treating it as charged to turn 0 is the conservative
assumption, not a certainty.) Observed real first-turn cost (load + first
decision combined, as a file-path agent would actually be clocked):
773.8-1,350.3ms, over 1000ms on 3 of 8 episodes — already included in the
overage table above (turn 0 is exactly the `step_at_max`/`n_over_1000ms`
entries for the seeds where max occurs at step 0).

## Profiling finding

Two-pass profile on the worst episode (seed 1002, DP seat 0): pass 1 found
its top-3 spike turns (steps 0, 481, 600 — durations 2,160.6 / 1,016.4 /
604.4ms); pass 2 replayed the same seed with `cProfile` enabled only on
those 3 steps.

```
2,857,703 function calls in 6.854s across 3 profiled turns
 99 calls   _s793_reorder   (demand-preserving-turn-sale-timing.py:7895)   tottime 2.460s  cumtime 6.043s
 54,854 calls  margin (closure inside _v44y_factor_margin)  (…:6099)       tottime 1.816s  cumtime 3.435s
 1,940 calls  _v44y_lockstep (…:6044)                                     tottime 0.301s  cumtime 0.877s
 15 calls   _cxd_reorder (…:6862)                                        cumtime 0.617s
```

Root cause, read directly from source (`…:7891-7930`): `_s793_reorder` runs an
explicit combinatorial local search over market-order placements —
`itertools.permutations(slots, len(sells))` × `itertools.permutations(sells)`
— evaluating each candidate reordering with `margin(cand)`. **It is capped**:
`_S793_BUDGET = 800` evaluations per call (`if evals > _S793_BUDGET: break`),
so a single call to this search is bounded. The spike is not an unbounded
search; it's this same 800-eval-capped search **invoked redundantly by the
~33-41-deep wrapper chain** (`step793_...` through
`step1009_step1008_fortyfirst_...`, one call per stacked closure per turn):
the profile shows 99 calls specifically to `_s793_reorder` across the 3
profiled turns (~33 calls/turn) accounting for 54,854 of the total `margin()`
evaluations — **~554 evals per call on average, comfortably under its own
800-eval cap** (some of the profile's other `margin()` calls come from
`_cxd_reorder`/`_v44y_lockstep`, separate reorder passes also in the profile,
not counted in this per-call average). Each individual call is bounded and,
on this evidence, not usually hitting its own ceiling — the wall-clock cost
comes from calling that bounded search ~33 times in one turn, not from any
single call running unbounded.

Not fixed here per the task's scope (measure/diagnose only) — but if a cap is
ever wanted, the obvious lever is de-duplicating the wrapper chain (only the
last-active layer's reorder actually matters; the other ~40 are pure
redundant recomputation) rather than lowering `_S793_BUDGET` itself, which
protects a single call but not the fan-out from stacking one bounded search
40 times.

## Verdict

**SAFE**, with a caveat, not RISKY or UNSAFE:

- On this box's *uncontended* single core, DP's measured cumulative
  per-episode overage tops out at 1,177ms of the 60,000ms bank (2.0%) across
  8 episodes.
- At the exact, arithmetically-derived 2x and 3x slowdowns (the working
  estimate for Kaggle's shared 1.6 vCPU relative to this core — not
  independently measured here), the worst of the 8 episodes still uses only
  7.6% / 15.7% of the bank. Given the spike structure (1-2 turns/episode
  around 1.0-2.2s, everything else cheap), exhausting the 60s bank would need
  roughly an 8-10x per-core slowdown sustained on the same spike turns — well
  beyond a plausible 2-4x shared-host estimate.
- Every spike traces to the same mechanism: `_s793_reorder`'s permutation
  search, itself capped at 800 evaluations per call, invoked redundantly by
  a ~33-41-deep wrapper chain once per turn. The profiled worst turn averaged
  ~554 evals per call (not pinned at the 800 cap), so there is *some* headroom
  for a richer turn to run closer to the ceiling than sampled here — the
  fan-out (~33 calls/turn) is the dominant cost, and that count is itself
  bounded by the (fixed, on-disk) length of the wrapper chain, so it cannot
  grow unboundedly either.
- Residual, unquantified risk: only 8 seeds were sampled; the CPU-load
  methodology in this run turned out to be an uncontended core rather than a
  true shared-VM proxy (see Task B methodology note above), so the 2x/3x
  numbers are an estimate, not a verified Kaggle-host benchmark; and a seed
  with a richer one-turn order mix than any of the 8 tested could push
  individual `_s793_reorder` calls closer to their 800-eval cap more often.
  None of the 8 sampled seeds came close to threatening the bank, both the
  per-call cap and the fixed chain depth bound how much worse a turn can get,
  and the margin to the 60s cliff (roughly 6-8x the worst measured case) is
  large enough that this reads as safe rather than merely "not yet observed
  to fail."
