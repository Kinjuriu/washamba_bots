# Sonnet prompt, Sunday 27 September 2026 (evening): how the top 12 schedule labour

Run in VS Code from `~/KagricultureLocalData` with the .venv313 environment. Read-only analysis: no submissions, no git, no edits to agents. Stream replays one at a time (the Mac is short of RAM). Label every number MEASURED (with n) or INFERENCE.

```
Goal: measure how the top-12 agents run their workers, so Claude can build WANTAM's scheduler
(review_claude/WANTAM_SPEC.md) from their behaviour instead of guessing. Use the fresh corpus
episodes/20260927T124109Z_top12_strat/ (347 replays). For contrast, run the same measures on our
own seats in episodes/20260924T161358Z_washamba_0924b/replays (W3 = player file main.py /
w3_herdsafe2700.py; take 30 games).

Replay convention: steps[t][seat]['action'] was chosen from steps[t-1]'s observation. Both seats'
private state is in the replay. Units are the farmer plus the hired hands (action['farmer'],
action['hands'][k]); work out each unit's position turn by turn from the observation (read the
engine, kaggle_environments/envs/kaggriculture/kaggriculture.py, for where unit positions live and
how MOVE, WATER, HARVEST, PLANT, FEED, CARE, PICKUP, DROP, COLLECT_FERTILIZER, FERTILIZE work).
Check your position tracking on 2 games by confirming every non-move action happens on a tile
where it is legal.

For each team (and for W3), report medians with IQR over games, split by phase (days 0-7,
8-14, 15-22, 23-29) where it matters:

1. Capacity: hands held per day and per hour; when hires happen (hour of day) and when hands are
   let go; hands vs animals and vs planted tiles that day. Does crew size jump before known peaks
   (land purchase days, planting days)?
2. Zones: for each hand, the set of tiles it acts on per day. Measure zone stability (Jaccard
   overlap of a hand's tiles between consecutive days), zone size, and whether hands specialise
   (share of a hand's actions on animals vs crops; herders vs crop workers).
3. Routes and batching: per tile visit (arrival to departure), actions per visit and which action
   combinations occur together (for example WATER+HARVEST+PLANT); moves between visits; moves per
   useful action per day; share of turns idle (PASS or no action).
4. Deadlines: for animals, the hour of day FEED and CARE happen, and the minimum slack left before
   an escape (consecutive_unfed); escapes per game. For crops, the hour WATER happens and whether
   any crop ever reaches a weed/unwatered penalty. Which tasks are done early in the day and which
   are left late.
5. Replanting: steps from a HARVEST of wheat/carrot/tomato/strawberry to the next PLANT on the same
   tile; share replanted by the same hand in the same visit; plantings per day by crop.
6. Carrying: PICKUP of WHEAT and FERTILIZER per hand per day, quantity per pickup, hour; whether a
   hand fetches once at dawn or repeatedly.
7. Order within a day: for each hand, the sequence of task types over the day (compress to a
   pattern like FEED,FEED,CARE,...,WATER,...,HARVEST); report the most common daily patterns.
8. Anything that looks like a fixed rule (for example "all animals fed before hour 6", "every
   harvested wheat tile replanted within 2 steps", "hires only at hour 0").

Then write episodes/20260927T124109Z_top12_strat/SCHEDULER_INFERENCE.md (under 2,000 words):
- one table per section above, top-12 teams (grouped by opening family: DSM, Boey, other) vs W3;
- the 10 clearest scheduling rules the top teams follow and W3 does not, each with the evidence;
- a short "parameters for WANTAM" list: numbers Claude can plug in (crew by day, zone size, visit
  batching, feed/water hours, replant latency, pickup pattern).
Keep the analysis scripts under analysis/scheduler/. Do not download anything.
```
