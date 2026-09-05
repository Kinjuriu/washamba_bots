# Tools guide — experiments/ and tests/

A user guide to every evaluation tool in this repo: what it measures, when
to reach for it, and the exact command. Local reference only (`mydocs/` is
gitignored) — the authoritative, committed source for methodology is
`CLAUDE.md`; this file is the operator's manual that sits on top of it.

If a claim here ever disagrees with `CLAUDE.md` or with reading the
tool's own docstring, trust those over this file — this is a convenience
index, not a second source of truth.

---

## 1. The core loop, in the order you'd actually use it

```
bptk.py            screen a hypothesis structurally, in seconds
     │              (does this even look real, before spending a real episode?)
     ▼
param_search.py    search/confirm/profile the knob space on the REAL engine
     │              (screen many variants cheaply, profile one knob's dose-response)
     ▼
paired_compare.py  the decisive test for a single change: A vs B, same seeds
     │              (win-count-first; this is what upkeep/hiring/cash changes live or die on)
     ▼
head_to_head.py    contested-market validation against a real opponent file
     │              (the only local harness that can see a selling/market-timing change)
     ▼
selfplay_bench.py  ladder-predicting number: main.py vs main.py, contested order book
     │              (read this, not the built-in numbers, before trusting a bank figure)
     ▼
golden_master.py   record a behavioral snapshot before/after any refactor
     │        --update writes tests/golden/golden.json (bank, sells, water, escapes, ...)
     ▼
test_episode_contracts.py   CI gate: entrypoint, DONE/DONE, golden match, p99 < 1s
     ▼
git commit (with explicit check-in per this repo's own standing rule —
            ask before committing experiments, see the auto-memory feedback entry)
```

**Why this order and not some other one:** each stage is cheaper and
noisier than the one after it. `bptk.py` runs in seconds but is a
zero-travel-time model (1.5-2x inflated, direction-only). `param_search`
runs real episodes but only 2-4 seeds during screening. `paired_compare`
is the first stage that controls seed variance properly (same seeds, both
arms — this is why it beats reading `seeded_batch.py`'s across-seed
stdev, a mistake this repo made twice already; see CLAUDE.md). Skipping a
stage is fine when you're confident (a one-line typo fix doesn't need
`bptk.py`); skipping it because it's slow, when the change is genuinely
uncertain, is how this repo shipped two of its documented dead ends.

**A change worth shipping should clear the bar on at least two harnesses
that can disagree** (paired vs `starter`/`pass`, and either head-to-head
or self-play) — never on the built-ins alone. See "A second sheep is the
sharpest two-harness disagreement" in `CLAUDE.md` for the concrete
incident this rule comes from.

---

## 2. Worked example — "should MAX_ANIMALS be higher?"

1. `bptk.py` — cheap structural scan. Does 6 animals show an advantage in
   the model? (Per CLAUDE.md's own animal diagnosis pass, it won't — the
   model predicts cash-trough collapse at 5+.)
2. `param_search.py --profile MAX_ANIMALS` — one-at-a-time dose-response
   across 2/3/4/5/6, a handful of seeds. Confirms *where* the cliff is.
3. `param_search.py --stage screen --samples 32` — is `MAX_ANIMALS` even
   a top knob on its own, or is it coupled to crew size / cash reserve
   (as `BUY_LAND` × crew size was, twice)?
4. `paired_compare.py base.py candidate.py --seed-set dev` — if screen
   says a specific value is best, the decisive real test, win-count first.
5. `head_to_head.py candidate.py main.py` — contested-market check; does
   it still win when the opponent isn't a copy of the never-selling
   built-ins?
6. `golden_master.py --update` — record the new snapshot once the change
   ships.
7. `python -m unittest discover -s tests` — CI gate, must be green.
8. Confirm once, and only once, on holdout (`--seed-set holdout`) before
   calling it settled.
9. `git commit` — with explicit check-in first.

---

## 3. Tool reference

### `experiments/seeds.py` — the one seed-set definition
No CLI. Defines `DEV_SEEDS = range(12)` (iterate freely) and
`HOLDOUT_SEEDS = range(100, 112)` (touch once, for confirmation only,
after a change is frozen). Every harness below imports this — never
redefine a seed range in a new tool. Reusing dev seeds for confirmation
is the classic double-dip that manufactured false wins here before this
file existed (see CLAUDE.md's "Two seed sets" section).

### `bptk.py` — whole-economy structural model (research only)
```bash
.venv/Scripts/python.exe bptk.py --validate                     # sanity gate, must reproduce known numbers
.venv/Scripts/python.exe bptk.py --contested --validate-contested
.venv/Scripts/python.exe bptk.py --check-assignment             # Hungarian-assignment property check
```
Calls the real engine's own private state-mutation functions
(`_apply_unit_action`, `_daily_refresh_plants`, `market_price`, ...)
against a synthetic `farm["tiles"]` grid — not a reimplementation, so it
can't silently drift from an engine patch. Zero travel time (no spatial
pathing), so absolute bank numbers read **~1.5-2x high** vs a real
episode. Use it for **direction**, never for a bank-balance prediction.
Validated against 7 already-documented mechanisms before being trusted
for anything new. Not imported by `main.py`. Also carries `--straw-first`
and `--compare-path-c`/`--ladder` flags from two closed research threads
(both confirmed dead ends — see CLAUDE.md's dead-ends section); those
flags are historical, not part of the active workflow.

### `experiments/param_search.py` — joint knob search on the real engine
```bash
# Discover the current knob registry (AST-read from main.py, 29 knobs as of this session)
.venv/Scripts/python.exe -c "from experiments.param_search import discover_knobs; print(sorted(discover_knobs()))"

# Screen: N random variants vs baseline, cheap seed count
.venv/Scripts/python.exe experiments/param_search.py --stage screen --samples 32 --opponent starter

# Confirm: top-K screened candidates on DEV_SEEDS, paired
.venv/Scripts/python.exe experiments/param_search.py --stage confirm --top 5

# One-at-a-time dose-response for a single knob (+/-25%/+/-50%)
.venv/Scripts/python.exe experiments/param_search.py --profile MAX_ANIMALS
```
Exists because `paired_compare.py` tests exactly one knob at a time, and
this repo has multiple *proven* couplings (`BUY_LAND` × crew size, twice;
`CROP_PLANTING_WINDOWS` × `require_held_seed`; hire-gate × seed reserve)
that a one-at-a-time sweep is structurally blind to. Every screened
candidate + result appends to `experiments/param_search_results.jsonl`
(resumable audit trail, never overwritten). Variant generation rewrites
exactly one `^NAME = ...` line per knob and asserts exactly one
replacement — this guards against the exact failure this repo already
had once (the Path C override wrapper that silently read the wrong
constant and made every "different" arm byte-identical).

### `experiments/paired_compare.py` — the decisive single-change test
```bash
git show main:main.py > /tmp/base_main.py
.venv/Scripts/python.exe experiments/paired_compare.py /tmp/base_main.py main.py [opponent] [n_seeds] [--seed-set dev|holdout]
```
Both arms play the *same* seeds, so seed-to-seed variance (kinder weeds,
luckier shop unlocks) cancels instead of masking the delta —
`seeded_batch.py`'s across-seed stdev does not cancel it, which is why
two real gains (fertilizer +1,764, daily-feed +1,657) were nearly shipped
as "noise" before this tool existed. **Read the win count before any
t-value**: 12/12 needs no statistics; 7/12 is not rescued by a decent
mean. Only pair against `pass`/`starter` — `random`'s own RNG isn't
seed-controlled, so the pairing is invalid for it.

### `experiments/head_to_head.py` — contested-market validation
```bash
.venv/Scripts/python.exe experiments/head_to_head.py variant.py main.py [n_seeds] [--seed-set dev|holdout]
```
Plays two agent *files* directly against each other, both seats averaged
(seats are not symmetric — identical code gives seat 0 a few hundred
less). The only local harness that can see a selling/market-timing
change do anything, since built-ins never sell. Always include a
self-control (same file both sides) — it must land at ~0, or the harness
itself is lying. Caveat this repo learned the hard way: a win here can
be real only because the opponent is shaped like us (the second-sheep
incident) — never trust head-to-head alone.

### `experiments/selfplay_bench.py` — the number that predicts the ladder
```bash
.venv/Scripts/python.exe experiments/selfplay_bench.py [n_seeds] [--seed-set dev|holdout]
```
Both sides run `main.py`. Built-in opponents never sell, so
`pass`/`random`/`starter` numbers are inflated ~1.5x — this is the only
local setup with a real contested order book. Its `end price` line is
the tell: MELON finishes ~$280 vs a built-in, near the $1 floor here.
Use this, not the built-in batch, to judge whether a bank figure will
survive contact with the ladder.

### `experiments/seeded_batch.py` — quick smoke, not a verdict
```bash
.venv/Scripts/python.exe experiments/seeded_batch.py [--seed-set dev|holdout]
```
Mean/stdev/win-rate for one agent against all three built-ins. Cheap and
useful for a first look, but the ±2,000 across-seed stdev it reports is
the wrong test for "is my change real" — that's what `paired_compare.py`
is for. Don't ship or kill a change on this number alone.

### `experiments/golden_master.py` + `tests/golden/golden.json` — refactor safety net
```bash
.venv/Scripts/python.exe experiments/golden_master.py --update    # record: sole writer of golden.json
.venv/Scripts/python.exe experiments/golden_master.py             # verify against the snapshot
.venv/Scripts/python.exe experiments/golden_master.py --time      # per-turn latency (p50/p99) proxy
```
Records bank + action histogram (sells, water, fertilizer, harvest,
escapes) for seeds 0-2 vs `pass`/`starter` (6 records). Run `--update`
before a refactor you believe is behavior-preserving (e.g. dead-code
deletion), then compare after — "All fields match" or a specific,
named drift, never a silent surprise on the ladder later. **This is the
single writer of `tests/golden/golden.json`** — `test_episode_contracts.py`
only ever reads it. (An earlier version of the test file had its own,
incompatible `--update` writer; that's fixed now — see §5.)

### `tests/test_episode_contracts.py` — the CI gate
```bash
.venv/Scripts/python.exe -m unittest tests.test_episode_contracts -v
```
Four contracts, all must pass before a submission:
1. **Entrypoint**: `main.py`'s last non-comment statement is
   `agent = nikaangukia_meroni` (AST/text-verified — catches the silent
   "helper defined below `agent`" hijack the framework doesn't error on).
2. **Self-play DONE/DONE**: seed 0, both sides finish `DONE` with bank
   above starting money — catches a silent all-PASS fallback.
3. **Golden-master match**: every `(opponent, seed)` pair recorded in
   `golden.json` (all 6) is re-run and must match exactly.
4. **Latency**: p99 per-turn time is under the 1s `actTimeout`.

---

## 4. Diagnostic / research tools (secondary tier — reach for on a specific question, not routinely)

| Tool | Question it answers |
|---|---|
| `experiments/tape_profile.py` | **Is the season on the tape's schedule?** Crew, herd, plantings by crop and sells by product, per engine day, for a contested episode against the v20 tape mean and the live opponent. Written because `mydocs/FACTS.md`'s unit counters (`d0 4/4`, `unlock ≥ 14`) all passed for seven sessions while the shape drifted 4–6 days late and the contested bank fell ~51k → ~8k. Run it before reading a bank. |
| `experiments/replay_diagnostics.py` | Single-episode deep-dive: day-by-day money, action histogram, end-of-farm footprint. What found the weed cascade originally. |
| `experiments/market_probe.py` | Reconstructs the analytical price formula per product and cross-checks it against a live episode. |
| `experiments/ladder_episodes.py` | Reads real per-episode ladder records (bank, margin, opponent rating) instead of trusting the aggregate rating, which needs ~20+ episodes to mean anything. |
| `experiments/opponent_strata.py` | Splits our own ladder episodes by opponent rating — are we losing on economy or on matchups? |
| `experiments/replay_shape.py` | Pulls land/crew/animal/planting-window shape out of a real top-ladder replay JSON. |
| `experiments/animal_timeline.py` | Day-by-day cash/feed path for a replay's animal herd — companion to `replay_shape.py`'s end-state snapshot. |
| `experiments/opening_trace.py` | Turn-by-turn action order for a replay's opening days — the interleaving `replay_shape.py`/`animal_timeline.py` can't show. |
| `experiments/route_v20.py` | Decodes `boatlee`'s public V20 notebook (network + Kaggle CLI required) into a local sparring opponent — a yardstick, never a base to build on. Writes to a gitignored path, never committed. |
| `experiments/meta_opponent.py` | Same pattern as `route_v20.py` for the top public meta notebook — a harness, not an entry. |
| `experiments/benchmark.py` | Original reference-agent benchmark from before `paired_compare.py`/`seeded_batch.py` existed. |

## 5. Superseded / historical (don't build on these; kept for reference)

- **`experiments/bigfarm_opponent.py`** — a reference opponent built to
  test scale changes before `BUY_LAND` shipped. Per `meta_opponent.py`'s
  own docstring, it was neutralized the moment its settings shipped in
  PR #29 — it's no longer a differentiator from our own agent.
- **`experiments/aggressive_opponent.py`**, **`experiments/forward_pricing_experiment.py`**
  — stress-test / experiment-specific harnesses tied to closed research
  threads. Read their own docstrings before reusing; don't assume they
  reflect the current `main.py`.

## 6. Gotchas this file exists to prevent you re-learning

- **One writer per snapshot file.** `golden_master.py --update` is the
  only thing that should ever write `tests/golden/golden.json`. A second,
  divergent writer silently corrupted it once already (fixed this
  session) — if you add a new tool that touches this file, make it a
  reader, not a second writer.
- **Never run `--seed-set holdout` while iterating.** It exists to be
  touched once per candidate bundle. Reusing it for daily iteration is
  the exact double-dip `experiments/seeds.py` was built to prevent.
- **Read the win count before the mean, and the mean before the
  t-value.** A mean gain paid for with a floor loss is not a gain in a
  tournament scored on pairwise wins (Bradley-Terry) — see the
  sell-or-hold cadence dead end in CLAUDE.md.
- **A tool that reports "positive everywhere" on every harness but never
  clears the decisive bar on any one of them is not a ship** — see the
  Phase 3 aggressive-selling dead end.
- **Run the self-control before trusting a harness result.** Same file
  vs itself, or same seed both arms, must read ~0. If it doesn't, the
  harness is the bug, not your change.
