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

### Next lead, untested

In a contested mirror we spend **$6,156 on STRAWBERRY seed to earn $3,030**
selling strawberries, and MILK returns $15.7/u. Both are measured in the
harshest possible case - two identical agents flooring the same market - so
expect better against a varied field. The route is a recorded action plan, so
cutting a crop is not a constant tweak; `_MIN_SELL_PRICE_BY_ITEM` exists so a
per-item floor can be swept without touching the gate logic again.
