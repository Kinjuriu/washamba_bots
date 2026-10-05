# Forward-looking sell policy, v1.1: multi-day own-supply forecast

Follow-up to `experiments/forward_sell_policy_v0_report.md`, which
identified two concrete problems: (1) a one-turn horizon mostly captured
town-demand recovery, never our own future harvest (pinned at 0 - a
day-vs-turn unit mismatch), and (2) quantity was sized to `PRICE_FLOOR`
regardless of the sell/hold decision, coupling timing with sizing. v1.1
fixes exactly these two things and nothing else. `main.py` and
`pricing.py` are untouched throughout (`git diff --stat -- main.py
pricing.py` empty at every step). Nothing merged, nothing submitted -
this is the final pricing report before today's submission decision, per
the task's own instruction not to start another experiment after this.

## 1. Hypothesis

Bidirectional, must be able to fail: given the *exact* quantity
`main.py` would already sell this turn, does a genuine multi-day
own-supply forecast (own harvest timing over the next 3-5 days,
`pricing_v1.estimate_own_pipeline`, already validated) improve the
decision of *when* to sell it, versus selling immediately? Section 8
answers this directly, and decisively - just not in the direction
hoped for.

## 2. Baseline policy

Unmodified `main.py`: `should_sell` (fixed threshold) sizes via
`recommend_sell_quantity(..., min_acceptable_price=SELL_PRICE_THRESHOLDS[product])`.

## 3. Candidate policy

`experiments/candidates/forward_sell_policy_v1_1.py`. The sell loop is
copied verbatim from `main.py`, with one substitution, in two steps:

1. **Quantity, unchanged formula.** `amount =
   recommend_sell_quantity(product, inventory, sell_quantity,
   min_acceptable_price=SELL_PRICE_THRESHOLDS.get(product,
   DEFAULT_SELL_THRESHOLD), max_per_turn=cap)` - character-for-character
   what `main.py` already computes once `should_sell` says yes. This
   line alone is mathematically equivalent to `should_sell`'s own
   `price >= threshold` test (`recommend_sell_quantity`'s walk stops at
   the first unit quoting under the floor), so no separate `should_sell`
   call is made or needed.
2. **Decision, forward-looking.** If `amount > 0`:
   `pricing_v1.estimate_multi_day_sell_or_hold_decision(product,
   inventory, quantity=amount, day, remaining_days,
   tiles=farm["tiles"], liquidation_start_day=LIQUIDATION_START_DAY,
   ...)` decides SELL (append `["SELL", product, amount]` - the exact
   `amount` from step 1) or HOLD (append nothing this turn).

Liquidation (`day >= LIQUIDATION_START_DAY`) is untouched - same bypass,
same `PRICE_FLOOR`-based quantity, and the forward function is never
even called on a liquidating turn (test-verified). Everything else -
`SHED_FORCE_SELL_THRESHOLD`, `choose_crop`/`BUY_SEED`, FERTILIZER logic,
`MAX_HANDS_PER_DAY`, land, animals, labor, opponent modelling - is
character-for-character `main.py`.

## 4. Mathematical / economic definition of SELL vs HOLD

New function, `pricing_v1.estimate_multi_day_sell_or_hold_decision`
(section 8 of `pricing_v1.py`), composed entirely from already-verified
building blocks - no new price math:

- **Horizon:** `min(DEFAULT_HORIZON_DAYS=4, remaining_days,
  liquidation_start_day - 1 - day)`. Chosen from game mechanics, not
  swept against results (see section 5).
- **For each candidate day `day+1 .. day+horizon`:**
  `our_pipeline_supply = estimate_own_pipeline(tiles, day,
  future_day)[item]` (the same function `choose_crop`'s own forward-
  pricing already uses), then `compare_immediate_vs_delayed_selling(item,
  current_inventory, quantity, day, delay_turns=(offset)*24,
  our_pipeline_supply=..., opponent_pipeline_supply=0, ...)`.
- **Best day** = the one with the highest `revenue_delayed`.
- **HOLD** only if `best_revenue_delayed > revenue_now` (strict, no
  added margin - ties resolve to SELL, same convention v0 established;
  see section 5 for why no coefficient was added here).
- `opportunity_cost_of_holding = max(0, revenue_now - best_revenue_delayed)`.

## 5. Assumptions

- **Animal products (WOOL/MILK/EGG) get `our_pipeline_supply = 0` for
  the entire horizon.** `estimate_own_pipeline` only covers `PLANT`
  tiles (crops) - extending it to the CARE-bank-driven animal accrual
  model would be a genuinely different estimator, not a reuse of an
  existing one, which the task's "use existing validated machinery"
  instruction rules out. Stated up front because it turns out to be
  load-bearing (section 7).
- **Horizon = 4 days**, from game mechanics: WHEAT's `max_yield_day` is
  4 (so the window captures a growing WHEAT tile's entire remaining
  yield trajectory, and WHEAT is this repo's highest sell-volume
  product), it spans a full production interval for both active animals
  (COW=2, SHEEP=3), and it's inside the task's own "approximately 3-5
  days" spec. Not tuned against any evaluation result.
- **No margin/coefficient added to the SELL-vs-HOLD comparison** - a
  strict inequality on a directly economic quantity (realised revenue)
  needs no further justification to add one.
- **Season urgency is structural, not a weight:** the horizon cap
  (`liquidation_start_day - 1 - day`) shrinks the candidate-day set on
  its own as the season ends, with no blended coefficient. On the last
  pre-liquidation day the horizon is 0 and the function returns SELL
  immediately without evaluating anything.
- **No opponent supply anywhere** - not even pinned to 0, no parameter
  exists for it in this candidate's call chain at all.

## 6. Tests

`tests/test_pricing_v1.py::TestEstimateMultiDaySellOrHoldDecision` (11
cases): key structure, quantity pass-through (`quantity` in must equal
`quantity` out - the property the whole experiment hinges on), the
horizon covering exactly the requested days, horizon shrinking to
`remaining_days`, horizon shrinking to the day before liquidation, zero
future opportunity on the last pre-liquidation day forcing SELL, a
currently-growing tile measurably worsening the forecast versus no
tiles at all (the exact gap v0 left open), best-day selection logic,
tie-resolves-to-sell, and opportunity-cost sign checks in both
directions (a real bug caught here during development - see below).

`tests/test_forward_sell_policy_v1_1.py` (10 cases) - directly targets
the task's validation checklist:

- **Baseline quantity preserved exactly:**
  `test_sell_order_quantity_exactly_matches_baseline_formula` and
  `test_quantity_is_never_sized_to_price_floor` (the latter explicitly
  proves the v0 bug does not recur - constructs a case where
  `PRICE_FLOOR` sizing and threshold sizing genuinely diverge, and
  confirms the candidate's order uses the smaller, threshold-based
  amount).
- **Liquidation unchanged:**
  `test_liquidation_bypasses_the_forward_decision_entirely` (the
  decision function is never called) and
  `test_liquidation_quantity_still_uses_price_floor_as_baseline_does`.
- **No future information leaks:**
  `test_forecast_only_uses_currently_known_tiles_and_inventory` - the
  forecast is a deterministic function of the tiles/inventory it's
  given right now, with no mechanism to reach an actual future
  observation (no `obs` object is even threaded past this call chain).
- **Pricing mechanics still come from the verified backbone:**
  `test_decision_matches_estimate_multi_day_sell_or_hold_decision_directly`
  - the wired decision agrees exactly with calling the `pricing_v1`
    function directly on the same inputs.

**Two real bugs caught by these tests before evaluation ran, not just
`main.py` conventions being followed:**
1. `opportunity_cost_of_holding`'s sign - a first draft of the test
   suite asserted it should equal the *gain* from holding when holding
   wins; the actual (correct) semantics are "the cost of holding *if it
   had been wrong*," which is 0 when holding is in fact the better
   choice. Caught by `test_no_opportunity_cost_when_holding_is_the_right_call`.
2. Two of the wiring tests' own setups (MELON with a `MAX_SELL_PER_TURN`
   cap of 15, and a shallow WHEAT glut) produced identical baseline and
   `PRICE_FLOOR` quantities, silently proving nothing - fixed by finding
   inventory levels where the two formulas genuinely diverge before
   trusting the assertion.

Full suite: **283/283 pass** (262 pre-existing + 11 + 10).

## 7. Behavioral diagnostics (the task's most important requirement)

`/tmp/v11_decision_diag.py`-equivalent, 12 self-play seeds, 10,425
logged decisions:

| | v0 (1-turn) | **v1.1 (multi-day)** |
|---|---|---|
| ties (revenue_now == best revenue_delayed) | 393/653 (60.2%) | **123/10,425 (1.2%)** |
| genuine differences | 260/653 (39.8%) | **10,302/10,425 (98.8%)** |
| HOLD wins among genuine differences | 260/260 (100%) | **10,298/10,302 (99.96%)** |

**The 60%-tie problem is gone, exactly as intended** - a multi-day
horizon gives the comparison something to differentiate on almost
every turn. **But the fix reveals the deeper problem v0's single-turn
horizon had been hiding, not solving: without a real downside to
waiting, "more days elapsed" is *monotonically* good for the forecast**
(`apply_town_demand`'s recovery term only ever moves price back toward
base, and nothing in the model penalises the elapsed time itself), so a
longer horizon just gives HOLD more chances to win, not better
information to weigh. Preferred-future-day distribution confirms this
directly: **6,856 of 10,425 decisions (66%) prefer the single furthest
day in the horizon** (offset=4) over every closer alternative - "wait
the maximum allowed time" is close to the default answer, not a
considered one.

**Per product:**

| product | n | sell rate |
|---|---|---|
| MELON | 4,048 | **1.8%** |
| WOOL | 6,377 | **0.9%** |
| WHEAT/CARROT/STRAWBERRY | **0** (never reached the decision at all - see section 9) | - |

**By day bucket:** sell rate is 0.0% for days 5-14, rising only to 3.6%
for days 15-19 - "more aggressive as liquidation approaches" is barely
present and nowhere near enough to matter (section 5's structural
horizon-shrink mechanism is real, but a shrinking *chance* of holding
from ~100% to ~96% is not the season-end behaviour the task was hoping
the structural approach would produce).

## 8. Seeded evaluation

| harness | result |
|---|---|
| self-play (12 seeds), candidate vs itself | mean **16,892-17,216**, stdev 1,555-2,286, range ~12,816-20,239 |
| self-play, baseline (`main.py`) | mean 61,303-64,737, stdev 8,870-11,626 |
| head-to-head vs `main.py`, 24 matches | **-55,589 mean, 0/24 wins** |
| paired vs `starter`, 12 seeds | **-53,066 mean, 0/12 wins, sd=9,104, t=-20.19** |

**Every seed, every harness, the same direction, at a scale far beyond
anything measured in this repo's pricing-experiment history.** Per-seed
paired deltas vs `starter` range from -30,203 to -64,797 - no seed comes
close to neutral, let alone positive. This is not the v0 pattern
(harnesses disagreeing, moderate variance); it's unanimous and total.
**Do not declare success from a single opponent was the task's own
caution - here, all three independent harnesses agree, which is exactly
the standard this repo's own evidence practice asks for before trusting
a result, and what they agree on is rejection.**

## 9. Mechanism, fully traced

Behavioral diagnostic (baseline vs. candidate, self-play, 6 seeds):

| | baseline | candidate |
|---|---|---|
| final reward (mean) | 64,737 | **17,216** |
| MELON avg pre-liq shed qty | 0.17 | **14.10** (83x) |
| WOOL avg pre-liq shed qty | 0.52 | **4.31** (8x) |
| WHEAT sell-events | 74.7 | **41.8** |
| cash @ day 10 | 353 | **15** |
| cash @ day 29 | 59,207 | **8,804** |

**The full causal chain, traced and confirmed, not inferred:**

1. MELON and WOOL (the only two products that ever reach the decision -
   STRAWBERRY, being an ongoing crop that's usually held in small
   quantities, and CARROT/WHEAT, whose production itself collapses in
   step 4 before they ever accumulate enough to be evaluated) hold
   99%+ of the time, for the reason in section 7: no genuine downside to
   waiting, own-pipeline supply frequently reads 0 even for crops
   (`estimate_own_pipeline` correctly returns 0 whenever nothing of that
   crop happens to be currently growing - verified directly: at the
   exact turns MELON decisions were evaluated, tracing
   `estimate_own_pipeline`'s own tile-scan confirmed 0 growing MELON
   tiles at that moment in the *candidate's own trajectory*, even though
   the *unmodified baseline's* trajectory had 3 growing at the
   equivalent point - harvest events cluster, so the tiles that produced
   a sellable batch are often freshly empty right when that batch
   becomes worth deciding about).
2. Shed inventory of MELON/WOOL balloons (14.10 / 4.31 average
   pre-liquidation, vs. 0.17 / 0.52 baseline) because it is essentially
   never sold until forced.
3. **Cash starves.** Verified directly on seed 0: money sits at
   **exactly $19** from day 10 through day 15, with **zero hired
   hands** the entire time - the crew has completely collapsed, not
   just slowed down.
4. With no hands, farm throughput collapses across the board - not just
   for the held products, for everything. This is why WHEAT sell-events
   fall (74.7 -> 41.8) despite WHEAT never once reaching the forward
   decision in the 12-seed sample: there's no cash-starvation-immune
   channel here, the whole farm's production shrinks together. This is
   the same "single farmer's/crew's upkeep capacity caps income"
   mechanism `CLAUDE.md` already documents from the hiring-gate and
   crew-density experiments - reproduced here in an extreme form by
   cutting off the cash side of that loop entirely.
5. Final bank collapses to ~17,000-25,000, a fraction of baseline's
   ~60,000-80,000.

This is not a subtle mispricing. It's a policy that, by refusing to
convert two of its most valuable products into cash, starves the entire
operation of the working capital everything else depends on.

## 10. Failure modes

- **The value model still has no genuine cost of waiting** - v1.1 fixed
  v0's *information* gap (own pipeline supply is now modelled) but not
  its *structural* gap: nothing in `compare_immediate_vs_delayed_selling`
  penalises elapsed time itself, only the (never-negative) town-demand
  recovery term rewards it. Adding real information to a model with no
  downside for using more of it just makes the model more confidently
  wrong, which is exactly what happened (v0: 100% HOLD among genuine
  differences at a 1-turn horizon; v1.1: 99.96% HOLD among genuine
  differences at a 4-day horizon that's used almost entirely at its
  maximum length).
- **Own-pipeline supply is unavailable for animal products entirely**,
  and frequently reads 0 even for crops at exactly the moments a
  decision is being made (harvest-then-idle tile timing), so the
  "multi-day forecast" degrades toward "town demand only" - the same
  failure mode as v0 - for the majority of real decisions, just spread
  over more days instead of one turn.
- **A severe, previously undersized second-order effect: holding
  crashes cash flow, which crashes hiring, which crashes total farm
  output.** This dominates the final score far more than the direct
  cost of any individual delayed sale - the mechanism section shows
  the crew going to *zero hands* for a five-day stretch on a
  representative seed.
- **No hard limit on how much can be held.** `inventory_pressure`
  exists in this codebase and could have forced a sale once a position
  became structurally overcommitted, but this candidate never wires it
  in (out of this experiment's stated scope: only quantity-sizing and
  the multi-day forecast were meant to change) - its absence is a real
  contributor to the severity here, not just a missed nice-to-have.

## 11. Recommendation

**B - reject V1.1.** Not A: every harness, every seed, shows a severe
loss (paired t=-20.19, head-to-head 0/24). Not D (insufficient
evidence): the evaluation is unanimous and the mechanism is fully
traced end to end, from decision log to shed inventory to cash to hands
to final bank - there is nothing more to learn from re-running this
exact candidate. Not quite C either, stated plainly: "one final targeted
refinement" undersells what's broken here. The multi-day forecasting
*idea* is not shown to be unsound (section 7's tie-elimination worked
exactly as designed), but *this* value model has no mechanism that can
ever produce a balanced decision - it needs a structural downside to
waiting, not a parameter tweak, before it is safe to re-evaluate. That
is a new design question, not "adjust the horizon" or "add a margin,"
both of which the task correctly warned against inventing without
justification.

**What a genuinely different v1.2 would need, if this line of work
continues on a future day (not started here, per instruction not to
begin another experiment automatically):**

1. A real cost-of-waiting term - not a coefficient bolted onto the
   existing comparison, but something economically grounded: e.g.
   requiring the forecast to also model competing inventory pressure
   from the *other* products still to be produced and sold this season
   (a genuine capacity constraint, in the spirit of `inventory_pressure`
   but applied here, not left unwired), so holding one product has a
   modelled opportunity cost against the farm's overall cash needs -
   which is precisely what collapsed in section 9.
2. Explicitly bound how much can ever be held before a hard sell is
   forced, independent of the forecast - `inventory_pressure`'s `>= 1`
   break-even already exists in this codebase for exactly this purpose
   and simply was not wired into v1.1's decision.
3. Address the animal-product gap directly rather than defaulting it to
   0 - either build a genuine CARE-bank-aware production estimator (a
   real, scoped new capability, not a parallel reimplementation of an
   existing one) or explicitly exclude animal products from a
   forward-looking gate until one exists, rather than letting them
   default into the same "always hold" failure this report found.

No implementation follows from this report. `main.py` and `pricing.py`
are untouched; nothing merged; nothing submitted. Per instruction, no
further pricing experiment follows automatically from this result -
this closes today's pricing track pending a human submission decision.
