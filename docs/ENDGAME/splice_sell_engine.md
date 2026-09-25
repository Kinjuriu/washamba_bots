# Splice sell engine: cadence proof, price model, diagnostic (Builder A, 25 Sept)

Scope: the market brain the day-8 controller calls (`experiments/splice/price_model.py`, `experiments/splice/sell_engine.py`). Build contract: `docs/ENDGAME/splice_build.md`. Engine: kaggle-environments 1.32.7, `kaggriculture.py`. Where FABLE_IDEAS and the engine disagree, the engine wins and section 5 says so.

## Summary

- **Price model is exact.** `quote` equals the engine's `market_price` on every inventory tried, with 0 mismatches in 560,009 evaluations. `sell_revenue`, `buy_cost`, `drain_per_step` and `project` match the engine's own `_process_market` and `_town_consume`, including 6,471 of 6,471 drains in a real episode.
- **Cadence, proved: the first post-drain call is `obs["step"] % 4 == 1`.** That is the action at replay row ≡ 2 (mod 4). FABLE's "hour ≡ 2" is the row index; keying on `obs["hour"] % 4 == 2` would sell one step late.
- **Engine defaults are FABLE §1, with one measured correction.** Healthy markets are sold on the cadence turn in drain+headroom slices. The decaying quote threshold is replaced by a **glut rule**: when no shop consumes a product, or its market sits more than half a day of drain above I0, the whole release sells on any turn. The threshold held 29 milk into a crash and sold it at 1-5 while the tape sold at 32-79. That mechanism is a property of the market, not of the opponent.
- **Diagnostic answer: no, the engine does not realize higher prices than the tape.** On seeds 900-907, same-day matched sales:
  - Default: wool +0.6, milk -4.0, strawberry -0.7 per unit.
  - Mirror-tuned alternative (every turn, contested products sold whole): wool +1.1, milk -1.4, strawberry +0.6 per unit, which is parity.
- **The alternative is not the default, on purpose.** Its edge comes from W3 dropping the same goods on the same turn as us, which a non-tape controller will not reproduce. The same goes for the default's bank loss (0-16), which is W3's own tape purchases failing on shifted cash. The brief said mirror desync is not a reason to change the engine, so the switch (`healthy_phases`, `contested_dumps`) is documented here and the coordinator makes the call.

## 1. The cadence, proved on the engine

`experiments/splice/_probe_cadence.py` (seed 900, plus seed 901 for wool, the first seed with a YARN_STORE):

| check | result |
|---|---|
| A. Undoctored pass-vs-pass episode: every market-inventory change, attributed to the interpreter call that produced it | all 2,292 consumed units at calls with `step % 4 == 0`; 0 at other phases |
| A. `drain_per_step` vs the real change, every product and call | exact on 6,471 of 6,471 |
| C. `env.steps[i][0]["action"]` equals the action decided from obs step `i-1` | 719 of 719 (from obs step `i`: 0 of 718) |
| B. Every realized sale price vs the quote on the deciding observation's inventory | 575/575 milk, 503/503 strawberry, 431/431 wool |

For B, seat 0 sells 1 unit of each premium product every step once a consuming shop is unlocked. The only doctoring is 600 units of each product in seat 0's starting shed. Results over complete drain cycles (obs steps 4k+1 to 4k+4) with no $1 sale:

| product | cycles | phase 1 paid the most | mean price, phase 1 / 2 / 3 / 0 |
|---|---|---|---|
| MILK | 84 | 84 of 84, strictly | 44.0 / 41.8 / 39.7 / 37.6 |
| STRAWBERRY | 102 | 102 of 102, strictly | 61.5 / 59.5 / 57.6 / 55.5 |
| WOOL (seed 901) | 107 | 107 of 107 (93 strictly, 14 ties from rounding on the flat log curve below I0) | 194.8 / 193.5 / 192.2 / 190.7 |

The mechanism, read from the engine: `interpreter` applies unit actions, then `_process_market`, then `_town_consume(step)`. Here `step` is the same counter as the `obs["step"]` the agents decided on. Shops fire when `step % 4 == 0`, after that call's market. A SELL decided at `obs["step"] ≡ 0` therefore executes before the drain, and `≡ 1` is the first on the drained inventory. The framework (`core.py`) records the post-call state at index `len(steps)`, so an action sits one row after the observation it was decided from. That is the off-by-one behind the 13 Sept misdiagnosis.

## 2. Price model exactness

`tests/test_splice_price_model.py` (14 tests) compares everything with the installed engine's own code:

- **Tables.** `MARKET_PARAMS`, `SHOPS`, `PRODUCTS`, `TOWN_CENTER_PRODUCTS`, I0, the floor and `HINGE_GAIN` are identical to the engine's. An engine patch fails the suite loudly.
- **`quote`.** Every integer inventory within I0 ± 3,000 for all 9 products, plus 60,000 randomized int and float inventories from -40,000 to 60,000. A one-off sweep covered 560,009 evaluations (every integer from -10,000 to 30,000, plus 200,000 random floats). There were 0 mismatches, including Python's banker's rounding and the $1 floor.
- **`sell_revenue`, `sell_path` and `inventory_after_sells`** vs the engine's `_process_market` on 400 random orders, including orders that cross the floor: exact. Sales at $1 add no inventory (`_commit_unit`), and the model reproduces that.
- **`buy_cost`** vs `_process_market` BUY_PRODUCT on 300 random orders: exact. Each unit is quoted post-buy.
- **`drain_per_step`** vs `_town_consume` on 3,000 random shop lists (with duplicates, up to 8 instances) × steps: exact. `project` matches repeated `_town_consume` calls: exact.
- Log-shaped gluts never reach $1. Wheat at I0 + 10^7 still quotes 12. Only sq, linear and sqrt shapes floor (first floored unit: wool +59, strawberry +62, milk +76).

## 3. The sell engine

Stateless. `orders(obs, sellable, slots)` reads only the observation and the release. Defaults (class attributes, overridable per instance):

| case | test (public data only) | what it sells |
|---|---|---|
| **glut** | no unlocked shop consumes it, or its market sits more than `glut_days` = 0.5 day of drain above I0 | the whole release, any turn |
| **healthy** | otherwise | on `healthy_phases` = (1,) only, i.e. the post-drain turn: last tick's drain + ceil(`headroom_share` 0.2 × units below I0), at least 1, and at least enough to clear the release within `hold_windows` = 6 selling turns (a day at the cadence) or before the season ends. EGG, WHEAT and FERTILIZER are sold whole (flat curves). Scarcity-taking: a quote of at least 1.4×base sells down to 1.3×base, never below |
| contested (off by default) | `contested_dumps = True` and the other farm has a producer: sheep for wool, cows for milk, geese for eggs, any animal for fertilizer, a planted crop | the whole release, any turn |

On top of that:

- **Endgame.** The last processed turn is obs step 718 (with 720 episode steps, the interpreter marks DONE after processing step 718), and on it everything goes. Before that, the clearance term spreads what is left over the remaining selling turns.
- **Shed valve** (any turn). If shed plus carried goods exceed 90, the engine sells released units down to 80, greedily by highest quote/base. Overflow past 100 is discarded silently.
- **Output order.** If truncation is needed, the highest-revenue orders survive. They are then placed by per-unit quote, dearest in slot 0: slot i of both players runs to completion before slot i+1.

**Why the glut rule replaces FABLE's threshold.** The literal §1 engine (a reservation price of 0.55×base decaying to the floor by day 27) was run on seed 900, both seats. It realized 32 vs 37 on wool and 31 vs 47 on milk (pooled). The per-day profile showed the mechanism. With no YARN_STORE and milk shops only from day 15, both markets glut by days 9-15 and never recover. The threshold held 29 milk into day 15 while the tape sold 48 units at 79 down to 32, and the backlog then sold at 1-5. Over days 11-16 that was about 94 revenue for 43 units against the tape's roughly 2,080 for 48. Holding pays only when the drain lifts the price before the next sale, and in a market that isn't draining no opponent changes that. **The threshold version was measured on seed 900 only.** Its 900-907 result is unmeasured.

## 4. Diagnostic: W3 with the engine selling its premium goods vs W3

Setup. The overlay `agents/.wb_w3_sells.py` (gitignored; build it with `experiments/splice/_probe_w3_sells.py [name] [attr=value ...]`) is `agents/w3_herdsafe2700.py` verbatim. From step 192 only, W3's WOOL/MILK/STRAWBERRY SELL orders are replaced by the engine's orders, which go in front of W3's other orders. `sellable` is W3's own projected shed. It was run with `experiments/splice/_run_agents_small.py`, which is `experiments/tapes/run_agents.py` on Pool(2) plus an instrumented `_commit_unit` that logs every executed sale per seat and day. Both seats per seed; every run is deterministic, and repeat runs reproduced to the coin.

- **"Same-day"** compares the two sides' average prices on days both sold the product, weighted by the smaller volume. That removes composition effects.
- **"Animals d12"** measures desync: W3's scheduled purchases fail when its cash arrives later than the tape expects.

| engine | seeds | bank W-L | mean | same-day vs tape, wool / milk / strawberry (per unit) | animals d12, ours vs W3 |
|---|---|---|---|---|---|
| FABLE §1 literal (threshold) | 900 | 0-2 | -3,741 | pooled: 32.1 vs 37.3 / 30.8 vs 46.8 / 86.8 vs 84.5 | not measured |
| **default** (spec + glut rule) | **900-907** | **0-16** | **-7,984** | **+0.6 / -4.0 / -0.7** | **244 vs 272** |
| **mirror-tuned alternative** (every turn, contested sold whole) | **900-907** | **5-11** | **-428** | **+1.1 / -1.4 / +0.6** | **272 vs 272** |
| mirror-tuned alternative | 910-913 (held out) | 6-2 | +104 | +2.1 / +0.2 / +0.2 | 136 vs 136 |

Pooled realized prices from step 192:

- Default: wool 140.0 vs 142.6 (1,654 vs 2,232 units: the desync cost volume), milk 98.0 vs 102.4, strawberry 121.0 vs 123.6.
- Alternative: wool 122.0 vs 121.3, milk 99.7 vs 101.1, strawberry 118.7 vs 118.1, on equal volumes.

Exploratory runs on held-out seeds 910-913, all impact-limited-slice variants since removed, isolated the timing effect:

| healthy-regime timing | W-L | same-day, wool / milk / strawberry | animals d12 |
|---|---|---|---|
| phase 1 only | 0-8 | -2.0 / -2.5 / -2.1 | 120 vs 136 |
| skip pre-drain phase 0 | 0-8 | +0.4 / -1.8 / -0.8 | 124 vs 136 |
| every turn | 4-4 | +1.9 / -0.0 / +0.8 | 136 vs 136 |

Reading, with the caveat the brief anticipated. In a W3 mirror both sides drop the same goods on the same turn, and W3 sells them at once. Any wait, whether the cadence or slicing, lets W3's batch land first, and the delayed cash makes W3's own scheduled purchases fail. Selling on arrival therefore reaches parity. Parity is the mirror's ceiling apart from slot order: we put wool in slot 0 and milk in slot 1, so where W3 orders them the other way, we front-run its wool and it front-runs our milk. None of this tells us how the cadence performs for a controller whose drops do not coincide with the opponent's. **The mirror cannot measure a timing edge in either direction.**

## 5. Where FABLE_IDEAS and the engine disagree

1. **Section 1's quote threshold** ("0.55×base early, decaying toward the floor") loses per unit in glutted markets. Held stock sells after the glut deepens, whoever the opponent is. The glut rule replaces it.
2. **"Hour ≡ 2 (mod 4)"** (sections 1 and 4) is the replay-row index. The agent's own frame is `obs["step"] % 4 == 1`, which is the same as `obs["hour"] % 4 == 1`. R2.2 states this correctly. Read literally, sections 1 and 4 would put the cadence one step late.
3. **The ~8,000 premium edge.** This run neither confirms nor refutes that the top six get it from sell timing, since a mirror cannot show a timing edge. A hypothesis for the coordinator, not a finding: part of it is production-side, meaning which products they make relative to each market's shop drain, and when.
4. **Wool quotes.** +33 over I0 is 137 (FABLE says 135) and +46 is 77 (FABLE says 78), because FABLE rounded the coefficient to 0.058. This is immaterial.
5. **R2.3 drain formula** `6·Σ shops·(2 if single) + 1`: the +1 town-centre unit does not apply to FERTILIZER.
6. **Confirmed as written:** per-unit lockstep paired by slot index; $1 sales add no inventory; the market resolves after unit actions and before consumption; one YARN_STORE drains 12 a day, 13 with the town centre; strawberry floors 62 above I0 and milk 76 above.

## 6. For Builder B: calling `orders()` (Builder B has confirmed this wiring)

- **Call it every turn.** Glut sales and the shed valve fire off-cadence. On a turn with nothing to do it returns `[]`.
- **Put its orders at the front of the market list.** Pass `slots` = market slots you can spare. It returns at most that many orders, one per product, dearest first.
- Construct once with `WB_SellEngine(WB_PriceModel())`. It is stateless and safe to share between seats. The mirror-tuned alternative is `se.healthy_phases = (0, 1, 2, 3); se.contested_dumps = True`.
- `sellable` may include units a DROP puts in the shed this same turn, because unit actions resolve before the market. Never release more than will be there: an order that runs out of shed stock aborts its remainder.
- **The last processed turn is obs step 718, and no midnight drop follows day 29.** Anything still in a unit's inventory after step 718 is lost. DROP it by 718.
- Cadence turns are hours 1, 5, 9, 13, 17 and 21. Hour 1 collides with the morning hire burst.
- Timing: well under 20 ms per call (the test's cap).

## Files

| file | what |
|---|---|
| `experiments/splice/price_model.py` | `WB_PriceModel`: exact market, drain, projection |
| `experiments/splice/sell_engine.py` | `WB_SellEngine` |
| `tests/test_splice_price_model.py`, `tests/test_splice_sell_engine.py` | 47 unittest cases |
| `experiments/splice/_probe_cadence.py` | the cadence proof (section 1) |
| `experiments/splice/_probe_w3_sells.py` | builds the gitignored overlay, optionally with engine attribute overrides |
| `experiments/splice/_run_agents_small.py` | `experiments/tapes/run_agents.py` on Pool(2), with realized sell prices (pooled and same-day) and the day-12 herd from an instrumented `_commit_unit` |
