<!--
Behaviour changes to main.py need numbers. See CONTRIBUTING.md.
Docs-only or tooling-only PR? Delete the benchmark sections and say so.
-->

## What changed and why

<!-- The mechanic, not just the diff. What in the game does this exploit or fix? -->

## Target metric

<!-- The number this change was supposed to move, before and after.
     A green suite is not evidence that the fix worked - we once shipped a
     "fix" for a low FEED count that left the count at exactly 15.
     e.g. FEED 15 -> 30 (engine max), EGG sold 26 -> 52 -->

| metric | before | after |
|---|---|---|
|  |  |  |

## Benchmark

Baseline measured on commit: `<sha>`

`.venv/Scripts/python.exe experiments/seeded_batch.py` — 12 seeds:

| vs | baseline mean | new mean | delta | stdev | win-rate |
|---|---|---|---|---|---|
| `pass` |  |  |  |  |  |
| `random` |  |  |  |  |  |
| `starter` |  |  |  |  |  |

`.venv/Scripts/python.exe experiments/selfplay_bench.py` — **the number that
predicts the ladder** (built-ins never sell, so they inflate everything):

| | baseline | new |
|---|---|---|
| self-play mean |  |  |
| stdev |  |  |

<!-- If a delta is inside the stdev, write "within noise". Do not call it a win. -->

## Checks

- [ ] `.venv/Scripts/python.exe -m unittest discover -s tests` is green
- [ ] Self-play validation gate returns `['DONE', 'DONE']` (Kaggle rejects the
      upload if this crashes, regardless of strategy)
- [ ] `agent = nikaangukia_meroni` is still the **last** callable in `main.py`
- [ ] No OS-specific interpreter paths (team is split macOS / Windows)
- [ ] No replay JSONs or other multi-MB artifacts in the diff

## What this does NOT do

<!-- Known gaps, so the next person doesn't assume coverage that isn't there. -->
