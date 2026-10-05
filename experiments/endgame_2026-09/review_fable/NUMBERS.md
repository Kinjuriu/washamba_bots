# Raw numbers behind REVIEW.md (review_fable, 26 Sep 2026)

## Corpus (analyze_corpus_dedup.py; 1,268 unique ladder games, 100% exact re-simulation)
| group | seats | win% | bank med | 2nd land day | 3rd quadrant | peak hands | geese d10/d20 | animals d10/d20 | tomato seeds | fert actions | feed/animal-day | care/animal-day | rev d0-9 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| top six | 473 | 0.79 | 106,438 | 9 | 179 (38%) | 12 | 4/5 | 19/20 | 9 | 213 | 0.70 | 0.69 | 13,608 |
| ranks 7-12 | 477 | 0.49 | 102,620 | 9 | 186 (39%) | 12 | 4/5 | 18/19 | 13 | 193 | 0.73 | 0.71 | 13,698 |
| washamba (W0/W1/W3/Peter's) | 588 | 0.66 | 98,523 | 11 | 134 (23%) | 12 | 2/3 | 16/17 | 0 | 116 | 0.77 | 0.94 | 13,164 |

Revenue medians per game (top six / washamba): WHEAT 17,809/15,090; CARROT 5,758/5,143; TOMATO 3,909/0; STRAWBERRY 29,129/26,964; MELON 13,840/14,267; EGG 8,138/4,514; MILK 17,623/15,690; WOOL 14,999/11,528; FERTILIZER 12,976/15,208.
Average realised price (top six / washamba): STRAWBERRY 144/117; WOOL 139/122; MILK 108/106; EGG 47/51; FERTILIZER 49/45.
Per team geese d10/d20: Boey 7/7, DSM 5/6, DECEM 4/5, UMG 3/4, M&M&P&Q 0/0, 吃白饭 3/6, Kaggledew 5/5, Azat 0/0, THIRD FARM CLUB 5/5, Arda 5/6.
Boey wheat: 3,317 sold / 2,924 bought per game (median, n=49). Seat-0 win rate 0.511 (n=1,259 decided); exact ties 9.
Premium (WOOL/MILK/STRAWBERRY) SELL rows by t mod 4: top six {0:.14, 1:.15, 2:.55, 3:.15} n=3,643; washamba {0:.19, 1:.24, 2:.35, 3:.23} n=2,175.

## Openings (fingerprints.py, 2,536 seats)
Top six vs opponent family (top-six seat margin): tape n=81 wins 80 median +21,064; DSM n=77 wins 65 median +8,184; Boey n=27 wins 25 median +10,095; other n=148 wins 135 median +11,751.
DECEM: 87/87 seats open [BUY_ANIMAL COW 1, BUY_PRODUCT WHEAT 5]. DSM 83/83, UMG 90/90, M&M&P&Q 68/72, Boey 60/61 Boey-opening, 吃白饭 80/80 own opening.
Our opponents (loose tape fingerprint / approximate exact money-signature match to W3-W0-2945 at obs steps 1-2): W3 upload 1: 74/84 tape, 25/84 exact (2000-2500 band 15/42; 2500-2800 band 10/25). W1 re-upload 57/61, 43/61. W0 152/158, 112/158. W1 first 141/153, 69/153.
Note: our own W3's step-1 money is 2,858 or 2,854 depending on the opponent's simultaneous orders, so the exact-signature count is approximate.

## Ranks 7-12 replay panel (r7to12panel.py, 60 recorded games, original seed and seat; faithful = tape bank within 5% of recorded)
| candidate | faithful/60 | wins | median margin | mean |
|---|---|---|---|---|
| W3 | 31 | 3 | −13,817 | −11,661 |
| W3 + front-run (PR 63) | 31 | 3 | −13,817 | −11,661 (identical banks in 60/60: overlay never fired) |
By recorded team (faithful n, wins, median): THIRD FARM CLUB 22, 0, −15,639; Arda Ceylan 5, 1, −9,979; TheEggman 3, 1, −6,314; Azat 1, 1, +17,546.

## Front-run vs opponents outside its gate pool (pool_harness.py, seeds 9001-9010, both seats)
| opponent | front-run W-L-T (mean) | W3 same seeds |
|---|---|---|
| W3 | 16-4 (+336) | ties |
| herdsafev3 | 14-6 (+476) | 16-4 (+198) |
| k0013 | 20-0 (+4,125) | (gate_w4: 0.95 on 8001-8020) |
| fieldcraft | 18-2 (+2,897) | (0.90) |
| farm2945 | 20-0 (+2,072) | (0.95) |

## Leaderboard 2026-09-24 16:13 UTC (9,975 teams)
rank 10 = 2,931; rank 50 = 2,760; rank 100 = 2,693; rank 150 = 2,652; rank 200 = 2,619; rank 300 = 2,568; rank 500 = 2,477. washamba_bots rank 508 at 2,473.7.

## Harness files re-read
race44_tests: race44 vs v15stack 19-1-4 (seeds 301-312); w1 vs w0 36-28-24 (seeds 801-924). top6_panel_results: w0 38 faithful, 6 wins, median −21,744. gen7_vs_w0: g7boey 0-20, g7decem 4-16, g7dsm 6-14. experiments_r3: B 17-43, D4 16-44, D8 13-47 vs w0.
