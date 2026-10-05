# Fable round 3: test production changes on the existing executor (overnight run)

Stephane is asleep. Your job tonight is to **build and test** experiments B, C and D below, and write one report she can read in the morning. Same safety rules as before, with one change: you may now create agent variants and run games.

## Rules

- Work only under `~/KagricultureLocalData/experiments_r3/` (create it). Do not edit anything else, do not submit to Kaggle, do not touch git.
- **Save API credits.** The games run on the Mac's CPU and cost nothing; your tokens do. Write each experiment as a script that runs its whole batch in the background (`nohup ... &`) and writes a summary file. Then check back with long sleeps (`sleep 900`) instead of watching logs. Don't print raw game logs into the conversation.
- Use `python` from the environment that has `kaggle-environments==1.32.7` (check with `importlib.metadata.version`). Use (CPU cores - 1) workers.
- Label every claim **measured** or **inference**. Report win-loss-tie, mean and median margin, and sample size.

## What has already been tested (don't repeat)

- W0 = public v15stack, unchanged (`submissions/w0_v15stack_control.py`, ladder 2,424). W1 = W0 with `V9_RACE_DEFAULT` 40 to 44 (ladder 2,018, still young).
- **Selling-only changes are ruled out.** Claude's W2 selling planner (`agents/w2/`) went 1-19 against W0 in mirrors, and +252 mean on the top-six panel. A "never sell less than the tape" version went 5-15.
- **Keeping geese by disabling v15stack's herd swaps**: no change on the top-six panel.
- **Top-six games as v15stack routes**: fail on new seeds.
- **Experiment A (75-tile cap) fails.** Blocking the third quadrant: 0-10-30 against W0 in mirrors (ties where the tape would not buy it; losses of 8,700 to 36,000 where it would) and -1,038 mean on the faithful top-six panel (34 games). v15stack's routes use that land, so capping it only removes capacity. Don't retest A.
- **Claude is testing a cheap version of D tonight:** v15stack's carrot switch threshold `V9_CARROT_RATIO` 1.8 to 1.4 (and the same with `V9_CARROT_LAST_DAY` 23 to 26). Build your D as the real per-tile reactive version.

## Tools (all under `~/KagricultureLocalData/harness/`)

- `pool_harness.py`: paired games, both seats, win/loss/tie. Example:
  `python harness/pool_harness.py --agent w0=submissions/w0_v15stack_control.py --agent X=experiments_r3/X/main.py --candidates X --opponents w0 --seeds 2001-2030 --workers 7 --out experiments_r3/X_mirror.jsonl`
- `top6panel.py` + `tapeopp.py`: plays a candidate against recorded top-six games on their original seeds. Build `harness/top6_panel_faithful.json` by keeping only the entries of `top6_panel.json` whose episode id is in `faithful_eps.json`, and run on that file (edit a copy of `top6panel.py` to read it). **Only compare two candidates on games where the replayed top-six bank stays within 5% of its original under both candidates** (`tape_bank` vs `orig_tape_bank`). W0's result on those 38 games: 6 wins, median -21,744 (`harness/top6_panel_results.jsonl`, rows with cand `w0`).
- `diag_products.py`: plays one game and prints units, revenue and average price per product for both sides; copy it into your folder and point it at your variant paths.
- `resim_trades.py`: re-simulates a ladder replay and logs every traded unit.

## How to build a variant (important)

Append a wrapper to a copy of `submissions/w0_v15stack_control.py`. Kaggle calls the **last callable defined in the file**, so the wrapper must be the last function. Pattern:

```python
_X_PARENT = v15_submission_entry
def x_agent(observation, configuration=None):
    action = _X_PARENT(observation, configuration)
    # modify `action` (a dict with "farmer", "hands", "market") here; never raise
    return action
```

Every variant needs a switch; **with the switch off, it must produce banks identical to W0** on 3 seeds. Check that first. v15stack has many layers inside; some decisions (for example herd species) are made by constants you can find with `grep -n "^V9_\|^_HD2_" main.py`.

## Experiments

**B. CARE deduplication.** W0 issues 1.04 CARE actions per animal per day; the engine banks at most one useful CARE per animal per day. First measure it: in 5 of W0's own games (replays in `episodes/20260923T161855Z_washamba_vs_top6/replays/`, player `w0_v15stack_control.py`), count CARE actions that actually changed `pending_care_bonus` (successful) versus no-ops. If no-ops are real, build a variant that replaces a duplicate CARE with the most valuable other task available to that worker that turn (water a thirsty plant, feed, harvest a ripe tile, collect fertilizer). Count successful actions before and after, not orders issued.

**C. More geese.** Confirm W0's goose count per day from its replays. Then build two variants that add geese up to about 5 in total: C1 after day 8, C2 before day 8. Each needs a coop tile, wheat for feed and labour. Gate every purchase on cash (never below the next day's tape purchases), free tiles, wheat stock and shed space. Keep everything else unchanged. Check that the geese survive (count escapes) and that eggs are actually sold.

**D. Limited reactive crop choice.** Keep the opening and the executor. From day 10, when the tape plants a crop on a tile, allow the variant to plant a different crop instead, on a limited number of tiles (start with 4, then 8). Choose by expected marginal profit per tile-day: the engine price at the market stock expected at harvest, yield, days to harvest, labour and feed. Shift away from products the market is over-supplied with, toward eggs, carrots, wheat and tomatoes, but only when the numbers say so. Seeds must be bought the turn before planting (the one-turn pipeline) and new plantings watered the same day.

**E. Combine** only the changes that passed, into one variant.

## Gate for every variant

1. Switch-off identity check passes.
2. Mirror vs W0, seeds 2001-2030, both seats (60 games): points share of at least 0.5 (a tie counts as half).
3. Faithful top-six panel: mean paired margin better than W0 on the faithful-under-both games.
4. No game ends with a status other than DONE, and no turn over 1 second on average.

A variant that improves the top-six panel by more than 2,000 on average but loses the mirror is still worth reporting: say so clearly.

## Report

Write `~/KagricultureLocalData/FABLE_ROUND3_REPORT.md`, under 1,500 words:
- one line per variant: what it changed, the mirror result, the panel result, pass or fail;
- the measured evidence for B and C (CARE no-ops, goose counts, escapes, eggs sold);
- which change, if any, should be combined next, and what you would test after that.
