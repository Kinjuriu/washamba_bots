# Experiment report: forward-pricing crop selection & selling (V0)

Branch: `experiment/forward-pricing-crop-selection`, off `research/forward-pricing-v0` (`9043010`), off V1 (`0265554`).
**Not merged. Not submitted to Kaggle. V1 checkpoint untouched.**

## Hypothesis

The agent picked crops and sized SELL orders using *today's* spot price and
two hand-tuned discount terms (a glut discount relative to baseline stock,
a self-supply discount shaped `1/(1+pressure)^2`). But a crop isn't sold
the instant it's planted - a melon planted today sells up to 12 days later.
A crop with a great spot price now may be a bad choice if its price will
have collapsed by harvest time (by town demand, or by our own pipeline
landing on it first). We predicted that scoring crops by
`pricing.py`'s `estimate_future_price()` at the crop's actual harvest
horizon - and sizing SELL orders with `recommend_sell_quantity()`'s real
per-unit price path instead of a static cap - would improve outcomes.

## Baseline (V1, commit `0265554`)

- `unittest discover -s tests`: 106 passing
- Validation gate: `['DONE', 'DONE']`
- Self-play, seeds 0-5 (`experiments/forward_pricing_experiment.py 6`):

  | | mean | median | stdev | min | max |
  |---|---|---|---|---|---|
  | baseline | 27,245.8 | 27,005.0 | 1,604.3 | 24,763.0 | 29,894.0 |

  (Matches `docs/CHECKPOINTS.md`'s V1 entry exactly - 27,246/±1,604 - confirming determinism.)
- Seeded batch vs built-ins, 12 seeds (already recorded in `docs/CHECKPOINTS.md`, not re-run):
  `pass` 41,969±2,206, `random` 42,812±1,926, `starter` 43,105±1,740, all 12/12.

## Change

`main.py`, two functions only - no movement/watering/harvesting/animal/hiring/land logic touched:

- **`choose_crop`**: replaced `price * glut_discount * self_supply_discount` with
  `pricing.estimate_future_price(crop, current_inventory, turns_ahead=first_yield_day*24,
  our_pipeline_supply=<existing count_pipeline_supply() total>)["future_price"]`.
  The two hand-tuned discount terms (and their constants, `MARKET_BASELINE_STOCK`,
  `MARKET_ABSORPTION`, `SELF_SUPPLY_EXPONENT`, `MIN_GLUT_DISCOUNT`) are removed rather
  than kept alongside - they were approximations of exactly what the real formula now
  computes, and keeping both would double-count the same effect.
- **`decide_market_actions`**: the SELL quantity (once `should_sell()`'s unchanged
  yes/no gate says to sell) now comes from `pricing.recommend_sell_quantity(product,
  market_inventory, held_quantity, min_acceptable_price=<same threshold should_sell used>,
  max_per_turn=MAX_SELL_PER_TURN)` instead of a blind `min(held_quantity, cap)`. Liquidation
  and the shed-force-sell path keep selling regardless of price (`min_acceptable_price=
  PRICE_FLOOR`), which makes them numerically identical to the old behaviour - only the
  normal, price-gated path can now sell *less* than the cap.
- One bug fixed in the same pass: `choose_crop` defaulted a crop missing from the
  observation's inventory dict to `0` (implying total scarcity); real observations always
  include every product, so this only mattered for malformed input, but `0` fed a
  near-zero inventory into `hinge`-shaped `below_func`s (CARROT/TOMATO), which explodes -
  see `notebooks/pricing_analysis_v0.ipynb` section 2b. Changed the default to `10000` (I0).
- `main.py` now imports `pricing.py` - **not yet resolved for a real submission**: the
  competition accepts a single `main.py` (or a `.tar.gz` with `main.py` at the root), and a
  bare `main.py` upload would not bundle `pricing.py`. Flagged, not fixed, since this branch
  isn't being submitted.

Existing `TestChooseCrop` fixtures for two tests (`test_avoids_oversupplied_high_price_crop`,
`test_a_glut_still_loses_to_a_scarce_crop_of_similar_value`) needed updating: they relied on
crops absent from the fixture's `inventory` dict scoring an implicit `0` (via the old code's
`prices.get(crop, 0)`), which no longer applies once price is derived purely from inventory.
Updated both to set every plantable crop's inventory explicitly (deep glut for the ones not
under test), preserving each test's original intent and assertion.

## New tests (`tests/test_nikaangukia_meroni.py::TestForwardPricingIntegration`, 5 tests)

1. `test_future_price_estimate_is_lower_than_spot_once_pipeline_lands` - future-price integration
2. `test_avoids_a_crop_whose_own_pipeline_will_collapse_its_price` - forward-price ranking changes the actual crop choice
3. `test_sell_quantity_shrinks_below_the_cap_when_price_would_cross_threshold` - selling quantity recommendation
4. `test_liquidation_still_sells_the_full_cap_regardless_of_price` - safety constraint preserved
5. `test_no_sale_when_market_is_already_at_or_above_the_glut_threshold` - glut edge case

## Results

- `unittest discover -s tests`: **111 passing** (106 preserved + 5 new)
- Validation gate: `['DONE', 'DONE']`
- Self-play, **same seeds 0-5**, same script:

  | | mean | median | stdev | min | max |
  |---|---|---|---|---|---|
  | baseline (V1) | 27,245.8 | 27,005.0 | 1,604.3 | 24,763.0 | 29,894.0 |
  | treatment | **34,285.5** | **34,463.0** | 4,709.7 | 27,310.0 | 41,959.0 |
  | delta | **+7,039.7 (+25.8%)** | +7,458.0 | +3,105.4 | +2,547.0 | +12,065.0 |

  Per-seed paired delta (same seed, both sides self-play, so directly comparable):

  | seed | baseline | treatment | delta |
  |---|---|---|---|
  | 0 | 26,786 | 35,147 | +8,361 |
  | 1 | 27,166 | 41,959 | +14,793 |
  | 2 | 24,763.5 | 27,310 | +2,547 |
  | 3 | 26,844 | 33,779 | +6,935 |
  | 4 | 28,021 | 31,219 | +3,198 |
  | 5 | 29,894 | 36,299 | +6,405 |

  **All 6 seeds improved. Zero regressions.**

- Seeded batch vs built-ins, 12 seeds:

  | vs | baseline mean | treatment mean | delta | win-rate | escapes |
  |---|---|---|---|---|---|
  | `pass` | 41,969 ±2,206 | 48,226 ±3,398 | +6,257 | 12/12 | 0 |
  | `random` | 42,812 ±1,926 | 49,819 ±2,340 | +7,007 | 12/12 | 0 |
  | `starter` | 43,105 ±1,740 | 49,128 ±3,040 | +6,023 | 12/12 | 0 |

## Interpretation

Every seed, in both the self-play and the built-in matchups, moved the same
direction by a wide margin - this is not a single lucky episode and not
noise within either benchmark's own stdev. The self-play mean delta
(+7,040) is roughly 4.4x the baseline's own stdev (1,604); the paired
per-seed deltas (which control for seed-specific variance - weed spawns,
shop unlocks) are uniformly positive and range +2,547 to +14,793, none
close to crossing zero.

Two things temper this rather than change the accept/reject call:

- **Treatment variance is higher** (self-play stdev 4,710 vs baseline's
  1,604) - the paired comparison shows this is dispersion in *how much*
  better the treatment does, not a mix of better and worse seeds, but it
  means the mean is a less precise summary than it was for V1.
- **This is a very small sample** (6 self-play seeds, 12 seeded-batch
  seeds) by the standard `CONTRIBUTING.md` itself sets - promising, not
  proven at scale. The consistent sign across every seed and both
  benchmarks is the strongest part of the evidence, not the mean alone.

## Decision: **NEEDS MORE DATA (leaning ACCEPT)**

The result clears the bar in `docs/EXPERIMENT_WORKFLOW.md` - a delta well
outside run-to-run noise, on both self-play and the seeded batch, with
every individual seed agreeing on direction. It should **not** be treated
as proven on 6 self-play seeds alone, per the same evidence standard this
experiment is trying to uphold. Before promoting this branch:

- Re-run self-play on a larger seed set (the standard 6 is `selfplay_bench.py`'s
  own default for a quick check; `CONTRIBUTING.md` calls this "the honest
  number" but doesn't treat 6 seeds as final for a big claimed delta).
- Resolve the `pricing.py` bundling gap before any submission is even
  possible (single-file constraint).
- Consider whether the increased variance is itself a risk worth
  characterizing (which seeds/conditions produce the smaller deltas).

Per instructions: **not merged, nothing submitted to Kaggle, V1 checkpoint
untouched.** The branch is preserved with this report for whoever picks up
the next iteration.
