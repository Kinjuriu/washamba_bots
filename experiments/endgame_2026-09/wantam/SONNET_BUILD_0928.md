# Sonnet build task, 28 September: WANTAM v2, a value-aware deadline scheduler

Run in VS Code in ~/KagricultureLocalData/wantam. Do not upload anything to Kaggle; Stephane
uploads, and only after she has seen your REPORT. The Mac is short of RAM: use 2 worker
processes at most, stream files instead of loading many replays at once, and back off
60 s on any HTTP 429.

Do Part A of SONNET_PROMPTS_0928.md (the tetsutani demand-preserving rebuild) first if it
has not been done; this task is Part B.

```
READ FIRST (all in ~/KagricultureLocalData/wantam):
  wantam.py        WANTAM dawn planner (WantamController, subclass of controller.WB_Controller)
  controller.py    Peter's splice executor (tasks, routing, market) that WANTAM uses now
  price_model.py, sell_engine.py, dump_predictor.py, value_model.py   splice modules
  build_wantam.py  builds one submission file: W3 to step 336, then WantamController
  match.py         full games, both seats:  python3 match.py A.py B.py 900,901,... 2
  h14.py, gates.py throughput gates and the day-14 identical-board harness
  PROGRESS_2026-09-28.md and ../episodes/20260927T124109Z_top12_strat/SCHEDULER_INFERENCE.md

WHAT WE MEASURED (so you do not repeat it):
  - wantam_h336.py (W3 to day 14, WANTAM after) vs W6, 16 seeds 900-915 x both seats:
    2-30, mean margin -10,639 (match_wantam_h336_w6_herdsafe_frontrun.json).
  - Split against W3 self-play on the same seeds: our own bank is only -2,952 lower,
    but the rival's bank is +7,687 higher. WANTAM's post-day-14 play hands the rival
    money: it starves animals and plants less of contested goods, so the rival sells
    into a thinner market at higher prices. The day-14 harness (h14.py) reported our
    own bank against W3's and missed that. The ladder scores the margin, not our bank.
  - Things that lost, do not retry: WantamExec executor v1 (-10,680 on 16 seeds),
    a wheat floor of 1.2 per animal, a current-price starve gate, land purchases,
    no mid-day drops, no maintenance watering.

THE METRIC FOR EVERYTHING BELOW:
  Head-to-head full games with match.py, 16 seeds 900-915, both seats (32 games),
  report W-L-T, mean margin (our bank minus rival bank in the same game), and the split
  (our bank minus W3 self-play bank, rival bank minus W3 self-play bank; W3 self-play
  banks are in ref_336_w3_herdsafe2700.py.json). Run against w3_herdsafe2700.py and
  against ../submissions/w6_herdsafe_frontrun.py. A candidate is worth an upload only
  if it wins at least 20 of 32 against both, with a positive mean margin.

STEP 1: make the planner's objective the margin, not our revenue.
  In WantamController._dawn, every choice (crop allocation, each starve decision) is
  scored by our revenue delta from _simulate. Change the score to
      our revenue delta - rival revenue delta
  using the same forward simulation (it already carries the rival's supply per product;
  add the rival's revenue as an output). Consequences to check in the logs: fewer
  starved animals (an animal's milk or wool also keeps the rival's price down), and
  crops chosen where the rival sells too. Test with match.py vs W3 (32 games). Report.

STEP 2: replace the executor with a value-aware deadline scheduler (routing inside it).
  Keep WANTAM's dawn plan (the strategic part, once per day). Replace the intraday task
  choice with a score per task j, computed each turn for each unit:
      Score_j = (ValueProtected_j + ExpectedMarginalRevenue_j + ScarcityPremium_j)
                / (Travel_j + Actions_j) * Urgency_j
  ValueProtected_j: what is lost if the task is missed before its deadline (a plant that
    weeds tonight loses its remaining forecast revenue; an animal that escapes loses its
    KeepValue = expected future output value minus expected feed, care and labour cost,
    valued with the dawn forecast, never today's price alone).
  ExpectedMarginalRevenue_j: forecast value of the unit this task produces, at the sale
    day the dawn plan assigns, including the rival effect from Step 1.
  ScarcityPremium_j: extra value when the product's market sits below its I0 hinge
    (tomato, carrot late in the season), taken from the dawn simulation.
  Travel_j: Manhattan steps from the unit's tile. Actions_j: turns to do it.
  Urgency_j: rises as hours left today approach the travel plus action time needed
    before the deadline (the trap door), 1.0 when there is slack.
  Assign units to tasks greedily by score, one unit per task; only then order each
  unit's committed tasks to minimise walking, and batch actions on a tile (a unit on a
  tile does every due action there before moving). Economic ranking first, routing
  second, never the other way round.
  The heavy work stays at dawn; the per-turn scoring must stay under 100 ms.
  Gates to print with gates.py alongside the money (money decides; gates only explain):
  actions per visit near 2, moves per useful action 0.60-0.71 on days 15-22, idle 1-3%
  after day 8, wheat replanting at least 4.6 per day through days 23-29, zero unintended
  escapes (starving a planned animal is allowed and must appear in starve_log).

STEP 3: if a Step 1 or Step 2 build clears the upload bar at handover 336, rebuild with
  H_STEP=192 (day 8) and test again. If Part A produced agents/dp/w3_dp_rebuild.py and
  it beats W3, use it as the base instead (python3 build_wantam.py <base> <out>).

BUILD AND CHECK every candidate with build_wantam.py, then: seed-0 self-play finishes
  DONE/DONE, the last callable in the file is washamba_agent, max turn under 500 ms.

REPORT in ~/KagricultureLocalData/wantam/REPORT_0928.md: a results table per build
(W-L-T and margin vs W3 and vs W6, the own/rival split), what changed, and one line
per result saying MEASURED (file, sample size) or INFERENCE. Plain English, no em dashes.
Stop rule: if nothing clears the bar by Tuesday 29 September 12:00 Nairobi, say so;
the final pair then stays W3 + demand-preserving (Peter's) and W6.
```
