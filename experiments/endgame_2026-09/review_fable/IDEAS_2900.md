# Ideas to test locally before the final upload (Fable 5.1, 26 Sep 2026)

Frame: 2,900 means beating the rank-7-12 reactive agents more than half the time. W3 wins 3 of 31 faithful games against them (median -13.8k). No four-day change closes that. What is testable is the sell race in the 2,400-2,800 band that sets our rating, where games are decided by 1-3% against forks of our own lineage. Realistic payoff of everything below: tens of points each, perhaps 2,650-2,800 if the ladder read lands where the lineage does.

## New measurement that motivates ideas 1, 2 and 5
The opponent's farm is fully public, including yield counters on animals and plants. A counter dropping to zero is a harvest. Exact re-simulation (review_fable/harvest_lag.py):
- Our ladder opponents (32 games): wool/milk/strawberry sales follow a visible harvest within a median 5/4/2 steps; 61%/68%/78% of sales land within 6 steps; melon 95%. 51-54% of harvests are sold within 6 steps, 72-85% within 12.
- Top six (24 seats: DECEM, M&M&P&Q, UMG, 吃白饭): the same. 60%/59%/76% of sales within 6 steps of a harvest; 75%/69%/68% of harvests sold within 6 steps.
So "the opponent just harvested P" predicts "the opponent sells P in the next few steps" for every family on the ladder, including the top.

## 1. Harvest-triggered front-running (market-only overlay on W3)
Rule, each turn: if the opponent's visible stock of P (P in WOOL, MILK, STRAWBERRY, MELON) dropped by h units since last turn, and our projected shed holds P beyond what W3 already sells this turn, insert SELL P q at slot 0, where q = the units whose current quote beats market_price(P, inventory + h) net of the drain in between. Never exceed 10 orders, never remove or reorder W3's orders, flag-off must be byte-identical. PR 63's file structure can be reused; replace its money-signature detector with the harvest detector. PR 63 fires against about 30% of W3's real opponents (exact signatures); this fires against all of them.
Test: 40 fresh-seed W3 mirror (both seats); 20 games each vs hsv3, k0013, fieldcraft, farm2945, v57; faithful top-six panel and the ranks-7-12 panel (review_fable/r7to12panel.py) paired against W3 on games faithful under both.
Pass: wins >= W3 on every pool; paired panel margin >= W3's. Kill: any pool worse by 2 or more wins, or faithful count falls below W3's by more than 5 (the overlay is knocking the tape opponents off their path).

## 2. Post-drain timing of our own reserve sells
Shops drain at interpreter steps that are multiples of 4, after that step's market. The first sale on the drained book is the action chosen at observation step 1 mod 4. Top six put 55% of premium sells there; our tapes 35%; uniform is 25%.
Rule: when W3's reserve wants to sell P now and (a) no rival sale of P was seen in the last 4 steps and (b) the rival has no visible harvest of P in the last 6 steps, hold the order until the next post-drain slot (at most 3 steps). Gain per unit = drain x slope: strawberry with two strawberry shops is about 12 units x $1.92 = $23 (15% of price); wool with one yarn store about 4 x $3.5 = $14; milk similar. Idea 1 is the guard against the rival selling in the gap.
Same harness. Kill on any mirror regression; a delay is the risky direction in this band.

## 3. Use the uploads as the test bed, with discipline
W3 stays in slot 1 at all times. One candidate per day in slot 2. Read only at >= 60 post-burst games, at equal n, with mean opponent rating within 150 of W3's. Order: PR 63 front-run (already gated), then idea 1, then idea 2, then the combination. Final pair = W3 + the best candidate; W3 x2 if nothing beats W3's equal-n read by more than 100. Log every upload in submissions_log.md before pressing the button.

## 4. Change the gate
An exact mirror is a tie by construction, so 17-43 at -19 mean is noise, not a fail. Gate on: wins against five siblings/forks on fresh seeds, absolute self-play bank, and paired faithful panels. Only about 30% of W3's ladder opponents are exact copies; about 88% are forks. C1's lost strawberry volume (247 to 180) looks like an order-cap or tile conflict, not a law of the mirror; not worth reopening this week, but do not carry "any board change loses" forward as fact.

## 5. The algorithm for a reactive agent (after the deadline, or a slot-2 long shot only if a controller already exists)
Selling is a two-player race with perfect information about supply in hand. Per product and step you can compute exactly: own stock, the opponent's visible pipeline (units on tiles, harvest events), the drain over the next k steps from unlocked shops, and market_price. Sell when the opponent's pipeline over the next k steps exceeds the drain over the same window (their units will hit the book before it recovers); otherwise hold to the post-drain slot. This is what the top six approximate. Pair it with the tape's second half as the production template (W3 replants 6-11 wheat a day from day 14 and converts strawberry land to carrots from day 22; PR 61 lost 15k by not matching that). Gate: the day-14 identical-board handover must be non-negative before anything else.

## Not worth the days left
Constant searches; production overlays on the tape; a third-quadrant tomato farm ($4k land plus $2.5k of 13th-14th hands against about $7k gross on a book that crashes after 200 units); tapes cut from top-six replays; RL; endgame liquidation (W3 sells everything, measured $0 left in 60 games); shed overflow (about 5 units and $235 a game, the same for everyone).

## Engineering notes for any overlay
Capture W3's real entrypoint as the last callable; respect the 10-order cap; a slot-0 insert shifts every W3 order one index later against the opponent's list; catch every exception and fall back to W3's action; flag-off identity on 3 seeds; W3 already peaks at about 245 ms a turn, so keep the overlay under 10 ms.
