# Predicting and front-running tape dumps (Builder A, 25 Sept)

Scope: `experiments/splice/dump_predictor.py` (`WB_DumpPredictor`) and the optional `predictor` argument of `WB_SellEngine`. The table was measured with `experiments/splice/_probe_dumps.py`.

## Summary

- **Tape dumps are a function of public data, and mostly predictable.** W3, W0 and the 2945 Farm share one route blob and one router (byte-identical in all four agent files). The route is fixed at step 144 by the first two unlocked shops, with a rival-key override at step 2. Measured over 72 games (144 seats), a dump of at least 4 units recurs at the same step. Held-out accuracy (table from seeds 900-915, scored on 916-923) is precision 0.73-0.74 and recall 0.67-0.68 for all three families (0.74-0.75 within ±1 step). By product:

  | product | precision | recall |
  |---|---|---|
  | **melon** | **1.00** | **1.00** |
  | carrot | 0.74 | 0.82 |
  | strawberry | 0.75 | 0.73 |
  | milk | 0.68 | 0.56 |
  | wool | 0.63 | 0.56 |
  | egg | 0.34 | 0.27 (dropped) |
- **Detection is exact at obs step 1.** Given our turn-1 orders (W3's opening), the opponent's money after turn 1 is W3 2,854 / W0 2,850 / 2945 Farm 2,860 / top six 2,460, in both seats. That matches the engine 8 of 8, and step 2 confirms (1,042 / 1,038 / 1,048 / 581). Any other opening means no prediction.
- **Selling ahead is only possible when we hold the goods.** In a seed-900 trace, the controller's melons reach the shed at W3's own dump steps (249-255), because both farms planted them the same tape day. So the engine cannot get ahead of the melon dump: we still get 186/unit against W3's 209. The melon race has to be won by harvesting and dropping melons at day 10 hours 0-8, which is B's harvest planner. I sent B the dump steps.
- **Gate, predictor on vs off** (same controller snapshot, dev seeds, both seats): the margin improves against every tape family, paired on identical games. Win counts do not move: this controller snapshot loses every game to all five opponents by about 21k either way.

  | opponent | margin delta | games better / worse | t |
  |---|---|---|---|
  | W3 | +978 | 28 / 4 | +3.9 |
  | W0 | +762 | 29 / 3 | +3.2 |
  | 2945 Farm | +683 | 28 / 4 | +3.0 |
  | W1 | +788 | 27 / 5 | +3.3 |

  Against reactive v1 and in self-play all 48 games are identical: the audit keeps it silent against non-tapes and mirrors.

## 1. Dump-schedule tables

Probe: each family plays W3, whose opening our splice plays through step 191, on seeds 900-923 with seats alternating by seed parity. Both seats are recorded, so W3 contributes 96 seats and W0 and the 2945 Farm 24 each. Each seat records:
- the route key (first two shops at obs step 144);
- the rival key the router reads at step 2;
- the route the chassis actually used at steps 150 and 650, read from the agent's own state;
- every executed SELL, from an instrumented `_commit_unit`.

All 72 games reached DONE with no errors.

- **Routes.** The 64 shop keys map to 20 routes. Route 105 takes 21 keys and route 9 (YARN_STORE worlds) takes 15. Every game switches to route 2 at step 648. The rival override (route 128) needs our money at step 2 to be 229. Ours is 1,042-1,048, so it never fires against the splice.
- **The table** (`WB_DP_DUMPS`, generated into `dump_predictor.py` by `_probe_dumps.py --table 4`) has 1,882 rows in 23 (family, route) cells, plus a pooled "any" cell per family used when a route has fewer than 2 recorded seats. It covers steps 180 onward (the controller acts from 192) for MELON, STRAWBERRY, MILK, WOOL, TOMATO and CARROT; EGG was measured as unpredictable. A row is a step where the family dumps at least 4 units in at least half of that route's games, with the median quantity. The tape's own order quantities are placeholders (`SELL MELON 1000` = everything in the shed), so quantities are measured, not read.
- **Families agree.** On route 105, W3 / W0 / 2945 share melon 7/7/7 dump steps, milk 14 of 15, strawberry 24-26 of 27, and carrot 6-7 of 7-8.

Big post-handover dumps, pooled, 8 units or more (step(units)):

| product | W3 (W0 and the 2945 Farm are near-identical) |
|---|---|
| MELON | 250(24) 251(12) 264(12), plus 249, 252, 253, 255 at 6 each |
| MILK | 196(12) 257(12) 432(9) 456(9) 600(12) 717(12) |
| WOOL | 293(8) 385(11) |
| STRAWBERRY | 382(8) 429(10) 452(10) 457(8) 477(8) 517(8) 523(16) 528(13) 553(8) 576(10) |
| CARROT | 673(22) 674(16) 697(33) 715(23) 716(16) |

## 2. Detection

`WB_dp_signatures` computes the opponent's money and the WHEAT market inventory at obs steps 1 and 2 for each family. It uses `_wb_dp_market`, a port of the engine's `_process_market` that includes the per-unit lockstep against our own orders in the same slot. The port equals the engine on 400 random order mixes (a unit test).

| family | turn-1 orders | opp money at step 1 | at step 2 |
|---|---|---|---|
| W3 (herd-safe) | BUY WHEAT 8, SELL WHEAT 3, SEED WHEAT 1 | 2,854 | 1,042 |
| W0 (v15stack) | BUY 20, SELL 15, SEED 1 | 2,850 | 1,038 |
| 2945 Farm | BUY 20, SELL 15 | 2,860 | 1,048 |
| top six | BUY_ANIMAL COW 1, BUY WHEAT 5 | 2,460 | 581 |

WHEAT is 9,989 at step 1 for every family, so money is what separates them. The figures are identical in both seats, and all 8 were confirmed on the engine with the real agent files. Our own orders are a constructor argument (default: W3's opening).

**Safety audit.** Our splice plays W3's opening, so a mirror or any other W3-opening non-tape looks like W3. After each predicted dump step, the predictor checks that the market rose by at least half the predicted size once the drain is added back. It switches itself off after 2 misses, once misses exceed hits. On seed 900 vs the real W3: 47 hits, 15 misses, stays on.

## 3. Front-running in the sell engine

`WB_SellEngine(pm, predictor=dp)`; the default is None, which is off and byte-for-byte the previous behaviour (all earlier tests unchanged).

- **Trigger.** A predicted dump of at least 4 units within the next 6 steps, for a product we hold and release, that would lower the price by at least 3%.
- **Size.** Sell now the units whose quote beats the price the market will show right after the dump, net of the drain in between. That is roughly the dump size less the drain.
- **Timing.** Wait one step if we are on the pre-drain phase and there is time. Front-run orders go to slot 0.

## 4. Gate: predictor on vs off (dev seeds, both seats, same controller snapshot)

Two private builds, made at the same moment from one controller snapshot (`build.py --output`):
- `agents/.wb_splice_dp_off.py`, the build as-is (predictor off);
- `agents/.wb_splice_dp_on.py`, the same file plus `dump_predictor.py`, the predictor attached to the controller's sell engine, and an entry wrapper that feeds `observe()` every turn from step 0.

`experiments/splice/gate.py --seeds dev --workers 3` ran on both (176 games each). Games were paired by (opponent, seed, seat); every game is deterministic, and a third run reproduced 28 of 32 W3 games exactly.

| opponent | wins off → on | mean margin off → on | paired delta | games better / worse / same | t |
|---|---|---|---|---|---|
| **W3** | 0 → 0 of 32 | -21,969 → -20,991 | **+978** | 28 / 4 / 0 | +3.88 |
| **W0** | 0 → 0 | -21,961 → -21,199 | **+762** | 29 / 3 / 0 | +3.21 |
| **2945 Farm** | 0 → 0 | -21,567 → -20,884 | **+683** | 28 / 4 / 0 | +3.00 |
| W1 | 0 → 0 | -22,012 → -21,224 | +788 | 27 / 5 / 0 | +3.29 |
| reactive v1 | 0 → 0 | -18,682 → -18,682 | 0 | 0 / 0 / 32 | - |
| self-play | 6 → 6 of 16 | -396 → -396 | 0 | 0 / 0 / 16 | - |

Our bank rises about 1.0-2.0k against the tapes, and the tapes' own banks rise less. Nothing changes against reactive v1 (no match, so no predictions) or in self-play. In self-play both seats detect the other as W3, and the audit switches the predictor off at step 224, verified on seed 900 (13 hits, 49 misses by the end), before any front-run changes the game. Reading:

- **It is a consistent, small, one-directional gain.** Win counts cannot move while this controller snapshot trails by about 21k on these seeds (0-32 against all five opponents, a regression from the -8.4k B logged on seeds 0-2). Most of what the engine front-runs is milk and strawberry held back by healthy-market pacing. Melon is untouched (+0 on every game), because our melons reach the shed at W3's own dump steps.
- **Wool stays in.** A run excluding wool from front-running (`front_run_products`) was worse than front-running everything: -115 per game, worse on 4 of 32 and identical on the other 28. The gate's per-product revenue column had pointed the other way. That column values declared quantity at the pre-trade price, which is unreliable when both seats sell in the same turn, so don't tune on it.
- **The larger win is upstream.** The dump steps are known (melon 249-264, milk 196/257/270, big strawberry lots at 523/528, endgame carrot 673-716). The controller can harvest and drop ahead of them, so the engine has stock to sell first. I sent the steps and `upcoming()` to B.

## Files

| file | what |
|---|---|
| `experiments/splice/dump_predictor.py` | `WB_DumpPredictor`, exact market port, signatures, generated tables |
| `experiments/splice/sell_engine.py` | `predictor=` front-running (off by default) |
| `tests/test_splice_dump_predictor.py` | 15 tests (market port vs engine, signatures, detection, window, audit, table shape) |
| `tests/test_splice_sell_engine.py` | +8 front-running tests |
| `experiments/splice/results/gate_.wb_splice_dp_{on,off}_dev_*.jsonl` | the two gate runs (176 games each) |
| `experiments/splice/_probe_dumps.py` | dump probe (`fam/dump_runs.jsonl`) and `--table` generator with the held-out check |
| `agents/.wb_splice_dp_on.py`, `agents/.wb_splice_dp_off.py` | gitignored gate candidates from one controller snapshot |
