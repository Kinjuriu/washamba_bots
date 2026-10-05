# Kaggriculture Episodes

Episode replays and results from the [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture)
simulation competition, collected from Kaggle's public episode API. One episode is one 720-turn
farming game (a turn is an in-game hour, a game is a 30-day season). A scheduled Kaggle notebook
refreshes this daily.

## Files

- `episodes.csv`: one row per episode: `episode_id`, `create_time`/`end_time`, `state`,
  `type` (`EPISODE_TYPE_PUBLIC` = ladder game, `EPISODE_TYPE_VALIDATION` = self-play check;
  filter those out for strength analysis), and per seat: `sub_N`, `team_N`, `bank_N`
  (final coins, the game score), `rating_N` (skill rating right after the game).
- `agents.csv`: the per-agent view: `episode_id`, `agent_index`, `submission_id`, `team_id`,
  `final_bank`, `rating_after`.
- `replays_2026-*.parquet`: full replays in monthly shards (a frozen month never changes,
  which keeps the nightly rebuild cheap): `episode_id` plus `replay_json`,
  the replay exactly as the episode CDN serves it (`steps` for 720 turns, `rewards`, engine
  `configuration`). Each `steps[t][seat]` holds that seat's `observation` and `action`.
  Zstd compresses the raw JSON about 236x (measured off the parquet's own column metadata;
  mean replay: 28 MB). Sizes grow with the ladder, so read them off the Data tab. Read all
  shards at once: `pyarrow.dataset(sorted(glob(f"{base}/replays_*.parquet")))`.
- `teams.csv`: `team_id`, `team_name`, `ladder_score`, `last_submission`: the join that puts
  readable names on charts (episode rows carry ids only). It is a leaderboard snapshot, so it
  names about half the teams that appear in the episodes; the rest have dropped off the board.
- `episode_features.csv`: one row per (episode, seat), parsed out of every replay so you don't
  have to: `engine_version` (the replay's own `module_version`, so balance patches split
  cleanly: the ladder cut over to 1.32.7 on Aug 15, 01:38-01:41 UTC), `peak_crew`, `total_hires`, `first_land_day`, `tiles_planted`, `plants_<crop>` per
  crop, and `price_<product>_min`/`_max` for the episode's shared market. Hires are read from
  farm state (`hires_today`), not submitted orders, because the engine rejects orders once
  money runs short. Two columns come from the outcome itself: `final_money` is identical to
  `bank_N`, and `elbow_day` (first day the bank crosses 10% of its final value) is derived
  from it. Keep both out of any feature set.
- `daily_stats.csv`: one row per UTC day: ladder games, active teams, median/p90/record
  winner's bank, and `replay_coverage`. That column is the share of the games *stored here*
  that day that have a replay, not the share of the ladder's games that day.
- `stream_hashes.csv`: one row per (episode, seat): sha256 over that seat's action stream.
  Use prefixes for lineage: the full-game hash (`stream_h719`) has ~one distinct value per
  seat-game, so it identifies the episode rather than the agent (measured by destbreso).
  Details: sha256 over that seat's action stream,
  cut at turns 24, 48, 100, 136, 200, 300, 400 and 719 (48 and 136 are the engine's
  information horizons, measured by destbreso), first 16 hex characters each, plus `turns` so an
  empty cell reads as "the episode ended before that turn" rather than as missing data.
  Two seats with the same value at turn N submitted identical actions through turn N, which
  makes "these agents run the same line" an observation instead of a distance threshold.
  Suggested by destbreso in the dataset discussion, along with this exact normalisation.
  Every stored episode has its row, all eight cuts filled (backfill completed 2026-08-28).
- `per_submission_coverage.csv`: episodes indexed vs stored per submission id, with their
  ratio. This is the exact reweighting factor for the corpus's submission bias, which used
  to be estimable only from outside.
- `state.json`: crawler state, including when each submission was last crawled. Updates are
  incremental because of it.
- `scrape.py`, `repack.py`, `teams.py`, `features.py`: the collector chain. Everything here
  reproduces from public endpoints.

## How complete is this?

Coverage is per submission, not per day. Every run crawls the freshest third of the known
submissions and rotates through the rest under a time budget, so a few hundred submissions
have near-complete histories while everyone else contributes a few percent of their games.
The thinning is priority-based, not a uniform lag: two submissions that played in the same
hour can sit at 100% and at 1%. Measured against the episode API on 2026-08-13: a seat from the 300 submissions with the
most rows here appears in 97% of everything stored (94% at a cut of 250, 98% at 400, so the
cut is a choice), and the twelve of those sampled hold 87-99.8% of their own games, while the
median submission appears in two episodes, drawn in as somebody else's opponent. Read daily totals as that sample rather than the ladder's true volume.
Every episode stored here does have its replay, which is what `replay_coverage` measures.

To weight by coverage today, compare per-`sub_N` counts in `episodes.csv` against what
`ListEpisodes` returns for that submission id; `scrape.py` shows the call.

## Rights

The games belong to their players and to Kaggle; this dataset only collects and reshapes
public episode data. Environment:
[kaggle-environments](https://github.com/Kaggle/kaggle-environments).
