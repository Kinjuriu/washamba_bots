# We are a route generation behind, and that is the whole gap

**2026-08-22/23.** Our ladder score plateaued at **1,687.5, rank 1,223 of 5,940**,
after a day spent tuning parameters on a route derived from the **V16-RC5**
notebook. The tuning worked — per-item front-run leads are +1,306 at 23/24 head
to head — and it did not matter, because the route itself is the constraint.

## The ecosystem, read off the leaderboard

| team | notebook generation | rank | score |
|---|---|---|---|
| raykkretzschmar | v20-era | 40 | **2,658** |
| boatlee (the author) | v20/v21 | 106 | **2,501** |
| bruceqdu | v20-era | 108 | 2,494 |
| kunaldesale2408 | v20-era | 186 | 2,391 |
| **flexonafft** | **a fork of v20** | **213** | **2,364** |
| denizeryilmaz | v16-era | 673 | 1,964 |
| kaitofukami | older | 814 | 1,891 |
| web3cainiao | older | 1,054 | 1,770 |
| **us** | **v16-RC5 + our own leads** | **1,223** | **1,687** |

`flexonafft` is the important row. It is a **fork**, not an original, and it is
**677 points above us**. Everything at 2,300+ is v20-era; everything v16-era is
under 2,000.

## Measured, not inferred

`experiments/route_v20.py` fetches the v20 notebook and decodes its agent
(base85+zlib, verified against the notebook's own SHA-256, decoded **without
executing** the notebook's code). Head to head, contested market, both seats:

| matchup | matches | mean | wins |
|---|---|---|---|
| v20 vs our current submission (per-item leads) | 24 | **+8,855** | **18/24** |
| v20 vs the stock v16 route (`meta_lead3`) | 16 | **+9,288** | 13/16 |

For scale, every lever we found by tuning the v16 route was worth **+1,000 to
+1,306**. The route generation is worth **seven times** that. Note what the two
rows say together: our per-item lead work is still worth ~433 *against v20*, so
the tuning is not wasted — it is an order of magnitude smaller than the thing it
was applied to.

## What this corrects

When the v16 notebook was found, the recorded conclusion was: **do not fork a
newer notebook, because you buy its saturated rating and land back in a 50%
mirror pool.** That reasoning was sound and the conclusion was wrong. A
saturated v20 rating is ~2,364. A saturated v16 rating is ours, 1,687.
Saturation compresses ratings *within* a generation; it does not equalise
across them.

Generalises: **check whether the ceiling you are optimising under is the
ceiling of your approach or the ceiling of your starting point.** A day of
clean, well-measured parameter work on the wrong base is worth less than one
base change — and the parameter work looked good precisely because both sides
of every comparison sat on the same wrong base, so the base could never show up
as the variable.

## Gate before anything is submitted

**The v20 notebook's licence is unverified.** Kaggle renders it only in the
page's JavaScript, so neither the API nor an HTTP fetch can read it; v16 was
Apache 2.0 with an attribution requirement we honoured in
`agents/meta_lead3.py`. A human has to open the page and read the licence field.

Using it as a local opponent is fine regardless — measuring is not
distributing, and `experiments/.v20_agent.py` is gitignored and never
committed. **Submitting a derivative is gated on that licence.**

## The plan once the gate clears

1. Submit v20 unmodified once, to find where the route actually lands for us.
2. Run the same contested-parameter hunt that found STRAWBERRY-6. v20 is a
   *multi-route* agent, so its route-selection logic is a far larger parameter
   surface than a single sell lead.
3. Ship v20 **plus** tuning the other forkers are not doing.

The durable asset from the v16 work is not the STRAWBERRY constant. It is the
method: find the shared route's contested parameter, sweep it against the stock
version, confirm at 24 matches, and read the win count before the mean.

## A minimum-price gate on all selling (2026-08-27)

`agents/route_moon_md_floor.py` adds `_min_sell_price_gate`, which trims a
`SELL` order to the units whose *marginal* clearing price is still at or above
`ratio x base_price` and drops it if none are. Exempt: late season
(`step >= 660`, where unsold stock scores nothing) and a nearly-full shed
(`held >= 90`, where overflow past 100 items is silently discarded).

This is **not** `_PREEMPT_MIN_PRICE_RATIO`, which is measured and lost at every
setting. That gate reordered *who dumps first* into an already-crashed market;
in a mirror, being first into a bad market beats being second. This one
withholds the volume outright.

Measured head to head against `agents/route_moon_md.py`, control at ratio 0.0
returning 2/12 and +0:

| ratio | 6 seeds x 2 | 12 seeds x 2 |
|---|---|---|
| 0.05 | 11/12 +314 | 19/24 +339 |
| 0.075 | - | 17/24 +363 |
| **0.10** | **11/12 +487** | **19/24 +432** |
| 0.15 | - | 18/24 +459 |
| 0.20 | 9/12 +375 | - |
| 0.35 | 5/12 -285 | - |

A broad plateau from 0.05 to 0.15, decaying monotonically past it.

Every match above is a mirror, which is the exact condition that blessed the
second sheep, so it was re-measured against two *foreign* selling opponents -
different route lineages, not clones - with a self-control:

| candidate | opponent | margin better on | mean | t |
|---|---|---|---|---|
| ratio 0.10 | `agents/route_v20.py` | **22/24** | +474 | +4.66 |
| ratio 0.10 | `agents/meta_lead3.py` | **21/24** | +314 | +5.42 |
| self-control | `agents/route_v20.py` | 0/12 | +0 | 0.00 |

### It does not make us richer - it makes the opponent poorer

Decomposed over six episodes, our own bank moves -22 / -740 / +136 (mirror) and
+93 / -18 / +85 (vs v20): noise around zero, mean about -78. The opponent's bank
falls -265 / -1,181 / -589 and -132 / -270 / -546: mean about -497, **and it
falls against v20 too**, so this is not a mirror artefact.

That makes it the first lever measured that moves the number
`docs/REPLAY_ANALYSIS.md` says we lose on - the leaders' opponents bank ~81,000
where ours bank ~90,049. It closes maybe 5-10% of that gap.

### A method note that cost a harness

The first foreign check compared **our own bank** across two episodes against a
fixed opponent and read 14/24, +19 - which looked like a mirror artefact and
nearly sank the change. That harness is structurally blind here: our bank is
flat by construction, so it reads ~0 however well a suppression change works.

Note this is *not* statistic-shopping after a bad result. `head_to_head.py` was
already measuring margin - it subtracts the two banks in the same episode - and
had said 19/24 before any foreign test ran. The two harnesses that measure
margin agree; the one measuring own-bank dissents precisely because own-bank
does not move. The switch was made from the mechanism, not from the answer.

Generalises: **when a change works by suppressing the opponent rather than
enriching yourself, a harness that measures only your own bank reports
nothing.** Pick the statistic from the mechanism, not from habit.

### The order-book audit refuted the premise this was built on

The gate was motivated by "we sell ~4,544 units at ~$20/unit while the leaders
take 63 $/unit on a third of the volume." Traced on a real episode, the mix is
**$41.5/unit**:

| band | units | revenue |
|---|---|---|
| <= $5 | 529 | $996 |
| $6-25 | 557 | $11,570 |
| $26-100 | 3,388 | $157,393 |
| > $100 | 124 | $21,108 |

Floor-priced selling is 11% of units and **0.5% of revenue**. FERTILIZER alone
is 2,935 of 4,598 units at $40.9/u, all produced free by the animals and none
bought back - 63% of season revenue. The 10-order cap binds on 6 turns of 387.

So the gate is a real, consistent, **small** win, and it is **not** the fix for
opponent suppression. The gap where our opponents bank ~9,000 more than the
leaders' opponents remains unexplained; do not let this entry be read as
closing it.

Generalises, and it is the third time in this repo: **check the magnitude of
the thing you are about to optimise before building the optimiser.** One
episode trace would have priced this at 0.5% of revenue before any code was
written.

### Per-item floors are a measured dead end - do not re-run them

Paired margin vs `agents/route_v20.py`, 8 seeds x 2 seats, baseline = the gate
at 0.10, self-control 0/8 and +0:

| arm | margin better on | mean | t |
|---|---|---|---|
| `{'MELON': 0.60}` | 0/16 | -409 | -2.61 |
| `{'STRAWBERRY': 0.50, 'MILK': 0.50, 'WOOL': 0.50}` | 0/16 | -1,554 | -8.25 |

Negative on every seed and seat. The reason no per-item variant can work is
that **premium withholding saturates at 0.10** - seed 0 vs v20:

| ratio | FERTILIZER | STRAWBERRY | MILK | WOOL | our bank | opp bank |
|---|---|---|---|---|---|---|
| none | 2935 | 294 | 273 | 179 | 32,092 | 27,619 |
| 0.10 | 2935 | 273 | 250 | 156 | **32,185** | **27,487** |
| 0.20 | 2873 | 273 | 250 | 156 | 31,917 | 27,821 |
| 0.35 | 2739 | 273 | 250 | 156 | 31,668 | 28,153 |

The premium columns stop moving past 0.10 because those curves are cliffs -
STRAWBERRY drops $5 to $1 across one unit. All a bigger ratio does is choke
FERTILIZER, 63% of season revenue, which is where our bank falls and the
opponent's rises. A `{'WHEAT': 0.80}` arm was byte-identical; a $20 floor never
binds on a crop quoted above $21.

Generalises: **a threshold can only pay where the underlying curve is smooth
near it.** Against a cliff every setting past the edge is identical, so
sweeping finer measures side effects on other items and nothing else.

### The selling thesis is closed. Count LANDED trades, not requests.

Everything above was motivated by "we sell ~4,544 units at ~$20/unit while the
leaders take 63 $/unit on a third of the volume." **That premise was an
artefact of counting market orders instead of executed trades** - the same
mistake this repo already recorded for `PLANT`, made again on `SELL`.

Measured against `pass` (which issues no market orders, so every rise in market
inventory is ours and every fall is deterministic town consumption, making
landed units exactly recoverable):

| item | requested | landed | fill | revenue | $/unit |
|---|---|---|---|---|---|
| WOOL | 270 | 219 | 81% | 51,338 | 234 |
| STRAWBERRY | 216 | 172 | 80% | 40,861 | 238 |
| WHEAT | 1,647 | 771 | 47% | 34,344 | 44 |
| MILK | 189 | 164 | 87% | 23,683 | 144 |
| MELON | 120 | 100 | 83% | 22,398 | 224 |
| FERTILIZER | 2,028 | **301** | **15%** | 20,816 | 69 |
| **TOTAL** | **4,472** | **1,727** | **39%** | 193,440 | **$112** |

(Revenue is uncontested and therefore inflated; the unit counts are exact.)

**We land 1,727 units at ~$112 each.** The top-10 figures we compared against
came from the same kind of action-stream parse, so they are request counts too -
the comparison was apples-to-apples, and what differs is that we re-request
stock we do not hold. Our realised unit economics are already at or above the
leaders'. There was never much to win on the sell side, which is exactly why the
gate bought only +474 and per-item floors bought nothing.

### FERTILIZER has zero demand, and it is the herd's cash flow

`TOWN_CENTER_PRODUCTS = [p for p in PRODUCTS if p != "FERTILIZER"]` and
FERTILIZER appears in no `SHOPS` entry, so **nothing ever consumes it**. Price is
`100 - 0.2 x excess`, floors after 495 units, and the whole season's fertilizer
market is worth ~$25,000 split between both players. Traced vs `route_v20`,
inventory rises 10,000 -> 10,477 and the price ends at **$5**.

That makes it look like a market to withhold from. It is not:

| arm | margin better on | mean | t |
|---|---|---|---|
| `{'WHEAT': 2.0}` (block all wheat sales) | 3/16 | -6,161 | -3.20 |
| `{'FERTILIZER': 2.0}` (block all fertilizer sales) | 0/16 | **-165,382** | -40.58 |

Blocking fertilizer sales ends seed 0 on a bank of **453 - below the $3,000
starting stake - with all 14 animals dead** while the opponent banks 127,109.
Fertilizer sales are the cash flow that buys feed; cut them and the herd starves,
taking WOOL and MILK with it. Same mechanism as the second-sheep cash trough.

The wheat arm was motivated by real churn - we sell 771 WHEAT at ~$44.5 while
buying back 970 at ~$44 - but the wheat we sell is funding the wheat we buy, and
stopping the churn stops the feed.

Generalises: **a market with no demand sink can still be load-bearing.** Its
value is not the price it clears at, it is the timing of the cash.

### The strawberry lead is also dead

The "$6,156 of seed for $3,030 of revenue" figure used the same request-count
error: STRAWBERRY lands 172 units at **$238/u**, and it is our second-largest
revenue source. It is not a loss-making crop.

### Where the remaining gap is NOT

Selling. Three independent attempts on this axis - a global price floor
(+474, shipped), per-item floors (0/16, 0/16) and blocking commodity churn
(3/16, 0/16) - and the trace explains why: our realised sell profile already
matches the leaders'. Anything further should be measured on **production**, not
trading.

## The production axis is closed too (2026-08-27)

Having closed selling, the obvious next question was production. Scoped by
measurement first. Contested episode vs `agents/route_v20.py`, seed 0:

| | |
|---|---|
| land | 75 tiles owned by day 12, 84-95% of usable tiles cropped |
| animals | 14, alive all season |
| weeds | 1-5 at any time |
| crew | 12-13 units |

**The farm is not the constraint.** Where the unit-turns go is:

| category | share of 6,915 unit-turns |
|---|---|
| **movement (N/S/E/W)** | **52.3%** |
| PASS (idle) | 8.1% |
| WATER | 13.1% |
| HARVEST | 5.8% |
| FEED / CARE / COLLECT_FERTILIZER | 13.7% |
| PLANT / PICKUP / FERTILIZE / PLACE | 6.2% |

### Movement is unreachable, not untuned

Half of every unit's life is walking, but that walking is baked into the
recorded `_kawa_actions` plan. The route's own routing machinery
(`_v65_plan_routes`, `_v65_compact_targets`) sits behind
`_v88_late_plan_active`, which never activates in this matchup - so its two
hardcoded constants are dead code here. Swept anyway to be sure:
`service_cost` at 1/2/5/8 and the compaction radius at 1/3/4 all returned
**byte-identical episodes**, 7 of 7.

### Idle turns are not free production - HARVEST is a timing decision

8.1% of unit-turns are PASS, and classifying what the idle unit was standing on
made them look like free money:

| standing on | count | share of 557 PASS turns |
|---|---|---|
| ripe crop (harvestable) | 218 | 39.1% |
| no position / off-board | 162 | 29.0% |
| animal tile | 67 | 12.0% |
| dry crop (waterable) | 49 | 8.8% |
| WEED (diggable) | 3 | 0.5% |

An `_idle_salvage` overlay that replaces PASS (and only PASS) with HARVEST /
WATER / DIG on the tile the unit is already standing on - costing zero movement -
is a **clear loss on all three harnesses**:

| harness | wins | mean |
|---|---|---|
| margin vs `route_v20` | 6/16 | -4,538 (t -2.77) |
| margin vs `meta_lead3` | 2/16 | -6,975 (t -2.71) |
| mirror head to head | - | -5,868 |

Splitting it isolates the cause exactly. With HARVEST removed, leaving only
WATER and DIG, the overlay is **byte-identical** (0/16 and +0 vs `route_v20`;
3/16 and +295 with a +0 median vs `meta_lead3`). The whole effect was HARVEST.

**`yield_units > 0` does not mean "ripe" - it means some yield has banked.**
`HARVEST` clears a one-shot crop's tile, so harvesting early forfeits the rest
of that tile's season. Those PASS turns are the route *waiting for max yield*.

Generalises, and it is the same shape as the `growth_days` dead end: **an idle
resource is not necessarily a wasted one.** Before salvaging slack, check
whether the slack is load-bearing.

### Where that leaves this route

Every overlay-reachable lever is now measured:

| lever | result |
|---|---|
| global price floor | **+474, shipped** |
| per-item floors | 0/16, 0/16 |
| block commodity churn | 3/16, 0/16 |
| routing constants | unreachable, 7/7 byte-identical |
| idle harvest salvage | -4,538 / -6,975 / -5,868 |
| idle upkeep salvage | byte-identical |

Nine parameters were swept before these, seven byte-identical. Set against the
history of this agent:

| change | gain |
|---|---|
| v16-derived -> v20 | **+8,855** (18/24) |
| v20 -> Moon | +730 (14/16) |
| Moon tuning | +196 (19/24) |
| MD lead | +598 (22/24) |
| price gate | +474 |

**Route-generation upgrades dwarf parameter tuning by an order of magnitude.**
The highest-value activity is not another sweep - it is watching the competition
Code tab for a newer public route and forking it, the way v20 and Moon were
found.

## Route generation four: the #3 team's public router (2026-08-30)

The previous section ends by saying the highest-value activity is watching the
Code tab for a newer public route. This is what that looked like when it paid.

`yhay81/public-match-history-router-rating-2929-aug-30` was published on the
morning of Aug 30 by Yusuke Hayashi, **#3 on the live leaderboard at 2,925.6**,
under Apache 2.0 (the decoded source carries its own SPDX header). It is a pure
tape replayer: ten 720-step action schedules scraped from public episodes of
top-rated teams, selected by the first shop unlocked at step 72 and the first
two by step 144. No board model, no weed repair, no market overlay.

Six fresh public routes were decoded without execution and put through a
round-robin, 6 seeds x 2 seats, contested market, win count first:

| candidate | vs `route_moon_md_floor_deficit` (our best) | vs the router |
|---|---|---|
| **yhay81 router** | **10/12, +11,455** | - |
| indarkarhana "shape the shop, work the pasture" | 12/12, +18,336 | 5/12, -4,077 |
| kaitofukami v48 "fast routes" | 12/12, +7,194 | 2/12, median -9,856 |
| prvsiyan "the soil remembers rain" (V202A) | 11/12, +4,136 | 2/12, -9,040 |
| boatlee v21-r1 | 1/12, -601 | - |
| salemali7 "2900" | 3/12, -13,194 | - |

Three things worth keeping from that table:

- **Two routes beat our best 12/12 and both lose to the router.** Same shape
  as HarvestForge-X beating us 16/16 and losing to v20 0/16. "Beats us" is not
  a ranking; the round-robin is.
- **The kaito-vs-router mean is +1,886 and the median is -9,856** - one seed
  came in at +66,943. Reporting the mean alone would have called a 2/12 loss a
  win.
- **salemali7's "2900" title is substantiated nowhere in its notebook**, and
  the agent lost 3/12. That account has oversold before ("3094" was 2,684).

The tapes themselves match what this week's top-of-ladder replays show
(Crop Dusta #1, Milan Leonard #2, pulled from the episodes dataset): every one
buys exactly two quadrants (75 tiles), runs a 9-12 animal COW+SHEEP herd on a
12-hand crew, sells heavily from day 10, and plants ~190 WHEAT. Shipped
unmodified as `agents/router_yhay.py`, per the same protocol as `route_v20.py`:
submit the base once, find where it lands, then tune.

### Two hypotheses tested against the ladder record and refuted

**"The Moon route's third quadrant is what loses."** Both of our biggest
ladder losses (opponents rated 1,951 and 2,027, margins -46% and -24% of the
winner's bank) showed our side at 100 tiles while every opponent stopped at 75.
Split across 76 ladder episodes vs opponents rated >= 1,800, by the route the
Moon base actually drew (read from the replay's shop-unlock order and fed to
its own `_kawa_route_label`):

| route | n | win rate | margin |
|---|---|---|---|
| `10c4s_3q` | 43 | **27.9%** | **-3,155** |
| `6c12s_4q_first_yarn` (100 tiles) | 9 | 22.2% | -3,920 |
| `6c12s_4q_second_yarn` (100 tiles) | 11 | 45.5% | +1,852 |
| `6c8s_3q` | 8 | 87.5% | +7,184 |
| `8c6s_3q` | 5 | 40.0% | -898 |
| 75 tiles pooled / 100 tiles pooled | 56 / 20 | 37.5% / 35.0% | -1,477 / -745 |

Tile count is a wash. The loss lives in `10c4s_3q`, a 75-tile route, which is
also the one the base draws most often (57% of episodes, triggered by a milk
shop in the first three unlocks). Moot on the new base, but the method - split
the ladder record by the route actually drawn - is the first thing to run on the
router once it has ~50 episodes.

**"The gap to the top is a tiebreak."** It is, at the very top: Milan Leonard
(#2) won a sampled match by 5%. But in the band we actually get drawn against
(1,900-2,050) our losses were 24-46% of bank - economic, and exactly the size
the route change closes.

Engine check: `kaggle-environments` 1.32.7 (Aug 15) is still the latest
release, so the recorded tapes are current.

### The price gate does not transfer to the tape base - and the reason constrains every overlay

`_min_sell_price_gate` at 0.10 was +474 (22/24 margin vs `route_v20`) on the
Moon base. Ported verbatim onto `router_yhay.py` (the `_MARKET_PARAMS` table
checked field-by-field against the engine, ratio-0.0 build byte-identical to
stock, control +0):

| harness | wins | mean |
|---|---|---|
| mirror vs stock router, 6 seeds x 2 | **1/12** | **-3,729** |
| paired margin vs indarkarhana, 6 seeds x 2 | **0/12** | **-3,487** |

Seeds 1/2/3/5 lose the identical amount on both seat orders - a self-inflicted
loss, not a market race. The counters make it stranger: on seed 0 the gate
withholds **zero** units (the -967 is pure seat asymmetry), and on seed 2 it
withholds only **39** (36 MILK, 3 FERTILIZER) for a **-9,836** swing. A few
hundred dollars of forgone revenue cannot be the mechanism.

The mechanism is the base. The Moon route re-reads shed state every turn, so a
unit withheld today is offered again tomorrow. **A tape never re-plans**: a
trimmed `SELL` is never re-issued, and - the likelier cost, not independently
verified - the cash it would have raised was assumed by a later scripted
`BUY_SEED` / `HIRE` / `BUY_ANIMAL` order, which the engine then rejects
silently (`money < price`, no error), and the schedule runs on with a hole in
it.

Generalises, and it sets the rule for tuning this base: **on a recorded route,
any overlay that changes the cash trajectory is a bet against the script's own
bookkeeping.** Overlays that only repair what the script already intended
(a weed where it wanted to plant) are the safe class; anything that withholds,
reorders or resizes a market order is not, however well it measured on a
re-planning base.

### The router's one measured loss is a tape, not a weed

The router lost seed 0 on both seats to every opponent it otherwise beat.
Traced against `route_moon_md_floor_deficit` (58,027 vs 63,357): seed 0's
shop unlocks route to tape 3 (`BAKERY__PET_CAFE`), whose scripted
`BUY_ANIMAL SHEEP 2` at step 199 fires with **$68** in the bank against a $500
price and is rejected silently. Cash sits at **$0 for six consecutive turns**,
a cow starves and escapes at step 216, and the season ends with **three empty
pastures** against the opponent's none - ~9 live animals against 14.

Weeds are ruled out as the cause: the router's farm ends seed 0 with 1 weed
(opponent 12), and seed 1 - a decisive win - has *more* PLANT-on-weed
collisions (19) than the loss (7).

So a tape's cash schedule was recorded against one opponent's market and
breaks against another. That is the structural fragility of this base, and it
makes **per-tape robustness** the contested parameter: the routing table is
ten indices, and a fragile tape can be remapped away from.

A weed-repair overlay ported from the Moon base (substitute `DIG` when the
tape wants to `PLANT` on a weed, then replay the shifted schedule) does
exactly what it says - seed 0's 7 blocked plants go to 0 and the residual weed
to 0 - and is byte-identical on 4 of 6 seeds. Where it fires it lost the
mirror (-2,680 / -1,764 on seed 0) and won the foreign pairing (+5,762 on the
same seed). 1/12 on both harnesses at 6 seeds, most of them exact zeros -
inconclusive, being re-run at 18.

### Per-tape sweep: routing protects the floor, and picks the best tape once in six

Every tape forced from step 0 vs indarkarhana, seeds 0-5 x 2 seats:

| tape | wins | mean | min |
|---|---|---|---|
| 0 | 4/12 | -3,064 | -15,473 |
| 1 | 5/12 | +1,354 | -2,023 |
| 2 | **8/12** | +2,250 | -12,720 |
| 3 | 3/12 | -13,218 | **-46,428** |
| 4 | 4/12 | -10,881 | -27,660 |
| 5 | 4/12 | -4,215 | -13,306 |
| 6 | **0/12** | -7,139 | -18,897 |
| 7 | 3/12 | -8,401 | -24,255 |
| 8 | 4/12 | -4,270 | -29,386 |
| 9 | 4/12 | +1,061 | -1,547 |
| **stock, routed** | 7/12 | **+4,077** | **-4,183** |

The routed agent's floor (-4,183) is better than any single tape's floor, and
its mean beats every tape's mean. That is what the two-shop key buys. What it
does not buy is the best tape: the per-seed winner differs on 5 of 6 seeds
and the router matched it once (seed 3). The oracle gap is **27,938 over six
seeds, ~4,700 a seed** - against one opponent, and with forced tapes played
from step 0 rather than from the step-144 switch, so read it as a ceiling on
what better routing could be worth, not a measured lever.

Caveat that matters for any remap: the forced runs mostly played tapes on
seeds whose shop pattern would never route to them. Tape 6's 0/12 says
nothing about tape 6 under its own trigger (ICE_CREAM / SMOOTHIE combos, which
none of seeds 0-5 produce). Tape 3's -46k *was* under its own trigger (seed 0,
`BAKERY__PET_CAFE`). A remap is being measured on matching seeds only.

### Remapping the fragile tapes, measured under their own triggers

`SECOND_ROUTES` entries pointing at tape 3 (2 keys) and tape 6 (4 keys)
redirected to tape 0. Seeds chosen by a real-match census (see the engine
note below), 8 that route to tape 3 and 7 that route to tape 6, both seats:

| remap | mirror vs stock | paired margin vs indarkarhana |
|---|---|---|
| tape 3 -> 0 | **12/16**, +2,823 | 9/16, +274 |
| tape 6 -> 0 | **0/14**, -3,770 | 2/14, -2,417 |

Tape 6 is fine under its own trigger - the forced sweep's 0/12 was tape 6
played on seeds that would never have chosen it, exactly the caveat above.
Tape 3 -> 0 is a decisive win against the stock router and a coin flip
against a third party: "positive everywhere, convincing nowhere", so it is
not shipped. The tape-3 failure is real (the cash-starved sheep); tape 0 is
just not clearly the right substitute. Untested: routing tape 3's keys to
tapes 1, 2 or 9 (the three with the best floors in the forced sweep).

### Engine note: shop unlocks depend on what both players plant

`_spawn_weeds` (`kaggriculture.py:836-840`) calls `rng.random()` only for
tiles that are `None`, and the same per-day RNG then draws the day's shop
unlock. So the unlock sequence is a function of the seed **and** of how many
tiles each farm has planted that day. Verified: seed 0 unlocks
`YARN_STORE, BAKERY` under `pass`/`pass` and `BAKERY, PET_CAFE` under real
agents. A `pass`/`pass` seed census is therefore wrong for predicting real
routing - a census must be run under real agents. Across `router` vs itself,
`router` vs `indarkarhana` and the reverse seating, seeds 0-119 gave
byte-identical tape histograms, so between real tile-occupying agents the
routing is stable; it is only the empty-farm baseline that differs.

Tape histogram, 120 seeds, real agents: tape 0 x74, 4 x10, 1 x9, 3 x8,
6 x7, 2 x4, 5 x4, 7 x2, 9 x2, 8 never.

### No substitute for tape 3 clears the bar - the router rides unmodified

The two `SECOND_ROUTES` keys that reach tape 3 were pointed at each of the
three tapes with the best floors in the forced sweep, measured on the eight
real-agent-census seeds that actually route to tape 3, both seats:

| tape 3 -> | mirror vs stock | paired margin vs indarkarhana |
|---|---|---|
| 0 | 12/16, +2,823 | 9/16, +274 |
| 1 | 4/16, -2,900 | 3/16, -5,714 |
| 2 | 1/16, -2,393 | 2/16, -4,659 |
| 9 | identical to 1 | identical to 1 |

Tapes 1 and 9 are byte-identical from step 144 on (they differ only in
steps 73-143, before the second branch fires), so a remap to either is the
same substitute - confirmed to the dollar across 32 episodes. Bar was
>= 12/16 on both harnesses; nothing clears it. (The tape-0 row came from the
six-key `remap36` build, but the tape-6 keys cannot fire on seeds that route
to tape 3, so on these seeds it is the two-key remap.)

Tape 3's failure is real and diagnosed; swapping the whole tape is too blunt
a fix. What would address it directly - and is untested - is a **cash guard
on the tape's own scripted purchases**: when a scripted `BUY_ANIMAL` is about
to fire with insufficient money, re-issue it on the first later turn that
can afford it and shift the dependent PICKUP/PLACE sequence with it. That is
a repair of what the script intended, the safe overlay class per the price
gate note above. Everything else on this base today was either dead or
underpowered, so per the rule set before the sweep ran, tuning stops here and
the unmodified router is the submission.

### The ladder answer: 1,850 -> 2,472, rank 689 -> 59

`55891543` (`router_yhay.py`, unmodified) after 34 episodes on the evening of
2026-08-30:

| | previous best (`55809595`) | **router `55891543`** | same-day `55891517` |
|---|---|---|---|
| episodes | 89 | 34 | 32 |
| wins | 45/89 (51%) | **29/34 (85%)** | 22/32 |
| rating | 1,850.3 | **2,472.2** | 1,623.8 |
| our bank | 93,219 | **98,155** | 94,887 |
| opponent bank | 90,514 | **83,530** | 83,222 |
| opponent rating | 1,737 | 1,832 (20/32 above 1700) | 1,412 (1/32) |

Team score 2,459.1, **rank 59 of ~6,600** against 689 that morning. Best
previous submission of the project was 1,914.5.

**The bank relationship inverted, and that is the part that matters.** Every
submission before this one banked *less* than its opponents - the pooled
figure was 52,517 against 60,815, 16% behind. This one banks **17% ahead**,
against a *harder* field than the one we were losing to. `PUBLIC_META.md`
recorded that we won 36% in the 1700-1900 band; the router wins 85% against a
field averaging 1,832.

`55891517`'s 1,623.8 is **not** a comparable reading and is not evidence
against the deficit port: matchmaking gave it opponents averaging 1,412 with
one above 1700. Beating a 1,200 opponent barely moves a rating - the same
trap recorded for `55650592` vs `55687852`.

**Where the remaining gap is, stated precisely.** #1 is 3,040. The author of
this route, Yusuke Hayashi, sits at **2,919.9** - roughly 460 above our copy
of their own published agent, and they submitted again 33 minutes after we
did. A published notebook is not a team's live build. So the gap to the top
is not an unknown strategy; it is the delta between a public release and a
private one, and closing it means tuning this base rather than hunting for
another.

### Correction: the tape-3 "cash-starved sheep" does not reproduce

The seed-0 diagnosis recorded above - a scripted `BUY_ANIMAL SHEEP` firing at
$68 against a $500 price, silently rejected - **is wrong, and it was recorded
here as measured fact.** Re-checked by instrumenting the real engine's
`_commit_unit` rather than reading a trace: on seed 0, **26 of 26
`BUY_ANIMAL` commits succeed** against `route_moon_md_floor_deficit` and there
are zero rejections against indarkarhana. Real cash rejections do exist, but
on **seed 43** (a COW at step 170, a SHEEP at step 198), not seed 0.

So every remap measured against "tape 3 is cash-starved" was aimed at a
failure that was not there. The remaps still lost on their own merits, but the
reason given for running them was not established.

**Seed 0's three empty pastures have a different cause: the tape buys 26
animals and places 10.** Sixteen head, at $400-500 each, sit in the shed
producing nothing. That is not a cash bug and not something an overlay caused
- it is what the recorded schedule does in our episodes.

A cash guard was built anyway and measured: defer an unaffordable
`BUY_ANIMAL`/`BUY_LAND`, re-issue when affordable, and drive a
walk/PICKUP/PLACE state machine to deliver it. Mirror **2/16**, paired vs
indarkarhana **0/16** - and both numbers are noise, because the guard never
fired on any of the 16 census matches. Where it did fire for real (seed 43, a
$400 COW deferred six steps, re-issued, delivered and placed) the season
ended **worse**: 59,756 against the stock tape's 70,407. Once again: on a
recorded route, moving cash by $400 in week one re-rolls the remaining 700
turns.

Three implementation notes kept because each one would have shipped a
disaster: simulating a whole order's cost instead of the engine's per-unit
partial fills drives simulated money negative; a delivery state machine that
waits for an empty pasture parks a unit on `PASS` for 40 turns (-58,000);
and `market_price(item, inv, params)` indexes `params[item]` internally, so
passing `MARKET_PARAMS[item]` raises inside a `try/except` and silently zeroes
every simulated sale.

Generalises, and it is the repo's own rule turned on itself: **a diagnosis is
a measurement too.** This one was read off a trace and written up without
instrumenting the engine call it claimed was failing, and three sweeps were
scoped against it before anyone checked.

### Correction 2, and the real fragility underneath it

"The tape buys 26 animals and places 10" is **also wrong**, and wrong the same
way the cash-starved sheep was: counted from an action stream instead of the
engine. `PICKUP` moves several animals in one call (`["PICKUP","SHEEP",2]`)
while `PLACE` moves exactly one, so counting calls invents a gap. Instrumented
across 25 episodes, 9 of the 10 tapes and 3 opponents: **`BUY_ANIMAL` never
fails**, `PLACE` never fails for want of a pasture, and the buy/place gap is
**0 in 22 of 25 episodes**, 1-2 animals when it appears - about 1% of bank.

Two bad diagnoses in one afternoon, both from reading an action stream. This
repo already has the rule (`count what lands`) recorded twice, for `PLANT`
and for `SELL`. It now applies to diagnosis as well as measurement.

**What the instrumentation did find is real and larger.** `action_for_depth`
ends with:

    hands = list(action.get("hands") or [])
    hands.extend([["PASS"] for _ in range(max(0, expected - len(hands)))])
    action["hands"] = hands[:expected]

`expected` is our **live** hand count. The tape blindly replays a `HIRE`
order; our cash diverges from the recorded episode as soon as the opponent
does, so that hire can fail silently - and then `hands[:expected]` deletes the
tail of the recorded hand-action list for the rest of the day. On seed 0 that
is **138 dropped unit-actions in one day**: WATER x22, NORTH x24, EAST x16,
FEED x5, CARE x4, PICKUP x2, PLACE x2.

`hire_fail > 0` predicts `truncation > 0` with **perfect correlation across
all 25 episodes**, and the three episodes with any animal gap are exactly the
three with the largest truncation counts. The same seed and tape truncates
against `route_moon_md_floor_deficit` and in self-play but **not** against
indarkarhana, so it is a narrow cash-timing effect, not a fixed tape defect.

Only the animal sliver of that has been priced (~1% of bank). The dropped
watering and feeding have not.

### Six overlays, six failures: a blind tape replay resists being helped

The truncation above was priced properly before anything was built. It fires
on **9 of 123 instrumented episodes (7.3%)**, in two regimes:

| regime | what happens | cost |
|---|---|---|
| transient burst shortfall | the tape queues several `HIRE`s in one turn, cash runs out mid-batch, and the tape's own next turns catch up | 22-23 dropped actions; in 4 of 5 cases **100% of them `PASS`** - literally free |
| full-day cash trough | money sits at **$0 all day** | 138-184 dropped actions including 22-37 `WATER` - real, and **unreachable by any same-day fix, because the cash is not there** |

So the expensive case cannot be fixed by retrying, and the fixable case is
mostly free. Both repairs were built and measured anyway, 12 seeds x 2 seats,
three harnesses, exact-copy control at ~0, counting **activated** matches
separately:

| variant | mirror (activated) | vs floor_deficit | vs indarkarhana |
|---|---|---|---|
| `hireretry` (re-issue the failed hire) | **0/2, -23,042** | 0/4, -187 | 0/2, -1,483 |
| `nodrop` (re-pack high-value actions into surviving slots) | 2/2, +5,379 | 2/4, -5,393 | 0/2, **+0 exact no-op** |

`hireretry` is actively harmful and the reason is the point of this whole
section: **a hand hired one turn later than the tape recorded is a different
hand.** Seed 0 self-play, it fixed the hire deficit exactly (`hire_ok`
268 -> 274) and `feed_ok` collapsed **203 -> 135** with `animals_alive`
9 -> 5, because the wheat got picked up by a unit that was no longer where
the schedule assumed. `nodrop` is safe and a true no-op when inactive, but
clears only one of three harnesses on 2-4 activations - unresolved, not a win.

Two implementation notes worth keeping: reassembling the market list by
category every turn moved bank by ~$30 **on seeds with zero hire failures**,
because `_process_market` pairs our queue index *i* against the opponent's
index *i* - order is state. And a first version that cleared its pending flag
on any hand growth missed every partial multi-hire failure, i.e. was a silent
no-op on exactly the case it targeted.

**The tally for this base, one day:**

| overlay | result |
|---|---|
| minimum-price sell gate | 1/12, 0/12 |
| weed repair | 6/9 activated, underpowered |
| tape remaps (0, 1, 2, 9) | none clear 12/16 on both |
| deferred-purchase cash guard | never fires; harms when it does |
| hire retry | 0/2, 0/4, 0/2 |
| high-value action re-pack | 1 of 3 harnesses |

Generalises, and it is the through-line of every row: **a recorded route has
no state to correct, so every overlay is a perturbation rather than a
repair.** The schedule's later steps assume the exact positions, inventories
and cash the recording had; move any of them and the assumption fails
somewhere downstream, usually far from the change. The only overlays that
survived on the *re-planning* Moon base (the price gate, the MD lead) are
precisely the ones that died here.

What this predicts: the next real gain on this base is **not** an overlay. It
is either a newer public route, or a change to which tape is played - which
is why the ladder record split by tape is the thing to read next.

### The ladder record split by tape: no remap is justified yet

All 119 completed episodes across `55891543` and `55891517`, each replay
fetched and the tape read from its own `town.unlocked_shops` fed through the
router's imported `route_index`:

| tape | n | win rate | our bank | opp bank | margin | opp rating |
|---|---|---|---|---|---|---|
| 0 | 62 | 63% | 88,184 | 83,681 | +4,503 | 1,869 |
| 1 | 18 | 72% | 90,941 | 80,419 | +10,522 | 1,726 |
| 2 | 6 | **100%** | 96,825 | 84,018 | +12,807 | 2,101 |
| 3 | 3 | 67% | 48,972 | 37,484 | +11,488 | 1,585 |
| 4 | 9 | 78% | 93,008 | 85,414 | +7,593 | 1,957 |
| 5 | 9 | 67% | 88,867 | 73,315 | +15,552 | 1,602 |
| 6 | 6 | **33%** | 121,871 | 120,214 | +1,657 | 1,821 |
| 7 | 2 | 1/2 | 100,524 | 99,322 | +1,203 | 2,402 |
| 8 | 2 | 2/2 | 78,491 | 63,484 | +15,007 | 2,406 |
| 9 | 2 | 1/2 | 129,886 | 109,340 | +20,546 | 1,265 |
| **all** | **119** | **66%** | **90,908** | **83,584** | **+7,325** | **1,844** |

By opponent rating band:

| band | n | win rate | margin |
|---|---|---|---|
| 0-1500 | 20 | 100% | +34,883 |
| 1500-1800 | 49 | **57%** | +2,104 |
| 1800-2100 | 3 | 2/3 | -1,037 |
| 2100+ | 47 | 62% | +1,575 |

**No tape justifies a remap on this evidence.** Tape 2 is the standout (6/6)
and tape 6 the weakest (2/6), but both sit at n=6, tape 6's losses are narrow
(-112, -2,006, -2,645, -9,796) and two of its six draws were opponents rated
2,378 and 2,404. That neither confirms the local forced sweep's 0/12 nor the
later finding that tape 6 is fine under its own trigger - it sits between
them, and n=6 cannot settle it. Tape 3, whose -46k local floor was the
motivation for three remap sweeps, has been drawn **three times** on the
ladder and collapsed on none of them.

Two things worth carrying forward. **Tape 8 was drawn twice on the ladder and
never once in a 120-seed local census** - the local shop-unlock distribution
against one opponent is not the field's. And the weakest band is
**1500-1800 at 57%**, not the top: against 2100+ we win 62%. The old agent's
problem band was 1700-1900 and this one's is similar, so the mid-field is
still where the margin is thinnest even after a +600 rating move.

## Route generation five: the #2 team's schedule, spliced to the router's YARN_STORE tapes (2026-08-31)

Overnight the field resubmitted around us and the router slid from rank 59 to
**115 of 7,003** without changing - 2,470.9, flat for 40 episodes, 51/79 wins,
against a #1 at 3,025.7. The docs above already say where the next gain had to
come from: *not an overlay - a newer route, or a change to which tape is
played.* This entry is both.

### How the corpus was built

Two notebooks published on 2026-08-30 changed the method. The #3 team
published *how* they build tapes (pull public replays, replay one seat's
actions across thousands of seeds, keep what transfers), and a long
measurement of the whole field ("a field guide to replay agents") put numbers
on three things this entry relies on: the recording underneath is worth ~73
points of win rate between best and worst founder while a perfect market layer
with hindsight is worth ~1.7% of bank; the source team's rating predicts
whether its tape transfers *negatively*; and candidates must be scored against
the population the ladder actually deals you - ranked against the strongest
agents instead, the ordering *inverts*.

So: public replays are downloadable per episode (`kaggleusercontent.com/
episodes/<id>.json`, ~31 MB, no auth), and the episode list per submission is
an internal endpoint that accepts `{"submissionId"}` or `{"ids": [...]}` only
(not `teamId`) and rate-limits hard - it went 429 after 19 calls and stayed
there for hours, which is why #1's own tapes were never fetched. From 87
replays (32 of the top-60 teams plus 31 of our own episodes spanning opponent
ratings 583-2,529) both seats were extracted: **174 tapes**, keyed by the shop
unlocked at step 72 and the pair at 144.

**63 of the 174 match one of our ten tapes at >=90% agreement.** Fourteen
teams run our slot-0 tape alone. The public commons the router stands on is
also the field's, which is the structural reason mirror games tie at the
margin and why an unmodified public router has a ceiling.

### The screen, and what it found

Every novel tape (111) was replayed as a single-tape agent against
`router_yhay.py` on the census seeds of its own route key, both seats - the
router plays the incumbent tape there, so the margin is candidate-minus-
incumbent under a router opponent. Grouped by schedule family:

| family | tapes | teams | best LB rank | beat router | games | mean margin |
|---|---|---|---|---|---|---|
| the 51-tape cluster (one 649-action farmer line, 20 teams) | 50 | 20 | 9 | 10/50 | 127-233 | -3,038 |
| **the #2 team's family** | 10 | 5 | **2** | **7/10** | **55-15** | **+10,095** |
| everything else | 51 | - | - | 17/51 | - | mixed |

The largest family on the ladder loses to the router. The one that wins is a
single schedule - byte-identical through step 143, >=90% to step 400, the rest
differing only in sell ordering - run by A Poor Vul (#2), gogogo (#12), cmasch,
islet and Lucien de Rubempre. It is not a published notebook (checked against
every candidate on the Code tab, including skomuro's "silver medal route",
which is a third, unrelated tape).

### Why it cannot be swapped in, and what can

Its opening agrees with ours on **6% of actions over turns 0-71** - a different
family, so no tape from it can be spliced into the router at step 72 or 144
the way the ten existing tapes are (those agree 100% through step 143 with
each other; that shared opening is what makes yhay81's design work at all).

Replayed whole on 16 fresh seeds (200-215, never used to select anything)
against the router, all four family tapes tested came out identical, 20-12,
mean +254 to +918 - a coin flip on mean. But the per-seed pattern is not a
coin flip:

| first two shops | seeds | family vs router |
|---|---|---|
| YARN_STORE among them | 6 | **0/6**, -7,249 to -20,708 |
| no YARN_STORE | 10 | **10/10**, +841 to +25,957, mean +10.5k |

Seven cows and three sheep against the router's nine or ten sheep on the
YARN_STORE tapes: the family has no answer to a wool draw, and a large edge
everywhere else.

The two lineages build the **same farm** in the opening - 3 COW, 2 SHEEP,
12 MELON, 10 WHEAT, 12-13 hires by step 72; the 6% agreement is walk order and
hand order, not a different plan. So the handover the router already performs
at its branch points is possible in one direction: play the family schedule,
and at step 72 (YARN_STORE first) or step 144 (YARN_STORE second) hand the
season to the yhay tape the router would have chosen.

### Measured: seeds 200-231, both seats, vs `router_yhay.py`

| build | W-L of 64 | mean | median | worst |
|---|---|---|---|---|
| **family opening, hand over on YARN_STORE** (`agents/router_fam_yarn.py`) | **47-17** | **+9,533** | **+7,738** | -14,522 |
| family schedule alone | 41-23 | +3,956 | +5,812 | -20,708 |
| yhay opening, family after step 72 | 34-18 | +4,496 | +860 | -12,884 |
| hand over on BAKERY-first as well | 43-21 | +8,834 | +6,592 | -14,522 |

The splice recovers the YARN_STORE seeds: where the family alone lost
-11.9k/-20.7k/-7.2k on seeds 208/204/210 (YARN_STORE second), the spliced
build wins them +13.0k/+6.7k/+8.1k - the family's turns 72-143 are better
than ours and the yhay tape continues cleanly from them. The residual is the
seven YARN_STORE-*first* seeds, where yhay tape 1 on the family opening's
state loses 0.3k-3.5k against +7k to +32k on the other 25. Handing over on
BAKERY too is worse on every seed it changes; the family is only weak to wool.
Mirror control: 0-0 of 8, margin exactly +0.

This is the same size as the base swap that took us 689 -> 59 (+11,455,
10/12). Be exact about which seeds did what, because half of the confirm set
is contaminated: the tapes were screened on seeds 0-119, the YARN_STORE rule
was *derived* from the 16-seed run on 200-215, and only 216-231 saw nothing
before the confirm. Split accordingly:

| seeds | role | W-L of 32 | mean | median |
|---|---|---|---|---|
| 200-215 | rule derived here | 26-6 | +7,909 | +7,394 |
| **216-231** | **untouched** | **21-11** | **+11,157** | **+8,550** |

The untouched half is, if anything, the stronger one. Provenance and the
Apache 2.0 attribution for the yhay81 half are in the file header.

### The population check: equal on replays, better against everything live

The field guide's sharpest warning is that ranking against the strongest
agents inverts the ordering you get against the opponents the ladder actually
deals you. So both builds were also run, seeds 200-215 both seats, against a
ten-opponent panel: eight tapes replayed from the opponents `55891543` really
drew (ratings 583-2,529, chosen to span the band) plus the two strongest
live public agents we hold (kaito v48, indarkarhana).

| opponent | H1 W-L | H1 bank | router W-L | router bank |
|---|---|---|---|---|
| eight drawn-opponent replays (256 games) | 220-36 | 97,386 | 222-34 | 98,606 |
| kaito v48 (live, adaptive) | **30-2** | 90,007 | 26-6 | 86,449 |
| indarkarhana (live, adaptive) | **28-4** | 92,736 | 24-8 | 91,547 |
| **all** | **278/320** | 96,183 | 272/320 | 96,684 |

Read carefully, because the two halves say different things. Against
**replayed** opponents - fixed tapes that neither route nor repair - the two
builds are indistinguishable (220 vs 222 wins), and the spliced build banks
~1.2k less; against the one replay that is a stale copy of our own slot-0 tape
it is 18-14 where the router is 30-2. Against every **live** opponent - the
router itself (47-17), kaito (30-2 vs 26-6), indarkarhana (28-4 vs 24-8) - it
wins more. By seed class across all ten opponents the splice costs nothing:
YARN_STORE-first 52 vs 48 wins, YARN_STORE-second 54 vs 54, no wool 172 vs 170.

The reading that fits all of it: the family schedule does not out-farm the
router tape, it **out-sells it in company** - its edge is what it lets a live
co-seller bank alongside it, which a replayed tape (already off-route, selling
into the wrong shops) cannot express. That is exactly the mechanism the field
guide names for why one tape beats another, and it is the quantity the ladder
pays for. Floor: min bank 37,272 vs 40,492 over the 320 games.

Ship decision: it goes to the ladder in the slot `55891517` occupies (the Moon
deficit build at 1,626, kept only as a control), alongside `55891543`, so the
two can be read at equal episode count against a shared field.

### The ladder answer, and the second cut: the family's own wool branch

`router_fam_yarn.py` went in as `55908478` at 05:56 UTC. Four hours later:
**2,732.2, rank 16 of 7,045** (from 115 at 2,471), with #1 at 2,915.7. The
per-episode endpoint has been 429 all day, so win rate and opponent field are
unread and n is at most ~20 - by yesterday's measurement of two identical
agents, that is still inside the noise. The rank move is large enough to
believe; the exact number is not yet.

The one weakness the first cut left was the YARN_STORE-*first* draw (7 of 32
fresh seeds), where it hands over to yhay tape 1 on a foreign opening and
loses 0.3k-3.5k. The harvest holds the answer: `103391169_1`, the family's own
YARN_STORE-first branch, recorded by Lucien de Rubempre **against our router**
(105,851 to 92,407 under YARN_STORE -> PET_CAFE), opening **100% identical to
the base schedule over turns 0-71**. The step-72 handover to it is between
two recordings of one plan, not a splice across families.

Sixteen YARN_STORE-first seeds (census 2, 25, 28, 38, 42, 55, 61, 96, 118 plus
fresh 200, 206, 214, 217, 222, 226, 227), both seats, vs `router_yhay.py`:

| YARN_STORE-first handling | W-L of 32 | mean | median |
|---|---|---|---|
| yhay tape 1 (first cut, `55908478`) | 0-32 | -1,754 | -1,641 |
| **family wool branch, whole season** (`agents/router_fam_yarn2.py`) | **28-4** | **+8,527** | **+10,805** |
| family wool branch to 144, then yhay pair tape | 0-32 | -2,642 | -2,515 |

The tape had been screened on seeds 2, 25, 28, 38; on the twelve it had never
seen it is 10-2 (losses 118 -1,947 and 226 -4,417). Handing it to a yhay tape
at step 144 kills it again - the family's wool line has to be played whole,
which is the same lesson as the first cut read the other way round.

Three checks before it goes out. Off YARN_STORE-first seeds the two cuts are
the same policy: six non-wool seeds vs the router reproduce the first cut's
margins **to the dollar** (201 +15,069, 203 +2,001, 204 +6,702, 208 +13,002,
209 +25,957, 213 +13,860). Head-to-head, second cut vs first, seeds 200-231:
**14-4 of 64, +1,551**, every non-wool seed an exact tie and six of the seven
wool seeds won (226 lost -2,388). Mirror: +0 mean. Gate `['DONE','DONE']`.

It replaces `55891543` (the plain router, 2,461 - the slot is dead weight now
that the team score is the max) so `55908478` and the second cut can be read
against each other at equal episode count.

### Correction: the second cut is not worse, and the change was unmeasurable before it shipped

`55916283` (cut 2) read **2,575 against cut 1's 2,727 at n=64** and that looked
like a clean regression. All 137 ladder replays of the two submissions were
downloaded and split by the shop draw. The two agents differ on **exactly one**
branch - episodes where YARN_STORE unlocks first - so the split is the whole
experiment:

| submission | YARN first? | n | wins | our bank | margin | opp rating | min bank |
|---|---|---|---|---|---|---|---|
| cut 1 (yhay tape 1) | **yes** | 6 | **6/6** | 97,861 | +20,527 | 1,976 | 83,460 |
| cut 1 | no | 66 | 48/66 | 90,221 | +8,496 | 2,342 | 43,854 |
| **cut 1 all** | | 72 | 54/72 | 90,858 | **+9,498** | 2,311 | 43,854 |
| cut 2 (family wool branch) | **yes** | 5 | **3/5** | 105,773 | +9,212 | 2,212 | 85,672 |
| cut 2 | no | 60 | 43/60 | 83,942 | +9,503 | 2,184 | 32,587 |
| **cut 2 all** | | 65 | 46/65 | 85,622 | **+9,481** | 2,186 | 32,587 |

Read the `no` rows first, because there the two agents **are the same
program**. They post the same win rate (72.7% vs 71.7%) and cut 2 posts the
*larger* margin (+9,503 vs +8,496) - yet their mean banks differ by **6,279**
and their opponent fields by 158 points. That is the size of pure draw
variance on 60-odd episodes of identical code, measured here for free.

Season margins land within **17 dollars of each other**: +9,498 and +9,481.
The 152-point score gap is the opponent field (2,311 against 2,186 - cut 1
beat a field 125 points harder at the same rate), not the wool branch. On the
cell where the two actually differ the counts are 6 and 5; cut 1 went 6/6 and
cut 2 3/5, which leans cut 1 and settles nothing at n=11.

**The number that should have stopped this before it was submitted: a
YARN_STORE-first draw is 8-9% of ladder episodes** (6 of 72, 5 of 65), and the
local census agrees at 7.5% (9 seeds of 120). It was written up here as "~22%"
- that was a conflation of *YARN_STORE first* with *YARN_STORE anywhere in the
first two*, and it is the error that made the change look worth a slot. At the
true rate, the local wool-seed result (+8,527 on 28-4) has an expected
aggregate effect of **0.08 x 8,527 = ~680 bank** - below the ~903 that
byte-identical agents differ by. The change was **unmeasurable on the ladder
by construction**, and no per-episode reading was ever going to resolve it.

Generalises, and it is cheap to apply: **before spending a submission slot,
multiply the measured local effect by the fraction of games the change can
touch, and compare that to the noise floor.** A large margin on a rare branch
is a small number. This repo already had the rule for judging a change
(win count first, both harnesses); it did not have one for deciding whether
the ladder *can* see it at all.

Both cuts stay live. They are the same agent for 91% of games, so the pair is
now a second natural experiment on the noise floor rather than a comparison of
two strategies.

### And the season aggregate is inflated: exclude the opening burst before reading anything

The same 137-replay split, cut again by opponent rating, exposes a second
error that affects every number in this file, not just this comparison.

**The first 16-18 episodes of a submission are played against provisional-rated
opponents around 1,200, and we beat them by about +30,000.** After that the
matchmaking converges on a steady state of 2,550-2,700. So a season mean folds
two different games together. Excluding everything under an opponent rating of
2,000:

| | n | win rate | margin | opp rating |
|---|---|---|---|---|
| cut 1, all episodes | 72 | 75.0% | **+9,498** | 2,344 |
| cut 1, opponents 2000+ | 54 | 66.7% | **+2,244** | 2,630 |
| cut 2, all episodes | 65 | 70.8% | **+9,481** | 2,220 |
| cut 2, opponents 2000+ | 45 | 62.2% | **+1,584** | 2,521 |

The season margin overstates the steady-state margin by roughly **4x**. Our
real standing against the field we now draw is a **~65% win rate at about
+2,000 bank** - a genuine edge, and a much narrower one than +9,498 suggests.
It is also self-consistent: 65% against a 2,630 field implies a rating near
2,730, which is what the board says.

Two consequences. **Any future ladder comparison must drop the burst before
computing anything** - it is 25% of a submission's episodes carrying 4x the
margin, and two submissions with different burst lengths are not comparable at
all. And it re-prices the target: closing the 195 points to #1 means going from
~65% to roughly ~78% against a 2,650 field, which is a base-quality change, not
a branch fix.

On the original question the refined cut says the same thing as the crude one.
Cut 2's ten worst episodes: **nine of the ten sit in the shared cell**, where
the two agents are the same program, all against opponents rated 2,493-2,620.
In the divergent cell above the burst it is cut 1 3-0 and cut 2 1-2, on three
episodes each. Not settled, not worth a slot to settle, and both stay live.

## The field's schedule map, and why "find a better base" has run out of room (2026-09-01)

The episode endpoint unblocked overnight, so all 40 top teams' current
submissions were resolved and their recent episodes harvested: **376 tapes**,
both seats, clustered at 90% action agreement over turns 0-399. The map is
more decision-relevant than any single candidate in it.

| cluster | tapes | teams | anchored by | what it is to us |
|---|---|---|---|---|
| 0 | **72** | 29 | **#2 MtN** | the family screened on 2026-08-31 and **rejected** - 10 of 50 beat our router |
| 1 | 62 | 17 | #3 Driz Lo | matches yhay `ref:0` - **we already carry it** |
| **2** | **45** | **15** | **#4 islet** | **our live schedule** (islet, gogogo, boatlee, yarneo, us) |
| 4 | 19 | 9 | #3 Driz Lo | matches yhay `ref:1` - we carry it |
| 5 | 18 | 3 | #8 QQ Farming | novel, small |
| - | 3 | 1 | **#1 tetsuya** | singleton, matches nothing at all |

Three readings follow, and together they close a line of work.

**We already run a top-tier base.** Cluster 2 is the schedule behind #4, and we
are in it. Cluster 1 is the schedule behind #3, and it is `ref:0`, which the
router has carried since 2026-08-30. The single largest family in the field -
29 teams, anchoring **#2** - is the one our own screen measured as *worse* than
ours in direct play. So the teams sitting 90-100 points above us are not there
because of a recording we lack.

**And #1 cannot be copied, which is measurable rather than a guess.** Tetsuya's
three harvested games agree with each other **100% over turns 0-71**, then
0.36 and 1.00 over 72-143 (a real branch on the shop draw), 0.02-0.38 over
144-399, and **0.00 over 400-718 for every pair**. Zero self-agreement in the
last third of the season is not a route table; it is state-dependent decision
making. There is no fixed plan in there to take, which is exactly what the
public field guide predicted when it measured source-team rating as a
*negative* predictor of tape transfer.

What tetsuya's tapes do give is an economic profile, and two gaps are large:

| | our base | tetsuya |
|---|---|---|
| HIRE, turns 0-71 | 13 | **19** |
| WHEAT bought / sold, turns 0-71 | 23 / 11 | **59 / 48** |
| FERTILIZER bought / sold, turns 144-719 | 62 / 305 | **274 / 524** |

Those are quantities, not schedules, so they are testable without copying
anything - but note that each is a *purchase*, and this file already records
what inserting purchases into a recorded cash-flow schedule does.

**The gap we can name is the rim, not the tape.** Our agent replays a tape,
pads the hands list, and returns PASS on exception. That is the entire rim.
Every agent in the published survey of sixteen ships repair machinery on top -
retry what the tape asked for and could not have - and that survey calls it
"most of the value the rim adds". Six overlays failed here on 2026-08-31, two
of them repair-class, but all six were measured on the *yhay router* base, and
the reason recorded for their failure was specific to it: a blind replay of a
foreign schedule has no state worth repairing. The current base is a different
lineage. That makes repair a live hypothesis again rather than a settled dead
end - and it needs its own measurement, not an assumption in either direction.

One repair class is already closed by measurement: terminal liquidation is
monotone by construction, but end-of-season shed value is **65 for us against
21 for top-20 teams** - both effectively zero. There is nothing stranded to
collect.

### The 80-tape screen: #1's recording is worse than ours, and a tape cannot be spliced across openings

Every novel tape from a top-20 team was replayed whole against
`agents/router_fam_yarn.py` (our live agent, rank 18) on the census seeds
matching its own route key, both seats. 79 candidates, 594 games.

**Tetsuya's three tapes, from the #1 team, lose: 4-4, 4-4 and 0-8 (-13,773).**
The published field guide predicted this - source-team rating is a *negative*
predictor of tape transfer - and it is now measured on our own harness rather
than taken on faith. The strength of the leading agent is in machinery that
does not travel with the recording. **"Copy #1" is closed.**

24 of 79 candidates beat our live agent, and they concentrate hard: seven of
the top eight are YARN_STORE route keys, at +3,957 to +11,743, mostly 8-0.
Our wool handling is the weak spot in the current build.

**But assembling the winners into a router loses**, and the failure is the most
transferable thing in this entry. A 20-tape key-router scored **18-12, -834**
switching at step 144 and **20-22, -4,104** switching at 72 (worst game
-35,073) on fresh seeds 240-271. Per-seed, most seeds tie exactly (no tape for
that key) while the seeds that do switch produce both +9,555 and -16,699.

The cause is visible without any further games. **13 of the 20 winners share
only 6-53% of our opening over turns 0-71.** A tape is a plan timed against
the state its own opening produced; entering it at step 144 hands it a farm,
a bank and a shed it was never written for. It wins as a whole season and
loses as a continuation. The seven that *do* share our opening (>=0.90) are
not foreign at all - they are **islet (#4), xi luo (#16) and gogogo (#11),
our own cluster 2** - and five of the seven are the high-margin YARN keys.

Generalises: **before splicing a harvested tape behind a branch point, check
its agreement with the opening it will inherit.** Route selection is only safe
between recordings of the same plan; between plans it is a state mismatch with
a recording pasted over it. This is the same wall the six overlays hit on
2026-08-31, reached from the opposite direction - there the layer was foreign
to the tape, here the tape is foreign to the opening.

### The ladder pays for WINS, not for bank margin - and this file has been quoting the wrong number

Measured on our own 135 rated episodes, using each episode's `initialScore` and
`updatedScore`, restricted to steady state (both ratings >= 2,000, which drops
the opening burst):

| | n | mean rating change |
|---|---|---|
| wins | 68 | **+23.63** |
| losses | 37 | **-11.83** |
| wins, small-margin half (+119 .. +2,529) | 34 | +18.51 |
| wins, large-margin half (+2,709 .. +34,128) | 34 | +28.75 |
| losses, big-loss half (-11,791 .. -2,091) | 18 | -12.91 |
| losses, small-loss half (-1,696 .. -205) | 19 | -10.80 |

**`corr(rating change, margin | steady-state wins) = +0.002`.** Zero. Winning
by 34,000 is worth the same rating as winning by 119, and losing by 11,791 costs
the same as losing by 205. The apparent margin effect over the full record
(+0.584) is entirely the opening burst, where huge margins and huge rating gains
co-occur because the rating is converging up from 600 - not because the margin
earned it.

This matters immediately, because it inverts a live decision. The
Semyon Epanov schedule, replayed whole against `agents/router_fam_yarn.py` on
fresh seeds 400-431, both seats:

| | win-loss | mean margin | median margin |
|---|---|---|---|
| Semyon Epanov (#20) | **54-10 of 64** | **-795** | +2,096 |
| cygn (#14) | **52-12 of 64** | -907 | +1,784 |

By mean margin both look like losses. By the metric the ladder actually pays
they beat our live agent in **84%** and **81%** of games - it wins small and
often, and loses rarely and hugely (5 seeds at -7,700 to -24,500). A negative
mean bought with an 84% win rate is a **good** trade here, and this repo's own
"read the win count before any t-value" rule was right for a reason it had not
yet measured.

Both are pure blind replayers: one fixed 719-step schedule, byte-identical
across four and six different shop draws respectively, with **no routing at
all**. They beat a router.

Correction to earlier entries in this file: every "+X mean bank" claim used to
justify or reject a change was measuring a quantity the ladder does not score.
The win counts quoted alongside them were the load-bearing numbers all along.
Rankings by margin should be re-read as rankings by win count wherever the two
disagree - and they disagree here, on the largest candidate of the day.

### The population check, and what it rejected

Three candidates went to the same ten-opponent panel - eight tapes of opponents
`55908478` actually drew on the ladder (rated 583-2,529) plus kaito v48 and
indarkarhana - on seeds 200-215, both seats, 320 games each. Win count, since
that is what the rating pays:

| agent | panel record | vs `router_fam_yarn.py` head to head |
|---|---|---|
| `agents/router_fam_keys.py` (V4) | **280-40 (87.5%)** | 46-20 of 320 decided |
| `agents/router_fam_yarn.py` (live, rank 18) | 278-42 (86.9%) | - |
| Semyon Epanov's schedule | **262-58 (81.9%)** | **54-10 of 64** |

**Semyon Epanov's schedule is rejected, and it is the sharpest counter-example
this repo has recorded.** It beats our live agent in 84% of head-to-head games
- decisive by every rule in this file - and is 5 points *worse* against the
field. It is a counter to our specific schedule, not a better agent, and the
ladder matches us against the field. Shipping on the head-to-head number alone
would have traded 86.9% for 81.9% while every local reading said we had
improved. cygn's schedule (52-12 head to head) has the same shape.

This is the documented "head to head can bless a change that only works because
the opponent is a copy of us", in its sharper form: the opponent need not be a
copy, only a specific counter. **A head-to-head win against the incumbent is
not evidence of a field improvement. Only the panel is.**

V4 ships on a weaker claim than the ones this file usually makes, and the claim
is stated as it is: **+2 games in 320 against the base is inside noise.** It is
the base agent by construction on every draw outside its six route keys, it
wins more than it loses on the rest (46-20), its worst single game against the
base is -6,579 against an identical minimum bank, and the slot it occupies was
otherwise holding `55916283`, which is the same program as the base on 91% of
games. Weakly dominant, in a slot that was doing nothing.

## The eviction, the wave, and the sell-advance rim (2026-09-02)

### First, a correction: `55928263` evicted the best agent, not the duplicate

The entry above says `55928263` "replaces the near-duplicate slot". It did
not. The latest-2 rule evicts the **oldest** active submission, and the oldest
was `55908478` - the 2,722 agent. `55916283` (the yarn2 cut) stayed active. By
the 2026-09-01 19:55 UTC snapshot the team read **2,435.9, rank 186 of 7,216**,
because that is the better of the two submissions that were actually active.
The record of the evicted agent is frozen at 77 episodes; nothing about it is
lost except its slot.

### The field resubmitted on 2026-09-01, and our lineage stopped winning mirrors

`55916283`, in steady state (opponent rated 2,000+), before and after the wave:

| window | record | opponent rating |
|---|---|---|
| all 111 rated episodes | 45-66 (41%) | 2,519 |
| **last 30** | **4-26 (13%)** | 2,490 |

Not a rating artefact - 4 of 30 is p < 0.0001 against a coin. Every
top-20 team's last submission date on the leaderboard is 2026-09-01.

Replays of the last 24 episodes, our seat against the opponent's, action
agreement by window:

| group | n | agreement 0-71 / 144-399 / 400-718 | typical margin |
|---|---|---|---|
| **mirror: our schedule with a market rim** | 11 | 1.00 / 0.94-0.99 / 0.7-0.9 | **-96 to -2,311** |
| a related opening variant | 3 | 0.83 / 0.86 / 0.61 | -790 to +247 |
| our wool branch vs a different wool branch | 3 | 1.00 / 0.35 / 0.5 | -4,669 to -7,248 |
| unrelated agents | 2 | 0.12-0.14 | -1,147, -14,893 |

The mirror group is the story. Eleven different teams play our farm schedule
**action for action** (first divergence at step 120, and that one is an
order-of-orders change), and their per-product season SELL totals are ours to
within 3 fertilizer and 2 strawberries. The whole difference is **timing**:

| their SELL order relative to ours | count |
|---|---|
| same step | 1,969 |
| 1 step earlier | 114 |
| 2 steps earlier | 48 |
| 3 steps earlier | 16 |
| 5-6 steps earlier | 4 |
| later | 8 |

In a mirror match both agents hold the same goods on the same hour. Whoever
sells first takes the quoted price; the other sells into the crash their order
just made. That is the whole margin, a few hundred dollars out of ~100,000,
and the ladder pays for the win regardless of its size. Front-running a copy
of yourself by one hour is worth +23.6 rating per game.

### The rim: pull the tape's own SELL orders forward, never change them

`agents/router_fam_lead.py` = `router_fam_keys.py` plus: at step >= 144, look
`LEAD_K` steps ahead in the currently selected tape; any SELL of a product
other than WHEAT or FERTILIZER whose quantity the shed already holds is placed
now and skipped at its original step. Tape orders first, cap 10. Quantities
are untouched (verified: identical per-product season totals in a mirror
game). WHEAT and FERTILIZER stay on schedule because the tape feeds and
fertilizes out of them.

Measured, `fam/run_agents.py`, both seats:

| test | K=1 | K=3 | K=6 | K=12 |
|---|---|---|---|---|
| mirror vs `router_fam_keys`, seeds 200-215 (32 games) | 32-0, +1,907 | 32-0, +2,213 | 32-0, +1,854 | 32-0, +1,051 |
| vs the 9 recorded front-runners as tapes, seeds 200-207 (144 games) | 84-58 | - | **144-0** | - |
| base `router_fam_keys` on the same 9 | 64-80 | | | |

The base loses to the recorded front-runners locally the way it does on the
ladder (64-80). A one-step lead beats the one-step opponents and ties the
rest; K=6 beats every observed lead (max 6) in every game. K=12 is already
paying for the extra hours in lost recovery time (+1,051 against +2,213), so
the lead is the smallest one that clears the field, not the largest one that
still wins a mirror.

Non-mirror panel (8 drawn-opponent tapes, seeds 200-215): K=6 **230-26 (89.8%)** against the base's **222-34 (86.7%)** on the same eight opponents, and never worse on any single one:

| opponent | base | K=6 |
|---|---|---|
| 103310582_0 | 32-0 | 32-0 |
| 103330604_1 | 32-0 | 32-0 |
| 103366436_0 | 28-4 | **32-0** |
| 103391169_1 | 22-10 | **26-6** |
| 103395570_0 | 18-14 | 18-14 |
| 103397845_0 | 28-4 | 28-4 |
| 103404555_0 | 32-0 | 32-0 |
| 103415744_1 | 30-2 | 30-2 |

Selling an hour or two earlier is free against a non-mirror, and against the
two panel opponents that share our late-season sells it is a win. No slot
is being spent on a head-to-head-only claim this time: mirror, front-runners
and panel all point the same way.

**Size it honestly.** Mirrors were 11 of the last 24 draws and we lost 10 of
them. Flipping those returns the lineage to roughly its pre-wave standing -
rank ~20 - and it is only good until the field advances its own sells again.
It is a repair, not the 195-point lever to #1. What it does establish is the
class of lever that lever will come from: the recording underneath is now the
field's commons, so the remaining edge is in the rim, and the rim's first job
is the market.
