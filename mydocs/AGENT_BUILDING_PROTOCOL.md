# Agent building protocol

How we build this agent from 2026-09-01. It exists because Path A–C were
specs of a *strategy slogan*, `param_search` was a spec of *numbers*, and
neither wrote down the *state that must already be true* for a trajectory
to replay. Pasting v20 tape orders onto crop-first gates is the same
failure with a new costume.

This is the method. The live fact-set is **`mydocs/FACTS.md`** — one table,
each row an invariant + when + counter + code rule. `HANDOFF.md` is the
session diary; it does not duplicate the table. Measurement harnesses and
“change one thing” still apply **inside** a chosen equilibrium — see
`docs/EXPERIMENT_WORKFLOW.md`. Do not use that sequence as a substitute
for steps 1–3 here.

## Session ritual

1. Read `mydocs/FACTS.md` first (not HANDOFF archaeology).
2. Classify the change: **fact** (add/remove/supplement a row), **knob**
   (number inside rows that hold), or **slogan** (stop; expand or drop).
3. If fact: edit the table, paste the fact card from that file, diff the
   throwaway against **every** row, then run. If a pre-run checkbox is
   empty, the episode is not a test of this shape.
4. Judge named counters **before bank**, and judge them **contested vs
   `agents/route_v20.py` on seeds 0 and 8**. `starter` is a crash /
   escape smoke check only — it never sells and never buys wheat, so it
   cannot price a sell path, a feed bill, or a production-timing slip.
   Run `experiments/tape_profile.py` (per-day crew / herd / plant / sell
   against the tapes) before reading the bank: a row whose *day* is off
   the tape is a failing row even when its own unit counter passes. Do
   not patch shipped `main.py` until the throwaway shows the rows *and*
   the contested bank is not down.
5. **Report to the user before writing `mydocs/HANDOFF.md`.** Numbers,
   win counts, and the add / drop / supplement call go in the chat first.
   HANDOFF is the diary after that, not the first copy of the result.

Two speeds: **shape days** work the table and `experiments/_*.py`.
**Knob days** use `docs/EXPERIMENT_WORKFLOW.md` and must leave every row
true. If a sweep breaks a counter (d0 goes 1/1), it was never a knob.

## Facts, knobs, slogans

| | What it is | Example | Tool |
|---|---|---|---|
| **Fact** | Invariant of farm shape. Usually yes/no or an ordering. | `BUILD_PASTURE` is not gated on animal-purchase cash. `SELL FERTILIZER` is listed before `BUY_ANIMAL`. Wheat reserve counts *owned*. | Implement until a real episode shows it. Not a sweep. |
| **Knob** | Numeric constant *inside* one shape. | `MIN_CASH_RESERVE_FOR_SEED_BUYING = 450`, `MAX_ANIMALS`, sell thresholds, `WORK_TILES_PER_HAND`. | `param_search` / paired compare, after the facts hold. |
| **Slogan** | Named season picture with dependents unstated. | Path C: “STRAW pin + 3→10.” Path B: “animal-led, no carpet.” | Not a spec. Expand to facts or drop it. |

A tape is a **trajectory** (`actions[step]`). Reusable logic is a
**policy** (given this observation, emit this). A trajectory only replays
if the facts it silently assumes are already true on *our* board.

Bank at turn 720 is how the game scores. It is not how you choose the
next edit. Bradley-Terry cares about pairwise wins and the floor; one
seed vs `starter` will bless a lie.

## Equilibria

A **fact-set** is an equilibrium when every fact can be true at once.

Crop-first “keep ~$450 and hold fertilizer for plants” and animal-first
“be broke on day 3 so collected fert pays for the cow” are both complete
enough. They **cannot share** the same buy/build/sell rules. That is not
“450 vs 400.”

Path A **is** shipped `main.py` — a crop-first fact-set that is stable at
four animals. Path C failed by taking Path A’s gates and adding Path C’s
sequence: one named fact moved, the unnamed ones stayed pinned. That is
the same pattern as `MIN_MONEY_TO_HIRE` priced against $150 instead of
the $1 hire, and as a shared seed budget without a repurchase-cadence
fix.

If two facts fight, drop one. Do not average them into a knob.

## The sequence

```
1. WRITE THE FACTS
     → 2. DROP THE ONES THAT CANNOT COEXIST
     → 3. IMPLEMENT UNTIL A REAL EPISODE SHOWS THEM
     → 4. THEN TUNE KNOBS INSIDE THAT SHAPE
```

### 1. Write the facts

List the invariants the season shape requires, as state that must be
true at a named time (end of day 0, hour 0 of day 3, …). Name the
**counter** each fact should move (`d0 pens/herd`, `COLLECT_FERTILIZER`,
`SELL FERTILIZER` before `BUY_ANIMAL`, escapes, animals *placed* not
just bought).

A slogan is not this step. “Match v20” is not this step. “Raise
`MAX_ANIMALS`” is not this step.

### 2. Drop the ones that cannot coexist

Read the list as a single equilibrium. Crop-first reserve vs
animal-first broke-on-purpose: pick one. Serial pens vs four placed on
day 0: pick one. Hold fertilizer for crops vs sell it to fund the day-3
cow: pick one.

What remains is the spec. Put it in `mydocs/FACTS.md` so the next session
does not re-derive it. Session narrative goes in `HANDOFF.md`.

### 3. Implement until a real episode shows them

Throwaway copy of `main.py` (`experiments/_*.py`), real engine, seed 0
vs `starter` first. Self-play only if the opening does not freeze
(d0 pens/herd is not **1/1**).

Judge the **fact counters** before bank. If the counter the fact names
did not move, the change did not work — positive bank is correlation.

Do this on the **real engine**. `bptk.py` has zero travel time and
assigns crew to top-N tiles with no walking or shed trips. It cannot
see the day-0 pen freeze, pickup/place lag, or collect→sell→buy. Use it
for structural crop/cash questions inside an equilibrium that does not
depend on pathing.

Do not patch shipped `main.py` until the throwaway shows the facts
**and** the usual harnesses (paired vs `starter`/`pass`, contested
head-to-head when selling or scale changed). One fact at a time is
allowed only when the rest of the set stays true; a “half stack” that
breaks a fact you already had (calendar-only vs hour-0 batch that
returns to 1/1) is a failed step 3, not a partial win.

### 4. Then tune knobs

Only after the facts hold. `param_search` / one-at-a-time response
curves on constants that remain *inside* the shape. It will not discover
“don’t gate `BUILD_PASTURE` on animal cash.” That is not a parameter. It
will happily sweep 450 on an agent that still freezes at 1/1.

`docs/EXPERIMENT_WORKFLOW.md` (one change, freeze a control, paired
compare, self-play, holdout last) applies **here**, in this step.

## Where each tool sits

| Tool | When |
|---|---|
| `mydocs/FACTS.md` | Step 1–2 output. Live spec. Every shape change starts here. |
| `mydocs/HANDOFF.md` | Session diary. Points at FACTS.md; does not replace it. |
| `experiments/tape_profile.py` | Step 3 timing. Per-day crew / herd / plant / sell vs the tapes, before the bank. |
| Throwaway `experiments/_facts_v20.py` (tracked) | Step 3. Real engine, fact counters. Commit it with each card so a regression can be bisected. |
| `bptk.py` | Crop/cash structure *inside* an equilibrium. Never cadence/pen/pathing. |
| `paired_compare.py` / `head_to_head.py` / `selfplay_bench.py` | After facts hold, or to reject a throwaway that already fails them. |
| `param_search` | Step 4 only. |
| Shipped `main.py` | After step 3 wins on the fact counters and step 4 (if any) clears the harnesses. |

## What we are not doing

- Porting Path C, or “carrying Path A over” (A is already `main.py`).
- Pasting tape orders onto gates from a different equilibrium.
- Treating mean bank as evidence a fact moved.
- Using `bptk.py` to certify an animal cadence.
- Running `param_search` to find the architecture.
- Raising shipped `MAX_ANIMALS` as the first edit.
