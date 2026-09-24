# Public inventory — Kaggriculture, read 2026-09-21

Task T2 of `docs/superpowers/plans/2026-09-21-endgame.md`. Facts only; every row has a
command or file backing it. Kernel pulls cached at `experiments/endgame/kernels/<slug>/`
(gitignored, not committed). Raw listings at `experiments/endgame/kernels_by_date*.csv`
and `kernels_by_votes.csv`.

## needs_peter_download

Discussion pages are JS-rendered; `WebFetch` returns only the page shell (verified on the
discussion index itself). Peter should open these directly:

- `https://www.kaggle.com/competitions/kaggriculture/discussion?sort=recent-comments` — full thread list, unreadable via fetch.
- `https://www.kaggle.com/discussions/kaggriculture/733431` — "Balance Changes" (34 votes) — engine may change again before the freeze; check before trusting any mechanic table below.
- `https://www.kaggle.com/discussions/kaggriculture/731587` — "Comment on the final evaluation for this competition" (16 votes).
- `https://www.kaggle.com/discussions/kaggriculture/731215` — "Daily Top Episodes Dataset" (24 votes) — almost certainly the thread announcing the dataset family found below; worth reading for any stated freshness/coverage guarantee.
- `https://www.kaggle.com/discussions/kaggriculture/734684` — "Match outcome contradicts stated win condition (higher coin total reco[gnized as loss?])" (2 votes, title truncated by the renderer) — sounds like a scoring-rule report; check it's not something that invalidates our win/loss reading.
- `https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-index` discussion/comments (if any) — the dataset itself was pulled and is summarized below, but its own page may carry usage notes.

## Top finding: an official, rate-limit-free replay dataset family

`.venv/Scripts/kaggle.exe datasets list -s kaggriculture` (run 2026-09-21) surfaces a dataset
family neither the plan nor our prior notes mention:

| ref | size | updated | votes |
|---|---|---|---|
| `kaggle/kaggriculture-episodes-index` | 1.9 KB | 2026-09-21 | 29 |
| `kaggle/kaggriculture-episodes-2026-09-20` | ~21.5 GB | 2026-09-21 | 22 |
| `kaggle/kaggriculture-episodes-2026-09-19` .. `-07-30` | ~13–21.5 GB each, one per day | daily | 20–24 each |
| `georgymamarin/kaggriculture-episodes` (community mirror) | 22.9 GB | 2026-09-21 | 66 |
| `destbreso/kaggriculture-benchmark-matchups` | 492 MB | 2026-08-26 | 22 |
| `vijaikm/kaggriculture-match-replay-corpus` | 2.0 MB | 2026-08-22 | 10 |
| `raykkretzschmar/kaggriculture-reference-agents` | 153 KB | 2026-08-17 | 34 |
| `destbreso/kaggriculture-donor-agents-20260902` | 43.6 MB | 2026-09-20 | 21 |

Pulled and read `kaggle/kaggriculture-episodes-index/manifest.csv` (CC0-1.0, 54 rows, one per
day 2026-07-30 → 2026-09-20): columns `date, daily_dataset_slug, daily_dataset_url,
episode_count, total_bytes, top_avg_score, median_avg_score`. Each day's linked dataset
(`kaggle/kaggriculture-episodes-YYYY-MM-DD`) holds 639–928 full episode replay JSONs for that
day, published by Kaggle itself. `top_avg_score` climbed 1152 (7/30) → 3239.8 (9/20);
`median_avg_score` 670 → 3040 over the same window.

**Why this matters for T3/T4/T9:** those tasks are budgeted in single-digit-to-dozen
`ListEpisodes` API calls because that endpoint 429s after ~19 calls. This dataset delivers
full replay JSON for the *entire* top band, every day, via the ordinary Kaggle datasets
download path — no `ListEpisodes` calls at all. It looks like the correct source for T4's
top-10 copyability harvest and T9's final crawl, replacing (or heavily supplementing) the
budgeted `ListEpisodes` crawl the plan describes. Not yet integrated into any of our tooling.
`destbreso/kaggriculture-donor-agents-20260902` ("community agents and arena") was not pulled —
this harness's untrusted-code guard blocked the download; flagged for Peter if the team wants
its contents.

## Kernel table

`ref | author | dateRun | votes | license | kind | claimed score | measured vs nf_trim | verdict | local path`. License is "Apache-2.0 (stated)" only where the notebook's own text/header says so — Kaggle's kernel-metadata.json carries no license field, so this is read from markdown/code, not API metadata. "kind" from grepping each pulled `.ipynb` for `_TAPES_DATA`/`base85`/`zlib` (tape) vs `obs[` (reactive) vs neither (tooling/EDA).

| ref | author | dateRun | votes | license | kind | claimed score | measured vs nf_trim | verdict | local path |
|---|---|---|---|---|---|---|---|---|---|
| thomastschinkel/the-2945-farm-96-vs-the-top-10-public-bots | Thomas Tschinkel | 2026-09-19 | 142 | Apache-2.0 (stated, credits 6+ authors) | tape+reflex hybrid | **2944.7 live** (submission 56269928), 128-73 over its first 201 games; 519-21 (96%) vs the 10 top-scoring *public* notebooks; 0-36 vs 7 of the real top-10 teams | **gate: DONE/DONE, 72,101/72,762 (seed 0). 16-0 of 16 seeds (300-307, both seats) vs `router_yuan_nf_trim`, mean +15,982, worst +5,395, min bank 64,263** | **T6 candidate — beats nf_trim decisively** | `experiments/endgame/kernels/the-2945-farm-96-vs-the-top-10-public-bots/main.py` (extracted `%%writefile` cell; sha256 does not match the notebook's own `EXPECTED_SHA256`, see note below) |
| boatlee/v16-rc5-high-score-8c-4s-premium-market-lead | boatlee | 2026-08-12 | 314 | none stated | tape router (base85/zlib blob) | none (local paired sims only: 60/60 vs its own reconstructed source, 30 seeds) | not run (superseded — see note) | not verified, not run | `experiments/endgame/kernels/v16-rc5-high-score-8c-4s-premium-market-lead/` |
| salemali7/kaggriculture-2900 | Salem Ali | 2026-09-17 | 77 | none stated | tape router, appears to be a reworded fork of v16-rc5 (same 3 donor episode ids, same "99.91%" figure, same 8c/4s) | title claims "2900+" but body only repeats the same local 60/60 paired-sim claim as v16-rc5 — no ladder submission id or score shown | not run | **claim not substantiated in the notebook text** | `experiments/endgame/kernels/kaggriculture-2900/` |
| ahmedberatozer/kaggriculture-v48-clear-the-queue | Ahmed Berat Özer | 2026-09-17 | 82 | Apache-2.0 (stated, EXP-167 lineage header, credits thomastschinkel/yhay81/destbreso/aurax7/tetsutani/prvsiyan/Dmitrii Gluzdov) | tape+reactive hybrid | none in this file's own header beyond the lineage note | not run (superseded by the-2945-farm, which is downstream of this exact lineage) | tooling/lineage source, not tested standalone | `experiments/endgame/kernels/kaggriculture-v48-clear-the-queue/` |
| aurax7/kaggriculture-shop-router-reactive-v5 | Yaxon | 2026-09-14 | 93 | Apache-2.0 (stated, same EXP-167 header) | tape+reactive hybrid | none | not run | lineage source | `experiments/endgame/kernels/kaggriculture-shop-router-reactive-v5/` |
| flexonafft/kaggriculture-multi-route-farming-agent | Igor Zharov | 2026-09-16 | 93 | Apache-2.0 (stated, same EXP-167 header) | tape+reactive hybrid | none | not run | lineage source | `experiments/endgame/kernels/kaggriculture-multi-route-farming-agent/` |
| yhay81/shop-router-0913 | Yusuke Hayashi | 2026-09-13 | 4 | not checked (yhay81's other kernels state Apache-2.0; assume same) | tape router | none stated | not run | newer than our adopted `agents/router_yhay.py` (sourced Aug 30); not yet evaluated | `experiments/endgame/kernels/shop-router-0913/` |
| yhay81/shop-router-0911-simple | Yusuke Hayashi | 2026-09-11 | 9 | — | tape router | none stated | not run | newer than our base | `experiments/endgame/kernels/shop-router-0911-simple/` |
| yhay81/shop-router-0909 | Yusuke Hayashi | 2026-09-09 | 134 | — | tape router (0 grep hits for tape/obs signatures — likely a data-blob format grep missed; not opened line-by-line) | none stated in this pull | not run | newer, highest-voted of the yhay81 series since our Aug 30 adoption; referenced directly by the-2945-farm's credits as its route-tape source | `experiments/endgame/kernels/shop-router-0909/` |
| yhay81/shop-router-0908 | Yusuke Hayashi | 2026-09-08 | 90 | — | tape router | none stated | not run | superseded by 0909/0911/0913 | `experiments/endgame/kernels/shop-router-0908/` |
| yhay81/six-day-public-state-fieldbook | Yusuke Hayashi | 2026-09-02 | 131 | Apache-2.0 (stated) | tooling/fieldbook (public-state lookup, not a full agent per title) | none stated | not run | reference doc | `experiments/endgame/kernels/six-day-public-state-fieldbook/` |
| yhay81/three-day-shop-router | Yusuke Hayashi | 2026-09-03 | 123 | Apache-2.0 (stated) | tape router | none stated | not run | earlier than 0908/0909 | `experiments/endgame/kernels/three-day-shop-router/` |
| yhay81/when-do-daily-top-episodes-see-your-agent | Yusuke Hayashi | 2026-09-08 | 3 | — | tooling/mechanic doc (ladder-timing analysis) | n/a | n/a | relevant to our own ladder-noise section in CLAUDE.md; not read in depth | `experiments/endgame/kernels/when-do-daily-top-episodes-see-your-agent/` |
| jaxa623/2802-two-identical-agents-90-points-apart | sdy623 | 2026-09-17 | 70 | Apache-2.0 (stated) | mechanic-doc + one tape agent, byte-exact, hash-checked | **2802 in title; body shows two byte-identical entries at rating 2857 (56272485, 91 games) and 2786→peaked ~2767 (56276050, 119 games) — a measured ~90-point noise floor** | not run | **corroborates CLAUDE.md's own ~86-90-point ladder-noise finding independently**; also documents a turn-0 `BUY_PRODUCT WHEAT n / SELL WHEAT n` opening that targets the *rival's* index-1 order via lockstep settlement (credited to ahmedberatozer's V45), with a measured attack-size sweep (n=30 optimal, plateau 25-50, cliff below 10, self-harm above 85) — a mechanic not in our CLAUDE.md | `experiments/endgame/kernels/2802-two-identical-agents-90-points-apart/` |
| cjlcjlcjl/kaggriculture-what-the-top-farms-do-a-live-meta | Furina | 2026-08-12 | 75 | not checked | tooling/EDA (live meta tracker over official replay dataset) | reports ladder #1 at 3179.7 (2026-08-12 snapshot, stale) | n/a | stale (Aug 12) but methodology is reusable; confirms STRAWBERRY's 62-unit price-cliff floor matches our CLAUDE.md table exactly, and documents the top-band farm shape (8-9 cow + 4-6 sheep, NE+SW/NE+NW+SW land, 10-12 hands) matching our own `docs/REPLAY_ANALYSIS.md` | `experiments/endgame/kernels/kaggriculture-what-the-top-farms-do-a-live-meta/` |
| raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta | Rayk Kretzschmar | 2026-08-11 | 192 | not checked | EDA/meta doc | mentions scores 2836.8 and 2182.2 in context (not independently verified) | n/a | not read in depth | `experiments/endgame/kernels/kaggriculture-findings-from-zero-to-top-meta/` |
| raykkretzschmar/kaggriculture-rank-your-agent | Rayk Kretzschmar | 2026-09-13 | 137 | not checked | tooling (self-rating tool, per its Aug-12 mention in the live-meta doc: "agent 排名工具") | n/a | n/a | tooling, not an agent | `experiments/endgame/kernels/kaggriculture-rank-your-agent/` |
| georgymamarin/kaggriculture-visualized-what-every-crop-pays | Georgy Mamarin | 2026-09-15 | 104 | not checked | EDA (crop economics visualization) | n/a | n/a | tooling/EDA, not an agent | `experiments/endgame/kernels/kaggriculture-visualized-what-every-crop-pays/` |
| kaitofukami/25-27-strict-future-v27-midgame-meta-reset | Kaito Fukami | 2026-08-10 | 206 | not checked | tape router (title pattern "X/Y" = self-reported record vs a public holdout set) | 25/27 in title (own holdout, not ladder) | not run | part of kaitofukami's long versioned tape-router series (v21.1 → v48, 25-27 through 177-180); not individually tested, superseded in relevance by the-2945-farm which already benchmarks against multiple public agents including this lineage's relatives | `experiments/endgame/kernels/25-27-strict-future-v27-midgame-meta-reset/` |
| kaitofukami/40-40-early-floor-39-46-top-10-v48-fast-routes | Kaito Fukami | 2026-08-24 | 133 | not checked | tape router | 40/40 and 39/46 in title (own holdout) | not run | same series | `experiments/endgame/kernels/40-40-early-floor-39-46-top-10-v48-fast-routes/` |
| kaitofukami/177-180-fresh-top-30-v21-1-conditional-memory | Kaito Fukami | 2026-08-06 | 104 | not checked | tape router | 177/180 in title (own holdout) | not run | earliest of the series pulled | `experiments/endgame/kernels/177-180-fresh-top-30-v21-1-conditional-memory/` |
| boatlee/84-84-base-public-holdout-v14-clone-preemption | boatlee | 2026-08-08 | 179 | not checked | tape router | 84/84 in title (own holdout) | not run | earlier boatlee version than v16-rc5 | `experiments/endgame/kernels/84-84-base-public-holdout-v14-clone-preemption/` |
| tetsutani/adaptive-farming-strategy-for-kaggriculture | tetsu2131 | 2026-08-19 | 143 | not checked | reactive (has `obs[` hits) | n/a | not run | named as an opponent test case in the-2945-farm's section 6 ("adaptive farms" that beat it after day 11) | `experiments/endgame/kernels/adaptive-farming-strategy-for-kaggriculture/` |
| tetsutani/shape-the-shop-work-the-pasture-kaggriculture | tetsu2131 | 2026-09-06 | 126 | not checked | reactive | n/a | not run | credited in the-2945-farm's chassis table for "repair mechanisms" | `experiments/endgame/kernels/shape-the-shop-work-the-pasture-kaggriculture/` |
| tetsutani/market-smart-farming-kaggriculture | tetsu2131 | 2026-09-17 | 103 | not checked | reactive | n/a | not run | — | `experiments/endgame/kernels/market-smart-farming-kaggriculture/` |
| indarkarhana/shape-the-shop-work-the-pasture-top-10 | Indar Karhana | 2026-08-29 | 94 | not checked | tooling/EDA (title suggests a fork/analysis of tetsutani's notebook) | "top 10" in title, not substantiated in this pull | not run | not read in depth | `experiments/endgame/kernels/shape-the-shop-work-the-pasture-top-10/` |
| thomastschinkel/kaggriculture-public-state-router-74-5-win-rate | Thomas Tschinkel | 2026-09-05 | 99 | not checked | tape+reactive hybrid | 74.5% win rate claimed in title (own harness) | not run | thomastschinkel's earlier notebook — explicitly named in the-2945-farm as "My Public State Router [that] became part of the chassis of Ahmed Berat Özer's V25 to V48 series"; i.e. an ancestor of the T6 candidate above, not a separate one | `experiments/endgame/kernels/kaggriculture-public-state-router-74-5-win-rate/` |
| pilkwang/kaggriculture-structured-economic-policy | Pilkwang Kim | 2026-09-12 | 108 | not checked | not classified (0/0 grep hits, not opened) | n/a | not run | not read in depth | `experiments/endgame/kernels/kaggriculture-structured-economic-policy/` |
| prvsiyan/kaggriculture-frontier-the-soil-remembers-rain | prvsiyan | 2026-09-20 | 103 | Apache-2.0 (stated) | tape+reflex ("Frontier" series) | n/a in this pull | not run | credited in the-2945-farm's chassis table for tomato (V221B/V219), cattle transfer (V231) and six-sheep expansion (V233) projects — a direct upstream contributor to the T6 candidate | `experiments/endgame/kernels/kaggriculture-frontier-the-soil-remembers-rain/` |
| guruprasaathas111/kaggriculture-master-engine-v3 | Guru Prasaath S | 2026-09-20 | 83 | not checked | not classified (0/0 grep hits, not opened; 850 KB file suggests embedded data) | n/a | not run | not read in depth | `experiments/endgame/kernels/kaggriculture-master-engine-v3/` |
| reyhanksatria/kaggriculture-dynamic-route-agent | Reyhan Ksatria | 2026-09-16 | 85 | not checked | not classified (0/0 grep hits, not opened) | n/a | not run | not read in depth | `experiments/endgame/kernels/kaggriculture-dynamic-route-agent/` |
| lynnsakurai/farming-score-v3-replay-revised | Arlene | 2026-09-03 | 74 | not checked | not classified (0/0 grep hits, not opened) | n/a | not run | not read in depth | `experiments/endgame/kernels/farming-score-v3-replay-revised/` |
| andrewsokolovsky/kaggriculture-breaking-the-tie | Andrey Naymushin | 2026-08-23 | 73 | not checked | not classified (0/0 grep hits, not opened) | n/a | not run | not read in depth | `experiments/endgame/kernels/kaggriculture-breaking-the-tie/` |

**Coverage caveat.** 501 kernels last ran after 2026-08-06 (`experiments/endgame/kernels_after_aug6.csv`, from paging `kernels list --sort-by dateRun` through 6 pages). Pulling all 501 was not attempted; the 33 pulled above are the top ~30 by vote count within that window plus a handful named directly by the-2945-farm's credits, on the standard Kaggle assumption that votes track reach/quality. This is a sample, not a census — the ranked list (`experiments/endgame/top_after_aug6.txt`) has ~470 more unexamined titles, mostly lower-voted iterations of the same author series already represented above (ahmedberatozer alone has 8+ dated versions v38-v48 in the after-Aug-6 window; only the newest was pulled).

## What changed since our last look (Aug 30)

Our current `agents/router_yhay.py` derives from yhay81's `public-match-history-router-rating-2929-aug-30`. Since then yhay81 shipped four more route generations (`shop-router-0908`, `-0909` [134 votes, the most-voted of the series], `-0911-simple`, `-0913`), none yet pulled into our agents. Separately, and more importantly, a whole cross-team lineage formed downstream of yhay81's routes and thomastschinkel's original "Public State Router": Ahmed Berat Özer folded yhay81's shop routes, prvsiyan's sheep/tomato/cattle projects ("Frontier" V219/V221B/V231/V233), Dmitrii Gluzdov's stock-reservation logic, and aurax7/tetsutani's repair mechanisms into a versioned V25→V48 series (all Apache-2.0, all crediting each other in-file), which thomastschinkel then took as a base for the "2945 Farm" (v9/4) published 2026-09-19 — claiming a **live ladder score of 2944.7**, and measured here at **16-0 vs our `router_yuan_nf_trim`, mean +15,982 over 8 seeds both seats**. That agent did not exist at our Aug 30 checkpoint and is the clearest, best-evidenced T6 harvest candidate found. Separately, the official `kaggle/kaggriculture-episodes-*` dataset family (daily since 2026-07-30, continuing through today) was not in our notes before and offers a `ListEpisodes`-rate-limit-free path to top-band replays for T4/T9.

## Mechanic notes vs CLAUDE.md (not corrections — cross-checks)

- STRAWBERRY's price floor at 62 units of oversupply (linear curve) is independently confirmed by `kaggriculture-what-the-top-farms-do-a-live-meta`, matching our `MARKET_PARAMS`-derived table exactly.
- The-2945-farm's "rival_sold = inventory' − inventory + town_draw − own_sold" gives an exact public estimator of the opponent's same-turn sales; not written down in our CLAUDE.md as a formula, worth adding if we ever build a sale-racing layer.
- The-2945-farm's lesson 8.1 (Kaggle runs the last callable, not `agent` by name) is identical to our own documented gotcha — independent confirmation, not new information.
- jaxa623's ~90-point ladder noise floor (two byte-identical submissions, 2857 vs 2786/2767) independently reproduces our own measured ~86-90-point identical-code swing — strong cross-validation of that section of CLAUDE.md.
- jaxa623 also documents an undocumented-by-us exploit: a turn-0 `BUY_PRODUCT WHEAT n` then `SELL WHEAT n` at list index 0 doesn't hurt your own sell (same-index lockstep settlement) but raises the *rival's* index-1 order's clearing price, costing an exactly-funded opponent a seed on day 0. Swept optimum n≈30 against a 70-unit-opening rival; author's own conclusion is this is opponent-dependent, not a fixed constant.

## Not covered

GitHub repos (`WebSearch`, not cloned): `straf10/Kaggriculture` (MIT, majority-vote replay reconstruction + overlays, reached "top ~18%") and `graceyunliu/kaggriculture` (no license stated, replay-sync + evolutionary-search infrastructure) both independently validate our own tape-harvest strategy but were not pulled — their code is their own pipeline, not a drop-in agent. Discussion threads: see `needs_peter_download` above.
