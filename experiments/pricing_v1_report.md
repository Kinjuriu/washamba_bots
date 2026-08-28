# Research report: pricing V1 forward-price-path model

Not a strategy change to `main.py` - a research module, following the spirit
of `docs/EXPERIMENT_WORKFLOW.md`'s discipline (observe → hypothesis →
validate → document) applied to a model rather than an agent change, since
the checkpoint machinery in `docs/CHECKPOINTS.md` is scoped to frozen agent
states and this doesn't produce one.

**Not merged into `main.py`. Not submitted to Kaggle. `main.py` and
`pricing.py` untouched.**

## Observation / hypothesis

`docs/pricing_engine_notes.md` audited `pricing.py`'s wiring into `main.py`
and found the forecasting layer (`estimate_future_price`) reaches the
planting decision (`choose_crop`) but never the selling decision, and named
several specific, unmodelled gaps: own-harvest timing was a flat "lands all
at once" assumption, opponent supply never reached the sell path even
though it's already computed, same-turn concurrent selling wasn't modelled
at all, and nothing compared holding against selling now.

Hypothesis: those gaps can be closed by a research module that **reuses**
`pricing.py`'s already-engine-verified mechanics core rather than
re-deriving it, adding only the pieces that were actually missing.

## What was built

`pricing_v1.py` (repo root, alongside `pricing.py`) - imports
`market_price`, `price_path_for_sale`, `apply_town_demand`,
`simulate_single_product`, `estimate_future_price`, and
`recommend_sell_quantity` directly from `pricing.py`; adds:

- `estimate_own_harvest_units` / `estimate_own_pipeline` - a real
  yield-accrual timing model (window-based for one-shot crops,
  interval-based for ongoing crops), replacing the flat assumption.
- `estimate_opponent_pipeline` - `main.py`'s `count_opponent_pipeline`
  logic, reimplemented generic over a tiles structure so this module has
  no dependency on `main.py`.
- `price_path_concurrent` - true per-unit lockstep modelling of two
  same-turn sellers sharing one inventory, mirroring the engine's actual
  `_process_market` loop.
- `expected_revenue_for_selling_n`, `compare_immediate_vs_delayed_selling` -
  the hold-vs-sell-now comparison nothing in the live agent currently
  makes.
- `inventory_pressure`, `season_urgency`, `recommend_sell_cadence` - a
  continuous cadence building block, replacing a hard liquidation-day
  cliff with a ramp (same idea `experiment/sell-cadence` already tried
  once - see `docs/pricing_engine_notes.md`'s "prior art" section before
  building on this piece further).
- `forecast` - one call producing the required core outputs together
  (`expected_future_inventory`, `expected_future_price`,
  `price_path_for_selling_n`, `expected_revenue_for_selling_n`).

## Tests

`tests/test_pricing_v1.py` - 49 cases, one class per function, covering
every deterministic component: window/interval accrual boundaries, pipeline
aggregation, concurrent-selling mechanics (shared pricing, exhaustion
order, inventory accounting, floor behaviour, equivalence to
`price_path_for_sale` in the one-sided case), the hold-vs-delay comparison,
pressure/urgency/cadence, and the top-level `forecast` orchestrator.

One cross-check worth calling out: `TestEstimateOpponentPipeline` compares
this module's `estimate_opponent_pipeline` against `main.py`'s
`count_opponent_pipeline` on identical input and asserts the two agree -
so this module's independent reimplementation can't silently drift from
what the live agent actually computes on the same tiles.

## Validation against the live engine

`notebooks/pricing_v1_validation.ipynb` - executed end to end
(`jupyter nbconvert --execute`), zero errors, zero mismatches. Runs real
episodes rather than re-checking formulas against each other:

- **Own-harvest timing**, all five plantable crops, one tile each, watered
  every eligible day, read directly from the replay at the start of every
  day: **0 mismatches across 47 day-checks.** This caught a real bug in
  the first draft before this report was written - see below.
- **Same-turn concurrent selling**, a controlled two-agent episode where
  both sides SELL the same product in the same turn: the model's predicted
  ending market inventory and predicted revenue both matched the engine
  **exactly** (9,949 vs. 9,949; $498 vs. $498). The notebook also shows,
  side by side, that the sequential approximation this replaces would have
  been wrong in a specific, biased direction - overstating our own average
  price and understating the opponent's, because it implicitly gives our
  own order "first pick" of the early high-inventory quotes that a
  genuinely contested turn does not grant either side.

## A bug the live-episode check found and the unit tests didn't

The first draft of `estimate_own_harvest_units` for one-shot crops (WHEAT,
CARROT, MELON) matched at the middle of its accrual window but was wrong
at both edges - it omitted the `+1` baseline `yield_units` the engine gives
every one-shot crop the instant it's planted (`_new_plant`,
kaggriculture.py:215-226), and it didn't account for an `hour == 0`
observation on day *D* only reflecting watering already completed through
day *D - 1* (watering is a real-time action, not an end-of-day batch step -
unlike the ongoing-crop accrual, which matched exactly on the first try
because `_daily_refresh_plants` is already keyed to `next_day`).

The unit tests written before the notebook was run did not catch this: they
asserted values in the *middle* of the window, where the two missing
adjustments happen to cancel out arithmetically, and never checked the
first or last day. Only running a live episode and reading the engine's own
`tile["yield_units"]` surfaced the discrepancy. Fixed in `pricing_v1.py`
before this report was written, tests updated to the corrected,
episode-verified values, notebook re-executed clean. Kept in this report
rather than smoothed over, because it's a direct, current-project
illustration of `CONTRIBUTING.md`'s standing rule: a green suite is
necessary, never sufficient - and here, specifically, a formula that is
internally self-consistent is not the same claim as a formula that matches
the engine.

## Status: proposal-grade, validated, not integrated

Every deterministic component is unit-tested; the two genuinely new
mechanics are validated against real episodes, not just against
themselves. Nothing here has been measured for whether it *improves* agent
performance - that is a different, later question (see
`docs/pricing_engine_notes.md`'s "Proposed next experimental layer" for
what a follow-up strategy experiment built on this module should measure,
and in what order), and this report makes no claim about it either way.

Per instructions: not merged into the agent, not submitted to Kaggle,
`main.py` untouched.
