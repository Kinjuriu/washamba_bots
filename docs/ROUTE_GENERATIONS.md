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
