# Forward-looking sell policy, v0: one-step sell-now-vs-hold lookahead

Follow-up to `experiments/sell_threshold_audit_report.md`, which found
that no flat `SELL_PRICE_THRESHOLDS` constant can distinguish "price is
high and about to fall" from "price is low and about to recover,"
because a constant carries no forecast. This experiment replaces the
constant with a genuine forecast, built entirely from already-verified
`pricing_v1.py` functions. `main.py` and `pricing.py` are untouched
throughout (`git diff --stat -- main.py pricing.py` empty at every
step). Nothing merged, nothing submitted.

## 1. Hypothesis

Bidirectional, must be able to fail: replacing `current_price >
SELL_PRICE_THRESHOLD` with a one-step sell-now-vs-hold-one-turn value
comparison produces better selling decisions than the flat threshold. It
might not - `pricing.py`'s mechanics can only project *known* effects
forward (our own pipeline supply, town demand), not genuinely unknown
future information, and at a one-*turn* horizon those known effects are
narrow. Both outcomes are informative; see section 10 for which one this
turned out to be.

## 2. Baseline policy

Unmodified `main.py`: `should_sell(product, quantity, market_state)` -
`True` iff current spot price clears a fixed `SELL_PRICE_THRESHOLDS[product]`
constant, no forecast, no notion of what happens next turn.

## 3. Candidate policy

`experiments/candidates/forward_sell_policy_v0.py`. `decide_market_actions`'s
main sell loop is copied verbatim from `main.py`, with exactly one
substitution: `should_sell(...)` is replaced by a call to
`pricing_v1.estimate_sell_or_hold_decision(...)` (new function, section 7
of `pricing_v1.py` - the research-layer extension the task authorized
when the existing `compare_immediate_vs_delayed_selling` proved
insufficient on its own). Everything else - the `liquidating` bypass
(untouched: `day >= LIQUIDATION_START_DAY` still means "sell regardless
of price," unmodified), the WHEAT-reserve and FERTILIZER exclusions, the
`SHED_FORCE_SELL_THRESHOLD` overflow loop, `choose_crop`/`BUY_SEED`, the
fertilizer buy logic, `MAX_HANDS_PER_DAY`, land, animals, labor,
opponent modelling - is character-for-character the same as `main.py`.
Verified, not just claimed:
`tests/test_forward_sell_policy_v0.py::test_liquidation_bypasses_the_forward_decision_entirely`
asserts the forward decision function is never even *called* on a
liquidating turn.

## 4. Mathematical / economic definition of SELL vs HOLD

For each product with `sell_quantity > 0` this turn (pre-liquidation):

1. **Size the candidate sale to `PRICE_FLOOR`**
   (`recommend_sell_quantity(item, current_inventory, shed_quantity,
   min_acceptable_price=PRICE_FLOOR, max_per_turn=cap)`) - "how much
   would we sell this turn if we decided to sell at all," the same
   quantity `LIQUIDATION_START_DAY` already uses. Both branches below
   compare selling *this exact quantity* now vs. later - never a sizing
   question riding along with the timing question.
2. **Compare** (`pricing_v1.compare_immediate_vs_delayed_selling`, hold
   horizon = 1 turn):
   - `revenue_now` = realised revenue selling `quantity` units this
     instant (`price_path_for_sale`, walking the engine's real per-unit
     decay).
   - `revenue_delayed` = realised revenue selling the *same* `quantity`
     units one turn later, after our own pipeline supply (pinned at 0 -
     see assumptions) and one turn of town demand (`apply_town_demand`)
     have had their effect on inventory.
   - `opportunity_cost_of_holding = max(0, revenue_now - revenue_delayed)`.
3. **Decide:**
   - if `inventory_pressure(shed_quantity, our_pipeline_supply=0,
     remaining_days, max_per_turn) >= 1` (structurally overcommitted -
     even selling flat-out every remaining day at the cap wouldn't clear
     the position in time): **force SELL**, regardless of the
     comparison. Not a new number - the same `>= 1` break-even
     `recommend_sell_cadence` (already in `pricing_v1.py`) uses.
   - else if `revenue_delayed > revenue_now` (`delay_is_better`):
     **HOLD**.
   - else (includes exact ties): **SELL**.
4. `season_urgency(day)` is computed and logged on every decision but
   **not** used to bias the comparison with a blending coefficient - see
   section 5 for why, and section 8's seasonality measurement for what
   that choice actually produced.

No new price math anywhere in this chain - every dollar figure comes
from `pricing.py`'s own verified `market_price`/`price_path_for_sale`/
`apply_town_demand`, reached through `pricing_v1.py` functions that
already had their own test coverage before this experiment.

## 5. Assumptions

- **`our_pipeline_supply` is pinned at 0**, not threaded from
  `pricing_v1.estimate_own_pipeline`. That function operates at *day*
  granularity (yield accrual relative to a horizon day); this
  experiment's hold horizon is a single *turn*. Feeding a day-level
  estimate into a turn-level window would be a unit mismatch, not a
  genuine signal - deferred, not silently guessed around.
- **Opponent pipeline supply is entirely out of scope**, per the prior
  experiment's explicit closing instruction. Not pinned at 0 as an
  isolation guard (like the earlier opponent-aware candidates did) -
  there is no parameter for it in this candidate's call at all.
- **`hold_horizon_turns = 1`** is the literal spec ("evaluate: 1. HOLD
  for one turn"), not tuned. Section 8 shows exactly what this choice
  does and doesn't capture in `pricing.py`'s model - it matters more
  than it might look.
- **Ties resolve to SELL** (`delay_is_better` requires strict `>`).
  Stated as a real modelling choice, not hidden - see section 8, where
  it turns out to be the single largest driver of the candidate's
  behaviour.

## 6. Tests

`tests/test_pricing_v1.py::TestEstimateSellOrHoldDecision` (10 cases):
key structure, zero-shed edge case, the tie-resolves-to-sell property
(directly constructed via a `start_step` where no demand-tick interval
divides the hold window), a demand-tick case that genuinely favours
holding, the `inventory_pressure >= 1` hard override (mocked comparison
proves the override wins even when the forecast says wait), opportunity-
cost sign checks, urgency/pressure computed-not-hardcoded, and quantity
capping.

`tests/test_forward_sell_policy_v0.py` (7 cases): the wiring - produces
a SELL order when the decision prefers sell, produces none when it
prefers hold (mocked), **liquidation never even calls the forward
decision** (the load-bearing isolation property for "do not replace
liquidation"), WHEAT reserve and FERTILIZER exclusions still respected,
`MAX_SELL_PER_TURN` still capped, one log entry per evaluated product.

Full suite: **262/262 pass** (245 pre-existing + 10 + 7). No test-order
pollution issues this time (`base.decide_market_actions` is still a
shared, monkeypatched global across multiple candidate files, so
`TestWiring.setUp` re-pins this candidate's patch before each test, the
same pattern the two prior candidate test files already established).

## 7. Behavioral diagnostics (the task's "most important diagnostic")

`experiments/forward_sell_policy_decision_diag.py`, 12 self-play seeds,
653 logged decisions (both seats combined):

| | count |
|---|---|
| total decisions | 653 |
| SELL (`sell_now_beats_hold`) | 393 (60.2%) |
| HOLD (`hold_beats_sell_now`) | 260 (39.8%) |
| forced SELL by `inventory_pressure >= 1` | **0** |

**The single most important structural finding: among the 260 genuine
(non-tie) differences, HOLD wins 260/260 - 100%.** This is not evidence
that holding is empirically superior; it is close to a mathematical
certainty of how the model is configured here. With `our_pipeline_supply`
pinned at 0, the *only* thing that can make `revenue_delayed` differ
from `revenue_now` in a single turn is `apply_town_demand`'s recovery
effect - and recovery, by construction, can only ever move price back
*toward* the base level, never away from it. There is no modelled
mechanism in this configuration by which "sell now" could ever win on a
genuine (non-tie) margin - it only ever wins via the tie-break rule. The
remaining 393 SELL decisions (60.2% of the total) are therefore **all**
tie-breaks: cases where nothing in the model distinguished the two
turns at all (no demand tick fell inside the one-turn window - true on
most turns, since `shop_interval=4` and `center_interval=24` fire on a
minority of individual turn boundaries).

**Mean |advantage| when a genuine difference exists: $9.54** - real but
small, consistent with recovering from one town-demand tick, not a
structural repricing.

**Per product** (sell rate = share of decisions where SELL was chosen):

| product | n | sell rate | mean sell quantity |
|---|---|---|---|
| WOOL | 288 | 66.3% | 4.27 |
| MELON | 127 | 63.0% | 11.51 |
| CARROT | 45 | 55.6% | 4.42 |
| MILK | 144 | 50.0% | 5.94 |
| STRAWBERRY | 47 | 48.9% | 5.13 |
| WHEAT | 2 | 100.0% | 3.50 |

Every product holds a meaningful fraction of the time (33-51%) - this is
**not** a degenerate "always sell" policy, contrary to what the tie-break
analysis alone might suggest; the ~40% genuine-difference rate is doing
real, if narrow, work.

**Seasonality** (day-bucketed, pre-liquidation only):

| day range | n | sell rate | mean urgency | mean pressure |
|---|---|---|---|---|
| 5-9 | 168 | 57.1% | 0.271 | 0.045 |
| 10-14 | 242 | 65.7% | 0.418 | 0.085 |
| 15-19 | 243 | 56.8% | 0.586 | 0.071 |

**The policy does NOT naturally become more aggressive as liquidation
approaches - by design, and the data confirms exactly that design's
consequence.** `season_urgency` was deliberately left out of the
decision rule (section 4, point 4) rather than blended in with an
unjustified weight, and sell rate here tracks which products are being
evaluated at each day range (season-specific crop maturity timing) far
more than it tracks urgency itself - the 15-19 bucket has the *highest*
mean urgency (0.586) and a *lower* sell rate than the 10-14 bucket. This
directly answers the task's seasonality question: **no, the forward
policy does not naturally ramp up aggressiveness with urgency in this
configuration** - it would need urgency (or the `inventory_pressure`
override, which never even fired here - `pressure` stayed far below 1 in
every bucket) wired into the comparison to do that, which was
deliberately not done to avoid an unjustified coefficient. The existing
`LIQUIDATION_START_DAY` hard cliff is still what actually produces
season-end aggressiveness, exactly as before - untouched, as instructed.

**A second, distinct behavioral driver, found while reading the
sell-event data (section 9), not anticipated going in:** because
quantity is always sized down to `PRICE_FLOOR` (step 1 of section 4)
rather than to a threshold, **whenever the candidate does sell, it sells
a deeper order than baseline would at the same spot price** - baseline's
`recommend_sell_quantity` stops walking once price would drop under
`SELL_PRICE_THRESHOLDS[product]`; this candidate's only floor is $1.
CARROT is the clearest case: mean units moved per self-play season
**jumps from 4.8 (baseline) to 20.2 (candidate)**, a ~4x increase, at a
similar sell-event count (1.9 vs 7.0) - both more frequent sales *and*
each one going deeper. This means the measured economic effect below is
a composite of two changes, not one: the timing gate, and how far each
authorized sale is walked. Worth separating in any follow-up.

## 8. Seeded evaluation (12 seeds where run, matching this repo's
   standard workflow)

| harness | result |
|---|---|
| self-play, candidate vs itself | mean **57,946**, stdev 9,513, median 61,322, range 41,948-67,720 |
| self-play, baseline (`main.py`) | mean 61,303, stdev 11,626, median 65,058, range 39,554-75,064 |
| head-to-head vs `main.py`, 24 matches | **+1,209 mean, 16/24 wins** |
| paired vs `starter`, 12 seeds | **-1,001 mean, 4/12 wins, sd=7,713, t=-0.45** |

Per-seed paired deltas vs `starter` (candidate − baseline): -3396,
-6145, **+13831**, -9403, **+12663**, -1783, -4315, +575, +1713, -71,
-11648, -4038. **The spread here (sd 7,713) is far larger than any
threshold-only variant produced** (the stricter/permissive candidates in
`sell_threshold_audit_report.md` had paired sd around 0-2) - direct,
independent confirmation that this candidate makes substantively
different decisions, not a marginal nudge. Some seeds swing sharply
positive, most swing negative or flat; the mean is negative but the
t-statistic (-0.45) shows this is not distinguishable from noise at 12
seeds either way.

## 9. Comparison to baseline

**The three harnesses disagree, and not in the pattern this repo has
learned to distrust before.** `CLAUDE.md`'s standing caution is that
head-to-head can "bless a change that only works because the opponent is
a mirror of us" when self-play *also* shows a win. Here it's the
opposite shape: **self-play shows a clear loss** (-3,357 mean, tighter
stdev too - -2,113), **head-to-head shows a clear win** (+1,209, 16/24),
and **paired-vs-`starter` is negative but not significant, with unusually
high variance**. A change that helps against an unmodified `main.py`
opponent but hurts when both sides run the modified policy is not the
familiar "flatters itself" failure mode - it suggests the candidate's
behaviour interacts with *what the opponent does*, which the behavioral
diagnostics support: this policy sells deeper, more often, on ties; two
identical copies of it selling deeper into the same shared order book
plausibly crowd each other's prices down in self-play in a way a single
copy against `main.py`'s more conservative, threshold-gated selling does
not.

## 10. Failure modes

- **The value model cannot distinguish "sell now" on a genuine margin
  from a tie-break** (section 7) - 100% of its non-trivial comparisons
  favour holding, by construction, because no supply-side information is
  in scope at this horizon. The "forecast" driving 60% of SELL decisions
  is not a forecast at all; it's a default.
- **Quantity sizing and the sell/hold gate are coupled** (section 7) -
  a product-level result mixing "sold more often" with "sold deeper
  each time it did" cannot cleanly attribute the score effect to the
  timing decision this experiment was supposed to isolate.
- **`inventory_pressure`'s hard override never fired once** in 653
  logged decisions across 12 seeds - either the crew/production balance
  in this repo's current build never actually produces a structurally
  overcommitted position pre-liquidation (plausible, given
  `sell_threshold_audit_report.md`'s finding that most products barely
  build up shed inventory before day 19 anyway), or the override's
  `>= 1` threshold is simply never reached at this decision cadence.
  Either way, it contributed nothing measurable here.
- **High outcome variance, seed-dependent in both directions** (section
  8) - not a stable, predictable improvement or regression; a
  Bradley-Terry-style tournament (per `CLAUDE.md`'s own documented
  concern about self-play stdev) would likely punish this kind of
  variance regardless of its mean.
- **Self-play and head-to-head disagree in direction**, which this
  report's own evidence standard (read multiple harnesses before
  trusting one) treats as inconclusive, not as "head-to-head wins,
  ship it."

## 11. Recommendation

**D - technically works but needs a better value model.** Not A: the
evidence is inconsistent across harnesses, and self-play (the harness
this repo's own documentation treats as "the number that predicts the
ladder") shows a loss. Not B: the diagnostics prove this is not "no
measurable difference" - decision-log analysis, sell-event volume, and
the unusually high paired-comparison variance all show a real,
substantial behavioural change. Not C: no product-level pattern of
"helps here, hurts there" emerged cleanly enough to support it - the
harness-level disagreement dominates. Not E: there is ample evidence,
it just doesn't converge on a clean verdict.

**What "a better value model" concretely means, grounded in what was
actually found here, not a general wish list:**

1. **Give the comparison something to weigh besides a demand-tick
   coin-flip.** Own pipeline supply at a *day*-scale horizon (not
   turn-scale) would let `revenue_delayed` reflect actual incoming
   competition from our own harvest, the one channel this v0 explicitly
   deferred rather than guessed around (section 5). This is the most
   promising, most directly implied next step, not a new idea invented
   here.
2. **Decouple quantity sizing from the sell/hold gate** - size to a
   principled floor (e.g. the current threshold, or a
   `recommend_sell_cadence`-style pressure/urgency-adjusted floor)
   rather than always walking to `PRICE_FLOOR`, so a future evaluation
   measures the timing decision in isolation.
3. **Investigate why self-play and head-to-head disagree** before
   trusting either in isolation - itself informative regardless of what
   ships next, since it's a genuinely new disagreement shape for this
   codebase's experiment history.

No implementation follows automatically from this report. `main.py` and
`pricing.py` are untouched; nothing merged; nothing submitted.
