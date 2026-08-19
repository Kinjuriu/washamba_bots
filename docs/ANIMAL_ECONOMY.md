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
