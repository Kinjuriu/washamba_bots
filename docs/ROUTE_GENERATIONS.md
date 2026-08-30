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
