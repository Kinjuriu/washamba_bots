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
