# Checkpoints and the experiment workflow

A checkpoint is a **frozen, documented, measured** version of the agent that
every later experiment is compared against. It is our experimental control.

The point is not ceremony. It is that this project has repeatedly produced
numbers that looked like results and were not — a rating that was really a
default, a "no gain" that was really the wrong statistical test, a benchmark
that pointed in the *opposite* direction to the ladder. A fixed control is
what makes those detectable.

## Why "whatever is on main" is not a control

`main` moves. If you measure your experiment on Tuesday against a baseline
you measured on Monday, any change someone else merged in between is inside
your delta and you cannot see it.

A checkpoint pins a **commit SHA** and the exact numbers that commit
produced. Two people measuring against the same checkpoint a week apart get
comparable answers.

**A frozen checkpoint is never edited.** If its numbers turn out to be wrong,
add a correction note to the *newer* checkpoint saying so — do not rewrite
history, because other people's comparisons refer to the old figures.

## The workflow

```
OBSERVE      something in a replay or diagnostic looks wrong
HYPOTHESIZE  say what you think causes it, and what number would move
FREEZE       note the checkpoint you are measuring against
CHANGE ONE   one variable, so a result is attributable
TEST         unit tests pass
COMPARE      paired or head-to-head against the checkpoint (see below)
DIAGNOSE     confirm the mechanism fired, not just that the mean moved
DOCUMENT     record it, including if it lost
SUBMIT       only if it won, and only after announcing it
NEW CHECKPOINT once merged and measured
```

Two steps carry most of the weight.

**CHANGE ONE THING.** Two changes measured together give one number and no
way to attribute it. If they interact, you learn nothing about either.

**DIAGNOSE.** A mean can move for reasons unrelated to your change. We once
shipped a "fix" for a low `FEED` count where the suite passed, the mean moved
and `FEED` stayed at exactly 15 — the actual bug untouched. Count the thing
you were trying to change.

## Choosing the comparison

This is the part that has bitten us most, so it has its own rule.

| what you changed | harness | why |
|---|---|---|
| farm upkeep, planting, movement, animals | `experiments/paired_compare.py` | vs `pass`/`starter`, same seeds, paired |
| **anything about selling** — thresholds, timing, quantities, liquidation | `experiments/head_to_head.py` | the built-ins never sell, so a market change looks free against them |
| overall level of the agent | `experiments/selfplay_bench.py` | the headline number |
| broad regression check | `experiments/seeded_batch.py` | inflated, but cheap and wide |

**Never judge a delta against the across-seed stdev.** That spread (~2,000)
measures how much *seasons* differ from each other; both versions play the
same seeds, so it cancels. Use the paired difference. This mistake caused us
to reject two real, sizeable gains — see `CONTRIBUTING.md`.

**Read the win count before any statistic.** Better on 12 of 12 seeds needs
no t-value; better on 7 of 12 is not rescued by one.

**The built-in benchmark can point the wrong way, not merely overstate.**
Liquidating from day 19 instead of 25 measures **−440, worse on 10 of 12
seeds** against `starter`, and **+617, winning 21 of 24 matches** head to
head. With an uncontested market, holding out for a better price is simply
correct; with a competitor in the same order book, selling late means losing
the race for the town's daily demand. The ladder is contested.

## Kaggle ratings are secondary evidence

**Do not interpret a single rating reading.** Every submission is seeded at
**600** before it has played anything, then drifts. One measured trajectory
on unchanged code:

```
600.0 → 707.8 → 571.6 → 488.5 → 547.8 → 472.1 → 475.0
```

Quoting minute six gives "+28%"; minute twenty-one gives "no change". The
swing is roughly ±120 — wider than any single change we have shipped.

Keep one of the two active submission slots as an **unchanged control** while
evaluating a new one. That is the only reason we could tell that a 20-point
gap between two of our agents was noise.

Local self-play is the better signal. The ladder confirms direction over
days, not hours.

## Recording an experiment that lost

**A negative result is worth as much as a feature**, and it is only worth
anything if it is written down. `CLAUDE.md` has a "measured dead ends"
section; add to it, with the numbers and the harness used.

We have re-run losing ideas because nobody recorded them, and we nearly
re-ran the four-goose experiment on a theory that had already been
disproved. If you burn an afternoon proving something does not work, that
afternoon is only spent once if you document it.

## Deterministic vs LLM experiments

Everything above describes our **deterministic** agent: a fixed rule ladder
whose behaviour on a given seed is identical every run. That is what makes
paired comparison work at all — two versions on seed 7 differ only by the
change you made.

**No LLM experiment has been run in this repo yet**, and this section exists
to record the constraints rather than to describe a workflow we have. Anyone
starting one should know the evaluation gets harder, not just the code:

- **A sampled model is not reproducible per seed**, so the paired comparison
  above breaks. You need either temperature 0 or many more episodes to
  average the model's own variance out — treat it like the built-in `random`
  opponent, which we already exclude from pairing for this reason.
- **1 second per turn**, with a 60-second bank for the whole episode
  (`obs["remainingOverageTime"]`). The current agent uses none of that bank.
  There is no room for a per-turn API call, and there is no network anyway.
- **No network I/O inside the agent.** Episodes run with no ingress or
  egress, so a model has to be bundled.
- **100 MiB total submission, 6.5 GiB RAM, 1.6 vCPUs.** That bounds a
  bundled checkpoint to something small.

A hybrid is the more plausible shape: an LLM used *offline* to tune
constants or propose crop policies, with the shipped agent staying
deterministic. That keeps the evaluation machinery in this document valid.

## Checkpoints

| checkpoint | commit | date | self-play mean | notes |
|---|---|---|---|---|
| **[V2 sheep](checkpoints/V2-sheep.md)** | `93d6bed` | 2026-08-16 | **35,583** | **current control** — sheep, denser crew, demand-aware scoring |
| [V1 baseline](checkpoints/V1-baseline.md) | `df69f97` | 2026-08-16 | 28,212 | superseded: crop economics + goose + fertilizer |

## A note on self-play stdev, if you compare across checkpoints

Until 2026-08-16, `selfplay_bench.py` pooled **both** players' banks into one
sample set. In a mirror match those two banks are near-perfectly correlated —
usually byte-identical — so pooling halved the apparent spread and overstated
precision. It now averages the pair into one observation per seed.

**Means are unaffected**; only the stdev changes, and it gets *larger*. V2's
record quotes 3,678 from the old pooling; re-measured properly it is ~4,164.
V1's figure has the same flaw, so the two frozen records stay comparable to
each other — just don't compare either stdev against a freshly measured one.

Both records are left as written. A frozen checkpoint is never edited, even
when the tooling behind it improves.

## Creating the next one

Copy `checkpoints/V1-baseline.md`, fill in every field from a fresh
measurement of the merged commit, and add a row above. Do not copy numbers
forward from a previous checkpoint — re-measure. Then add the row to this
table and leave the older record untouched.
