# Checkpoints

A checkpoint is a named, reproducible snapshot of the agent that the team can
point at, compare against, and roll back to. It is not a submission and it is
not a git tag by itself — it's the record that makes a git SHA *interpretable*
months later, when nobody remembers why the numbers were what they were.

See **[EXPERIMENT_WORKFLOW.md](EXPERIMENT_WORKFLOW.md)** for how a change
earns the right to become a checkpoint, and
**[Issue #4](https://github.com/Kinjuriu/washamba_bots/issues/4)** for live
team coordination (submission scheduling, who's doing what).

## Why this exists

`CONTRIBUTING.md` already states the standard: "Measurements go stale. Always
state *which commit* a number was measured on, and re-measure before acting
on someone else's." A checkpoint is that discipline turned into a fixed
record instead of a claim someone has to keep re-verifying by memory.

## What a checkpoint must record

| Field | What goes here |
|---|---|
| Name/version | e.g. `V1`, `V1.1-fertilizer` — short, stable, referenced elsewhere |
| Git commit SHA | The exact commit the numbers below were measured on |
| Date | When it was measured |
| Main behavioural changes | What actually changed in `main.py`, in plain language — not a diff dump |
| Tests | `unittest discover -s tests` result and count |
| Environment/version | Python version, `kaggle-environments` version (mid-season balance patches change scoring — see `CLAUDE.md`) |
| Self-play benchmark | `experiments/selfplay_bench.py` output: mean, stdev, min, max, seed count — **this is the number that predicts the ladder, not the built-in table** |
| Seeded benchmark | `experiments/seeded_batch.py` output vs `pass`/`random`/`starter`: mean, stdev, win-rate |
| Benchmark seeds/configuration | Seed range/count, `episodeSteps`, anything non-default |
| Action-level diagnostics | Whatever `experiments/replay_diagnostics.py` or the notebook surfaced that's relevant to this checkpoint (e.g. `FEED` count, weeds at season end, plants *landed* vs requested) |
| Kaggle submission ID | If this checkpoint was submitted, the ID (`kaggle competitions submissions kaggriculture`) |
| Kaggle rating/range | If available — **see the rule below** |
| Interpretation | What the numbers mean, including "this is a wash" if it is one |
| Known limitations | What this checkpoint does *not* do or hasn't proven |
| Frozen / control / experimental | See below |

### Checkpoint status

- **Frozen** — the reference point for A/B comparisons. Not touched. There
  should be exactly one active frozen checkpoint at a time (currently V1,
  once tagged — see EXPERIMENT_WORKFLOW.md's FREEZE CONTROL step).
- **Control** — the unchanged submission kept active on the ladder
  specifically so it keeps collecting rating signal while a treatment is
  tested (workflow rule #5).
- **Experimental** — anything mid-evaluation. Not yet accepted, not a basis
  for further changes until it clears the workflow.

### The Kaggle rating rule

**A Kaggle rating is observational evidence, never primary evidence, and it
must never be used alone to declare a strategy better or worse.** Record it
if you have it, but it does not gate acceptance — the seeded batch and
self-play numbers do that.

This isn't a hedge, it's measured. As of this checkpoint the live submission
score is described in `README.md` as oscillating in the **~450–560** range
run to run with no code change in between. That range alone rules out reading
any single submission's rating as a verdict on a change: a 472 today and a
548 tomorrow does not mean the agent got better or worse overnight, only that
the ladder is a noisy small-sample signal (opponent mix, matchmaking, live
market conditions). Treat a rating move the same way `CONTRIBUTING.md` says
to treat a one-episode score: not evidence by itself.

> **Open item:** a more detailed run-by-run account of ladder noise has been
> referenced verbally but is not yet written down anywhere in this repo or in
> the GitHub issues/PRs as of this checkpoint. If you have that data, it
> belongs in this file (or a linked comment on Issue #4) with the submission
> IDs it corresponds to — don't let it stay a verbal claim.

### Reproducibility

A checkpoint should be reproducible from the repository alone: `git checkout
<SHA>`, recreate the environment per `README.md`'s Setup section, run the
recorded test/benchmark commands, and get numbers within noise of what's
recorded here. If a checkpoint depends on something not in the repo (a
manual step, an external dataset, a specific machine), that's a known
limitation and must be written down as one.

---

## Checkpoint template

```markdown
## <NAME> — <STATUS: frozen | control | experimental>

- **Commit:** `<sha>`
- **Date:** <YYYY-MM-DD>
- **Environment:** Python <x.y.z>, kaggle-environments <version>

### Behavioural changes
<what changed in main.py, plain language>

### Tests
`unittest discover -s tests`: <N> passing

### Self-play benchmark (experiments/selfplay_bench.py)
| | mean | stdev | min | max | seeds |
|---|---|---|---|---|---|
| self-play | | | | | |

### Seeded benchmark (experiments/seeded_batch.py)
| vs | mean | stdev | win-rate |
|---|---|---|---|
| `pass` | | | |
| `random` | | | |
| `starter` | | | |

### Benchmark configuration
<seed range, episodeSteps, anything non-default>

### Action-level diagnostics
<whatever's relevant — FEED count, weeds, plants landed, etc.>

### Kaggle
- Submission ID: <or "not submitted">
- Rating/range: <observational only — not evidence>

### Interpretation
<what this means, including "wash" calls if applicable>

### Known limitations
<what's not covered/proven>
```

---

## V1 checkpoint

- **Commit:** `0265554` (merge of PR #7, `feat/goose-integration`, into
  `main`) — the last behaviour-affecting commit in that history is `8f94ec0`
  ("feed daily instead of only after a missed day"); everything from
  `a0e9703` onward through `a9bf7d1` is docs/tooling only (no `main.py`
  behaviour change; `a0e9703`'s own message confirms "No behaviour change. 82
  tests pass.").
- **Date:** 2026-08-16
- **Environment:** Python 3.13.7, `kaggle-environments>=1.32.6`
- **Status:** frozen (recommended — see EXPERIMENT_WORKFLOW.md's FREEZE
  CONTROL step; this repo has not yet formally tagged a frozen control, so
  treating V1 as it is the first order of business)

### Behavioural changes

V1 is the merge of two lines of work that had been developed in parallel and
measured separately:

1. **Crop economics** (PR #3, prior to this merge): fixed `choose_crop`'s
   scoring bug that ranked crops by cheapness instead of value density
   (melon scored last despite being the strongest crop in the game),
   end-of-season liquidation regardless of price, and self-supply-aware
   pricing (discount a crop's score by tiles already committed to it).
2. **Animal/goose loop** (PR #7, this merge): one-goose coop/feed/care/egg
   loop, `FERTILIZE`-adjacent wheat reserve logic, plus two bugs found and
   fixed during integration — duplicate tile actions from units acting on a
   shared observation snapshot, and a feed rule that self-oscillated into
   feeding every other day.

### Tests

`unittest discover -s tests`: **82 passing**

### Self-play benchmark (experiments/selfplay_bench.py)

Three points on the same metric, not a single before/after — each step
changed more than one thing, so read this as a trajectory, not a clean A/B:

| stage | commit | self-play mean | stdev |
|---|---|---|---|
| crop economics only (no animals) | `6c6a7d7` | 22,852 | — |
| + animal loop merged in + duplicate-tile fix, feed still oscillating | `a0e9703` | 27,799 | ±2,362 |
| + feed-daily fix (`FEED` 15→30) | `ebc8212` (= this checkpoint's behaviour) | **27,246** | ±1,604 |

The last step (27,799 → 27,246) is explicitly **inside stdev — the PR
description calls it "a wash, not a measured gain," shipped for risk
reduction (0 animal escapes across 48 episodes), not for mean bank. Don't
quote 22,852 → 27,246 as "the animal integration gain" — the gain from
animals alone is closer to +4,947 (22,852 → 27,799); the last ~550 is noise
plus a deliberate risk trade.

### Seeded benchmark (experiments/seeded_batch.py)

12 seeded 720-turn seasons per opponent:

| vs | mean | stdev | min | max | win-rate |
|---|---|---|---|---|---|
| `pass` | 41,969 | ±2,206 | 38,524 | 46,198 | 12/12 |
| `random` | 42,812 | ±1,926 | 40,929 | 45,922 | 12/12 |
| `starter` | 43,105 | ±1,740 | 40,949 | 46,028 | 12/12 |

**Read the self-play number above, not this table** — `pass`/`random`/
`starter` never sell, so the market stays pristine and these are inflated by
roughly 1.5x versus a real competitor.

### Benchmark configuration

Seeded batch: seeds 0–11 (12 seeds), `episodeSteps: 720`, vs each of `pass`/
`random`/`starter`. Self-play: seeds 0–5 (6 seeds → 12 agent-results),
`episodeSteps: 720`. Validation gate: seeds 0–4, `['DONE', 'DONE']` required.

### Action-level diagnostics

Measured during PR #7 integration, 12-seed batches unless noted:

| metric | before (`a0e9703`) | after (`ebc8212`) |
|---|---|---|
| `FEED` / season | 15 | 30 (engine max) |
| `EGG` sold | 26 | 52 |
| `CARE` duplicate/wasted turns | 46 | 0 |
| `WATER` | 509 | 568 |
| plants **landed** (not just requested) | 70 | 95 |
| animal escapes / 48 episodes | — | 0 |

The "plants landed" row exists because raw `PLANT` action counts are
misleading here: the engine drops *all* `PLANT` requests for a crop when
demand exceeds held seeds that turn, not just the excess, so a raw histogram
made a 36% real rise look like a 35% drop. See `CONTRIBUTING.md`.

### Kaggle

- Submission ID: see `kaggle competitions submissions kaggriculture` for the
  current active pair — not recorded here as a fixed value since it changes
  as the team submits.
- Rating/range: live submission oscillating **~450–560** as of this
  checkpoint (`README.md`), unsettled. **Observational only — see the rule
  above.**

### Interpretation

V1 is a genuine improvement over the crop-economics-only baseline on every
metric that matters for risk (animal survival, duplicate-turn waste,
plants actually landing), and the animal loop itself is a real mean gain
(+4,947 self-play vs the crop-only baseline). The final two bug fixes on top
of that are a deliberate risk-for-mean trade, not a further mean gain, and
should not be reported as one.

### Known limitations

- `FERTILIZE` for already-planted crops is not implemented (tracked in PR
  #5 — has a known off-by-one bug, not yet merged).
- `BUY_LAND` is a measured dead end (tested twice, always a loss) — not
  implemented, intentionally.
- Only one goose (`MAX_ANIMALS`); cow/sheep are data-driven off `ACTIVE_ANIMALS`
  but untested with more than one animal active.
- No per-turn seed budget across units — a unit can still "claim" a seed
  type another unit already spent this turn (~43 wasted unit-turns/season
  measured, down from 144 pre-fix).
- The gap between self-play (~27,000) and the live ladder (~450–560 rating,
  not bank) is large and not fully explained; self-play is the best local
  proxy the team has, not a validated predictor.
