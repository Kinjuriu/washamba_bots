# Top-six per-day targets (Builder A, 25 Sept)

What the top six actually do, day by day, measured from 114 real top-six seats. This is the target for Builder B's controller. Machine-readable version: `experiments/splice/top6_targets.json`. To compare a candidate, run `experiments/splice/compare.py` (section 5).

## Summary

- **The plan, as medians.**
  - Hires and cash: 4 hands on day 0, 6 on days 2-4, 8 on day 6, 11 from day 10. Cash is run near zero at dawn on days 2-8 (median $29-110; $797 on day 6).
  - Herd: 2 cows and 3 sheep until day 6, then 9 cows by day 10. Geese go 0 → 3 → 5 by day 12.
  - Land: 50 tiles on day 8, 75 by day 10, and in most non-tape games 100 by day 12.
  - Crops: 10 melon and 10 wheat by day 2. Strawberries start on day 3-4 (8 tiles on day 4) and peak at 28-32 tiles on days 15-18. Tomatoes start on day 10-12 and reach 13 tiles by day 21. Carrots come last, at 20 tiles on day 27.
  - Upkeep: 45-58 waters a day and about 0.9 fed/cared share through day 15. Fertilizer: 17-20 collected and 7-14 applied a day. About 1% idle.
- **Against tapes they win by +7,235, not 21,000.** In 27 real games vs 2945_farm-family tapes, the top six win 22 and the median margin is +7,235. Compared within the same game, so seed and shops cancel, the top six **trail** by about 5.8k at dawn on days 12-14 and **lead** by 10-11k over days 20-26. The edge comes from:
  - strawberries 3-4 days earlier (+5 to +8 tiles on days 4-8, +6.2k per season);
  - about one more hand every day;
  - the second land quadrant on day 10;
  - wool (+2.4k).
  They concede melon (-4.6k), wheat (-3.5k) and carrot (-2.5k) to the tape.
- **Premium prices are market context, not skill, at this resolution.** In the same games the tape opponent realizes about the same premium prices: milk 115 vs 109, strawberry 151 vs 163. Shop draws move prices a lot. W3 against itself banks 70.6k / 116.3k / 136.3k on seeds 900 / 901 / 902, against a top-six median of 111.5k. A single-seed `compare.py` read is a statement about the **plan**, not the bank.

## 1. Data and method

- **Source.** `experiments/endgame/kaggle_ds/` (ashok205 top-10 replay archive), shards 2026-09-13 to 09-23. There are 82 distinct episodes: 55 picked round-robin across top-six teams, most recent first, plus all 27 top-six-vs-tape episodes in the archive. That gives 114 top-six seats, since mirrors count both seats. Dates 09-16 (2 games) and 09-20 to 09-23. Seats by team: Vadim Vasilenko 34, UMG 18, DSM 17, DECEM 16, mtmr_s1 10, Orbital Terraformer 8, Arda Ceylan 6, TheEggman 5.
- **Seat rule.** The top-six seat is identified from each replay's own turn-1 orders, BUY_ANIMAL COW 1 + BUY_PRODUCT WHEAT 5, using the canonical form from `experiments/endgame/field_families.py`. The opponent's family comes from the same classifier. Teams switch families. DECEM opens top-six on 09-23, contrary to `field_families_2026-09-25.md`'s n=4 sample. mtmr_s1 opens 2945_farm on 09-21 and top-six on 09-23.
- **Exact re-simulation.** Every replay was re-run through the local engine (1.32.7) from its recorded actions and `info.seed`. Money for both seats matched the recording at every step in all 82 games. On one game the tiles, market inventory and shops were also checked at every step: 0 mismatches. Instrumented engine functions (`experiments/splice/daymetrics.py`) then give exact trades at realized prices, effective unit actions (no-ops excluded) and feed/care coverage at midnight.
- **Splits.**
  - **vs_tape**: 27 seats. The opponent is in the v15stack / 2945_farm / herd_safe families. In practice all 27 are 2945_farm: mtmr_s1 18, 吃白饭的大肥鱼 7, Thomas Tschinkel 2. It is also concentrated: 16 of the 27 are Vadim Vasilenko vs mtmr_s1 on 09-21. Treat it as indicative.
  - **vs_other**: 23 seats, other families.
  - **vs_top6**: 64 seats (32 mirror games).
  - **all**: 114 seats.
  Top-six-vs-tape games are rare because the ladder pairs by rating. In the full archive since 09-13 the scan found only 27 such seats, against 1,307 vs other families and 1,032 in mirrors (`experiments/splice/top6_scan.json`).
- **Day convention.** Day d covers obs steps 24d to 24d+23. State metrics (money, tiles, animals, crops) are taken at dawn, obs step 24d. Flows (revenue, hires, waters) are totals over the day. "Fed/cared share" is the share of placed animals fed or cared that day, measured just before the midnight reset. Care only banks on a day the animal is also fed.

## 2. Per-day targets: median [p25-p75]

### all (n = 114)

Assets at dawn:

| day | money at dawn | tiles owned | tiles planted | hands hired | cows | sheep | geese |
|---|---|---|---|---|---|---|---|
| 0 | 3.0k [3.0k-3.0k] | 25 [25-25] | 0 [0-0] | 4 [4-4] | 0 [0-0] | 0 [0-0] | 0 [0-0] |
| 2 | 29 [2-32] | 25 [25-25] | 20 [19-20] | 6 [6-6] | 2 [2-2] | 3 [3-3] | 0 [0-0] |
| 4 | 68 [12-91] | 25 [25-25] | 20 [19-20] | 6 [6-6] | 2 [2-2] | 3 [3-3] | 0 [0-0] |
| 6 | 797 [729-861] | 25 [25-25] | 20 [20-20] | 8 [8-8] | 2 [2-2] | 3 [3-3] | 0 [0-0] |
| 8 | 110 [44-290] | 50 [50-50] | 36 [36-37] | 9 [9-9] | 7 [5-8] | 3 [3-3] | 1.5 [0-2] |
| 10 | 454 [224-701] | 75 [75-75] | 53 [52-54] | 11 [11-12] | 9 [7-11] | 3 [3-6] | 3 [1-5] |
| 12 | 8.3k [6.2k-11.0k] | 100 [75-100] | 61 [56.2-66] | 11 [11-12] | 9 [7-11] | 3 [3-9] | 5 [3-7] |
| 15 | 23.8k [21.6k-27.0k] | 100 [75-100] | 64 [57-73] | 11 [11-12] | 9 [7-11] | 3 [3-9] | 5 [3-7] |
| 18 | 42.5k [38.6k-46.7k] | 100 [75-100] | 63 [56.2-74] | 12 [11-12] | 9 [7-11] | 3 [3-9] | 5 [3-7] |
| 21 | 58.6k [51.8k-68.6k] | 100 [75-100] | 63 [56-73] | 11 [11-12] | 9 [6.2-11] | 4 [3-9] | 5 [3-7] |
| 24 | 72.7k [62.6k-83.0k] | 100 [75-100] | 61 [56-70] | 11.5 [11-12] | 8 [6-10] | 3.5 [3-8] | 5 [3-7] |
| 27 | 85.8k [76.1k-97.7k] | 100 [75-100] | 60 [56-69] | 11 [11-11] | 7 [5.2-10] | 3.5 [3-7] | 5 [3-7] |
| 29 | 98.3k [86.8k-110.8k] | 100 [75-100] | 34 [30-39] | 10 [10-10] | 7 [4-9] | 0 [0-3] | 4 [2-6] |

Crops at dawn (tiles):

| day | wheat | strawberry | tomato | carrot | melon | empty structures | empty tiles |
|---|---|---|---|---|---|---|---|
| 0 | 0 [0-0] | 0 [0-0] | 0 [0-0] | 0 [0-0] | 0 [0-0] | 0 [0-0] | 25 [25-25] |
| 2 | 10 [10-10] | 0 [0-0] | 0 [0-0] | 0 [0-0] | 10 [10-10] | 0 [0-0] | 0 [0-1] |
| 4 | 0 [0-1] | 8 [7-9] | 0 [0-0] | 0 [0-0] | 10 [10-11] | 0 [0-0] | 0 [0-1] |
| 6 | 0 [0-0] | 10 [9-10] | 0 [0-0] | 0 [0-0] | 10 [10-11] | 0 [0-0] | 0 [0-0] |
| 8 | 7 [4-11] | 19 [14-22] | 0 [0-0] | 0 [0-0] | 10 [10-11] | 0 [0-0] | 1 [0-2] |
| 10 | 20 [17-22] | 21 [16-24] | 1 [0-2] | 0 [0-0] | 10 [10-11] | 0 [0-0] | 4 [3-6.8] |
| 12 | 29 [25-34] | 23 [19-29] | 3 [0.2-5] | 0 [0-4] | 0.5 [0-2] | 0 [0-0] | 6 [1-13] |
| 15 | 22 [17-27] | 28.5 [22-34.8] | 6 [3-12] | 0 [0-8.8] | 0 [0-0] | 0 [0-0] | 2 [0-6] |
| 18 | 17.5 [14-21] | 30 [24-36.8] | 10 [5-17] | 1.5 [0-9] | 0 [0-0] | 0 [0-0] | 2 [0-5] |
| 21 | 22 [15.2-27] | 19.5 [14-28] | 13 [8-19] | 4.5 [0-13] | 0 [0-0] | 0 [0-0] | 2 [1-5] |
| 24 | 30 [24.2-35.8] | 12 [7.2-16.8] | 9 [6-13] | 11 [3-17] | 0 [0-0] | 0 [0-1] | 3 [1-7] |
| 27 | 28 [22-33] | 8 [4-11] | 6 [3-8] | 20 [15-27.8] | 0 [0-0] | 0 [0-1] | 5 [2-8.8] |
| 29 | 15 [12-19] | 6 [1.2-8] | 5 [3-6] | 8 [5-12] | 0 [0-0] | 4.5 [3-8] | 31.5 [24-36] |

Flows per day:

| day | revenue to date | revenue that day | waters | fed share | cared share | fertilizer collected | fertilizer applied | idle share |
|---|---|---|---|---|---|---|---|---|
| 0 | 140 [140-140] | 140 [140-140] | 16 [15-16] | 0.80 [0.80-0.80] | 0.80 [0.60-0.80] | 0 [0-0] | 0 [0-0] | 0.08 [0.07-0.12] |
| 2 | 1.1k [1.1k-1.2k] | 514 [489-517] | 20 [19-20] | 0.60 [0.60-0.95] | 1.00 [1.00-1.00] | 5 [5-5] | 0 [0-0] | 0.26 [0.15-0.27] |
| 4 | 2.2k [2.1k-2.2k] | 496 [466-500] | 11 [9-17] | 1.00 [1.00-1.00] | 1.00 [1.00-1.00] | 5 [5-5] | 0 [0-0] | 0.24 [0.10-0.44] |
| 6 | 6.7k [6.6k-6.8k] | 4.0k [3.9k-4.1k] | 27 [25-28.8] | 0.50 [0.42-0.82] | 0.60 [0.50-0.91] | 5 [5-5] | 0 [0-0] | 0.05 [0.04-0.07] |
| 8 | 10.9k [10.6k-11.1k] | 3.1k [2.8k-3.4k] | 37 [36-39] | 0.74 [0.55-0.93] | 0.85 [0.69-0.98] | 12 [12-13] | 0 [0-0] | 0.04 [0.03-0.08] |
| 10 | 22.8k [22.3k-23.4k] | 9.4k [9.0k-9.9k] | 45 [41-47] | 0.94 [0.89-1.00] | 0.94 [0.89-1.00] | 17 [16-18.8] | 2 [0-3] | 0.01 [0.00-0.03] |
| 12 | 32.1k [30.8k-34.1k] | 4.2k [3.5k-5.4k] | 56 [52-61] | 0.91 [0.82-1.00] | 0.92 [0.82-1.00] | 20 [18-21] | 7 [5-9] | 0.01 [0.00-0.02] |
| 15 | 51.7k [47.2k-55.6k] | 5.3k [4.2k-7.3k] | 58 [53-63.8] | 0.92 [0.84-1.00] | 0.92 [0.84-1.00] | 20 [18-22] | 12 [10-14] | 0.01 [0.00-0.02] |
| 18 | 75.0k [68.3k-81.4k] | 7.2k [5.4k-9.1k] | 50 [44-56] | 0.70 [0.53-0.82] | 0.70 [0.53-0.82] | 20 [17.2-22] | 9 [8-12] | 0.01 [0.00-0.02] |
| 21 | 91.2k [81.1k-101.8k] | 5.0k [3.7k-6.2k] | 57 [52.2-63] | 0.84 [0.75-0.93] | 0.79 [0.70-0.89] | 19 [17-22] | 13 [10-16] | 0.01 [0.00-0.02] |
| 24 | 106.5k [95.2k-119.0k] | 5.2k [4.2k-6.4k] | 58 [52.2-62] | 0.59 [0.45-0.73] | 0.58 [0.43-0.73] | 18 [16-20] | 14 [12-17] | 0.01 [0.00-0.02] |
| 27 | 121.3k [109.9k-134.9k] | 5.5k [4.5k-6.6k] | 52 [48.2-56] | 0.66 [0.56-0.78] | 0.62 [0.50-0.76] | 17 [15-19] | 13 [11-15] | 0.01 [0.00-0.03] |
| 29 | 135.8k [122.3k-149.3k] | 7.1k [6.1k-8.3k] | 20 [4-24] | - | - | 11.5 [9-13] | 0 [0-0] | 0.02 [0.01-0.05] |

Fed/cared share falls to 0.5-0.7 from day 18. The top six stop feeding animals whose next yield won't pay back before the end, and sheep go to 0 by day 29.

### vs_tape (n = 27): where it differs from `all`

The same schedule, with these differences:

- **Never a third quadrant** against tapes: 75 tiles all season (0 of 27 seats buy it, against 13/23 vs other and 50/64 in mirrors).
- Fewer geese: 3 [0.5-5].
- A slightly later tomato start: 2 tiles on day 15, 5-7 on days 18-21.
- More strawberries: 32 tiles on days 15-18.

Money at dawn: 630 on day 10, 10.4k on day 12, 23.1k on day 15, 45.5k on day 18, 68.7k on day 21, 81.3k on day 24, 94.6k on day 27, 105.4k on day 29. The full tables are in the JSON (`splits.vs_tape.per_day`).

### Season

| | all (n=114) | vs_tape (n=27) | vs_other (n=23) | vs_top6 (n=64) |
|---|---|---|---|---|
| final bank | 105,648 [92,034-119,627] | 111,517 [99,034-122,461] | 114,280 [105,174-128,756] | 97,154 [89,399-110,620] |
| margin vs opponent (median) | +2,005 | +7,235 | +1,851 | +0 |
| MILK revenue (units x avg price) | 19,424 (196 x 111) | 21,000 (208 x 109) | 27,599 (196 x 133) | 18,092 (184 x 103) |
| WOOL | 13,758 (102 x 141) | 12,719 (80 x 141) | 11,712 (98 x 150) | 15,962 (122 x 138) |
| STRAWBERRY | 28,882 (212 x 142) | 34,320 (246 x 163) | 36,275 (228 x 147) | 25,904 (190 x 129) |
| TOMATO | 6,631 (97 x 69) | 4,353 (60 x 84) | 5,549 (94 x 73) | 8,388 (124 x 65) |
| EGG | 7,035 (160 x 46) | 4,462 (88 x 48) | 6,836 (156 x 45) | 7,796 (176 x 45) |
| MELON | 13,064 (60 x 202) | 12,016 (66 x 182) | 13,650 (60 x 211) | 13,457 (60 x 207) |
| WHEAT | 15,896 (455 x 35) | 14,446 (379 x 38) | 17,569 (451 x 37) | 15,984 (498 x 33) |
| CARROT | 6,110 (153 x 43) | 4,545 (112 x 48) | 6,222 (144 x 47) | 6,570 (160 x 40) |
| FERTILIZER | 12,392 (228 x 53) | 13,234 (242 x 55) | 12,106 (220 x 55) | 12,264 (226 x 52) |

The "avg price" is pooled over all games (total revenue / total units). The unit counts are medians.

## 3. Top six vs tape, within the same game (27 games, median of per-game differences)

Both seats share the seed, shops and market, so this is the clean read of where the top six beat a tape.

| top6 minus tape | d4 | d6 | d8 | d10 | d12 | d14 | d16 | d18 | d20 | d24 | d29 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| money at dawn | -218 | -59 | -320 | -1,654 | -5,805 | -5,589 | +2,322 | +7,345 | +9,204 | +10,781 | +7,507 |
| revenue to date | -263 | +359 | +538 | -7,150 | -7,461 | -2,670 | +5,252 | +9,678 | +10,759 | +11,096 | +1,556 |
| tiles owned / planted | 0 / 0 | 0 / +1 | 0 / 0 | +25 / +17 | 0 / +3 | 0 / 0 | 0 / -2 | 0 / -2 | 0 / -4 | 0 / -6 | 0 / -7 |
| hires to date | +4 | +7 | +10 | +12 | +15 | +19 | +19 | +19 | +20 | +21 | +18 |
| strawberry tiles | +8 | +5 | +5 | +4 | -5 | -1 | -1 | +1 | -2 | -2 | +5 |
| strawberry revenue to date | 0 | 0 | 0 | 0 | 0 | 0 | +7,277 | +9,504 | +7,862 | +6,284 | +6,228 |
| melon revenue to date | 0 | 0 | 0 | -6,863 | -4,642 | -4,642 | -4,079 | -4,031 | -4,031 | -4,031 | -4,642 |
| idle share | -0.13 | -0.03 | -0.10 | -0.08 | -0.10 | -0.03 | -0.05 | -0.04 | -0.03 | -0.03 | -0.04 |

Season revenue, top six minus tape:

| product | difference |
|---|---|
| strawberry | +6,228 |
| wool | +2,413 |
| egg | +696 |
| milk | +564 |
| fertilizer | -443 |
| tomato | -1,891 |
| carrot | -2,467 |
| wheat | -3,465 |
| melon | -4,642 |

Spending is about equal (-1,043). The final bank margin is +7,235.

Reading: the top six invest harder on days 10-14, with the second quadrant on day 10 and more hands. They trail on melon while it sells, then overtake on strawberries from day 15 and keep the lead.

## 4. W3 against the targets (`compare.py`, W3 vs W3, seeds 900-902, vs_tape band)

W3's own plan barely varies by seed (it is a tape), so these gaps repeat on all three seeds:

1. **The second land quadrant comes two days late.** W3 owns 50 tiles on days 10-11; the top six own 75 on day 10. W3 has 37 tiles planted on day 10 against 54. It holds 2.1-2.8k at dawn on day 10 against the top six's 630, and is +3.3k / +4.9k / +6.0k above the top-six median on day 12. That is cash not yet turned into production.
2. **Strawberries start three days late.** W3 has 0 strawberry tiles on days 3-5 against 3 / 8 / 9, and 4 on day 6 against 9. Its cumulative strawberry harvest by day 13 is 0 against 14. Early strawberries are the top six's biggest within-game edge over tapes (+6.2k per season, section 3). This is in W3's pre-handover tape, so the splice inherits it.
3. **No tomatoes, ever.** W3 has 0 tomato tiles all season against the top six's 2 on day 15, 5-7 on days 18-21 and 3-5 later (vs tape). Top-six tomato revenue is 4.4k vs tapes and 6.6k across all games.

Also consistent: 4 hands on days 2-5 against 6, and 8 on days 8-9 against 9-10. W3 idles 3-13% of unit-turns on days 8-20 against 1-3%. It waters less on most mid-season days (40 vs 54 on day 15, 38 vs 53 on day 17). It keeps 4-6 sheep against 3.

What is **not** consistent is the bank: 70,559 / 116,330 / 136,330 against the median of 111,517. Those numbers come from the seeds' shop draws. Seed 900 drains 7 milk a day on day 15 against a real-game median of 13; seed 902 drains 19-25 milk and 25-37 strawberries a day. Read `compare.py`'s market-context line before reading its prices.

## 5. Using `compare.py`

```
.venv/Scripts/python.exe experiments/splice/compare.py <candidate.py> [--seed 900]
    [--opponent agents/w3_herdsafe2700.py] [--seat 0] [--split all|vs_tape|vs_other|vs_top6] [--top 15]
```

It plays one episode in a single process, about 40 s with two tape agents, and prints:

- the dawn-money gap to the top-six median every 3 days;
- the town drain for milk, wool, strawberry, tomato and egg on days 9/15/21, against the median real game;
- the headline metrics furthest outside the top-six IQR, with the days they are outside it (`--all-metrics` ranks everything);
- four day-by-day panels: assets, crops, revenue and harvest to date, and upkeep. Each cell is `value (top-six median)`, marked `<` or `>` when outside the IQR;
- season revenue by product for both seats against the top-six medians for every split.

Use several seeds for anything price-related. For the plan metrics (land, herd, crops, crew, cash deployment), one seed is enough.

To refresh the targets after new shards arrive (single process, about 10 s per game):

```
top6_extract.py --games 60 --tape 30 --since <date>
top6_extract.py --scan --since <date>
top6_extract.py --add-tape 40
top6_extract.py --add-shops
```

## Files

| file | what |
|---|---|
| `experiments/splice/top6_targets.json` | percentiles by day (p25/p50/p75/n) for about 150 metrics × 4 splits, plus season aggregates |
| `experiments/splice/top6_games.jsonl` | 114 seats: per-day values for the top-six seat and its opponent (3.4 MB; re-split without re-parsing) |
| `experiments/splice/top6_scan.json` | opening classification of 3,371 archive episodes (for finding more top-six-vs-tape games) |
| `experiments/splice/daymetrics.py` | the shared instrumentation and metric definitions |
| `experiments/splice/top6_extract.py` | extraction and aggregation |
| `experiments/splice/compare.py` | candidate vs targets |
