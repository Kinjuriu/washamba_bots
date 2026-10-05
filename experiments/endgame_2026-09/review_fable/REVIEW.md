# Independent review of the Washamba Bots Kaggriculture effort
Fable 5.1, 26 September 2026. Read-only; scripts and outputs are under `review_fable/` (raw tables in `NUMBERS.md`). Engine: kaggle-environments 1.32.7. MEASURED names the file; INFERENCE is my judgement. I ran 242 games in total.

## 1. Independent view, then what changed

**Written before reading any conclusions** (`step1_independent_view.md`, unchanged):

1. All four submissions are public agents. W0 is v15stack unchanged, W1 changes one constant, W3 is the "Herd-Safe LB 2700" notebook unchanged, W4 changes two constants (MEASURED, normalized diffs). Our rating can only be the public agent's rating plus noise.
2. The market is shared, premium books crash within 60 to 160 units, rank is pairwise win/loss. At the top it is same lineage against same lineage, decided by route choice, who sells premium lots first, and small economy edges.
3. What limits us is not the constants. A copy cannot out-rate its own field; a sale-horizon tweak moves sales by a few turns and is inside noise against a diverse ladder.
4. Engine facts worth checking: animals give fertilizer and scheduled product whether fed or not and only two consecutive unfed days lose them; a 12 to 13 hand crew costs 8 to 10% of a 100k bank; floor sales add no inventory; shop draws are seeded and visible.
5. 3,000 is not reachable with copies plus constant search; realistic best is the strongest public fork, about 2,600 to 2,750.

**What changed after the work and my own corpus pass** (`analyze_corpus_dedup.py`: 1,268 unique ladder games re-simulated exactly, every one reproduces the recorded banks):

- I expected a hidden mechanic behind the top-six gap. There is none. The top six feed *less* often than we do (about 0.70 vs 0.77 feeds per animal-day) and apply about twice the fertilizer to crops (213 vs 116 FERTILIZE actions a game) while selling less of it. The edge is a broader economy: three more animals by day 10, tomatoes, and better premium prices. Every trick in my point 4 is already inside the public lineage.
- I underweighted ladder mechanics. Identical W3 code read 2,191 and 2,474 at equal n (frontier_screen_2026-09-25.md); the herd-safe author reads 2,672; the 2,700 to 2,800 band is largely this lineage (field_families_2026-09-25.md). So "2,150 to 2,450" is partly path and eviction noise.
- I underestimated the tape's second half. The splice controller lost 15k from an identical day-14 board (PR 61). Execution is a moat, not only the plan.
- The gap to the actual top-10 line is smaller than the gap to the top six: on 31 faithful ranks-7-12 replays W3 wins 3 at a median of −13,817, and 0 of 22 against THIRD FARM CLUB (MEASURED, `r7to12_panel_results.jsonl`).

## 2. Audit table

| # | Conclusion | Source | Verdict | Evidence |
|---|---|---|---|---|
| 1 | W0/W1/W3/W4 are public agents with 0 to 2 constants changed | submissions/ | CONFIRMED | normalized diffs |
| 2 | Top six are reactive; their moves do not transfer as tapes | TOP6_FINDINGS §3, copyability.md | CONFIRMED | gen7_vs_w0.jsonl: Boey routes 0-20, DECEM 4-16, DSM 6-14; agreement 0.14/0.00. Not recomputed at trajectory level. |
| 3 | Top six vs tape family 79-1, median +21k | TOP6_FINDINGS §2 | CONFIRMED | Recomputed: 80-1, median +21,064 (n=81, `fingerprints_*.jsonl`). W0 panel: 6 of 38, median −21,744. |
| 4 | Gap: wool +4.6k, strawberry +3.5k, eggs +5.8k, tomato +5.6k, carrot +5k, wheat +4.6k | TOP6_FINDINGS (14 games) | Direction right, magnitudes WRONG | My medians, top six minus our seats (n=473/588): wool +3.5k, egg +3.6k, tomato +3.9k, wheat +2.7k, strawberry +2.2k, milk +1.9k, carrot +0.6k, melon −0.4k, fertilizer −2.2k. |
| 5 | Early revenue days 0-9: 21,500 vs 12,500 | TOP6_FINDINGS, decision log | WRONG | Medians 13,608 vs 13,164. The 21.5k is Boey's wheat churn (49k gross). FABLE_IDEAS §5.5 corrected it; the decision log did not. |
| 6 | Boey's order rate is churn | TOP6_FINDINGS §1 | CONFIRMED | Boey median 3,317 wheat sold, 2,924 bought (n=49). |
| 7 | Top six run 5 to 6 geese vs our 2 | TOP6_FINDINGS, FABLE_IDEAS | PARTLY | Top six median 4 (day 10), 5 (day 20); ours 2/3. M & M & P & Q (rank 2) and Azat run 0 geese. |
| 8 | Crews are the same size | FABLE_IDEAS §2 | CONFIRMED | Peak hands median 12 both. |
| 9 | Top six never buy the third quadrant (0/360) | FABLE_IDEAS §2 | WRONG | 179 of 473 top-six seats buy it; DSM 26/26, DECEM 25/33. Experiment A rested on this. |
| 10 | No CARE deficit (W0 1.04 vs 0.74-0.82) | FABLE_IDEAS R2.1, ROUND3 | CONFIRMED (approx.) | 0.94 vs 0.69 with approximate denominators. |
| 11 | Premium sells cluster at the post-drain hour (59%) | FABLE_IDEAS R2.2 | CONFIRMED, weak differentiator | 55% for top six (n=3,643) but 35% for our tapes (n=2,175); uniform 25%. |
| 12 | Slot-index front-running is exploited by the top six | FABLE_IDEAS §1 | WRONG, self-corrected R2.2 | no slot edge measured |
| 13 | Board-changing deviations lose the mirror (B 17-43, C 1-59, D 16-44) | FABLE_ROUND3_REPORT | CONFIRMED | experiments_r3 summaries. "Both get richer" mechanism rests on one game; PLAUSIBLE. |
| 14 | W1 (race44) wins the mirror | brief, decision log | CONFIRMED as small edge; UNSUPPORTED as ladder lever | Selection 19-1-4 on 12 seeds; confirmation 36-28-24 (points 0.545). Ladder: W3 beats W1 52-28; W1 read 2,107. |
| 15 | W3 already contains race44; line 3778 is shadowed | frontier §2 | CONFIRMED | line 6662 reassigns; globals read at call time |
| 16 | c042 (W4) beats W3 +0.18 / +0.13 | es_w3/REPORT.md | Measured, conclusion UNSUPPORTED | Pool = W3, W1, hsv3. Gain is vs W3 itself (0.50 to 0.80-0.90); flat vs W1. Wider gate: 0.871 vs 0.886, worse vs W1 (gate_w4). Correctly not uploaded. |
| 17 | _HP_WINDOW 7-8 beats W4 (+0.043) | es_gen2/REPORT.md | UNSUPPORTED | shrinks each stage (+0.085 to +0.043); two of five opponents are mirrors |
| 18 | W3 8-17 and W1 0-5 in the 2,500-2,800 band | 0924b report | CONFIRMED | recomputed from manifest.csv |
| 19 | WHEAT −284k is the lever | 0924b report §5 | WRONG, corrected | wheat_check.md: net −5.6k |
| 20 | Identical code reads 240 points apart | frontier §1 | CONFIRMED by their read | not recomputed |
| 21 | W3 beats 11 public agents 196-24; keep it | PR 62 | CONFIRMED as measured | pool is older forks; loses 9-11 to demand_preserving |
| 22 | W3 + front-running passes its gate (32-0 / 26-6 mirror) | PR 63 | CONFIRMED on its pool; small elsewhere | My tests, seeds 9001-9010 both seats: vs W3 16-4 (+336); vs hsv3 14-6 (+476) against W3's own 16-4 (+198) on the same seeds; k0013 20-0, farm2945 20-0, fieldcraft 18-2. Ranks-7-12 panel: identical to W3 in 60 of 60, the overlay never fires. Detector matched about 30% of W3's real ladder opponents by exact money signature, 70% of W0's and W1's. |
| 23 | Splice controller cannot ship (0-32) | PR 61 | CONFIRMED | their gate; stop rule honoured |
| 24 | DECEM shares the top-six opening | TOP6_FINDINGS §2 | CONFIRMED | 87 of 87 DECEM seats open COW 1 + WHEAT 5. The PR 61 "correction" (field_families) used 4 games from 17-22 September and is WRONG for the current DECEM. |
| 25 | Tape family tops out at 2,600-2,700 | decision log | UNSUPPORTED as hard ceiling | field_families: lineage entries at 2,900+; author at 2,672 |
| 26 | Animals must be fed every day | decision log Part 1 | WRONG | engine: escape after two consecutive unfed days; production does not check feeding |
| 27 | W2 paced-premium layer: +100 to +250 | FABLE_IDEAS §4 | WRONG | 1-19 vs W0 |
| 28 | Final rank is Bradley-Terry over 1-15 October, latest two uploads | decision log, brief | UNTESTED | cannot verify offline |
| 29 | Seat order matters | implicit | No bias | seat-0 win rate 0.511, n=1,259 decided games |

## 3. Mistakes, most costly first

1. **Slot churn (team, 21-25 September).** submissions_log.md and the plan status log record at least 12 uploads in five days: a 464-rated atlas_profile evicted the base on the 21st; four uploads on the 22nd evicted both slots and dropped the team to rank 3,508; W0/W1 evicted V56 at n=48 while it was 19-9 and climbing; V57 was uploaded and retired within a day; W1 was re-uploaded; then two W3 copies. Each upload restarts a climb that needs about 100 games, and identical code reads 240 points apart by path. Cost: the "2,150 to 2,450" framing of this review is partly self-inflicted, and no submission has been read at a settled equal-n state.
2. **Tuning the mirror against copies of itself (Sonnet prompts of 24-25 September; Claude's W1).** es_w3 (2,184 games), es_gen2 (6,980), gate_w4 (640), race44 (388) and the race sweep used pools of W3, W1, hsv3, v57. Every edge came from beating W3; the wider gate failed; W1's 0.545 edge never showed on the ladder, nor did the fork's 28-4. About 10,000 games and two days; correctly, nothing shipped.
3. **Small samples promoted into the decision log (Sonnet, 23 September).** Rows 4 and 5 came from 14 games and are wrong or overstated; the decision log was not updated after FABLE_IDEAS corrected one. Row 9 (from the earlier Fable session) spawned experiment A.
4. **The splice controller started on 25 September (PR 61, from FABLE_IDEAS §4).** About three builder-days; 0-32. The stop rule was good and honoured. The premise "executor mechanics are not the moat" was wrong. A reactive agent was the only prize path, so trying once was right; starting five days before the deadline was a scheduling error.
5. **Screening public forks after the question was closed (Billy/Sonnet, 24-25 September).** copyability.md (21 September) and TOP6_FINDINGS (23 September) had settled it; the 25 September screen's last line says stop. One to two days.
6. **Gross-instead-of-net reporting (Sonnet, 24 September).** Requested orders counted as sales; SELL revenue without BUY spend (wheat −284k). Two correction passes.
7. **Stale-data "correction" (PR 61 field_families).** Declared DECEM not top-six on four games from a week earlier; wrong today (row 24). It has not cost anything yet, but it is in a PR as fact.
8. **Faithful-panel comparisons shrunk to 16 games** (frontier §6) cannot separate anything under a ±21k spread.

## 4. What is missing

- **The 2,500-2,800 band, where our rating is decided.** W3 loses 8-17 there. 74 of its 84 opponents are tape family by the loose fingerprint, but only about 10 of 25 in that band match the exact money signature the front-running overlay needs (MEASURED, approximate). Nobody has looked at what those 25 agents are.
- **A panel against the top-10 line.** All work measured against the 3,000+ top six. The line is 2,930. My ranks-7-12 panel: W3 3 of 31 faithful, median −13,817; 0 of 22 vs THIRD FARM CLUB (Boey family), 1 of 5 vs Arda Ceylan. About 7k of the famous 21k is the top six being unusually strong.
- **Feeding cadence.** Top six feed about 0.70 per animal-day; the engine tolerates alternate-day feeding at the cost of the CARE bonus only. Nobody priced wheat saved against product lost.
- **Fertilizer application vs sale.** 213 vs 116 FERTILIZE actions; a "hold fertilizer for strawberry and tomato" flag was listed and never tested.
- **Tomato.** Our lineage plants none (median 0); ten of the top twelve do. D4/D8 only swapped wheat for carrot.
- **Ladder convergence.** No one measured how many games a fresh upload needs, or compared the two W3 copies at equal n.
- **Ties.** 36 to 44% of W3's tape games end within ±500; how Kaggle rates ties is unknown to the team.

## 5. Is 3,000 reachable?

**No.** Confidence about 90%. INFERENCE from: (a) every agent we hold wins about 3 of 16 faithful top-six games at a median near −21k, and 3 of 31 against ranks 7-12 at −13.8k; (b) the one reactive attempt lost 0-32 by 17k to 20k after three builder-days; (c) 2,930 requires beating rank-7-12 reactive agents more than half the time, and we win 10%; (d) four days remain, an upload freeze is on, and a rating needs about 100 games to settle. What it would take: a reactive agent at or above 50% on the ranks-7-12 faithful panel that keeps W3's record against the tape band. That is weeks. The first test that would show it working is a day-14 identical-board handover that is not negative; PR 61 never got near it.

**Best realistic finish.** W3 in both slots, already active. In the October tournament W3 should land where its lineage lands, about 2,600 to 2,750, which on the 24 September board is rank 57 to 240 (MEASURED, leaderboard CSV). The only slot-2 candidate that is not a coin flip is W3 + front-running (PR 63): equal to W3 where the overlay does not fire, +336 mean in the W3 mirror, no regression I could detect (row 22). Worth tens of points at most.

## 6. Ranked plan to 30 September

1. **Hold W3 in slot 1. No uploads except to fill a broken slot.** This is the stop.
2. **Slot 2: W3 + front-running, one upload by 28 September, if the team accepts a small positive with bounded risk.** Evidence for: rows 22. Evidence against: the detector matches only about a third of W3's real opponents and 14-6 vs hsv3 against W3's 16-4 is a possible sibling-fork regression at n=20. Stop rule: if a 40-game W3-vs-hsv3 paired rerun on fresh seeds shows front-running below W3 by more than two wins, keep W3 ×2.
3. **Stop:** constant searches, public-fork screens, the splice controller, corpus re-downloads, and any test whose pool is only our own files.
4. **Read the ladder once, correctly.** On 29 September compare the two active submissions at equal n and field within 150 points, and log it. Stop rule: if within 100 points, do nothing.
5. **For the record, not for rating:** price feeding cadence and fertilizer application from the corpus. Stop rule: build nothing from it before the deadline.

## 7. Least sure

1. That W3's tournament rating lands at the lineage level (2,600 to 2,750) rather than its current 2,200 to 2,450 read. An equal-n comparison of the two W3 copies, or knowledge of how the October tournament seeds ratings, would change this.
2. That front-running is net positive on the ladder. It fires on roughly 30 to 70% of opponents depending on which band we sit in, and the hsv3 result is within noise. A paired 40-game rerun would settle it.
3. That the top-six gap cannot be closed in four days. A day-14 handover at −8k or better would make me revise; nothing in the record reaches it.

## 8. Tests I ran (242 games, all under review_fable/)

- 1,268 unique ladder games re-simulated exactly (`summarize_replays.py`, `analyze_corpus_dedup.py`, `fingerprints.py`).
- W3 and W3+front-run on 60 ranks-7-12 replays at their original seed and seat (`r7to12panel.py`, faithful = tape bank within 5%).
- Front-run vs W3, hsv3, k0013, fieldcraft, farm2945, seeds 9001-9010 both seats (`frontrun_pool.jsonl`); W3 vs hsv3 on the same seeds (`w3_vs_hsv3_ref.jsonl`).
- One note on the prompt: it says the pair reads 2,150 to 2,450. The active pair since 25 September is two W3 copies, one of which (2,191) is younger and met a weaker field; the two numbers are not two agents.
