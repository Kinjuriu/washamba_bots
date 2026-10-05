# Sonnet prompts, Sunday 27 September 2026

Run in VS Code from `~/KagricultureLocalData`. Download and analysis only: no submissions, no git pushes, no edits to agents. Use at most 2 parallel downloads and back off on HTTP 429; the Mac is short of RAM, so close nothing of Stephane's and keep memory use low (stream files, do not load a whole corpus into memory).

---

## Prompt A: fresh, stratified corpus of the current top 12 (30 games each)

```
Build a fresh corpus of the current leaderboard top 12, 30 games per team, stratified. Read-only.

1. Disk first: print `df -h .` and `du -sh episodes/*`. Delete
   episodes/20260923T161855Z_washamba_vs_top6/replays/ (superseded by the 0924b corpus; keep its
   reports and csv files). Do not delete anything else.
2. Resolve ranks 1 to 12 from the live leaderboard at run time, with each team's currently active
   submissions (same method as episodes/20260924T161358Z_ranks7to12/: leaderboard CSV cross-checked
   against ListTeamPublicSubmissions). Record the snapshot time and ratings. A team can have two
   active submissions; keep both IDs and sample from the one with the higher rating unless it has
   fewer than 30 completed episodes.
3. For each team, list all completed public episodes of that submission (exclude validation), then
   choose 30 by stratified sampling, not simply the most recent:
   - half with the team in seat 0 and half in seat 1 (as close as possible);
   - spread over the opponent's rating: about a third each below 2,500, 2,500 to 2,800, above 2,800,
     using the opponent's current leaderboard rating (fill from neighbouring strata if one is short);
   - spread over time: no more than 10 of the 30 from any single 6-hour window.
   Write manifest.csv with the stratum of every row BEFORE downloading, then download replays only
   (no agent logs) from the manifest into episodes/<UTC timestamp>_top12_strat/, with the same
   validate-gzip-revalidate pipeline as before. Reuse any replay already on disk instead of
   downloading it again.
4. Report in episodes/<timestamp>_top12_strat/README.md: the team table (rank, name, rating,
   submission ID, episodes available, episodes sampled per stratum), download errors, total MB.
   Do not analyse beyond that; Claude will do the analysis.
```

## Prompt B: results-only crawl for a local Bradley-Terry fit (no replays)

```
Collect episode RESULTS only (no replay files) to fit a local Bradley-Terry model. Read-only.

1. Seed set of submissions: every submission appearing in the manifests of
   episodes/20260924T161358Z_washamba_0924b/, episodes/20260924T161358Z_ranks7to12/ and the new
   *_top12_strat corpus (both sides of every game), plus our active submissions
   (w6_herdsafe_frontrun.py and Peter's w3_frontrun.py; resolve their IDs from our submissions list).
2. For each seed submission, page through ListEpisodes and record, for every completed public
   episode: episode_id, end_time, and for both seats: submission_id, team_id, team name, reward
   (final bank), status. One JSON line per episode into
   episodes/<UTC timestamp>_bt_crawl/episodes.jsonl; deduplicate by episode_id. Cap at 400 episodes per
   submission (most recent first). Do not download replays or logs.
3. Save the leaderboard CSV snapshot (all teams) next to it as leaderboard.csv.
4. Report: number of submissions, episodes, distinct teams, and file size. Stop when done; Claude
   will fit the model.
```
