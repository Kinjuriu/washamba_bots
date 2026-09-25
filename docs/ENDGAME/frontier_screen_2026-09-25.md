# Frontier screen and live-pair audit, 2026-09-25

Method: the endgame campaign's (`docs/superpowers/plans/2026-09-21-endgame.md`). Per-episode
ladder read at equal n, a frontier screen of public notebooks, and a paired pool harness
(`harness/pool_harness.py`, kaggle-environments 1.32.7, both seats). Read the win count before
the mean. Nothing was submitted or committed. Extracted public agents stay out of the repo,
following the V56 convention.

## Result

**Keep W3 (`agents/w3_herdsafe2700.py`). Nothing screened today beats it across the field.** For the
second slot, the only measured improvement on W1 is another copy of W3 (§7).

This reverses the first draft of this note, which recommended `demand_preserving`. That agent beats
W3 head to head, 56-16 over 72 games. It is still the worse agent:

- **Against the field** (§6, 11 public opponents × 20 games, the same seeds for both): W3 goes
  **196-24**, `demand_preserving` goes **142-60-18**. It wins fewer games against almost every opponent.
- **Against the top six** (§6, faithful replay panel): no edge. Paired against W3 on the 16 games
  faithful under both, it is -2,840 mean and better on only 6 of 16.
- **Self-play bank** $798 below W3's (90,711 vs 91,509), which fails the plan's $300 gate.

It is a narrow counter to W3, not a stronger agent. The field is non-transitive, the same kind of
cycle the 2026-09-24 screen found. **A head-to-head win against our own agent is not evidence of a
better agent; screen every candidate against the field before calling it.**

The honest ceiling is unchanged. Against the top six, every agent tested wins about 3 of 16 at a median
margin near -21,000. No candidate here closes that gap.

## 1. Ladder read (`experiments/ladder_episodes.py`, fetched 2026-09-25)

The first 20 episodes of each submission are the opening burst and are excluded.

| submission | file | score | post-burst n | W-L | mean margin | opponents |
|---|---|---|---|---|---|---|
| 56518334 | W3, upload 1 | 2,433.3 | 86 | 38-48 | -538 | 76 rated 2,400-2,700 |
| 56532456 | W3, upload 2 | 2,191.1 | 64 | 26-38 | -1,141 | all rated 2,000-2,400 |
| 56521297 | W1 | 2,107.5 | 95 | 40-55 | -782 | 92 rated 2,000-2,400 |

- **Identical code, 240 points apart.** At n=84 the two W3 uploads read 2,191.1 and 2,473.8, but
  their opponents averaged 2,043 and 2,212. The fields are 169 apart, so the tool flags the pair
  as not comparable. This is a second measurement of the ladder's noise floor, after the
  `55591700`/`55606684` pair.
- All three win under half their post-burst games. We sit at the equilibrium of a band of copies.

Derivation of the pooled margins: 56518334 = (10 × -288 + 76 × -571) / 86 = -538;
56521297 = (3 × -544 + 92 × -790) / 95 = -782.

## 2. What the live pair actually runs

- **W3 already contains W1's lever.** A late override in W3 (`# EXP389 frozen market-race
  reservation horizon`, line 6662) sets `V9_RACE_DEFAULT = 44`, `V9_RACE_MAX = 48`. It shadows the
  `= 40` at line 3778. A `sed` on line 3778 is therefore a no-op: W3+race44 and W3+race48 built that
  way were game-for-game identical to W3 over 160 games. Edit the override, not the first definition.
- **W3 beats W1**: 26-14 (+166, seeds 5001-5020) and 26-14 (+209, seeds 7001-7020). W1 adds nothing
  as the second slot.

## 3. Race-horizon sweep on W3 (the only overlay class that won mirrors, per `FABLE_ROUND3_REPORT.md`)

Edited at the override line. Seeds 5001-5020, both seats.

| variant | vs W3 | vs W1 | vs W0 |
|---|---|---|---|
| race 40 / max 48 | 4-34-2, -153 | 28-12, +237 | 32-8, +391 |
| **race 48 / max 52** | **20-4-16, -5** | 30-10, +261 | 34-6, +431 |
| race 52 / max 56 | 18-6-16, -12 | 26-14, +237 | 32-8, +433 |

The race 48 result held on seeds 7001-7020: 26-8-6 vs W3 (+106), with self-play equal to W3's
(91,495 vs 91,509). Pooled vs W3: **46-12-22, mean +50** = (40 × -5 + 40 × 106) / 80.

Verdict: a real mirror edge at no absolute cost. But +$50 is far below the ~$1,000 the ladder can
see, and the fork's 28-4 mirror edge never showed on the ladder (2026-09-22 read). Against
`demand_preserving` it changes nothing (8-32, same as W3). **Not worth a slot.** It is a free add-on
if W3 is re-uploaded for another reason.

## 4. Frontier screen: public notebooks newer than the 2026-09-24 screen

Pulled with `kaggle kernels pull`. Agents were decoded by AST (literal evaluation plus a whitelist of
decode calls, never executed). Every notebook-published sha256 matched. Gate: self-play seed 0, DONE/DONE,
neither reward 3,000. Screen: seeds 6001-6008, both seats (16 games).

| ref | author | date | gate | vs W3 | vs W1 | verdict |
|---|---|---|---|---|---|---|
| tetsutani/demand-preserving-turn-sale-timing | tetsu2131 | 09-24 | pass | 8-8, +82 | 12-4, +429 | **follow-up, see §5** |
| evgendvorkin/kaggriculture | Дворкин Е. В. | 09-24 | pass | 8-8, +82 | 12-4, +429 | same results as the row above |
| haideptry/the-shepherds-ledger-herd-safe-sovereign | haideptry | 09-24 | pass | 4-10-2, -188 | 10-6, +208 | reject |
| arsgorynich/herd-safe-v3-experimental-risk-aware-feed | Arsgorynich | 09-23 | pass | 4-10-2, -188 | 10-6, +208 | reject |
| haodou092/kaggriculture-harvest-ledger | haodou092 | 09-24 | pass | 6-10, -829 | 8-8, -196 | reject |
| ahmedberatozer/kaggriculture-v57-funding-order-invariant | A. B. Özer | 09-22 | pass | 6-10, -749 | 2-14, -1,147 | reject; 0-16 on 6009-6016 |
| statma/kaggriculture-herd-safe-sale-window-race-ca25 | statma | 09-23 | pass | 4-12, -580 | 2-14, -389 | reject |
| statma/kaggriculture-herd-safe-sale-window-race-ca20 | statma | 09-23 | pass | 4-12, -658 | 2-14, -466 | reject |
| dmitriigluzdov/kaggriculture-more-wheat-smarter-sales | D. Gluzdov | 09-22 | pass | 4-12, -417 | 4-12, -302 | reject |
| hanifnoerrofiq/pioneers-of-kaggle-town-candidate-2 | H. N. Rofiq | 09-24 | pass | 4-12, -385 | 4-12, -268 | reject |
| aurax7/kaggriculture-shop-router-reactive-v7 | Yaxon | 09-17 | pass | **0-16, -3,440** | 16-0, +12,912 | reject (margin trap, as on 09-24) |
| leoprovorov/a-song-of-ice-and-fire-fixed-flexible | AlekseiProvorov | 09-25 | **fail**: both seats 3,000 | — | — | broken as published |

- `abhinav0370/cha22-agent` and `guruprasaathas111/kaggriculture-master-engine-v3` are
  **byte-identical** to `demand_preserving` (sha256 `127ed3e6…`).
- `a-song-of-ice-and-fire` ends with `agent = install_water_repair_local_patch(agent)`. The factory is
  a new name added after `agent`, so Kaggle's last-callable loader runs the factory. That is the
  gotcha in `CLAUDE.md`, "Agent I/O contract".
- `georgymamarin/kaggriculture-what-2600-farms-do-differently` is a dashboard over an external
  dataset, not an agent. Its claims match ours: ladder spread is matchup rather than engine dice,
  head to head is non-transitive, and identical openings before turn ~48 are engine determinism.
- **W3 now beats V57**, the previous screen's pick: 6-26 from V57's side over two seed sets.

## 5. `demand_preserving`: what it is, and the confirmation

A W3 sibling, not a new family. It has the same v15stack/V39 chassis and attribution header, and its
diff against W3 is about 2,000 lines (tail layers and the race block). Apache-2.0, with upstream
notices retained. sha256 `127ed3e62988c0474d386db6527ae8ca9de9bb1fe7004128557ddef67126c652`.

Gates:
- Self-play seed 0: DONE/DONE, 71,702 / 72,340.
- Timing: **max 101 ms/turn, mean 1.3 ms** over 719 turns (in-process timer, seed 0).

Record vs W3, by seed set:

| seeds | W-L | mean margin |
|---|---|---|
| 6001-6008 | 8-8 | +82 |
| 6009-6016 | 16-0 | +1,479 |
| 7001-7020 | 32-8 | +913 |
| **pooled, 72 games** | **56-16** | **+854** = (16 × 82 + 16 × 1,479 + 40 × 913) / 72 |

Per seed on 7001-7020 (margin, identical in both seats): 856, 206, 299, 880, 882, 1,776, 5, 4,530,
2,828, 159, -222, 1,789, -13, -24, 464, 1,666, 201, -644, 1,109, 1,509. That is 16 positive and
4 negative, and no loss is bigger than $644. Pooled vs W1 and the 2945 Farm:
(16 × 429 + 40 × 1,126) / 56 = +927 and (16 × 1,614 + 40 × 2,274) / 56 = +2,085.

## 6. Robustness tests: field and top six

### Field (`harness/pool_harness.py`, seeds 8001-8010, both seats, 20 games per cell)

| opponent | W3 | `demand_preserving` | W3 + race48 |
|---|---|---|---|
| statma ca20 | 20-0, +1,116 | 13-7, +472 | 20-0, +1,131 |
| statma ca25 | 20-0, +1,059 | 13-7, +348 | 20-0, +1,059 |
| more_wheat | 20-0, +991 | 11-9, +468 | 20-0, +1,028 |
| pioneers2 | 20-0, +956 | 12-8, +454 | 20-0, +992 |
| V57 | 20-0, +1,559 | 16-4, +806 | 20-0, +1,395 |
| reactive_v7 | 20-0, +3,254 | 20-0, +2,664 | 20-0, +3,248 |
| 2945 Farm | 20-0, +2,025 | 20-0, +2,057 | 20-0, +1,974 |
| shepherds_ledger | 19-1, +446 | 12-8, +372 | 17-3, +616 |
| harvest_ledger | 14-6, +362 | 12-8, +461 | 14-6, +346 |
| W0 (v15stack) | 14-6, +702 | 12-8, +742 | 12-8, +546 |
| evgendvorkin | 9-11, -260 | 1-1-18, +0 | 9-11, -219 |
| **total, 220 games** | **196-24** | **142-60-18** | **192-28** |

### Top six (faithful replay panel, 80 recorded top-six games replayed on their own seed and seat)

The 80 replays were re-downloaded from `kaggleusercontent.com/episodes/` into the scratchpad (not
committed). The runner, `harness/panel_local.py`, reproduces the documented W0 baseline exactly: **6 wins of 38, median -21,744**
on `harness/faithful_eps.json`, so the harness is trusted. Faithful means the tape's bank stays within
5% of its recorded bank.

| agent | faithful games (of 80) | on the 16 faithful under W0, W3 and dp: wins | median margin | mean bank |
|---|---|---|---|---|
| W0 | 38 | 3 | -21,098 | 91,648 |
| W3 | 46 | 3 | -20,292 | 92,525 |
| `demand_preserving` | **25** | 3 | -21,666 | 89,641 |

`demand_preserving` wins 48 of all 80 games, but that is the frozen-tape artefact the Sept 21 log
warns about. It pushes the recorded top-six moves off their original path in 55 of 80 games, and a
frozen tape that has lost its path collapses where a live reactive agent would adapt. Only the faithful
subset counts.

## 7. Second slot

W1 is dominated: W3 beats it 52-28 over seeds 5001-5020 and 7001-7020. The two W3 uploads read
2,433 and 2,191 on identical code, and team score is the better of the two active submissions. So a
second W3 upload replacing W1 is a free extra draw at W3's strength. W3 + race48 is the same agent
against the field (192-28 vs 196-24) and wins the W3 mirror 46-12-22. It is an equal alternative if
the band fills with W3 copies, but it is not a measured improvement.

## Next steps

1. Team decision: replace W1 with a second W3 (or W3 + race48). Agree with Stephane; the upload
   evicts W1, the older active submission.
2. Log it in `docs/ENDGAME/submissions_log.md`. Compare only at equal n with opponent fields within 150.
3. Stop screening public forks of this family. The gap that matters is the top six's ~-21,000, and it
   needs the reactive track in `docs/research/TOP6_FINDINGS_2026-09-23.md` §4, not another fork.
