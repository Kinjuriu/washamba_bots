# Sonnet task, 29 September night: final scan for anything stronger than Step1009

Run in VS Code in ~/KagricultureLocalData with .venv313/bin/python. Read-only on Kaggle: do not
submit anything. Few calls, back off 60 s on HTTP 429, 2 workers at most (RAM). Do the parts in order
and write each part's note as soon as it is done.

```
PART A: newest public agents (the scan that found Step1009 last time)
1. kaggle kernels list --competition kaggriculture --sort-by dateRun --page-size 100 --page 1
   (and pages 2-3). Keep kernels last run after 2026-09-27 00:00 UTC; also keep every
   tetsutani kernel regardless of date. Save the table as public_notebooks/scan_0929/kernels.csv
   (ref, title, author, lastRunTime, totalVotes).
2. Pull each kept kernel (kaggle kernels pull <ref> -p public_notebooks/scan_0929/<slug> -m).
   Extract the agent: plain code cells concatenated into main.py, or the embedded archive decoded
   the same way as public_notebooks/tetsutani/extract_archive.py. If auto mode blocks a tar
   extraction, do NOT add a permission rule; just list the .ipynb path.
3. For each extracted main.py: sha256, self-play seed 0 status, name of the last callable,
   max turn duration. Skip any file with network calls or subprocess use.
4. Write public_notebooks/scan_0929/INDEX.md: one row per kernel (ref, date, votes, extracted?,
   sha256 first 16, self-play status, whether sha256 = 55be5d5f124c8daa which is Step1009).
   Tell Stephane when INDEX.md is saved; Claude will test the candidates.

PART B: recent ladder games
5. For our two active submissions (nikaangukia_meroni.py and tetsu_step1009_full.py), list all
   episodes since 2026-09-28 18:30 UTC into episodes/20260929_final/episodes.csv (same columns as
   episodes/20260928_ladder_check/episodes.csv) and download every replay (gzip) to
   episodes/20260929_final/replays/.
6. From the current leaderboard, for teams ranked 1-20, download the 5 most recent completed
   episodes each into episodes/20260929_final/top20/, with a manifest.csv (team, rank, rating,
   episode_id, seat, won, opp_team, opp_rating).
7. Write episodes/20260929_final/SUMMARY.md (under 30 lines): W-L-T and mean opponent rating per
   submission of ours, and any non-DONE statuses.
```
