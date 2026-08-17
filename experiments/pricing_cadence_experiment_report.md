# Experiment report: selling cadence — sell now vs. hold (V1)

Branch: `experiment/pricing-cadence-v1`, off `main` (`da8cdea`).
**`main.py` untouched throughout.** Not merged. Not submitted to Kaggle. No new
checkpoint created.

## Research question

Not "which crop has the highest current price" — `choose_crop` already answers
that with a forward-price forecast. This experiment is about the shed:
**given inventory pressure, town demand, opponent supply, harvest timing, and
remaining season, should the agent sell what it's holding right now, or wait?**

## What was already there (technical assessment)

1. **`pricing.py` / the inlined copy in `main.py`** models an engine-verified
   `market_price()` (piecewise scarcity/glut curve, five shape functions, $1
   floor), the per-unit lockstep sell mechanic, and town demand. Sufficient —
   nothing here needed re-deriving.
2. **The forward-price model** (`estimate_future_price`) assumes supply lands
   all at once at turn 0 (rather than spread across the window) and freezes
   `unlocked_shops` at whatever's passed in (no future unlocks modelled).
   Both documented, both pessimistic on price.
3. **Opponent-supply modelling** (`count_opponent_pipeline`) is real: visibility
   into the opponent's *planted tiles*, wired into `choose_crop` already. It's
   a lower bound — their shed is private. Not used anywhere in the selling
   path before this experiment.
4. **`recommend_sell_quantity()`** is a pure quantity-sizer against a
   caller-supplied acceptance price. It has no opinion on what that price
   should be — that's `should_sell()`'s job.
5. **Already sufficient**: all the price mechanics (spot, path, town demand,
   opponent supply) and `recommend_sell_quantity`'s quantity-sizing.
6. **Missing**: `should_sell()` was (and, on `main`, still is) a flat,
   state-blind per-product constant. Nothing compared today's price against
   the model's own near-future forecast; nothing scaled willingness-to-sell by
   how much of a product was piled up; `LIQUIDATION_START_DAY` (19) was the
   only cadence concept in the agent at all, and it's a hard binary switch.

**Scope note, surfaced by `docs/REPLAY_ANALYSIS.md`** (already in the repo,
verified against real ladder replays): selling cadence is explicitly ranked
**last** (Phase 6) of six identified gaps, behind land expansion and crew
scaling (Phases 1–2, not yet implemented — the agent still runs ~25 tiles /
~6 units against the replay's 75 tiles / 13–15 units). These results describe
cadence *at the current scale*. Whether the same mechanism holds once the crew
and market pressure are 3x larger is untested.

## Engine mechanics (re-verified, not re-derived)

Same installed engine as every prior pricing experiment
(`kaggle-environments` 1.32.7, unchanged file hash). `market_price()`,
per-unit lockstep selling, town-demand intervals, the harvest-timing gate,
`maxMarketOrdersPerTurn=10`, and `PRICE_FLOOR=1` all confirmed unchanged.

## The framework: sell-now-vs-hold

`estimate_sell_or_hold_value(item, quantity, inventory, day, pipeline_supply,
opponent_pipeline_supply, ...)` — no financial futures-curve assumption, just
the engine's own mechanics run forward:

- `value_now` = revenue from `price_path_for_sale()` at current inventory —
  the real per-unit decay within this turn's order, not just spot price.
- `value_hold` = `quantity * estimate_future_price()`'s forecast a short
  horizon out (`SELL_HORIZON_DAYS = 3`), given our own pipeline and the
  opponent's visible pipeline landing in between, and town demand draining
  the market in the meantime.

Two supporting functions, both new:

- `inventory_pressure(shed_quantity, pipeline_supply, remaining_days,
  per_turn_cap)` — how much of a product is carried relative to what could
  plausibly still move before season end. `>= 1` means structurally
  overcommitted, independent of price.
- `cadence_urgency(day)` — 0 at day 0, ramping smoothly toward 1 near season
  end. A continuous replacement for `LIQUIDATION_START_DAY`'s hard switch,
  chosen specifically because the replay evidence shows **no day-22 selling
  cliff** — cadence ramps, it doesn't flip.

All three are pure and deterministic. No LLM, no API, no online inference.

## Experiment design: four variants, isolated

Four **standalone agent files** under `experiments/pricing_cadence_variants/`
(root `main.py` never touched — each variant is a full copy with only the
selling-decision block patched):

| variant | mechanism |
|---|---|
| **A** | Current, unmodified `main.py` — byte-identical control |
| **B** | `should_sell()`'s static threshold replaced by `estimate_sell_or_hold_value`'s own 3-day forecast |
| **C** | B + `inventory_pressure` lowers the acceptance price as the pile grows relative to what can clear in time |
| **D** | C + `cadence_urgency` lowers the acceptance price further *and* raises the per-turn cap as the season runs out |

`should_sell()`'s yes/no gate is bypassed entirely for B/C/D — the dynamic
acceptance price does that job instead. The liquidation and shed-force-sell
safety nets are **unchanged** in every variant (still sell regardless of price
once triggered). One bug found and fixed while building the variants: the
shed can hold an unplaced *animal* (e.g. `SHEEP` before `BUILD_PASTURE`),
which isn't in `MARKET_PARAMS` — `should_sell()`'s plain `.get(product, 0)`
silently no-opped on it, but the new code called `market_price()`
unconditionally and raised `KeyError`. Fixed with an explicit
`if product not in MARKET_PARAMS: continue` guard.

`SELL_HORIZON_DAYS`, `INVENTORY_PRESSURE_WEIGHT`, and the two
`CADENCE_URGENCY_*_WEIGHT` constants are **first-pass, unswept** — the
experiment measures the direction of each mechanism, not a tuned optimum.

## Benchmark: head-to-head, paired, seat-swapped, 12 seeds

Per `docs/CHECKPOINTS.md`: **anything about selling needs a contested
market** — the built-in opponents never sell, so a market-timing change looks
free against them. Used `experiments/head_to_head.py`'s exact methodology
(each variant vs. unmodified A, both seats played and averaged so seat
advantage cancels).

| variant | mean | median | stdev | best | worst | wins |
|---|---|---|---|---|---|---|
| B vs A | +1,118.4 | +441.0 | 2,056.2 | +5,917 | **−1,499** | 21/24 |
| C vs A | +403.3 | +317.5 | 388.2 | +1,304 | −342 | 22/24 |
| **D vs A** | **+1,571.0** | **+1,597.0** | **209.4** | +1,956 | **+999** | **24/24** |

Per-seed paired deltas (all 12 seeds, seat-averaged):

```
seed:        0     1     2     3     4     5     6     7     8     9    10    11
B vs A:    566   810 -1488   109   326   441  1398  5851   321   183   201  4704
C vs A:    466   836   143   159   178   490  1304   206   196   233   228   402
D vs A:   1704  1577  1478  1617  1523  1678  1360  1557  1519  1627  1576  1638
```

Full raw data: `experiments/pricing_cadence_benchmark_results.json`.
Diagnostics and all 8 requested charts: `experiments/pricing_cadence_v1.ipynb`.

## Interpretation

**D is the clear result, not B or C in isolation.** B (forecast only) has the
highest raw mean but is driven by two large outlier seeds (7 and 11, both
under $4,700–5,900) and **loses seed 2 outright** (−1,499) — a forecast-only
acceptance price without any notion of urgency leaves the agent still capable
of holding out too long on an unlucky seed. C (+ pressure) tames the variance
sharply (388 vs B's 2,056) but at less than half B's mean — pressure alone is
a brake, not a driver. D (+ urgency) is qualitatively different from both:
**every one of 24 matches won**, the lowest variance by an order of magnitude,
and even its single worst result (+999) is a comfortable win. Adding the
continuous cadence/urgency term is what converts an inconsistent gain into a
robust one — consistent with the replay evidence that top-ladder agents sell
on a ramping schedule, not a threshold-triggered one.

This reproduces, mechanistically, what `main.py`'s own `LIQUIDATION_START_DAY`
history already found by hand (day-19 hard cutoff: +617 head-to-head, worse
against a non-selling opponent) — D generalizes that same insight (urgency
matters, and only shows up against a contested market) into a smooth,
state-aware policy instead of one hand-tuned day.

## What remains hypothetical

- **The four constants are unswept.** The experiment shows the *mechanism*
  (pressure + urgency) is directionally strong; it says nothing about whether
  `SELL_HORIZON_DAYS=3`, `INVENTORY_PRESSURE_WEIGHT=1.0`, or the two
  `CADENCE_URGENCY_*_WEIGHT` values at 0.6/1.0 are anywhere near optimal.
- **Scale mismatch with the ladder's actual leaders**, per
  `docs/REPLAY_ANALYSIS.md`: this was measured on the current ~25-tile/~6-unit
  agent. The replay's 75-tile/13–15-unit agents sell 15–48 orders/day — a
  volume this experiment's agent structurally cannot reach yet. Whether
  pressure/urgency matter as much (more? less?) once land and crew scale up
  is untested.
- **12 seeds, one opponent (self).** No sweep of `SELL_HORIZON_DAYS` or the
  weight constants; no test against a differently-tuned opponent (only
  mirror-match self-play, per this repo's paired-comparison convention for
  seed-reproducibility).
- **`estimate_sell_or_hold_value`'s value_now is a whole-order figure**, but
  `should_sell`'s replacement compares it as a *per-unit* number
  (`value_now_per_unit`) against `value_hold_per_unit` implicitly through
  `recommend_sell_quantity`'s own per-unit walk — the two are consistent by
  construction, but this wasn't independently stress-tested against a
  multi-product, multi-order turn.

## What was implemented

- `experiments/pricing_cadence_lib.py` — the sell-now-vs-hold framework,
  standalone and tested (`tests/test_pricing_cadence.py`, 15 tests).
- `experiments/pricing_cadence_variants/agent_{a,b,c,d}.py` — four standalone,
  runnable agents for the head-to-head comparison.
- `experiments/pricing_cadence_v1.ipynb` — 8 requested diagnostics (price vs.
  inventory, expected future vs. current price, sell quantity vs. pressure,
  sales/day, inventory by crop over time, revenue by crop, price trajectory
  by crop, cumulative realised revenue) plus the benchmark comparison, 0
  execution errors.
- **`pricing.py` changes** (promoted only after the benchmark validated the
  approach, per instructions): `estimate_sell_or_hold_value`,
  `inventory_pressure`, `cadence_urgency` added, with a cleaned-up API
  (`inventory_pressure` takes an explicit `per_turn_cap` rather than an
  internal per-product table, so the research module doesn't need to track
  `main.py`'s own `MAX_SELL_PER_TURN` constants). 11 new tests in
  `tests/test_pricing.py`. **Not wired into `main.py`** — that remains a
  separate, explicit step.
- 152 tests pass overall (139 pre-existing/lib-level + the 11 new
  `pricing.py` tests — `test_pricing_cadence.py`'s 15 tests against the
  experiment-lib copy are included in the 139). Validation gate: all four
  variants run to `['DONE', 'DONE']`.

## Decision: **ACCEPT** (mechanism), pending scope before wiring into `main.py`

The D variant clears every bar this repo's own evidence standard sets: paired
comparison (not across-seed stdev), a contested market (not the built-ins),
win count read first (24/24), and a result that holds seed-by-seed rather
than living in the mean. This is not a single-seed or single-metric result.

**Recommended before wiring into `main.py`:**
1. A constant sweep (at minimum `CADENCE_URGENCY_PRICE_WEIGHT` and
   `INVENTORY_PRESSURE_WEIGHT`) — the current values are a reasonable first
   guess, not a validated optimum.
2. Re-run once land/crew scaling (`docs/REPLAY_ANALYSIS.md`'s Phases 1–2)
   lands, since this experiment's inventory/pressure numbers are scaled to
   the current ~25-tile agent.
3. A `paired_compare.py` run against `pass`/`starter` too, purely as a
   regression check — head-to-head is the number that matters here, but a
   built-in regression would still be worth knowing about.

Per instructions: **not merged, nothing submitted to Kaggle, no new
checkpoint created.** `main.py` is unchanged; wiring D's mechanism into it is
a separate step pending explicit review.
