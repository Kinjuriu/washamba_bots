# Splice controller log (Builder B)

Working notes for `experiments/splice/controller.py` (`WB_Controller`). Newest first. The
lead can pick up state from here.

Harness: `experiments/splice/_dev_b.py` (private). `diag A B --seeds N --verbose` prints
per-product revenue, spend, herd/plants by day, envelope and the controller's own day log;
`gate A B --seeds 0-2 --workers 3` plays both seats. `dev` = W3 through step 191 then the
controller; `shadow` = the controller with a fixed W3-like plan; `dev@336` = handover at a
later step; `dev:<module>` = an older controller snapshot (`_dev_b_ctrl_*.py`). Builder A's
modules are frozen in `experiments/splice/_dev_b_frozen/` for stable A/B comparisons (set
`WB_LIVE_A=1` to use the live ones).

## 2026-09-25 05:15 UTC: -8.4k mean vs W3 on seeds 0-2, 2 of 6 won

| build | vs W3 (seeds 0-2, both seats) | mean | note |
|---|---|---|---|
| first full episode | 0-1 | -45k | value-weighted routing, 68% of unit-turns were moves |
| tier weights + zones | 0-1 | -39k | nearest-first inside a must-do tier |
| wedge zones (polar sweep) | 0-6 | -33k | one zone per unit, animals included; waters 52/day |
| shop/opponent crop targets, herd mirror | 0-6 | -36k | |
| economic feeding, late tomato, harvest ongoing at 2+ | 2-6 | -16k | seed 1 (4x PIZZA) turns positive |
| wheat pickup capped at 8 | 2-6 | -18k | removes day-20+ escapes (farmer took all shed wheat at h0) |
| same-day DROP of premium goods | **2-4** | **-8.4k** | day-8 milk/fert sold same day like W3 |

Per game (seeds 0-2): seed 0 -14k/-7k, seed 1 +11.7k/+11.7k, seed 2 (2x YARN) -26k/-26k.

Envelope (candidate, 6 games): idle 2.0%, waters 36.8/day, care 0.80 per animal-day (care is
skipped on purpose when the product is worth less than the wheat), 0 duplicate CARE, 0 escapes,
max turn 71 ms (4 ms mean).

### What moved the number (measured)

- **Routing, not values, was the first leak.** Value-weighted rates sent units across the farm;
  must-do tasks have no order value within a day. Tiered weights made the matching nearest-first.
  Then a polar sweep around the shed (one wedge per unit, equal expected work, animals included,
  each unit takes its wedge's feed wheat and fertilizer on the way out) cut moves per tile visit
  from 1.85 to W3's range and lifted waters from ~33 to ~52/day.
- **The opponent's premium markets are the margin.** W3 banks 94-121k against us versus 72k in
  self-play: uncontested, its strawberry takes 44-48k (21k in self-play). Every premium unit we
  do not sell is W3's.
- **Tomato is the reactive edge.** With FARMERS_MARKET/PIZZA unlocked nobody supplies tomato until
  W3's late planting; the hinge curve spikes (seed 1: 611). Planting days 13-18 so production lands
  in the spike: tomato revenue 21.7k vs W3's 10.3k per game.
- **Feeding is an investment, not a duty.** CARE banks only on fed days; feeding pays only its
  care-bank unit and tonight's payout. When wool/milk crash below a wheat's worth we feed only to stop
  an escape (W3 feeds ~0.7 per animal-day too).
- **Same-day selling.** Carrying goods to the midnight auto-drop means selling the next morning,
  after the opponent. A value-based DROP (premium goods worth >= 250) recovered ~10k per game.

### Handover step (measured, not changed)

From an identical board, the controller loses to W3's own tape by ~47k over days 14-29 (handover at
step 336) and ~51k at step 288, versus -36k at 192 with the same build. Later handover is worse,
so the build keeps 192.

### Open problems (largest first)

1. Wheat: 205 vs 341 units sold per game, and we buy feed. W3 keeps 20-30 wheat tiles.
2. Strawberry: 164 vs 246 units. We cannot reach W3's 33 tiles by day 13 (cash trough days 8-10).
3. Seed 2 (2x YARN_STORE): -26k. W3 runs 17 sheep; the wool market is its.
4. Fertilizer: 219 vs 347 units sold.
5. Melon race: W3 sells first at d10h9; we sell 60 at ~210 vs its 72 at ~205.
