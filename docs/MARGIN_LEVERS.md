# The ladder is decided by ~1% of bank, and we were burning $600 a season

> **VERDICT, 2026-09-07. The build this file recommended lost 637 places, and
> the reason is a test I ran on one lever and not the other.**
>
> `56027523` (both levers, on the `router_yuan_cov` base) was submitted
> 2026-09-05. Two days and 405 episodes later the team is **rank 878 at
> 2,079.3**, down from **rank 241 at 2,433.8**. The field did not deflate -
> #100 rose 2,594 -> 2,621 and #250 rose 2,423 -> 2,487, and 2,433.8 would
> still rank 314 today. The drop is ours.
>
> **What the levers were actually worth, in absolute self-play bank:**
>
> | build | mean | vs previous |
> |---|---|---|
> | `router_yuan_cov` (base) | 96,867 | - |
> | `+ _trim_seed_buys` | 97,190 | **+323** |
> | `+ _sells_first` (shipped) | 97,192 | **+2** |
>
> `_sells_first` adds **+2**. Its 63-1 mirror record was entirely price taken
> off the opponent, never revenue added - **the exact property used two
> sections below to disqualify `LEAD_K` 6->9.** That test was applied to the
> rim and not to the reorder, and the reorder shipped on a mirror number alone.
>
> **The generalisable rule, stated properly this time: in a contested market,
> measure every candidate lever's ABSOLUTE self-play bank before its mirror
> record.** A mirror win with no absolute gain is a front-running weapon: it
> pays only against opponents still on the old schedule, expires when the field
> matches it, and is indistinguishable from a real improvement in head-to-head.
> Lever 1 passes that test (+323, and +547 on 19/19 panel opponents). Lever 2
> fails it. `LEAD_K` 6->9 fails it. They are the same finding three times.
>
> **Second error: the base.** Both `cov`-derived builds plateaued far below the
> `router_yuan_nf` build they replaced, and both were still falling when read:
>
> | submission | agent | n | rating | last-100 wins | last-100 field |
> |---|---|---|---|---|---|
> | `55992408` | `router_yuan_nf` | 328 | **2,431.7** | **54%** | 2,409 |
> | `56019070` | `router_yuan_cov` | 496 | 2,075.1 | 36% | 2,177 |
> | `56027523` | both levers on `cov` | 405 | 2,053.7 | 32% | 2,136 |
>
> At matched `n` all three win ~2/3 of games, and the rating gap tracks the
> opponent field almost exactly (f2,259 / f2,148 / f2,026 at n=328) - but `nf`
> equilibrated at 54% and held, while both `cov` builds are at 32-36% and
> sliding. **This file's own opening section flagged `56019070` as unproven and
> said not to plan around it; the levers were then built on it anyway.**
>
> **Unresolved and worth someone's time:** `cov` banks *more* than `nf` in
> self-play (96,867 vs 92,250) and measured 38-12 on fallback seeds, yet rates
> ~350 points worse over 496 ladder episodes. Local and ladder disagree on the
> coverage change and the mechanism is not known.
>
> **The corrected build is `agents/router_yuan_nf_trim.py`** - the `nf` base
> plus lever 1 only:
>
> | | |
> |---|---|
> | vs `router_yuan_nf`, seeds 200-215 x 2 seats | **28-0 of 32, mean +595, worst +0** |
> | absolute self-play, 8 seeds | mean **92,735** (+485), floor **59,450** (+600) |
> | pre-submit gate | `['DONE','DONE']` |
>
> Mean *and* floor improve, and it never loses a game - lever 1 is recovered
> dead cash with no second-order term. The shipped two-lever build had a
> -1,590 worst case; the reorder was the source of that variance.
>
> Everything below is preserved as written on 2026-09-05, including the
> reasoning that was wrong.


**2026-09-05.** `washamba_bots` sits at **rank 241 of 7,666, score 2,433.8**.
The leader (`keiz`) is at **3,061.2**; rank 44 is 2,721.9, which is where our own
`55908478` finished on Aug 31 before it was evicted at 77 episodes.

This file records what the ladder record actually says about where the remaining
gap is, and the first lever measured off it.

## Our agent has converged, and it converged at a coin flip

`55992408` (`router_yuan_nf`) has 304 rated episodes. Read as a whole it looks
strong - 203/304, mean bank 97,119 against 79,630. Read as a time series it has
stopped moving:

| window | n | wins | our bank | opp bank | opp rating | rating |
|---|---|---|---|---|---|---|
| first 101 | 101 | 85% | 106,738 | 68,103 | 1,969 | 2,319 |
| last 100 | 100 | **54%** | 88,795 | 88,703 | **2,405** | 2,434 |

That is what a converged Elo looks like: matchmaking has walked us up to a band
where we win half. **Our true strength is ~2,434.** The early 85% is the climb
through a weak field, not evidence about the agent.

`56019070` (the 26-key coverage fix) is at 87% over 101 episodes but against a
1,870 field, and at the *same* episode count it reads 2,180 against `55992408`'s
2,319. Coverage is not disproven - it is a sub-$1,000 change, which this repo
already knows the ladder cannot resolve - but it is **unproven**, and nothing
should be planned around it converging high.

## Every generation since Aug 31 landed lower at equal episode count

| submission | agent | n | rating @77 | final | mean bank |
|---|---|---|---|---|---|
| `55891543` | yhay router base | 98 | 2,472 | 2,453 | 92,012 |
| `55908478` | gen5 splice | 77 | **2,722** | 2,722 | 90,165 |
| `55916283` | gen5 cut 2 | 148 | 2,577 | 2,395 | 86,212 |
| `55948802` | sell rim K6 | 326 | 2,550 | 2,194 | 81,739 |
| `55973335` | gen6 am | 147 | 2,381 | 2,285 | 86,460 |
| `55981065` | gen6 yuan (wheat flip) | 270 | 1,937 | 2,114 | 78,266 |
| `55992408` | yuan no-flip | 304 | 2,248 | 2,434 | 97,119 |
| `56019070` | key coverage | 101 | 2,133 | 2,180 | 102,968 |

**Bank rose monotonically across the generations and rating did not follow.**
The mechanism is in `docs/ROUTE_GENERATIONS.md` already: the field harvests each
other, and copies of each route are on the ladder within ten hours. We upgraded;
the band upgraded with us; relative position held. **Harvesting the tier above
buys parity with its current plan for about a day, not a lead.**

## The top band is not out-playing us - it is out-margining us by ~1%

52 of our episodes were against opponents rated >2,650 at the time. The record
is **25-27** - a coin flip - and the economy is level to a rounding error:

| | ours | theirs |
|---|---|---|
| mean bank over the 52 | **87,491** | **87,263** |

Mean margin **+229 (+0.26%)**, median **-109**. **16 of the 27 losses are under
$2,600 and 8 are under $1,000.** Individual games:

| episode | opponent rating | our bank | their bank | margin |
|---|---|---|---|---|
| 103980175 | 2,745.9 | 74,487 | 74,692 | **-205** |
| 104460032 | 2,747.4 | 44,816 | 45,114 | **-298** |
| 103993606 | 2,771.5 | 117,160 | 117,825 | **-665** |
| 103977923 | 2,768.3 | 119,158 | 119,824 | **-666** |

Byte-level diffs of those replays: `103993606` and `104460032` agree with the
opponent **1.00 over steps 0-71, 0.99 over 72-143 and 0.98-0.99 over 144-400.**
They are not rivals running a better plan. **They are copies of our own tape**,
and they beat us by a few hundred dollars.

**This is the single most important number in the file.** We are not behind the
2,650+ band on strategy, production or economy - we bank 0.26% *more* than it
does across 52 games and still split them 25-27. The whole of our distance from
the top of the leaderboard is which side of a coin flip we land on, and the coin
is weighted in units of a few hundred dollars.

## What a small universal edge is worth

Across 813 rated episodes the margin distribution is dense at zero - median
**+832**, IQR **-3,037 .. +6,860**. So:

| universal bank edge | games flipped (of 813) | win-rate points |
|---|---|---|
| +$500 | 33 | **+4.1** |
| +$1,000 | 62 | **+7.6** |
| +$2,000 | 95 | +11.7 |
| +$3,000 | 113 | +13.9 |
| +$5,000 | 137 | +16.9 |

The ladder pays for wins, not margin (`corr(rating, margin) = +0.002`), so this
is the conversion rate that matters. **A few hundred dollars a season is a real
lever here, and a plan-level rewrite is not the only way up.**

## Lever 1: stop buying seed we never plant

In `103993606` the whole -665 is one order. At step 265 we issue
`BUY_SEED STRAWBERRY 23`; the opponent issues `17`. The gap opens at exactly
-600 at that step and never closes. We finish the season holding **6 STRAWBERRY
seeds**; they finish holding none.

Seed left at turn 720 scores nothing and **cannot be sold back** - only `WHEAT`
and `FERTILIZER` can be repurchased, and no seed can be sold at all. It is cash
deleted from the bank.

Static audit of all 65 tapes in `router_yuan_cov.py`:

| | |
|---|---|
| tapes that buy seed they never plant | **36 of 65** |
| mean dead cash per tape | **$390** |
| worst tape | **$1,110** |
| total surplus STRAWBERRY across tapes | 247 units |
| steps where it happens | **264, 624, 669 - all of them** |

Every trimmable order lands at step >= 144, where `_which` has already settled
on its final key tape and never switches again. That makes the fix exact.

`agents/router_yuan_seedtrim.py` = `router_yuan_cov.py` plus `_trim_seed_buys`:
cap every `BUY_SEED` at what the selected tape still plants, minus what the shed
already holds.

**The cap cannot starve a planting.** Buying `remaining - held` leaves exactly
one seed for every `PLANT` left in the tape, so the engine's all-or-nothing drop
(it rejects *every* `PLANT` of a crop on a turn that asks for more than is held,
`kaggriculture.py:920-931`) can never fire because of the trim. `remaining`
counts the current step too, which over-buys by at most one turn's plantings
rather than risking that.

Measured, `experiments/tapes/run_agents.py`, seeds 200-231, both seats:

| | |
|---|---|
| vs `router_yuan_cov.py` (live) | **39-1 of 64, mean +452, median +600** |
| exact ties | 24 seeds (tapes with no surplus - nothing else moved) |
| worst | -3,226 (one seat, one seed) |
| top-band panel, 19 opponents x 8 seeds x 2 seats | **+547 mean, better on 19/19, worse on 0, min +335** |
| panel record | control 268-36, candidate **270-34** |
| pre-submit self-play gate | `['DONE','DONE']` |

The panel delta is **+566 on 17 of the 19 opponents** - the same number every
time, because it is the same tape leaking the same dollars regardless of who is
on the other side. That is the signature of a universal lever rather than a
matchup effect.

**Every non-zero per-seed delta is exactly the dead-seed value of the tape that
seed selected** (+600, +740, +780, +1,110) - the same season with the cash left
in the bank.

The one exception is worth naming, because it is a second-order effect and not a
starved planting. Seed 228 reads **+5,446 in seat 0 and -3,226 in seat 1**, both
far larger than that tape's $1,110 of dead seed, and averaging to exactly
+1,110. Dropping a `BUY_SEED` shortens the turn's market list, so every later
order moves one index earlier, and the engine processes both players' orders in
index lockstep - so the trim also changes *when* our SELLs land relative to the
opponent's. That is a coin flip per seat, it nets out across 64 games, and it is
the same mechanism the sell-advance rim exploits deliberately.

Generalises: **audit a harvested tape for spend that produces nothing before
turn 720.** A recording is a snapshot of one season's choices, and nothing in
the harvest pipeline checks that its purchases were used. Checked and clean in
the same audit: end-of-season shed is empty (liquidation works), fertilizer is a
net revenue stream (55 bought against 1,673 sold), plantings too late to yield
cost only $14-20 a season, and no tape ever issues more than the 10-order market
cap (1,686 steps sit exactly at 10, none above).

### One idea killed on inspection - do not rebuild it

The tape issues deliberately oversized SELL orders (`SELL EGG 2000`) as a
sell-everything idiom. Measured against the *previous* step's shed, 101 SELL
orders a season look unbacked and the fill rate reads 5%, which suggests
dropping them to free order slots and pull real sells to a lower index.

**That measurement is wrong and the idea is unsafe.** `_apply_unit_action` runs
for every unit *before* `_process_market` in the same step
(`kaggriculture.py`, the interpreter's step body), and `PLACE` deposits into the
shed - so `["PLACE","MILK",18]` followed by `["SELL","MILK",18]` in one turn is
fully backed. The pre-turn shed is not what backs a sell, so a "drop the
unbacked SELLs" filter would cancel real sales.

This is the same trap as `c0a69cc` ("count landed trades, not market orders"),
hit from a new direction. **Before filtering any order against inventory, check
which side of `_process_market` that inventory is written on.** The rim's use of
the pre-turn shed is safe only because it is conservative in the other
direction - it only *adds* a sell when stock is already held.

## Lever 2: sell at a lower order index

`_process_market` walks both players' order lists **by index in lockstep**: at
index `i` it parses each player's `i`-th order, quotes them against the
*current* book, and commits both. So a SELL at index 0 prices into a
less-depleted market than the opponent's same-product SELL at index 4.
**Order position is price.**

The tape already puts its own SELLs first at 97% of the steps that have one
(index histogram over the `open` tape: 258 SELLs at index 0, 58 at index 1,
28 beyond). But `_advance_sells` **appends** the sells it pulls forward to the
end of the list - the worst possible index for exactly the orders the rim
exists to get in early.

`_sells_first` moves every SELL to the front, preserving relative order inside
both groups, and **never moves a SELL ahead of a `BUY_PRODUCT` of the same item
in the same turn** - the tape runs FERTILIZER buy/sell round trips inside one
step (step 266) and reordering those would sell stock not yet bought. Quantities
and membership are untouched, so this changes only *when* our orders price,
never what we sell.

| test (seeds 200-231, both seats) | result |
|---|---|
| lever 2 alone, vs the lever-1 build | **59-5 of 64, mean +321, median +174** |
| **both levers, vs `router_yuan_cov.py` (live)** | **63-1 of 64, mean +773, median +669** |

**The two levers are additive to the dollar** - 452 + 321 = 773 - which is what
two independent leaks should do, and is a check that neither is quietly
cannibalising the other.

Shipped together as `agents/router_yuan_margin.py`, re-measured on the exact
file rather than on the equivalent build the sweep used:

| | |
|---|---|
| vs `router_yuan_cov.py` (live `56019070`), seeds 200-231 | **63-1 of 64, mean +773, median +669, worst -1,590** |
| vs `router_yuan_nf.py` (live `55992408`), **held-out seeds 300-315** | **27-5 of 32, mean +1,813, median +659** |
| top-band panel (lever 1 component) | +547, better on 19/19 |
| pre-submit self-play gate | `['DONE','DONE']` |
| `python -m unittest discover -s tests` | 166 tests, OK |
| per-turn time (720 turns, seed 205) | max **44.8 ms**, p99 1.8 ms, mean 0.24 ms against the 1,000 ms `actTimeout` |

The 44.8 ms is the one-off `_plant_suffix` build on the first `BUY_SEED` step at
or after 144; every other turn is under 2 ms. Module import (the base85+zlib
tape decode) is 1.4s and is **unchanged from the live agent**, which carries the
same blob and has run 304 rated episodes.

The held-out seed set matters: 200-231 is where both levers were found, and
300-315 is a set neither was tuned on.

Note what this lever is *not*. `c0a69cc` closed the selling axis, but what it
closed was **withholding**: per-item price floors (0/16, -409 and -1,554) and
commodity churn blocks (0/16, -165,382). Those change *what and how much* we
sell. This changes neither - only the index the same orders sit at. The closed
result does not cover it, and the engine's lockstep is the mechanism the same
docs already invoke to explain why HIRE-first ordering lost the mirror 4-28.

## Lever 3 that is not a lever: the rim is an arms race, not an edge

`LEAD_K` is recorded in `docs/ROUTE_GENERATIONS.md` at 6, chosen as "the
smallest one that clears the field". The field has advanced its own sells
since, so the obvious question is whether the optimum moved. It did - and
chasing it is a trap worth writing down.

**Mirror**, K variants vs the live `router_yuan_cov` (K=6), seeds 200-231 x 2
seats. Every variant also carries lever 1, so read these against lever 1's own
+452:

| K | 0 | 3 | 6 | **9** | 18 |
|---|---|---|---|---|---|
| record | 5-59 | 4-60 | 39-1 | **63-1** | 20-0 (10 seeds) |
| mean | -1,397 | -1,450 | +452 | **+2,095** | +2,123 (10 seeds) |

K=9 is **+1,643 over the shipped K=6** - bigger than both margin levers
combined, and on the face of it the largest single find of the session.

**It is not a gain. Two independent harnesses say so.**

| harness | K=6 | K=9 |
|---|---|---|
| absolute bank, self-play, 6 seeds | mean **101,003**, floor 59,493 | mean **100,548**, floor 59,427 |
| top-band panel, 4 opponents | 12,251 | 12,033 (**lowest of five K values tried**) |

**K=9 banks no more than K=6 - marginally less.** Its whole mirror win is price
taken *off the opponent*, not revenue added to us. And a longer lead does not
keep paying: on the same seeds K=9 reads +2,854 and K=18 +2,123, so the curve
peaks near 9 and turns over, exactly as the K=12 result in
`ROUTE_GENERATIONS.md` already suggested.

That makes the rim a **front-running arms race with a decaying edge and a small
permanent cost**. The edge exists only against opponents whose sells are still
on the old schedule, and this file's own history records how fast that expires:
the K=6 rim read 93-59 on arrival and **8-30 over its last 30 games** once the
field advanced too. Shipping K=9 hands our copies K=9 within a day, returning
mirrors to parity while we keep the ~455 absolute cost.

This is the **second-sheep shape** (`+3,623` head to head, `-19,514` against a
built-in) in a milder form: a large win against an opponent that is a copy of
us, with every non-copy harness flat to slightly negative. Milder, because the
non-mirror cost here is ~455 rather than catastrophic - so K=9 is probably
positive expected value *today*, while our own lineage is a large share of
draws. But it is a tactical, expiring weapon, not a structural gain, and it
should not be bundled with changes that are.

**Levers 1 and 2 are the opposite kind of thing.** They add absolute bank that
no opponent can take back, they are not visible in an action histogram, and
they do not decay when the field harvests our replay.

## What this says about the route to #1

The three-week pattern - clone the tier above, get copied inside a day, hold
station - is a treadmill, and the replay diffs say why: at the top of this ladder
**the plan is commodity and the margin is the product.** The 2,700-2,800 band
runs our hires (273-290 against our 280), our land (2 quadrants), our herd
(13-18 animals), our MELON program - and beats us by 0.3%.

So the ranking lever is a **stack of small universal bank edges**, each of which
survives being copied for as long as it takes the field to find it, and each of
which converts at ~7.6 win-rate points per $1,000.

Two levers found in one session come to **+773 a game, 63-1 of 64** against the
live agent - call it +6 to +7 win-rate points, on the order of +70-110 rating.
**The gap to #1 is 627.** The stack is the right shape and it is nowhere near
long enough on its own; it buys maybe a sixth of the distance. What it does buy
is a class of change that is cheap to find, provable in one afternoon, and does
not evaporate the moment the field harvests our replay - because the field has
to notice it first, and these are invisible in an action histogram.

## The structural finding: our 65 tapes are 11 behaviours

Pairwise agreement across all 65 tapes in `router_yuan_cov.py`:

| segment | mean agreement | pairs identical |
|---|---|---|
| 0-71 | 0.999 | 2,016 / 2,080 |
| **72-143** | **1.000** | **2,080 / 2,080** |
| 144-400 | 0.529 | 356 / 2,080 |
| 400-718 | 0.451 | 345 / 2,080 |

Collapsing tapes that agree >0.999 after step 144: **10 distinct behaviours, and
11 distinct whole-season tapes, out of 65 route keys.** The 72-143 segment - the
"first-shop medoid" branch - is a single byte-identical sequence for every key
in the router. It does nothing.

Two episodes of the *same* submission, for comparison, taken from teams that
were rated 3,100+ when those episodes ran:

| submission | 0-71 | 72-143 | 144-400 |
|---|---|---|---|
| `55714246` | 1.00 | 0.72 | **0.02** |
| `55574890` | 1.00 | 0.97 | **0.10** |
| `55623460` | 1.00 | 1.00 | **0.05** |
| `55714252` | 0.85 | 0.82 | **0.29** |
| ours (two different keys) | ~1.00 | **1.00** | **0.53** |

Everyone has a fixed opening. **They diverge far harder than we do after the
opening, and they start diverging earlier.**

State it as a **variety** gap, not as proven reactivity: a router with many more
branches and a genuinely reactive policy are indistinguishable in this test, and
nothing here separates them. And do not over-read it into "route-keying does
nothing" - the 26-key coverage fix measured **38-12 on exactly the seeds where
the fallback applied**, so the 11 groups differ enough to matter. The finding is
that there is **much less branching than the 64-key table implies**, and that the
strongest agents on the ladder have much more.

That is the shape of the remaining gap, and it is a multi-day project rather than
a constant to tune: either many more distinct branches, or a policy that repairs
when the season stops matching the recording. The documented `-124,133`
collapse in `docs/ROUTE_GENERATIONS.md` - a blind tape buying into a market the
opponent had already crashed - is the same hole seen from the other side.

## New tooling: a panel drawn from the actual top of the ladder

Every local opponent this repo has ever used was our own lineage or a built-in.
`experiments/ladder_episodes.fetch_episodes` plus the replay endpoint now gives
better:

- **19 tape opponents**, harvested from the 52 episodes we played against
  opponents rated >2,650 **at the time of the episode**. Replays download in
  ~10s each, not the ~1/min the older notes assume.
- **452 episodes against opponents rated 2,850+ at episode time**, reachable
  transitively by listing the episodes of opponents we have played.

**Read those ratings as historical, not as a current tier.** A rating is the
submission's score at that episode, and the leaderboard shows a team's *current*
submission - the two diverge fast:

| team | rating when we met it | rank today |
|---|---|---|
| `16704466` QQ Farming | 2,802 | **924** (1,873) |
| `16626732` islet | 2,787 | **775** (2,006) |
| `16623716` tetsuya & yuanzhe zhou | **3,155** (weeks-old episodes) | **68** (2,653) |
| `16714457` Crop Dusta | **3,119** (weeks-old episodes) | **139** (2,548) |

So the transitive harvest did **not** find a live tier above #1 - it found old
submissions that were rated highly at the time. Nothing above `keiz`'s current
3,061.2 has been located.

**The panel is a paired control, not a strength test.** Both `router_yuan_cov`
and `router_yuan_seedtrim` beat these tapes 16-0 by ~+12,000, because a
recording replayed on a season it was not recorded for plays badly. The only
readable number is the *difference* between the two arms on the same opponent
and seed.

`ListEpisodes` rejects `teamId`; it takes `submissionId` only, so the transitive
route through opponents we have played is the way in.

### What the panel can and cannot measure

It resolves a **deterministic universal** lever cleanly and a **contested**
one not at all. Same panel, same seeds, both run this session:

| lever | panel reading |
|---|---|
| seed trim | **+547, better on 19/19**, and +566 on 17 of them - unambiguous |
| `LEAD_K` sweep (0/3/6/9/12) | K=0 12,380, K=3 12,477, K=6 12,251, K=9 12,033, K=12 12,050 - **all five 54-10**, spread 444 |

The rim reading is worthless, and predictably so: we beat an off-seed tape by
~12,000, so a lever worth a few hundred in a contested near-tie has nothing to
bite on. Note this includes `LEAD_K = 0` - **turning the rim off entirely does
not register on this panel**, while `docs/ROUTE_GENERATIONS.md` measured it at
-1,946 a game in a mirror.

So: **a tape replayed on a season it was not recorded for is a weak opponent, and
a weak opponent cannot price a margin lever.** Use the panel for anything whose
size does not depend on the opponent playing well (dead spend, wasted turns,
arithmetic errors), and a mirror against the live agent for anything that is a
contest over the same order book.
