# WANTAM v2: rival-aware objective and a value-aware scheduler, 28 September 2026

Stop-rule verdict up front: **neither build clears the upload bar.** Recommend the final pair
stays Peter's W3 + demand-preserving and W6, per the stop rule in the brief. Nothing was
uploaded; `washamba_agent` is the last callable in every build checked (self-play seed 0
DONE/DONE, max turn under 500 ms, throughout).

## Results table (match.py, 16 seeds 900-915, both seats = 32 games, vs W3)

| build | W-L-T | mean margin |
|---|---|---|
| Step 1 only (rival-aware dawn objective, Peter's executor unchanged) | 1-31-0 | -15,811 |
| Step 2, first pass (+ value-aware executor) | 0-32-0 | -31,958 |
| Step 2, after the trap-door-floor fix (below) | 0-32-0 | -31,516 |

All three are well short of the 20-of-32-with-positive-margin bar. Because Step 2 was already
badly behind on W3, it was not run against W6 as well — that would only have re-confirmed
failure at further compute cost, which the RAM/worker constraints argue against spending.

## Step 1: margin objective

`WantamController._simulate` now optionally returns the rival's revenue under the same shared
price path (`want_rival=True`), and both scoring sites in `_dawn` (the per-animal starve
decision, the greedy crop-planting loop) score `(our revenue delta) - (rival revenue delta)`
instead of our revenue alone. Mechanically this does what the brief predicted: starving is
rarer (keeping an animal fed also suppresses the rival's price on the same product) and crops
the rival also sells score higher. Head-to-head, though, the result got *worse* than the
existing baseline, not better (PROGRESS_2026-09-28.md's day-14-harness numbers, which measure
our own bank against a W3-continuing reference rather than a live margin, were -3,563/-2,639;
this is a different, harsher metric — a real match against a reactive rival — and the two
aren't comparable on the same footing, but the live number is the one the ladder actually
scores). **Diagnosis:** Peter's executor, inherited unchanged for this test, was already the
identified bottleneck before Step 1 (SONNET_BUILD_0928.md's own "what we measured" section);
fixing the plan's objective without fixing execution didn't have room to show up in the score.

## Step 2: value-aware deadline scheduler

Added `WantamScoreExec` (`wantam.py`), extending `WantamExec` (the existing routing/batching
executor from Stage 1). Kept `WantamExec`'s routing and batching machinery unchanged — arrival
batching, herder grouping, route-horizon extension by density — and replaced only the *value*
each task carries. `WB_Controller._tasks` still decides which tasks exist (eligibility); a new
`_tasks` override recomputes each task's weight as
`(ValueProtected + ExpectedMarginalRevenue + ScarcityPremium) * Urgency`, using the dawn plan's
own forecasts (`plan['crop_rate']` per crop, `plan['animal_keep']` per animal, both new this
session) instead of Peter's fixed `WB_W_*` constants. The division by `Travel + Actions` needed
no new code: `WantamExec`'s existing `dens = val / (d + na)` already does exactly that.

**Two real bugs found and fixed along the way, for the record:**
1. `build_wantam.py` used to truncate `wantam.py` before `class WantamExec` entirely, so no
   executor built this way was ever the one PROGRESS.md's "batching executor v1" row actually
   tested — fixed by making the controller class selectable (`WA_CTRL_CLASS` env var).
2. A `from price_model import WB_MARKET_PARAMS` at the top of `wantam.py` works when the module
   is imported standalone, but silently becomes a real (and here, missing) cross-file import
   once concatenated into a single self-contained submission by `build_wantam.py` — the
   concatenation makes the *name* available as a global, but Python's `import` statement still
   tries to locate an actual separate module file. Fixed by hardcoding the nine base prices as a
   local dict instead of importing them.

**One bug found, partially fixed, not resolved:** `WantamExec._execute`'s late-hour trap-door
preemption (inherited unchanged) compares a task's weight against Peter's fixed constants
(`WB_W_FEED + 20`, `WB_W_WATER_URGENT`) to decide whether to steal a task for the nearest unit.
The new $-scaled scores don't share that constant's scale, so real trap doors often never
crossed it. Floored trap-door weights above those constants explicitly — this measurably
improved one gate (`escapes_unintended` dropped on 2 of 4 sample seeds) but left the actual
money result unchanged (-31,958 to -31,516, no meaningful difference) and one seed got *worse*
(5 unintended escapes on seed 903, up from 0). **This means the floor fix treated a symptom, not
the cause.** Gate detail on 4 seeds (900-903), before vs after the floor fix, is in
`gates.py`'s stdout captured this session; wheat losses to weeds stayed in the 6-25/game range
both times, essentially unmoved.

**What this means, as inference:** the real fault is upstream of the preemption pass — most
likely that `_extend`'s density-based route-building, which runs *before* a task ever becomes
urgent, now systematically under-values cheap-product WATER/FEED tasks relative to their old
fixed weights, so routes fill up with higher-value work and the trap door only gets a chance to
fire once it's already too late in the day to reach every animal/tile. WANTAM_SPEC.md's own
Layer 1 design (mandatory load reserved as slack *before* productive work is scheduled) is
built for exactly this failure mode; this session's `_tasks`-only patch never touched capacity
reservation, which is likely why it didn't fix it. A real fix needs the mandatory-load reservation
from Layer 1, not another tweak to Layer 2's per-task weights.

## Step 3: not attempted

Gated explicitly on a Step 1 or Step 2 build clearing the bar at handover 336. Neither did, so
the day-8 handover rebuild and the demand-preserving-base swap were not built or tested — doing
so on top of a losing base would not be informative, and the brief's own gate ordering agrees.

## Files
`wantam.py` (Step 1 + Step 2 source), `build_wantam.py` (now takes `WA_CTRL_CLASS`),
`wantam_score_mod.py` (re-export for `gates.py`/`h14.py`), `wantam_step1.py`, `wantam_step2.py`
(built candidates), `step1_vs_w3.log`, `step2_vs_w3.log`, `step2_vs_w3_fixed.log` (match.py raw
output).

## Labels
- All W-L-T/margin numbers, the two build-script bugs, and the gate numbers: **MEASURED**
  (n=32 games per match row; n=4 seeds for the gate comparison).
- The root-cause diagnosis for the unresolved crop-loss/escape regression and the Layer-1
  recommendation: **INFERENCE** — plausible and specific, but not verified by a fix that
  actually restores the money.
