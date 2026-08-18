# Fix B Evaluation: Fertilizer-Aware TOMATO Yield Bonus

*Session: 2026-08-17. Branch: `fix/tomato-fertilizer-yield-bonus` (pushed to
origin, net diff vs `main` is `CLAUDE.md`-only — see below). Result:
**measured negative, not shipped.***

## Intent

`choose_crop` picks which crop to plant next using
`score = future_price * expected_yield / growth_days`. TOMATO was
structurally disadvantaged in that formula (low base price, long growth
window) and rarely won selection — matching the repo's historical
observation that TOMATO sells 0 units most seasons. The fertilizer
machinery (`FERTILIZE`, `wants_fertilizer`, `find_fertilizer_target`) was
already fully built and already targets TOMATO/STRAWBERRY tiles once
planted — but the *planting decision itself* had no awareness that
fertilizer access existed.

Hypothesis: give TOMATO's `expected_yield` a small boost when a reliable
fertilizer source (a placed, filled sheep) is present, so it occasionally
wins the crop-selection tie-break, and see if that converts into more
TOMATO revenue without hurting anything else.

## Implementation

- `FERTILIZER_YIELD_BONUS = {"TOMATO": 1.0}` — a flat additive bump to
  `expected_yield`, deliberately conservative (not the naive "+3 covered
  ticks" ceiling — checked the engine's `_daily_refresh_plants` first and
  confirmed fertilizer mostly buys *earlier* arrival at the same yield
  cap, not literally more units).
- `has_active_fertilizer_source(farm)` — gates the bonus on a **placed
  and filled** sheep structure, not on currently-held FERTILIZER stock.
  Reasoning at the time: held stock is a shared balance already
  reactively claimed by existing tiles, so crediting a new planting
  decision with it would double-count — the same shape of mistake that
  caused Fix A's seed-repurchase spiral.
- Inserted into `choose_crop`'s scoring loop right before the score line;
  no signature changes.
- 5 new unit tests, values found empirically against the real pricing
  simulator rather than guessed (a WHEAT-vs-TOMATO near-tie constructed
  by giving WHEAT a small, empirically-measured glut).
- All local checks passed cleanly: 123/123 unit tests, `['DONE','DONE']`
  validation gate, sheep survival intact.

## Observations — what actually happened

The measurement is where it fell apart, and it's informative *why*:

- **`paired_compare.py` vs `starter`, 12 seeds: 2/12 wins, mean -101.**
  Vs `pass`, 12 seeds: 2/12 wins, mean +63. Both are minority
  win-counts — by the repo's own rule ("read wins before t-value"),
  these are losses/washes, not the "small but consistent gain" the plan
  called for.
- **`head_to_head.py` vs baseline, 24 matches: 11/24 wins, mean +386.**
  The positive mean is misleading on its own — under half the matches
  actually won, meaning the mean is carried by a small number of large
  swings in one direction while more matches lean the other way. The
  self-vs-self control came back at exactly 0 mean, confirming the
  harness itself was behaving correctly.
- **Root-cause diagnosis, not just a number.** Pulled per-seed action
  histograms (PLANT/SELL counts by crop) comparing candidate vs baseline
  on the seeds with the biggest deltas. On `seed=2` vs `starter`
  (delta -655), the candidate planted 7 TOMATO / 24 WHEAT where the
  baseline planted 0 TOMATO / 45 WHEAT. Total units sold dropped from 35
  (all WHEAT) to 18 (15 WHEAT + 3 TOMATO). So the bonus wasn't competing
  with MELON at all — the thing three earlier "diversify away from
  melon" attempts in this repo's history all died to — it was
  cannibalizing **WHEAT and CARROT**, the cheap, fast-turnover crops.
  TOMATO costs 5x WHEAT's seed price and occupies a tile for 8 days
  versus WHEAT's 4; a fast crop replanted repeatedly can out-earn one
  slower, pricier planting, because total throughput per tile-day is
  what actually gets paid for.
- **The general lesson.** The score formula's `/ growth_days` denominator
  already prices in how long a crop ties up a tile. A flat additive bump
  to the numerator (`expected_yield += 1.0`) doesn't carry that same
  accounting — it ignores what a faster crop would have cycled through in
  that same tile-time instead. That's a formula-shape problem, not a
  magnitude problem, which is why it wasn't retried at 1.5/2.0 — the
  diagnostic showed displacement of the wrong crop, and more bonus would
  only displace more of it.

## Outcome

Clean implementation, honest measurement, a real (if disappointing)
finding written up in `CLAUDE.md`'s "Measured dead ends" section as a new
entry. Branch history: implementation commit (`4bd053c`) → docs commit
(`b1e943b`) → `git revert` of the implementation (`404e94b`), so the
branch's net diff against `main` is `CLAUDE.md`-only. Pushed to origin; no
PR opened, since there's no functional change to merge.

## If picking this up again

Don't just retune the constant — the diagnostic says the gate/formula
shape is the problem, not the magnitude. `mydocs/FIX.md`'s original
framing ("tomato becomes competitive when melon/strawberry are already
gutted") gestured at something like this: a bonus that only fires when
the *displaced* crop (WHEAT/CARROT) is also saturated might avoid the
tile-time trade shown here. Untested.
