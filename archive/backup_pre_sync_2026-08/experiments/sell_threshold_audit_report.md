# Sell-threshold audit: is `SELL_PRICE_THRESHOLDS` too permissive?

Follow-up to `experiments/opponent_aware_sell_gate_exact_yield_report.md`,
which closed the opponent-supply track (per instruction, not re-opened
here) and found the real bottleneck was structural: pre-liquidation,
`should_sell` is almost always `True` for MELON/STRAWBERRY under current
thresholds, leaving almost no "hold vs. sell" decision for any
forward-looking signal to influence. This audit asks whether the
threshold *values themselves* are the fix. `main.py` and `pricing.py`
are untouched throughout (`git diff --stat -- main.py pricing.py` empty
at every step). Nothing merged, nothing submitted - this is a report for
a human submission decision, per the task's own instruction to stop and
report rather than decide.

## 1. Historical audit

**Correction to the task's premise, found while auditing, not assumed:**
`SELL_PRICE_THRESHOLDS` is **not currently halved.** Direct inspection of
the checked-out `main.py` (`grep SELL_PRICE_THRESHOLDS main.py`) plus
`git blame` on every constant the halving commit touched shows current
`main.py` already sits at the **original, pre-halving values** - the
halving happened, was live for a period, and was walked back at some
point with no revert commit recorded. This matters directly for how
"candidate B" below is constructed.

**The halving:** commit `9c52c09` ("experiment: land + crew + animals +
early selling, as one change", Spidey-Acer, 2026-08-18), bundled with
`LIQUIDATION_START_DAY` 19→10, `SHED_FORCE_SELL_THRESHOLD` 70→40,
`MAX_HANDS_PER_DAY` 8→15, `MAX_ANIMALS` 3→4, and `BUY_LAND`. Stated
reason (commit message): *"a 75-tile farm outproduces the old gates"* -
a much bigger farm's production needed a lower price bar to actually
clear before season end. Reported evaluation at the time, and the
commit's own warning that it doesn't agree across harnesses:

| harness | result |
|---|---|
| paired vs `starter`, 12 seeds | +4,828, 8/12, t=2.18 |
| head-to-head, 24 matches | +1,652, 14/24 |
| self-play, 6 seeds | mean up, but stdev 6,329 vs 3,481 (1.8x worse) |

| product | original | halved (9c52c09) |
|---|---|---|
| WHEAT | 20 | 10 |
| CARROT | 25 | 12 |
| TOMATO | 40 | 20 |
| STRAWBERRY | 90 | 45 |
| MELON | 180 | 90 |
| EGG | 35 | 17 |
| WOOL | 140 | 70 |

**Current `main.py`** (verified directly): `LIQUIDATION_START_DAY=19`,
`SHED_FORCE_SELL_THRESHOLD=70`, `MAX_HANDS_PER_DAY=8`, and
`SELL_PRICE_THRESHOLDS` at the **original** table above - i.e. every
constant from that bundle was reverted except `MAX_ANIMALS=4` and
`BUY_LAND` (`decide_land_orders`) itself, which are still live. No
"Revert" commit was found for the specific reversion; a later,
explicitly **NOT FOR MERGE** experiment (`9a6a5c6`, porting a sell-or-
hold cadence branch) references *"Swept 13/16/19/21/23/25/27: 19 is an
interior peak, not an edge effect"* for `LIQUIDATION_START_DAY` - direct
evidence the team re-swept and re-confirmed 19 at some point, consistent
with (though not conclusive proof of) how the thresholds ended up back
at their original values too. **`CLAUDE.md`'s section describing the
halving as currently shipped is stale and should be corrected** - flagged
here, not fixed in this pass (out of scope: this audit doesn't edit docs
outside its own deliverable).

**Practical consequence for this audit:** "current baseline" and
"pre-halving" are the *same* configuration today. Candidate B below
therefore tests the *other* historical value set (the halved one) as a
genuinely distinct alternative, not a no-op reproduction of current
behaviour.

## 2. Candidate set

Per instruction, a small set, not a grid:

- **A - current baseline.** Unmodified `main.py`.
- **B - historical permissive** (`experiments/candidates/sell_thresholds_historical_permissive.py`).
  The exact `9c52c09` halved table, reproduced verbatim, isolated from
  every other change that commit bundled (land/crew/animals/liquidation
  day are all untouched `main.py`).
- **C - data-driven stricter** (`experiments/candidates/sell_thresholds_stricter.py`).
  **Not** an interpolation between A and B - moves in the *opposite*
  direction, justified by data gathered specifically for this audit (see
  below), because that data shows B's direction is very unlikely to help
  and the task explicitly said not to assume the historical values were
  better.

Measured pre-liquidation spot-price distribution (6 self-play seeds,
`main.py` vs itself, day < 19 only - `experiments/price_dist_probe`,
not committed, reproducible from this report):

| product | min | p10 | p25 | median | p75 | p90 | max | base price | current threshold |
|---|---|---|---|---|---|---|---|---|---|
| MELON | 171 | 206 | 212 | **260** | 268 | 271 | 272 | 250 | 180 |
| STRAWBERRY | 120 | 132 | 147 | **182** | 214 | 234 | 263 | 120 | 90 |
| WOOL | 116 | 141 | 189 | **199** | 215 | 234 | 243 | 200 | 140 |
| WHEAT | 25 | 29 | 31 | 35 | 39 | 42 | 46 | 25 | 20 |
| CARROT | 35 | 35 | 35 | 36 | 37 | 41 | 46 | 35 | 25 |

**MELON's pre-liquidation median (260) is above its own base price
(250)** - the market spends most of the season *undersupplied*, not
oversupplied, and the current threshold (180) sits below even the 10th
percentile (206). That is the direct, measured reason `should_sell`
almost never says no for MELON (`opponent_aware_sell_gate_exact_yield_report.md`,
17/866 checks): the bar isn't close to where price actually trades.
STRAWBERRY and WHEAT show the same pattern relative to their own
thresholds. Candidate C raises each threshold to roughly its own
measured 25th percentile (rounded): WHEAT 20→30, CARROT 25→35,
STRAWBERRY 90→145, MELON 180→210, WOOL 140→190. TOMATO/EGG/MILK are left
untouched - no measured price series behind TOMATO (essentially never
planted, per `CLAUDE.md`'s closed TOMATO-scoring investigation) or EGG
(no GOOSE in `ACTIVE_ANIMALS`), and MILK's sell gate was already recorded
as a measured no-op at the current animal mix (commit `cc9645d`) -
changing a threshold with no data behind it would be exactly the kind of
guess this audit was asked not to make.

Both candidates change **only** `SELL_PRICE_THRESHOLDS`. Verified, not
just asserted: `tests/test_sell_thresholds_candidates.py` checks both
candidates' exact tables, that every other touched-by-9c52c09 constant
(`LIQUIDATION_START_DAY`, `MAX_HANDS_PER_DAY`, `SHED_FORCE_SELL_THRESHOLD`,
`MAX_ANIMALS`) is untouched, and the intended monotonic direction (B
never stricter than baseline, C never more permissive than baseline, for
every product each touches). **One real bug caught by this test file
before it ever reached evaluation:** candidate C's first draft built its
"leave unchanged" values (TOMATO, EGG) by copying `dict(base.SELL_PRICE_THRESHOLDS)`
at import time - since candidate B *also* monkeypatches that same shared
module global, running both candidates in one process silently let
whichever one imported last determine C's "unchanged" values. Fixed by
hardcoding the literal original numbers instead of reading the mutable
global. Full suite after the fix: **245/245 pass.**

## 3. Interaction with the existing pricing backbone

No mechanism was changed - verified by inspection, not just claimed.
`should_sell` still does exactly one thing (`price >=
SELL_PRICE_THRESHOLDS.get(product, DEFAULT_SELL_THRESHOLD)`); once it
(or liquidation) says yes, `recommend_sell_quantity` still walks the same
per-unit price path and still stops at the same
floor-of-the-turn logic, just handed a different `min_acceptable_price`
input. `estimate_future_price`/`pricing.py` is never called from the
sell gate at all in current `main.py` (confirmed again here, matching
`pricing_engine_notes.md`'s original finding) - so "does this let the
forward-looking pricing backbone influence selling" has a mechanical
answer: **no capacity for that exists on the sell/no-sell gate today,
threshold value notwithstanding.** What a threshold change *can* do is
create more `should_sell == False` moments - the raw material a future,
separate experiment would need to route through a real forecast (out of
scope here, and explicitly not built). This audit only tests whether the
threshold value alone, still gated on nothing but today's spot price,
helps.

## 4. Controlled evaluation

Same three harnesses as the prior experiments, 12 seeds each.

| | self-play (candidate vs itself) | head-to-head vs `main.py` (24 matches) | paired vs `starter` (12 seeds) |
|---|---|---|---|
| **A - baseline** | mean 61,303 / stdev 11,626 / median 65,058 / range 39,554-75,064 | - | - |
| **B - historical permissive** | mean 61,263 / stdev 11,619 / median 64,955 | **+312 mean, 13/24** | **+0 exact, 0/12, sd=0** |
| **C - stricter** | mean 60,490 / stdev 11,361 / median 62,352 | **-956 mean, 10/24** | **+2 mean, 6/12, sd=2, t=3.32** |

**Read `better on` before the t-value, per this repo's own standard.**
B's paired result is an exact +0 on every one of 12 seeds (against
`starter` the gate essentially never binds regardless of threshold, so
lowering an already-non-binding bar changes nothing - consistent with
`opponent_aware_sell_gate_exact_yield_report.md`'s finding of zero
`should_sell==False` checks against `starter` at all). C's paired result
has a "significant" t=3.32, but the underlying deltas are **+2 to +3
dollars** on a ~75,000-dollar bank, and the win count is an exact 6/12
coin flip - textbook noise dressed up by a tiny, consistent-magnitude
delta, not a real effect (the harness's own guidance: *"read `better on`
first"*).

**Neither candidate clears the bar.** B is statistically indistinguishable
from baseline everywhere it was measured (self-play Δ-40, head-to-head
+312/13-24 - barely above a coin flip, paired exact zero). C is flat-to-
negative on every harness that has any contested market at all
(self-play Δ-813, head-to-head **-956/10-24** - losing more often than
winning, on the mean too) and negligible-to-meaningless against
`starter`. This is not "harnesses disagree" (the pattern that has
previously flagged a real, ladder-relevant effect in this repo) - both
contested-market harnesses agree, in the same (non-positive) direction,
for both candidates.

## 5. Behavioral mechanism (candidate C, the one that actually moved)

`experiments/sell_threshold_behavior_diag.py`, 8 self-play seeds,
baseline vs. candidate C, both in self-play so the only difference is
each side's own thresholds. Sell events/units are reconstructed from
shed-quantity deltas turn-to-turn (a lower bound / approximation, not an
exact SELL-order log - the observation has no action log, per
`opponent_supply_forecast_audit.md`'s observability section - good
enough for a same-seed relative comparison, not for exact revenue
accounting):

| | baseline | candidate C | Δ |
|---|---|---|---|
| final reward (mean) | 64,225 | 63,538 | **-687** |
| MELON sell-events | 5.5 | 6.1 | more, smaller sells |
| MELON units moved | 58.4 | 58.8 | **~unchanged** |
| WOOL sell-events | 16.1 | 17.9 | more, smaller sells |
| WOOL units moved | 63.5 | 63.5 | **~unchanged** |
| CARROT sell-events | 1.9 | 2.6 | more, smaller sells |
| MELON avg pre-liq shed qty | 0.17 | 0.37 | held longer |
| WOOL avg pre-liq shed qty | 0.65 | 2.64 | held ~4x longer |
| cash @ day 19 | 5,737 | 4,606 | **-1,131** |
| cash @ day 29 (final) | 58,549 | 57,553 | **-996** |

**The mechanism is exactly what candidate C was designed to produce, and
it doesn't pay off.** `should_sell` does say no more often (more sell
events, inventory held noticeably longer pre-liquidation, especially
WOOL), and cash arrives later (day-19 checkpoint down ~$1,131). But
**total units sold is essentially unchanged** for every product - nothing
is being left permanently unsold or force-dumped differently; the
liquidation-day sweep (unmodified, day 19) still clears whatever's held
regardless of threshold. So the effect isn't "sell more" or "sell less",
it's purely **timing** - hold a bit longer, then sell into whatever price
happens to be there later - and on average that timing shift **cost
slightly more than it gained** (-996 final cash for the same volume).

**This is a coherent, generalizable finding, not just a losing number:**
a flat threshold bump can't tell "price is likely to rise, worth
waiting" from "price is likely to fall, sell now" - it just raises the
bar uniformly, so it holds in both cases indiscriminately. Given MELON's
own price series is noisy around (and often above) its base price rather
than trending, "wait longer" has no systematic edge to capture, only
variance to eat. This matches `pricing_engine_notes.md`'s original,
still-unimplemented recommendation: the fix that could plausibly work is
a genuinely forward-looking hold-vs-sell comparison
(`estimate_future_price`-based), not a better constant on the same blind
gate - which is exactly the mechanism this task's own constraints put
out of scope ("do not redesign the entire pricing system").

**MELON/STRAWBERRY/WOOL specifically**, per the task's emphasis: MELON
and WOOL both show the held-longer pattern clearly (WOOL most of all,
4x); STRAWBERRY's pre-liquidation shed quantity stayed at 0.01 in *both*
arms - it essentially never reaches a nonzero pre-liquidation shed
position at all in self-play (matching the exact-yield report's finding
that STRAWBERRY never produced a single `should_sell==False` check),
so raising its threshold from 90 to 145 had no realistic opportunity to
matter in this sample regardless of the number chosen.

## 6. Recommended candidate

**None. Do not submit either.** Per the task's own instruction: *"If the
results are ambiguous, do not force a conclusion."* This is that case,
and the evidence is consistent enough across harnesses to call it
directly rather than hedge:

- **B (historical permissive):** statistically flat everywhere measured.
  Reintroducing the halved values does not recreate whatever benefit the
  original bundled `9c52c09` change reportedly had (that change bundled
  land/crew/liquidation-day/threshold changes together; isolated to
  thresholds alone, on today's already-different other settings, it does
  nothing).
- **C (data-driven stricter):** creates real, measurable behavioral
  change (more holding, later cash) exactly as designed, but that change
  costs slightly more than it gains, consistently, on both harnesses
  with a contested or self-competing market (self-play, head-to-head).
  Not a "close call rescued by more seeds" pattern - both point the same
  direction.

**The audit still answers the task's key question, just not with a
threshold recommendation:** *"Can a better sell/no-sell threshold
materially improve performance by letting the agent wait for better
future prices when appropriate?"* - **No, not via a flat constant.** The
constant can't distinguish "wait, price is about to recover" from "sell
now, price is about to fall"; it can only move the average bar, and
moving it (either direction) doesn't help. The forward-looking machinery
that *could* make that distinction (`estimate_future_price`,
`compare_immediate_vs_delayed_selling` in `pricing_v1.py`) already
exists and is already wired into the *planting* decision - it has simply
never been connected to the *sell* gate itself, which is a structurally
different, larger change than this task's scope ("only investigate the
sell threshold / sell gate" as a constant) allows.

**Exact change required if either were to ship anyway (not
recommended):** for B, in `main.py`, replace the `SELL_PRICE_THRESHOLDS`
dict literal (currently `{"WHEAT": 20, "CARROT": 25, "TOMATO": 40,
"STRAWBERRY": 90, "MELON": 180, "EGG": 35, "WOOL": 140}`) with
`{"WHEAT": 10, "CARROT": 12, "TOMATO": 20, "STRAWBERRY": 45, "MELON": 90,
"EGG": 17, "WOOL": 70}`. For C, with `{"WHEAT": 30, "CARROT": 35,
"TOMATO": 40, "STRAWBERRY": 145, "MELON": 210, "EGG": 35, "WOOL": 190}`.
Both are one-dict-literal changes, nothing else in `main.py` moves. Given
section 4-5's results, neither change is recommended for today's
submission.

Full test suite (`python -m unittest discover -s tests`): **245/245
pass.** `main.py` and `pricing.py` untouched. Nothing merged, nothing
submitted.
