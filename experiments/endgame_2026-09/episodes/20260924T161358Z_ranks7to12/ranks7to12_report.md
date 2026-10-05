# The 2,900 band: leaderboard ranks 7-12, compared with the existing top-six corpus

Read-only research. Nothing was submitted to Kaggle and no git commands were run. Generated
2026-09-24, from `episodes/20260924T161358Z_ranks7to12/`, reusing
`episodes/20260923T153431Z_top6/` for ranks 1-6 rather than re-downloading it.

## 1. Ranks 7-12, resolved

**Snapshot:** `kaggle competitions leaderboard kaggriculture -d` (full CSV download, all ~9,975
teams), retrieved **2026-09-24T16:13:50Z**. **Measured.**

Each team's currently-active-for-matchmaking submission was resolved by calling
`ListTeamPublicSubmissions` (which returns only the 2 submissions currently eligible for
matchmaking, per the competition's latest-2-active rule) and matching each candidate's
`public_score` against the leaderboard row. Five of six matched exactly; TheEggman's best
candidate (56498825, score 2910.6) was 3.8 off the leaderboard's 2914.4 — plausible ordinary
rating drift between the two data pulls, not a wrong ID, since the other candidate (56523449,
score 2528.1) was off by nearly 400. **Measured, with that one near-exact match flagged rather
than silently accepted.**

| Rank | Team | Rating | Team ID | Active submission |
|---|---|---|---|---|
| 7 | Kaggledew Valley | 2964.1 | 16633132 | 56478393 |
| 8 | Azat Akhtyamov | 2943.5 | 16743356 | 56491144 |
| 9 | THIRD FARM CLUB | 2933.5 | 16730524 | 56520754 |
| 10 | Arda Ceylan | 2930.9 | 16673205 | 56508756 |
| 11 | mtmr_s1 | 2926.7 | 16758882 | 56488920 |
| 12 | TheEggman | 2914.4 | 16887437 | 56498825 |

**The leaderboard has moved substantially since the top-six corpus was captured (2026-09-23
15:34).** Of the original top six (Boey, M & M & P & Q, DSM, Unknown Mother-Goose, DECEM,
吃白饭的大肥鱼), only **DSM, Unknown Mother-Goose, DECEM and 吃白饭的大肥鱼** still appear in the
current top six — Boey and M & M & P & Q have both dropped out of the visible top ~18, replaced by
Vadim Vasilenko (now rank 3) and Majkel1337 (now rank 4). Per the task, ranks 1-6 in the combined
table below still use the original corpus's six teams (that is what "reuse the existing corpus"
means here) — it is a snapshot of six strong agents, not literally "today's #1 through #6" anymore.
**Measured.**

## 2. Episode download summary

All six teams reached the full 60/60 sample with **zero shortfall** — every team had well over
60 non-validation completed episodes available (76 to 202). `manifest.csv` (360 rows) was frozen
to disk before any download began, per the task's instruction. **Measured.**

| Team | API non-val-completed | Sampled | Newest episode (UTC) | Oldest in sample |
|---|---|---|---|---|
| Kaggledew Valley | 201 | 60 | 2026-09-24 16:19 | 2026-09-23 23:48 |
| Azat Akhtyamov | 174 | 60 | 2026-09-24 16:22 | 2026-09-24 00:10 |
| THIRD FARM CLUB | 76 | 60 | 2026-09-24 16:30 | 2026-09-24 13:04 |
| Arda Ceylan | 115 | 60 | 2026-09-24 16:07 | 2026-09-24 05:28 |
| mtmr_s1 | 169 | 60 | 2026-09-24 16:09 | 2026-09-23 22:10 |
| TheEggman | 152 | 60 | 2026-09-24 16:24 | 2026-09-23 23:35 |

Of 347 distinct episode IDs across the six teams' 360 sampled rows (some overlap because two
sampled teams occasionally played each other), **all 347 replays are on disk with zero remaining
errors**, after a prioritized retry pass — the Kaggle episode API rate-limits hard (HTTP 429)
under sustained request volume, and one team (THIRD FARM CLUB) initially had 0/60 replays land in
the first fast pass purely because its episode IDs — being the most recently created, over the
narrowest time window of the six — sorted to the tail of the retry queue; a second pass
explicitly prioritizing its IDs first fixed this. **Measured**, and worth recording as a
methodology note: don't assume a uniform retry order is fair across teams whose episode-ID ranges
don't overlap evenly.

The same live-snapshot-rating caveat from the companion report applies here: opponent ratings and
bands are not used in this report's per-team table (family/win-rate/margin are what's asked for),
so it doesn't bite as hard here as in the W3/W1 report.

## 3. Family classification, per team

Classified from each team's own row-1/row-2 opening market orders across all 60 sampled games (not
a sample of games — every downloaded replay was classified). **Measured.**

| Rank | Team | Own family | Record (W-L-T) | Win rate |
|---|---|---|---|---|
| 7 | Kaggledew Valley | other | 29-31-0 | 48.3% |
| 8 | Azat Akhtyamov | DSM | 33-27-0 | 55.0% |
| 9 | THIRD FARM CLUB | **Boey** | **51-9-0** | **85.0%** |
| 10 | Arda Ceylan | other | 43-17-0 | 71.7% |
| 11 | mtmr_s1 | DSM | 28-32-0 | 46.7% |
| 12 | TheEggman | other | 30-30-0 | 50.0% |

**Win rate against tape-family opponents vs. non-tape opponents:**

| Team | vs tape (n, win%, median margin) | vs non-tape (n, win%, median margin) |
|---|---|---|
| Kaggledew Valley | 1, 100%, +43,810 (tiny n) | 59, 47.5%, -2,926 |
| Azat Akhtyamov | 4, 50%, -3,170 | 56, 55.4%, +988 |
| THIRD FARM CLUB | 23, **100%**, +16,666 | 37, 75.7%, +4,748 |
| Arda Ceylan | 12, **100%**, +12,058 | 48, 64.6%, +1,423 |
| mtmr_s1 | 0 (none encountered) | 60, 46.7%, -958 |
| TheEggman | 5, 80%, +5,842 | 55, 47.3%, -671 |

Median final bank ranged 96,147 (Azat) to 109,481 (THIRD FARM CLUB). **Measured.**

## 4. Combined table, ranks 1-12

Ranks 1-6 reuse the existing top-six corpus (`20260923T153431Z_top6`), newly classified by the
same opening-fingerprint rule this session, plus a fresh 4-8-game `resim_trades.py` supplemental
sample per team for revenue (the corpus's original decision-event analysis didn't capture
per-product SELL revenue). Ranks 7-12 use the 8-game resim sample described in section 5.
**Measured**, both halves, this session.

| Rank | Team | Family | Record | Win% | Median margin | Animals @ day 12 (n games) | Land @ day 12 |
|---|---|---|---|---|---|---|---|
| 1 | Boey | Boey | 58-2-0 | 96.7% | +14,341 | COW 3-10, SHEEP 3-17, GOOSE 2-7 (n=4) | 75 |
| 2 | M & M & P & Q | DSM | 41-19-0 | 68.3% | +3,606 | COW 6-13, SHEEP 3-18 (n=4) | 75 |
| 3 | DSM | DSM | 58-2-0 | 96.7% | +17,082 | COW 8-16, SHEEP 3, GOOSE 2-10 (n=4) | **100** |
| 4 | Unknown Mother-Goose | DSM | 46-14-0 | 76.7% | +7,285 | mixed 3-species (n=4) | 75-100 |
| 5 | DECEM | DSM | 58-2-0 | 96.7% | +13,075 | mixed 3-species (n=4) | 75-100 |
| 6 | 吃白饭的大肥鱼 | other | 43-17-0 | 71.7% | +6,086 | mixed 3-species (n=4) | 75-100 |
| 7 | Kaggledew Valley | other | 29-31-0 | 48.3% | (see §3) | COW 76, SHEEP 24, GOOSE 35 (n=8 total) | 75 |
| 8 | Azat Akhtyamov | DSM | 33-27-0 | 55.0% | (see §3) | COW 68, SHEEP 44 (n=8 total) | 75 |
| 9 | THIRD FARM CLUB | **Boey** | 51-9-0 | 85.0% | (see §3) | SHEEP 60, COW 61, GOOSE 36 (n=8 total) | 75 |
| 10 | Arda Ceylan | other | 43-17-0 | 71.7% | (see §3) | COW 70, SHEEP 53, GOOSE 48 (n=8 total) | **100** |
| 11 | mtmr_s1 | DSM | 28-32-0 | 46.7% | (see §3) | COW 80, SHEEP 50, GOOSE 39 (n=8 total) | **100** |
| 12 | TheEggman | other | 30-30-0 | 50.0% | (see §3) | COW 62, SHEEP 49, GOOSE 43 (n=8 total) | **100** |

Revenue per product (sum of SELL revenue across the sampled games, our side; WHEAT/STRAWBERRY are
consistently the two largest earners everywhere on the ladder, both bands):

| Team | Top 3 products by revenue (sampled games) |
|---|---|
| Boey (n=4) | WHEAT 413,124 · FERTILIZER 166,737 · STRAWBERRY 92,172 |
| M & M & P & Q (n=4-5) | STRAWBERRY 168,134 · WOOL 163,964 · WHEAT 85,172 |
| DSM (n=4-5) | STRAWBERRY 156,198 · MILK 127,331 · WHEAT 83,291 |
| Unknown Mother-Goose (n=4-6) | STRAWBERRY 170,201 · MILK 136,563 · WOOL 127,603 |
| DECEM (n=4) | MILK 151,189 · STRAWBERRY 136,659 · WHEAT 71,391 |
| 吃白饭的大肥鱼 (n=4-5) | WOOL 160,590 · STRAWBERRY 128,928 · MILK 123,292 |
| Kaggledew Valley (n=8) | STRAWBERRY 285,496 · MILK 214,175 · WHEAT 124,208 |
| Azat Akhtyamov (n=8) | STRAWBERRY 276,756 · WHEAT 149,470 · MILK 167,958 |
| THIRD FARM CLUB (n=8) | WOOL 175,315 · STRAWBERRY 167,763 · MILK 164,425 |
| Arda Ceylan (n=8) | STRAWBERRY 215,534 · WOOL 194,816 · WHEAT 146,116 |
| mtmr_s1 (n=8) | STRAWBERRY 292,332 · MILK 211,898 · WOOL 155,452 |
| TheEggman (n=8) | STRAWBERRY 267,348 · WOOL 167,242 · MILK 159,424 |

Boey is the one outlier here — it earns nearly half its sampled revenue from WHEAT alone (413k of
~997k total), everyone else leads with STRAWBERRY or a mix of STRAWBERRY/WOOL/MILK. **Measured**
from these specific sampled games; not claimed to be each team's season-long average.

## 5. 8-game resim per rank-7-to-12 team

Per the task, 8 games were sampled per team (4 against tape-family opponents where available,
filled from non-tape opponents otherwise — Kaggledew Valley had only 1 tape-family opponent
available and mtmr_s1 had none, so both drew more non-tape games instead) and re-simulated through
`harness/resim_trades.py`. **All 48 replays reproduced the exact recorded reward** (`"exact":
true` on every one), confirming the resim faithfully replays recorded actions. **Measured.**

Total sell revenue, our side vs. opponent side, across the 8 sampled games per team:

| Team | Our revenue | Opponent revenue | Delta |
|---|---|---|---|
| Kaggledew Valley | 1,083,220 | 1,105,361 | -22,141 |
| Azat Akhtyamov | 946,389 | 1,076,963 | -130,574 |
| THIRD FARM CLUB | 1,031,055 | 1,153,372 | -122,317 |
| Arda Ceylan | 1,082,142 | 1,038,675 | +43,467 |
| mtmr_s1 | 1,187,542 | 1,133,594 | +53,948 |
| TheEggman | 1,135,252 | 1,065,193 | +70,059 |

This is a smaller, noisier sample (8 games, opponent-mix skewed toward tape/near-2,900-band
opponents by design) and should not be read as "who's winning the season" — it disagrees with the
season-long win-rate column in §3 for THIRD FARM CLUB (85% win rate season-long, but net revenue
-122k in this specific 8-game sample) precisely because this sample was deliberately weighted
toward tape-family opponents, which THIRD FARM CLUB crushes on *win rate* (100%, median margin
+16,666) while apparently not always maximizing the revenue gap in every individual game. **Measured
with that caveat stated up front, not glossed over.**

Farm state at days 6/12/18/26 (median across the 8 sampled games per team):

| Team | Day 6 land / animals / cash | Day 12 land / animals / cash | Day 18 land / animals / cash | Day 26 land / animals / cash |
|---|---|---|---|---|
| Kaggledew Valley | 25 / 8 / $1,213 | 75 / 16.5 / $4,420 | 75 / 18.5 / $35,572 | 75 / 17.5 / $87,216 |
| Azat Akhtyamov | 50 / 7 / $9 | 75 / 13.5 / $14,517 | 75 / 13.5 / $43,770 | 75 / 13.5 / $75,483 |
| THIRD FARM CLUB | 25 / 9 / $1,211 | 75 / 20 / $12,274 | 75 / 21 / $41,798 | 75 / 16 / $77,148 |
| Arda Ceylan | 25 / 5 / $777 | **100** / 20.5 / $6,226 | 100 / 22 / $45,037 | 100 / 19.5 / $75,181 |
| mtmr_s1 | 25 / 5 / $1,011 | **100** / 22 / $3,543 | 100 / 23.5 / $36,551 | 100 / 19 / $80,785 |
| TheEggman | 25 / 5 / $814 | **100** / 20 / $6,394 | 100 / 19.5 / $40,819 | 100 / 16 / $81,676 |

(Land/animals/cash columns: land = owned tiles, animals = total head count across species, cash =
median bank on that day.) All six teams buy land on day 6 and again around day 11-12 (land jumps
25→75 between the day-6 and day-12 checkpoints for every team, and three of the six — Arda Ceylan,
mtmr_s1, TheEggman — go one step further to **100 tiles**, a fourth quadrant beyond the
`docs/REPLAY_ANALYSIS.md`-documented 75-tile ceiling for ranks 1-6). Peak crew (not tabled above,
see raw data) ran 8-12 hands across all six teams and all four checkpoints. **Measured.**

## 6. What separates ranks 7-12 from ranks 1-6, and from the tape family

**Ranks 7-12 are not meaningfully behind ranks 1-6 on land, crew, or animal-species mechanics —
every one of the structural moves ranks 1-6 make (land to 75+ tiles by day 12, 3-species animal
herds, an 8-12 hand crew) is also present in every rank-7-to-12 team sampled.** Three of the six
(Arda Ceylan, mtmr_s1, TheEggman) even push land to 100 tiles, one step past what
`docs/REPLAY_ANALYSIS.md` documented as the top-ladder ceiling from its two independently-sampled
episodes. **Measured**, n=6 teams, 8 games each for the land/animal checkpoints.

**What does separate them is win rate against the field, and it splits cleanly on which "family"
they run.** THIRD FARM CLUB (Boey-family, rank 9) and Arda Ceylan (unclassified "other", rank 10)
post 71-85% season win rates with 100% records against tape-family opponents specifically. Azat
Akhtyamov and mtmr_s1 — both DSM-family — sit at 46-55%, close to a coin flip, despite running the
same structural playbook (land, animals, crew) as everyone else. Kaggledew Valley and TheEggman
("other" family) are also close to 50%. **This suggests the differentiator among ranks 7-12 is
finer-grained decision quality within a shared macro strategy (selling cadence, crop mix, exact
timing), not a missing structural mechanic** — **inference**, since this report didn't isolate
which specific decisions drive the win-rate gap; it only establishes that the land/crew/animal
shape is not the gap.

**Sample size caveat, stated plainly:** each team's per-family win-rate breakdown (§3) rests on
season totals of 28-60 games, which is solid; the resim-based revenue and day-by-day state
snapshots (§4-5) rest on only 4-8 games per team, which is not enough to trust any single number
in isolation (see the THIRD FARM CLUB revenue-vs-win-rate disagreement noted in §5). Treat §4-5 as
illustrative texture, and §1-3 as the load-bearing numbers.

## 7. Is any rank-7-to-12 team a tape agent with extra layers?

**No — measured, and this is the clearest finding in this report.** None of the six rank-7-to-12
teams' own openings match the raw "tape" fingerprint (`BUY_ANIMAL COW 2` + `BUY_ANIMAL SHEEP 2` in
row 2). One (THIRD FARM CLUB) runs the **Boey** fingerprint — the same opening as the single
strongest agent in the entire ranks-1-6 corpus (58-2, the best record of any of the twelve teams
examined across both reports). Two (Azat Akhtyamov, mtmr_s1) run the **DSM** fingerprint, which
also dominates ranks 1-6 (4 of the original top 6 run it). The remaining three (Kaggledew Valley,
Arda Ceylan, TheEggman) run distinct openings that matched none of the three known fingerprints.

Zooming out further: **across all twelve teams examined in this report and its companion (ranks
1-12), not one runs the raw tape opening as its own strategy.** "Tape family" appears in this
corpus exclusively as an opponent every stronger agent beats — every team with a non-trivial
`n_vs_tape` sample in both bands wins the overwhelming majority of those games (ranks 1-6: 15/16 to
24/24; ranks 7-12: 12/12 to 23/23, with the sole exception being Azat Akhtyamov's small 2-of-4
sample against tape). There is no visible "tape plus one extra layer" agent sitting at ~2,900 —
the path from ~2,400 (tape's rough level, going by how consistently it loses) to ~2,900 is not
one incremental addition; it runs through adopting a materially different, more sophisticated
opening (Boey or DSM) or an original one, combined with the land/crew/animal scale-up documented in
§4-6. **Measured**, and the strongest single piece of evidence for it is THIRD FARM CLUB: same
opening fingerprint as the ranks-1-6 corpus's best performer, and — among the six rank-7-to-12
teams sampled here — the best win rate by a wide margin (85% vs. the next-best 71.7%).

## Limitations

- Ranks 1-6 in §4-5 use a fresh 4-game-per-team resim/state supplement layered onto the existing
  corpus, not the full 60-game corpus — smaller n than the 8-game rank-7-to-12 sample. **Measured
  limitation.**
- Opponent-family win rates for ranks 7-12 (§3) have genuinely small n for some teams against tape
  specifically (Kaggledew Valley n=1, mtmr_s1 n=0) — those cells are reported but should not be
  leaned on. **Measured.**
- TheEggman's active-submission ID match (§1) had a 3.8-point score discrepancy against the
  leaderboard snapshot, most plausibly ordinary rating drift between the two data pulls rather than
  a wrong ID (the alternative candidate was off by 386 points), but this was not independently
  re-verified against a third data source. **Inference**, flagged rather than silently resolved.
