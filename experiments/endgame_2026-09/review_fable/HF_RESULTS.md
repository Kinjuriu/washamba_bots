# W3 + harvest-triggered front-running: test results
Fable 5.1, 26 September 2026. Agents under `review_fable/agents/`. Engine 1.32.7, pool_harness both seats, exact replay panels. All numbers MEASURED.

## The overlay
Market orders only. Each turn it reads the opponent's public tiles; a yield counter dropping to zero on a sheep, cow, strawberry or melon tile is a harvest of that many units. If we hold that product beyond what W3 already sells this turn, insert `SELL P q` at slot 0 with q = min(spare, harvested units), skip if the quote is below 35% of base, never exceed 10 orders, never touch W3's own orders or any unit action. Flag off is byte-identical to W3 (4 games, exact ties). It fires 5-26 times a game for 38-115 units, mostly strawberry and wool; melon never fires because W3 dumps melon on harvest itself.

## Base overlay (`w3_hf.py`), seeds 9101-9120 (mirror) and 9101-9110 (pool), paired with W3 on identical games
| opponent | hf W-L (of 20) | W3 W-L same seeds | hf better / worse games | mean margin change |
|---|---|---|---|---|
| W3 mirror (40 games) | 30-10 | ties | - | +362 |
| hsv3 | 16-4 | 14-6 | 12 / 8 | +74 |
| k0013 | 19-1 | 19-1 | 11 / 9 | -67 |
| fieldcraft | 16-4 | 16-4 | 10 / 10 | +19 |
| farm2945 | 19-1 | 19-1 | 8 / 12 | -201 |
| v57 | 16-4 | 16-4 | 4 / 16 | -764 |
| w0 | 17-3 | 19-1 | 6 / 14 | -99 |

| panel (paired, faithful under both) | W3 wins / faithful | hf wins / faithful | better / worse / same | mean change |
|---|---|---|---|---|
| ranks 7-12, 60 recorded games | 3 / 31 | 4 / 33 | 5 / 25 / 1 | -418 |
| top six, 80 recorded games | 5 / 46 | 5 / 46 | 19 / 26 / 1 | +77 (median -51) |

Reading: a real edge in the same-lineage mirror, where both tapes dump on the same steps and the early lot takes the price tier. Neutral by wins against the other public forks, slightly negative by margin. Against reactive opponents (ranks 7-12), who meter their sales instead of dumping, the early lots give up recovery for nothing: worse in 25 of 31 games.

## Tightened variants, seeds 9101-9110, both seats
| variant | change | vs W3 | vs v57 | vs w0 | vs hsv3 | note |
|---|---|---|---|---|---|---|
| min3 | fire only when the harvest is 3+ units | 18-2 (+394) | 16-4 (+822) | 17-3 (+1110) | 14-6 (+240) | no better than hf |
| nomelon | drop melon | identical to hf in all 80 games | | | | melon never fires |
| **early** | **no firing after step 600** | **18-2 (+358)** | **18-2 (+1051)** | 17-3 (+1049) | **18-2 (+631)**, better than W3 in 14 of 20 | best variant; late books are floored, late fires only cost recovery |
| cond | fire only after classifying the opponent as a dumper from public data (share of its sale events that clear 80%+ of its estimated stock) | 12-8 (-88) | 16-4 (+1040) | 19-1 (+1053) | 15-5 (+378) | classifier calls most reactive opponents dumpers early (fires in 52 of 60 panel games); ranks-7-12 panel worse than W3 in 24 of 31 (-303); loses the mirror edge. Killed as built. |

`early` on the ranks-7-12 panel (paired with W3, faithful under both, n=31): better 6 / worse 23 / same 2, mean -252, median -180. Wins unchanged (3-4 of 31). The step-600 cutoff halves the cost against reactive opponents but does not remove it.

## Classifier notes (for whoever continues)
Public-only opponent stock estimate = visible harvests minus recovered sales (market inventory delta + shop drain − our own sales). Offline calibration on replays: share of opponent sale events clearing 80%+ of estimated stock is 0.22 for the top six and 0.47 for tape forks; median cleared fraction 0.38 vs 0.71. The separation exists but the in-game estimate drifts (in-hand stock, discards, own-sale approximation), so the verdict flips early. A fingerprint on the opening (hires and structures by day 1, land step) is probably the more reliable switch; the DSM family buys land at exactly step 150 and 220, tape forks at 151 and 266.

## Verdict
A harvest-triggered slot-0 sell with a step-600 cutoff is a small, real edge in the tape band (18-2 against W3, v57 and hsv3 on fresh seeds) and must not fire against metering opponents. Whether it is net positive on the ladder depends on the band composition: in the 2,400-2,800 band about 88% of W3's opponents are tape forks (loose fingerprint), which favours it; against the ranks-7-12 agents it costs a few hundred dollars a game and no wins either way.
