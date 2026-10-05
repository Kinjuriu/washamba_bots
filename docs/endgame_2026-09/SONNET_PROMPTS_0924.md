# Sonnet prompts, Thursday 24 September 2026

Run in VS Code from `~/KagricultureLocalData`. Both are download and analysis only: no submissions, no git pushes, no edits to existing agents.

---

## Prompt 1: the 2,900 band (leaderboard ranks 7 to 12) compared with the top six

```
Download and analyse the current leaderboard ranks 7 to 12, and compare them with the existing
top-six corpus. Read-only research; do not submit anything.

1. Resolve ranks 7 to 12 from the live leaderboard at run time, with each team's currently active
   submission (same method as episodes/20260923T153431Z_top6/: leaderboard CSV cross-checked against
   ListEpisodes' publicLeaderboardSubmissionId). Record the snapshot time and ratings.
2. For each team, take up to 60 of the most recent completed public episodes (exclude the validation
   episode). Write manifest.csv to disk before any download, then download from the manifest only,
   into episodes/<UTC timestamp>_ranks7to12/, with the same validate-gzip-revalidate pipeline.
3. Classify every trajectory (both seats, all teams) by opening fingerprint, read from the action
   rows (the action at row t was chosen from the observation at row t-1):
   - "tape family": row-2 market orders contain ["BUY_ANIMAL","COW",2] and ["BUY_ANIMAL","SHEEP",2]
   - "DSM family": row-1 market orders == [["BUY_ANIMAL","COW",1],["BUY_PRODUCT","WHEAT",5]]
   - "Boey": row-1 starts with ["BUY_PRODUCT","WHEAT",3] followed by five HIREs
   - otherwise "other" (keep the exact row-1 and row-2 orders so new families can be grouped)
4. For each rank-7-to-12 team report: family, W-L-T, win rate against tape-family opponents and
   against non-tape opponents, median bank margin for each, and median final bank.
5. For 8 games per team (4 against tape-family opponents where available), run
   harness/resim_trades.py on the replay to get exact units and revenue per product for both sides.
   Also record, from the replays at days 6, 12, 18 and 26: animals by species, land tiles, crop tiles
   by crop, peak hands that day, and cash.
6. Write episodes/<timestamp>_ranks7to12/ranks7to12_report.md with:
   - a table with one row per team (ranks 1 to 12, using the existing top-six corpus for 1 to 6):
     family, record vs tape family, median margin, animals at day 12, and revenue per product;
   - the decisions that separate ranks 7-12 from ranks 1-6, and ranks 7-12 from the tape family,
     with sample sizes; mark each claim as measured or inference;
   - whether any rank-7-to-12 team is a tape agent with extra layers (the path from ~2,400 to
     ~2,900 would then be visible in its behaviour).
```

## Prompt 2: our own games since 23 September

```
Download every episode played so far by our three most recent submissions and analyse them.
Read-only research.

1. Submissions: w0_v15stack_control.py (56487592), w1_v15stack_race44.py (56491123) and Peter's
   washamba_base_v3.py (the newest, "public V57 verbatim"). Resolve IDs from the submissions list and
   check them against the file names. Include all episodes Kaggle exposes (paginate to the end);
   exclude validation episodes. Reuse replays already in
   episodes/20260923T161855Z_washamba_vs_top6/replays/ instead of downloading them again.
2. Save to episodes/<UTC timestamp>_washamba_0924/ with a frozen manifest, as before. Download our own
   agent logs too (the opponent's logs return 403; don't retry them).
3. For each submission report: W-L-T, rating trajectory, and results split by
   (a) opponent rating band (below 2,000, 2,000 to 2,500, 2,500 to 2,800, above 2,800) and
   (b) opponent family, using the fingerprints from Prompt 1 step 3.
4. For games against tape-family opponents, report how many ended as exact or near ties
   (|margin| < 500) and the median margin of the rest.
5. For every loss against an opponent rated above 2,500, run harness/resim_trades.py and list the
   products where we lost the most revenue.
6. Write episodes/<timestamp>_washamba_0924/washamba_0924_report.md, plain English, under 1,500
   words, with the tables above and a short list of the clearest patterns.
```
