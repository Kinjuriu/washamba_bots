# Fix B, retry #2 — fertilizer-aware TOMATO bonus, relative gate

*Not committed. Working notes for this session, following on from
`FIX_B_FERTILIZER_YIELD_BONUS_EVALUATION.md` (retry #1, measured negative)
and this session's own first attempt (retry #2a, measured **inert** — see
"What went wrong with 2a" below before reading the proposal).*

## Recap: why retry #1 lost

A flat `FERTILIZER_YIELD_BONUS = {"TOMATO": 1.0}` applied to `expected_yield`
unconditionally whenever a fertilizer source was active. Measured -101 to
-655/seed: it displaced WHEAT/CARROT, not MELON, because nothing stopped the
bonus from out-competing a WHEAT/CARROT pick that was still the better plant.

## What went wrong with 2a (this session, retry #2a — also not shipped)

The obvious-looking fix: gate the bonus on WHEAT/CARROT's own forecast price
being below `SELL_PRICE_THRESHOLDS` (`$20`/`$25`) first. Implemented, unit
tested (synthetic scenarios confirmed the gate logic itself is correct in
isolation), then run through `paired_compare.py` vs `starter`, 12 seeds:

**+0 delta, 0/12 seeds, sd 0** — byte-identical to baseline on every seed.

That result is too clean to be "no improvement" — it means the code path
never executed differently at all. Traced it properly (not guessed, same
discipline as Fix A's instrumented turn-by-turn trace) by instrumenting
`has_active_fertilizer_source` and the gate check directly in `main.py`,
then running real episodes:

| | seed 0 | seed 1 | seed 2 | seed 3 |
|---|---|---|---|---|
| fertilizer source active (turns) | 861 | 917 | 911 | 873 |
| gate checked (TOMATO scored, fert active) | 574 | 574 | 570 | 566 |
| WHEAT blocked the gate | 574/574 | 574/574 | 570/570 | 566/566 |
| lowest WHEAT forecast price seen | 27 | 27 | 27 | 27 |

The sheep **is** active almost the whole season. The gate **is** being
checked constantly. It never once fires, on any seed, because WHEAT's
forecast price never dropped below 27 in any of these games — comfortably
above its $20 sell threshold, every single turn.

**Root cause: `SELL_PRICE_THRESHOLDS` answers the wrong question.** It's
calibrated for "is it worth selling this crop *at all* right now" — a
floor near the bottom of WHEAT's realistic price range. The question this
gate actually needs answered is "is WHEAT/CARROT a *worse tile-time bet
than a bonused TOMATO right now*" — a completely different, much higher
bar. Reusing `SELL_PRICE_THRESHOLDS` because it was sitting right there,
without checking whether its meaning fit the new question, made the gate
permanently closed in practice.

## What the real score margins look like

Before proposing a replacement, this session pulled the actual numbers
instead of guessing again. Same seed-0 trace, logging the real computed
score gap (`TOMATO's own unbonused score − best of WHEAT/CARROT's own
score`) every time the gate was checked (574 samples, one game):

- **179 / 574 (31%)**: TOMATO's unbonused score *already* wins. No bonus
  needed — these are turns the current, unmodified `main.py` should
  already be capable of choosing TOMATO on the real formula alone.
- **395 / 574 (69%)**: TOMATO loses. Closest miss: **-11.5**. Median miss
  is much larger — the 10th-percentile-from-the-top loss is already -12.5,
  and most losses run -13 to -16.5.
- **A +1.0 bonus can contribute at most `future_price / growth_days` ≈
  `60 / 8` = **7.5** points of score**, since TOMATO's own market base
  price caps at $60. That's smaller than *every single* observed loss
  margin in this trace (closest was -11.5). **A relative gate built
  correctly, with the existing +1.0 bonus value, would also have fired
  zero times** — not because the gate is miscalibrated, but because the
  bonus itself is too small to ever close the gap that actually occurs in
  real play.

This is a different failure mode than 2a's, and worth being explicit about
so the next person doesn't re-run 2a's mistake at a different magnitude:
2a failed because the *gate's threshold* referenced the wrong question.
This is where retry #1's diagnosis was actually consistent: retry #1
found that a flat bonus was too *aggressive* against real WHEAT/CARROT
competition, and this trace shows the flip side — a flat bonus at that
same magnitude is too *weak* to ever help once a proper relative gate is
in place. Both things can be true at once because they're about two
different failure directions on the same knob.

## Proposal

Replace the `SELL_PRICE_THRESHOLDS`-based gate with a **direct relative
comparison against WHEAT/CARROT's own score**, computed the same turn, in
the same units the final decision actually uses — not against an
unrelated absolute constant:

```python
if crop == "TOMATO" and fertilizer_active:
    rival_score = max(
        (score_by_crop[c] for c in ("WHEAT", "CARROT") if c in score_by_crop),
        default=None,
    )
    if rival_score is not None:
        bonused_score = future_price * (expected_yield + FERTILIZER_YIELD_BONUS["TOMATO"]) / growth_days
        if raw_score <= rival_score and bonused_score > rival_score:
            expected_yield += FERTILIZER_YIELD_BONUS["TOMATO"]
```

This is structurally safe against retry #1's failure mode **by
construction**, not by tuning a threshold: it only ever changes the
outcome on a genuine near-miss (TOMATO was about to lose, now it barely
wins) — it can never take a plant away from a WHEAT/CARROT that was
winning by a wide margin, because in that case `bonused_score` still
won't clear `rival_score`. There's no separate "how gutted is WHEAT"
question to calibrate at all.

Given the trace above shows the current `1.0` bonus never closes a real
gap (closest miss -11.5 needs ≈1.53), **raise the bonus to `1.5`** — still
conservative, and informed by the actual observed margin distribution
rather than picked to "try a bigger number." At `1.5`, the bonus
contributes up to `1.5 × 60 / 8` = 11.25 points — enough to flip the
closest observed miss (-11.5) but not the next ones (-12.0 and below),
so this should fire rarely, on the closest calls only. That rarity is the
point: it's a tie-break, not a redirection of the crop-choice policy.

## What to check before trusting this

- Does the relative gate ever actually fire in a real game at
  `BONUS=1.5`, or does the same "checked constantly, never fires"
  pattern recur for a different reason? (Traced below.)
- `paired_compare.py` vs `starter`, 12 seeds — must show a real win
  count, not a flat +0 line again.
- `head_to_head.py` vs baseline — the better proxy for a real ladder
  opponent (contested market, WHEAT actually gets sold by both sides).
- Whatever fires (or doesn't), read the actual per-seed action histogram
  before trusting a mean — same rule that caught retry #1.
