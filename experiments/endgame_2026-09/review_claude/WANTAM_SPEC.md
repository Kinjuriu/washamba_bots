# WANTAM: a new labour scheduler in three layers (spec, 27 September 2026)

Stephane's design, with Claude's additions marked (C). Reuses only proven infrastructure from Peter's splice build: board parsing (_WB_View), legal-action emission, movement primitive (_step_toward), the exact price model, the sell engine and dump predictor, and W3's opening up to the handover. Everything that decides how much labour to buy, what work matters, which worker does it and how long it stays committed is new.

## Honest status of P1 so far

Reused unchanged from Peter: every class and function in the build (W3 opening, WB_PriceModel, WB_SellEngine, WB_DumpPredictor, value model, WB_Controller with _dawn, _plan_herd, _crop_targets, _tasks, _zones, _execute, _market, _sellable).
Modified: two lines (a wheat floor in _crop_targets, a longer wheat reserve in _sellable) plus constant patches.
New scheduler code: none. So P1 has not yet done what we set out to do; WANTAM is that work.

## Layer 1: capacity planner (dawn)

Question: how many hands to hold today, given that each extra hire costs more than the last (the Fibonacci wage ladder: the 12th hand of a day costs 144, the 13th 233).

1. Mandatory load (trap doors). Tasks whose miss is catastrophic or irreversible, each with a latest-finish turn:
   - FEED any animal with consecutive_unfed = 1 (a second unfed day means escape: 300 to 500 coins of animal lost plus its output).
   - WATER any crop whose miss tonight creates weeds or kills a one-shot harvest window.
   - HARVEST anything capping or decaying tonight; the day-29 final harvest and shed run.
   Mandatory unit-turns = actions + travel, estimated from yesterday's route lengths per zone.
2. Productive load: every discretionary task valued in coins per unit-turn (care bank, extra harvest units, planting that pays within the season, fertiliser applications, collection).
3. Hire rule: add hand n while (value of the best unassigned productive work it can do today) > wage(n), and always enough hands that mandatory load fits with a slack reserve (C: 15% of mandatory turns, because travel estimates are noisy). Stop hiring when the marginal hand's value falls below its Fibonacci wage.
4. (C) Capacity sets the production plan, not the other way round: animal purchases, land and plantings are only approved if tomorrow's mandatory load still fits in the crew the ladder can afford. This is the exact failure measured in Peter's controller (buys 4 cows and builds pastures on wheat land on day 14, then cannot keep the wheat rotation).

## Layer 2: deadline-aware task scheduler (each turn, horizon to midnight)

1. Every task carries: value, duration, tile, earliest start, latest start (deadline minus travel from the assigned worker).
2. Mandatory tasks are scheduled by least slack first (slack = latest start minus now minus travel); anything with slack under 2 turns preempts.
3. Remaining capacity takes productive tasks by value density (coins per unit-turn including travel), inserted into routes where they fit (C: cheapest-insertion, the standard vehicle-routing-with-time-windows heuristic from the tomato-distribution paper Stephane read).
4. Replant rule (C): a harvested wheat or carrot tile is replanted by the worker that harvested it, same visit, if seeds are in hand; seeds are bought the turn before by the market layer. This is what gives W3 its steady 6 to 11 wheat plantings a day.

## Layer 3: route commitment and batching

1. (C) Stable zones: each worker owns a contiguous zone that changes only when the farm changes (new land, new herd). W3's tape effectively has fixed territories; the controller's re-cut wedges are part of its walking cost.
2. At dawn and whenever a route empties, a worker's route is built for the rest of the day: an ordered tile list from its zone, cheapest insertion then a 2-opt pass. Each tile visit batches every task there (water, harvest, replant, fertilise, care, collect).
3. Commitment: a worker follows its route until it ends; it deviates only for a mandatory task whose slack would otherwise go negative, or a race harvest the dump predictor flags.
4. Carrying: a worker picks up the wheat and fertiliser its route will use at the start, once.

## Gates

1. Envelope on 3 seeds: every game DONE, max turn under 500 ms, zero escapes, moves per useful action at or below W3's (1,828 moves for about 2,000 actions in days 14 to 29 on seed 902).
2. Day-14 identical-board test (8 seeds): better than Peter's -17,411; target -8,000 or better.
3. Full game from the handover at step 192: at least 16 of 32 against W6.
4. Band panel at or above W6's 0.667; ranks 7 to 12 panel at or above W3's 3 of 31.

## Plan

Build in /home/claude/bt/wantam/ as a new module that replaces WB_Controller._execute and the hire decision in _dawn, keeping _WB_View, _step_toward and the market layer. Layer 3 first (routes and batching, measurable on its own at the day-14 test with Peter's plan), then Layer 2 (deadlines and replant), then Layer 1 (capacity and plan gating).
