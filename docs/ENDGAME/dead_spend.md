# Dead-spend audit of `agents/public_farm2945.py`

**The headline: there is no dead spend on this base.** The lever this audit was
sent to find - the `MARGIN_LEVERS.md` "$390/tape of seed we never plant" - does
not exist here, and the reason is structural rather than lucky: `router_yuan_*`
is a *recording*, and nothing in the harvest pipeline ever checked that the
recorded purchases were used; `farm2945` buys reactively, one turn at a time,
against the state it is actually in.

Everything the audit could price as "spend that produces nothing by turn 720"
adds to **$187/season in self-play and $107/season on the real replays**. The
largest single line in the whole table - unsold product left in the shed and in
unit inventories at 720 - is **$451/$555**, and it is not spend at all but
revenue never collected; realising it means selling more, which this work is
explicitly not allowed to do.

For scale: the identical-code noise floor on a 16-seed mirror is **±1,131 per
seat-result** (`docs/ENDGAME/rim_results.md` §4). **Every item below is inside
it**, most by an order of magnitude.

## Method

Two datasets, both engine-exact.

* **Self-play, seeds 300-315, base vs base, both seats = 32 seat-records.**
  Mean final bank **99,554** (61,836 - 148,575). Restricted to seeds 300-307,
  the 8-seed window the rest of `docs/ENDGAME/` quotes, the same run gives
  **89,667** - `v2_results.md`, `v3_results.md` and `rim_results.md`'s base
  reference, to the dollar. Both figures are used below, each against its own
  seed set.
* **The 17 reproducing real `farm2945` ladder replays** listed in
  `docs/ENDGAME/traces_2026-09-21.md` §0 (the 19 reachable `56269928` episodes
  minus `109551974` and `109793226`). The base was seated live against each
  recorded opponent tape at the recorded seed; **all 17 reproduce both banks to
  the dollar**, so the seat/seed conventions are right.

Instrumentation was a throwaway wrapper plus five monkey-patches applied in the
runner process, never on disk: `_do_hire` (cost, `hires_today` at the time,
landed vs cash-refused), `_commit_unit` (every commit and every `False` return,
by op/item/price), `_do_buy_land`, `_daily_refresh_animals` (escapes) and
`_apply_unit_action`. That last one is the one worth describing: it snapshots
the unit's tile, its inventory, the shed, the seed dict, its position and the
farm's money before the call and compares after, so every unit-turn is labelled
**effective** or **silent no-op**. All three instrumented passes reproduce the
uninstrumented final banks exactly on all 33 episodes, so the patches perturb
nothing.

The agent wrapper records, per step and per seat, the emitted action, the
market list, money, shed, seeds, per-unit inventories, and a tile census; the
daily grid snapshot is what prices the land question.

Cash reconciles to the dollar: starting $3,000 + $127,546 SELL revenue −
$30,992 of buys = $99,554, the measured mean bank. The whole of the spend side,
self-play mean per season, is the denominator every figure below sits against:

| buy | $/season | units | | sell | $/season | units |
|---|---:|---:|---|---|---:|---:|
| `BUY_PRODUCT` WHEAT | 6,022 | 165.5 | | STRAWBERRY | 37,423 | 246.2 |
| `HIRE` | 4,860 | 270.9 | | MILK | 19,218 | 205.7 |
| `BUY_ANIMAL` SHEEP | 3,344 | 6.7 | | WHEAT | 15,382 | 405.2 |
| `BUY_SEED` STRAWBERRY | 3,300 | 33.0 | | FERTILIZER | 15,144 | 334.7 |
| `BUY_ANIMAL` COW | 3,100 | 7.8 | | MELON | 14,267 | 72.0 |
| `BUY_PRODUCT` FERTILIZER | 2,587 | 87.5 | | WOOL | 13,309 | 139.4 |
| `BUY_SEED` WHEAT | 1,547 | 154.7 | | CARROT | 6,811 | 127.9 |
| `BUY_SEED` MELON | 960 | 12.0 | | EGG | 4,098 | 76.9 |
| `BUY_SEED` CARROT | 941 | 47.1 | | TOMATO | 1,895 | 10.0 |
| `BUY_ANIMAL` GOOSE | 769 | 2.6 | | | | |
| `BUY_LAND` | 3,500 | 2.1 | | | | |
| `BUY_SEED` TOMATO | 63 | 1.2 | | | | |
| **total** | **30,992** | | | **total** | **127,546** | |

## The ranked table

$/season, mean over seat-records. "Removable" means: as a pure deletion or a
cap, without changing what the farm produces or sells.

| # | item | self-play (32) | replays (17) | removable |
|---|---|---:|---:|---|
| 1 | product unsold at 720 (shed + unit inventories) | **451** (133-993) | **555** (118-1,423) | **no** - only by selling more |
| 2 | **seed still held, unplanted, at 720** | **137** (0-200) | **67** (0-260) | **cap** - built below |
| 3 | hires whose only effective work happens while an earlier unit `PASS`es | 36 | 38 | re-routing, not deletion ($8 / $13 is a last-of-day hire) |
| 4 | seed bought *after* that crop's last landed planting (subset of #2) | 19 | 4 | foresight - not implementable locally |
| 5 | animal bought and still in the shed at 720, never placed | 12 (one $400 COW on 1 of 32) | 0 | no local rule sees it coming |
| 6 | hires whose hand never changes any state all day | 2 | 2 | 0 of them is the last hire of its day |
| 7 | hires issued at hour 23 (the hand is deleted the same interpreter call) | **0** | **0** | - |
| 8 | `HIRE` orders refused on cash | **0** | **0** | - |
| 9 | `PLANT`s dropped by the engine's all-or-nothing seed rule | **0** | **0** | - |
| 10 | market orders past the 10-order cap | **0** | **0** | - |
| 11 | seed planted too late to reach `first_yield_day` | **0** | **0** | - |
| 12 | land bought and then not planted | **0** | **0** | - |
| 13 | structures built and never filled | 0 (`BUILD_*` costs no cash) | 0 | - |
| | **total spend priced as dead** (#2-#6, no double counting) | **$187** | **$107** | |
| | plus #1, revenue never collected | 451 | 555 | |

**One measured effect is deliberately left out of the table.** Animals escape on
**0.19 of a season in self-play (6 escapes across 32 seat-records) and 0.12 on
the replays (2 across 17) - and every one of the eight is on day 26.** An animal that escapes on day 26 has
already produced for two weeks, so its $300-500 purchase is not dead spend - what
is lost is its last three days of production, which this audit does not price.
It is systematic (day 26, every time) and out of scope here; worth a look by
whoever next touches the animal layer.

### 1. Unsold product at 720 - the biggest line, and out of scope

At the last agent call (step 718) the shed is essentially empty - liquidation
works - but the *unit inventories* are not:

| | self-play | replays |
|---|---:|---:|
| CARROT | 4.38 | 3.59 |
| WOOL | 2.44 | 2.71 |
| EGG | 0.50 | 1.88 |
| WHEAT | 1.00 | 1.41 |
| FERTILIZER | 0.19 | 0.53 |
| value at the closing quote | **$451** | **$555** |

`_end_of_day` drops inventories into the shed at step 719, with no turn left to
sell them. Collecting it means adding SELL orders in the last turns, i.e.
changing what is sold. Recorded here because it is the largest item, not as a
proposal.

### 2. Seed held at 720 - the only spend line big enough to name

|  | self-play | replays |
|---|---:|---:|
| WHEAT | 2.38 seeds ($24) | 1.41 ($14) |
| CARROT | 5.50 seeds ($110) | 2.35 ($47) |
| STRAWBERRY | 0.03 ($3) | 0.06 ($6) |
| **total** | **$137** (max $200) | **$67** (max $260) |
| records ending with any | 22 of 32 | 5 of 17 |

Seed cannot be sold and cannot be bought back, so this is cash deleted from the
bank - the same mechanism as the `MARGIN_LEVERS.md` lever, two orders of
magnitude smaller.

**It is not recoverable by a local cap, and the buy/plant ledger says why.** Per
crop, seeds bought against seeds actually planted, by day:

| crop | bought | planted | left | last buy | last landed plant |
|---|---:|---:|---:|---:|---:|
| WHEAT | 154.7 | 152.3 | 2.38 | day 27 | day 25.8 |
| CARROT | 47.1 | 41.6 | 5.50 | day 27 | day 27.0 |
| MELON | 12.0 | 12.0 | 0 | day 0 | day 0 |
| STRAWBERRY | 33.0 | 33.0 | 0.03 | day 11 | day 11 |
| TOMATO | 1.2 | 1.2 | 0 | day 18 | day 18 |

Only **$19/season** is bought after the crop's last landed planting - the rest
accumulates in ones and twos across days 7-27, at moments when the farm
genuinely could still plant it and simply then doesn't. The CARROT surplus, the
bulk of the line, climbs +0.5 at a time from day 7 onward. There is no step at
which a local rule can see that a particular seed will go unused.

### 3-5. The three things that could have been levers and are not

**Hires.** 270.9 landed hires a season for $4,860 in self-play (273.8 / $5,302
on the replays, matching `traces_2026-09-21.md` §3.1 exactly). Landed hires by
hour of day:

| hour | 0 | 1 | 2 | 3 | 4 | 6 | 23 |
|---|---:|---:|---:|---:|---:|---:|---:|
| hires/season | 214.8 | 49.4 | 3.5 | 3.0 | 0.1 | 0.1 | **0** |
| $/season | 1,659 | 2,476 | 394 | 315 | 11 | 6 | **0** |

The hour-23 class is the one clean deletion the engine offers - unit actions run
before `_process_market`, which runs before `_end_of_day`, so a hand hired at
hour 23 is created and destroyed inside one interpreter call and can never act.
**The base never does it**, on either dataset. Neither does it ever issue a
`HIRE` it cannot pay for: 270.9 issued, 270.9 landed, 0 refused.

Nor is any hire idle. By hire index `k` (the `k`-th hire of a day costs
`fib(k)`), with "effective" meaning the unit-turn changed some state:

| k | hires/season | $/season | $/hire | effective ops/season | silent no-ops | PASS |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 30.0 | 30 | 1 | 340.2 | 4.3 | 88.8 |
| 5 | 24.0 | 192 | 8 | 279.6 | 4.1 | 23.0 |
| 9 | 17.3 | 949 | 55 | 191.5 | 3.0 | 19.8 |
| 10 | 14.7 | 1,307 | 89 | 142.7 | 0.1 | 20.9 |
| 11 | 2.4 | 342 | 144 | 21.5 | 0.0 | 5.8 |
| 12 | 0.9 | 218 | 233 | 8.8 | 0.0 | 3.1 |
| 13 | 0.1 | 47 | 377 | 1.1 | 0.0 | 0.8 |

Exactly **two hands a season** - the second hire of day 0 and the first of day 2,
**$1 each** - spend their whole day on `PASS` and moves. Neither is the last hire
of its day, so even those two cannot be deleted without shifting every later
hand's index (`action["hands"][k]` drives physical hand `k`), which is the
`-30k` class of failure recorded in the T5 plan. **Dead hire spend removable as
a pure deletion: $0.**

Across all units, 3,411.8 of 3,456.5 non-move, non-`PASS` unit-turns a season
are effective; the 44.7 silent ones are mostly `CARE` (13.7) and `WATER` (9.9)
repeated on an animal or plant already cared for or watered that day. That is
1.3% of the farm's work, and it costs turns rather than cash.

**Limitation, stated once.** "Effective" here means the unit-turn changed some
state - a tile, an inventory, the shed, the seed dict, a position or the bank.
That is a lower bar than economic value: a `WATER` on a plant harvested later
the same day flips `watered_today` and earns nothing. The conclusion survives it
because the expensive hands are not marginal on that axis either - `k=11` spends
its 21.5 effective ops a season on `WATER` (7.5), `FERTILIZE` (7.3), `HARVEST`
(2.5), `PICKUP` (1.3), `CARE` (0.8) and `FEED` (0.6) for $342, and the `HARVEST`
and `FERTILIZE` alone plausibly cover that.

**The brief's other hire question - hands whose work an idle earlier hand could
have done - is also near-zero.** Counting a hand as substitutable when *every*
one of its effective ops lands at a step where the farmer or an earlier hand
emitted `PASS`: **6.62 hands a season, $35.6** in self-play (6.65 / $38.2 on the
replays), and only **2.0 a season / $8** of those is the last hire of its day,
which is the only position that could be deleted without shifting every later
hand's index. It is also not a deletion in the first place - the idle earlier
hand is standing somewhere else on the board, so this is re-routing, and
re-routing is exactly the class of change the plan's status log has already
rejected seven times.

**Land.** Two quadrants always, on days 6 and 11, $3,000. A third, $4,000, in 4
of 32 self-play seat-records (seeds 300 and 312, both seats, day 18) and 4 of 17
replays (day 18, except `109856068` at day 11) - and it is *not* dead: on the
self-play seeds the daily grid shows 10 TOMATO planted on it the next morning
and still standing at day 29, and `SELL TOMATO` revenue is concentrated on
exactly those records. This is the `v219` program, which `docs/ENDGAME/v3_results.md` already
measured as paying (disabling it loses all 6 seat-results, mean −4,799).

**Market orders.** 0 steps over the 10-order cap on either dataset, so nothing
is silently dropped. Failed `_commit_unit` calls are ~180/season and are
**entirely** the deliberate oversize-`SELL` idiom (`SELL MILK 2000` against a
shed of 18) - they move no cash, and `MARGIN_LEVERS.md` already records why
filtering them is unsafe. Failed `BUY_PRODUCT` on cash: 0.2/season.

**Fertilizer and wheat round trips.** The base buys 87.5 FERTILIZER at a mean
$29.6 and sells 334.7 at $45.3, and buys 165.5 WHEAT at $36.4 against 405.2 sold
at $38.0. Same-step round trips are 40.1 FERTILIZER and 16.5 WHEAT units a
season and net **+$31**, not a cost. There is no dead trade here either.

## What was built: `agents/farm2945_trim.py`, flag `TRIM_SEED`

The largest removable item is #2, so the lever is a `BUY_SEED` cap, built as an
overlay on the byte-verbatim base (`agent` re-bound last; `TRIM_SEED = False`
returns the parent's exact action object).

For crop `C`, `29 - first_yield_day(C)` is the last day a planting can still
reach its first yield inside the season. Before that day nothing is capped. On
it, held + bought is capped at `_trim_capacity` - the tiles a seed could still
go into *today*: empty tiles, `WEED` tiles (a `DIG` clears them), and
harvest-ready **non-`ongoing`** crops, because `_apply_unit_action`'s `HARVEST`
branch sets the tile to `None` for those and the base harvests-then-replants the
same tile inside a day. After that day the cap is 0. A trimmed order is
**rewritten in place as quantity 0**, never removed: `_parse_order` returns
`None` for `n <= 0` and the index loop skips it while `q[:max_orders]` keeps
every position, so no later `SELL` moves index and the lockstep coin-flip that
gave MARGIN_LEVERS its +5,446/−3,226 seed cannot fire.

**The first version of this cap counted only already-empty tiles, and it cost a
whole CARROT harvest (~$200) on 7 of 16 self-play seeds** - 7 seeds at +$10,
2 at $0, 7 at −$121 to −$226. That is the measurement that produced the
harvest-ready term above, and it is worth keeping visible: a cap sized on
*tiles free now* is not the same as a cap sized on *tiles plantable today*.

`tests/test_farm2945_trim.py` - 14 tests: capacity counts the right tiles,
`ongoing` crops are never capacity, nothing binds before the last plantable day,
a trimmed order keeps its index as quantity 0, several orders of one crop share
one budget, `PLANT`s emitted this turn raise the room, held seed can never fall
below what the turn plants, non-seed orders and malformed quantities are passed
through, flag-off returns the parent's object, `agent` is the last callable.

### Measured

| test | result |
|---|---|
| `run_agents.py` paired vs base, seeds 300-331, both seats | **3-3 of 64, 58 exact ties, mean +0, median +0, worst −1,131, +0 on all 32 per-seed averages** |
| the same harness, **base vs itself**, identical seeds | **3-3 of 64, 58 exact ties, mean +0, median +0, worst −1,131, min bank 53,049** - the same line |
| absolute self-play, seeds 300-315 both seats (n=64 banks) | **99,554** (61,836 - 148,575) vs base **99,554**, Δ **+0** |
| absolute self-play, seeds 300-307 (the `v3_results.md` window) | **89,667** vs base **89,667**, Δ **+0** |
| vs `agents/router_yuan_nf_trim.py`, seeds 300-307 both seats | **16-0 of 16, mean +15,982, worst +5,395** - the base's own recorded record, to the dollar |
| pre-submit gate, self-play seed 0 | `['DONE', 'DONE']`, 72,101 / 72,762 - the base's recorded gate, to the dollar |
| `python -m unittest discover -s tests` | **268 tests, OK** (1 skipped), the 14 new ones included |
| per-turn time, 720 turns, seed 305 | overlay max **0.153 ms**, p99 0.131, mean 0.005; the base's own turn is max 339 ms against the 1,000 ms `actTimeout` |

**Read the control row.** The candidate's summary line is character-for-character
the line the base produces against itself on the same seeds, and going below the
summary, **all 128 recorded bank values are identical** - the candidate is
behaviourally indistinguishable from the base on every one of the 64 games.

The 3-3 is not the overlay and it is not run-to-run noise either: the three
non-tie seeds are **300, 310 and 313**, and on each of them a *mirror* game ends
with the two seats on different banks (+1,131 / +762 / −80), identically in both
arms. `run_agents.py` diffs seat 0 against seat 1, so a seat-asymmetric mirror
shows up as one win and one loss. This is the deterministic half of what
`rim_results.md` §4 records as the ±1,131 identical-code noise floor - in a
lockstep order book the two seats are simply not symmetric.

**The cap never binds on any measured episode.** Directly: `_TRIM_REPORT` reads
`trim_units: 0, trim_cash: 0, trim_orders: 0, trim_errors: 0` over all 16 seeds
300-315, both at the shipped `_TRIM_SLACK = 2` and with the slack removed
entirely (`_TRIM_SLACK = 0`). Indirectly, and this
covers all 32 paired seeds: a `BUY_SEED` is never refused on cash on this base,
so a trimmed unit is a unit that *would* have landed and every trimmed dollar
would show in the bank - and all 128 bank values match the control exactly.

The reason is the one the ledger above already gives: on its last plantable day
the base's seed purchases are always inside that day's capacity, and the $137 of
leftover seed was bought earlier in the season, when the capacity was real.

So the ship criterion is met in the only way the arithmetic allows - every
non-tie delta should be about the dollars deleted, $0 are deleted, and the
candidate is indistinguishable from the base on all four harnesses - and the
lever is worth **nothing**. It is a correct guard against a purchase the base
does not currently make, not a gain. **Recommendation: do not spend a submission
slot on it.** Keep the file as the tested place to put a seed cap if a future
base ever needs one.

## What this rules out, for the plan

`docs/superpowers/plans/2026-09-21-endgame.md`'s status log now has seven
rejected levers that changed *what* the farm produces or sells. This audit was
the eighth angle - the levers that change neither - and it closes it with
numbers rather than a judgement call:

* No hire is wasted; the marginal hand is priced correctly all the way to the
  13th of a day.
* No seed is wasted that a local rule could see.
* No order is dropped, no planting is blocked, no cash purchase is refused.
* No land is bought that is not farmed.
* The base's own liquidation already empties the shed.

The remaining $451-555 of unsold product at 720 is the only four-figure-adjacent
number in the table and it is on the selling side, which is the side every
previous lever died on. **If anything is still on the table it is not spend
discipline; this base is already tight.**
