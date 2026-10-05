# Wheat-gap check: does the -284,220 WHEAT revenue gap survive as a net cash gap?

Re-simulated all 17 of W3's close losses to opponents rated above 2,500 (same set as report.md
section 5) through an instrumented resim of the recorded actions (extends `harness/resim_trades.py`
with a second instrumentation point on `_apply_unit_action`, to also capture own-tile HARVEST and
FEED, alongside the existing SELL/BUY_PRODUCT market instrumentation). All 17 replays reproduced
the exact recorded reward for both seats (34/34 records `exact: true`), confirming the resim is
faithful. Read-only: no files under `harness/` or `submissions/` were changed.

## WHEAT, summed across the 17 losses

| Metric | W3 (us) | Opponents | Δ (us − opp) |
|---|---:|---:|---:|
| Units sold | 10,664 | 17,681 | -7,017 |
| SELL revenue | 437,319 | 721,539 | **-284,220** |
| Units bought | 6,972 | 13,949 | -6,977 |
| BUY spend | 286,513 | 565,096 | -278,583 |
| **Net wheat cash (revenue − spend)** | **150,806** | **156,443** | **-5,637** |
| Harvested from own tiles (units) | 9,482 | 9,459 | +23 |
| Fed to animals (units) | 5,754 | 5,704 | +50 |

## FERTILIZER, summed across the same 17 losses

| Metric | W3 (us) | Opponents | Δ (us − opp) |
|---|---:|---:|---:|
| Units sold | 5,664 | 6,063 | -399 |
| SELL revenue | 255,084 | 266,706 | -11,622 |
| Units bought | 1,387 | 1,864 | -477 |
| BUY spend | 41,109 | 54,963 | -13,854 |
| **Net cash (revenue − spend)** | **213,975** | **211,743** | **+2,232** |
| Collected via animals (units) | 6,289 | 6,283 | +6 |
| Used on tiles / FERTILIZE (units) | 1,960 | 2,041 | -81 |

(SELL revenue and per-side totals for both products match the 0924b report's section 5 table
exactly, confirming this resim and the original one agree on the market data; the harvest/feed/
collect/fertilize columns are new, computed only for this check.)

## Verdict — measured

The wheat gap does **not** survive as a net cash gap. The -284,220 figure is a SELL-revenue-only
number, and it is driven almost entirely by churn: across these 17 losses, opponents both sold and
bought back roughly 1.6-2x as much wheat as W3 did (17,681 vs 10,664 units sold; 13,949 vs 6,972
units bought), so their extra SELL revenue is mostly offset by their own extra BUY spend. Netting
revenue against spend collapses the gap from -284,220 down to **-5,637** (W3 net wheat cash 150,806
vs opponents' 156,443) — under 2% of either side's wheat cash flow, and two orders of magnitude
smaller than the SELL-only figure. Own-tile wheat production tells the same story: units harvested
(9,482 vs 9,459) and units fed to animals (5,754 vs 5,704) are essentially identical between W3 and
these opponents, so this is not a production shortfall either — it looks like these >2,500-rated
opponents simply run more wheat market volume (buy-low/sell-high churn) without it translating into
a meaningfully larger net cash advantage. FERTILIZER shows the same pattern at smaller scale: a
-11,622 SELL-revenue-only gap flips to a **+2,232** net-cash edge for W3 once BUY spend is netted
out. **Measured**: on this data, WHEAT throughput is not the lever the SELL-revenue-only reading in
the 0924b report suggested — the two sides are close to parity in net wheat cash and own-tile wheat
production across these 17 games, and closing these losses likely needs a different lever.
