# Splice value rules: fertilizer and crop per tile-day (Builder A, 25 Sept)

Why: in B's day-14 identical-board trace (`splice_controller_log.md`, 07:20 UTC), we apply 149 fertilizer and sell 96, while W3 sells 218 and buys 73 cheap late units to apply. W3 also keeps 24-38 wheat tiles to about day 26, then runs 18-31 carrot tiles on days 26-28. Helper: `experiments/splice/value_model.py` (`WB_ValueModel`). Its yield simulation matches the engine unit for unit (every crop, fertilized at every age 0-16, plantings from day 0 to 27: 0 mismatches; `tests/test_splice_value_model.py`, 14 tests).

## Summary

- **Fertilizer rule (sent to B):** apply iff extra units × crop quote > fertilizer quote; sell every unit you won't apply that way; buy fertilizer whenever its quote is below the best pending application. In a tape market that means:
  - days 8-9: fertilize only strawberry and tomato production days, and sell the rest (fertilizer fetches 80+);
  - wheat pays from about day 10, carrots from about day 14;
  - from about day 16, buy fertilizer to put on every wheat and carrot tile.

  Our controller has it backwards: we apply early and sell late.
- **Crops, tape market:**
  - strawberry only if planted by day 9 (the tape dumps strawberries on days 22-24, crashing them to 11);
  - tomato days 10-18 (37-50 per tile-day with typical shops, far more with 2+ tomato shops);
  - **carrot beats wheat from about day 12, and is clearly best from day 19**, because tapes don't sell carrots until day 26.
- **W3's late plan is right for non-tape markets, a week late for tapes.** Against non-tapes wheat wins until about day 23 and carrots from about day 24. Against a tape, switch wheat tiles to carrots from about day 19.

## 1. One FERTILIZE (engine rules)

- **Covers three days.** FERTILIZE on day d sets `fertilized_until_day = max(current, d + 2)`, covering days d, d+1 and d+2.
- **One-shot crops (wheat, carrot, melon):** a watered day inside the yield window adds 2 instead of 1, up to the crop's cap. The bonus is decided when the WATER happens, so **FERTILIZE before that day's WATER**.
- **Ongoing crops (tomato, strawberry):** a production event at the end of a watered, fertilized day adds 2 instead of 1. Order within the day doesn't matter.

Extra units from one application, by plant age at application (fresh, daily-watered tile):

| crop | extra units by age | units per planting, plain → best plan |
|---|---|---|
| WHEAT | age 0: +1, **ages 1-3: +2**, age 4: +1 | 4 → 6 (one application, age 2) |
| CARROT | **ages 0-3: +1** | 3 → 4 (one, age 2) |
| TOMATO | 5: +1, 6: +2, **7-8: +3**, 9: +2, 10: +1 | 4 → 8 (ages 7 and 10) |
| STRAWBERRY | **production days 9, 11, 13: +2**; other ages 7-15: +1 | 4 → 8 (ages 9 and 13) |
| MELON | 0 at every age (it reaches the cap of 6 unfertilized) | 6 → 6 |

**Economics.** Gain of one application at the best age, priced at measured realized prices on the sale day, against fertilizer's price that day. Nothing drains fertilizer (no shop, no town centre), so its price only falls as players sell.

| day | fertilizer price (tape market) | wheat +2 | carrot +1 | tomato +3 | strawberry +2 | melon |
|---|---|---|---|---|---|---|
| 8 | 83 | 80 ✗ | 36 ✗ | 186 ✓ | 422 ✓ | 0 ✗ |
| 10 | 77 | 80 ✓ | 42 ✗ | 191 ✓ | 422 ✓ | 0 ✗ |
| 12 | 67 | 82 ✓ | 42 ✗ | 195 ✓ | 422 ✓ | 0 ✗ |
| 14 | 55 | 82 ✓ | 58 ✓ | 201 ✓ | 414 ✓ | 0 ✗ |
| 16 | 46 | 84 ✓ | 58 ✓ | 207 ✓ | 390 ✓ | 0 ✗ |
| 20 | 32 | 84 ✓ | 61 ✓ | 224 ✓ | 183 ✓ | 0 ✗ |
| 24 | 18 | 80 ✓ | 62 ✓ | 244 ✓ | 81 ✓ | 0 ✗ |
| 28 | 8 | 72 ✓ | 44 ✓ | 87 ✓ | 30 ✓ | 0 ✗ |

The non-tape market has the same shape: fertilizer 82 on day 8, 40 on day 18 and 20 on day 28. Wheat pays from day 10, carrots from about day 18, and tomato and strawberry always.

**The rule, one line:** apply iff `extra_units × crop quote > fertilizer quote` (tile watered that day, FERTILIZE before WATER); sell every unit you won't apply; `BUY_PRODUCT FERTILIZER` whenever its quote is below your best pending application. That is W3's pattern: sell 218 early at 55-83, buy 73 late at 8-32 for wheat and carrots.

**Labor.** A FERTILIZE costs one unit-turn, plus a PICKUP or COLLECT to carry the fertilizer. Late wheat nets about 60-75 per turn and strawberry and tomato 150-400, against about 40-60 for a WATER. The high-value applications are worth routing for.

## 2. Value per tile-day by planting day

`crop_value(crop, plant_day, scenario=...)` works per planting. It assumes the tile is watered daily and harvested promptly, and applies fertilizer per the rule above. The result is net of seed and fertilizer, divided by the tile-days occupied (planting to last harvest, ongoing crops including the DIG day). Prices are median realized prices by day in two markets:
- tape: 72 local W3/W0/2945 games;
- non-tape: 87 real top-six seats against non-tape opponents.

Tomato in the tape market uses a drain-only projection with typical shops (see below). All values are for a marginal tile: our own extra supply lowers the price a little per unit (carrot about 0.08 per unit below I0, tomato 0.12 below the hinge knee).

Net per tile-day (net per labor turn):

| plant day | tape: wheat | tape: carrot | tape: tomato | tape: strawberry | non-tape: wheat | non-tape: carrot | non-tape: tomato | non-tape: strawberry |
|---|---|---|---|---|---|---|---|---|
| 8 | 31 | 27 | 34 | **44** | 31 | 31 | 38 | **44** |
| 10 | 34 | 27 | **37** | 26 | 32 | 28 | **39** | 37 |
| 12 | 36 | 39 | **40** | 10 | 33 | 28 | **38** | 37 |
| 14 | 39 | 42 | **44** | 2 | 33 | 28 | **37** | 28 |
| 16 | 41 | 45 | **47** | 1 | 36 | 30 | **36** | 20 |
| 18 | 42 | 48 | **50** | -5 | **37** | 32 | 36 | 7 |
| 20 | 41 | **46** | 28 | - | **38** | 33 | 18 | - |
| 22 | 42 | **53** | - | - | **37** | 33 | - | - |
| 24 | 42 | **51** | - | - | 31 | **32** | - | - |
| 26 | **41** | 37 | - | - | 20 | **26** | - | - |
| 27 | 31 | **36** | - | - | 13 | **24** | - | - |

(Per labor turn: wheat 22-30, carrot 21-35, tomato 26-37, strawberry up to 39. The crops are close per unit of labor; per tile-day they differ.)

**Tomato depends on the shops, not the calendar.** The hinge curve spikes once cumulative drain passes 200 units below I0. Net per tile-day of a fertilized tomato planting, from a drain-only projection:

| plant day | typical (1 tomato shop day 9, 2 by day 18) | 2 tomato shops from day 6 | 3 tomato shops from day 9 |
|---|---|---|---|
| 10 | 36 | 46 | 65 |
| 12 | 39 | 52 | 89 |
| 14 | 41 | 61 | 122 |
| 16 | 43 | 75 | 164 |
| 18 | 50 | 93 | 216 |
| 20 | 28 | 59 | 144 |

**Verdicts:**
- **Strawberry:** plant only through day 9 against a tape; its 22-24 dump crashes later plantings. Against non-tapes, through about day 13.
- **Carrot vs wheat against a tape:** carrots beat wheat from about day 12 and lead by 4-11 per tile-day on days 16-25. Against a tape, correct W3's "wheat until 26, carrots from 26" to **carrots from about day 19** (with the tape's own day 26-28 carrot dumps in view). Against non-tapes, W3's plan holds: wheat until about day 23, carrots from day 24.
- **Tomato:** beats both in any world with 2+ PIZZA_SHOP / FARMERS_MARKET by day 9, and dominates with 3. In typical worlds it is only marginally better (days 10-18) and needs production-day fertilizing. Price it live: `crop_value(crop, day, market=obs["market"], shops=...)`.
- **Melon:** never fertilize.

## 3. API (`experiments/splice/value_model.py`)

```python
vm = WB_ValueModel(WB_PriceModel())
vm.fertilize_value(tile, day, obs["market"], shops)
    # -> {'extra_units', 'gain', 'cost', 'net', 'apply'}
    # tile is the obs tile dict (crop, planted_day, yield_units, fertilized_until_day, watered_today)
    # gain = extra units x the crop's live quote; cost = fertilizer's sell quote now
vm.crop_value(crop, plant_day, market=None, shops=None, scenario="tape"|"nontape")
    # -> units, revenue, fert_days, net, tile_days, per_tile_day, labor, per_labor
    # with market=obs["market"] + shops: live drain projection, capped by the tape curve
    # for products tapes flood
WB_vm_harvests(crop, planted_day, day, ...)   # exact [(sale_day, units)] for a tile
```

Stdlib only, WB_-prefixed, imports only `price_model`. To call it from the controller, the harness adds `value_model.py` to `build.py` SPLICE_MODULES before `controller.py`.
