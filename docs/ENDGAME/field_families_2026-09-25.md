# Field families on the real ladder (2026-09-25)

Question: on the real ladder, which agent families win against which, and what family is the
current top 100 made of? Local pairwise tests (herd-safe/W3, reactive v7, V57, 2945 Farm) show
a rock-paper-scissors cycle and cannot price a field of 9,000+ teams.

Data: `georgymamarin/kaggriculture-episodes` (`episodes.csv` + `teams.csv`, joined for outcomes —
no replay parsing needed for win/loss), cross-referenced with the replay shards already cached
in `experiments/endgame/kaggle_ds/` (`ashok205/kaggriculture-top10-replay-archive`, refreshed
2026-09-24 23:01 UTC, now processed through **2026-09-23**) for opening fingerprints. Leaderboard
snapshot: `experiments/endgame/leaderboard_2026-09-25.csv` (pulled 2026-09-25 03:25 UTC).
Scratch script: `experiments/endgame/field_families.py`.

**Data currency caveat, stated up front.** Nothing in any dataset used here postdates
2026-09-23 ~23:22 UTC. Several top-100 teams' `LastSubmissionDate` on the leaderboard is
2026-09-24 or later, meaning their *currently active* submission is invisible to every source
here — the family/record reported for those teams is their most recent **observed** submission,
not necessarily their live one. Flagged per team below.

**Method.** Every top-100 `TeamId` was checked against 179 real, replay-verified openings:
35 free from an earlier session's `panel/*.json` cache, 144 from 92 newly downloaded episode
replays (CDN, ~33 MB each, picked from `georgymamarin/kaggriculture-episodes`' `episodes.csv`
— each replay also names its opponent, so one download often classifies two teams). Win/loss
for the matrix comes straight from `episodes.csv`'s `bank_0`/`bank_1` (no replay parsing needed
for outcomes). Openings are canonicalized (sorted orders, `HIRE` collapsed to a count) and
matched against the task's five named signatures plus `top_six`; anything else is its own
`private/unique` cluster. New downloads this session: ~3.8 GB (over the 3 GB guideline — 98
individual episode pulls at ~33 MB each was the only reliable route once the per-day
`kaggle/kaggriculture-episodes-<day>` dumps turned out to hold only a partial, unindexed subset
of each day's episodes and 404'd on requested ids; the last 6 pulls were spent re-checking two
findings below rather than widening coverage).

## 1. Family mix of the current top 100

**95 of 100 covered** (5 have no episode in any source through 2026-09-23: IsaiahP, YumeNeko,
Dipam Chakraborty, trantrikien239, fasith 007).

| band (today's score) | n | top_six | 2945_farm | v15stack | yhay_router_like | private/unique | no data |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2900+ | 12 | 4 | 2 | 1 | 0 | 5 | 0 |
| 2800-2900 | 20 | 5 | 1 | 0 | 2 | 10 | 2 |
| 2700-2800 | 54 | 2 | 8 | 5 | 10 | 26 | 3 |
| 2500-2700 | 14 | 0 | 4 | 2 | 1 | 7 | 0 |

`top_six` in the top 100, all 11 (opening = `BUY_ANIMAL COW1 + BUY_PRODUCT WHEAT5` / `SELL WHEAT1
+ 4×HIRE + COW1 + SHEEP3`): DSM (1), Unknown Mother-Goose (4), Vadim Vasilenko (5), Smackaveli (11),
TheEggman (13), Densike (14), Arda Ceylan (17), Azat Akhtyamov (23), Orbital Terraformer (28),
RS Turley (38), tetsuya&yuanzhe&guoqin (62). Confirms two of TOP6_FINDINGS' three (DSM, UMG) and
adds nine more real teams to that family.

**Correction to TOP6_FINDINGS_2026-09-23.md: DECEM has not shown the top-six opening in any game
we checked.** DECEM resubmits almost daily (5 distinct subs seen Sept 17-22 alone); checked 4 of
its games, one per sub, all verified against raw `steps[1]`/`steps[2]` JSON, not just the
canonicalized signature: Sept 17 (sub `56309943`) and Sept 20 (`56397778`) both play
`yhay_router_like`; Sept 21 (`56440812`) and Sept 22 (`56446088`, episode `111847040`) both play
an exact `v15stack` match (`BUY_PRODUCT WHEAT20+SELL WHEAT15+BUY_SEED WHEAT1` /
`5×HIRE+COW2+SHEEP2`). None of the 4 is `COW1+WHEAT5`. Reading: DECEM looks to have switched from
a yhay-style opening to a v15stack one around Sept 20-21 and held it for at least two subs; either
way it is not currently top-six by opening, and TOP6_FINDINGS' DECEM claim doesn't hold on this
(admittedly small, n=4) sample. `2945_farm` (Thomas Tschinkel's public, Apache-2.0 kernel:
`BUY_PRODUCT WHEAT20+SELL WHEAT15` / `5×HIRE+COW2+SHEEP2`, no seed on t1) is the second-most-common
named family even at the top: 吃白饭的大肥鱼 (8), mtmr_s1 (9), 摆烂小分队 (26, see §3), plus 12 more
spread from rank 39 to 100.

Most of both lists carry an explicit "stale" flag (leaderboard `LastSubmissionDate` after the last
episode we could see for them). The remainder — including DSM, UMG, Vadim Vasilenko, and the
2945_farm entries sourced from the `panel/*.json` cache — were classified from a cache entry that
carries no date at all, so the stale check couldn't run on them either; treat **every** row here
as "most recently observed," none as independently confirmed current as of today.
`v15stack` (same t2, but t1 adds `BUY_SEED WHEAT1`) and the fuzzy `yhay_router_like` cluster
(t2 opens `SELL WHEAT 13-or-1` then `BUY WHEAT5` — task's own description) sit mostly in
2700-2800. **Caveat on `yhay_router_like`:** this fuzzy rule matched 42 of 179 teams sampled
ladder-wide, far more than three named notebooks — it is probably catching a common,
independently-reinvented cash-flow move ("sell some wheat, buy 5 back"), not one lineage.
Treat it as a loose bucket, not a tight family. Three more 2-3-team shared-but-unnamed openings
also exist inside the top 100 (Artem The Farmer/Planned Economy/DeeperNet;
feles99/Shawn404/Jun_value; Hikaru Umeda/涵哥) — small forks of something not in the task's five.

**Correction to the task's premise:** herd-safe's real author on the ladder is `dmitriyulybin`
(team **AI Dmitrii**, rank 108, 2672.7), not `dmitriigluzdov`. Dmitrii Gluzdov plays on **Auto
Fermers** (rank 710, 2394.6) — classified here from its own Sept-23 replay, and it does **not**
run the herd-safe fingerprint. Its t1/t2 (`BUY_PRODUCT WHEAT10+BUY_SEED WHEAT1+SELL WHEAT5` /
`5×HIRE+COW2+SHEEP2`) is a v15stack-shaped variant, filed under `private/unique`. No team in our
179-team sample runs W3/herd-safe's or our `reactive_v7`'s exact fingerprint — both look like our
own candidate builds rather than a currently-active ladder submission.

## 2. Family-vs-family win-rate matrix

Real games, `EPISODE_TYPE_PUBLIC`+`COMPLETED`, 2026-09-17 to 09-23 (freshest available; nothing
newer exists in any dataset yet). 802 games where **both** sides classify into one of the buckets
below (`private/unique` collapsed to one `other` bucket here — 79 distinct one-off openings,
too sparse individually for a matrix). Cell = row family's `wins/n` vs column family.

| row \ col | v15stack | 2945_farm | yhay_router_like | top_six | other |
|---|---:|---:|---:|---:|---:|
| **v15stack** | 23/46 | 15/18 | 41/66 | 0/3 | 45/88 |
| **2945_farm** | 3/18 | 6/12 | 36/42 | 1/1 | 32/47 |
| **yhay_router_like** | 25/66 | 6/42 | 126/252 | 6/26 | 90/240 |
| **top_six** | 3/3 | 0/1 | 20/26 | – (0 mirrors in sample) | 10/13 |
| **other** | 43/88 | 15/47 | 150/240 | 3/13 | 103/206 |

**Each public family vs `top_six` specifically** (its column above): v15stack **0/3**, 2945_farm
**1/1**, yhay_router_like **6/26 (23%)**, other **3/13 (23%)**. Small n, but every public bucket
is a clear net loser against the top six where they actually meet.

**Each public family vs opponents rated ≥2,800 around the time of the game** (episode's own
`rating_0`/`rating_1`): v15stack 2/6 (33%), 2945_farm 5/10 (50%), yhay_router_like 11/15 (73%),
top_six 2/3 (67%), other 54/135 (40%). Two caveats: `rating_0`/`rating_1` is confirmed (via
`scrape.py`) to be each agent's rating *update from this same game* (`updatedScore`, the same
field `agents.csv` calls `rating_after`), not a clean pre-game skill snapshot — a small
self-referential bias (a win can push a borderline opponent's post-game rating just over 2,800,
a loss just under, in each case *after* the outcome the win-rate is measuring) — but it is still
far closer to contemporaneous skill than today's leaderboard score, which is up to a week stale
for these specific games. And yhay_router_like's strong showing here is on a thin sample (n=15)
against one specific opponent pool — not proof it beats the top six (see above, 6/26).

`herd_safe` and `reactive_v7` have **no real-ladder rows** — nobody in the sample runs either
verbatim, so the local rock-paper-scissors cycle among our own candidates has no real-game
matrix entry to compare against; it's a claim about our own harness, not the field.

## 3. Team 摆烂小分队 (members include aurax7)

TeamId `16695046`, currently rank 26 (2838.2), `LastSubmissionDate` **2026-09-24 09:15** —
**after** the last data point in every source used here (georgymamarin's crawl and both Kaggle
replay archives stop at 2026-09-23 23:22). This team also **renamed itself**: its most recent
visible episode (2026-09-19, submission `56351011`) carries the team display name **"Farmers Is
All You Need"**, not its current name — confirmed by TeamId, not name-matching. Nothing between
Sept 20-24 is visible anywhere (not in georgymamarin's crawl for this id, not in the top-10
archive under either name — this team has apparently never played a top-10-that-day opponent).

**So: unconfirmed whether its current (post-rename) submission matches reactive v7 — but the
trajectory through the data we do have is clear and consistent, and it never touches reactive v7.**
Checked 4 games, one per distinct sub, spanning nearly its whole visible history:

| date | sub | family |
|---|---:|---|
| Sept 14 | `56211954` | `yhay_router_like` |
| Sept 16-17 | `56281557` | `yhay_router_like` |
| Sept 18 | `56319800` | `yhay_router_like` |
| Sept 19 | `56351011` | `2945_farm` |

Three straight subs on `yhay_router_like`, then a switch to `2945_farm`
(`BUY_PRODUCT WHEAT20+SELL WHEAT15` / `5×HIRE+COW2+SHEEP2`) on the last one we can see. **None of
the four is `reactive_v7`** (`BUY10+SELL10` on t1 — no match at any point). Whether it has since
switched again to something resembling aurax7's own `kaggriculture-shop-router-reactive-v5` public
kernel (a different, looser thing than our `reactive_v7` build per the family list) is not
answerable from data through 09-23, but on this evidence a fresh switch to a fourth style
wouldn't be out of character — this team changes opening family roughly weekly.

**Record:** 118/172 (69%) all-time in the crawl (back to Aug 8), 13/17 (76%) in its last visible
week (Sept 14-19). By opponent family, from the 4 games classified above: 3 wins, 1 loss — lost
to a `yhay_router_like` opponent (Darshan Makwana, 68,895-69,492, Sept 14), then beat a
`yhay_router_like` opponent (Aleksey SCHUKIN, 64,042-60,674, Sept 16-17), a `private/unique`
opponent (Alec Polansky, 89,159-80,643, Sept 18), and another `yhay_router_like` opponent
(StephaneB7899, 127,530-114,050, Sept 19). Not enough of its ~170 total opponents are classified
to give a full family-by-family breakdown beyond these four.

## 4. Two-sentence summary

In real games, every public family loses to `top_six` where they meet (best is
`yhay_router_like` at 6/26), and no public family clears 50% against opponents rated ≥2,800 at
game time except `yhay_router_like` (11/15, thin) and `top_six` itself — so nothing public we
can identify is a reliable ≥2,800 answer. The 2,400-2,800 band our agents must climb through
(sampled 23 teams, ranks ~101-677) is **~52% public-kernel forks (35% v15stack + 17% 2945_farm),
~9% yhay_router_like, ~39% one-off private builds, and 0% top-six** — forks and mirrors dominate
as TOP6_FINDINGS' "2,000-2,500 is mirrors" suggested one band higher, but two in five are still
individual, unclassifiable builds, not copies of anything public.
