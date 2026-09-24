# T11 — the near-copy fork that beats the base, reproduced and measured

**Date 2026-09-21, night.** Target: the `WHEAT 20/15 + BUY_SEED WHEAT 1` fork that
`docs/ENDGAME/ladder_diagnosis_56431632.md` §2 finds on **11 post-burst ladder games at
2-9, −896** against our live submission `56431632` (= `agents/public_farm2945.py`).
Build: `agents/washamba_base_v1_fork.py` (base byte-verbatim, overlay appended, `agent`
last, two flags at the top, behaviour-identical when off). Tests:
`tests/test_washamba_base_v1_fork.py` (16, stdlib `unittest`); full suite 284 OK.
No existing agent, `main.py`, test or doc was edited. Nothing committed, nothing
submitted, no `ListEpisodes` call, no dataset download.

---

## 0. Answers up front

| question | answer |
|---|---|
| **Is the extra `BUY_SEED WHEAT 1` the tweak?** | **No.** Fed to the unmodified base it is **inert** — the seed is never planted and the `_CA` telemetry is byte-identical (`ca_swaps` 21, `ca_feed_block` 48, bank 92,543 → 92,532 on `111661624`). It is a fingerprint of a build with two other edits. |
| **What are the real edits?** | **A.** The `_CA` carrot layer's feed reserve is **1 day, not 2** (`_CA_FEED_DAYS`). **B.** One extra wheat cycle is grown on tile **(2,4)** before that tile becomes a pasture — the extra seed at step 0 is what funds it. |
| **Why does one wheat seed move eleven carrots?** | It doesn't. The carrots move because of **A**, which is a different edit that happens to travel with the same build. See §2. |
| **Is it one fork or several?** | **One**, on all 11 (10 distinct submissions, 10 distinct teams). Two sub-variants differ only in *when* the extra wheat is harvested: day 3 (9 of 11) or day 2 (2 of 11). |
| **Does the reproduction work?** | **Partly, and the gap is measured.** Seated in the **fork's own seat** against the live base, the opening is byte-exact on the **9 majority-form episodes** (first divergence ≥ step 91) and the season bank lands within **−1,023…+1,225** of the fork's recording, beating the base on **11 of 11** — but reproducing only **+350 of the fork's +896** edge. §3. |
| **Ship?** | **No.** Mirror-vs-base passes (28-4, +191), fork tapes near-miss (10-12 of 22), **absolute self-play fails by 3,180** — and all of that failure is one seed, for a named reason (§5). |

---

## 1. The full action diff, all 720 steps, all units, all market orders

Both tapes come from the downloaded replays in `experiments/endgame/rep/`; the base
reproduces **both** recorded banks to the dollar on all 11, so the diff is exact.

| episode | seat | seed | margin | opp submission |
|---|---:|---:|---:|---:|
| 111661624 | 0 | 633939918 | −2,378 | 56430883 |
| 111663604 | 0 | 1239871650 | −2,222 | 56415919 |
| 111673167 | 1 | 1298100494 | −2,661 | 56424794 |
| 111674389 | 0 | 909044638 | −50 | 56391644 |
| 111677802 | 0 | 1053563432 | **+519** | 56424507 |
| 111678199 | 0 | 1334389667 | −448 | 56431434 |
| 111687490 | 1 | 152283595 | **+734** | 56418371 |
| 111687255 | 1 | 462407937 | −1,169 | 56434293 |
| 111690678 | 1 | 1278881831 | −75 | 56424507 |
| 111693073 | 0 | 1958074022 | −1,593 | 56433304 |
| 111699696 | 1 | 1406557049 | −515 | 56413985 |

**First divergence is step 0 on all 11, in the market only; the first labour divergence is
step 2 on all 11.** Whole-season counts (sum over the 11, ours vs theirs):

| | ours | fork | Δ |
|---|---:|---:|---:|
| `PLANT WHEAT` | 1,677 | 1,634 | **−43** |
| `PLANT CARROT` | 456 | 501 | **+45** |
| `BUY_SEED CARROT` (units) | 504 | 549 | +45 |
| `BUY_SEED WHEAT` (units) | 1,705 | 1,671 | −34 |
| `PASS` | 5,385 | 5,205 | **−180** (≈16/season) |
| `WATER` / `HARVEST` / `WEST` | 12,021 / 5,331 / 9,579 | 12,058 / 5,353 / 9,628 | +37 / +22 / +49 |
| `BUILD_PASTURE`, `FEED`, `CARE`, `HIRE`, `PLANT MELON/STRAWBERRY/TOMATO` | — | — | **equal or ±3** |

The `PASS` gap is on **all 11**; the crop-mix gap is on **4 of 11** (111661624 52→73,
111663604 65→77, 111673167 49→58, 111690678 54→57) and those four are three of the four
worst losses. The other **7 have byte-equal crop counts** — a falsifier that any candidate
mechanism has to survive, and one that kills "the fork just plants more carrot everywhere".

### 1.1 Edit B — the opening, recovered verbatim

Diffing steps 0–71 and grouping by signature gives **exactly two forms**, and every unit is
standing on the **same tile as ours** at every diffed step, so this is not a layout change:

```
s0   MKT   + ["BUY_SEED","WHEAT",1]
s2-4 hand1 PASS  -> WEST,WEST,WEST      (5,4) -> (2,4)
s5   hand1 PASS  -> PLANT WHEAT         (2,4)
s6   hand1 PASS  -> WATER               (2,4)
s29  hand2 BUILD_PASTURE -> WATER       (2,4)   <- the pasture is DEFERRED
s49-51 hand0 PASS -> WEST,WEST,WEST     (5,4) -> (2,4)
s52  hand0 PASS  -> WATER               (2,4)
   9 of 11:  s84-91  hand0 EAST,EAST,WATER,HARVEST,BUILD_PASTURE,EAST,EAST,DROP
   2 of 11:  s53-57  hand0 HARVEST,BUILD_PASTURE,EAST,EAST,DROP
```

`BUILD_PASTURE` on (2,4) moves from **step 29** (ours) to **step 88** (9 of 11) or **step
54** (2 of 11). Both sides build **14 pastures** in total, at identical steps otherwise.
So: *grow one wheat crop on the tile before turning it into a pasture, using a hand the
tape leaves idle, and pay one extra wheat seed for it.* The `SELL WHEAT` adjustments at
steps 57/79/80/91 are **not** part of the edit — they are the base's own sell layers
reacting to a different shed, and our reproduction emits the same ones.

**Only the harvest timing distinguishes the two sub-variants**, so they are one build with
a reactive harvest rule, not two forks. The 9-episode form is the one reproduced.

---

## 2. Mechanism, traced — not the seed, and not `V9_CARROT`

Instrumented by importing the base as a module and wrapping `agent` and `Chassis.act`; the
file on disk was never touched, and every trace reproduces **both** recorded banks to the
dollar. Traced on `111661624` (seed 633939918).

**`V9_CARROT` is not involved. It fires zero times.** Its gate (l.3052–3098) needs
`10 ≤ day ≤ 23`, `ratio ≥ 1.8` **and** `wheat_held ≥ 40`. The traced season reaches
ratio 1.8 only on **day 21**, by which time the shed holds **31–34** wheat. Both conditions
are missed by a small margin all season; `carrot_swaps = 0`.

**The layer that actually decides carrot vs wheat is `_CA` (l.4590–4720, days 6–28).** It
scores each `PLANT WHEAT` tile-cycle against a carrot one on the unit's real future visits,
and **aborts the whole swap loop** when

```python
wheat_ok = _ca_wheat_total(observation) >= _ca_feed_need(seat, step, _CA_FEED_DAYS)
if not wheat_ok:
    _CA_REPORT["ca_feed_block"] += 1
    break
```

Per-day trace, our base, seed 633939918:

| day | carrot/wheat ratio | `pays_now` | wheat held | `_ca_feed_need(…, 2)` | `ca_swaps` | `ca_feed_block` |
|---:|---:|---|---:|---:|---:|---:|
| 15 | 1.39 | True | 24 | 34 | 0 | 3 |
| 16 | 1.51 | True | 25 | 34 | 0 | 10 |
| 17 | 1.57 | True | 36 | 34 | 3 | 12 |
| 19 | 1.74 | True | 34 | 34 | 3 | 20 |
| 20 | 1.79 | True | 29 | 34 | 3 | 25 |
| 22 | 1.94 | True | 31 | 34 | 3 | 38 |
| 24 | 2.23 | True | 30 | 28 | 10 | 45 |
| 29 | 3.33 | True | 38 | 0 | 21 | **48** |

**48 aborted turns a season, every one of them 0–10 wheat units short of a two-day feed
reserve.** The swap is economically live (`pays_now` True from day 15) and is refused on a
feed-safety check, not on price.

**The fork is not clearing that gate with stock — it holds a shorter reserve.** Read from
the engine in a $0-exact local reproduction, the fork's own wheat total is **lower** than
ours from day 18 on (27 vs 36, 16 vs 34, 18 vs 29, 25 vs 34, …) and it still swaps more.

Sweep, 11 episodes, frozen fork tapes:

| `_CA_FEED_DAYS` | record | mean margin | crop mix within ±2 of the fork |
|---|---|---:|---:|
| **2 (base)** | 2-9 | −896 | 7/11 (the 7 no-op seeds) |
| **1** | 2-9 | **−663** | **10/11** (exact on 9) |
| 0 | 5-6 | −482 | 8/11 — **overshoots** (86 carrot vs the fork's 77) |

`_CA_FEED_DAYS = 1` is **an exact no-op on the 7 crop-identical episodes** — it clears the
falsifier — and reproduces the fork's mix on the four that differ. `0` is a different
agent, not this fork.

So: **the extra wheat seed does not move eleven carrots.** Edit B moves the wheat seed and
about sixteen idle unit-turns; edit A moves the carrots. They travel together in one build,
which is why the diagnosis saw them as one fingerprint.

---

## 3. Reproduction

### 3.1 The decisive test — candidate in the **fork's** seat, live base in ours

If the candidate *is* the fork, this reconstructs the recorded game and both banks come
back. Both agents are real files (the base reacts), on the recorded seed:

| episode | candidate | fork's recorded | Δ | live base | base's recorded | first divergence from the fork's tape |
|---|---:|---:|---:|---:|---:|---:|
| 111661624 | 95,631 | 94,921 | +710 | 93,533 | 92,543 | 91 |
| 111663604 | 60,680 | 61,292 | −612 | 60,061 | 59,070 | **53** |
| 111673167 | 74,401 | 75,424 | −1,023 | 74,307 | 72,763 | 91 |
| 111674389 | 124,411 | 124,427 | −16 | 124,191 | 124,377 | **53** |
| 111677802 | 128,066 | 127,489 | +577 | 127,968 | 128,008 | 295 |
| 111678199 | 69,642 | 69,790 | −148 | 69,533 | 69,342 | 253 |
| 111687255 | 152,350 | 152,945 | −595 | 152,244 | 151,776 | 91 |
| 111687490 | 93,660 | 92,435 | +1,225 | 93,554 | 93,169 | 91 |
| 111690678 | 64,651 | 64,276 | +375 | 64,469 | 64,201 | 253 |
| 111693073 | 90,718 | 91,016 | −298 | 90,611 | 89,423 | 91 |
| 111699696 | 112,557 | 112,990 | −433 | 112,450 | 112,475 | 91 |

**0 of 11 reproduce to the dollar** — say "reproduces to within ±1,225", not "reproduces".
What *is* exact: **the opening.** Step 91 is the last scripted step, so the 9 episodes with
`first_divergence ∈ {91, 253, 295}` match the fork's action stream **byte-for-byte through
step 90** — and the only two that diverge earlier, at **step 53**, are exactly the two
minority-form episodes whose fork harvests a day early (§1.1). The residual is the `_CA`
half: the fork's swap rule is reproduced in *effect* (10 of 11 crop mixes within ±2) but
not in *code*, and the last two carrots on `111661624` (71 vs 73) are inside that gap.

**The candidate beats the live base from the fork's seat on 11 of 11, mean +350.** The
fork's own recorded margin over the base is **+896**, so this build recovers about **39%**
of the fork's edge over the base.

### 3.2 Frozen-tape harness — our seat vs the fork's recorded tape

`agents/washamba_base_v1_fork.py` with both flags on, seated where we really played, on the
recorded seed, against the fork's own recorded tape:

| episode | our bank | base's recorded bank | fork's recorded bank | margin | base's margin |
|---|---:|---:|---:|---:|---:|
| 111661624 | 94,478 | 92,543 | 94,921 | **+140** | −2,378 |
| 111663604 | 57,878 | 59,070 | 61,292 | −1,829 | −2,222 |
| 111673167 | 72,738 | 72,763 | 75,424 | −2,443 | −2,661 |
| 111674389 | 124,390 | 124,377 | 124,427 | **+60** | −50 |
| 111677802 | 128,072 | 128,008 | 127,489 | **+608** | +519 |
| 111678199 | 69,400 | 69,342 | 69,790 | −346 | −448 |
| 111687255 | 151,835 | 151,776 | 152,945 | −1,060 | −1,169 |
| 111687490 | 93,228 | 93,169 | 92,435 | **+843** | +734 |
| 111690678 | 64,348 | 64,201 | 64,276 | **+106** | −75 |
| 111693073 | 89,468 | 89,423 | 91,016 | −1,488 | −1,593 |
| 111699696 | 112,541 | 112,475 | 112,990 | −409 | −515 |
| **mean** | **96,216** | 96,104 | | **−529** | **−896** |

**Better than the base's recorded margin on 11 of 11**; record **2-9 → 5-6**; all
`['DONE','DONE']`, no $3,000. It reaches or beats the fork's recorded bank on **3 of 11**,
not 11 — because with the flags on the game is fork-vs-fork, not fork-vs-base, and the
frozen tape cannot respond to the book we now crowd. That asymmetry is the
`ladder_replay.run()` caveat, stated in its own docstring, pointing the *other* way for
once: here it makes the reproduction look worse, not better.

---

## 4. Measurements

All on `experiments/tapes/run_agents.py`, both seats, `timeout 2400`. Base self-play
**89,667.3** reproduces `v2_results.md` §1.2 exactly, so the harness is calibrated.

| build | mirror vs base, seeds 300-315 ×2 seats | self-play mean, seeds 300-307 ×2 seats | self-play min | vs `router_yuan_nf_trim`, 8 seeds ×2 | vs the 11 fork tapes ×2 seats |
|---|---|---:|---:|---|---|
| `public_farm2945` (control) | — | **89,667** | 61,836 | 16-0, +15,982 | 4-18, −896 |
| **A only** (`_CA_FEED_DAYS=1`) | 15-5 of 32 (12 ties), +74 | 89,252 (**−416**) | 58,430 | — | 4-18, −663 |
| **B only** (the opening) | **30-2 of 32**, +115 | 86,895 (**−2,772**) | 61,878 | — | 8-14, −760 |
| **A+B — the shipped file** | **28-4 of 32, mean +191** | **86,488 (−3,180)** | 58,498 | **16-0, +17,310** | **10-12 of 22, −529** |

Per-seed mirror margin (A+B): `300:+351 301:−720 302:+238 303:+739 304:+425 305:+106
306:+799 307:+107 308:+106 309:+101 310:+109 311:+106 312:+194 313:+109 314:+106 315:+179`
— positive on 15 of 16 seeds; the deterministic ≈+107 floor is lever B, the large swings
are lever A.

**The fork does not bank less against the base — only against itself.** On seeds 300-307,
fork-vs-base banks **89,696** against base-vs-base's 89,667, while the base opponent drops
to 89,441. The −3,180 appears only when *both* seats run the fork.

Seed-0 pre-submit gate on the shipped file: **`['DONE','DONE']`, 72,281 / 72,943** (base:
72,101 / 72,762) — no $3,000. Timing, 720 turns: mean 2.2 ms, p99 7.3 ms, **max 153 ms**
against a 1,000 ms `actTimeout`.

---

## 5. Why self-play fails, and it is one seed with a name

Per-seed self-play mean bank:

| seed | base | A only | B only | A+B |
|---:|---:|---:|---:|---:|
| **300** | **106,394** | 106,426 | **84,253** | **84,253** |
| 301 | 61,836 | 58,430 | 61,878 | 58,498 |
| 302–307 | — | ±100 | ±100 | ±100 |

**The entire −3,180 is seed 300 losing 22,141 to lever B**, and seed 300 is the one seed in
this range where the base's day-18 `_v219` program (tomato + `BUY_LAND` + ~22 hires) fires
(`v2_results.md` §1.2, `v3_results.md`). Action histogram, base vs B-only on seed 300:
`PLANT TOMATO 10 → 0`, `BUY_SEED TOMATO 1 → 0`, `PLACE TOMATO 9 → 0`, `SELL TOMATO 11 → 6`
— **`_v219_qualifies` (evaluated once, at step 432) now returns False.**

**Qualify that carefully: it is not lever B's own footprint.** On the same seed 300, with
lever B in one seat and the *base* in the other, the candidate banks **107,368 / 105,997**
— v219 still fires, and B wins. The disqualification appears only when **both** seats run
B, i.e. it is a function of the shared market state `_v219_qualifies` reads at step 432,
not of B's local cash or structures. That is the same asymmetry as §4's "does not bank
less against the base — only against itself", and it is the whole of the self-play failure.

This is the **third** time this exact trap has been measured on this base:
`late_overlay_results.md` L1 ("the base already has a shop-gated tomato program and L1's
tomatoes disqualify it"), `v2_results.md` lever A, and now lever B. Generalises, and it is
now earned rather than argued: **on `farm2945`, any early-game edit that moves money or
structures must be checked against `_v219_qualifies` at step 432 before its self-play
number is believed.** A small, obviously-local change 400 steps earlier is not local.

Lever A's own worst seed (301: 61,836 → 58,430) is a separate, smaller effect and sits
inside the ±1,131 identical-code noise floor on a single seat-result.

---

## 6. Verdict — no-ship

| ship criterion | result | |
|---|---|---|
| mirror vs base ≥ 20-12 **and** mean ≥ 0 | **28-4, +191** | **PASS** |
| vs the fork tapes ≥ even | **10-12 of 22** (base 4-18) | **near-miss** |
| self-play ≥ 89,667 − 300 = 89,367 | **86,488** | **FAIL by 2,879** |

**Not shipped.**

> **Deliberate deviation from repo convention, flagged for the caller.**
> `agents/farm2945_v2.py`, `_late.py` and `_v3.py` all ship *no-ship* overlays with their
> flags at the base's own values, so an accidental submit is the base. **This file ships
> with both flags ON**, because the brief's deliverable is the fork reproduction and the
> flags are the reproduction. If the file is to sit in a submission slot, set
> `FORK_CA_FEED_DAYS = None` and `FORK_OPENING = False` first — that restores the base
> bit-for-bit, pinned by `test_flags_off_is_behaviour_identical_to_the_base`.

**What is worth keeping from it:**

1. **The fork's advantage is real and now explained.** It is not front-running, not sell
   timing and not the wheat seed: it is a **one-day feed reserve in `_CA`** instead of two,
   which converts 48 refused turns a season into carrot swaps, plus a free wheat cycle on a
   tile the tape was about to pave. Against the base it is worth ≈ +190 a season, which is
   the size of the whole ladder deficit the diagnosis measured.
2. **Lever A alone is the mechanism-true half** and the one a future attempt should start
   from: −416 self-play (inside noise), +74 mirror, and it carries the harness from −896 to
   −663 on its own. It fails the win-count bar (15-5 with **12 exact ties** of 32), so it is
   *unresolved*, not rejected — it needs more seeds, not a new idea.
3. **Lever B is closed.** +115 mirror on a deterministic ≈+107 is not worth a 1-in-8 chance
   of disqualifying `_v219` for −22,000.
4. **Nine levers on this base, nine rejected.** The one that changed is *why*: this is the
   first one whose full mechanism was recovered from an opponent's recorded tape rather
   than invented, and it still does not clear the bar.

---

## Reproduce

```bash
PY=.venv/Scripts/python.exe
# the 11 fork episodes are already cached in experiments/endgame/rep/
$PY -m unittest tests.test_washamba_base_v1_fork          # 16 tests
$PY -m unittest discover -s tests                         # 284 OK
$PY experiments/tapes/run_agents.py agents/washamba_base_v1_fork.py 300 316 \
     agents/public_farm2945.py fam/fork_mirror.jsonl      # mirror, 28-4
$PY experiments/tapes/run_agents.py agents/washamba_base_v1_fork.py 300 308 \
     agents/washamba_base_v1_fork.py fam/fork_self.jsonl  # self-play, 86,488
$PY experiments/tapes/run_agents.py agents/washamba_base_v1_fork.py,agents/public_farm2945.py \
     300 308 agents/router_yuan_nf_trim.py fam/fork_nf.jsonl
```

§3.1 (candidate in the fork's seat vs the live base), §3.2 (frozen fork tapes) and the
per-day `_CA` trace of §2 were run from throwaway scripts in the session scratchpad; each
one only imports `experiments/endgame/{replay_tools,ladder_replay,make_tape_agent}.py` and
seats `agents/*.py` files, so they are a dozen lines to rebuild from the tables above.
Nothing under `experiments/` or `agents/` other than the new file was modified.
