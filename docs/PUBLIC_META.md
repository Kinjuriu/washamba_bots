# The top-meta strategy is published, and it is 3-5x our agent

Source: [`boatlee/v16-rc5-high-score-8c-4s-premium-market-lead`](https://www.kaggle.com/code/boatlee/v16-rc5-high-score-8c-4s-premium-market-lead)
(183 votes), on the competition's public Code tab.

**No third-party code is committed here.** This records the measurements and the
route spec so we can act on them; the notebook itself stays where it is.

## Measured against our agents

Head to head, our `main` (the land build) in seat 0:

| seed | ours | notebook agent |
|---|---|---|
| 0 | 53,884 | **148,321** |
| 1 | 29,602 | **123,856** |
| 2 | 29,450 | **83,451** |

Against `refactor/phase3-land-and-second-animal` (Stephane's build, live as
`55630182`):

| seed | phase3 | notebook agent |
|---|---|---|
| 0 | 35,021 | **182,302** |
| 1 | 29,498 | **118,585** |

Its own self-play: 52,298 / 52,537 on seed 0 and 124,172 / 123,166 on seed 1.

## What it does

Per the notebook, reconstructed by majority vote across three public replays of
another competitor's submission (`55440039`), matching at 99.91% of decision
steps:

- **three** unlocked quadrants, not the two we buy
- **4 SHEEP immediately, 8 COW by step 192** - a 12-animal herd
- mixed WHEAT / STRAWBERRY / MELON program
- daily HIRE, FEED, CARE, harvest and fertilizer work
- produce released in repeated premium-goods market waves, with a one-turn
  market lead on MELON, MILK, STRAWBERRY and WOOL

Mechanically it is a compressed hardcoded action schedule with drift repair -
it replays the route and fixes up weeds that block a scheduled PLANT or
BUILD_PASTURE.

## Why this matters beyond the score

**It answers the question three of our experiments failed on.** `docs/ANIMAL_ECONOMY.md`
concluded that a 12-animal herd was unreachable from our crop-first economy and
that no single-constant path exists between the two equilibria. That conclusion
stands - but the route shows the destination is real, reachable, and what it
costs: three quadrants of land and the whole starting stake committed to
animals up front.

**And it is the strong reference opponent we could not build.** #27's opponent
was neutralised when its settings shipped in #29, and `replay_shape_agent` banks
705-18,280 against our 67,586. This agent beats everything we have by 3-5x, so
using it as a sparring partner immediately unblocks every scale measurement that
has been unreadable all week - including #23, which is blocked on exactly that.

## Open questions before anything is submitted

1. **Licence.** The notebook metadata pulled via the API carries no licence
   field and the page is JS-rendered, so it could not be confirmed
   programmatically. Kaggle notebooks carry an author-selected licence; check it
   on the page before reusing the code in a submission.
2. **Provenance.** The notebook is itself a reconstruction of a third party's
   submission from their public replays. Using public notebook code is ordinary
   Kaggle practice, but a submission built from it is not our strategy, and that
   is a call for the team rather than a technical decision.
3. **Robustness.** A hardcoded route is brittle by construction. Its self-play
   spread (52k on one seed, 124k on another) is far wider than ours, and it has
   not been tested against the opponents we actually draw.

Using it as a **harness** carries none of questions 1-3 in the same way, and is
worth doing immediately regardless of what we decide about submitting.

---

# What the ladder said back (2026-08-22)

Two arms ran simultaneously as our only active submissions, which makes this the
cleanest A/B we have had: the stock route as the control, and one constant
changed as the candidate.

| | submission | episodes | rating |
|---|---|---|---|
| stock route, lead 1 | `55638404` | 152 | 1,665.0 |
| **lead 3** | `55650592` | 135 | **1,755.5** |

At an equal 135 episodes that is **1,755.5 against 1,701.1**. **Do not quote
that 54-point gap as the result** - our own measured noise floor is ~100 points
and identical code has read 86 apart. The rating is not the evidence.

## Matchmaking pairs by rating, so the top of the board is invisible

`experiments/opponent_strata.py` splits our own episodes by the opponent's
rating going into the match. Pooled over both arms, 287 episodes:

| opponent rating | n | our bank | opp bank | margin | wins |
|---|---|---|---|---|---|
| 0-1200 | 13 | 109,905 | 48,899 | +61,006 | 13/13 |
| 1200-1500 | 9 | 96,089 | 81,888 | +14,201 | 8/9 |
| 1500-1700 | 63 | 93,180 | 90,536 | +2,644 | 39/63 |
| **1700-1900** | **191** | **89,502** | **92,068** | **-2,566** | **69/191** |
| 1900-2200 | 11 | 81,900 | 89,747 | -7,847 | 2/11 |

**We never played anyone above 2,200.** The 2,500+ teams are not opponents we
are losing to, they are opponents we are not drawn against. There is no single
match to win against the leaders - the only route up is through the 1700-1900
band, where two thirds of our episodes are played.

## In that band the economy is level and the matches are coin flips

Losing by 2,566 on a 90,000 economy is a 3% deficit, but we win only 36% there.
That combination only happens if the matches are near-ties. They are:

| in band 1700-1900 | lead 3 | stock |
|---|---|---|
| episodes | 104 | 87 |
| **median** margin | **-502** | **-138** |
| decided by under 5,000 bank | **83 (80%)** | **62 (71%)** |
| **of those near-ties, won** | **49 (59%)** | **17 (27%)** |

That is the finding. **Same route, same opponents, level economy - and four out
of five matches turn on a rounding error.** The mean margin is nearly identical
between the two arms (-2,554 against -2,581) because it is dragged by a tail of
blowout losses to agents on a *different* route. The mean cannot see the effect
at all; the near-tie conversion rate doubles.

This is what the local sweep predicted and it is the mechanism, not a
correlation: two agents on an identical schedule bank identical money, so the
match is decided at the order book, and selling three steps early is reaching it
first.

One cost, recorded honestly: lead 3 loses *harder* when it loses (mean loss
margin -6,044 against the stock route's -4,077). Bradley-Terry counts wins, not
margins, so this is an acceptable trade - but it is a real one.

## What this rules in and out

- **Not an economy problem.** We bank what the band banks. Chasing a bigger farm
  is aiming at a gap that the data says is 3%.
- **A mirror-tiebreak problem.** 80% of the matches we care about are decided
  under 5,000 on 90,000. Every contested parameter of the shared route is worth
  more than any amount of yield.
- **Forking a newer public notebook does not obviously help.** It buys that
  notebook's saturated rating and puts us back in a mirror pool at 50%. The
  lead-3 result says the edge came from *modifying* the route, not from having
  it. Any newer base has to come with its own contested parameter.

## Dead end: front-run *volume* is closed, because it is stock-bound

The obvious follow-up to the lead was to pull more units forward, not just pull
them earlier. `_VOL` multiplies the quantity `_front_run` moves; everything else
is unchanged, so `_VOL = 1.0` reproduces the shipped agent exactly and rides
along as a control.

6 seeds x 2 seats against `agents/meta_lead3.py`:

| `_VOL` | wins | mean margin | median |
|---|---|---|---|
| **1.0 (control)** | 3/12 | **+0** | +0 |
| 1.25 | 6/12 | -71 | -30 |
| 1.5 | 6/12 | -90 | +10 |
| 2.0 | 6/12 | -89 | +18 |
| 3.0 | 5/12 | -131 | -74 |

The control returning exactly 0 is the harness telling the truth (its 3/12 is
the documented seat asymmetry: three seeds tie exactly, three split one-all).
Every real arm is a coin flip at a slightly negative mean. **No candidate.**

**And the mechanism was visible before the sweep ran, by checking the counter
the knob was meant to move.** `quantity = min(want, stock - reserve)` - the
route already sells essentially everything it holds at the moment it sells, so
asking for double buys a few percent:

| item | base | `_VOL = 2.0` |
|---|---|---|
| MELON | 126 units | **126 - unchanged** |
| MILK | 323 | 329 |
| STRAWBERRY | 321 | 335 |
| WOOL | 154 | 180 |

MELON, the most valuable premium good, does not move at all. Generalises:
**a multiplier on a quantity that is already inventory-limited is a no-op
wearing a knob.** The lead works by selling the same units into a better price,
not by selling more of them.

## Resolved: the lead is a pure timing change, and the volume axis is closed both ways

`_front_run` overwrites `state["due"]` wholesale every time it pulls, so a pull
whose repayment has not yet come due is cancelled by the next pull. Counted
against the route, **28 of 83 pull opportunities sit inside another pull's
repayment window** - and that is impossible at the stock lead of 1, because a
1-step window has no interior. So on paper `_LEAD = 3` did two things: it sold
premium goods earlier, *and* it stopped giving some of that volume back.

**Measured, the second effect does not exist.** A per-item repayment ledger
(`ledger.py`: `state["ledger"]` keyed by due step, so nothing is clobbered)
plays **byte-identical episodes to the unfixed agent** - same banks, every seed,
every seat:

| | seed 0 | seed 1 | seed 2 |
|---|---|---|---|
| exact control vs base | -239 | +1,004 | -60 |
| **ledger vs base** | **-239** | **+1,004** | **-60** |

8 seeds x 2 seats: **ledger 5/16, mean +0, median +0 - the same figures the
exact control returns.**

**Why, and this is the part worth keeping.** The ledger *does* change what we
emit: 900 premium units requested against the unfixed agent's 924, where 900 is
exactly the route's own planned total (MELON 126 / MILK 320 / STRAWBERRY 300 /
WOOL 154). Those 24 extra units are **phantom** - `_front_run` sizes a pull off
shed stock at the moment it pulls, so the un-repaid order it leaves behind at
the later step is asking for goods the shed no longer holds, and the engine
drops it. The clobbering is real, it inflates the action histogram, and it
sells nothing.

Generalises: **an unexecuted order is not a position.** A diff in requested
volume is not a diff in traded volume, and on this engine the two come apart
silently - exactly the trap `CLAUDE.md` already records for `PLANT`, where the
engine drops requests that exceed held seed. Count what lands.

**Deliberately over-selling does not work either.** `norepay.py` skips
repayment entirely, lifting requested premium volume to 1,106 against the
route's 900 - a real 23% overshoot, not a phantom one. It is **8/16, mean -38,
median +79**: a coin flip.

So both directions of the volume axis are now closed - more per pull
(`_VOL`, above) and more pulls left unpaid (`norepay`) - and the shipped agent
does exactly what its header claims: **the same volume, three steps earlier.**
That is a cleaner result than the alternative. Whatever comes next has to move
*when* or *what* we sell, not *how much*.

## The lead is not one number: it is four, and only two of them matter

`_LEAD` applies one constant to MELON, MILK, STRAWBERRY and WOOL. Those markets
have very different decay shapes, so a single constant is a compromise. Testing
one item at a time against the shipped agent, 8 seeds x 2 seats:

| arm | wins | mean margin | median |
|---|---|---|---|
| control | 5/16 | +0 | +0 |
| MELON -> 1 | 5/16 | **+0** | +0 |
| MELON -> 6 | 5/16 | **+0** | +0 |
| STRAWBERRY -> 1 | **1/16** | **-1,414** | -1,656 |
| **STRAWBERRY -> 6** | **15/16** | **+983** | +1,202 |
| WOOL -> 6 | 12/16 | +194 | +152 |
| MILK -> 6 | 4/16 | -938 | -1,057 |

**MELON is never front-run, at any lead.** Both arms reproduce the control's
numbers exactly, which can only happen if the code path never fires - and its
emitted sell steps are byte-identical at leads 1, 3 and 6. The cause is the
stock cap: `quantity = min(target, stock - reserve)`, and the harvest -> PICKUP
-> SELL pipeline delivers MELON just in time, so the shed holds no spare when a
pull is attempted. **Our most valuable premium good has been outside this
mechanism the whole time.** Note this is also why the `_VOL` sweep above could
not move MELON by a single unit - one cause, two dead sweeps.

**STRAWBERRY is where the lead-3 win actually lives.** Reverting it alone to
lead 1 gives back -1,414 at 1/16, close to the entire original gain, and
pushing it to 6 is +983 at 15/16 - the same shape as the original lead-3
discovery (8/8, +1,646).

**MILK wants the opposite direction.** 4/16 at -938 when pushed to 6.

So the uniform constant was averaging over items that want different answers.
Generalises: **before tuning a constant, check how many distinct things it is
applied to.** A single knob across four differently-shaped markets can only be
right for one of them, and can be inert for another without anyone noticing.

## Confirmed at 12 seeds: STRAWBERRY 6 + WOOL 6

Round 2 mapped each item's curve, then the winners were re-measured together at
the repo's standard 12 seeds x 2 seats, against the shipped agent:

| item | 1 | 2 | **3 (shipped)** | 6 | 8 | 10 | 12 |
|---|---|---|---|---|---|---|---|
| STRAWBERRY | -1,414 (1/16) | - | control | **+983 (15/16)** | -40 (9/16) | +702 (13/16) | -76 (8/16) |
| MILK | -110 (6/16) | -124 (4/16) | **best** | -938 (4/16) | - | - | - |
| WOOL | - | - | control | **+194 (12/16)** | +126 (12/16) | - | - |
| MELON | +0 | - | +0 | +0 | - | - | - |

**MILK is already correct at 3** - every deviation loses in both directions.
That is a real result, not a null one: it says the stock constant was right for
that item and wrong for STRAWBERRY.

**STRAWBERRY's curve is not monotone**, and that is recorded rather than
smoothed over: 1 << 3 < 6 is unambiguous, but 8 and 12 dip while 10 recovers.
Either 16 matches is too few to separate them, or it is a resonance with the
spacing of the route's 20 STRAWBERRY sell steps. **6 is a measured point, not a
located optimum** - treat any claim about the shape between 6 and 12 as
unsupported.

Confirmation, 12 seeds x 2 seats = 24 matches:

| candidate | wins | mean | median |
|---|---|---|---|
| exact-copy control | 6/24 | +0 | +0 |
| STRAWBERRY 6 | 22/24 | +1,016 | +1,110 |
| **STRAWBERRY 6 + WOOL 6** | **23/24** | **+1,306** | **+1,351** |
| STRAWBERRY 10 | 20/24 | +725 | +951 |

The two effects are close to additive (+1,016 and +194 separately, +1,306
together), which is not something to assume - they share the shed and the
ten-orders-per-turn cap - so it was measured rather than inferred.

Shipped as `agents/meta_per_item_lead.py`. Entrypoint rule checked (`agent` is
the last callable) and the self-play gate returns `['DONE', 'DONE']`.
