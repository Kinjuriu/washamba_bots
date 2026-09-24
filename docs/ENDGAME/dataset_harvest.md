# Dataset harvest — farm2945 loss/win set + top-current panel gaps (2026-09-21)

Task: enlarge (A) submission `56269928` ("2945 Farm", Thomas Tschinkel)
losses vs 3,000+-rated opponents and wins vs 2,700+-rated opponents, and
(B) episode coverage for Otter Vibe, THIRD FARM CLUB, KawattaTaido, Unknown
Mother-Goose, ymg_aq, SpaTaro's *current* submissions — using only Kaggle
datasets, zero new `ListEpisodes` calls. Builds on `docs/ENDGAME/copyability.md`.

## What each dataset actually contains

**`kaggle/kaggriculture-episodes-index`** (`manifest.csv`, 8 KB) — a
per-day pointer table only: date, the daily dataset's slug/URL, episode
count, byte size, and that day's top/median score. No episode-level data.
Covers 2026-07-30 through 2026-09-20 (54 rows), refreshed daily. Used only
to confirm the daily datasets exist; not queried further.

**`kaggle/kaggriculture-episodes-YYYY-MM-DD`** — not used this session
(large, unindexed; the two datasets below cover the same ground with a
manifest in front of it). Spot-checked one day's file listing only:
`kaggriculture-episodes-2026-09-20` holds individually-named
`<episodeId>.json` files (~33 MB raw each), presumably a subset of that
day's ~650-900 total episodes (unconfirmed how the subset is chosen — no
manifest inside this dataset itself).

**`ashok205/kaggriculture-top10-replay-archive`** (CC0) — the one that did
the real work. Two layers: (1) `episodes.parquet` (2 MB, all days,
33,789 rows) — one row per (day, top-10-that-day team, episode), with
`team_name`, `opponent` (a name string, not an id), `daily_rank`,
`daily_score_proxy` (that team's rating snapshot for the day — verified
against `ListEpisodes`-sourced `initialScore` on 9 episodes, agrees to
within ~0.1%), but **no submission id and no per-episode reward**; (2)
per-day `replays_YYYY-MM-DD.parquet` shards (30-110 MB, growing over the
season), each `episode_id` + the full raw replay JSON text exactly as the
episode CDN serves it. Coverage is "any episode where a top-10-that-day
team appears, on either side" — so a team that was *never* top-10 (like
Tschinkel/"2945 Farm", or KawattaTaido before this week) still shows up
whenever it played a team that *was* top-10 that day, via the `opponent`
column. Freshness: processed through 2026-09-19; nothing for 09-20 or later,
and no coverage at all before a team's *first* top-10 appearance, so
KawattaTaido and Vadim Vasilenko (both newly top-10 this week) are absent
throughout, confirmed by grep (0 rows). Downloaded 4 shards (09-13 through
09-16, ~416 MB) plus 5 more (08-14 through 08-18, ~270 MB, explored then
set aside — see caveat below) for a total ~700 MB.

**`georgymamarin/kaggriculture-episodes`** (22.9 GB total; **only the small
manifest CSVs were downloaded, ~103 MB, never a replay shard**) — a
crawler-built corpus with `episodes.csv`/`agents.csv` (submission id +
reward + rating per episode/seat, no team names) and `teams.csv` (id →
name, leaderboard-snapshot). Its own README states coverage is
priority-weighted toward the "freshest third" of submissions and thins
sharply elsewhere (median submission: 2 episodes). Checked directly:
**zero rows for submission `56269928` and zero for `56417128`** in
`agents.csv`, and both teams are absent from a `56417128`/`56269928` grep
— confirms this corpus simply hasn't crawled either team, not a matching
bug. Not useful for either gap; the small manifests were enough to
establish that without touching a replay shard.

## Part A: farm2945_losses / farm2945_wins (submission `56269928`)

**A critical finding first, because it shapes everything below.** The
`ashok205` archive's `opponent` column has no submission id, only a team
*name*. Cross-referencing the 14 accumulated `episodes_*.json`
`ListEpisodes` dumps already cached in this repo (from this session's
earlier work) against `teamId == 16719123` (Thomas Tschinkel) shows the
team has run **5 different submissions this month** (56222223, 56237702,
56246133, 56258845, then 56269928), and the transition to the current one
(`56269928`) is bracketed precisely: its earliest confirmed episode is
`109666520` and the last confirmed episode of the prior submission
(`56258845`) is `109687967` — both dated **2026-09-16**. So team-name
matches dated 2026-09-16 or later are the current submission with high
confidence; matches dated 2026-09-13 through 09-15 are very likely an
**older** submission and were excluded rather than mislabeled.

- **Losses vs ≥3,000-rated opponents: 4 → 14** (want 15, short by 1).
  The 4 original entries are unchanged. Added **10** new episodes, all
  dated 2026-09-16 and rating-filtered ≥3,000 from the archive's 12
  same-day Tschinkel-as-opponent rows (2 of the 12 were the already-known
  duplicates `109694364`/`109821873`). These 10 are team-name-matched, not
  individually `ListEpisodes`-confirmed as `56269928` — flagged
  `"verification"` in `panel/index.json` accordingly. The 28 Sep 13-15
  matches (would have been "found" easily) were deliberately **not** added
  for the reason above.
- **Wins vs ≥2,700-rated opponents: 0 → 2** (want 8, short by 6). Both are
  individually `ListEpisodes`-verified as `56269928` (episodes `109773242`
  vs `mikelou1`, rating 2949.5; `109856068` vs Orbital Terraformer, rating
  3006.0) — these were already sitting in the panel as `top_current`
  entries from earlier work and just needed the `farm2945_wins` label
  added. No further wins exist in the verified-submission window; the
  archive has zero win rows dated 2026-09-16, and the Sep 13-15 wins found
  (3 of them) are excluded for the same submission-uncertainty reason as
  above.

The Aug 14-18 window (848 team-name rows, the bulk of what exists for
"Thomas Tschinkel" in the archive) was downloaded and inspected but **not
used at all** — it's a different, much older submission era (predates all
5 submissions seen in the `ListEpisodes` cross-reference), matching
`copyability.md`'s own caution about that window being stale.

## Part B: top-current panel

Filled entirely from the same 14 cached `episodes_*.json` dumps
(teamId × submissionId crosstab), zero new downloads needed beyond
2 individual replay pulls (`replay_tools.download`, ~62 MB):

| team | current sub | episodes now in panel |
|---|---:|---:|
| Otter Vibe | 56328447 | **7** (already sufficient) |
| SpaTaro | 56384319 | **3** |
| ymg_aq | 56393666 | **3** (added all 3) |
| THIRD FARM CLUB | 56372014 | **3** (added 1) |
| Unknown Mother-Goose | 56417993 | **1** (genuinely all that exists) |
| Unknown Mother-Goose | 56401905 (next-most-recent) | 3 (added for context; not the sub confirmed current in `copyability.md`) |
| KawattaTaido | 56417128 | **1** (genuinely all that exists anywhere) |

KawattaTaido and Unknown Mother-Goose's confirmed-current sub remain
short. Checked exhaustively: scanned the full `experiments/endgame/rep/`
cache (now ~6.8 GB, 300+ files) by team name and cross-referenced all 14
`episodes_*.json` dumps by `teamId`+`submissionId` — KawattaTaido appears
**exactly once** anywhere in any dataset or cache touched this session
(consistent with `copyability.md`'s "unreached" verdict and with its
absence from both the `ashok205` and `georgymamarin` corpora). Unknown
Mother-Goose resubmits ~12×/week, so its true "current" sub is a moving
target; sub `56417993` (the one `copyability.md` identified as current as
of Sep 21) has only the 1 known episode.

## Remaining gap for Peter

Paste into `experiments/endgame/top10_episodes.txt` (recent completed
episode ids):

1. **Submission `56269928`** (or whatever succeeds it) — need ~7 more
   losses vs 3,000+ opponents and ~6 more wins vs 2,700+ opponents to hit
   15/8. The archive has nothing more to give past 2026-09-16; anything
   newer needs either a fresh `ListEpisodes(56269928)` call or pasted ids.
2. **KawattaTaido**, sub `56417128` — completely unreached across every
   dataset checked; needs ids directly.
3. **Unknown Mother-Goose**, current sub (confirm via leaderboard which one
   is live right now — it changes fast) — only 1 episode on the
   `copyability.md`-identified current sub.

## Cache and budget

New downloads this session: ~700 MB (`ashok205` shards, including the
270 MB Aug 14-18 set that ended up unused) + ~103 MB (`georgymamarin`
manifests) + ~62 MB (2 individual episode pulls) ≈ **865 MB**, inside the
~4 GB budget. Total `experiments/endgame/` cache: `rep/` 6.8 GB, `panel/`
43 MB, `kaggle_ds/` 693 MB — 7.5 GB combined, under the ~15 GB ceiling, no
deletion needed. All gitignored already (`rep/`, `panel/`; `kaggle_ds/` is
not explicitly listed — same pre-existing gap `copyability.md` already
noted and left alone, per instructions not to touch `.gitignore`).
