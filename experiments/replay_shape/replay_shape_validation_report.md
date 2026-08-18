# Track C reference opponent — structural validation report

Agent under test: `experiments/replay_shape_agent.py`. Instrumentation:
`experiments/replay_shape_instrumentation.py`. Spec: `experiments/replay_shape_spec.md`.
Audit: `experiments/track_c_replay_audit.md`.

Method: `trace_episode()` runs a real 720-turn episode (`replay_shape_agent.py`
vs the built-in `pass` opponent) and records per-day state; `run_validation_report()`
checks each structural target from the spec, tagged HARD or SOFT as the spec
tags them. Run on 3 seeds (0, 1, 2) — `pass` reproduces deterministically per
CLAUDE.md, so these are exact repeats of the same agent logic under different
weed/shop-unlock draws, not independent confirmations of a stochastic strategy.

## Results (3 seeds)

| seed | final bank | land | crew (peak) | animals (final) | stranded |
|---|---|---|---|---|---|
| 0 | $33,965 | 75 | 15 | 6 COW + 3 SHEEP = 9 | 0 |
| 1 | $19,675 | 75 | 15 | 5 COW + 3 SHEEP = 8 | 0 |
| 2 | $33,882 | 75 | 15 | 5 COW + 3 SHEEP = 8 | 0 |

## Per-target verdict

**1. Farm scale — HARD — ACHIEVED.** All 3 seeds reach exactly 75 tiles
(both `BUY_LAND` orders fire). Timing is later than the spec's target
window, though: land purchases land around day 10–11 for both quadrants
back-to-back, not ~day 6–7 and ~11 as separate events. The day-11 minimum
for the second purchase is the binding constraint on the first, because
`decide_land_orders` requires the cash for it too, and cash doesn't clear
`$2,000` until the day-6 gate has already passed. Not scored as a failure
(the HARD target is the tile count, not the timing — spec §1 tags timing
SOFT), but worth flagging since it compresses ~10 days of crew/production
growth into a much narrower window than a real ladder agent likely gets.

**2. Crew scale — SOFT — ACHIEVED.** All 3 seeds hit the top of the target
range (15) by day 20 and hold it. Not a partial result — every seed reaches
the exact ceiling.

**3. Animal survival — HARD (behavioural) — ACHIEVED.** 0 stranded animals
in the shed at season end, all 3 seeds. The two bugs that caused stranding
(wrong structure-capacity math, cash gate blocking free housing) are fixed
and stayed fixed across seeds.

**3b. Animal scale — SOFT — ACHIEVED (low end).** 8–9 total, split 5–6
COW : 3 SHEEP, matching the spec's evidenced ratio exactly. Two of three
seeds land at 8 rather than 9 — inside the range, at its floor.

**4. Production — not a named target, checked as a diagnostic.** Harvest
actions accumulate steadily all season (0 → ~190 cumulative by day 29 in
the seed-0 trace), no stall. Planted-tile count fluctuates in the teens to
low 40s out of 75 owned — well under full utilization, but this wasn't a
named priority-1–4 target and the agent is deliberately not tuned on it.

**5. Selling — SOFT — shape achieved, volume not diagnosed as sufficient.**
`validate_selling_throughput` passes on all 3 seeds: no orders before day
10, then a sustained ramp with no day-22 liquidation cliff (max stays ≥1
order/day through day 29). But the absolute numbers are small — mean
~1.5 orders/day from day 10 on, peaking at 4/day — against a 75-tile,
15-crew farm. The check only validates *shape* (ramp direction, no cliff),
which is all the spec asked for; it does not claim the *volume* is
sufficient, and the bank result below shows it likely isn't.

**6. Final bank ($90k–100k) — NOT MET, and also below the corrected
$53k–$126k evidenced range** on all 3 seeds ($19.7k–$34k). This was
flagged in the audit as a narrow, likely-unrepresentative headline number
to begin with; the wider evidenced range is the fairer bar, and the agent
still misses its floor by 36–63%.

## Where it failed, and the diagnosed bottleneck

Per instruction, no parameters were tuned before diagnosing. The day-by-day
trace (seed 0) shows cash repeatedly collapsing to single digits
(`$3, $8, $10`) in the exact window crew sits at 14–15, despite steady
revenue arriving the same days:

```
day  cash  land crew planted harv_cum sell_ord units_sold revenue
 14   1301   75   15      43       25        0          0        0
 15    127   75   14      40       37        0          0        0
 16      3   75   11      35       41        1          8      280
 17      8   75    6      26       52        1          1       35
 18   1073   75   15      35       54        2         14     3036
 19     10   75   14      32       57        1          1       37
```

Cause, confirmed against the engine source
(`.venv/.../kaggriculture/kaggriculture.py:690-699`): hire cost is
`mult * fib(n_already_hired_today)`, `fib(0..14) = 1,1,2,3,5,8,13,21,34,55,
89,144,233,377,610`, and **hands are wiped every night and must be rebought
from `fib(0)` each morning** (CLAUDE.md, confirmed in the engine loop).
`decide_hire_orders` has no cost-awareness at all — it just hires toward
`crew_target_for(owned_tiles)`, capped at `MAX_HANDS_TARGET=15`, gated only
by a flat `$20` floor. Rebuilding a 15-hand crew from scratch every single
morning costs `Σ_{k=0}^{14} fib(k) = $1,596/day`. Over the ~19 days the
agent holds 14–15 hands (day 10–29), that's up to **~$28k** in hiring alone
— against $76,968 in gross revenue across all 3 pieces summed for seed 0.
That one line item is large enough by itself to fully explain the gap
between gross revenue and the $33,965 final bank, without needing to
invoke selling volume, crop mix, or anything else as a second cause.

This is the same mechanic CLAUDE.md's own baseline analysis already
flags — "cheap for the first hire of the day, expensive for the third+"
— but the existing `main.py` baseline never tests it at this crew size:
its documented ROI measurement was for **4 hands** (`fib(0..3)` sums to
$7/day, ~$210/season), a completely different regime on the same curve.
The spec's 12–15-hand target, taken at face value without re-deriving the
hire economics at that scale, walks the agent onto the expensive tail of
a curve that's cheap by design only near its start. This reconciles with,
and sharpens, Track A's own finding in the audit that a denser crew was a
measured loss (`WORK_TILES_PER_HAND=4` cost 1,300–3,400) — that test point
never even reached 15 hands, and this data suggests the ceiling is lower
still once daily-refresh Fibonacci cost is priced in rather than assumed
free.

**Selling throughput is a secondary, unconfirmed candidate**, not ruled
out but not isolated either: 1.5–4 orders/day is thin for this scale, but
without first controlling for the hiring drain it's not possible to tell
whether low sell volume is a second independent bottleneck (not enough
production reaching the shed) or a downstream symptom of the same cash
starvation (e.g., fewer hands free to walk to sellable state, less produce
because animals/crew were cash-starved). This should be re-checked only
*after* the hiring-cost issue is addressed, per the "diagnose, don't
tune" instruction — re-running this exact instrumentation on a
crew-cost-aware variant would isolate it cleanly.

## Explicitly not done

No parameters were changed in `replay_shape_agent.py` as part of this
report. `main.py` is untouched (`git diff origin/main -- main.py` is
empty). Nothing was merged or submitted.
