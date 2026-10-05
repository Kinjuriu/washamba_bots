# Fresh top-6 Kaggriculture replay corpus: decision report

**Corpus:** `/Users/stephanengugi/KagricultureLocalData/episodes/20260923T153431Z_top6/`
**Leaderboard snapshot retrieved:** 2026-09-23T15:34:31Z
**Analysis performed:** 2026-09-23

> **Naming note.** The task title says "top seven leaderboard teams," but every other
> instance in the same task (§2 header, the requested folder name `_top6`, "six worked
> branch examples" in the deliverables list) says **top six**. I resolved this as
> **top 6** on the consistent majority signal rather than silently guessing — flagging
> it here instead of picking one convention without telling you.

---

## 1. Who we downloaded, freshness, completeness

Leaderboard pulled via `kaggle competitions leaderboard kaggriculture -s --csv`
and cross-checked against Kaggle's internal `ListEpisodes` `teams` payload
(`publicLeaderboardSubmissionId`) to resolve each team's **currently active**
submission — not the newest submission, not last week's hardcoded IDs.

| Rank | Team | Rating | Team ID | Active submission |
|---|---|---|---|---|
| 1 | Boey | 3098.2 | 16915014 | 56484772 |
| 2 | M & M & P & Q | 3059.5 | 16681125 | 56464621 |
| 3 | DSM | 3056.7 | 16732748 | 56489014 |
| 4 | Unknown Mother-Goose | 3045.1 | 16730612 | 56478145 |
| 5 | DECEM | 3026.6 | 16623559 | 56489091 |
| 6 | 吃白饭的大肥鱼 | 3005.8 | 16854176 | 56483899 |

Only **DSM** and **Unknown Mother-Goose** survive from the previous (2026-09-21)
hardcoded `TOP5`; Majkel1337, ymg_aq and Vadim Vasilenko have all fallen out of
the current top 6. Reusing the old IDs would have pulled two stale/wrong teams.

**Sample per team:** up to 60 most recent **completed, public** ladder episodes.
Kaggle's `ListEpisodes` tags every episode `type`; exactly **one** episode per
submission carried `EPISODE_TYPE_VALIDATION` (Kaggle's own submission-validation
self-play run — confirmed live to also be the one episode with the same `teamId`
on both seats) and was excluded, reported per team below. No episode was
excluded for `state != COMPLETED`.

| Team | API returned | excluded (validation) | competitive available | selected | shortfall |
|---|---|---|---|---|---|
| Boey | 96 | 1 | 95 | 60 | 0 |
| M & M & P & Q | 170 | 1 | 169 | 60 | 0 |
| DSM | 88 | 1 | 87 | 60 | 0 |
| Unknown Mother-Goose | 120 | 1 | 119 | 60 | 0 |
| DECEM | 93 | 1 | 92 | 60 | 0 |
| 吃白饭的大肥鱼 | 99 | 1 | 98 | 60 | 0 |

All six teams reached the full 60/60 — no shortfall, no need to mix in an older
submission. **Freshness:** every team's 60-episode window is entirely within the
last 24 hours of the snapshot time (60/60 `within_24h` for all six); oldest
episode in the whole sample is `2026-09-22T22:57:33Z` (M & M & P & Q), newest is
`2026-09-23T15:34:28Z` (Unknown Mother-Goose, seconds before the snapshot).

**Manifest freeze.** `manifest.csv` (360 rows) is written to disk in full
*before* any replay download begins, and the download loop re-reads episode
IDs from that file on disk (never from in-memory state), so a mid-run
leaderboard change cannot silently change what gets downloaded. This fixes the
297→270-style drift noted from the previous pull: that drift happened because
an earlier session ran `--manifest-only` and a full download in two separate
invocations, and `list_episodes` was called again on the second pass, days
later, against a leaderboard that had moved. This run calls each submission's
episode list exactly once, in one process, and downloads strictly from what
that one call produced.

**Trajectories vs unique episodes.** 360 target-player trajectories (6 teams ×
60), but only **337 unique episodes** — 23 episodes are two of our six targets
playing each other, downloaded once and kept as two manifest rows (one per
seat), per spec.

**Download.** 337/337 unique replays downloaded, **0 failures**, 0 cached
(fresh directory), 195.4 MB compressed on disk
(`/Users/stephanengugi/KagricultureLocalData/episodes/20260923T153431Z_top6/replays/`).
Each file went through: stream to `.part` → structural validation (non-empty
`steps`, `configuration` present, terminal rewards present) → gzip → gzip
re-validated by reading it back → atomic rename. Seat index: this project's
existing `build_manifest_rows`-equivalent logic (reused unmodified) looks up
each agent by `submissionId` first and only reads `.get("index", 0)` *after*
confirming that agent object exists — a missing agent is skipped and logged,
never silently coerced to seat 0. Zero episodes were skipped this run
(`logs/malformed_episodes.log` is empty).

**Old corpus** (`~/KagricultureLocalData/episodes/manifest.csv`, `replays/`,
2026-09-21) is untouched — nothing in this run wrote into it. (In the course
of validating this pipeline against it, I confirmed the previous corpus is the
already-drifted **270**-unique-episode version the task describes, not 272.)

---

## 2. Replay format verification (before trusting anything else)

Read `kaggle_environments/core.py::Environment.step`/`__loop_through_interpreter`
and `envs/kaggriculture/kaggriculture.py::interpreter`, then checked the claim
empirically against a real replay (`verify_replay_format.py`, run against
`111409601.json.gz`, a replay from the old corpus with a real `BUY_LAND` order
to test against).

**Result, stated precisely, since earlier internal reports here disagreed
about this:**

- `steps` is a flat list, **0-indexed**, one entry per engine turn.
  `steps[t][seat]["observation"]["step"] == t` for every t (spot-checked at
  t=0,1,2,100,719 across the season — exact match, no drift).
- **`steps[t][seat]["action"]` is the action the agent chose using
  `steps[t-1][seat]["observation"]` as input** — the interpreter feeds the
  *previous* state's observation into `_apply_unit_action` together with the
  newly-submitted action.
- **`steps[t][seat]["observation"]` is the state *after* that action (and
  that turn's market/town/decay ticks) resolved** — i.e. it is simultaneously
  "the result of the action recorded at `t`" and "what the agent will see
  before choosing the action recorded at `t+1`."
- Empirical proof: seat 0 in episode 111409601 issued `BUY_LAND` in the action
  recorded at step 150. Tile count at `steps[149]` (prior row) = 25. Tile
  count at `steps[150]` (**same row as the order**) = 50. It does **not** wait
  until `steps[151]`. This settles the same-row-vs-t+1 question this repo has
  gone back and forth on: **the causal input is the prior row; the causal
  result is the same row.**
- `steps[0]` is the reset/initial state (day 0, hour 0); its `action` field is
  a schema-filled `{'farmer': ['PASS'], 'hands': [], 'market': []}` for both
  seats, not a real decision — there is nothing "before" it.
- Terminal row: `steps[-1][seat]["reward"]` is the final bank, set by the
  engine once `step >= episodeSteps - 2`; `status` is `DONE` on both seats
  in every one of the 337 replays we downloaded (checked as part of the
  structural-validation gate on every file).

**Every extraction in this report follows this rule**: a "decision" at step
`t` is described using `steps[t-1]` as the pre-decision state and
`steps[t]`/onward as the result and its consequences. `checkpoint_states.jsonl`
(the day-boundary timeline sample) is the one place that intentionally uses
`steps[t]`'s own observation for a state snapshot rather than a decision's
pre-state — documented in the file and in `stage_a_summary.py`'s docstring,
so it can't be confused with the causal pairing.

**Public vs private observation fields**, confirmed against `kaggriculture.json`'s
own schema (`"shared": true/false`) and a live replay's key set: `obs["farms"]`
(tiles, money, farmer/hand positions, `unlocked_quadrants`, `hires_today`) is
**public/shared** — visible for both seats, opponent included. `obs["private"]`
(shed inventory, seed counts) is **per-agent only**. Every "opponent" field
used anywhere in this report and in the extraction scripts reads only from
`farms`/`market`/`town`; the opponent's own `private` block is never read even
though the replay file (an admin dump) technically contains it for both seats.

**Midnight/crew trap, checked directly.** Hands vanish at midnight and are
re-hired daily (per this repo's own documented Atlas mistake). A raw
hour-0 snapshot at day 6 shows `crew: 1` (farmer only) in essentially every
trajectory — that is not "no hired workers," it's the reset instant before
that day's hiring lands. All crew claims in this report use **peak crew for
the day** (`crew_by_day`, the max hand-count observed across all 24 hours of
that day), never the hour-0 instant.

**Bug caught and fixed during this run, worth recording.** The first pass of
`stage_a_summary.py`'s tile scan excluded `None` tiles (empty-but-owned,
tillable land) from the "land" count, counting only *occupied* tiles. That
produced a nonsensical result — land appearing to *shrink* late-season as
harvested/ongoing-crop tiles emptied out. Caught by directly re-deriving tile
counts from the raw replay and comparing against `unlocked_quadrants`, which
is unambiguous ground truth. Fixed (`land` now = every non-`"LOCKED"` tile,
whether or not it currently holds anything) and the entire pipeline was
re-run before any of the numbers below were computed. This is exactly the
kind of check §4 of the task asked for, and it would have quietly corrupted
every land-timing claim in this report if skipped.

---

## 3. Most common economic decisions, with counts and denominators

Computed across all 360 target-player trajectories (`decision_events.csv`,
2151 rows) and the full-season action histograms in `episode_summaries.jsonl`.

**BUY_LAND (first extra-quadrant purchase): near-universal, and clustered
almost exactly on the day-6 boundary.**

| First BUY_LAND day | trajectories (of 360) |
|---|---|
| day 4 | 18 (5.0%) |
| day 5 | 30 (8.3%) |
| **day 6** | **312 (86.7%)** |

360/360 trajectories bought land at least once (0 shortfall — every single
game in the sample expands past the starting 25 tiles). The engine's own
`LAND_PRICES = [1000, 2000, 4000]` for `LAND_ORDER = ["NE", "SW", "SE"]`
(read from the installed `kaggriculture.py`) means a third extra quadrant
(100 tiles total) is mechanically available — **no trajectory in this
360-game sample ever bought it.** Every one of the six teams stops at 25→50→75
tiles (two extra quadrants: NE then SW). This matches, and now directly
confirms with fresh data, the "every strong player buys land exactly twice"
finding already recorded in this repo's `docs/REPLAY_ANALYSIS.md`.

**Animals: COW + SHEEP + GOOSE, bought by every team in (almost) every game.**

| Team | COW | SHEEP | GOOSE | n |
|---|---|---|---|---|
| Boey | 60/60 | 60/60 | 60/60 | 60 |
| M & M & P & Q | 60/60 | 60/60 | 60/60 | 60 |
| DSM | 60/60 | 60/60 | 60/60 | 60 |
| Unknown Mother-Goose | 60/60 | 60/60 | 60/60 | 60 |
| DECEM | 60/60 | 60/60 | 58/60 | 60 |
| 吃白饭的大肥鱼 | 60/60 | 60/60 | 60/60 | 60 |

COW and SHEEP are bought on **day 0** on average across every single team
(`animal_species_first_day_mean` = 0.0 for both, in every team) — i.e. in the
opening turns of the game, before any land purchase, before any real crop
income. GOOSE is bought later and its timing is the one place teams diverge:
Boey buys it ~day 2, M & M & P & Q ~day 1, while DSM/DECEM/吃白饭的大肥鱼/
Unknown Mother-Goose buy it ~day 7–8 (after the land purchase, once cash is
flowing again). This is a genuine strategic split among otherwise
near-identical builds — earlier GOOSE ties up cash during the day-3-7 trough;
later GOOSE waits it out.

**Peak crew.** Median across teams: 12–14 hands+farmer, max observed 15
(matches this repo's own `docs/ROADMAP.md`/`REPLAY_ANALYSIS.md` figure of
12–15-unit crews). `吃白饭的大肥鱼` and `DSM` run the densest crews (median
14); `M & M & P & Q` and `Unknown Mother-Goose` the leanest (median 12).

**Cash trough, days 3–7 (min daily-open money in that window):**

| Team | mean trough | mode day |
|---|---|---|
| Boey | **$3.3** | day 3 |
| DSM | $6.0 | day 3 |
| DECEM | $12.7 | day 3 |
| Unknown Mother-Goose | $13.4 | day 3 |
| M & M & P & Q | $25.6 | day 4 |
| 吃白饭的大肥鱼 | $46.9 | day 3 |

All six run the trough down close to zero by design — this is not a mistake,
it's the shared meta (spend everything on the animal/land/hire ramp, then
recover on the day-6 land purchase's aftermath). Boey runs the tightest margin
of the six and has the best record; 吃白饭的大肥鱼 (rank 6 of the six) leaves
the most slack. Directionally consistent with, but not proof of, "tighter
cash discipline correlates with a better record" — sample of six teams, many
confounds (see §8).

**Dominant crop shifts (day 3 → day 9):** 353/360 trajectories (98.1%) change
their single most-planted crop between day 3 and day 9 — essentially
universal. The typical shift is WHEAT (or an early STRAWBERRY/MELON split)
early → STRAWBERRY or MELON dominant once land/crew capacity increases.

**Selling cadence (mean *requested* SELL orders/day by season phase — requested,
not confirmed executed volume):**

| Team | d0–2 | d3–7 | d8–14 | d15–21 | d22–29 |
|---|---|---|---|---|---|
| **Boey** | **43.5** | **70.7** | **116.0** | **146.1** | **147.1** |
| DSM | 4.2 | 6.2 | 12.2 | 19.6 | 28.4 |
| DECEM | 4.5 | 6.1 | 14.1 | 24.2 | 34.8 |
| Unknown Mother-Goose | 5.4 | 5.9 | 8.6 | 14.0 | 20.0 |
| M & M & P & Q | 4.6 | 7.5 | 9.3 | 13.9 | 18.1 |
| 吃白饭的大肥鱼 | 1.7 | 4.5 | 6.2 | 8.1 | 11.1 |

Boey (rank 1, 58-2 record in this sample) is not just a little more aggressive
than the field — it issues **5–13× more SELL orders per day than every other
top-6 team, from the very first two days of the season onward.** This is the
single sharpest behavioral outlier in the whole corpus. §7 shows exactly how
this connects to Boey's near-zero cash trough (many small sells recover cash
fast) and §6 flags it as the most concrete, evidence-backed idea worth testing
on our own agent.

---

## 4. Six worked branch examples

All six center on the **day-6 land purchase**, because §3's data shows that's
where 86.7% of trajectories actually make their marked economic move near
turn 144 — not an assumption forced onto the data; four of six teams' land
purchase itself lands within a few turns of 144, and the other two (Boey,
M & M & P & Q in some games) hit an equally sharp **cash-trough** event
exactly at step 144 that resolves into the same land purchase a few turns
later. Category labels use the task's A/expand/C schema.

### 4.1 — M & M & P & Q (rank 2), episode `112194936`, seat 1

**Turn 144 (day 6, hour 0).** Pre-state: `$13 cash, 25 land, peak crew 7,
crops {STRAWBERRY:10, WHEAT:7, MELON:9}, animals {COW:4, SHEEP:2}`. Opponent
(吃白饭的大肥鱼, public fields): `$1051, 25 land`, similar crop mix.

Action at 144: `PASS`/`WATER` only — cash too low to do anything else.
**t145:** 9× `HIRE` orders queued (day's crew ramp). **t148:** `SELL WOOL x6`
lands, cash jumps $1→$1304. **t149–153:** a burst of `BUY_ANIMAL SHEEP` (5
orders in 9 turns — this team buys SHEEP in bulk rather than one at a time)
plus `BUY_LAND`, `BUY_ANIMAL`, `PLACE FERTILIZER`. By day 9, SHEEP count is
already 11 (vs. the field's typical 2–3). **Category: B (expand the existing
line) + C (crop-mix shift toward STRAWBERRY over the next 10 days: 10→43
units by day 18, while WHEAT and MELON shrink).**

Result: land 25→75 by day 8–9 via two orders; final bank **$113,051** vs.
opponent **$108,768** — a win, margin +4,283 (close).

**Contrast — same submission, different timing (`112260929`, seat 1).** Here
the same team's first `BUY_LAND` attempt fires at **step 106 (day 4)**, six
BUY_LAND orders in a row (steps 106–116) while cash ($787–946) sits below the
$1000 quadrant price and each order simply no-ops — the purchase only lands
once cash crosses $1000 around day 5. Land timing bucket comparison across
this team's 60 games: **day ≤4 first-purchase, n=18, win rate 61%** vs.
**day 5–7 ("normal"), n=42, win rate 71%.** BUY_LAND-order-count comparison:
**≤4 orders/game, n=10, win rate 80%** vs. **>10 orders/game (the repeated-retry
pattern), n=21, win rate 67%.** Both gaps are directional, not dramatic, and
confounded by opponent strength (see §8) — this is the one team of the six
that shows this "spam BUY_LAND before affordable" pattern at all; every other
team's order count tops out at 7. *Inference, not proof:* the redundant
orders themselves cost nothing extra (the engine just no-ops an unaffordable
`BUY_LAND`, it doesn't burn the 10-orders/turn budget meaningfully since only
1 order is queued most of those turns) — the real signal is that this team's
land-timing is simply more variable than its five peers, and the variable
tail correlates with a slightly worse outcome.

### 4.2 — Unknown Mother-Goose (rank 4), episode `112307319`, seat 0

**Turn 150 (day 6, hour 6).** Pre-state (from `steps[149]`): `$885, 25 land,
crew 9, crops {STRAWBERRY:10, MELON:10}, animals {COW:2, SHEEP:3}`. This
pre-state — cash in the $850–2150 band, 25 land, 8–9 crew, a 10/10
STRAWBERRY/MELON split, COW:2/SHEEP:3 — is **the near-universal day-6
template** shared by DSM, DECEM and Unknown Mother-Goose alike (§4.3, §4.4,
§4.5 below land on almost the same numbers independently). Action: farmer
walks, hands work fields, market issues `SELL WOOL` + `BUY_LAND`. Land 25→50
the same turn. **Category: A (continue) into B (expand)** — no crop-mix or
animal-species change accompanies this purchase; it's a pure capacity buy.

Result: final bank **$151,846** vs. opponent (QQ农场, not one of the six
targets) **$128,863** — the best single outcome of any of the six worked
examples in this report.

**Contrast — same submission, loss (`112413080`, vs. DSM, seat 0).** Same
day-6 land purchase (step 150), same template pre-state. Final: **$114,720**
vs. DSM's **$121,026** — a near-tie loss (margin -6,306) against another
top-6 team running the identical branch. The economic *decision* was the
same; the outcome flip here is not explained by a different branch at day 6
— see §8's execution-vs-plan discussion.

### 4.3 — 吃白饭的大肥鱼 (rank 6), episode `112364025`, seat 1

**Turn 149 (day 6, hour 4).** Pre-state: `$873, 25 land, crew 9`, the same
STRAWBERRY:10/MELON:10, COW:2/SHEEP:3 template. Action bundles `SELL WOOL`,
`BUY_LAND`, and (uniquely among the six primary examples) **two `BUY_SEED`
orders in the same turn** (`STRAWBERRY x10`, `WHEAT x3`) — this team pre-buys
seed stock at the same moment it buys land, rather than letting the
seed-restock rule fire reactively later. Land 25→50 that turn.
**Category: A continue, with a B-adjacent seed-stockpile top-up.**

Result: final **$96,700** vs. opponent (qianqiuwushang) **$77,087**, a win.
This team is the single most disciplined of the six on land-order count:
**60/60 of its games use exactly 2 `BUY_LAND` orders, always landing on day
6** — zero variance, the tightest execution of any team measured.

**Contrast — same submission, loss (`112369884`, vs. DECEM, seat 0).**
Nearly identical pre-state (`$864` vs. `$873`) and identical day-6 land
timing. Final: **$87,662** vs. DECEM's **$92,662** — again a near-tie loss
against another of the six targets, with the branch itself unchanged.

### 4.4 — Boey (rank 1), episode `112395923`, seat 0

**Turn 144 (day 6, hour 0) — the sharpest cash-trough moment measured in the
whole corpus.** Pre-state: **`$0.00` cash**, 25 land, crew 6, crops
`{MELON:10, STRAWBERRY:5}`, animals `{COW:6, GOOSE:2, SHEEP:2}`. Action at
144: pure movement (`EAST`), no market orders possible — literally nothing to
spend. **t145:** `HARVEST` + `SELL WHEAT x3` + **9× `HIRE`** lands, cash
$0→$10. **t146:** `SELL WOOL x6` + `BUY_LAND` → cash $61, land 25→**50** in
the same turn. **t148–150:** a run of small `SELL`/`BUY_PRODUCT WHEAT` pairs
(this team's signature — many small orders, not a few big ones) takes cash
$48→$861→$726 across three turns. Land reaches 75 by day 9.
**Category: A continue → B expand, funded turn-by-turn rather than from a
cash buffer.**

Result: final **$125,828** vs. opponent (Yannik Schiffner) **$110,504** — a
win, and this team's day-0-through-2 SELL cadence (43.5 orders/day, §3) is
already running at 5–25× every other team's before this trough is even hit.

**Contrast — same submission, loss (`112411520`, vs. 吃白饭的大肥鱼, seat 1).**
Same $0–3 trough at step 144, same land-buy pattern. Final: Boey **$136,286**
— its *second-highest* bank of the four Boey games sampled here — but
吃白饭的大肥鱼 banked **$150,952**, so Boey still lost. **This is the clearest
evidence in the corpus that final-bank magnitude alone doesn't determine
win/loss** — Boey played a strong game by its own standard and lost to an
opponent (itself one of our six targets) that played a stronger one.

### 4.5 — DSM (rank 3), episode `112418188`, seat 1

**Turn 150 (day 6, hour 5).** Pre-state: `$2111, 25 land, crew 9`, the same
template as §4.2–4.3. `BUY_LAND` lands the same turn. **Category: A continue.**

Result: final **$104,543** vs. opponent (Gemini IS ALL YOU NEED) **$87,912** — a win.
DSM's land-order-count distribution is the tightest after 吃白饭的大肥鱼's:
46/60 games use exactly 3 orders (one more than the "minimum" 2 — the third
is very likely a rejected/no-op attempt at the $4000 third quadrant, never
actually affordable inside 30 days at this spend rate, though this is
inferred from the count pattern rather than directly traced turn-by-turn for
every game).

**Contrast — same submission, loss (`112499720`, vs. Boey, seat 0).** Same
day-6 branch. Final: DSM **$97,872** vs. Boey **$100,556** — the closest
margin of any pairing in this report (-2,684), and notably: DSM's two losses
in the entire 60-game sample are **both against the other two of our six
targets** (吃白饭的大肥鱼 and Boey) — DSM is undefeated in this sample against
every opponent outside the six.

### 4.6 — DECEM (rank 5), episode `112424118`, seat 0

**Turn 150 (day 6, hour 5).** Pre-state: `$708, 25 land, crew 9`, template
match. `BUY_LAND` lands the same turn. **Category: A continue.**

Result: final **$91,097** vs. opponent (Paing) **$63,173** — a comfortable
win.

**Contrast — same submission, loss, target-vs-target (`112424162`, vs. DSM,
seat 1).** This is the sharpest state-match in the whole corpus: at
`steps[149]`, DECEM shows `$1968, 25 land, crew 9, {STRAWBERRY:9, MELON:11},
{COW:2, SHEEP:3}` and DSM (opponent, public fields) shows `$1917, 25 land,
crew 9, {STRAWBERRY:10, MELON:10}, {COW:2, SHEEP:3}` — **effectively the same
farm, one turn from the same decision.** Both buy land the same turn. Final:
DECEM **$90,438** vs. DSM **$94,672** (margin -4,234). With the day-6 branch
this close to identical, the outcome gap here is decided by execution in the
following ~23 days (selling cadence, exact hire timing, crop-mix
micro-choices), not by a different choice at the branch point — see §8.

---

## 5. What changed from the previous corpus (only where comparable)

The 2026-09-21 corpus targeted a materially different team set (DSM,
Majkel1337, ymg_aq, Unknown Mother-Goose, Vadim Vasilenko). Only DSM and
Unknown Mother-Goose carry over, so cross-corpus comparison is limited to
those two, and even then the *opponent field* differs (the current corpus's
360 games face today's ladder, not the 2026-09-21 field), so any bank/win-rate
delta below is confounded by opponent-strength drift and should be read as
context, not a clean A/B:

| | old corpus (2026-09-21, DSM) | new corpus (2026-09-23, DSM) |
|---|---|---|
| n | 60 | 60 |
| win rate | 100% (0 losses) | 96.7% (2 losses — both vs. Boey/吃白饭的大肥鱼, teams not in the old top-5 sample) |
| mean bank | 111,804 | 112,998 |

The qualitative picture — universal COW+SHEEP+GOOSE, day-6 land purchase,
12–14 peak crew — reproduces across both corpora for DSM and Unknown
Mother-Goose, which is a useful cross-check that this isn't an artifact of
one snapshot: the same submission plays the same recognizable strategy two
days apart. The old corpus's manifest count (270 unique episodes from a
notional 272) is the exact drift this task asked me to check for; §1
explains the mechanism and confirms this run's manifest doesn't reproduce it.

---

## 6. Modifications worth investigating on our own agent

All three are tied to concrete replay evidence above, not general intuition.

**1. Selling cadence: many small orders, started from day 0, not a
threshold-triggered ramp.** Boey (rank 1, 58-2 in this sample) issues
5–13× more SELL orders per day than every other top-6 team from day 0
onward (§3), and its cash trough is the tightest of the six ($3.3 mean)
without ever starving (§4.4's per-turn trace shows a `SELL`→cash-recovery
cycle repeating every 1–2 turns through the trough). This repo's own
`main.py` sells on a threshold/liquidation-day schedule, and CLAUDE.md
records two prior attempts at a *continuous urgency ramp* that both lost
decisively (`sell-or-hold cadence model`, twice). Boey's pattern is
different from what was tried: not a smoother price-based ramp, but **flat
high-frequency small-order selling from turn 0**, which is closer to the
already-documented "spread large sells rather than dumping them" guidance
in CLAUDE.md's own mechanics section, just pushed much further and much
earlier than our agent currently does. Worth a narrowly-scoped test: raise
sell-order frequency/reduce per-order size specifically in the opening
days, independent of the urgency-ramp machinery that already failed twice.
*Counterfactual value not estimated — this needs a `paired_compare.py` or
`head_to_head.py` run, not just replay reading, to know if it actually
helps our agent's specific cost structure.*

**2. GOOSE purchase timing is a real, load-bearing split among top teams,
not a single "right" answer.** Boey and M & M & P & Q buy GOOSE almost
immediately (day 1–2); DSM/DECEM/吃白饭的大肥鱼/Unknown Mother-Goose wait
until day 7–8, after the land purchase. Both groups include both winners and
one loser of the six. This repo's own `ACTIVE_ANIMALS` currently doesn't run
GOOSE at all (`["SHEEP", "COW"]` per CLAUDE.md) — the corpus shows GOOSE at
100% adoption (58–60/60) across all six top teams, which is a stronger,
fresher signal than the existing docs anticipated. Since CLAUDE.md already
has a documented, carefully-reasoned rejection of a second SHEEP specifically
because of days-3–7 cash starvation, and this same window is exactly where
the early-GOOSE teams choose to spend, the timing question (day-1 vs. day-7
GOOSE) looks like the right next experiment, not just "add GOOSE."
*Counterfactual value not estimated.*

**3. Don't queue BUY_LAND before affordability is confirmed.** §4.1's
contrast example shows one team (M & M & P & Q, the weakest-by-win-rate of
the six) repeatedly queuing `BUY_LAND` for 6+ consecutive turns while cash
sits below the $1000 threshold, and that team is also the only one of the six
whose land-purchase timing is meaningfully bimodal (day ≤4 vs. day 5–7) with
a measurable (if modest, confounded) win-rate gap between the two. This
doesn't cost anything mechanically (an unaffordable order just no-ops), but
it's a tell that the team's land-purchase trigger isn't cash-gated the way
the other five teams' evidently is. Worth checking our own `decide_land_orders`
already gates on affordability before ever emitting the order (skimmed, not
deep-verified as part of this task) rather than relying on the engine's
silent rejection.

---

## 7. Unresolved questions and proposed counterfactual tests

- **Why does the near-identical DECEM/DSM branch in §4.6 diverge by turn
  720?** The day-6 states are within noise of each other; the ~4,200-bank
  gap must come from the following ~23 days. Smallest test: replay both
  `112424118`/`112424162`-style games' post-day-6 action streams side by
  side turn-by-turn (not done in this pass — this report used day-granularity
  sampling after the branch point, not a full per-turn diff) to isolate
  whether it's selling cadence, hire timing, or crop-mix micro-choices.
- **Does the GOOSE-timing split (§6.2) actually cause the outcome
  difference, or is it correlated with something else (e.g. which teams
  happen to draw easier opponents)?** Not separable from this observational
  corpus alone — win rates for the two GOOSE-timing groups are confounded by
  which specific opponents each team's 60 games happened to draw. Smallest
  counterfactual: on our own agent, run `paired_compare.py` with GOOSE
  purchase gated at day 1 vs. day 7, same seed set, same opponent.
- **Is the third land quadrant (`SE`, $4000) ever worth it?** Zero
  occurrences in 360 games across six top teams strongly suggests no, but
  this corpus can only show what these six agents chose, not what a
  fourth-quadrant purchase would have returned. If a fixed-opponent replay
  tape were used to test this, it could not reproduce how the real opponent
  would adapt to a policy change — so this needs a live `bptk.py` or
  `selfplay_bench.py` test on our own agent, not a replay-tape simulation.
- **Boey's sell-cadence outlier (§3, §6.1): correlation or the actual reason
  for its rank-1 position?** Boey also has the tightest cash trough and
  densest early hiring; these are entangled, not isolated variables, in the
  observational data. Smallest test: A/B just the sell-order frequency
  (holding everything else fixed) on our own agent via `paired_compare.py`.

---

## Files in this corpus

- `leaderboard_snapshot.json` — frozen leaderboard read + resolved targets
- `manifest.csv` — 360 frozen trajectory rows / 337 unique episodes
- `teams.json` — team name → id → active submission map (all teams seen, not just the six)
- `fetch_stats.json` — per-team freshness/exclusion accounting (§1)
- `replays/<episode_id>.json.gz` — 337 files, 195.4 MB total
- `download_results.json` — per-episode download status
- `checkpoint_states.jsonl` — 3,960 rows: one per (episode, player, checkpoint step ∈ {0,24,48,72,144,216,288,432,576,696,terminal})
- `decision_events.csv` — 2,151 rows: BUY_LAND, first-BUY_ANIMAL-per-species, cash-trough-min, dominant-crop-shift events with pre-state
- `episode_summaries.jsonl` — full per-trajectory working data (checkpoints + full action histograms); source for everything above
- `aggregate_stats.json` — per-team rollups behind §3's tables
- `candidate_examples.json` — the nearest-to-turn-144 event per team, used to select §4
- `fresh_top6_decision_report.md` — this file

**Report location:**
`/Users/stephanengugi/KagricultureLocalData/episodes/20260923T153431Z_top6/fresh_top6_decision_report.md`
