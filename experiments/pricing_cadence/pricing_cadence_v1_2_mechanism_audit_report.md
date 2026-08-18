# Pricing Cadence V1.2 — Mechanism Audit

Branch: `experiment/pricing-cadence-v1`, off `main` (`da8cdea`). **`main.py`
untouched throughout.** Not merged. Not submitted to Kaggle. No new
checkpoint created. Continues `experiments/pricing_cadence_v1_1_report.md`,
which found D's entire measured gain traces to `CADENCE_URGENCY_CAP_WEIGHT`
alone, and that D carries roughly a quarter of A's average shed inventory.
This round asks *why*, with instrumented per-turn evidence rather than
inferring from the headline score.

**This is not a parameter sweep.** No constant was tuned to maximize a
benchmark number. The one new agent variant built this round
(`agent_a_cap_boost.py`) is explicitly a diagnostic counterfactual, not a
candidate — its cap multiplier (2×) is a deliberately round, unoptimized
number, chosen and stated as such before running anything.

## Task 1 — state preserved

Confirmed before starting: `git status` clean, local and remote both at
`1e34404` (the V1.1 commit, tagged `pricing-cadence-v1.1-sensitivity-complete`).

## Task 2 — Instrumenting the selling bottleneck

`experiments/pricing_cadence_decision_trace.py`. For every (day, product)
where a variant held any inventory, records: market inventory, shed
quantity, desired sell quantity before any cap, the base and
cadence-adjusted cap, the minimum acceptable price, current spot price,
price after the proposed sale, a diagnostic forecast price (computed
identically for every variant, whether or not that variant's own logic
uses it), and the actual sold quantity — then classifies the decision as
`cap-bound` / `price-bound` / `inventory-bound` / `no-sell` / `liquidation`.

**A real bug found and fixed while building this**: `env.steps[i].action`
in `kaggle_environments` is the action *chosen from* `env.steps[i-1]`'s
observation, not `env.steps[i]`'s — it's recorded at the index of the state
it produced, not the state it was computed from. Confirmed directly: a real
`SELL MELON 21` order only makes sense paired with the *previous* step's
shed quantity (59, not the same-index reading of 38). Both this tracer and
(retroactively identified, not yet fixed) V1.1's mechanism trace paired
observation and action at the same index — off by one turn. Fixed here by
pairing `steps[i].observation` with `steps[i+1].action`. This does not
change any benchmark result (those come from the engine directly, not from
this analysis code) but it matters for anything that reasons about *why* a
specific turn's decision looked the way it did.

`classify_decision()` is the one new pure deterministic function this round
introduces; 8 tests in `tests/test_pricing_cadence_decision_trace.py`.

## Task 5 — The counterfactual (built early; its result shapes every later task)

`experiments/pricing_cadence_variants/agent_a_cap_boost.py`: **exactly**
`agent_a.py`, with `MAX_SELL_PER_TURN` doubled (`STRAWBERRY` 10→20, `MELON`
15→30, `WOOL` 5→10) and nothing else changed — no forecast, no pressure, no
urgency, `should_sell()` and its static thresholds untouched. Full 12-seed
paired/seat-swapped benchmark vs A, same methodology as every prior number
in this experiment:

| | mean | median | stdev | best | worst | wins |
|---|---|---|---|---|---|---|
| D vs A (V1.1) | +1,571.0 | +1,597.0 | 209.4 | +1,956 | +999 | 24/24 |
| D′ vs A (V1.1) | +1,748.7 | +1,782.0 | 216.5 | +2,129 | +1,147 | 24/24 |
| **A_cap_boost vs A** | **+2,326.3** | **+2,386.0** | 243.5 | **+2,824** | **+1,702** | **24/24** |

**The naive, unoptimized, price-blind counterfactual beats both D and D′.**
This single number reframes the entire mechanism question: a policy with
*zero* forecasting, *zero* pressure-awareness, and *zero* cadence logic —
just a bigger static cap — captures more value than the sophisticated
sell-or-hold framework. That is the headline finding this report has to
explain, not paper over.

## Task 3 — Decomposing the gain by crop

3 seeds (0, 1, 2) traced per pairing (A vs D, A vs D′, A vs A_cap_boost),
every turn, both sides. Full data: `experiments/pricing_cadence_v1_2_multi_seed_trace.csv`,
summary table: `experiments/pricing_cadence_v1_2_crop_decomposition.csv`.

| crop | A revenue/ep | D revenue/ep | D′ revenue/ep | A_cap_boost revenue/ep | D−A | D′−A | A_cap_boost−A |
|---|---|---|---|---|---|---|---|
| WHEAT | 1,227 | 1,139 | 1,139 | 1,139 | −88 | −88 | −88 |
| CARROT | 550 | 549 | 549 | 549 | −1 | −1 | −1 |
| TOMATO | 5,904 | 5,904 | 5,904 | 5,904 | 0 | 0 | 0 |
| STRAWBERRY | 19,917 | 20,282 | 20,299 | 20,296 | +365 | +382 | +379 |
| **MELON** | **16,343** | **19,031** | **19,359** | **20,045** | **+2,688** | **+3,016** | **+3,702** |
| WOOL | 7,591 | 7,605 | 7,605 | 7,605 | +13 | +13 | +13 |
| FERTILIZER | 9,667 | 10,955 | 10,955 | 10,955 | +1,288 | +1,288 | +1,288 |

**MELON accounts for the overwhelming majority of every variant's gain.**
STRAWBERRY moves a little; WHEAT/CARROT/TOMATO/WOOL are noise-level
(WOOL — one of the three explicitly capped goods — shows essentially **no**
measurable contribution at all, identical across all three treatments).
FERTILIZER's identical +1,288 across D/D′/A_cap_boost (not present for A) is
a side effect of `FERTILIZER`'s liquidation-only sell guard interacting with
the higher hire/harvest volume all three treatments produce, not a pricing
effect — flagged here as a secondary mechanism, not analyzed further this
round (out of scope: "keep unrelated agent behaviour frozen").

## Task 4 — What actually constrains A

Per-crop decision-classification counts, pooled across the 3 traced seeds
(this is the evidence base — not inferred from the score):

**MELON**, A (589 turn-opportunities where melon was held):

```
no-sell        567  (96.3%)
liquidation     13
cap-bound        9
```

**MELON**, A_cap_boost (445 opportunities — fewer than A's 589, see note below):

```
no-sell            423  (95.1%)
price-bound          9
liquidation          7
cap-bound            3
inventory-bound      3
```

**MELON**, D (17 opportunities — an order of magnitude fewer than A):

```
cap-bound          6  (35%)
inventory-bound    6
liquidation         5
no-sell             0
```

**A's dominant constraint is B — an excessive, static minimum acceptable
price — not C, insufficient capacity.** 96.3% of A's melon-holding turns are
`no-sell`: the static `$180` threshold simply isn't cleared, so the per-turn
cap is irrelevant almost all the time (only 9 of 589 opportunities ever
reach `cap-bound`). Doubling the cap alone (`A_cap_boost`) barely moves the
no-sell rate (95.1%, statistically the same problem) — **because it doesn't
touch the gate at all.** D removes the gate almost entirely (`no-sell` never
appears for D on melon in this sample) by replacing the static threshold with
a forecast-derived one that's usually satisfiable.

**Yet A_cap_boost outperforms D.** The resolution is in *how much moves when
the gate finally opens*. A (and A_cap_boost) wait for melon's price to
genuinely clear $180 — a rare, favourable moment — and A_cap_boost can then
dump twice as much into it (30 units vs 15). D never waits; it sells small
to moderate amounts continuously at whatever the forecast currently accepts,
which is very often well under $180. **A's real failure is an interaction
(Outcome F): a static price gate that blocks almost everything, combined
with a capacity cap that (when the rare good moment does arrive) is too
small to clear the backlog that built up while waiting.** Fixing either one
alone helps; A_cap_boost's result shows that at the current game scale,
fixing capacity while leaving the gate broken captures *more* value than
fixing the gate while only modestly raising capacity (D's actual
configuration) — because patient, large, well-timed sales currently beat
frequent, moderate, average-timed ones for this crop.

Why A_cap_boost's melon opportunity count (445) is *lower* than A's (589)
despite identical selling logic: the bigger cap clears each accumulated pile
faster once the rare price-clearing window opens, so fewer subsequent turns
still have melon sitting in the shed to log as a fresh "opportunity" — this
is consistent with, not contradictory to, the throughput story.

## Task 6 — Cadence shape vs. the replay evidence

Sell-order-event counts (not unit volume) per day, pooled across 3 seeds,
across all products:

| | mean orders/day (0–29) |
|---|---|
| A | 4.7 |
| D | 4.8 |
| A_cap_boost | 4.9 |

**Order-event frequency is essentially unchanged across every variant.**
None of D, D′, or A_cap_boost come close to the replay's observed 15–48
orders/day, and none move meaningfully in that direction relative to A.
**The mechanism under test increases volume per order, not order
frequency** — a different lever than whatever produces the replay's shape.
This is very likely the same scale mismatch V1.1 already flagged: the
replay's agents run ~75 tiles / 13–15 units and sell across a
proportionally wider crop mix simultaneously; ours still runs ~25 tiles /
~6 units. No evidence either variant reproduces the replay's *qualitative*
cadence shape — this experiment doesn't test the lever that would.

No day-19/22 discontinuity was visible in the daily order-count series for
any variant (all show a gradual day-10-to-day-25 ramp, consistent with
V1.1's finding that the liquidation-day price override doesn't visibly
distort the shape) — but this is a weak check at only 3 seeds and coarse
daily bucketing, not a claim that the cliff question is fully closed.

## Task 7 — Crop-specific cap coverage, verified against the engine

`kaggriculture.py:25`: `PRODUCTS = ["WHEAT", "CARROT", "TOMATO",
"STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]` — 9 real market
products. **`MAX_SELL_PER_TURN` (agent-side, not an engine concept) has
explicit entries for exactly 3**: `STRAWBERRY` (10), `MELON` (15), `WOOL`
(5). The engine itself has no per-order quantity cap at all — the only
engine-side per-turn limit is `maxMarketOrdersPerTurn=10`, a count of
*order objects*, not units, and orthogonal to this mechanism entirely
(confirmed unchanged from prior rounds' engine reading).

Every uncapped product (`WHEAT`/`CARROT`/`TOMATO`/`EGG`/`FERTILIZER`) falls
back to `cap = quantity` in the selling loop — i.e., **genuinely uncapped in
practice**, not merely a large number; `inventory_pressure`'s separate
`MAX_SELL_PER_TURN.get(item, 10_000)` fallback (used only inside the
pressure calculation, not the actual sell cap) is a different, even more
generous ceiling that keeps pressure ≈ 0 for these products regardless.

**The D gain is not just "concentrated in capped products" — it is
concentrated in one of the three** (Task 3's table: MELON +2,688 to +3,702
depending on variant; STRAWBERRY +365 to +382; WOOL +13, indistinguishable
from noise). `WOOL`'s near-total absence from the gain despite having an
explicit cap suggests the mechanism's current benefit isn't "any capped
crop" so much as "a crop whose static threshold is badly miscalibrated
relative to its actual price dynamics" — melon's $180 threshold against a
$250 base that self-crashes hard on oversupply (documented since the very
first forward-pricing work) is a much bigger mismatch than wool's.

**Should this generalize or stay product-specific?** Not decided this round
by design (implementation changes were out of scope), but the evidence
points toward: **the current design's 3-crop scope is not arbitrary — it
happens to line up with which crops have a badly-calibrated static
threshold, but that's a coincidence of which constants were hand-tuned when,
not a structural constraint.** A more general fix would recompute
`SELL_PRICE_THRESHOLDS` (or bypass it as D already does) for every product,
not just the three with a `MAX_SELL_PER_TURN` entry.

## Task 8 — Outcome, without overfitting the conclusion

**Outcome C (a combination), with a quantified skew toward throughput.**
Neither pure story survives the evidence:

- **Not purely Outcome A (throughput alone)**: D's forecast mechanism
  demonstrably fixes a real problem (A's 96.3% no-sell rate on melon,
  down to 0% for D) — that's a genuine pricing/gating fix, not a throughput
  effect.
- **Not purely Outcome B (sell-now-vs-hold valuation alone)**: A_cap_boost
  has *none* of that valuation logic and still wins by more than D does.
- **Quantified split**: of A_cap_boost's +2,326 total gain, essentially all
  of it (+3,702 on melon alone, against smaller/offsetting moves elsewhere)
  comes from capacity with the price gate left completely broken. D's
  +1,571 comes from fixing the gate (0% no-sell) while only modestly raising
  effective capacity (`CADENCE_URGENCY_CAP_WEIGHT`'s boost is smaller and
  time-dependent, vs. A_cap_boost's flat 2×). **On this evidence, capacity
  is the larger single lever at the current game scale, but the price-gate
  fix is not redundant** — it's what lets D sell *at all* on 100% of
  opportunities instead of ~4%, which matters for inventory risk even where
  it doesn't win on raw revenue.
- **Outcome D confirmed as a secondary finding**: the result is strongly
  crop-specific (Task 3/7) — this is a melon-throughput finding dressed as a
  general pricing-cadence policy, not a universal one.

## FINAL REPORT

### WHAT WE KNOW

D's advantage traces entirely to `CADENCE_URGENCY_CAP_WEIGHT` (V1.1); this
round establishes that a naive, unoptimized 2× cap-only counterfactual with
*zero* forecasting or pressure logic beats D outright (+2,326 vs +1,571,
both 24/24 vs A). The gain in both cases is concentrated almost entirely in
one crop, MELON, with STRAWBERRY contributing modestly and the other five
products contributing nothing to negligible amounts.

### WHAT ACTUALLY DRIVES D

An interaction, not a single cause. A's real failure on melon is its static
$180 threshold blocking 96.3% of selling opportunities (`no-sell`) — a price
problem. D fixes that almost completely (0% no-sell) via its forecast-based
threshold. But when A's gate *does* open, A can still dump less per event
than a simply-bigger cap would allow, and that patient/large-batch pattern
turns out to capture more total value than D's frequent/moderate one at the
current game scale.

### CROP CONTRIBUTION

MELON: +2,688 (D) to +3,702 (A_cap_boost) — effectively the entire story.
STRAWBERRY: +365 to +382, real but an order of magnitude smaller. WOOL
(also explicitly capped): +13, indistinguishable from noise despite sharing
the same mechanism. WHEAT/CARROT/TOMATO: flat to slightly negative, noise.

### BOTTLENECK

**B (excessive/static minimum acceptable price) is A's dominant, directly
measured constraint** — not C. But C (capacity) is what the evidence shows
matters *most* for the score once B is no longer the binding constraint
system-wide, because A_cap_boost never fixes B at all and still wins bigger
than the variant that does. Read literally: A's gate is broken worse than
its cap is small, but its cap being small costs more money than its gate
being broken, given how the two interact with melon's actual price dynamics.

### RELATIONSHIP TO REPLAY EVIDENCE

No variant tested this round moves sell-order *frequency* toward the
replay's 15–48/day — all three sit at ~4.7–4.9/day, statistically
indistinguishable from each other. The mechanism under test is a
volume-per-order lever, not the order-frequency lever the replay's shape
implies top agents use. This is consistent with, and does not resolve, the
scale-mismatch caveat already on record from V1.1.

### REMAINING UNCERTAINTY

- Only 3 seeds traced at the decision level (vs. 12 for the headline
  benchmarks) — the crop/bottleneck breakdown is directionally strong (the
  melon concentration is not a close call) but not measured at the same
  statistical weight as the accepted D-vs-A number.
- `FERTILIZER`'s identical +1,288 gain across all three treatments is
  unexplained by this round's scope and flagged, not investigated.
- The `reserved_wheat` approximation in the tracer (assumed 0, not the real
  per-turn reserve) makes `WHEAT`'s specific rows unreliable context;
  `WHEAT`'s crop-table numbers are still real (from actual episode
  outcomes), only its per-turn *classification* detail is approximate.
- Whether A_cap_boost's 2× multiplier is anywhere near where the
  throughput-alone lever stops helping is unknown and out of scope this
  round on purpose (no sweep was run on it).
- V1.1's own single-episode mechanism trace had the off-by-one bug this
  round found and fixed — its qualitative conclusion (D holds less total
  inventory) is *confirmed* at 3-seed scale here (154.2 vs 40.7), but any
  V1.1 statement about *which turn* a specific decision happened on should
  be treated as approximate, not re-verified.

### DECISION: **NEEDS MORE DATA**

Not a rejection of D, and not an endorsement of `agent_a_cap_boost.py`
(explicitly a diagnostic, never a candidate, per the task). The mechanism is
now identified with much more precision than V1.1 had — a real, quantified,
crop-concentrated interaction between a broken price gate and an
undersized cap — but two things block calling this settled: the finding
that a strictly simpler policy beats the accepted one demands a real
explanation of *why*, not just a note that it happens (a plausible
mid-fidelity account is above — the price-gate fix trades sale frequency for
average price, and averages fewer big sales at good prices beats many
smaller ones at moderate prices, on melon, at this game scale — but it isn't
independently verified against, say, a variant that fixes *only* the gate at
D's exact cap or *only* the cap at zero pressure/urgency change); and the
crop concentration means whatever ships next needs to be evaluated as a
melon-specific fix, not a general selling-cadence policy, which the current
framing doesn't yet do.
