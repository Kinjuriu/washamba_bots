# Why we cannot run more than four animals

Extracted from ladder replay `94063004` (2026-08-18 dump, both teams rated
~2,900-3,200) with `experiments/animal_timeline.py`, against our own agent on
seed 0. This answers a question three previous attempts got wrong by reasoning
about cash instead of looking.

## The two openings, side by side

| | top-ladder agent | ours |
|---|---|---|
| day 0 | **4 pens, 4 animals**, cash to $22 | 3 pens, 3 animals, cash to $484 |
| day 7 | 10 pens, 9 animals | 4 pens, 3 animals |
| day 11 | **14 animals**, held all season | **4 animals**, capped |
| wheat held | 5 -> 29 -> 86 | **2, every single day** |
| `FEED` | 321 | 111 |
| `COLLECT_FERTILIZER` | 306 | 0 |
| `BUY_PRODUCT:FERTILIZER` | 0 | **187** |
| `HARVEST` / `PLANT` | 399 / 184 | 189 / 133 |
| cash, days 1-10 | **$9-$375** | $17-$1,500 |

Both teams in that episode play the same opening, which matches the four-team
convergence already recorded in `REPLAY_ANALYSIS.md`.

## Four differences, and none of them is the cash trough

1. **They front-load the herd.** The entire animal investment happens on day 0
   out of the starting $3,000, and they then run at near-zero cash for ten days.
   We spread purchases out to protect a reserve. **Being broke on day 3 is their
   plan, not their failure mode.**

2. **The feed buffer is per-animal for them and per-farm for us.**
   `MIN_WHEAT_RESERVE_FOR_FEEDING = 2` is a flat floor, so we hold exactly two
   wheat whether we run one animal or four. They carry 20-90. Four animals
   eating daily against a two-unit buffer is already marginal; a fifth misses
   meals between shed trips and the herd starves.

   Note the asymmetry this creates in our own code: the *sell* exemption is
   `filled_animals * MIN_WHEAT_RESERVE_FOR_FEEDING`, which scales, while the
   *buy* trigger does not.

3. **Pen construction is serialised.** `choose_animal_to_build` refuses to start
   a pen while any stands unfilled, so the herd grows at the speed of one
   build -> pickup -> place round trip. We bought four animals on day 0 and had
   **one pen on day 7**. They had four pens on day 0.

4. **They produce the fertilizer we buy.** 306 `COLLECT_FERTILIZER` against our
   187 `BUY_PRODUCT:FERTILIZER`. The herd is not only a revenue stream, it is
   the input supply for the crops - and we are paying cash for it.

## Why every single-knob fix fails

Four attempts, all collapsing to a bank of $200-$2,000 against a healthy 60-70k:

| change | result |
|---|---|
| herd-scaled cash floor (#30) | 0/3 on all 8 variants, one seed ends at $443 |
| per-animal wheat buffer alone | bank 10 - buy and sell sides fight over the same wheat |
| ...plus a feed cash floor at 200 | bank 208 - undercuts `MIN_CASH_RESERVE_FOR_SEED_BUYING`, `PLANT` falls to **19** for the season |
| ...plus parallel pens and `MAX_ANIMALS = 8` | bank 331 - cash-dead by day 3 |

The pattern is the same every time, and it is the same one this repo has now
hit three times: **one variable moved while the variable it depends on stays
pinned.**

The deeper reason is structural. **Their economy is animal-first; ours is
crop-first.** Our crops fund the animals, so any change that spends crop money
on the herd starves the thing paying for it - while their herd funds the crops,
so being broke on day 3 costs them nothing. There is no ordering of single
constant changes that walks from one equilibrium to the other; every
intermediate state is worse than both ends.

## The opening book was tried. It fails, and here is exactly where.

Transcribed verbatim from the replay (`experiments/opening_trace.py`, episode
94063004, hour 0) - ten orders, the per-turn cap, taking the bank from $3,000
to $22:

    BUY_PRODUCT WHEAT 6 | BUY_ANIMAL COW 2 | BUY_ANIMAL SHEEP 2
    HIRE x5 | BUY_SEED WHEAT 7 | BUY_SEED MELON 12

Implemented with the three prerequisites above. Bank across the attempts:

| state | seed 0 bank |
|---|---|
| shipped `main` | **77,577** |
| book, feed gated behind the seed reserve | 6,409 |
| book firing at hour 0, feed ordered first | 293 |
| wheat reserved against animals *owned* rather than placed | **24** |

**It got worse with each correct fix.** Every one exposed another downstream
rule tuned for a crop-first economy:

1. **The book fired an hour late.** A replay row shows the observation *after*
   the action, so the orders visible in the hour-1 row were issued at hour 0.
   Firing at hour 1 let the normal ladder spend first.
2. **Order within the turn is load-bearing.** Orders execute in sequence against
   one bank and whatever is last is dropped silently
   (`kaggriculture.py:663`). With feed wheat last it was rejected every time and
   `FEED` fired **zero times in a whole season**.
3. **Feed was gated behind `MIN_CASH_RESERVE_FOR_SEED_BUYING`.** At the $5-50
   the book leaves, nothing could be bought at all. Feed has to outrank seed - a
   missed meal loses the animal permanently, a missed seed loses one planting.
4. **The sell reserve counts *placed* animals.** Placement lags purchase by a
   build/pickup/place round trip, so we bought six wheat at hour 1 and **sold
   all six at hour 2** while four animals waited in inventory. *(This defect is
   in shipped `main` too, though at `MAX_ANIMALS = 4` it is nearly invisible.)*
5. **Pens serialise.** `choose_animal_to_build` refuses to start one while
   another stands empty; without `pending_builds` in the new guard, every unit
   sees the same board and they all build - eight pens for three animals.

After all five, the agent still ends at **$14-24 with no crew, no seed and no
income**: below `MIN_MONEY_TO_HIRE`, below the wheat price, below the seed
reserve. Every threshold in the agent is set for a farm that keeps a cash
buffer, and the book's whole point is not keeping one.

**This is the prediction in the section above, confirmed rather than refuted.**
There is no walk between the two equilibria - not by constants, and not by
transplanting the opening either, because the opening only works if everything
downstream already assumes it.

## What to try instead


Not another constant. The change that could work is an explicit **opening
book**: a scripted first two or three days that buys the pens and animals out
of the starting stake before the normal ladder takes over, with the crop economy
allowed to start poor. That is a different shape of change from anything tried
so far, and it is the only one consistent with the replay.

Prerequisites, all measurable before touching strategy:

- pens buildable in parallel (`choose_animal_to_build`'s unfilled guard)
- feed buffer per-animal on **both** the buy and sell sides
- fertilizer sourced from the herd before the market

Test it against `experiments/bigfarm_opponent.py` and the ladder, not against
`starter` - the built-ins never sell and cannot price an animal economy.
