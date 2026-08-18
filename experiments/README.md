# Experiments

This directory holds every non-production agent, benchmark tool, and
research report for the Kaggriculture competition. Nothing in here is
what gets submitted to Kaggle unless explicitly promoted.

## The production line

- **`main.py`** (repo root) is the production agent — the file that gets
  uploaded to Kaggle. It is not touched by anything in this directory.
- **`pricing.py`** (repo root) is the production pricing module `main.py`
  inlines its forward-pricing logic from.
- **`tests/`** (repo root) is the production regression suite —
  `python -m unittest discover -s tests`. It only tests `main.py` and
  `pricing.py`. Experiment-specific tests live next to their experiment
  (see below), not here.

**Nothing enters production without explicit validation** — a real,
reported benchmark against today's `main.py`, not a plausible-sounding
idea. Every folder below exists to keep that evidence attached to the
code it belongs to, so nobody has to re-derive "did this actually work?"
from scratch.

## Layout

```
experiments/
  README.md                  this file
  candidates/                 things that have been benchmarked against
                               today's main.py and could plausibly be
                               submitted - see the status table below
                               before assuming "candidate" means "safe"
  pricing_cadence/            forward-price / inventory-pressure / cadence-
                               urgency selling research (D, D')
  replay_shape/                Track C large-farm reference-opponent
                               research (structural shape harness,
                               cash-aware hiring gate)
  forward_pricing/             README only - see "Deliberately left in
                               place" below
  benchmarks/                  README only - see "Deliberately left in
                               place" below
  archive/                     pointers to dead-end research that exists
                               only as unmerged git branches, not files
                               in this working tree
```

## Status table

| experiment | status | report | Kaggle-safe? |
|---|---|---|---|
| `main.py` (production) | **PRODUCTION** | — | this *is* what's submitted |
| `pricing.py` (production) | **PRODUCTION** | — | inlined into `main.py`, not uploaded separately |
| MILK sell-threshold/cap fix (`candidates/milk_fix_candidate.py`) | **VALIDATED / NEUTRAL** | exact no-op vs today's `main.py`: mean +0.0, median +0.0, 24 seat-swapped matches, every diff an exact mirror pair (pure seat-asymmetry noise) — see root `CLAUDE.md`'s "MILK sell gates" note | **KAGGLE-SAFE** — passes the full standalone uploadability test; safe precisely because it changes nothing measured, while closing a documented latent gap |
| D′ pricing-cadence + today's multi-species main.py (`pricing_cadence/`) | **INCONCLUSIVE** | `pricing_cadence/pricing_cadence_v1_2_mechanism_audit_report.md` (mechanism); combined-with-current-roster benchmark (19/24 wins, mean +1,061, stdev 1,972, worst −3,221) was run as a scratch-only evaluation, never committed — not reproduced as a file here | **DO NOT SUBMIT** — real regressions on 5/24 seeds, variance 9x the original D′ benchmark; D′ alone (`experiment/pricing-cadence-v1` branch, unmerged) was validated only against an older, single-animal main.py, not today's |
| replay-shape reference opponent (`replay_shape/`) | **REJECTED** | `replay_shape/replay_shape_validation_report.md` | not a submission candidate — it's a benchmarking harness, and self-play (its own validation condition) collapses economically: animal-scale and no-feed-collapse checks fail 0/12 |
| cash-aware hiring gate (inside `replay_shape/replay_shape_agent.py`) | **REJECTED** | `replay_shape/replay_shape_v1_1_report.md` | fixed the fib-cost hiring problem vs `pass` but left self-play unchanged (identical 0/12 failure) — a real poverty-trap bottleneck remains undiagnosed-and-unfixed |
| second-animal (`MAX_ANIMALS=2`) | **REJECTED** | root `CLAUDE.md` ("A second sheep is the sharpest two-harness disagreement..."); code preserved on unmerged branch `experiment/second-animal` (pushed to GitHub) | not applicable — never a file in this working tree; −19,514 mean, 0/12 vs `starter` |
| tomato-fertilizer-yield-bonus | **REJECTED** | commit `b1e943b` on branch `fix/tomato-fertilizer-yield-bonus` (pushed to GitHub), self-reverted at `404e94b` | not applicable — never a file in this working tree; also badly stale relative to current `main.py` |

## Deliberately left in place (not moved into a subfolder)

Two groups of tracked files stay at `experiments/` root, on purpose, after
checking their imports and cross-references — moving them would be
cosmetic risk for zero benefit:

- **`benchmark.py`, `head_to_head.py`, `ladder_episodes.py`,
  `market_probe.py`, `paired_compare.py`, `seeded_batch.py`,
  `selfplay_bench.py`, `replay_diagnostics.py`, `aggressive_opponent.py`**
  — these are the team's standard, actively-used evaluation harnesses.
  Root `CLAUDE.md`'s Setup/commands section documents exact invocations
  like `experiments/paired_compare.py A.py B.py` and
  `experiments/replay_diagnostics.py`; relocating them would silently
  break every one of those documented commands and any muscle-memory
  script the team already has, for a purely cosmetic gain. See
  `benchmarks/README.md`.
- **`forward_pricing_experiment.py`, `forward_pricing_experiment_report.md`**
  — `main.py` itself contains a comment pointing to
  `experiments/forward_pricing_experiment.py's report` (line ~1661).
  `main.py` cannot be modified, so that pointer can never be corrected if
  the file moves — leaving it in place is the only way to keep the
  pointer accurate. See `forward_pricing/README.md`.

Prose *mentions* of old paths inside the moved markdown reports (e.g. a
report saying `experiments/replay_shape_agent.py` instead of the new
`experiments/replay_shape/replay_shape_agent.py`) were **not**
rewritten — only executable imports and the notebook's functional path
cells were fixed, since those are what actually breaks something. A
human reader opening a report from inside its new folder will find the
file it's talking about right next to it regardless.

## Running experiment-specific tests

Not part of `python -m unittest discover -s tests` (production only).
Each experiment's tests are self-contained:

```
python -m unittest discover -s experiments/pricing_cadence/tests
python -m unittest discover -s experiments/replay_shape/tests
```
