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
