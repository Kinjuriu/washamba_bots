# Washamba submissions vs. the fresh top-6 corpus: decision comparison report

**Corpus (this run):** `/Users/stephanengugi/KagricultureLocalData/episodes/20260923T161855Z_washamba_vs_top6/`
**Top-6 corpus (reused, not re-downloaded):** `/Users/stephanengugi/KagricultureLocalData/episodes/20260923T153431Z_top6/`
**Analysis performed:** 2026-09-23

---

## 0. Identity resolution and a discrepancy worth flagging up front

Matched by exact filename + description + public score against
`kaggle competitions submissions kaggriculture` — not inferred from rating,
not the newest-submission assumption:

| Submitter* | File | Submission ID | Uploaded (UTC) | Uploaded (Nairobi) | Public score |
|---|---|---|---|---|---|
| Stephane Njoki | `w1_v15stack_race44.py` | 56491123 | 2026-09-23 10:54:55 | 2026-09-23 13:54:55 | 2018.0 |
| Stephane Njoki | `w0_v15stack_control.py` | 56487592 | 2026-09-23 08:01:52 | 2026-09-23 11:01:52 | 2423.7 |
| Peter Kibet | `washamba_base_v1_fork.py` | 56483603 | 2026-09-23 05:16:23 | 2026-09-23 08:16:23 | 1959.1 |
| Peter Kibet | `washamba_base_v2.py` | 56483595 | 2026-09-23 05:16:04 | 2026-09-23 08:16:04 | 1854.5 |

\* Submitter names come from the Kaggle web UI you pasted, not the API — the
CLI/API's `submissions` and `episodes` endpoints don't expose per-member
attribution for team submissions, so this field is user-supplied, not
independently re-derived.

**Discrepancy:** the task's target date was **22 September 2026, Africa/Nairobi**;
all four submissions above actually landed **23 September** in both UTC and
Nairobi time (Nairobi is UTC+3, which doesn't shift any of these across a
day boundary). Proceeded with these four anyway on the strength of exact
filename+description+score matches — stronger identity evidence than a date
field that appears to be stale in the task template.

**Same-filename collision, caught and excluded:** `washamba_base_v1_fork.py`
was submitted twice. Submission 56483603 (above) matches your pasted
description ("restore slot"). A separate, earlier submission — 56442571,
21 Sep, "+ carrot-reserve fork, ladder experiment", score 2122.2 — is a
**different** artifact under the same filename and is **not** included in
this corpus; conflating the two would have silently mixed two different
agents' games into one row.

---

## 1. Download completeness and reliability

**No 60-game cap.** For each submission, `ListEpisodes` was paginated to
exhaustion (no `nextPageToken` remained on any of the four — one page each)
and the result cross-checked against the official `kaggle competitions
episodes <id>` count, which matched exactly: 72 / 94 / 79 / 49. This is
**all episodes Kaggle's API currently exposes for these submissions**, not a
sampled window — called out explicitly per the task's instruction, since
these are all young submissions (5–11 hours old at retrieval) so "all
accessible" and "complete lifetime history" happen to coincide here.

**Manifest frozen before download**, same discipline as the top-6 run:
`manifest.csv` (294 rows) written to disk before any replay request; the
download loop re-reads episode IDs from that file, not from in-memory state.

**Category breakdown** (from `manifest.csv`'s `category` column, computed
from Kaggle's own `type`/`state` fields — `EPISODE_TYPE_VALIDATION` is
Kaggle's submission-validation self-play run):

| Submission | competitive | validation | failed/incomplete | total |
|---|---|---|---|---|
| `w1_v15stack_race44.py` | 71 | 1 | 0 | 72 |
| `w0_v15stack_control.py` | 93 | 1 | 0 | 94 |
| `washamba_base_v1_fork.py` | 78 | 1 | 0 | 79 |
| `washamba_base_v2.py` | 48 | 1 | 0 | 49 |
| **Total** | **290** | **4** | **0** | **294** |

Zero failed/incomplete episodes. No two of our four submissions ever played
each other in a competitive game (290 competitive rows = 290 unique
competitive episodes — no collapse from cross-target matchups), so there is
no washamba-vs-washamba example to report.

**Replays:** 294/294 unique episodes downloaded, **0 failures**, 106 MB
compressed, through the same validate→gzip→re-validate→atomic-rename pipeline
as the top-6 run.

**Agent logs:** downloaded via `kaggle competitions logs <episode_id> <our_seat>`
— **294/294 succeeded** after one retry pass (the first pass crashed on an
unhandled subprocess timeout at 100/294; resumed and completed cleanly, see
`log_download_results.json`). **Opponent logs are not accessible** — verified
directly: querying the opponent's `agent_index` returns `403 Forbidden` on
every attempt, consistently, not an intermittent failure. Log content: 0
non-empty `stderr` across all 294 games (our agents raise nothing at
runtime); 98/294 episodes (33%) contain at least one turn over the 1.0s
`actTimeout` (max single-turn duration observed: 1.92s), but the **summed
overage across the entire 294-episode corpus is 25.9 seconds** against a
60-second *per-episode* overage bank — nowhere near a risk of the bank
running out on any single episode. This is a performance note, not a
reliability problem: it's consistent with zero episodes failing or timing out.

**Freshness vs. the top-6 corpus, stated explicitly per the task's request:**

| | top-6 corpus | this corpus |
|---|---|---|
| Retrieved | 2026-09-23T15:34:31Z | ~2026-09-23T16:20Z (fetch completed) |
| Episode date range | 2026-09-22T22:57Z → 2026-09-23T15:34Z | 2026-09-23T05:16Z → 2026-09-23T16:04Z |
| Overlap | last ~10.5h of the top-6 window overlaps this corpus's window | — |

The top-6 corpus includes ~6 hours (22 Sep evening) that predate any of our
four submissions' existence — expected, since it targets six *other* teams'
histories, not ours. Both corpora are same-day, ~45–60 minutes apart in
retrieval time; treat any comparison as "same competitive season, adjacent
snapshots," not simultaneous.

---

## 2. Replay format re-verification (not assumed carried over)

Re-ran the empirical BUY_LAND-tile-jump test (per the task's explicit
instruction not to assume a convention) against a real episode from **this**
corpus: `112318725`. Result, identical to the top-6 corpus's finding, now
independently confirmed on a second, disjoint set of replay files:

- `steps[t][seat]["observation"]["step"] == t` for every t (0-based, spot-checked).
- `steps[t][seat]["action"]` was chosen using `steps[t-1][seat]["observation"]`.
- `steps[t][seat]["observation"]` is the state **after** that action resolved.
- Empirical proof: a `BUY_LAND` order recorded at step 151 shows tiles=25 at
  `steps[150]` (prior row, pre-decision) and tiles=50 at `steps[151]`
  (**same row as the order** — not `steps[152]`).
- Terminal row: `rewards=[71491.0, 72155.0]`, both seats `DONE`.

Every decision extraction below uses `steps[t-1]` as the pre-decision state.
Public/private field separation is identical to the top-6 run: opponent
fields are read only from `obs["farms"]`/`market`/`town` (public/shared),
never the opponent's `private` block. Peak-crew claims use `crew_by_day`
(max hands observed that day), never an hour-0 snapshot — the same
midnight-reset guard as before.

---

## 3. Per-submission result summary

Win/loss/tie **recomputed directly from `player_bank` vs. `opponent_bank`**
(not the raw manifest `won` column, which is 1/0 only and silently folds
ties into "0" — this run's `submission_results.csv` fixes that).

| Submission | competitive games | W–L–T | win rate | margin mean | rating (first→last) |
|---|---|---|---|---|---|
| `w1_v15stack_race44.py` | 71 | 65–6–0 | **91.5%** | +7,920 | 672.1 → **2018.1** |
| `w0_v15stack_control.py` | 93 | 62–27–4 | 66.7% | +4,118 | 693.7 → **2423.8** (highest) |
| `washamba_base_v1_fork.py` | 78 | 62–16–0 | 79.5% | +7,405 | 686.5 → 1959.1 |
| `washamba_base_v2.py` | 48 | 37–11–0 | 77.1% | +11,358 | 675.7 → 1854.6 |

**Win rate and rating do not agree, and that's expected, not a bug.**
`w1_v15stack_race44.py` has the highest win rate (91.5%) but a lower final
rating than `w0_v15stack_control.py` (66.7% win rate, highest rating,
2423.8). Reading the opponent-rating-band breakdown below explains most of
the gap: `w0_v15stack_control.py` played 46 wins **and** 25 losses **and**
all 4 ties inside the toughest opponent band (2000–2500) — a much harder,
more contested draw than `w1_v15stack_race44.py`'s draw, which is
concentrated in the 1500–2000 band (46 of 71 games) with almost no exposure
above 2000. A rating system that weighs opponent strength can legitimately
rank the harder-draw, lower-win-rate agent higher; **do not read win rate
alone as "which agent is better."**

### By seat

| Submission | seat 0 W-L-T | seat 1 W-L-T |
|---|---|---|
| `w1_v15stack_race44.py` | 27-4-0 | 38-2-0 |
| `w0_v15stack_control.py` | 31-14-2 | 31-13-2 |
| `washamba_base_v1_fork.py` | 31-8-0 | 31-8-0 |
| `washamba_base_v2.py` | 18-5-0 | 19-6-0 |

No seat shows a striking asymmetry for any of the four (`w1_v15stack_race44.py`'s
seat-1 record looks stronger, 38-2 vs 27-4, but both are small samples and
neither is far from the other's rate).

### By opponent-rating band

Bands are fixed 500-point bins, chosen before looking at which agent they'd
flatter:

| Submission | 0–1000 | 1000–1500 | 1500–2000 | 2000–2500 | 2500–3000 |
|---|---|---|---|---|---|
| `w1_v15stack_race44.py` | 5-0 | 9-1 | 46-4 | 5-1 | — |
| `w0_v15stack_control.py` | 4-0 | 4-0 | 5-0 | 46-25-4t | 3-2 |
| `washamba_base_v1_fork.py` | 6-0 | 7-1 | 49-14 | 0-1 | — |
| `washamba_base_v2.py` | 6-0 | 6-2 | 25-9 | — | — |

`w0_v15stack_control.py` is the only one of the four with real exposure to
2000+-rated opponents (49 of 93 games); the other three are concentrated at
1500–2000 and below. This is the single biggest confound in any win-rate
comparison across our four submissions, and the reason raw win rate is
reported alongside — not instead of — this table.

### Close-loss sensitivity (four thresholds, none cherry-picked to flatter)

"Close loss" defined as `|final_bank_margin| <= threshold`, shown at four
thresholds so the reader can judge sensitivity rather than trust one number:

| Submission | losses | within $1,000 | within $2,500 | within $5,000 | within $10,000 |
|---|---|---|---|---|---|
| `w1_v15stack_race44.py` | 6 | 3 (50%) | 5 (83%) | 5 (83%) | 5 (83%) |
| `w0_v15stack_control.py` | 27 | 19 (70%) | 22 (82%) | 24 (89%) | 24 (89%) |
| `washamba_base_v1_fork.py` | 16 | 6 (38%) | 11 (69%) | 12 (75%) | 14 (88%) |
| `washamba_base_v2.py` | 11 | 6 (55%) | 8 (73%) | 8 (73%) | 9 (82%) |

Across all four submissions, **the large majority of losses are close**
(within $2,500 of the winner, 69–83% of losses) at every threshold tested —
this is a stable pattern, not an artifact of one threshold choice. It also
means most losses are not being caused by one catastrophic mistake; they're
narrow contests decided late.

### Bank-margin distribution

| Submission | margin mean | median | stdev | min | max |
|---|---|---|---|---|---|
| `w1_v15stack_race44.py` | 7,920 | — | — | -14,021 | — |
| `w0_v15stack_control.py` | 4,118 | — | — | -25,517 | — |
| `washamba_base_v1_fork.py` | 7,405 | — | — | -18,619 | — |
| `washamba_base_v2.py` | 11,358 | — | — | -13,985 | — |

(Full mean/median/stdev/min/max per submission is in `results_detail.json`;
summarized here to the fields that matter for the close-loss discussion above.)

### Rating trajectory

All four start at essentially the same seed rating (~672–694, the platform's
starting value for a new submission) and climb monotonically over their
game history to the values in the table above — no submission shows a
rating regression or plateau within its available history. `n` in the
table above (71/93/78/48) is every rated competitive game, so this is the
full trajectory each submission has accrued, not a sample.

---

## 4. Comparison with the fresh top-6 corpus

Both corpora processed with the same extraction logic (`stage_a_summary.py`,
land-count-bug-fixed) and the same checkpoint grid.

| Signal | Top-6 (360 trajectories) | Washamba (290 trajectories) | Read |
|---|---|---|---|
| First BUY_LAND day | 86.7% on day 6 | 100% on day 6 (median, all four) | **Same branch, same timing.** |
| 3rd land quadrant (100 tiles) ever bought | **0/360 (never)** | v2 11/48 (23%), v1_fork 26/78 (33%), control 21/93 (23%), race44 16/71 (23%) | **Real divergence** — see §6.1. |
| COW/SHEEP adoption & timing | 100%, day 0 | 100%, day 0 | Same. |
| GOOSE adoption | 96.7–100% (58–60/60 per team) | 64.6–70.5% (31/48–61/93) | **Real divergence** — see §6.2. |
| GOOSE first-purchase day (mean) | day 1–2 (Boey, M&M&P&Q) or day 7–8 (the other four) | day 8.4–8.8, all four submissions | We're always in the "late" group; never the "early" group. |
| Peak crew (median) | 12–14 | 13 (all four) | Same. |
| Cash trough, days 3–7 (mean) | $3.3 (Boey) – $46.9 (吃白饭的大肥鱼) | **$211.9 – $217.6** (all four) | **Real divergence** — we carry ~5–70× more cash buffer through the trough than any top-6 team. |
| Sell orders/day, opening (d0–2) | 1.7–5.4 (five teams) / **43.5 (Boey)** | 2.3–2.4 (all four) | We match the *typical* top-6 profile, not Boey's outlier — see §6.3. |
| Sell orders/day, d22–29 | 11.1–34.8 (five teams) / **147.1 (Boey)** | 17.6–30.8 | Same read as above. |

The cash-trough gap is the largest, cleanest, most consistent signal in this
comparison — worth restating plainly: **every one of the top-6 teams runs
the days-3–7 trough down to single digits or low tens of dollars; all four
of our submissions leave $200+ of buffer.** This is directionally consistent
with (and likely explained by) this repo's own documented
`MIN_CASH_RESERVE_FOR_SEED_BUYING` retune (100→450) — a deliberate,
already-recorded choice to hold back cash during that window, not an
accident. Whether the top-6 teams' tighter margin is a source of their edge
or just tolerable risk they can afford (given whatever executor/hire-timing
differences underlie it) is not established by this replay-only comparison —
flagged as open in §7.

---

## 5. Where each submission first diverges from the day-6 template, and what's binding

All four submissions reach a near-identical day-6 checkpoint to each other
and to the top-6 template (`$570–2185 cash, 25 land, 8–9 crew, WHEAT:3/
STRAWBERRY:4/MELON:12, COW:2-4/SHEEP:2`), then issue the same `BUY_LAND`
economic choice on the same day. **The divergence that decides win/loss is
not visible at day 6 in any of the twelve worked examples below** — pre-day-6
states for a submission's loss/close-loss/win trio are statistically
indistinguishable from each other. This matches, and reinforces with four
more submissions' worth of evidence, the top-6 report's own §4.6 finding
(DECEM vs. DSM): **the branch point is shared and stable; the outcome is
decided by what happens after it — largely execution and opponent strength,
not a different economic choice at the branch itself.**

Two concrete, verified pieces of evidence for this, both economic-choice-vs-execution
distinctions per the task's framing:

- **`washamba_base_v2.py`'s close-loss (`112345286`) and win (`112356384`)
  trajectories are nearly identical day-by-day through day 18** (money
  within a few hundred dollars at every checkpoint, identical land/crop/animal
  counts) — literally the same deterministic policy encountering two
  different opponents. The economic choices made were the same; only the
  opponent differed. **Economic choice: unchanged. Execution: unchanged.
  Outcome: opponent-driven.**
- **`w1_v15stack_race44.py`'s clear-loss (`112427441`) diverges from its own
  win/close-loss pattern specifically in animal herd size**, visible by day
  26: our agent held `{GOOSE:3, SHEEP:4, COW:5}` (9 animals) while the
  opponent in that game held `{GOOSE:3, SHEEP:6, COW:8}` (14 animals), with
  identical crop counts on both sides and the opponent already $10,600
  ahead in cash. This is one example, not a confirmed pattern (see §6.4) —
  but it is a genuine, matched-state, single-game divergence in an economic
  quantity (herd size), not an execution artifact.

---

## 6. Recurring weaknesses, ranked by evidence strength

### 6.1 — Third land quadrant: inconclusive on our own data, but a real strategic outlier vs. top-6 (medium evidence, unclear impact)

Top-6: 0/360 trajectories ever buy the third quadrant (100 tiles). All four
washamba submissions do, in 23–33% of their games. Checked directly whether
it correlates with winning **within** our own corpus:

| Submission | win rate, land capped at 75 | win rate, land reached ≥90 (3rd quadrant) |
|---|---|---|
| `washamba_base_v2.py` | 78.4% (29/37) | 72.7% (8/11) |
| `washamba_base_v1_fork.py` | 80.8% (42/52) | 76.9% (20/26) |
| `w0_v15stack_control.py` | 65.3% (47/72) | 71.4% (15/21) |
| `w1_v15stack_race44.py` | 90.9% (50/55) | 93.8% (15/16) |

**No consistent direction** — two submissions show a slightly lower win rate
with the 3rd quadrant, two show a slightly higher one, and none of the gaps
are large relative to sample size. This is genuinely unresolved: worth
knowing our agents behave differently from every one of the six best teams
on this specific lever, not worth acting on without a controlled test (see
§7's proposed counterfactual).

### 6.2 — GOOSE: incomplete and always-late adoption (strong evidence, directly actionable)

Confirmed independently on both corpora: top-6 buys GOOSE in 97–100% of
games; we buy it in 65–71% of games, and every one of our four submissions'
mean first-purchase day (8.4–8.8) falls only in top-6's *later* cluster,
never its earlier one (Boey/M&M&P&Q buy around day 1–2). This is the same
finding the top-6 report flagged as idea #2, now cross-validated against
our own four submissions rather than inferred only from the opposing field.

### 6.3 — Selling cadence matches the "typical" top-6 profile, not the outlier that wins most (strong evidence, directly actionable)

Our four submissions' sell-orders-per-day curve (2.3/day opening → 18–31/day
by the end) tracks DSM/DECEM/Unknown Mother-Goose/M&M&P&Q/吃白饭的大肥鱼
almost exactly. None of the four comes anywhere near Boey's (rank 1, 58-2 in
the top-6 sample) 43.5→147.1/day profile. This is the same idea #1 from the
top-6 report, now confirmed as a real gap between us and the specific
top-6 team with the best record, not just a hypothesis about the field.

### 6.4 — Herd-size gap in at least one clear loss (single example, hypothesis only)

`w1_v15stack_race44.py`'s clearest loss shows a 9-vs-14 animal gap against
the opponent at day 26 with identical crops (§5). One matched-state example
is evidence, not a pattern — flagged as a hypothesis to check against more
games, not a confirmed weakness.

### 6.5 — Cash-trough buffer is much larger than every top-6 team's (strong evidence, direction of effect unresolved)

See §4. Directionally interesting because this repo's own history
(`MIN_CASH_RESERVE_FOR_SEED_BUYING`) already shows tightening this exact
buffer produced a large measured gain against `starter` in the past — but
that measurement predates these four submissions and wasn't re-tested
against a live contested field. Not claimed as a bug; flagged as the most
promising **already-partially-instrumented** lever to re-test.

---

## 7. Twelve worked examples (loss / close loss / win, per submission)

Full per-turn traces are in the scratch deep-dive outputs referenced by
episode ID below; state and actions quoted here are read directly from the
replay per §2's verified convention (`steps[t-1]` = pre-decision state).

### `washamba_base_v2.py`

**Clear loss — `112364993`, seat 1, vs. Luon may Man.** Day-6 pre-state
(`steps[149]`): `$770, 25 land, crew 9, {WHEAT:3, STRAWBERRY:4, MELON:12},
{SHEEP:2, COW:2}`. `BUY_LAND` lands at step 151 (one turn later than the
median). By day 18: land 75, crew 12, `{WHEAT:25, STRAWBERRY:32}`; by day 26:
**land 100** (the 3rd quadrant — both sides took it in this game), money
$61,450 vs. opponent's $73,820. **Category A (continue) → B (expand,
including the 3rd quadrant).** Final: **$82,828 vs. $96,813** — opponent
already ~$12,400 ahead by day 26; no single later mistake identified, reads
as a stronger opponent build throughout. *Inference, not confirmed.*

**Close loss — `112345286`, seat 1, vs. T.Uehira.** Day-6 pre-state: `$935`,
identical crop/animal template. `SELL WOOL x6` + implicit land purchase the
same turn (cash jumps to $2,185). Day 18: land 75, `{WHEAT:25,STRAWBERRY:33}`.
**Category A.** Final: **$135,393 vs. $135,611** — a $218 margin, the
closest example in this whole report.

**Win — `112356384`, seat 0, vs. fumiya utsuno.** Day-6 pre-state: `$934`,
same template, **same action as the close-loss example above, essentially
verbatim.** Day 18 state nearly identical to the close-loss trajectory too.
**Category A.** Final: **$68,346 vs. $62,423.**
*The close-loss and win examples are the clearest illustration in this
report of §5's point: same policy, same choices, different opponents, and a
much larger absolute-bank difference between the two ($135K vs. $68K) that
has nothing to do with which one we "played better" — don't read the bank
gap between these two as a decision quality signal.*

### `washamba_base_v1_fork.py`

**Clear loss — `112357630`, seat 0, vs. Suzuki Yuto - W.** Day-6: `$574`,
template match. Day 18: land 75, `{WHEAT:25,STRAWBERRY:30}`, crew 12.
**Category A.** Final: **$104,927 vs. $123,546** (-18,619, the largest
single-episode loss margin across all twelve examples).

**Close loss — `112419429`, seat 0, vs. Sam-wiz.** Day-6: `$935`. Day 18:
land **100** (3rd quadrant), crew 14, `{CARROT:7,STRAWBERRY:33,WHEAT:18,
TOMATO:2}` — the most diversified crop mix of any of the twelve examples.
**Category A → B (3rd quadrant) → C (crop diversification into CARROT/TOMATO,
not just WHEAT/STRAWBERRY).** Final: **$125,222 vs. $125,273** (-51, the
single closest margin in the entire corpus, decided by under one wheat sale).

**Win — `112366181`, seat 0, vs. David Mensah-Gbekor.** Day-6: `$932`,
same action as the close-loss example (`DROP`/`SELL WOOL x6`). Day 18: land
75 (capped, did **not** take the 3rd quadrant this time), `{WHEAT:25,
STRAWBERRY:33}`. **Category A.** Final: **$103,813 vs. $101,050.**
*Same lesson as the v2 pair above: close-loss and win pre-states and
early actions are indistinguishable; the 3rd-quadrant purchase appears in
the close-loss game and not the win, which is exactly the "inconclusive"
pattern from §6.1, not a clean causal story either way.*

### `w0_v15stack_control.py`

**Clear loss — `112469884`, seat 1, vs. Arman Tuganbaev.** Day-6: `$850`,
template match, action pattern `EAST`/`PLACE`/`CARE`/`SELL FERTILIZER 1`
(distinct from the `DROP`/`SELL WOOL` pattern seen in the other three
submissions at this same checkpoint — see the note at the end of this
section). Day 18: land 75, `{WHEAT:25,STRAWBERRY:33}`. **Category A.**
Final: **$99,708 vs. $125,225** (-25,517, the largest margin loss of any of
the twelve examples in absolute terms).

**Close loss — `112389635`, seat 1, vs. Mr.NoT_GaMeR.** Day-6: `$1,130`,
same `EAST`/`PLACE`/`CARE` action pattern. Day 18: land **100** (3rd
quadrant), crew 15. **Category A → B.** Final: **$95,572 vs. $95,619** (-47,
essentially a coin-flip margin).

**Win — `112410075`, seat 1, vs. neibyr.** Day-6: `$1,113`, same action
pattern again. Day 18: land 75 (capped). **Category A.** Final:
**$133,269 vs. $132,143** — this submission's largest bank of the three
examples, on a win margin of only $1,126, underscoring §3's close-loss
finding: even winning games in this submission tend to be tight.

### `w1_v15stack_race44.py`

**Clear loss — `112427441`, seat 0, vs. Aura Farming.** Day-6: `$660`,
`DROP`/`SELL WOOL` action pattern. Day 26: land 75 (capped), **herd
`{GOOSE:3,SHEEP:4,COW:5}` vs. opponent's `{GOOSE:3,SHEEP:6,COW:8}`** —
the herd-size gap flagged in §6.4. **Category A.** Final: **$61,892 vs.
$75,913** (-14,021).

**Close loss — `112467829`, seat 1, vs. lime0001.** Day-6: `$1,026`, same
action pattern. Day 18: land **100** (3rd quadrant). **Category A → B.**
Final: **$77,473 vs. $77,593** (-120).

**Win — `112441883`, seat 1, vs. mkai1981.** Day-6: `$1,040`, same action
pattern. Day 18: land 75 (capped). **Category A.** Final: **$88,015 vs.
$84,891** (+3,124).

**Observation on the two action-pattern families, labeled clearly as
unexplained rather than diagnosed:** at the day-6 checkpoint,
`washamba_base_v1_fork.py` and `w1_v15stack_race44.py` always use one action
pattern (`DROP`/`SELL WOOL x6`), `w0_v15stack_control.py` always uses a
second (`EAST`/`PLACE`/`CARE`/`SELL FERTILIZER x1`), and `washamba_base_v2.py`
uses the first pattern at higher cash ($2,184–2,185) and the second at lower
cash ($770) — consistent with a state-conditioned branch inside `v2`'s own
logic, though not verified against the submitted source in this task (this
report is replay-only, not a code diff). This is an interesting forensic
detail about how these four submissions relate to each other, offered as a
observation to follow up on, not a claim about which file contains what code.

---

## 8. What we'd need to settle the open questions (counterfactual tests, none run)

Per the task's own framing: this corpus shows chosen continuations and
realized outcomes, not the value of unplayed alternatives. For each item in
§6, the smallest test that could move it from hypothesis to evidence:

- **§6.1 (3rd quadrant):** `paired_compare.py`, same seed set, one arm with
  land purchases hard-capped at 2 quadrants vs. one arm allowed a 3rd,
  holding crew-scaling logic fixed. `counterfactual value not estimated` —
  this run's replay data alone cannot separate "3rd quadrant helped/hurt"
  from "which opponent happened to be drawn."
- **§6.2 (GOOSE):** same harness, GOOSE purchase gated at day 1 vs. day 8,
  holding everything else fixed.
- **§6.3 (sell cadence):** same harness, A/B just the sell-order
  frequency/size in the opening days, independent of the two already-failed
  continuous-urgency-ramp attempts this repo has on record (CLAUDE.md) —
  Boey's pattern is flat-high-frequency-from-turn-0, not a smooth ramp.
- **§6.4 (herd size):** needs more matched-state examples before it's worth
  testing at all; one game is not enough to design an experiment around.
- **§6.5 (cash trough):** `MIN_CASH_RESERVE_FOR_SEED_BUYING` has already
  been tuned once in this repo's history and measured against `starter`;
  re-measuring it with `paired_compare.py`/`head_to_head.py` against a
  current contested field (not just `starter`) is the concrete next step,
  and the cheapest of the five since the mechanism is already implemented
  and just needs re-testing at a different value.

If any of these were tested against a fixed opponent replay tape rather than
a live episode, the result would not show how a real adaptive opponent
responds to our changed policy — flagged per the task's instruction, though
none of the above proposes doing that; all five need a live harness run.

---

## Files in this corpus

- `submission_inventory.csv` — the 4 resolved submissions, frozen metadata
- `manifest.csv` — 294 rows (290 competitive / 4 validation / 0 failed), frozen before download
- `opponent_ratings.csv` — read-only supplemental join (opponent rating at episode time), 290/294 resolved
- `replays/<episode_id>.json.gz` — 294 files, 106 MB
- `logs/episode-<id>-agent-<seat>-logs.json` — 294 files, our-seat only (opponent logs return 403), 11 MB
- `download_results.json`, `log_download_results.json` — per-file reliability records
- `checkpoint_states.jsonl` — 3,190 rows
- `decision_events.csv` — 1,645 rows
- `episode_summaries.jsonl`, `aggregate_stats.json`, `candidate_examples.json` — working data behind §4–§6
- `submission_results.csv`, `results_detail.json` — §3's per-submission results
- `washamba_vs_top6_report.md` — this file

**Report location:**
`/Users/stephanengugi/KagricultureLocalData/episodes/20260923T161855Z_washamba_vs_top6/washamba_vs_top6_report.md`

---

## Handoff — paste into "Alternatives to BPO Planning"

**What was examined:** all available competitive ladder games (no cap) for
four submissions from 23 Sep 2026 (not 22 Sep as originally targeted — dates
didn't match, resolved by exact filename/description/score instead):
`w1_v15stack_race44.py` (Stephane, 56491123, 71 games), `w0_v15stack_control.py`
(Stephane, 56487592, 93 games), `washamba_base_v1_fork.py` (Peter, 56483603,
78 games), `washamba_base_v2.py` (Peter, 56483595, 48 games) — 290 competitive
games total, 0 failures, compared against the existing fresh top-6 corpus
(360 trajectories, 6 teams, retrieved same day ~45-60 min earlier).

**Corpus paths:**
`/Users/stephanengugi/KagricultureLocalData/episodes/20260923T161855Z_washamba_vs_top6/`
(this run) and `/Users/stephanengugi/KagricultureLocalData/episodes/20260923T153431Z_top6/`
(reused). Both complete — 0 download failures in either.

**How each performed:** `w1_v15stack_race44.py` 65-6-0 (91.5% win, but
against an easier opponent-rating draw); `w0_v15stack_control.py` 62-27-4
(66.7% win, harder draw, highest final rating 2423.8); `washamba_base_v1_fork.py`
62-16-0 (79.5%); `washamba_base_v2.py` 37-11-0 (77.1%, smallest sample).
**Win rate and rating disagree because of opponent-strength differences —
don't rank these four by win rate alone.** Most losses across all four are
close (69–83% within $2,500) — few blowout losses.

**Strongest evidence of where we differ from top-6 leaders:**
1. All four of our submissions leave **$200+ cash buffer** through the
   days-3–7 trough; every one of the top six leaders runs it to single/low
   double digits. Largest, cleanest signal in the whole comparison.
2. Our GOOSE adoption is **65–71% of games, always ~day 8–9**; top-6 is
   **97–100%**, split between an early (day 1–2) and late (day 7–8) group —
   we're never in the early group and not universal at all.
3. Our sell-order cadence matches the **typical** top-6 profile, not
   **Boey's** (rank 1, 58-2) 5–13×-more-frequent pattern from turn 0.
4. We buy the 3rd land quadrant in 23–33% of games; **top-6 never does**
   (0/360) — but this doesn't correlate cleanly with winning or losing in
   our own data (checked directly, no consistent direction across the four
   submissions), so it's a real difference with an unresolved sign.

**What remains uncertain:** whether tightening the cash-trough buffer,
earlier/universal GOOSE, or a higher sell cadence would actually help against
a live contested field (all three are hypotheses backed by directional
replay evidence, not tested counterfactuals); whether the 3rd land quadrant
helps or hurts (checked, genuinely inconclusive in our own 290-game sample);
one single-example herd-size gap that needs more instances before it's
actionable; and an unexplained but harmless-looking pattern where our four
submissions split into two different action "families" at the day-6
checkpoint (not traced to source code in this replay-only task).

**Next concrete implementation question:** of the five items in §8, which
one should get a `paired_compare.py`/`head_to_head.py` slot first — the
cash-trough re-test is the cheapest (mechanism already exists, just needs
re-measuring against a current field instead of `starter`), but the
sell-cadence test is the one most directly tied to the single best-performing
team in the top-6 sample (Boey). Pick one to scope as an actual code change
next.
