# T4: Top-10 copyability and top-band panel (2026-09-21)

Task: `docs/superpowers/plans/2026-09-21-endgame.md`, T4. Determines whether
any of today's top-10 teams (leaderboard snapshot, this morning) run a fixed,
harvestable schedule the way the Aug 31 rank-16 harvest depended on, or
whether they are reactive like the then-#1 team on Sept 1.

**Today's top 10** (teamId, name, score at time of assignment):
16732748 DSM 3177.3 · 16718819 Majkel1337 3089.1 · 16770421 Vadim Vasilenko 3064.7 ·
16730524 THIRD FARM CLUB 3052.9 · 16730612 Unknown Mother-Goose 3042.8 ·
16640510 SpaTaro 3039.0 · 16732403 ymg_aq 3032.4 · 16675778 Orbital Terraformer 3024.7 ·
16654697 KawattaTaido 3017.0 · 16760569 Otter Vibe 3016.1.

## How teams were reached (budget: 12 `ListEpisodes` calls, used exactly 12)

`experiments/endgame/top10_episodes.txt` was still empty when this task
started, so a transitive crawl was used instead, per the plan's fallback.
Call log: `experiments/endgame/listepisodes_calls.log` (unedited, 12 lines).

Climb: our two live submissions (`56202213`, `56202203`) had **zero**
episodes against any of today's top-10 teamIds directly (502 episodes
scanned). Hopped through our highest-rated opponent 4 times
(rating 1722 → 2737 → 2867 → 2950), and the 4th hop's opponent list
(submission `56263268`, rating 2950) directly contained **5** of the 10
target teams as its own opponents: THIRD FARM CLUB, ymg_aq, Orbital
Terraformer, Otter Vibe, SpaTaro. Fetching those 5 teams' own episode lists
(5 more calls) turned up the remaining 4 (DSM, Majkel1337, Vadim Vasilenko,
Unknown Mother-Goose) as opponents inside those lists — free, no extra
calls. The last 3 calls went to DSM/Majkel1337/Vadim Vasilenko's own
*current*-submission episode lists directly, since only 1 scattered episode
of each was otherwise known.

**9 of 10 teams reached. KawattaTaido not reached** — appears exactly once,
as an opponent inside Majkel1337's list (submission `56417128`, episode
`111566809`), not enough for any verdict.

A public Kaggle dataset, `ashok205/kaggriculture-top10-replay-archive`
(daily top-10 replay index + shards, CC0), was found and used *after* the
budget was already spent, for two things that needed no `ListEpisodes`
call: (1) an opening-clade cross-check across all reached teams (below),
and (2) identifying that our own opponent-lookup wasn't blind to
`submissionId 56269928` (coordinator's "2945 Farm") — confirmed by episode
metadata to be team **Thomas Tschinkel** (teamId `16719123`). The archive's
daily-top-10 index does **not** cover KawattaTaido or Vadim Vasilenko by
name at all (their rise into today's top 10 postdates the archive's last
processed date, 2026-09-19), so it could not fill either gap.

## Per-team results

Windows: 0–71 (opening), 72–143 (post-first-shop), 144–400, 400–718.
`same-key72` / `diff-key72` = pairwise agreement over 72–143 grouped by
whether the two episodes shared the same day-72 shop. A true tape router
shows a **large gap** here (same-key high, diff-key low); a reactive agent
shows little or no gap. `own-opening` = pairwise agreement of the team's own
tape over 0–71 across its own episodes — this must itself be ~1.0 for a
"fixed opening" claim to mean anything. `ag 144-400 same/diff` similarly
splits the plan's core window by whether the 144-key matched, computed for
every pair (not just same-key ones), so a team with <2 same-key144 pairs
still gets a same-vs-diff comparison rather than a blank cell. **Where
same-key144 pairs < 2, the plan's strict rule (`copyable` if ≥0.90 on ≥2
same-key pairs, `reactive` if ≤0.30) returns `unclear` by its own
definition** — those cells are marked `unclear (strict)` below even where
the verdict column reads `reactive` on corroborating evidence (own-opening
+ the 72–143 gap + the same/diff-144 gap).

| team | sub used | latest? | n eps | own-opening | same72 ag(n) | diff72 ag(n) | 144–400 same(n)/diff | 400–718 same | verdict |
|---|---|---|---:|---:|---|---|---|---:|---|
| DSM | 56401245 | yes | 15 | 0.40 | 0.23 (18) | 0.05 (87) | 0.31 (1) / 0.06 | 0.003 | `unclear (strict)`; **reactive** on corroborating evidence — own-opening low, 5x same/diff-144 gap still tiny in absolute terms |
| Majkel1337 | 56407295 | yes | 15 | 0.76 | 0.42 (21) | 0.40 (84) | 0.14 (1) / 0.09 | 0.02 | `unclear (strict)`; **reactive** — no 72–143 same/diff gap at all |
| Vadim Vasilenko | 56396983 | yes | 15 | 0.71 | 0.43 (19) | 0.27 (86) | 0.20 (3) / 0.09 | 0.004 | **reactive** — clears the ≥2-pair bar, 0.20 ≪ 0.90 |
| Orbital Terraformer | 56212726 | yes | 15 | 0.45 | 0.16 (19) | 0.19 (86) | — (0) / 0.07 | — | `unclear (strict, 0 pairs)`; **reactive** — diff72 ≥ same72, the opposite of a router signature, on the deepest public history of anyone (862 eps) |
| **Otter Vibe (current, re-run 2026-09-21)** | **56328447** | **yes** | 7 | **1.00** | 1.00 (2) | **0.97** (19) | **0.14 (1)** / 0.05 | **0.00** | `unclear (strict, 1 pair)`; **reactive post-144 on corroborating evidence** — fixed through 143 exactly as before (same≈diff≈0.97–1.0, still not key-driven in that window), but the one same-key144 pair now available (`110920468`/`111547147`) crashes to 0.14 at 144–400 and 0.00 at 400–718 — well inside the ≤0.30 reactive band, closing out what had been the strongest harvest lead |
| THIRD FARM CLUB (old sub, original pass) | 56279316 | **no**, transfers (below) | 15 | 1.00 | 0.95 (15) | 0.87 (90) | 0.00 (1) / 0.05 | 0.00 | **fixed through 143, then genuinely diverges** — same144 (0.00) is *below* diff144 (0.05), so whatever branches its schedule at turn 144 is not the shop-key convention used here |
| **THIRD FARM CLUB (current sub, re-run 2026-09-21)** | **56372014** | **yes** | 3 | **1.00** | — (0) | **0.98** (3) | — (0) / 0.001 | — | `unclear (strict, 0 same144 pairs)` — all 3 episodes landed different day-144 keys, so no new post-144 evidence; still fixed through 143 (1.00 own-opening, 0.98 diff72) exactly as the old-sub row shows. Combined with the transferring old-sub same144 pair (ag=0.00, above), the only post-144 data point on this lineage remains reactive-consistent but the strict ≥2-pair bar is still unmet |
| Unknown Mother-Goose | 56266758 | **no**, stale (below) | 15 | 0.99 | 1.00 (9) | 1.00 (96) | 0.48 (2) / 0.40 | 0.02 | old sub only — see staleness table |
| Otter Vibe (old sub) | 56218366 | **no**, stale (below) | 15 | 1.00 | 0.86 (9) | 0.76 (96) | 0.28 (1) / 0.01 | 0.00 | superseded by the current-sub row above |
| SpaTaro (old sub, original pass) | 56263693 | **no**, stale (below) | 15 | 0.07 | 0.04 (11) | 0.03 (94) | — (0) / 0.00 | — | **reactive even on the old sub** |
| **SpaTaro (current sub, re-run 2026-09-21)** | **56384319** | **yes** | 3 | **0.03** | 0.04 (1) | 0.03 (2) | — (0) / 0.00 | — | **reactive, confirmed on the current sub** — own-opening near zero (0.03) and same72 agreement also near zero (0.04) even when the two episodes share a day-72 shop key. Matches the old-sub verdict exactly; this team has been reactive on every submission checked |
| ymg_aq (old sub, original pass) | 56265958 | **no**, stale (below) | 15 | 0.68 | 0.58 (13) | 0.45 (92) | 0.02 (2) / 0.00 | 0.00 | **reactive** |
| **ymg_aq (current sub, re-run 2026-09-21)** | **56393666** | **yes** | 3 | **0.99** | 0.17 (1) | 0.10 (2) | **0.004 (1)** / 0.01 | **0.00** | **reactive** — fixed opening (0.99 own-opening, near-identical 0-71 tape every game) but 72-143 already crashes even on a matching key (0.17), and the one same-key144 pair (`111381657`/`111444483`) is 0.004 at 144-400, 0.00 at 400-718. Same shape as before, now confirmed on the live submission |
| KawattaTaido | 56417128 | unknown | 1 | — | — | — | — | — | **unreached** |
| Thomas Tschinkel ("2945 Farm") | 56269928 | yes (as of Sep 17) | 9 | 1.00 | 0.99 (7) | 0.99 (29) | **0.77** (3) / 0.36 | 0.36 | **hybrid, genuinely key-driven**: 0.77 same144 vs 0.36 diff144 is a real gap (not just time-drift), fixed template through ~400 that degrades after |

No team clears the plan's strict `copyable` bar (≥0.90 over 144–400 on
≥2 same-key pairs). **Thomas Tschinkel/"2945 Farm" comes closest** (0.77 on
3 same-key144 pairs, and the 0.77-vs-0.36 same/diff gap confirms it is
actually reading the shop key, not just a static tape with time-drift) but
the same pairs show agreement roughly halving to 0.36 by 400–718 — the
"agrees early, drifts/adapts late" shape the Sept 1 #1 team showed, softer
here (0.36, not ~0.00).

### The headline: today's top 3 and the best-covered sub all look reactive

DSM (#1), Majkel1337 (#2) and Vadim Vasilenko (#3) are all analyzed on
their **current, active submission** (not a stale one), each with a full
15-episode sample, and each shows either a low own-opening consistency
(DSM 0.40), a same-key/diff-key gap that's small or absent (Majkel1337:
0.42 vs 0.40 — essentially zero gap, the clearest negative signal in the
table), and in every case 144–400 agreement on the few same-key144 pairs
found is far below the 0.90 bar (0.14–0.31), with the same-vs-diff gap at
144 tiny in absolute terms even where present (DSM 0.31 vs 0.06). **Orbital
Terraformer**, which has by far the most public episodes of anyone reached
(862, the only sub that clears "thin key coverage" on its own), is also
clearly reactive — its diff-key72 agreement (0.19) is *higher* than its
same-key72 agreement (0.16), the opposite of what a router would show.
This matches the plan's stated downside case: **if the top band is
reactive, T6 (harvested routers) is closed for these teams and the honest
target is the repair leg (T5) plus whatever T6 candidates survive below.**

### Stale-submission caveat (do not skip this when reading the table)

Five of the rows above are analyzed on an **older, no-longer-active**
submission, because that's what had ≥15 locally-known episodes. A direct
check — one current-sub episode's 0–71 tape vs the analyzed old-sub tapes —
gives:

| team | old sub | current sub | opening agreement (old vs current) | does the row above transfer? |
|---|---:|---:|---:|---|
| THIRD FARM CLUB | 56279316 | 56372014 | **1.00** | **yes** — same lineage, row is live |
| Otter Vibe | 56218366 | 56328447 | 0.014 | **no** — fully rebuilt |
| SpaTaro | 56263693 | 56384319 | 0.028 | **no** — fully rebuilt |
| ymg_aq | 56265958 | 56393666 | 0.00 | **no** — fully rebuilt |
| Unknown Mother-Goose | 56266758 | 56417993 | 0.00 | **no** — fully rebuilt (12 distinct subs seen this week — a moving target regardless) |

So **THIRD FARM CLUB's row is informative about the live agent** (a
genuinely fixed opening, 1.00 own-opening and 1.00 old-vs-current, and a
strong 72–143 signature). **Re-run 2026-09-21 on 3 fresh current-sub
episodes still found 0 same-key144 pairs** (all 3 landed different day-144
keys) — no new post-144 evidence, the divergence recorded on the old sub
(same144 0.00 < diff144 0.05) is still the only post-144 data point on this
lineage and it remains short of the 2-pair bar. **Otter Vibe's stale-sub row
(old sub `56218366`) doesn't transfer, but its current sub `56328447` now
has 7 episodes (up from 5), and the 2 new ones finally produced a
same-key144 pair** (`110920468`/`111547147`, both `YARN_STORE__BRUNCH_SPOT`)
— own-opening and 72–143 are unchanged (still ~0.97-1.00 regardless of key,
not reading the shop signal in that window), but that one same-key144 pair
agrees only **0.14** over 144–400 and **0.00** over 400–718 — decisively
below the 0.90 copyable bar and inside the ≤0.30 reactive band. **This
closes out Otter Vibe as a harvest lead**: it runs one fixed script through
turn ~143 regardless of opponent, then diverges hard once real play starts,
the same "fixed-early/reactive-late" shape as DSM and Majkel1337. **SpaTaro
and ymg_aq were re-run on 3 fresh current-sub episodes each and both
confirm their old-sub verdicts on the live agent**: SpaTaro stays reactive
throughout (own-opening 0.03, same72 0.04 — no fixed opening at all on the
current sub either), and ymg_aq keeps its fixed-opening/reactive-body shape
(own-opening 0.99, but the one same-key144 pair found is 0.004 at 144-400
and 0.00 at 400-718). **Unknown Mother-Goose's row still describes an agent
that no longer exists on the ladder** (not re-run this session) — do not
use it to judge the current field.

### Cross-team opening clade check

Built an 11×11 pairwise 0–71 agreement matrix (our `router_yuan_nf_trim`
opening plus one current-sub tape per reached team, `experiments/endgame/clade_map.py`
→ `experiments/endgame/clade_matrix.json`) to check whether any of the
rebuilders (or anyone else) converged on a shared public template — e.g.
"2945 Farm" itself, since it's a public Apache-2.0 kernel. **No
convergence found**: every off-diagonal entry is ≤0.31 (DSM–Vadim 0.11,
Vadim–Orbital 0.31, UMG–Orbital 0.18, everything else ≤0.08, our own
opening agrees with nobody above 0.04). Nobody in this sample is visibly
running the public hybrid, and no two top teams share an opening.

### "2945 Farm" / Thomas Tschinkel — separately requested detail

Identified `submissionId 56269928` as team **Thomas Tschinkel**
(`teamId 16719123`) by downloading one of its episodes and reading
`info.TeamNames` — this is an *inferred* name mapping from the submission
id the coordinator supplied, not independently confirmed against a public
kernel title. Only **9 episodes** of this submission are reachable within
budget (all Sept 16–17; the public `ashok205` archive only lists this team
under name "Thomas Tschinkel" for 2026-08-14 through 08-18, a stale, older
window with no rating data attached, so it was not used for the loss set).

Of those 9, **4 are losses against opponents rated ≥3,000** (the other 5
are either wins or losses to opponents rated <3,000):

| episode | seed | Tschinkel seat | Tschinkel reward | opp reward | opp submission | opp rating |
|---|---:|---:|---:|---:|---:|---:|
| 110055611 | 1520555243 | 1 | 81,680 | 98,006 | 56265958 (ymg_aq, old sub) | 3044.9 |
| 109848580 | 1225767790 | 0 | 78,960 | 82,717 | 56263693 (SpaTaro, old sub) | 3055.0 |
| 109821873 | 1203526051 | 1 | 111,067 | 112,115 | 56265958 (ymg_aq, old sub) | 3034.1 |
| 109694364 | 1361507966 | 0 | 66,533 | 74,922 | 56265958 (ymg_aq, old sub) | 3030.4 |

Opponent seat's tape for each saved to `experiments/endgame/panel/<episode>_<opp_seat>.json`;
`experiments/endgame/panel/index.json` has a `"set": "farm2945_losses"` entry
for each with the exact fields requested. **This is short of the requested
15** — verified by scanning both (a) all 3,894 completed episodes visible
across the 12 `ListEpisodes` calls made this session, and (b) all 174
replays (5.4 GB) already cached in `experiments/endgame/rep/` by any agent
this session (zero new Tschinkel appearances found in either). Getting to
15 needs either more `ListEpisodes` budget (submission `56269928` directly,
or its current/any later submission if it has one) or Peter pasting
episode ids.

## Panel

`experiments/endgame/panel/<episode>_<seat>.json` — 282 action-list files
(one per team-seat per analyzed episode, both the top team's own tape and
its opponent's, plus the 4 farm2945_losses opponent tapes — those 4 files
were already written by the Tschinkel row itself, since a "loss" episode's
opponent tape and a "top team" row's opponent tape are the same file; each
now carries **both** the `is_top_team`/`team` fields and the
`"set": "farm2945_losses"` fields in `index.json`, which T5 should be aware
of). `experiments/endgame/panel/index.json` maps each file to
`{seed, team/team_id, sub, rating, reward, opp_*, key72, key144, is_top_team}`,
or the `farm2945_losses`-specific schema. Both gitignored
(`experiments/endgame/panel/`, `experiments/endgame/rep/`).

### Splice-vs-rebuild check (gated on same-key144 ≥ 0.9)

Per the task's gate, farm2945/router_yuan_nf_trim opening comparisons only
get run for a team with a same-key144 pair ≥0.90. **None of the four
re-run teams cleared that bar** — best same-key144 result across all four
was Otter Vibe's 0.14 — so this comparison was not run for any of them; the
question of splice-vs-rebuild doesn't arise because none of them qualify as
copyable in the first place.

## Harvest recommendation, one line per team

- **DSM, Majkel1337, Vadim Vasilenko** (today's #1–#3): reactive on current
  subs — **do not harvest**, T6 is closed for these three as of today.
- **Orbital Terraformer**: reactive despite the deepest public history of
  anyone (862 episodes) — **do not harvest**.
- **Otter Vibe (current sub `56328447`), re-run 2026-09-21 on 7 episodes**:
  **do not harvest.** Still fixed through turn ~143 regardless of opponent
  (own-opening 1.00, same≈diff72 ≈0.97-1.00), but the first same-key144 pair
  ever obtained (`110920468`/`111547147`) agrees only 0.14 over 144-400 and
  0.00 over 400-718 — well inside the reactive band. This was the best lead
  in the original pass; it no longer is.
- **THIRD FARM CLUB (current sub `56372014`, via transfer), re-run
  2026-09-21 on 3 more episodes**: **unresolved, not a confirmed harvest
  candidate.** Still fixed through 143 (1.00 own-opening), but the 3 new
  episodes landed 0 same-key144 pairs (all different day-144 keys) — no
  progress on the post-144 question. The only post-144 data point remains
  the transferred old-sub pair (0.00 agreement, reactive-consistent). Would
  need several more episodes landing a repeated day-144 key to settle either
  way — not worth chasing given Otter Vibe, ymg_aq and SpaTaro all came back
  reactive on the same kind of evidence.
- **SpaTaro, ymg_aq, re-run 2026-09-21 on 3 episodes each**: **reactive,
  confirmed on the live submission — do not harvest.** SpaTaro has no fixed
  opening at all (own-opening 0.03, same as the dead sub). ymg_aq has a
  fixed opening (0.99) but its one same-key144 pair agrees 0.004 at 144-400
  and 0.00 at 400-718 — same fixed-early/reactive-late shape as Otter Vibe
  and DSM.
- **Unknown Mother-Goose**: not re-run this session (still only 1 episode of
  its current sub known) — row above describes a dead submission; **no
  verdict on the live agent**.
- **KawattaTaido**: **unreached**, no verdict possible.
- **Thomas Tschinkel / "2945 Farm"**: hybrid shape (genuinely key-driven,
  copy-worthy through ~turn 400, then drifts) and, per the coordinator, a
  **public Apache-2.0 kernel** — if that license claim holds, reading its
  published source is strictly better than reverse-engineering it from
  replays, and should be checked against T2's `public_inventory.md` rather
  than harvested here.

## What's needed from Peter to finish this

Paste into `experiments/endgame/top10_episodes.txt` (3 ids each, most
recent completed episodes of the team's **current** submission):

1. **Otter Vibe** — resolved 2026-09-21 (reactive post-144, do not harvest);
   no further episodes needed for this question.
2. **THIRD FARM CLUB**, current sub `56372014` — still only 3 episodes, 0
   same-key144 pairs; 10-15 more episode ids would be needed to get
   same-key144 coverage on the confirmed-transferring opening, but this is
   now low priority given every other re-run team came back reactive.
3. **KawattaTaido** (only known sub: `56417128`) — completely unreached.
4. **Unknown Mother-Goose**, current sub `56417993` — only 1 episode known;
   team resubmits ~12×/week so ids need to be fresh.
5. **ymg_aq** — resolved 2026-09-21 (reactive, do not harvest) on 3
   episodes of current sub `56393666`; not a priority for more.
6. **SpaTaro** — resolved 2026-09-21 (reactive, do not harvest) on 3
   episodes of current sub `56384319`; not a priority for more.
7. **Vadim Vasilenko** — has 15 current-sub episodes and a `reactive`
   verdict already, but a second independent submission's episodes (it
   only has 2 known subs total) would confirm the verdict isn't an
   artifact of one submission's early-game variance.
8. For the farm2945_losses set: 10+ more episode ids of submission
   `56269928` (or its current successor, if any) to close the gap from
   4 to 15 requested losses vs 3,000+-rated opponents.

## Untracked scratch files (do not commit)

`experiments/endgame/panel_plan.json`, `episode_agents_index.json`,
`expanded_plan_raw.json`, `to_download.json`, `download_log2.txt`,
`our_opening.json`, `clade_matrix.json`, `current_sub_opening_check.json`,
`tschinkel_scan_hits.json`, `tschinkel_scan.log`, `copyability_results.json`,
`kaggle_ds/*.parquet`, `kaggle_ds/*.json`, `kaggle_ds/*.csv` — all
intermediate working data for this task, not covered by an explicit
`.gitignore` line (only `rep/`, `kernels/`, `panel/`, `*.csv`, and
`episodes_*.json` are listed there). `.gitignore` was not touched, per
instructions.
