# Sonnet task, 28 September night: pull the ladder episodes of our three recent submissions

Run in VS Code in ~/KagricultureLocalData. Read-only on Kaggle: do not submit anything.
Few calls, back off 60 s on HTTP 429, stream files, 2 workers at most. Reuse
episodes/_scratch_pyfetch/ (download_top12_strat.py, classify_our_subs.py) for the API calls.

```
1. kaggle competitions submissions kaggriculture  -> note the submission ids of
   tetsu_step1009_full.py (Stephane, ~20:20 Nairobi 28 Sep) and both w3_dp_saletiming.py
   uploads by Peter ("Final pair A", "Final pair B").
2. For each of the three submissions, list every completed episode so far and write
   episodes/20260928_ladder_check/episodes.csv with: submission, episode_id, end_time, seat,
   our_bank, opp_bank, margin, won, opp_team, opp_submission, opp_rating_at_the_time (as the
   API gives it), and any agent status other than DONE (ERROR, TIMEOUT, INVALID).
3. Download the replay JSON (gzip it) for every Step1009 episode into
   episodes/20260928_ladder_check/replays/, and for Peter's two only the losses.
4. Write episodes/20260928_ladder_check/SUMMARY.md (under 40 lines): per submission, episode
   count, W-L-T, mean margin, mean and range of opponent rating, rating now, and a list of every
   Step1009 loss with opponent name, rating, margin and seat. Flag any non-DONE status first.
Tell Stephane when the replays are saved; Claude will analyse them.
```
