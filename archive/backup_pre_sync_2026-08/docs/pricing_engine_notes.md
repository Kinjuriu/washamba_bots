# Pricing backbone audit: what it predicts, what it assumes, what it ignores

Audit only — no code changed. `main.py` was read but not modified; `pricing.py`
was not redesigned, only inspected against its own tests, the research
notebook, and the installed engine source
(`.venv/lib/python3.13/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py`,
cited by line number below). This closes the dangling reference in
`pricing.py`'s own module docstring ("see docs/pricing_engine_notes.md for
the full write-up"), which pointed at a file that didn't exist yet.

## TL;DR

- The price-mechanics core (`market_price`, `price_path_for_sale`, town
  demand) is a faithful, tested reproduction of the engine. This part is
  solid.
- **The forecasting layer (`estimate_future_price`, opponent-pipeline
  awareness) is wired into the *planting* decision (`choose_crop`) but not
  into the *selling* decision.** `decide_market_actions` receives
  `opponent_pipeline` as an argument and only ever forwards it to
  `choose_crop` — the SELL loop above it never reads the variable sitting
  in its own scope. This is the single largest, cheapest-to-close gap.
- **The actual sell/no-sell gate (`should_sell`) is still a flat spot-price
  threshold with no forward-looking information at all** — no future
  price, no opponent activity, no explicit inventory-pressure signal, no
  time-remaining signal beyond the separate hard `LIQUIDATION_START_DAY`
  cutoff.
- **A mechanic the backbone doesn't model at all, found while reading the
  engine source for this audit (not previously documented anywhere in this
  repo): same-turn concurrent selling.** When both players SELL the same
  product in the same turn, the engine quotes and commits their orders in
  true per-unit lockstep against a *shared* inventory
  (`kaggriculture.py:583-628`) — not sequentially. `price_path_for_sale`
  only ever walks *our own* order in isolation. This affects the live
  `recommend_sell_quantity` call every turn, not just the forecast.
- A near-identical "hold vs. sell now" layer was already built and merged
  once (`experiment/sell-cadence`), then reverted the same day with no
  reason recorded in the revert commit. Any new experiment in this space
  should read that branch first, not rebuild it blind.

## Method

Read in this order: `pricing.py` in full; `main.py`'s inlined copy of the
same functions (`main.py:196-430`) and every call site that touches them
(`choose_crop`, `decide_market_actions`, `should_sell`,
`count_opponent_pipeline`, `count_pipeline_supply`); `tests/test_pricing.py`
and `tests/test_inlined_pricing.py`; the markdown cells of
`notebooks/pricing_analysis_v0.ipynb`; `experiments/forward_pricing_experiment_report.md`;
and the engine's own `market_price`, `_refresh_prices`, `_town_consume`, and
— not previously cross-referenced anywhere in this repo's docs —
`_process_market` (`kaggriculture.py:544-628`), which is where the
same-turn concurrency finding below comes from.

## Audit, by function

### 1. Current inventory → price (`market_price`)

**Predicts:** the exact spot price for one unit at a given inventory level,
via `price = base ± amp * shape(|inv - I0|)`, floored at $1
(`pricing.py:123-142`).

**Fidelity:** exact. `pricing.py` calls the engine's own `market_price`
directly when the import succeeds, and its fallback reproduction is
line-for-line the same formula (`kaggriculture.py:192-206`). Verified
numerically, not just read, by `tests/test_pricing.py::TestMarketPriceMatchesEngine`
across the full inventory range for both code paths.

**Assumptions / what it ignores:** none within its own scope — it is a pure
function of `(item, inventory)`. Everything the rest of this audit finds
missing is missing *upstream or downstream* of this function, not in it.

### 2. Multi-unit price paths (`price_path_for_sale`)

**Predicts:** the sequence of per-unit prices realised by selling `quantity`
units of one item in one order, re-quoting from the running inventory after
each unit, with the engine's own rule that a sale landing at the $1 floor
does not add inventory (so every unit after the floor is hit also prices at
$1) — `pricing.py:145-166`, matching `kaggriculture.py:653-661`.

**Fidelity:** exact for a *single-player, single-order* walk. Confirmed by
`tests/test_pricing.py::TestPricePathForSale` (non-increasing path, correct
inventory growth, floor behaviour) and by the notebook's section 6 (average
realised price for orders of 1/5/10/25/50 units).

**Assumption that matters, found reading the engine source (not previously
documented):** this function assumes our order is the *only* thing moving
the market during the walk. The real engine's `_process_market`
(`kaggriculture.py:544-628`) processes **both players' SELL orders for the
same product in true per-unit lockstep** when both submit one in the same
turn — at each step, both players are quoted against the *same* pre-commit
inventory, both commit, *then* inventory updates once
(`kaggriculture.py:590-628`, explicit comment: "Both players see the same
pre-commit inventory for this unit"). If the opponent is also selling
MELON this turn, our order does not walk the price path alone — it shares
each step with theirs, and the smaller of the two orders exhausts first,
after which only the excess of the larger order continues walking alone.
`price_path_for_sale` has no way to represent this at all; it can only
model "we are the only seller this turn."

### 3. Town demand (`apply_town_demand`)

**Predicts:** how much a product's market inventory drains from Town Center
and shop consumption alone, over a given number of engine steps, with no
player orders involved (`pricing.py:169-199`).

**Fidelity:** exact reproduction of `_town_consume`
(`kaggriculture.py:728-749`) — same two independent interval checks
(`step % shop_interval == 0`, `step % center_interval == 0`), same
single-product-shop 2x rule, same `TOWN_CENTER_PRODUCTS` exclusion of
FERTILIZER. Verified by `tests/test_pricing.py::TestApplyTownDemand`.

**Assumptions, self-documented and correctly flagged in the code itself:**

- `unlocked_shops` is a **frozen snapshot** passed in by the caller. Future
  shop unlocks are stochastic (per `CLAUDE.md`, shops unlock "with
  replacement" as the season progresses) and are not modelled — the
  docstring calls this out explicitly: "treat this as 'if no new shop
  unlocks in this window.'" Real recovery from a glut is therefore *at
  least* as fast as this function predicts, possibly faster, never slower.
- `start_step` has to be supplied correctly (the real `obs["step"]`) for
  the interval phase to line up with what the engine will actually do —
  the function has no way to detect a wrong value.

### 4. Future-price estimation (`estimate_future_price` / `simulate_single_product`)

**Predicts:** what a product will be worth `turns_ahead` steps from now,
given how much of it we and an assumed opponent add to the market *up
front*, then town demand draining/growing inventory over the window
(`pricing.py:275-390`).

**Fidelity:** internally consistent composition of the two verified pieces
above (it is literally `price_path_for_sale` → `price_path_for_sale` again
for the opponent → `apply_town_demand` → `market_price`). Verified by
`tests/test_pricing.py::TestSimulateSingleProduct` and
`TestEstimateFuturePrice` (monotonicity: more turns ahead never reduces
recovery).

**Assumptions, two of them material:**

- **Both `our_pipeline_supply` and `opponent_pipeline_supply` land
  instantly at turn zero**, not spread across the window before the actual
  harvest/sale date — explicitly flagged in the docstring as "a
  deliberately simple (and slightly pessimistic on price) approximation."
  Notebook section 10 repeats this as an open item.
- **The two supplies are modelled sequentially — ours fully processed,
  then the opponent's fully processed on top** (`simulate_single_product`,
  `pricing.py:238-253`) — not interleaved per-unit the way `_process_market`
  actually processes two same-turn orders (see item 2 above). For a
  multi-day-ahead forecast this sequencing detail matters much less than
  it does for a same-turn sell decision, since the forecast only cares
  about aggregate quantity landed by a future date, not step-by-step
  contestation — but it is still not what the engine does, and nothing in
  the codebase currently measures how much the approximation costs.

### 5. Opponent supply

**What's available:** `count_opponent_pipeline(obs)` (`main.py:1629-1661`)
reads the opponent's own visible tiles every turn — everything currently
`PLANT`ed on their side of the board — as a **lower bound** on what they
will bring to market (their shed is private and never visible, per
`CLAUDE.md`). This is computed once per turn inside `extract_state` and
stored as `state["opponent_pipeline"]` (`main.py:1014`).

**Where it's actually used:** `decide_market_actions` receives
`opponent_pipeline` as a parameter (`main.py:1872`) and forwards it to
exactly one place — `choose_crop` (`main.py:2000-2002`), which feeds it
into `estimate_future_price`'s `opponent_pipeline_supply` argument
(`main.py:1781`) when scoring what to plant next.

**What it never touches: the sell decision.** The SELL loop inside the
same function (`main.py:1885-1954`) never reads `opponent_pipeline` at
all, despite it being a variable already in scope. `should_sell` doesn't
take it as an argument; `recommend_sell_quantity`'s call
(`main.py:1945-1951`) passes only `inventory.get(product, 10000)` — the
live spot inventory, with no opponent-activity adjustment. This is not a
missing capability, an unvisible signal, or a hard data problem — it is
data the code already computes and already threads to a neighbouring
decision, just not to this one.

**A caveat on what the signal is worth even where it is used:** it's a
lower bound on *standing crop*, not shed inventory, and it says nothing
about *when this turn* the opponent will actually submit a SELL order for
it — `choose_crop`'s forecast treats it as landing all at once regardless
(item 4 above).

### 6. Recommended sell quantity (`recommend_sell_quantity`)

**Predicts:** how many units of a product we could sell *this turn* before
the price path drops below a minimum acceptable price, walking the same
`price_path_for_sale` mechanic and stopping at the first unit that would
quote below the floor (`pricing.py:320-355`).

**Fidelity:** exact for the single-seller case (same caveat as item 2 —
doesn't model a same-turn opponent order on the same product).

**Wiring status — this one *is* live, and its own docstring is stale about
it.** Both `pricing.py`'s and `main.py`'s copies of this function still
say "does not call `should_sell()` and is not wired into
`decide_market_actions()`" (`pricing.py:332-333`, `main.py:405-406`). That
was true when `pricing.py` was first written, but it has not been true
since the forward-pricing experiment merged
(`experiments/forward_pricing_experiment_report.md`): `decide_market_actions`
calls `recommend_sell_quantity` directly to size every SELL order once
`should_sell()`'s separate yes/no gate has already said yes
(`main.py:1945-1951`). The docstring in both files should be corrected —
small, but worth fixing since it actively misleads about what's already
shipped.

**What it still doesn't do:** decide *whether* to sell, or *when* — it
only sizes an order once the decision to sell has already been made
elsewhere by `should_sell`.

### 7. Selling cadence (`should_sell` + `LIQUIDATION_START_DAY` + `MAX_SELL_PER_TURN`)

**What actually gates a sale, end to end, as shipped today:**

1. `should_sell(product, quantity, market_state)` (`main.py:1800-1814`) —
   `True` iff the *current spot price* clears a fixed
   `SELL_PRICE_THRESHOLDS[product]` constant. No history, no forecast, no
   opponent signal, no notion of how much is held or how long until it's
   worthless.
2. Once `day >= LIQUIDATION_START_DAY`, the threshold gate is bypassed
   entirely — "sell regardless of price" (`main.py:1883`, `1921-1925`).
   This is a single hard day cutoff, not a gradient.
3. `SHED_FORCE_SELL_THRESHOLD` is a second, independent override — once
   shed occupancy crosses it, force a sale regardless of the threshold too
   (overflow valve, not a price signal).
4. Order size, once (1) or (2) says yes, comes from `recommend_sell_quantity`
   (item 6), capped by `MAX_SELL_PER_TURN[product]` — a fixed per-product
   constant, hand-tuned (notebook section 6 finds it "broadly consistent
   with" the real order-size knee for melon/strawberry but explicitly notes
   it "was not derived from this data").

**What this means structurally:** "cadence" as shipped is really **two
step functions layered on top of a spot-price threshold** — a per-product
price floor, and a day-19 all-bets-off cliff — with no continuous signal
connecting them. There is no representation anywhere in the live decision
path of "the price is falling and about to cross my threshold, sell now
while I still can," or "the price is above threshold now but about to
recover further, worth holding one more turn," or "I'm sitting on so much
of this that even selling at the cap every remaining day won't clear it."

## The central gap, stated plainly

The deterministic backbone answers the pricing *mechanics* question well:
given an inventory level, a quantity, and a time horizon, it tells you
almost exactly what the engine will pay. What it does not answer — and
what nothing in the current wiring asks it to answer — is the actual
strategic question: **for the goods sitting in the shed right now, is this
turn better or worse than a later turn to sell them, given where the price
is headed and what the opponent is doing?**

That comparison — `value_now` vs. `value_hold(horizon)` — is exactly what
`estimate_future_price` was built to compute, and it is already wired into
one decision (crop choice) but not the other (sell timing), even though
the sell decision runs far more often and is the one actually converting
production into bank balance.

## Prior art: this has already been attempted once

`experiment/sell-cadence` (still on `origin`, not merged) built almost
exactly this layer: `estimate_sell_or_hold_value(item, quantity, inventory,
day, pipeline_supply, opponent_pipeline_supply, ...)` compared
`price_path_for_sale` at the current inventory against
`estimate_future_price`'s forecast at a `SELL_HORIZON_DAYS` horizon, plus
an `inventory_pressure` signal (carried stock relative to what could
plausibly still be sold in the remaining days at the per-turn cap) and a
continuous `cadence_urgency(day)` replacing the hard `LIQUIDATION_START_DAY`
cliff with a smooth ramp — directly motivated by the same replay evidence
already in this repo (`docs/REPLAY_ANALYSIS.md`) that real top-ladder play
shows no day-22 selling cliff.

It was merged to `main` (`87573fe`) and reverted the same day (`8608cac`),
with **no reason recorded in the revert commit message**. Before building
anything new in this space, that gap should be closed — either by finding
the reason in team chat/PR discussion outside git, or by re-measuring the
branch fresh against current `main` to see whether the revert was about a
regression, a conflict, or something unrelated to the mechanism itself.
Redoing this work blind risks reproducing whatever already failed.

## Proposed next experimental layer (proposal only — nothing implemented)

In order of cost to test, cheapest first:

1. **Thread `opponent_pipeline` into the sell decision.** The data is
   already computed and already in scope inside `decide_market_actions`
   (item 5). Lowest-cost possible experiment: pass it through to a
   sell-side `estimate_future_price` call and see whether knowing the
   opponent's visible standing crop changes anything measurable about sell
   timing, before building any new formula. This alone isolates whether
   the "opponent supply" gap is worth more work.

2. **Replace `should_sell`'s flat threshold with a hold-vs-sell-now
   comparison**, reusing `estimate_future_price` exactly as `choose_crop`
   already does, at a short horizon (a few turns, not the crop's full
   growth cycle) — this is the mechanism `sell-cadence` already built.
   First step here should be reconstructing *why* it was reverted, not
   re-implementing from scratch.

3. **Model same-turn concurrent selling explicitly.** A new function
   alongside `price_path_for_sale` that walks two orders in true per-unit
   lockstep (mirroring `_process_market`'s actual loop) against a shared
   inventory, for the case where we have a reason to believe the opponent
   is selling the same product this turn (e.g., both players' crops matured
   on the same day, or late-season liquidation is a shared incentive for
   both sides). This is the one gap found in this audit that isn't already
   named anywhere else in the repo's docs or prior experiments — worth its
   own small, isolated measurement (does ignoring it produce a
   measurably-wrong `recommend_sell_quantity` in self-play, where a
   same-turn double-sell is actually reachable?) before deciding whether it
   is worth modeling at all.

4. **Derive `MAX_SELL_PER_TURN` and `SELL_PRICE_THRESHOLDS` from the price
   curves instead of hand-tuning them**, per the notebook's own section 12
   proposal — lowest priority of the four, since the notebook's section 6
   finding is that the current hand-tuned caps are already "broadly
   consistent with" what the data supports; this would tighten an
   already-roughly-correct constant, not close a structural gap.

Each of these should be measured in isolation (`paired_compare.py` /
`head_to_head.py`, per `CONTRIBUTING.md`'s evidence standard) before being
combined — the `sell-cadence` revert is itself a reminder that a plausible
mechanism is not evidence it helps.

## Test coverage as it stands

`tests/test_pricing.py` (24 cases) verifies the mechanics against the live
engine directly. `tests/test_inlined_pricing.py` (5 cases) guards that
`main.py`'s copy never numerically drifts from `pricing.py`'s, and that
`main.py` still does not import `pricing` (the single-file submission
constraint). No test in either file exercises same-turn concurrent
selling, opponent-supply-in-the-sell-decision, or a hold-vs-sell-now
comparison — consistent with this audit's finding that none of the three
are wired into any live decision yet.
