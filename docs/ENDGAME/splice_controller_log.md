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

## Files

- `experiments/splice/controller.py`: `WB_Controller` (current build: wedge zones, zone-local feeding
  with a day-15 rescue, economic feeding, same-day premium DROP, shop/opponent crop targets with
  top-six floors, herd mirror, melon race). Plan switches are module constants (`WB_*`), with the
  measured verdict beside the switches that were tried and turned off.
- `tests/test_splice_controller.py`: 19 unittest cases (planner targets, no duplicate CARE, PLANT
  never exceeds seeds and is watered next turn, structure/animal matching, the 10-order cap with
  sells first, never the fourth quadrant, exception fallback, day-28/29 feeding, final-day DROP).
- `experiments/splice/_dev_b.py`: private harness (see top). Snapshots `_dev_b_ctrl_*.py` and
  single-change variants `_dev_b_var_*.py` are the builds measured in the tables below.

## 2026-09-25 09:00 UTC: stop signal reached (day-14 gap stays near -16k to -18k, bar was -8k)

**Official gate, current controller** (build of 08:00, with the dump predictor wired by build.py,
16 dev seeds x both seats):

| opponent | result | mean margin |
|---|---|---|
| W3 | **0-32** | -19,803 |
| W1 | 0-32 | -19,992 |
| W0 | 0-32 | -19,789 |
| reactive v7 | 0-32 | -16,879 |
| 2945 Farm | 0-32 | -20,416 |
| self-play mean | 100,214 | vs W3 self-play 104,348 |

Envelope: idle 1.9%, waters 36.8/day (FAIL), care 0.81, 0 duplicate CARE.

**Stop test (agreed with the coordinator): move the day-14 identical-board gap from about -15k to
about -8k.** Handover at step 336, 16 dev seeds, one seat each, one change at a time against the
current-build baseline of -18.1k:

| change | mean | median |
|---|---|---|
| baseline (current build) | -18.1k | -17.6k |
| late carrots: every freed tile from day 23 | -16.6k | -15.7k |
| sell fertilizer unless a premium crop is producing | -18.0k | -16.4k |
| mirror the opponent's crops and herd | **-15.8k** | -14.6k |
| batch all tasks on a tile before leaving | -18.7k | -18.1k |
| rotation: harvested wheat/carrot tiles keep their crop | -17.5k | -15.3k |
| animals harvested at 2+ units | -17.8k | -16.6k |
| no extra geese, no tomato | -19.6k | -15.0k |
| tile-bundle matching (at step 192, vs -21.9k there) | -28.0k | -28.9k |

None reaches -8k. On seed 900 the tape's second half is a steady machine the controller does not
reproduce: W3 plants 6-11 wheat **every day** from day 14 to 24 (a ~28-tile rotation), converts
expiring strawberry land to wheat and then to 4-14 carrots a day from day 22, sells fertilizer early
and buys it cheap late to apply. Our plantings come in lumps (0 on day 14, 1 a day on days 18-20),
so harvests do too.

**Timing (single-threaded, nothing else running):** controller turn mean 1.5-1.9 ms, p99 4.3 ms,
dawn turns at most 3.7 ms. One 138 ms outlier in 1,054 turns (non-dawn, GC or OS). Under the 300 ms
rule with a wide margin. The 330-810 ms reads came from 4-worker contention and W3's own first call.

**Which build is "the controller".** `controller.py` today is the 08:00 build: -19.8k on the
official gate with Builder A's live, cadence-gated sell engine and the dump predictor. The 05:20
snapshot (`_dev_b_ctrl_1045_drop.py`) read -17.4k on A's earlier every-turn engine. Both are 0-32;
the difference is confounded by A's default change, not a controller regression.

**Per-product revenue vs W3, same games** (current build, 16 dev seeds, one seat each, exact from
the engine's commit log; gate.py's opponent-side columns are broken and not used here): strawberry
25.1k vs 33.5k, wheat 8.9k vs 15.6k, wool 16.3k vs 20.7k, fertilizer 12.4k vs 15.8k, carrot 2.3k vs
6.8k, melon 13.6k vs 14.9k, milk 27.4k vs 26.7k; we lead on egg (+3.3k) and tomato (+1.2k).

**Recommendation for the lead.** The splice controller, as built, should not ship. Against W3 the
natural baseline for any W3-based agent is a tie (same tape, same state), so an agent that keeps W3's
tape for every unit action and changes market orders only (the W2 overlay, FABLE section 4) would
pass the W3 gate with any consistent positive edge. Be clear about its size: Builder A's own overlay
diagnostic found the paced sell engine neutral on a glutted W3 board (wool +0.6, milk -4.0,
strawberry -0.7 per unit), so the case rests on the dump predictor's measured +683 to +978 a game
against tapes. That is a +$800 agent, not a prize-line one. Wheat and fertilizer must stay the
tape's (it feeds from the shed). The lead decides.

## 2026-09-25 07:20 UTC: official gate 0-32 vs W3 (-17.4k); dev-seed reads all ~-20k

**Official gate** (`gate.py`, 16 dev seeds x both seats, build of 05:20 = "drop" build):

| opponent | result | mean margin |
|---|---|---|
| W3 | **0-32** | -17,356 |
| W1 | 0-32 | -17,115 |
| W0 | 0-32 | -17,144 |
| reactive v7 | 2-30 | -14,601 |
| 2945 Farm | 0-32 | -16,151 |
| self-play mean | 99,942 | vs W3 self-play 104,348 |

Envelope: idle 1.8% (pass), waters 37.7/day (FAIL, need 40), care 0.81 (pass), 0 duplicate CARE,
7 escapes (all on day 28 by design, since fixed), max turn 347 ms in the build check.
Seeds 0-2 flattered us (-8.4k): tomato-rich seed 1 was +11.7k.

**Everything since, on the 16 dev seeds, one seat per seed (seat = seed parity), vs W3:**

| variant | mean | note |
|---|---|---|
| drop build (baseline) | -20.4k | |
| + top-six schedule floors | -21.0k | noise |
| + strawberry floor 33 from day 10 | -21.9k | +2k strawberry, lost carrot/tomato |
| mirror opponent's crops and herd | -23.6k | |
| tomato cap 6, carrots from day 23 | -23.4k | |
| zone-local feeding (late rescue) | **-21.9k** (median -19.3k) | adopted: waters 38.1, 0 escapes |
| handover step 72 (day 3), schedule plan | -28.7k | earlier handover is worse |
| handover step 144 (day 6) | -25.3k | |
| handover step 336 (day 14) | -15.0k | identical boards at day 14, still lose |

**The day-14 handover isolates execution + late plan: from an identical board we lose 15k in
days 14-29.** Seed 900 detail:
- wheat: W3 harvests 428 after day 14 and sells 271 (keeps 24-38 wheat tiles, then carrots from
  day 26); we harvest 343 and sell 195 (tomato and extra geese take wheat land).
- fertilizer: W3 sells 218 and buys 73 cheap late units to apply; we apply 149 and sell 96.
- strawberry: identical plants, we produce 235 vs 247 (fertilizer timing on production days).
- carrots: W3 runs 18-31 carrot tiles on days 26-28; we run 9-13.

**Executor vs W3 (seed 900, days 10-27, per day):** we make 83 tile visits with 156 moves and 136
actions; W3 makes 75 visits with 110 moves and 144 actions. W3 does more per visit (1.91 vs 1.64
actions) and walks less between visits (1.46 vs 1.88 moves). Roughly 30 unit-turns a day of
throughput are lost to routing.

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
