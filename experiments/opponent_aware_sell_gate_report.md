# Experiment report: does opponent-supply information improve the sell gate?

Branch state: `main`, uncommitted research files only. **Not merged into the
agent. Not submitted to Kaggle. `main.py` and `pricing.py` both untouched**
(`git diff --stat -- main.py pricing.py` empty throughout).

## 1. Hypothesis

Bidirectional, and required to be able to fail: incorporating the
opponent's visible standing-crop supply (`opponent_pipeline`, already
computed every turn by `count_opponent_pipeline` but only ever reaching
`choose_crop`, never the sell decision) into the SELL/no-sell gate changes
expected revenue - in either direction.

Mechanism claimed: when the opponent has substantial visible standing crop
of a product we're holding, waiting is more likely to land us into a
market they've already depressed by the time we'd otherwise sell, so
selling now may beat waiting even when today's spot price doesn't clear
`should_sell`'s existing threshold. When opponent supply is negligible,
the signal should do nothing. The experiment had to be capable of showing
no effect, or a negative one (e.g. selling too early on a signal that
never actually materializes into a real opponent sale, since their shed -
what they actually intend to sell - is never visible, only their standing
crop is).

## 2. Baseline

Unmodified `main.py`, current state (post the land/crew/animal Phase 3
merge and the meta-opponent-finding merge - `LIQUIDATION_START_DAY=19`,
`SELL_PRICE_THRESHOLDS` at their current, roughly-doubled-back-up values).
Self-play, 6 seeds: mean 66,043, stdev 8,652, median 68,417, range
51,327-75,064 (`experiments/selfplay_agent.py main.py 6`).

## 3. Treatment

`experiments/candidates/opponent_aware_sell_gate.py` - a copy of
`main.py`'s `decide_market_actions`, with exactly one behavioural change:
the main sell loop's `should_sell(...)` call is replaced by
`should_sell_opponent_aware(...)`, which is `should_sell(...)` **plus**
exactly one additional way to say yes, and is provably identical to
baseline whenever the opponent has no visible standing crop of the
product in question. No cadence change, no new `SELL_PRICE_THRESHOLDS`
value, no `MAX_SELL_PER_TURN` change, no change to quantity sizing beyond
the one consistency fix needed to make the gate's "yes" actually produce a
non-empty order (section 4).

**Mechanism chosen, and why:** of the four candidate integration points
the task named (modify expected future price / modify expected price
decline / a sell-now-vs-wait comparison / the sell/no-sell gate), the
sell/no-sell gate was chosen, implemented via a short-horizon
(`OPPONENT_AWARE_HORIZON_TURNS = 24`, one day) sell-now-vs-wait comparison
reusing `pricing_v1.compare_immediate_vs_delayed_selling` directly. A
general hold-vs-sell comparison that also reacted to plain town-demand
recovery with zero opponent supply would have been the sell-cadence
experiment, explicitly excluded from this one - the guard
`opponent_units <= 0 -> return False` is what keeps this experiment about
opponent supply specifically, not selling timing in general.
`our_pipeline_supply` is deliberately pinned at `0` in every comparison
call, for the same reason: this experiment isolates opponent supply's
marginal contribution, not our own harvest timing (a separate, already-
built `pricing_v1.py` capability).

## 4. Implementation

`should_sell_opponent_aware(product, quantity, market_state, opponent_units, day, unlocked_shops, start_step)`:

```
if should_sell(product, quantity, market_state):      # unchanged baseline
    return True
if quantity <= 0 or opponent_units <= 0:               # isolation guard
    return False
comparison = compare_immediate_vs_delayed_selling(
    product, inventory, quantity, day, horizon_turns=24,
    our_pipeline_supply=0, opponent_pipeline_supply=opponent_units,
)
return not comparison["delay_is_better"]
```

**A real integration bug found and fixed before any evaluation ran:** the
first draft left `recommend_sell_quantity`'s `min_acceptable_price`
argument as the unchanged fixed `SELL_PRICE_THRESHOLDS` value even when
the sale was authorized via the opponent-aware override. Since the
override only ever fires when spot price is *below* that threshold (the
baseline check already covers the case where it's above), quantity sizing
silently rejected every unit and produced an empty order - the gate said
yes, the sale never actually happened. Caught by
`TestDecideMarketActionsOpponentAwareIsWired`, not by
`should_sell_opponent_aware`'s own unit tests (which correctly tested the
gate in isolation and had no way to see this). Fixed by tracking *why* a
sale was authorized (plain threshold vs. liquidating vs. opponent-aware
override) and using the current spot price as the floor specifically for
the override case - "sell down to today's price, no further," the
minimal floor consistent with a decision that was only ever about whether
today beats waiting.

## 5. Tests

`tests/test_opponent_aware_sell_gate.py`, 9 cases:

- Identical-to-baseline in both directions when `opponent_units == 0`
  (the isolation guarantee the whole experiment depends on), including a
  defensive negative-input case.
- Never suppresses a sell the baseline would already have made.
- Fires on a real (non-mocked) case and agrees exactly with
  `pricing_v1.compare_immediate_vs_delayed_selling` on the same inputs.
- Does **not** fire on every positive `opponent_units` value - tested via
  a mocked comparison result, because at this module's 1-day horizon,
  real market curves in this game make the override fire on almost any
  positive opponent supply once the baseline has already failed (see
  section 7) - a natural counterexample doesn't exist in the reachable
  parameter space, which is itself a finding, not a reason to skip testing
  the branch that says no.
- Quantity/day edge cases.
- End-to-end: the patched `decide_market_actions` actually produces a
  SELL order in a case the unmodified gate would have held (confirms the
  section-4 fix, not just the gate function alone).

Full suite: **220/220 pass** (211 pre-existing + 9 new).

## 6. Evaluation setup

Seeded, reproducible, three harnesses per the project's checkpoint
workflow (`docs/EXPERIMENT_WORKFLOW.md`, `docs/CHECKPOINTS.md`):

```
.venv/bin/python experiments/selfplay_agent.py experiments/candidates/opponent_aware_sell_gate.py 6
.venv/bin/python experiments/selfplay_agent.py main.py 6
.venv/bin/python experiments/head_to_head.py experiments/candidates/opponent_aware_sell_gate.py main.py 6
.venv/bin/python experiments/paired_compare.py main.py experiments/candidates/opponent_aware_sell_gate.py
```

## 7. Results

| harness | seeds | result |
|---|---|---|
| self-play, treatment | 6 | mean 66,043, stdev 8,652, median 68,417, range 51,327-75,064 |
| self-play, baseline (`main.py`) | 6 | **identical to the dollar, every seed** |
| `head_to_head.py` vs `main.py` | 6 (12 matches) | **+0 mean, 6/12 wins** |
| `paired_compare.py` vs `starter` | 12 | **+0 delta on all 12 seeds, sd=0** |

Every number is a hard zero, not "within noise" - this is not a marginal
result requiring a t-test to interpret.

**Diagnostic trace (why, not just that):** instrumented the candidate to
count every time the override was reached and whether it fired, across
multiple seeds and both opponents.

- **Self-play, seed 0:** 114 shed-checks, `should_sell` already `True` in
  all 114 - the override was never even reached.
- **Self-play, seeds 1 and 3:** `should_sell` was `False` often (178 and
  163 times respectively) and the override *was* evaluated (162 and 142
  times, after excluding the liquidation window) - but **in every single
  one of those 162 checks, the opponent's visible standing supply of the
  specific product we were holding was exactly zero**, so the isolation
  guard (`opponent_units <= 0 -> False`) rejected it before the price
  comparison ever ran.
- **Vs. `starter`, 3 seeds:** `should_sell` was `False` only 0-3 times per
  game (a built-in that never sells keeps our own prices high almost all
  season, per `CLAUDE.md`'s long-standing "built-ins inflate everything"
  finding) - and the few times it was `False`, day was already past
  `LIQUIDATION_START_DAY`, where the override path is correctly bypassed
  by design.

**The override fired zero times across every seed and every opponent
tested** - not "rarely," zero.

A separate, hand-constructed scenario matrix (32 combinations of
inventory glut depth x opponent-supply level x held quantity, MELON, using
`pricing_v1` directly) shows the override *is* capable of firing, and
fires reliably (12/32 constructed scenarios) whenever `opponent_units` is
given a positive value directly - confirming the mechanism itself is
implemented correctly. The gap between "fires readily when opponent_units
is supplied" and "never fires in a real game" is entirely explained by the
diagnostic trace above: **real games essentially never produce a
positive `opponent_units` reading for the specific product we happen to be
stuck holding, at the moment we'd need it.**

## 8. Interpretation

The mechanism is implemented correctly and behaves exactly as designed in
isolation - the unit tests and the scenario matrix both confirm this. The
zero-effect result is not a bug in the gate; it is a property of
`opponent_pipeline` as currently defined and of how the two products'
timing actually correlates in play:

- `opponent_pipeline` is a **snapshot** of the opponent's currently-
  standing crop, not their intentions or their shed. In self-play, both
  sides run the identical `choose_crop` logic, which already avoids
  overproducing a crop currently in oversupply (via `estimate_future_price`'s
  own pipeline-supply term). If *we* are stuck holding excess of product
  X, the same scoring logic already discouraged the opponent from having
  X standing at that same moment either - the two conditions this
  experiment needed to co-occur (we're stuck with X, they visibly have X
  growing) are anti-correlated by the very logic both sides share, not
  independent events.
- Against `starter`, the precondition on our own side barely occurs at
  all, for the separate, already-documented reason that a non-selling
  opponent keeps our own market pristine.

This is a genuine, informative negative result about a specific
implementation of the mechanism, not evidence that "opponent supply can
never matter" - see recommendation C below for what a version with a
real chance of firing would need to look like.

## 9. Recommendation

**B. Reject this specific signal, as implemented.**

Evidence support: zero measured effect across three independent harnesses
(self-play, head-to-head, paired vs. `starter`), fully explained by a
direct instrumented trace showing the override's precondition never
co-occurs with a real held-and-unsellable position, on any of the seeds
and opponents tested. This is not "insufficient evidence" (D) - the
diagnostic trace *is* the evidence, and it's decisive about the mechanism,
not just the outcome. It is also not "keep it" (A) - a change with a
mechanically-verified zero opportunity to ever fire in practice is not
worth the added code path regardless of how clean its isolation
properties are.

**A future, more targeted version (not built here, per the instruction not
to proceed automatically) would need to close the actual gap found:**
`opponent_pipeline`'s standing-crop snapshot essentially never lines up
with our own held-and-unsellable inventory. Two directions worth
naming, neither implemented or evaluated:

- Widen the signal from "opponent's *current* standing crop of this exact
  product" to something with more surface area to actually co-occur - e.g.
  overall opponent market pressure across correlated crops, or a longer
  memory of what the opponent has recently harvested/sold (still
  respecting that their shed itself is never visible).
- Test the signal against a genuinely differently-shaped opponent than
  `starter`/self-play - `docs/PUBLIC_META.md`'s reconstructed top-meta
  agent (`experiments/meta_opponent.py`, from a separate, unrelated
  session) runs a visibly different crop program and might produce the
  co-occurrence this experiment never saw. Not run here - this experiment
  intentionally stayed within the checkpoint workflow's standard harnesses
  and did not introduce a new opponent as an additional variable.

Per instructions: no further pricing experiment follows automatically from
this report.
