# Our current games and the 2,900 band: W3 and the W1 re-upload

Read-only research. Nothing was submitted to Kaggle and no git commands were run in either
`washamba_bots` or this data directory. Generated 2026-09-24, from
`episodes/20260924T161358Z_washamba_0924b/`.

## 1. Submission IDs

| Submission | File | Submission ID | Uploaded (UTC) |
|---|---|---|---|
| **W1 re-upload** | `w1_v15stack_race44.py` | **56521297** | 2026-09-24 12:34:20 |
| **W3** | `main.py` (`w3_herdsafe2700.py`) | **56518334** | 2026-09-24 09:55:45 |
| W0 (retired) | `w0_v15stack_control.py` | 56487592 | 2026-09-23 08:01:53 |
| W1 (first upload) | `w1_v15stack_race44.py` | 56491123 | 2026-09-23 10:54:55 |

**Measured**: resolved from `kaggle competitions submissions kaggriculture -v`, matched by upload date
(24 Sep) and description text. The W1 re-upload's own description literally says "Re-uploaded to pair
with W3 (Herd-Safe 2700)"; W3's `fileName` is `main.py` and its description names it
`w3_herdsafe2700`. W0 and the first W1 upload were given directly by the task. As of this snapshot,
W1-re-upload and W3 are the two most recently uploaded submissions, i.e. Kaggle's current active
matchmaking pair; W0 and first-W1 are both retired (displaced from the latest-2 slot on 2026-09-24,
confirmed below).

## 2. Episode download summary

| Submission | Non-validation completed episodes (API) |
|---|---|
| W1 re-upload (56521297) | 61 |
| W3 (56518334) | 84 |
| W0 retired (56487592) | 157 |
| W1 first upload (56491123) | 152 |

**Measured.** `manifest.csv` (454 rows) was written to disk before any download began. Of 454 distinct
episode IDs across the four submissions: 290 replays were freshly downloaded this run, 164 were
byte-identical episode IDs already sitting in the existing `20260923T161855Z_washamba_vs_top6` /
`20260923T153431Z_top6` replay caches and were copied rather than re-fetched, and after two retry
passes (the API 429-rate-limits aggressively under sustained load) **all 454 replays and all 454 of
our own agent-log files are on disk with zero remaining errors.** Opponent logs were never requested
(known 403, not retried, per the task's instruction).

W0 and first-W1's episode counts grew substantially since the 2026-09-23 16:18 snapshot (94→157 and
72→152 respectively) because both stayed in Kaggle's active-matchmaking pair for most of 2026-09-23-24
before being displaced by newer uploads — confirmed by their `newest` episode end-times landing right
at the moment each was displaced (W0's last episode ends 06:48:44, three minutes before
`washamba_base_v3` was submitted at 06:51:17; first-W1's last episode ends 10:06, eleven minutes after
W3 was submitted at 09:55, consistent with one game already in flight at the cutover). **Measured.**

**A methodology caveat that applies to every table below:** opponent "rating" and "band" are the
opponent's *current* leaderboard rating from one live snapshot (`kaggle competitions leaderboard
kaggriculture -d`, full CSV, retrieved 2026-09-24T16:13:50Z), not that opponent's rating at the moment
each specific episode was played. The authenticated episode API used here (`kagglesdk`'s
`CompetitionApiService`) does not expose a per-episode before/after rating the way the old manifest
format did; a snapshot rating is the best available substitute and is standard practice elsewhere in
this project's `opponent_ratings.csv` convention. Given the CLAUDE.md-documented ~1% noise on team
ratings inside a day, this is treated as a reasonable but imperfect proxy — **inference** that it does
not materially change the band assignments below, not independently verified per-episode.

## 3. Ranks 7-12 report (companion deliverable)

Built in the same run: `episodes/20260924T161358Z_ranks7to12/ranks7to12_report.md`.

## 4. W-L-T, opponent bands, opponent families, tape near-ties

Opponent family is classified per-game from that opponent's own row-1/row-2 market orders in the
downloaded replay (opening-fingerprint match: "tape" = row-2 orders contain both `BUY_ANIMAL COW 2`
and `BUY_ANIMAL SHEEP 2`; "DSM" = row-1 opens `BUY_ANIMAL COW 1` then `BUY_PRODUCT WHEAT 5`; "Boey" =
row-1 opens `BUY_PRODUCT WHEAT 3` then five `HIRE`s; else "other"). **Measured**, this session.

### W3 (main.py, 56518334) — record 51-32-1 (n=84, 61.3% win rate incl. ties)

**By opponent rating band:**

| Band | W | T | L |
|---|---|---|---|
| <2000 | 16 | 0 | 0 |
| 2000-2500 | 26 | 1 | 15 |
| 2500-2800 | 8 | 0 | 17 |
| >2800 | 1 | 0 | 0 |

**By opponent family:**

| Family | W | T | L |
|---|---|---|---|
| tape | 42 | 1 | 31 |
| other | 9 | 0 | 1 |

Tape-family opponents (n=74): 27 games (36%) finished a near-tie (|margin| < 500); median margin
across all 74 was +192.5. **Measured.**

### W1 re-upload (56521297) — record 35-25-1 (n=61, 58.2% win rate incl. ties)

**By opponent rating band:**

| Band | W | T | L |
|---|---|---|---|
| <2000 | 13 | 0 | 2 |
| 2000-2500 | 22 | 1 | 18 |
| 2500-2800 | 0 | 0 | 5 |

(No >2800 opponent encountered in this submission's 61-episode sample.)

**By opponent family:**

| Family | W | T | L |
|---|---|---|---|
| tape | 31 | 1 | 25 |
| other | 4 | 0 | 0 |

Tape-family opponents (n=57): 25 games (44%) finished a near-tie; median margin +81.0. **Measured.**

**The single clearest pattern in this section**: both W3 and the W1 re-upload go a combined 0-22 in
the 2,500-2,800 opponent band (W3: 8-17, W1-re-upload: 0-5 — W1-re-upload literally never won against
that band in this sample). Below 2,500 both submissions have a winning or roughly even record; at and
above 2,500 both submissions lose more than they win. **Measured.**

### For reference — W0 (retired) and first-W1

| Submission | Record (W-L-T) | Tape n | Tape near-ties (<500) | Tape median margin |
|---|---|---|---|---|
| W0 retired | 84-66-7 | 151 | 59 (39%) | +97.0 |
| W1 first upload | 116-36-0 | 140 | 30 (21%) | +1018.5 |

First-W1's much larger median margin lines up with its much softer opponent mix (its <2000-band record
was 62-4 with 0 ties); it was simply facing weaker opposition on average than the current pair.
**Measured.**

## 5. W3 losses against opponents rated above 2,500

**n = 17** such losses (all fall in the 2,500-2,800 band; W3 had zero losses against the single >2,800
opponent it met — it won that one game). **Measured**, via the frozen manifest + leaderboard snapshot.

These are close games, not blowouts. Final-bank margins range from -141 to -3,216 (median approx -986)
on banks in the ~60k-145k range — i.e. losing by roughly 1-3% of the game's total economy, not getting
routed. **Measured**, re-simulated through `harness/resim_trades.py` (all 17 replays reproduced the
exact recorded reward, confirming the resim is faithful).

**Day the opponent's bank first led by more than 3,000:** in 16 of the 17 losses, the opponent's bank
never led by more than 3,000 at any daily checkpoint — these were games that were close the entire
way and only tipped negative right at the end. The one exception is episode 112861962 (vs. xiao
xiongwei, rated 2689.1), where the opponent first opened a >3,000 lead on day 26; that game also
had the largest final margin of the 17 (-3,216). **Measured**, read directly from each replay's
per-turn farm money.

**Three products where W3 lost the most revenue**, summed across these 17 losses (W3's own SELL
revenue minus the opponent's SELL revenue for that product; most negative first). **Measured**, via
`resim_trades.py`'s instrumented replay of the recorded actions:

| Product | Revenue delta (W3 minus opponent) | W3 revenue | Opponent revenue |
|---|---|---|---|
| WHEAT | -284,220 | 437,319 | 721,539 |
| TOMATO | -12,947 | 70,725 | 83,672 |
| FERTILIZER | -11,622 | 255,084 | 266,706 |

For contrast, W3 actually out-earned these same opponents on CARROT (+5,847), MELON (+939) and EGG
(+333); STRAWBERRY, MILK and WOOL were close to even (-6,902, -1,619, -501).

**This is the clearest, most surprising finding in this report.** The WHEAT gap (-284,220) is roughly
20x the size of the next-largest gap (TOMATO, -12,947) and dwarfs every other product's deficit
combined (-32,591 total for TOMATO+FERTILIZER+STRAWBERRY+MILK+WOOL). Across these 17 close losses,
opponents extracted 65% more WHEAT revenue than W3 did (721,539 vs 437,319) while every other product
was roughly at parity. **Measured.** Whether this reflects W3 under-planting/under-selling WHEAT, or
these particular >2,500-rated opponents simply running a WHEAT-heavier strategy that out-produces W3's
mix, is not established by this data alone — **inference**: given how close these games are in final
margin, and how one-sided the WHEAT gap is relative to every other product, WHEAT throughput looks like
the most promising lever to check first for closing these specific losses, but that is a hypothesis
for a follow-up paired comparison, not a conclusion this read-only pass can prove on its own.

## What this run could and couldn't complete

- All four submissions are fully downloaded (manifests, replays, our own logs), zero outstanding
  errors, after two retry passes around the Kaggle API's rate limiting (HTTP 429). **Measured.**
- Opponent ratings are one live snapshot, not a per-episode historical value (section 2 caveat) —
  affects every band table here and in the ranks-7-to-12 report. **Measured limitation.**
- Section 5 covers all 17 qualifying W3 losses, not a sample. **Measured.**
