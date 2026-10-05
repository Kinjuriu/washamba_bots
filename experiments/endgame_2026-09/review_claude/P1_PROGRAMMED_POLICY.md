# P1: a programmed-policy agent built from the top six's inferred modules

Research track 2, separate from W6 (which stays untouched). Written 27 September 2026.

## What the top six run, module by module

Evidence: Fable's POLICY_INFERENCE.md (407 top-six seats, 402 ranks 7-12 seats, 84 W3 seats, exact re-simulation). The algorithm named for each module is the smallest mechanism consistent with the data; other mechanisms that produce the same behaviour are listed where they cannot be ruled out.

| module | what the replays show | algorithm family | ruled out |
|---|---|---|---|
| Opening (to step ~150) | action agreement across a team's own games 0.11 (Boey) to 0.91 (THIRD FARM CLUB) in steps 0-71 | fixed script (open-loop plan), a few branches on the first shops | nothing learned; Boey adds randomness |
| Land | DSM family buys at step 150, 220 and 254 in almost every game, with cash 1,900 to 5,600; Boey buys the moment cash allows | time-triggered rule with a cash guard (DSM); greedy "buy when affordable" (Boey) | cash-threshold rule for DSM (step does not vary with cash) |
| Herd | 3 sheep without a yarn store, 11 to 12 with one; 5 to 6 cows without milk shops, 9 to 10 with; 3 to 5 geese without egg shops, 6 to 8 with; same thresholds across six teams | lookup table keyed to unlocked-shop counts (a decision table, copied between teams) | per-game optimisation (would not give identical thresholds) |
| Labour | agreement 0.01 to 0.11 after step 144, no higher when the first shops match | reactive task scheduler: each turn, list the tasks the farm state needs, rank them, assign workers (greedy list scheduling or an assignment solver; the data cannot tell which) | tapes, shop-keyed routers |
| Selling (premium) | lots of 2 wool, 2 to 3 milk, 4 to 6 strawberry; 68 to 85% of lots at the hour right after the shops drain; lot size does not grow with stock; more likely to sell when price is at or above base | drain-metered release: sell about what the town just consumed, each drain tick, and more when the price is high; in trading terms a liquidity-paced execution schedule (TWAP keyed to the drain clock) | selling on price alone (milk sells equally at low prices); racing the opponent (only 3 to 8% of lots within 2 steps of theirs) |
| Selling (melon) | dumped at harvest | sell-on-harvest rule | |
| Feeding and care | 0.70 feeds and 0.69 CARE per animal-day; W3 0.77 and 0.94 | skip feeding on alternate days where the engine allows it (escape only after 2 unfed days) | |
| Fertiliser | 213 FERTILIZE actions a game vs 116 for us; they sell less of it | apply to crops rather than sell | |
| Boey's wheat | 3,300 bought and sold a game at the same average price | noise or churn; earns nothing | |

So the top six look like a hand-written hierarchical rule policy: a scripted opening, a clock for capital, a table for the herd, a reactive scheduler for labour and a paced sell rule. No module needs search or learning to explain it. Your reading is right, and it explains why replay cloning failed: we copied trajectories, when what generates them is a small set of rules that produce a different trajectory every game.

## Where W3 differs, as capital and inventory management

| | top six | W3 |
|---|---|---|
| second land quadrant | step 199 to 222 | step 266, with about $18,000 idle |
| animals at day 10 | 19 | 16 |
| stock held, share of value at day 12 | 53% | 30% |
| premium sale per event | 30 to 67% of stock | 100% of stock (full dump) |
| realised price, strawberry / wool | 144 / 139 | 117 / 122 |

W3 converts too fast, hoards cash and invests late: the opposite of the leaders (hold inventory, invest early, sell gradually).

## The hard part, measured

Peter's splice build (PR 61) already built a reactive controller with an exact price model, a sell engine and a value model. From an identical board at day 14, it lost about 16k to W3's tape over days 14 to 29. The measured causes: about 30 unit-turns a day lost to walking (1.88 moves between visits vs W3's 1.46; 1.64 actions per visit vs 1.91), lumpy wheat replanting (W3 replants 6 to 11 wheat tiles every day from day 14), and too few carrots late. The labour scheduler is the executor gap, and that is what P1 must beat.

## Build plan

1. Base: Peter's splice modules from branch agent/splice-v1 (price model, sell engine, value model, controller, day-14 handover harness). They run full episodes in 2 ms a turn.
2. Replace the capital and herd plan with the table above (land at 150/220/254, herd by shop counts).
3. Replace the labour scheduler: per turn, build the task list from farm state (feed, care, water, harvest, plant, collect, deliver), give each task a value per unit-turn, and assign workers by a min-cost assignment with batching (do every task on a tile before leaving; keep workers in fixed zones so walking stays short). Replant harvested wheat and carrot tiles the same day.
4. Selling: drain-metered lots, conditional on the opponent. Against a tape opponent (readable from its opening by day 1) keep PR 63's front-running; metering only pays against metered sellers.
5. Gates, in order: day-14 identical-board handover at -8k or better (current -16k); then from step 0, at least 16 of 32 games against W6; then the band panel at or above W6's 0.667; then the ranks 7-12 panel at or above W3's 3 of 31.

## Honest odds

The executor is the step where Peter's team stopped, so P1 is a long shot. It is also the only path above about 2,700 that the evidence points to. W6 stays in the final pair regardless, and slot 2 can carry P1 to the ladder as soon as it clears gate 2.

## Session 1 results (27 September, afternoon; MEASURED)

**Band test of production changes bolted onto the tape agent (W0 base, half the band panel, faithful games only):**
geese after day 8 -8,437 a game (0 better, 10 worse); geese before day 8 -8,614 (0/10); CARE dedup -7 (0/3); reactive crops -397 (4/11); 75-tile cap -861 (0/1, only 12 faithful games). Extra capacity on a tape costs money against real opponents, not only in the mirror.

**Day-14 identical-board test of Peter's controller (8 seeds, W3 plays both seats to step 336, then the controller takes one seat):** baseline mean -17,411. Thirteen probes of its settings (commitment, zones, planting priority, wheat target, carrots, tomato, geese, dump-style selling) all landed between -16,162 and -26,527. Parameter changes do not move it.

**Where the 17k goes (seed 902, days 14 to 29, controller vs W3):**
- Wheat: W3 keeps 25 to 30 wheat tiles and sells 308 wheat; the controller lets wheat fall to 14 to 19 tiles, sells 165 and buys 54. About -8.7k.
- Fertiliser: W3 sells 216 and buys 71 cheap to apply; the controller sells 131. About -0.8k net.
- Carrot -1.7k, strawberry -2.1k, wool -0.8k; milk +3.3k and egg +1.7k (the controller bought 4 cows and 2 geese).
- Labour: the controller makes 2,309 moves to W3's 1,828, yet W3 does more work: 690 waters vs 542, 414 harvests vs 365, 130 plantings vs 84, while also passing 162 turns vs 29. W3's tape does more with less walking.

Conclusion: the gap is a missing daily wheat rotation plus routing efficiency. Both need a new scheduler design (committed multi-task routes per worker and a replant-on-harvest rule), not settings.
