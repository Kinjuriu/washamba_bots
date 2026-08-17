# Pricing Cadence V1.1 — Sensitivity & Mechanism Validation

Branch: `experiment/pricing-cadence-v1`, off `main` (`da8cdea`).
**`main.py` untouched throughout.** Not merged. Not submitted to Kaggle. No new
checkpoint created. Builds on `experiments/pricing_cadence_experiment_report.md`
(V1), which established variant D (forward-price + inventory pressure +
cadence urgency) as a 24/24, low-variance win over the unmodified control A.

## Research question

Not "what values maximize the benchmark score." **Is D's advantage robust to
reasonable changes in its four constants, and what mechanism actually
explains it?** A narrow lucky optimum and a genuinely robust mechanism can
produce the same headline number; only a sensitivity sweep tells them apart.

## Step 1 — Assessment of the four constants (from the code, not guesswork)

Traced the exact application order in `agent_d.py`'s selling loop:
`min_price = value_hold_per_unit → ÷(1+PRESSURE·pressure) → ×(1-URGENCY_PRICE·urgency) → floored`;
`cap = base_cap × (1+URGENCY_CAP·urgency)`.

| constant | baseline | mechanism | activation range found by inspection |
|---|---|---|---|
| `SELL_HORIZON_DAYS` | 3 | turns_ahead for the forecast | **dead zone at zero pipeline supply** — with nothing landing, town demand barely moves price over a few days regardless of horizon |
| `INVENTORY_PRESSURE_WEIGHT` | 1.0 | divides accept price by `1+weight·pressure` | `inventory_pressure` looks up a per-turn cap via `MAX_SELL_PER_TURN.get(item, 10_000)` — **only `STRAWBERRY`/`MELON`/`WOOL` have a real entry**; every other product gets pressure ≈ 0 for any realistic pile |
| `CADENCE_URGENCY_PRICE_WEIGHT` | 0.6 | multiplies accept price by `1-weight·urgency` | **saturates at `urgency ≈ 0.62`, not 1.0** — `LIQUIDATION_START_DAY=19` overrides `min_price` straight to `PRICE_FLOOR` from day 19 on, so this term's effective window is days 0–18 only |
| `CADENCE_URGENCY_CAP_WEIGHT` | 1.0 | multiplies the per-turn cap by `1+weight·urgency` | same 3-crop activation gap as pressure, but **not** overridden by liquidation — the boosted cap is used as `max_per_turn` all the way to day 29 |

**Behaviour by season phase** (traced directly, not assumed): season start and
first-harvest days have zero pipeline supply for most crops, so `SELL_HORIZON_DAYS`
and the forecast are near-inert there too — D's divergence from A only starts
once real inventory exists. Mid-season is where pressure/urgency-cap can bind
for the three capped goods. From day 19, `LIQUIDATION_START_DAY` takes over
the *price* decision entirely (both A and D sell regardless of price), but D's
cap boost keeps compounding, so D can still move more per turn than A in the
liquidation window. At the price floor, both variants behave identically
(nothing left to discount).

**Working hypothesis going in**: two of four constants (pressure, cap-boost)
structurally only touch 3 of 9 market products — if D's edge is real, it's
either concentrated in those three crops or coming from somewhere else
entirely. Step 2 tests this directly.

## Step 2 — One-factor-at-a-time sweep (disciplined, not a grid search)

`experiments/pricing_cadence_sensitivity_sweep.py`. Each constant swept at
0.75/0.90/1.10/1.25× baseline (`INVENTORY_PRESSURE_WEIGHT`,
`CADENCE_URGENCY_PRICE_WEIGHT`, `CADENCE_URGENCY_CAP_WEIGHT`) with every other
constant held at D's current value. `SELL_HORIZON_DAYS` deviates from the
literal multiplier grid — it's a day count small enough that 0.75×3=2.25 and
0.90×3=2.7 both round to a value indistinguishable from baseline or each
other — so it uses the discrete local set `{1, 2, 5, 7}` instead. 4-seed
screen first (8 matches/config, seat-swapped) to find obviously poor regions
before spending a full 12-seed run on every point.

**Result — three of four constants are completely inert:**

| constant | settings tested | screen mean | vs. D itself |
|---|---|---|---|
| `SELL_HORIZON_DAYS` | 1, 2, 5 | +1,593.8 (identical) | no effect |
| `SELL_HORIZON_DAYS` | 7 | +1,733.2 | some effect, unconfirmed at scale |
| `INVENTORY_PRESSURE_WEIGHT` | 0.75 – 1.25 | +1,593.8 (identical, all four) | no effect |
| `CADENCE_URGENCY_PRICE_WEIGHT` | 0.45 – 0.75 | +1,593.8 (identical, all four) | no effect |
| `CADENCE_URGENCY_CAP_WEIGHT` | 0.75 – 1.25 | **+1,268.5 → +1,767.6**, monotonic | **the whole effect** |

Full numbers: `experiments/pricing_cadence_v1_1_sweep_screen.json`.

This is not what was expected from Step 1's activation-range analysis alone —
pressure was predicted to matter for the 3 capped goods, but the screen shows
it makes *zero* difference to the outcome even there. The reason: whenever
pressure or the price-side urgency term would lower the accept price, the
*cap* is already the binding constraint on how much sells that turn (a
`recommend_sell_quantity` call that's cap-limited never reaches the point in
its per-unit walk where a lower price threshold would have mattered). D's
entire measured advantage over A traces to one mechanism: **raising the
per-turn sell cap as the season progresses**, not to the forward-price
forecast or the pressure discount — even though both of those were
independently shown to help in V1 (variants B and C each beat A alone). They
just don't add anything *on top of* D's cap-boost, in this state space.

## Step 3–4 — Diagnosing the mechanism

Instrumented episode trace (`experiments/pricing_cadence_v1_1_trace_seed0.csv`),
D vs. A in one contested episode (seed 0, both sides traced every turn, so
market conditions are identical for both — a true side-by-side comparison,
not two separate mirror matches).

**Inventory behaviour** — the clearest, largest signal found:

| | mean units held (all products, all turns) | max held |
|---|---|---|
| A | 157.6 | 490 |
| D | **42.5** | **148** |

D carries roughly **a quarter** of A's average shed inventory and a third of
its peak. This is the mechanism, concretely: D doesn't forecast its way to a
better price, it just doesn't let inventory build up in the first place.

**Selling behaviour** (per-turn decision classification: SELL / PARTIAL_SELL
/ HOLD / LIQUIDATE, every turn, cross-checked against actual emitted orders):

| | HOLD | LIQUIDATE | SELL | PARTIAL_SELL | total opportunities logged |
|---|---|---|---|---|---|
| A | 871 | 119 | 6 | 6 | 1,002 |
| D | 681 | 121 | 5 | 5 | 812 |

D logs fewer total "something to sell" opportunities at all (812 vs. 1,002) —
consistent with the lower average shed occupancy: there's simply less sitting
around to make a decision about, because it moves faster.

**Price behaviour** — MELON sell-price sequences within the episode:

```
A:  244, 214, 165, 142, 34   (5 sells - visible price-impact cascade)
D:  244, 214, 34             (3 sells - same cascade shape, fewer total sells)
```

Both variants show the same self-inflicted price crash once melon inventory
gets large enough to require multiple big sells — D isn't immune to price
impact, it just triggers it less often because less inventory accumulates
between sells.

**Revenue by product** (same episode): D's approximated realised revenue
(order-quantity × spot-price-at-order-time) was *lower* than A's on MELON and
STRAWBERRY individually (D sells less of each, since less piles up to begin
with) but D's **final bank was still higher** (42,106 vs 40,369) — the gain
isn't from extracting more revenue per sale, it's from the compounding effect
of not tying up capital and shed space in a growing pile.

**Cash behaviour**: farm money for days 0–11 is *identical* between D and A
through day 7 (both hit the same well-documented early-season trough,
~$410–460 around day 3–4 — expected, since D and A share every non-selling
system unchanged) and diverges only slightly (D marginally lower,
~$60–100) from day 8 on. No sign of cash starvation.

**Final shed occupancy** (season end, day 29): both A and D finish with 1
unit of `WHEAT` unsold and nothing else — neither variant misses liquidation
in this episode.

## Step 5 — Failure modes checked

| mode | checked how | result |
|---|---|---|
| **A. Over-hold** | mean/max held, A vs D (above) | **Not observed for D** — D holds *less* than A, the opposite pattern |
| **B. Over-sell** | price sequences during D's sell runs | Same price-impact shape as A, not worse; not tested at very high `CADENCE_URGENCY_CAP_WEIGHT` (see Step 6 caveat) |
| **C. Miss liquidation** | final shed contents, day 29 | Not observed — both variants clear to ~0 |
| **D. Price-impact spiral** | consecutive-sell price sequences | Present in *both* A and D for MELON (self-inflicted crash), not unique to or worsened by D |
| **E. Forecast instability** | `estimate_sell_or_hold_value` swept over ±0.1% inventory and 0–50 opponent-supply steps | Smooth, monotonic response in both sweeps — no cliff or decision-flip found (`hold_is_better` transitions gradually as opponent supply rises from 10→20 units, not discontinuously) |
| **F. Crop asymmetry** | `MAX_SELL_PER_TURN` activation analysis (Step 1) | **Confirmed structurally**: 2 of 4 constants only ever affect `STRAWBERRY`/`MELON`/`WOOL`. Not a bug, but means "D" is really "a cap-boost policy for 3 crops" more than a general cadence policy |
| **G. Early-season cash starvation** | farm money, days 0–11 | Not observed — identical trough timing/depth to A |

## Step 6–8 — Robustness table and the robust candidate

Because three constants are provably inert in the tested regime, the
robustness question collapses to one dimension: `CADENCE_URGENCY_CAP_WEIGHT`.
Screened beyond the disciplined 0.75–1.25× window specifically to check
whether the visible trend was heading toward a peak or just extrapolating:

| setting | screen mean (4 seeds) | trend |
|---|---|---|
| 0.75× | +1,268.5 | |
| 0.90× | +1,453.1 | |
| **1.00× (current D)** | **+1,593.8** | reference |
| 1.10× | +1,619.0 | |
| 1.25× | +1,767.6 | |
| 1.50×* | +1,990.2 | |
| 2.00×* | +2,179.0 | |
| 3.00×* | +2,419.2 | diminishing returns, still rising |

\* Beyond the originally-scoped 0.75–1.25× window — measured only to
characterize the trend shape, explicitly **not** chased as a candidate. Doing
so would cross from "is this robust" into "what maximizes the score," which
this experiment was explicitly scoped not to do.

**This is a monotonic, diminishing-returns curve with no interior peak and no
reversal found anywhere tested.** That is a different shape than "a broad
plateau of near-equal performance" — it means the constant hasn't been
over-tuned to a lucky point, but it also means the *top* of its useful range
is still unlocated. Framed honestly: this is not evidence of a fragile
optimum (nothing sensitive or cliff-like was found), but it's also not a
fully closed robustness question — a truly robust pick would sit inside a
region already known to have a ceiling on both sides, and only one side has
been found here.

**Robust candidate chosen: `CADENCE_URGENCY_CAP_WEIGHT = 1.25`** — the top of
the originally-disciplined sweep window, not the top of the extended
trend-characterization points. Justification: it's the strongest setting
inside the range the experiment was actually scoped to test, every other
constant stays at D's already-validated value, and it doesn't require
extrapolating into a region where over-sell risk (failure mode B) hasn't been
checked.

## Step 8 — Full 12-seed confirmation: D vs. D′(1.25×) vs. A

Same paired/seat-swapped methodology and seed range (0–11) as the original
V1 benchmark.

| | mean | median | stdev | best | worst | wins |
|---|---|---|---|---|---|---|
| D vs A | +1,571.0 | +1,597.0 | 209.4 | +1,956 | +999 | 24/24 |
| **D′ vs A** | **+1,748.7** | **+1,782.0** | 216.5 | **+2,129** | **+1,147** | **24/24** |

Per-seed paired deltas (D′ vs A, all 12 seeds): +1844, +1754, +1626, +1847,
+1709, +1816, +1494, +1734, +1696, +1881, +1753, +1831 — **every seed
individually higher than D's corresponding seed** (D vs A: +1704, +1577,
+1478, +1617, +1523, +1678, +1360, +1557, +1519, +1627, +1576, +1638). D′ is
not just a better mean, it's a seed-consistent improvement over D, with a
comparable (not worse) worst-case and stdev. Full data:
`experiments/pricing_cadence_v1_1_robust_confirm.json`.

## Experiment artifacts

- `experiments/pricing_cadence_sensitivity_sweep.py` — the sweep generator +
  screening harness (reusable, documents the multiplier/discretization
  choices per constant).
- `experiments/pricing_cadence_v1_1.ipynb` — sensitivity visualizations per
  constant, the D-vs-A mechanism trace, and the final D/D′/A comparison.
- `experiments/pricing_cadence_variants/agent_d_robust.py` — standalone
  agent, D with `CADENCE_URGENCY_CAP_WEIGHT=1.25`, everything else identical
  to `agent_d.py`.
- `experiments/pricing_cadence_variants/sweep/` — all 19 generated
  sensitivity variants.
- `tests/test_pricing_cadence.py` — extended with tests confirming the
  inertness/activation findings for `inventory_pressure` (3-crop cap lookup)
  and `cadence_urgency` (liquidation-day saturation), so these aren't
  re-discovered by accident in a future session.
- Raw JSON/CSV: `experiments/pricing_cadence_v1_1_*.json/csv`.

## DISCOVERED

Three of D's four tuning constants (`SELL_HORIZON_DAYS` below 7,
`INVENTORY_PRESSURE_WEIGHT`, `CADENCE_URGENCY_PRICE_WEIGHT`) have **no
measurable effect** on the benchmark outcome in the tested state space — not
"small effect," identical results down to the exact dollar. The entire
measured gain traces to `CADENCE_URGENCY_CAP_WEIGHT` alone.

## MECHANISM

D outperforms A by **carrying roughly a quarter of A's average shed
inventory** (42.5 vs 157.6 units, traced episode), not by selling at a better
forecasted price. The cap-boost lets more of the 3 capped premium goods
(`STRAWBERRY`/`MELON`/`WOOL`) move per turn as the season progresses, which
prevents the pile-up that otherwise sits idle (scoring nothing while held)
and eventually forces a large, price-crashing dump. The forward-price
forecast and inventory-pressure discount are real, correctly-implemented
mechanisms (independently shown to beat A as variants B and C in V1) — they
just never end up being the binding constraint once the cap is also raised.

## ROBUSTNESS

`CADENCE_URGENCY_CAP_WEIGHT` has **no fragile point or reversal anywhere
tested** (0.75× to 3×, screen level) and the other three constants are
trivially "robust" because they're inert. This is not the same as having
found a bounded, broad-plateau optimum — the trend keeps rising through the
whole tested range, so the top of its useful region remains unknown. No
failure mode (A–G) was triggered by the accepted D configuration or by the
1.25× robust candidate at the seed counts tested.

## BEST ROBUST CONFIGURATION

`CADENCE_URGENCY_CAP_WEIGHT = 1.25`, all other constants unchanged from D.
Confirmed at full 12-seed paired benchmark: **every one of 12 seeds
individually better than current D**, mean +1,748.7 vs D's +1,571.0, worst
case +1,147 vs D's +999, 24/24 wins.

## REMAINING UNCERTAINTY

- The top of `CADENCE_URGENCY_CAP_WEIGHT`'s beneficial range is not located —
  values up to 3× still trend upward at the 4-seed screen level. Whether it
  plateaus, saturates against the shed's 100-unit capacity ceiling, or
  eventually triggers an over-sell failure mode (B) is unknown.
- `SELL_HORIZON_DAYS=7` showed a screen-level effect (+1,733.2 vs the
  otherwise-uniform +1,593.8) that was not confirmed at the full seed count
  and is not understood mechanistically.
- Three constants being fully inert in *this* state space doesn't mean
  they're inert in general — `docs/REPLAY_ANALYSIS.md`'s scale mismatch
  caveat from V1 still applies: this was measured on the current
  ~25-tile/~6-unit agent. At the ladder's 75-tile/13–15-unit scale, with far
  larger inventories and more products realistically hitting their caps, the
  pressure and price-forecast terms might well become the binding constraint
  instead. Untested.
- Failure mode B (over-sell) was checked qualitatively at D and D′, not at
  the higher cap-boost values where it would be most likely to appear.
- Single-episode mechanism trace (seed 0) for the inventory/decision/price
  diagnostics — the *aggregate* 12-seed benchmark is solid, but the *why*
  section leans on one representative episode, not all 12.

## DECISION

**NEEDS MORE DATA** for the specific candidate `CADENCE_URGENCY_CAP_WEIGHT =
1.25` to move beyond "promising and seed-consistent" to "settled" — the
robustness question is only half-closed (no fragile lower bound found, but no
upper bound found either), and the mechanism's crop-asymmetry (failure mode
F, confirmed structural) means this is really a policy for 3 of 9 products,
not yet characterized at the ladder's actual scale.

This is **not** a rejection: D′ beat D on every one of 12 seeds with no
failure mode triggered, which is meaningfully stronger evidence than V1's
original D-vs-A result had at the same stage. The honest gap is that the
sweep found a monotonic trend rather than a bounded plateau, and this
experiment was explicitly scoped not to chase that trend to find where it
stops — that's the natural next step, not a reason to accept or reject now.

Per instructions: **not merged, nothing submitted to Kaggle, no new
checkpoint created, `main.py` unchanged.**
