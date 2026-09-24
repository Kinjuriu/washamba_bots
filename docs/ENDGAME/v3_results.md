# T5e — v219 settled, and `agents/farm2945_v3.py`: the goose-tail swap, measured

**Date 2026-09-21.** Base: `agents/public_farm2945.py` (thomastschinkel's "2945 Farm",
Apache-2.0, submission `56269928`), **unmodified** — as are `agents/farm2945_v2.py`,
`agents/farm2945_late.py`, every other agent and `main.py`. New: `agents/farm2945_v3.py`
(base embedded byte-verbatim, one overlay appended, `agent` the last callable binding, the
lever a flag at the top of the overlay) and `tests/test_farm2945_v3.py` (19 stdlib
`unittest` tests; the whole suite is **235 tests, OK**). Nothing was committed, nothing was
submitted, and no Kaggle API or dataset call was made — every replay used is already cached
in `experiments/endgame/rep/`.

---

## 0. Answers up front

| question | answer |
|---|---|
| **Job 1 — does v219 pay?** | **Yes. Do not disable it.** On seeds 308-331 it fires on **exactly 3 of 24** (312, 328, 330) and disabling it costs **-8,111 / -2,571 / -3,715 per seat, 0 of 6 seat-results better, mean -4,799**. With seed 300 from `v2_results.md` §1.2 that is **four independent firing draws and four losses**. The frozen-tape +2,480 was the harness being wrong. |
| **Job 2 — goose tail, k=2** | **Do not ship.** Executes exactly as designed (3 geese placed, confirmed on tile, first divergence step 150 on every firing episode) and **self-play absolute is +6,730** — but it is **5-7 of 16 against the base**, **-2,336 mean d margin on the harness with one recorded win broken**, and it gives up ground against `router_yuan_nf_trim` (+14,053 against the base's +15,982). |
| **Job 2 — goose tail, k=3** | **Do not ship — it is the worst result in this series, and the harness loves it.** Frozen tape: **+8,244 mean d margin, six recorded losses flipped to wins.** Every responding harness: **0-16 of 16 against the base at -25,090**, **0-16 against `nf_trim` at -11,892**. Self-play absolute is **114,501 (+24,834)**. |
| **ship anything?** | **No.** `agents/farm2945_v3.py` ships with `V3_GOOSE_TAIL_K = 0` and is **bit-identical to the base on all 17 harness episodes** ($0 delta, `first_divergence` `None` everywhere) and on the seed-0 gate. |

**The premise the brief was built on is only half true on this base, and that is the first
thing to know.** The tape's animals are not all cows and sheep with geese as an idea
nobody had: **the route tapes buy GOOSE natively at day 10 and day 11**, and the base's own
`v9 HERD` and `HERD2` layers exist to convert those geese *into* sheep or cows when the shop
draw pays. Probed across seeds 308-331 in base self-play, **the emitted animal program
equals the drawn route's native tape on 24 of 24 seeds** — no conversion was observed on any
of them — and on 19 of the 24 the tape's **last three animals are already geese**. So "swap
the last k animals to GOOSE" is, for the modal draw, **already what the base does**, and the
swap can only reach further back into the cow/sheep body of the herd. That is what was
built and measured.

**The methodological headline is k=3.** It is the mirror image of lever A in `v2_results.md`:
there the frozen tape said +2,480 and three live harnesses said -8,500; here the frozen tape
says **+8,244 with six losses flipped** and three live harnesses say **-25,090, 0 of 16**.
Same tool, opposite sign, same cause — `ladder_replay.run()` cannot price a change that
hands the opponent a market. **A single harness would have shipped this.**

---

## 1. Job 1 — v219, settled

### 1.1 What was run

`experiments/tapes/run_agents.py` with `agents/farm2945_v2.py` at `V2_V219_OFF = True` as the
candidate and `agents/public_farm2945.py` as the opponent, **seeds 308-331, both seats** (48
seat-results). Firing was detected **independently of the bank delta**, because a delta of
zero is not proof of a no-op and a non-zero delta is not proof of firing: the base was played
against itself on the same 24 seeds and each player's action stream scanned for a **`BUY_LAND`
order at step >= 432**. That is v219's own footprint and it is unambiguous — `_v219_qualifies`
*refuses to commit* if the route tape itself buys land after step 432
(`agents/public_farm2945.py:1286-1289`), so a late `BUY_LAND` can only be v219's.

### 1.2 Result

**v219 fires on 3 of the 24 seeds: 312, 328, 330** (both seats, on every one). The probe and
the bank deltas agree exactly — the same three seeds are the only ones where lever A moves
the bank at all.

| seed | v219 fires | lever A, seat 0 | lever A, seat 1 |
|---|---|---:|---:|
| 312 | yes | **-8,111** | **-8,111** |
| 328 | yes | **-2,571** | **-2,571** |
| 330 | yes | **-3,715** | **-3,715** |
| 310 | no | +762 | -762 |
| 313 | no | -80 | +80 |
| the other 19 | no | +0 | +0 |

**Mean over the firing seeds: -4,799 per seat, better on 0 of 6.** Seeds 310 and 313 are the
only non-firing seeds whose delta is not exactly zero, and their deltas are exact mirrors —
that is the seat asymmetry of identical code, not a lever effect, and the probe puts both at
zero firings. Over the whole 24-seed set lever A reads **2-8 of 48, mean -600**, and the 2
"wins" are those two mirror halves.

**Verdict: v219 pays when the opponent can respond, and the `n = 1 seed` caveat in
`v2_results.md` §6 is closed.** Four firing draws (300, 312, 328, 330) across two independent
harnesses, four losses, worst -10,076 per seat. The paragraph in `v2_results.md` §6 has been
updated in place. What remains unexplained is unchanged: *why* v219 is worth ~$4-8k a seed in
a mirror when the traces cost its tomato P&L at a ±2k line item. The ten extra worked tiles
of the SE quadrant for the last eleven days is still the obvious suspect, still unmeasured.

---

## 2. The engine facts the goose swap rests on

All three were read out of `.venv/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py`
and are pinned by `tests/test_farm2945_v3.py::TestEngineFactsTheLeverRestsOn`, which exercises
the engine's own functions rather than quoting the docs.

**(a) GOOSE needs a COOP; COW and SHEEP need a PASTURE; the BUILD rename is mandatory and
is a clean 1:1.** `ANIMALS["GOOSE"]["structure"] == "COOP"`, `COW`/`SHEEP` → `"PASTURE"`
(l.19-23), and `_apply_unit_action`'s PLACE branch requires
`tile.get("kind") == ANIMALS[item]["structure"]` before it will take the animal (l.377-391).
`BUILD_COOP` and `BUILD_PASTURE` are two separate ops with identical preconditions
(`tile is None`, l.493-503), so renaming one to the other is a true 1:1 substitution.

**The failure mode is worse than a no-op, which is why the pairing had to be provable.**
A `PLACE GOOSE` onto a PASTURE does not simply return: it **falls through to the shed-drop
path** (l.393-400). Off the shed it is a silent no-op with the goose stuck in the unit's
inventory; on a shed-access tile it silently deposits the animal into the shed. Either way
$300 is spent and no animal is placed. `test_a_place_onto_the_wrong_structure_is_a_silent_no_op`
pins both halves.

**(b) Production is collected by an explicit `HARVEST` unit action on the animal tile, and
the cadence matters.** `_apply_unit_action`'s HARVEST branch moves `tile["yield_units"]` into
the unit's inventory as `ANIMALS[...]["product"]` (l.469-472) — nothing is automatic.
`_daily_refresh_animals` accrues `min(max_held, yield + 1 + care_bonus)` (l.821-828), so
**everything past `max_held` is discarded**: GOOSE **4**, COW/SHEEP **6**. A cared goose
gains about **2 a day** (`interval` 1) and therefore **caps in two days**; a sheep gains 4
every **3** days (`interval` 3, `first_yield_day` 6) and fits its cap exactly.

**So yes — a collection cadence tuned for cows and sheep does strand eggs, and it is
measurable on the real tape.** Traced on seed 308, the tape's HARVEST visits on the last
sheep tiles fall on days **15, 18, 24, 27** and **14, 17, 23, 26, 29** — 3-day steps with
6-day gaps. That is sheep-optimal and goose-lossy: a goose on a 3-day visit loses ~2 of 6
units, on a 6-day gap ~8 of 12. It is **not** fully unmitigated — the base's own `CAPHARV`
layer (`agents/public_farm2945.py:4980`) converts a `CARE`/`COLLECT_FERTILIZER` visit into a
`HARVEST` for an animal that would overflow tonight — but the tape's *native* goose slots
(days 10-11) are visited 9-11 times a season against a sheep slot's 4-6, which is the
cadence the geese were routed for.

**(c) `FEED` consumes exactly one `WHEAT` for every species** (l.505-514) — there is no
per-species quantity and no per-species item. So a swap does not change the feed bill.

---

## 3. What was built, and what could not be

### 3.1 The brief's literal "last k COW/SHEEP purchases" is not a 1:1 rename on this tape

Stated first, because it changed what was built — the same way `v2_results.md` §3.1 had to.
Traced op by op on a real episode (seed 308, base self-play, every PLACE matched to the BUILD
that created the tile it landed on):

| the last three COW/SHEEP placements | placed | its pasture was built |
|---|---|---|
| `PLACE SHEEP` (7,4) | t=202, day 8, unit 6 | t=162, **day 6, unit 1** |
| `PLACE SHEEP` (6,3) | t=214, day 8, unit 5 | t=161, **day 6, unit 7** |
| `PLACE SHEEP` (6,2) | t=230, day 9, unit 3 | t=156, **day 6, unit 6** |

Each pasture is built **two to three days earlier by a different unit**, out of a day-6 batch
of six or seven builds that collectively serve the day-6, day-7, day-8 and day-9 placements.
Which build serves which placement is decided by *position*, and the position is decided by
the unit's route — so renaming one of those builds to a COOP means predicting, on day 6, which
day-9 animal will stand there. This is exactly why the base's own COWSWAP planner
(`_cs_plan`, l.5563) only ever plans **inside a single day** and is windowed to steps 144-192:
it cannot pair a build with a placement across a day boundary either, and it returns `None`
rather than guess. A first attempt here that simulated the tape's moves for the whole season
to recover the tiles **produced the wrong tiles** — extra hires shift unit indices and later
layers rewrite commands, so the simulated placement landed on (4,0) where the real one landed
on (6,2). It was abandoned rather than shipped.

### 3.2 What was built instead

An order is swapped **only when the tape pairs its `PLACE` with that same unit's own
`BUILD_PASTURE`, on the same day, with no other placement by that unit in between.** Then the
coop's tile is provably the tile the unit is standing on, and no position simulation is needed
at all: the live position is recorded at the BUILD and must equal the live position at the
PLACE. Four renames, nothing else:

```
BUY_ANIMAL <sp> q  ->  BUY_ANIMAL GOOSE q     (same market slot, same index, same quantity)
BUILD_PASTURE      ->  BUILD_COOP             (same step, same unit)
PICKUP <sp> q      ->  PICKUP GOOSE q
PLACE  <sp>        ->  PLACE  GOOSE
```

No order is added, removed or moved, so no existing order's settle index changes; quantities
are never split, because splitting one order into two would add a market order. A `PICKUP`
that also carries an animal we are keeping is refused. Any emitted command that is not the
tape op the plan expected — or a unit that has moved between its BUILD and its PLACE —
latches `broken`, after which the lever stops touching the action for the rest of the episode.
`v3_placed` counts tiles **confirmed afterwards to hold a GOOSE**, because (a) means the
latch alone is not proof the animal landed.

**`k` therefore counts orders actually swapped, walking backwards and skipping orders that do
not resolve.** On the modal route that means **k=2 = the day-9 `SHEEP x1` plus the day-6
`COW x2` (three animals)**, and **k=3 additionally reaches the day-0 `SHEEP x2`**. k=3 is
therefore *not* the brief's "third-from-last purchase" — it is the opening order, a different
experiment, and it is reported as such.

### 3.3 Control

With `V3_GOOSE_TAIL_K = 0` the overlay returns the base's own action **object** before
touching any state. On the 17 harness episodes: **Δ bank $0, Δ margin $0, `first_divergence`
`None` on every episode, both recorded wins kept.** Seed-0 self-play gate:
**`['DONE','DONE']`, 72,101 / 72,762** — the base's own numbers, no $3,000. That is what makes
every column below attributable.

---

## 4. Measured

### 4.1 The table

Base references: self-play absolute **89,667** (8 seeds × 2 seats, 300-307);
vs `router_yuan_nf_trim` **16-0, +15,982**.

| | **k = 2** | **k = 3** |
|---|---:|---:|
| harness (17 ep), mean Δ bank | +856 | +7,568 |
| harness, **mean Δ margin** | **-2,336** | **+8,244** |
| harness, margin better / worse / no-op | 2 / 7 / **8** | 8 / 9 / **0** |
| harness, flips | 0 up, **1 down** | **6 up**, **1 down** |
| harness, the 2 recorded wins | `109773242` **-7,408 win->loss**, `109856068` +0 | `109773242` +7,103 kept, `109856068` **-8,258 win->loss** |
| **self-play absolute** (8 × 2) | **96,397** (+6,730), sd 22,162, min 61,836 | **114,501** (+24,834), sd 14,020, min 100,367 |
| **head to head vs the base** (8 × 2) | **5-7 of 16** (4 ties), mean **-1,072**, worst -8,597 | **0-16 of 16**, mean **-25,090**, worst -31,566 |
| vs `router_yuan_nf_trim` (8 × 2) | 16-0, **+14,053** | **0-16**, **-11,892** |
| seed-0 self-play gate | `['DONE','DONE']` 72,101 / 72,762 | `['DONE','DONE']` 89,376 / 89,376 |
| first divergence | **step 150** on all 9 firing episodes | **step 1** on all 17 |

### 4.2 Ship criteria

| criterion | k = 2 | k = 3 |
|---|---|---|
| self-play not below base by more than $300 | pass **+6,730** | pass **+24,834** |
| harness mean Δ margin >= +1,000 **and** 0 breaks | **FAIL** -2,336, **1 break** | **FAIL** +8,244 but **1 break** |
| >= 8-8 vs the base | **FAIL** 5-7 | **FAIL** 0-16 |

**Neither configuration meets the criteria, so `agents/farm2945_v3.py` ships with
`V3_GOOSE_TAIL_K = 0`.** Read win counts before means, as this repo's own rule says: k=2's
+6,730 self-play mean sits on a 5-7 head-to-head record, and k=3's +8,244 harness margin sits
on 0 of 32 seat-results against two responding opponents.

### 4.3 Coverage — where the lever is a no-op, and why

**k=2 fires on 5 of 8 self-play seeds and 9 of 17 harness episodes.** On seeds 300, 301 and
302 the plan is built (`v3_targets = d9:SHEEP*1,d6:COW*2`, 3 animals) and then the break latch
fires on the very first planned key: **`rewrites = 0`, `broken = 1`, `placed = 0`** — those
routes emit a different command at that (step, unit) than the tape does, the lever refuses,
and the episode is byte-identical (the exact `+0` ties in the head-to-head column). That is
the latch working as designed and costing nothing. On the other five seeds: **11 rewrites,
3 of 3 geese confirmed on tile, `broken = 0`, `errors = 0`** on every one.

### 4.4 The action diff — the lever does exactly what it says

Seed 305, k=2, our seat against the base, diffed against the same seat in base self-play:

| count | op |
|---:|---|
| +3 | `BUY_ANIMAL GOOSE`, `PLACE GOOSE`, `BUILD_COOP` (and -3 each of the sheep/cow ops they replace) |
| **+83** | `SELL EGG` |
| **-51 / -9** | `SELL MILK` / `SELL WOOL` |
| -7 / -4 | `FERTILIZE` / `COLLECT_FERTILIZER` |
| ±4-6 | `HARVEST`, `PASS`, and a few moves |

Nothing outside the animal program and its own downstream selling appears. `first_divergence`
is **step 150 on 9 of 9** firing harness episodes — the day-6 cow purchase turn, exactly the
first planned rewrite.

---

## 5. Why it loses, in one number

Seed 305, k=2, the same episode as §4.4: **we bank 126,604 and the base banks 135,201**, while
in base self-play both seats bank 122,124. **Both sides gain, and the opponent gains more.**
We trade 51 units of MILK and 9 of WOOL for 83 units of EGG; the EGG book absorbs ours without
complaint, exactly as the `MARKET_PARAMS` table predicts — and the MILK and WOOL we stopped
producing are books we stopped *crowding*, so the base's own unchanged milk and wool sells
clear at a higher price than they otherwise would. The hypothesis's arithmetic was right about
EGG and wrong about what vacating a floored book does in a two-player game: **in a thin
market, the supply you withdraw is a gift to whoever is still selling there.** k=3 is the same
sentence with five animals instead of three, which is why it goes from -1,072 to -25,090.

This also explains the split on the frozen tape, where k=2 reads **+856 bank but -2,336
margin**: the recorded opponent's sells are fixed, so vacating MILK and WOOL raises its bank
by more than the eggs raise ours. On this lever the frozen tape *agrees* with head to head —
the mirror image of lever A, and for the same underlying reason.

**And it is why self-play absolute is the wrong number here.** At k=3 both seats bank
**114,501**, up 24,834 on the base, with a *tighter* spread — because in a mirror neither side
is crowding MILK or WOOL and both sides' remaining premium units clear high. That is the
second-sheep trap of `CLAUDE.md` ("head to head can bless a change that only works because the
opponent is a copy of us") reproduced in the **self-play-absolute** harness instead of the
head-to-head one. The rule generalises one step further: *any* harness in which both sides run
the change can bless a change whose whole cost is what it hands to a differently-shaped
opponent.

---

## 6. What I could not determine

- **Whether the base's HERD / HERD2 conversion ever fires at all in these draws.** What was
  measured is that the **emitted** animal program equals the drawn route's native tape on
  24 of 24 probed seeds, i.e. **no conversion was observed**. The layers' own telemetry
  (`herd_species`, `hd2_decision`) was not read, so "never fires" is not established — only
  "no conversion on these 24 draws". If it does fire on ladder draws, a *narrower* lever
  exists that this work did not test: veto the conversion on the last k orders only, which is
  pure suppression of the base's own rewrite and needs no build rename at all.
- **Whether k=3 loses an animal outright.** The k=3 dev probe on seed 308 reports
  `v3_placed = 4` of 5 with `broken = 0`, and the season ends with **4 empty COOPs and 1 empty
  PASTURE** against the base's 1 empty COOP. So either a rename landed and the engine still
  refused the PLACE, or a day-0 goose starved — the base's economic-feed layers (`_r85_feed`,
  `_R88_ANIMAL_DAYS`) carry per-species schedules and were not audited against a goose in a
  sheep's slot. **The `broken` latch is not proof of survival**; `v3_placed` and the
  end-of-season structure counts are the diagnostic, and they disagree with each other here.
  Not chased further, because k=3 is dead at -25,090 whatever the answer.
- **Whether a goose in a *cow* slot behaves differently from one in a sheep slot.** k=2 swaps
  one day-9 sheep and two day-6 cows together and was not decomposed; a cow's 2-day interval
  is closer to a goose's than a sheep's 3-day, so the stranding cost is not uniform across the
  three animals and the -1,072 may not be evenly earned.
- **Whether the swap would pay if the collection cadence moved with it.** It cannot be moved
  without desynchronising a unit's route (the same wall as `v2_results.md` §3.1), so this is
  not a tuning question on this base — it is a reason the tape's native day-10/11 goose slots
  are the *only* good goose slots it has.

## 7. Files

`agents/farm2945_v3.py` (base verbatim + overlay, shipped at `V3_GOOSE_TAIL_K = 0`),
`tests/test_farm2945_v3.py` (19 tests; full suite 235, OK). The v219 verdict is also recorded
in place in `docs/ENDGAME/v2_results.md` §6. Measurement scripts were throwaway, run from the
session scratchpad against `experiments/tapes/run_agents.py`, `experiments/endgame/ladder_replay.py`
and the replays already cached in `experiments/endgame/rep/`. `agents/public_farm2945.py`,
`agents/farm2945_v2.py`, `agents/farm2945_late.py`, every other agent, `main.py` and every
existing tool are unmodified. Nothing was committed, nothing was submitted, and no Kaggle API
or dataset call was made.
