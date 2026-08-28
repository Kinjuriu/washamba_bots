# Experiment: does the exact-yield opponent signal help the sell gate?

Follow-up to `experiments/opponent_aware_sell_gate_report.md` (rejected:
`count_opponent_pipeline` never had a positive value at the 162 real
decision points checked) and `experiments/opponent_supply_forecast_audit.md`
(found exact `tile["yield_units"]` is directly observable and correlates
with future price/inventory for MELON/STRAWBERRY/WOOL). This experiment
makes the ONE swap the audit recommended and re-measures. `main.py` and
`pricing.py` are untouched throughout (`git diff --stat -- main.py
pricing.py` empty at every step below). Nothing merged, nothing
submitted.

## 1. Hypothesis

Unchanged from the previous experiment, restated for this signal:
opponent standing supply of a product we're holding should make selling
now beat waiting, when the opponent's *exact* accrued yield (not a flat
max-yield ceiling) says real supply is imminent. Must be able to fail:
if the exact signal still never co-occurs with a real decision point, or
co-occurs but doesn't move revenue, that is a valid, reportable result.

## 2. Baseline

Unmodified `main.py`, current `main` state (`SELL_PRICE_THRESHOLDS`
halved from the BUY_LAND-era retuning, `LIQUIDATION_START_DAY = 19` -
verified directly, not assumed, since an earlier `CLAUDE.md` passage
describes a stale `10`). Self-play, 12 seeds:

```
mean      61303   stdev   11626   median   65058   min 39554   max 75064
```

(12-seed baseline; the original report's 6-seed baseline of 66043 is the
first 6 of these same seeds and matches exactly - `main.py` self-play is
fully deterministic per seed.)

## 3. Treatment

`experiments/candidates/opponent_aware_sell_gate_exact_yield.py`. Same
`should_sell(...)` OR `<sell-now-vs-wait comparison>` mechanism, same
`OPPONENT_AWARE_HORIZON_TURNS = 24` (one day), same isolation guarantee
(byte-identical to baseline whenever the opponent-units guard is zero) as
the previous candidate. The one change: the opponent-units input to the
override is `exact_opponent_standing_yield(obs)` (sum of `tile["yield_units"]`
on the opponent's own tiles) instead of `count_opponent_pipeline(obs)`
(flat `crop_info["max_yield"]` per tile).

**Planting was verified untouched, not just claimed.** `decide_market_actions`
never receives `obs`, only a pre-extracted `opponent_pipeline` dict built
once per turn by `extract_state`'s call to `count_opponent_pipeline`, and
threaded to two `choose_crop` call sites (the PLANT branch in
`choose_unit_action`, and the BUY_SEED restock call inside
`decide_market_actions`). Widening `opponent_pipeline` itself would have
changed both. Instead, this candidate wraps
`base.count_opponent_pipeline` with a function that computes the
exact-yield reading as a side effect into a module-level cache, then
**returns the original, unmodified function's result unchanged** - so
`opponent_pipeline` and both `choose_crop` call sites are provably
byte-identical to baseline. `tests/test_opponent_aware_sell_gate_exact_yield.py::TestPlantingIsUntouched`
asserts this directly (`test_wrapped_return_value_matches_unpatched_function`),
not just by inspection. 16/16 new tests pass; full suite
`python -m unittest discover -s tests`: **236/236 pass** (running both
candidates' test files together required a small test-isolation fix -
see the note under "leakage/robustness" below; not a behavioural change
to either candidate).

## 4. Exact-yield definition

```python
def exact_opponent_standing_yield(obs):
    farms = obs.get("farms") or []
    player = obs.get("player", 0)
    opponent = farms[1 - player] or {}
    supply = {}
    for row in opponent.get("tiles") or []:
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                supply[tile["crop"]] = supply.get(tile["crop"], 0) + tile.get("yield_units", 0)
    return supply
```

`tile["yield_units"]` is the exact counter the engine's own `HARVEST`
handler moves into inventory (`kaggriculture.py:446-462`) and zeroes -
not an estimate, the literal quantity harvestable this instant.

## 5. Observability / leakage check

Every field this candidate reads is one already established as directly
observable in `experiments/opponent_supply_forecast_audit.md` section 1:
`obs["farms"][1-player]["tiles"][*]["yield_units"]`/`["crop"]`/`["kind"]`
- the same shared `farms` object both players already receive each turn.
No `env.steps` replay access, no reach into the opponent's `private`
(shed/seeds/inventories - genuinely unavailable, per the audit), no
future-turn data. `should_sell_opponent_aware_exact_yield` and the sell
loop only ever see the current turn's `market_state`/`day`/`opponent_units`,
matching the previous candidate's structure exactly.

**One thing worth flagging that isn't a leakage risk but is a test-
determinism risk:** both this candidate and the previous one monkeypatch
the same shared `main.decide_market_actions` global at import time.
Running the whole test suite with both candidate test files present
means whichever module a full `unittest discover` run imports last
silently wins for *every* wiring test, not just its own - this
surfaced as a spurious failure in the previous candidate's own test
(`TestDecideMarketActionsOpponentAwareIsWired`) the first time both
files were run together. Fixed by giving each wiring-test class a
`setUp` that re-pins its own candidate's patch immediately before
running (both test files touched, `main.py`/`pricing.py` untouched,
no behavioural change to either candidate - purely test isolation).

## 6. Activation diagnostics

Instrumented every reach of `should_sell_opponent_aware_exact_yield`
(i.e. `not liquidating and not baseline_says_sell` - the only case
`decide_market_actions` calls it for) into `ACTIVATION_LOG`, one record
per check: day, product, exact opponent_units, our held quantity, spot
price, sell threshold, revenue-now/revenue-delayed, whether the signal
was available (`opponent_units > 0`), whether the override fired.

**Self-play, 12 seeds (main.py vs itself, both sides run the candidate):**

| | count |
|---|---|
| total checks (`should_sell` was False, pre-liquidation) | 866 |
| by product | WOOL 849, MELON 17 |
| signal available (`opponent_units > 0`) | 17 / 866 (2.0%) - all MELON |
| override fired | 17 / 17 available (100%) |

**Every one of the 17 available/fired checks is on day 18** (one day
before `LIQUIDATION_START_DAY = 19`), holding 1-5 MELON units, spot price
164-174 (just under the 180 threshold). Concentrated in **2 of 12 seeds**
(seed 8: 8/8 fired; seed 11: 9/9 fired) - the other 10 seeds never had a
positive exact-yield reading at a `should_sell == False` moment at all.

**WOOL never once had a positive signal** at any of its 849 checks
across all 12 seeds - matching `opponent_supply_forecast_audit.md`'s own
co-occurrence probe (0/4 pre-liquidation WOOL glut turns had opponent
supply, small-n but consistent).

**Against `starter` (12 seeds): zero checks at all** - `should_sell` was
never once `False` pre-liquidation in any of the 12 episodes, so the
override never even gets a chance to matter against a non-selling
built-in under the current (halved) thresholds. This matches
`CLAUDE.md`'s existing note that `should_sell` fails "only 0-3 times per
game" against `starter`, now apparently rounding to exactly zero with
current thresholds.

**MELON and STRAWBERRY essentially never produce a `should_sell == False`
moment at all pre-liquidation any more.** In 866 checks across 12
self-play seeds, MELON appears only 17 times (all day 18) and STRAWBERRY,
WHEAT, CARROT, MILK **never appear at all**. Cross-checked against
`SELL_PRICE_THRESHOLDS` (halved during the BUY_LAND-era retuning) versus
`MARKET_PARAMS` base prices: MELON's threshold (180) is 72% of its base
price (250), STRAWBERRY's (90) is 75% of its base (120) - low enough that
ordinary in-season price movement almost never dips under them before
day 19. **This, not the opponent signal's quality, is now the binding
constraint on this gate ever mattering**: the "hold vs. sell" decision
this whole mechanism targets barely exists anymore for MELON/STRAWBERRY
under current thresholds - see section 9.

## 7. Seeded evaluation

**A. Self-play, 12 seeds, candidate vs itself:**

```
mean      61303   stdev   11626   median   65058   min 39554   max 75064
```

**Identical to baseline main.py, seed-for-seed, to the exact dollar** -
including seeds 8 and 11, where 17 real overrides fired. This is not a
measurement artefact (verified: `ACTIVATION_LOG` shows real activation on
those exact seeds); see section 9 for why moving a handful of units'
sale forward by one day, right before a liquidation sweep that would
have caught them the very next turn anyway, can net to exactly zero.

**B. Head-to-head vs `main.py` (non-symmetric, contested market):**

| seeds | matches | mean bank difference | wins |
|---|---|---|---|
| 6 (seeds 0-5, zero activations in this range) | 12 | +0 | 6/12 |
| 12 (seeds 0-11, includes seeds 8 & 11) | 24 | **+76** | **12/24** |

Extending to the seeds where activation actually happens breaks the
exact tie (self-play's symmetry can hide a real effect that shows up
once the two sides diverge) - but the result is a **statistically
negligible +76** on a ~50,000-80,000 bank scale, with an **exactly even
12/24 win rate**. Not a directional win or loss; noise-scale.

**C. Paired comparison vs `starter`, 12 seeds:**

```
mean delta +0, better on 0/12 seeds, sd of deltas 0, standard error 0
```

Exact zero on every seed, and fully explained rather than suspicious:
section 6 already showed zero activation checks occur against `starter`
at all under current thresholds, so baseline and candidate are
byte-identical on this opponent by construction.

## 8. Product-level results

| product | pre-liquidation `should_sell==False` checks (12 self-play seeds) | signal ever available | override ever fires |
|---|---|---|---|
| **MELON** | 17 | **17 (100%)** | **17 (100%)** - but only on day 18, only 2/12 seeds |
| WOOL | 849 | 0 | 0 |
| STRAWBERRY | 0 | - | - |
| WHEAT | 0 | - | - |
| CARROT | 0 | - | - |
| MILK | 0 | - | - |

Per the task's own instruction not to assume universality: **the question
"is the opponent signal useful" only even arises for MELON and WOOL under
current thresholds** - the other four products' `should_sell` gate is
essentially never closed pre-liquidation any more, so there's nothing for
any opponent signal to help with there, independent of signal quality.
Where the question does arise (MELON), the signal is available and fires
100% of the time it's checked - a complete reversal of the old signal's
0/162, exactly as the audit predicted. Where it doesn't fire because it's
never available (WOOL), that also matches the audit's own co-occurrence
finding for that product.

## 9. Mechanism analysis

**Which crops changed:** MELON only, and only during a one-day window
(day 18) immediately preceding the hard liquidation cliff (day 19,
`LIQUIDATION_START_DAY`).

**Earlier or later:** the override sells 1-5 MELON units on day 18 that
the baseline would otherwise have held until day 19's mandatory
liquidation sweep (`liquidating: sell regardless of price`) picks them
up one turn later. This is a **timing shift of about one day, not a net
change in whether or how much gets sold** - both baseline and treatment
sell the same units before the season ends.

**More or fewer units:** no measurable difference in total units sold -
the same shed quantity clears either on day 18 (treatment) or day 19
(baseline), both under a single-digit unit count per event.

**Did realized prices improve:** the logged comparisons consistently show
`revenue_now > revenue_delayed` at the module's fixed 24-turn horizon
(e.g. 687 vs. 620, 507 vs. 450) - the mechanism is doing what it's
designed to do, locally. But the actual baseline alternative isn't "wait
24 turns," it's "wait one turn into a liquidation sweep that sells at
essentially the same spot price" (MELON's price moves gradually enough
day-to-day that selling on day 18 vs. day 19 nets a difference too small
to survive rounding to the dollar in every one of the 17 logged cases,
consistent with the exact self-play zero-effect result in section 7A).

**Concentrated in MELON/STRAWBERRY/WOOL:** only MELON, and only in this
narrow pre-liquidation slice - not because STRAWBERRY/WOOL's underlying
market dynamics are different (the audit found real correlation for all
three), but because **STRAWBERRY never produces a `should_sell==False`
moment at all** under current thresholds, and **WOOL's opponent signal
is never available** when it does.

**Interaction with simultaneous selling:** not observed - none of the 17
logged events coincide with the opponent also holding a SELL order
against the same inventory pool in a way this instrumentation could
detect (the concurrent-selling mechanic `pricing_engine_notes.md`
flagged remains unmodeled here, same as the previous candidate; at 1-5
unit orders the price impact of missing it is small regardless).

**Root cause, stated plainly:** this isn't a failure of the opponent
signal - section 6 already shows it activates and fires exactly as
designed, a real reversal of the previous experiment's 0/162. It's that
`SELL_PRICE_THRESHOLDS`'s halving (a prior, unrelated retuning) closed
off almost every pre-liquidation moment this gate was built to help
with, for the two products (MELON, STRAWBERRY) where the audit found the
signal actually carries information. What's left is a one-day sliver
right at the liquidation boundary, where "sell now" and "the mandatory
sweep tomorrow" are economically almost the same action.

## 10. Conclusion

**B. Exact-yield signal has no measurable effect** on the current sell
gate's performance - with the important qualification that this is
different from the previous experiment's null result in kind, not just
degree, and the difference matters for what to try next:

- The previous signal (`count_opponent_pipeline`) failed because it
  **never activated** (0/162 checks had positive opponent units).
- This signal **does activate**, exactly as the audit predicted (17/17
  = 100% fire rate whenever available), confirming the audit's core
  claim that exact `yield_units` carries real, usable information the
  old flat-max_yield signal didn't.
- It still produces no measurable score effect, because **the decision
  points where it can activate have themselves become vanishingly rare
  and economically thin** under the current, already-halved
  `SELL_PRICE_THRESHOLDS` - not because the signal lacks information.

**Do not generalize this to "opponent-aware selling doesn't work."** The
audit's unconditional correlations (MELON r≈-0.73 with future price at a
4-day horizon) are untouched by this result - they describe information
content, not this specific gate's ability to use it under today's
thresholds. What this experiment actually closes off is narrower: **the
`should_sell`-gate integration point, at the current threshold values, no
longer has enough pre-liquidation "no" decisions left to be worth
augmenting** - a structural finding about the gate's operating window,
not about the signal.

**Recommended next step, smallest first, per the task's own
instruction not to widen scope in this experiment:** none is implemented
here. For the record, two directions worth naming without evaluating
them: (a) re-test this same exact-yield signal against a threshold
configuration where `should_sell` closes more often for MELON/STRAWBERRY
(reproducing this experiment's activation diagnostic first, before
touching thresholds, to confirm the mechanism); (b) per
`opponent_supply_forecast_audit.md`'s own recommendation 4, a cadence/
pacing signal *within* the liquidation window (where `should_sell` is
already bypassed but *how much* to sell each turn still isn't opponent-
aware) is a structurally different integration point that doesn't depend
on `should_sell` ever returning `False` at all - `pricing_engine_notes.md`'s
already-proposed layer 2, with the reverted `experiment/sell-cadence`
branch as prior art to read first.

No changes to `main.py` or `pricing.py`. Nothing merged. Nothing
submitted.
