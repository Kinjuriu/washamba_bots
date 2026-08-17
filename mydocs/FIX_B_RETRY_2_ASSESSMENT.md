# Assessment: `FIX_B_RETRY_2_PROPOSAL.md` — plus a deeper diagnostic

*Review of the retry-#2 proposal (relative-gate fertilizer bonus for
TOMATO), followed by a deeper diagnostic requested after the review.
No code changes were made anywhere in the repo during this session —
this is a research/assessment pass only.*

**Headline, up front:** after digging further (Fix-A-style — instrument,
don't guess), something surfaced that changes the whole direction:
`choose_crop`'s `growth_days` denominator for TOMATO/STRAWBERRY
("ongoing" crops) structurally **understates** their real
tile-occupancy time, because these crops don't clear the tile on harvest
the way WHEAT/CARROT/MELON do — they decay into a `WEED` some time
*after* their last production tick, and only then can be dug and
replanted. Measured directly against the installed engine (not
guessed): TOMATO's real cycle is **~12 days**, not the `8` the score
formula assumes; STRAWBERRY's is **~17 days**, not `10`. That means the
*current* formula is already more generous to TOMATO than its real
economics justify — every attempt to boost TOMATO further (retry #1,
#2a, the proposed #2) has been pushing an already over-valued crop even
higher, which is a coherent explanation for why each one measured
flat-to-negative. See "Deeper diagnostic" below for the full derivation
and the recommendation.

## Context

`FIX_B_RETRY_2_PROPOSAL.md` proposed retrying the tomato-fertilizer-bonus
idea (previously measured negative — see
`FIX_B_FERTILIZER_YIELD_BONUS_EVALUATION.md` and `CLAUDE.md`'s "Measured
dead ends"). The proposal claims an intermediate attempt ("retry #2a,"
gate on `SELL_PRICE_THRESHOLDS`) was inert (0/12 seeds, +0 delta — never
fired), diagnoses why, and proposes a replacement: gate the TOMATO yield
bonus on a **direct relative comparison** against WHEAT/CARROT's own
score that turn, rather than an absolute threshold, with the bonus
raised from `1.0` to `1.5`.

The proposal's numbers were not taken on faith — its core claims were
independently reproduced by reimplementing `choose_crop`'s real score
formula (using `main.py`'s actual exported functions: `CROPS`,
`estimate_future_price`, `count_pipeline_supply`, `count_opponent_pipeline`,
`scan_animal_structures`) and replaying real episodes (seeds 0-3 vs
`starter`), the same "instrument, don't guess" discipline this repo has
used throughout Fix A and Fix B retry #1.

Note: no trace of the described "retry #2a" implementation exists in this
repo's git history (checked all local/remote branches and the stash list)
— it exists only as a narrative in the proposal doc. That doesn't make it
false, but it means the numbers had to be independently re-derived rather
than traced to a commit.

## What checks out

- **The retry-2a diagnosis is architecturally sound.** `SELL_PRICE_THRESHOLDS`
  is calibrated for "is this crop worth selling at all" (a low floor), not
  "does fertilized TOMATO beat a specific rival crop this turn" (a much
  higher, situational bar). Reusing it for the latter question would
  plausibly never fire, matching the claimed 0/12-seed inert result.
- **The core margin number is corroborated almost exactly.** Reimplementing
  the score formula from scratch and replaying seed 0 vs `starter`
  independently, the closest-miss margin came out to **11.50** — matching
  the proposal's claimed `-11.5` to two decimal places. Strong evidence the
  underlying trace is real and the score arithmetic is right.
- **The relative-gate *construction* is a genuine improvement in shape**
  over retry #1's unconditional bonus and 2a's absolute-threshold gate. By
  construction it cannot take a plant away from a WHEAT/CARROT that's
  winning by a wide margin — verified logically: the final crop pick still
  runs through the existing max-over-all-crops comparison in
  `choose_crop`'s loop, so a bonused TOMATO score still has to beat
  MELON/STRAWBERRY too. The WHEAT/CARROT-specific gate only ever changes
  whether TOMATO is *allowed to compete* at all, not the final decision.

## What's wrong

1. **The "$60 cap" claim is false, and the whole `bonus=1.5` calibration
   rests on it.** The proposal argues TOMATO's forecast price "caps at
   $60" (its base price), so a 1.0 bonus contributes at most `60/8=7.5`
   points and 1.5 contributes at most `11.25`. But the engine's
   `market_price()` (`kaggriculture.py:192-206`) explicitly prices
   *above* base when inventory sits below `I0` (the `below_func` branch),
   and empirically — replaying all 4 seeds — TOMATO's forecast
   `future_price` at the moment the gate was checked ranged up to
   **$144-$286**, nowhere near capped at $60. TOMATO's own market
   inventory sits persistently just below `I0` (9553-9700 across seeds)
   even though our agent barely plants it, and `estimate_future_price`'s
   forward simulation amplifies that into a much higher forecast at the
   8-day horizon TOMATO's `first_yield_day` requires.

2. **Consequence: "fires rarely, as a tie-break" does not hold empirically.**
   The actual bonus needed to flip every real losing turn in each replayed
   seed, using the *real* `future_price` at that turn (not a constant $60):

   | seed | losing turns | flip rate @ bonus=1.5 | flip rate @ bonus=1.0 |
   |---|---|---|---|
   | 0 | 289 | **67%** | 0% |
   | 1 | 457 | 5% | 5% |
   | 2 | 454 | 26% | 17% |
   | 3 | 318 | 35% | 9% |

   On 3 of 4 seeds, `bonus=1.5` flips a quarter to two-thirds of *all*
   checked losing turns — not "the closest miss only." That's a
   wholesale redirection of crop policy on those seeds: the exact failure
   mode retry #1 was rejected for (displacing WHEAT/CARROT en masse),
   arrived at again via a different mechanism.

3. **The flip rate is highly seed-dependent (5% to 67%), and the proposal
   only traced seed 0** — which happens to be the worst case in this
   4-seed check. A design that behaves like a rare tie-break on one seed
   and a wholesale policy rewrite on another is not "structurally safe by
   construction" in the sense claimed. The *non-overshoot* guarantee
   (point 3 above, "what checks out") is real and by construction; the
   *rarity* framing is not — it's an empirical property that swings
   widely game-to-game and wasn't checked across seeds before being
   asserted as calibrated.

4. **Minor implementation gap, not a blocker.** The code sketch references
   `score_by_crop[c]` for WHEAT/CARROT, implying a dict of every crop's
   score is available when TOMATO is evaluated. The current `choose_crop`
   loop only tracks `best_score`/`best_crop`, not a full dict — building
   one is a small, mechanical change (`PLANTABLE_CROPS` order is `WHEAT,
   CARROT, TOMATO, STRAWBERRY, MELON`, so WHEAT/CARROT are naturally
   computed before TOMATO within a single pass; no restructuring needed,
   just accumulate into a dict as the loop runs).

## Recommendation on the retry-2 proposal specifically

**Don't implement it as specced** (`bonus=1.5`, additive against an
assumed $60 ceiling) — for the reasons above. But read the next section
before deciding whether to fix and retry it at all, because the deeper
diagnostic below suggests the entire "boost TOMATO" premise (retries #1,
#2a, #2) may be aimed at a crop that shouldn't be boosted in the first
place.

## Deeper diagnostic: is `growth_days` even the right number for TOMATO?

The open question was whether the current hypothesis (TOMATO deserves
help; the question is just calibration) still had more to it, to be
checked with a diagnostic rather than a guess — same discipline as Fix
A's instrumented trace. It does have more to it, and it points the
other way.

**The question:** `choose_crop`'s score is
`future_price * expected_yield / growth_days`, where `growth_days =
crop_info["max_yield_day"]` (8 for TOMATO). That denominator is meant to
represent "how many days does this planting tie up the tile" — the thing
that makes a fast crop's repeated turnover competitive with a slow crop's
bigger one-time payout. Is 8 actually how long a TOMATO tile stays
occupied?

**What the engine actually does (`kaggriculture.py`):**

- `TOMATO`/`STRAWBERRY` are `"ongoing": True`. For ongoing crops,
  `HARVEST` does **not** clear the tile (`kaggriculture.py:467-468`:
  `if not crop_data["ongoing"]: farm["tiles"][fy][fx] = None` — the
  `None` assignment is skipped for ongoing crops). The plant just sits
  there with `yield_units` reset to 0.
- The tile only frees up later, via `_decay_plants` (`kaggriculture.py:752-766`),
  which runs every single turn for both farms. Once a plant's final
  production tick fires (`production_count == max_yield`), the engine
  sets `max_lifespan_step` (`kaggriculture.py:801-802`) — a future turn
  after which the tile starts losing `yield_units` every 2 turns until
  it flips to `WEED` and needs a `DIG` to reclaim, same as a
  neglect-killed plant.
- Measured directly and deterministically by driving the installed
  engine's own internal functions (`_new_plant`, `_daily_refresh_plants`,
  `_decay_plants`) with perfect daily watering, no RNG involved:

  | crop | `growth_days` used in scoring | real last production tick | real day tile becomes a WEED |
  |---|---|---|---|
  | TOMATO | 8 | day 11 | **day ~12** |
  | STRAWBERRY | 10 | day 16 | **day ~17** |

  A real episode replay (seed 0, main.py vs starter) corroborates this
  independently: the two TOMATO plantings that completed a full
  plant→weed cycle within the episode averaged **11.6 days**, matching
  the engine-level number closely.
- On top of that ~12-day floor, `main.py` doesn't proactively dig a
  spent-but-still-`PLANT` tile — the only `DIG` call site
  (`main.py:1788-1789`) fires on `kind == "WEED"`, and actively seeking
  one out (`main.py:1841-1849`, step 11 of `choose_unit_action`'s
  ladder) is ranked *below* feeding, harvesting, watering, animal
  placement, planting, and fertilizer logistics. So in real play, the
  tile sits idle even longer than ~12 days before anything gets
  replanted there — the true figure is a floor, not the actual number.

**Why this matters for Fix B:** `growth_days=8` understates TOMATO's
real tile cost by at least 50%. The *current, unmodified* formula is
therefore already more generous to TOMATO than its real economics
justify — it's crediting TOMATO with cycling through a tile every 8 days
when the real figure is ~12+. Re-scoring with the corrected denominator
at baseline price ($60, `expected_yield=4`): `60*4/12 ≈ 20`, versus the
formula's current `60*4/8 = 30`. TOMATO looks *worse*, not better, once
the tile-time is counted honestly.

This reframes all three retries. Retry #1's flat bonus and the proposed
retry #2's relative-gated bonus were both trying to make an
*already-overvalued* crop win more often. That's a coherent explanation
for why both measured flat-to-negative once they actually fired: the
crops they displaced (WHEAT/CARROT) may genuinely be the better tile-time
investment even before accounting for this bug, and any nudge toward
TOMATO just makes that trade worse.

One puzzle this doesn't fully resolve: STRAWBERRY has the *same* bug
(understated by an even larger margin, 10 vs ~17) yet sells fine in
practice (75-92/game in the traces pulled this session), while TOMATO
sells ~0-15/game. STRAWBERRY's higher base price ($120 vs $60) and yield
apparently clear the bar even with the current generous accounting;
TOMATO's don't. That's consistent with — not contradicting — the
conclusion that TOMATO specifically is a marginal/bad tile investment,
not merely an undervalued one.

## Recommendation (revised, given the diagnostic)

**Stop trying to boost TOMATO's crop-selection score.** The repeated
"TOMATO sells 0 most seasons" observation that motivated Fix A/B's
original framing may not be a bug — it may be the correct economic
outcome given real tile-occupancy costs, and three separate attempts
(flat bonus, absolute gate, relative gate) have now all measured
flat-to-negative when they actually changed behavior. That's a strong
empirical signal in the same direction as this diagnostic's mechanism,
not just one data point.

If acting on this session's finding, the legitimate next step is a
**different, smaller, and more defensible fix**: correct `growth_days`
for ongoing crops in `choose_crop` to reflect real tile-occupancy
(`last_tick_age + decay-to-weed delay`, roughly `first_yield_day - 1 +
interval*(max_yield-1) + ~1-2` days) instead of the current
`max_yield_day`. This is a general accuracy fix, not a TOMATO-specific
nudge — it would very likely make TOMATO get chosen *less*, and could
also reduce STRAWBERRY's frequency somewhat, so it needs its own honest
paired/head-to-head measurement rather than being assumed to help. This
has **not** been implemented or measured — it's flagged as the most
probable *legitimate* lever, not a verified win.

Given three consecutive TOMATO-boosting attempts have now failed for
compounding reasons (aggressive displacement, wrong-question gating, and
now a formula that was already too generous), treat "make TOMATO sell
more" as a closed question for this repo unless new evidence appears,
and, if pursued at all, spend effort on the `growth_days` accuracy fix
instead — which is justified on its own terms (correctness) regardless
of what it does to TOMATO specifically.

## Verification performed

- Reproduced the proposal's closest-miss margin (11.50) independently via
  a from-scratch reimplementation of `choose_crop`'s real score formula,
  driven by real episode replays — not by trusting the proposal's
  numbers or its undiscoverable "retry 2a" instrumentation.
- Confirmed via the engine source (`kaggriculture.py:192-206`,
  `market_price()`) that price can exceed base when inventory is below
  `I0` — this is what falsifies the "$60 cap" claim.
- Extended the single-seed check to seeds 0-3 (matching this repo's
  established practice of not trusting one seed) and found the
  "fires rarely" claim doesn't generalize.
- No functional code was changed anywhere in the repo during this
  review — all verification ran from standalone scripts in a scratch
  tmp directory, reusing `main.py`'s real functions read-only.
- For the deeper diagnostic: drove the installed engine's own internal
  functions (`_new_plant`, `_daily_refresh_plants`, `_decay_plants`)
  directly in an isolated, RNG-free harness (no episode noise) to get an
  exact plant→weed cycle length per crop, then cross-checked it against
  real episode replays (seed 0-2 vs `starter`) tracking each tile's
  `PLANT`→`WEED` state transitions. Both methods agree on TOMATO's real
  cycle (~11.6-12.25 days vs the assumed 8).
- Confirmed `main.py` has no code path that proactively `DIG`s a
  still-`PLANT`-kind tile (only `WEED`-kind), and that its one
  weed-seeking routing step (`main.py:1841-1849`) is low priority in
  `choose_unit_action`'s ladder — so the ~12-day figure is a floor on
  real tile-occupancy, not the actual average.
