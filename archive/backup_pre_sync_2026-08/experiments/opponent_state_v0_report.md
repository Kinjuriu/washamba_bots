# Architecture experiment: Candidate B — generic opponent-state layer

Follow-up to `docs/architecture_comparison.md`. This is an architecture
experiment, not a pricing experiment, and the primary objective per
instruction is heterogeneous (Kaggle-representative) performance, not local
self-play. `main.py` and `pricing.py` are untouched throughout
(`git diff --stat -- main.py pricing.py` empty at every step). No file under
`agents/` (Peter's route files) was modified — they were read via `git
show` from fetched branches and copies were extracted to `/tmp/washamba_opponents/`
purely so they could be *run* locally as opponents; nothing there is tracked
by this repo. Nothing merged, nothing submitted.

## 1. Hypothesis

*"Our agent is disadvantaged because its decisions are insufficiently
conditioned on the actual opponent. Giving the agent a structured
representation of observable opponent state should allow existing decision
logic to react differently to different opponent behaviors."*

Isolated by construction: exactly two existing decisions are touched (crop
choice, animal-species choice), no new decision axis is introduced (no
routing, no sell-timing), and every opponent-state field is generic —
computed the same way regardless of who the opponent is, never keyed to a
specific competitor's identity or a hardcoded build signature.

## 2. Implementation

`experiments/candidates/opponent_state_v0.py`. Architecture, exactly as
specified:

```
current game state  +  extract_opponent_state(obs)
                              |
              cached once per turn, as a side effect
              of count_opponent_pipeline (the one function
              main.py already calls once per turn)
                              |
              read by exactly two decision functions
                              v
              choose_crop            pick_next_animal_species
              (existing call sites,   (existing call site,
               unpatched)              unpatched)
```

**`extract_opponent_state(obs)`** — one snapshot of `obs["farms"][1-player]`
(the same public object `count_opponent_pipeline` already reads), covering:
land tiles owned, hand count, money, per-crop standing yield and tile
count, per-animal standing yield and tile count, a Herfindahl-style crop-
concentration index, and the dominant crop/animal. Deliberately excludes
opponent shed/inventory (private, never observable) and opponent recent
actions/sales (would require cross-turn memory this repo's architecture
doesn't have — see "Out of scope," below).

**Decision 1 — crop choice.** `count_opponent_pipeline` is patched to
return exact standing yield (`tile["yield_units"]`, the amount `HARVEST`
would actually move to inventory right now) instead of the original's flat
`crop_info["max_yield"]` ceiling assumed the instant any tile of that crop
exists. Both existing call sites of `choose_crop` — the `PLANT` branch
inside `choose_unit_action`, and the `BUY_SEED` restock call inside
`decide_market_actions` — are unpatched and unaware anything changed; they
simply now receive a more accurate number through the same parameter.

**Decision 2 — animal species choice.** `pick_next_animal_species` gets the
opponent's per-species tile counts as a **secondary** tiebreak, after our
own herd balance (the *primary*, unchanged criterion): among species tied
on how many we already own, prefer the one the opponent owns *fewer* of.
Generalises the same "don't pile into what's already crowded" principle
`choose_crop`'s demand-absorption term already applies to crops, to
animals, where no opponent signal existed before at all.

**Which existing decisions are now opponent-aware, stated exhaustively:**
`choose_crop` (already was, now with a materially better input) and
`pick_next_animal_species` (was not, now is, as a tiebreak only). Nothing
else — not land timing, not hiring, not selling, not liquidation.

**Out of scope, and why, not silently dropped:** "opponent recent
sales/market pressure" (from the task's own example list) would need
turn-to-turn memory this repo doesn't have yet. Building that *and* wiring
it into a decision in the same candidate would make it impossible to
attribute a result to either change cleanly — left for a dedicated
follow-up, not assumed away.

## 3. Testing checklist (task's own five points)

`tests/test_opponent_state_v0.py`, 20 cases, plus the pre-existing suite:

1. **`main.py` unchanged** — `git diff --stat -- main.py pricing.py` empty
   throughout; `TestMainPyUnchanged` also spot-checks that the candidate
   imports the real module and never touches pricing-related globals.
2. **Passes all relevant unit tests** — 20/20 new, **303/303 total**
   (283 pre-existing + 20). Two cross-candidate collisions were caught and
   fixed in the process: this repo now has *three* candidates that
   monkeypatch the same shared `main.count_opponent_pipeline` global
   (`opponent_aware_sell_gate_exact_yield.py`, and now this one), which
   silently breaks whichever candidate's test file happens to import
   second in a full suite run. Fixed the same way this repo's other
   cross-candidate collisions were fixed earlier today: each affected test
   class re-pins its own module's patch in `setUp`, and one `pricing_v1`
   cross-check was rewritten to stop depending on the live (shared,
   mutable) `main.count_opponent_pipeline` binding at all.
3. **Produces valid game actions** — self-test (`_self_test`) and every
   evaluation run below report `status: DONE` on both seats, every seed,
   every opponent; `TestProducesValidActions` also exercises
   `decide_market_actions` directly.
4. **No illegal/unobservable information** — `extract_opponent_state` reads
   only `obs["farms"][1-player]`; `TestExtractOpponentState` asserts the
   function body (docstring excluded, since it legitimately *mentions*
   "private"/"shed" in prose explaining what's excluded) never touches
   `"private"` or `"shed"`, and separately confirms it correctly follows
   `1-player` rather than a hardcoded farm index.
5. **Identical to baseline wherever the design intends it** — proven
   directly, not just asserted: `test_identical_to_baseline_when_owned_counts_already_differ`
   shows the animal tiebreak never fires unless our own herd counts are
   tied; `test_no_opponent_crop_no_log_entry_added` shows crop choice is
   byte-identical to the unpatched original whenever the exact and crude
   opponent-supply readings agree (e.g. opponent has nothing standing).

## 4. Heterogeneous-opponent evaluation

Per the task's explicit priority, this section is the primary evidence —
self-play is reported only as a sanity check, in section 4d.

**Opponents used**, extracted read-only from fetched, unmerged branches
(`origin/agent/moon-md-lead`, `origin/agent/route-v20`) to `/tmp/washamba_opponents/`
for local execution only — never written into this repo:
`route_moon_md.py`, `route_moon_tuned.py`, `route_moon_md_r5.py`,
`route_v20.py`, all confirmed deterministic per seed (no RNG found in any
of the four architecture reads behind `docs/architecture_comparison.md`),
so a genuine paired comparison (same seed, both seats) is valid the same
way it already is against `pass`/`starter`.

**Method:** for each opponent, 6 seeds × both seats, BASELINE (`main.py`)
vs that opponent and CANDIDATE (`opponent_state_v0.py`) vs that opponent,
paired by seed. `experiments/opponent_state_v0_heterogeneous_eval.py`.

### a. Per-opponent results

| opponent | baseline mean | candidate mean | mean delta | candidate better on |
|---|---|---|---|---|
| `route_moon_md` | 40,906 | 37,827 | **-3,079** | 2/6 seeds |
| `route_moon_tuned` | 40,906 | 37,827 | **-3,079** | 2/6 seeds |
| `route_moon_md_r5` | 40,906 | 37,827 | **-3,079** | 2/6 seeds |
| `route_v20` | 40,577 | 37,271 | **-3,306** | 2/6 seeds |

**A finding worth stating precisely, because it looked like a bug and
isn't one: the first three rows are not approximately equal, they are
byte-identical, seed for seed** (e.g. seed 0 is baseline 29,386 / candidate
45,386 against all three). Verified this is not a script error — the three
files have distinct MD5 hashes (`de99...`, `9a99...`, `d2d6...`) and were
independently confirmed as genuinely different code by the architecture
comparison's own reading. The mechanism: `route_moon_md.py`'s,
`route_moon_tuned.py`'s, and `route_moon_md_r5.py`'s only disclosed
differences from each other (`_ADAPT_MIN_EVIDENCE`, `_PREEMPT_MAX_BATCH`,
`_v17_md_counter`/`_v17_r5_counter` lookahead) all live *inside* mechanisms
gated on `_clone_distance(obs) <= 6` or an opponent-archetype fingerprint
match (sheep-heavy/cow-heavy tile-count patterns) — see
`docs/architecture_comparison.md` section 2. Neither `main.py` nor this
candidate looks anything like a near-mirror or a sheep-/cow-heavy archetype
to those detectors, so `_preempt_shift`, `_v17_r5_counter`, and
`_v17_md_counter` never activate against us at all, regardless of what
their tuned constants are set to. **Peter's team measured these
differences mattering against their own control — and they do, just not
against an opponent shaped this differently from what those mechanisms
were built to react to.** `route_v20`'s close-but-not-identical numbers
are consistent with this too: same inert core mechanism, but a genuinely
earlier route generation (no crop-diversification overlays), so the base
game still plays out slightly differently.

### b. Aggregate

**Candidate B loses to baseline against every heterogeneous opponent
tested, by a consistent but modest margin (-3,079 to -3,306, roughly 7-8%
of the ~38-41k baseline mean against these opponents), with an identical
2-of-6 win rate in all four cases.** Per-seed deltas are large and volatile
in both directions (route_v20: +15,900, -8,311, -14,482, -16,326, -6,704,
+10,086) — a real, noisy effect, not a tight, confident one, but the mean
and the win count both point the same direction across all four
independent opponents.

### c. Contrast: vs. `main.py` directly (still heterogeneous relative to
this candidate, but the closest in shape)

```
experiments/head_to_head.py: opponent_state_v0.py vs main.py, 6 seeds x 2 seats = 12 matches
  mean bank difference: +5,782
  variant won: 7/12
```

A positive result, but per the task's own instruction not to weight
same-architecture comparisons like a heterogeneous one: `main.py` and this
candidate are structurally the closest opponent pair in this whole
evaluation (same crew logic, same land/animal caps, same everything except
the two touched decisions) — this result describes "does the new signal
help against an opponent that plays similarly to us," which is the
category of evidence this task explicitly asked to de-prioritize, not
extra confirmation on top of the heterogeneous result.

### d. Self-play sanity check (regression signal only, per instruction)

```
6 seeds: mean 61,023, stdev 13,027, median 67,089, range 34,812-67,620
```
No crash, no `DONE`-status failure, no collapse toward the "agent never
acted" $3,000 floor. In line with baseline `main.py` self-play (~61,303
mean) — confirms the candidate is a working, non-degenerate agent, and
nothing more. Not used to judge the hypothesis.

## 5. Mechanism analysis — causal traces, not just scores

`experiments/opponent_state_v0_mechanism_diag.py`, in-process so
`CROP_DECISION_LOG`/`ANIMAL_DECISION_LOG` are directly inspectable, 6 seeds
each against `route_moon_md` and against `main.py`.

**The candidate is not inert — it changes real decisions, frequently, with
a clear, traceable cause each time:**

| opponent | crop decisions changed | animal decisions changed |
|---|---|---|
| `route_moon_md` | **769** | 1 |
| `main.py` | **272** | 6 |

**Crop-choice mechanism, concretely (vs. `route_moon_md`, day 4):**
```
baseline_would_plant = CARROT      candidate_plants = WHEAT
exact_opponent_supply  = {MELON: 12, WHEAT: 11}
crude_opponent_supply  = {MELON: 72, WHEAT: 24}
```
`route_moon_md`'s route commits to melon early; at day 4 those tiles have
barely started accruing yield (MELON's `max_yield_day=12`), so the true
standing supply is small (12), but the old crude signal assumed every one
of those tiles was already at MELON's full `max_yield=6` the instant it
was planted, inflating the read to 72 — a wildly overstated glut warning
that pushed the old logic away from melon into carrot. The exact signal
sees the truth (barely-grown tiles), removes the false alarm, and the
crop-choice formula's own scoring picks wheat instead in this case. **This
is the mechanism working exactly as designed** — this is the same
exact-yield-vs-crude-max-yield gap this session's earlier
`opponent_aware_sell_gate_exact_yield_report.md` already established and
validated, now reused for crop choice instead of sell timing.

**Animal-choice mechanism, concretely (vs. `route_moon_md`):**
```
owned = {SHEEP: 2, COW: 2}      (tied)
opponent = {COW: 6, SHEEP: 8}
baseline_pick = SHEEP           candidate_pick = COW
```
Against a large route-based herd (this opponent runs 6-18 animals per
`docs/architecture_comparison.md`), the tiebreak correctly steers toward
the species the opponent has proportionally less of.

**So why does a real, correctly-firing mechanism still lose on net against
these opponents?** The most direct, code-grounded explanation: the
underlying `choose_crop` scoring formula (`future_price * expected_yield /
growth_days`, with the opponent term acting as a glut-avoidance signal) was
tuned and validated all session against same-scale opponents (self-play,
built-ins). Against an opponent whose total production is 5-15x larger
(`route_moon_md`'s reward on the same seeds — 39,758-45,386 for it
implicitly, vs. our ~26,000-45,000 — is itself evidence of the scale gap
`docs/architecture_comparison.md` already predicted), *any* reading of
opponent supply — crude or exact — is large by our farm's standards; making
that reading more *accurate* doesn't change the fact that our own
crop-scoring formula's glut-avoidance term was never calibrated for an
opponent operating at this scale. The mechanism correctly answers "is the
opponent's melon glut real or a data artifact" — it doesn't and can't
answer "does avoiding melon even make sense when my farm is 1/10th this
opponent's size," which is squarely candidate C's (scale/shape) territory,
not this one's.

**No opponent-class split beyond what's already reported**: all four
heterogeneous opponents produced the same direction (negative) and
magnitude band (-3,079 to -3,306); there is no "helps against X, hurts
against Y" pattern to report here — it's a consistent, if modest, loss
across the whole heterogeneous set tested.

## 6. Classification

**D — technically interesting, but not worth spending a Kaggle submission
on.**

Not A: every heterogeneous opponent tested shows a negative mean delta,
and per this task's own instruction, that evidence dominates the positive
result against `main.py` itself, not the reverse.

Not B: there is no single, specific correction identified that would
plausibly flip this result. The mechanism analysis's own conclusion — the
real limiting factor is a scale mismatch between our economy and the
opponents that matter, not an inaccuracy in the opponent-state signal
itself — points toward candidate C (shape/scale) or a genuinely different
follow-up, not a fix *within* this candidate's scope.

Not C ("no evidence of competitive benefit; reject" in the flat, inert
sense): that undersells what was actually found. This is not a null
result — 769 and 272 real decisions changed against two different
opponents, each with a traceable, sensible cause, several of them
individually correct (the melon-glut-false-alarm case is a genuine
improvement in isolation). The architecture works exactly as designed. It
just doesn't net out positive against the opponents that matter most right
now, and 6 seeds of noisy, volatile per-seed deltas isn't enough margin to
call it a coin flip either way with confidence.

**What this result actually establishes, stated plainly:** giving
`choose_crop` and `pick_next_animal_species` a more accurate *reading* of
the same narrow opponent signal they already had access to is not, by
itself, the fix for the 598-vs-1,687-2,658 tier gap `docs/architecture_comparison.md`
found. That gap is dominated by scale (candidate C) and by the field's
mirror-density (candidate D from that same doc, not yet built). This
candidate is best read as evidence *ruling out* "we just needed better
data feeding the same small decisions," not as a step toward shipping
anything.

No submission artifact is provided, since classification is not A.

## Recommendation

Do not submit Candidate B. Per `docs/architecture_comparison.md`'s own
ordering, proceed to candidate D (mirror-aware sell timing, tested first
in self-play since every self-play turn is a mirror by construction) or
candidate C (shape/scale) next, whichever the team prioritizes — this
result doesn't change that ordering, it removes "enrich the existing
opponent signal alone" from further consideration.

Full suite: **303/303 pass.** `main.py` and `pricing.py` untouched. Nothing
merged, nothing submitted.
