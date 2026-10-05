# Experiment Workflow

This is the sequence every strategic change to `main.py` goes through, from
noticing something to (maybe) putting it on the ladder. It exists because
this repo has a documented habit of shipping changes that looked right,
passed the suite, and turned out to be noise or a regression — see
`CONTRIBUTING.md`'s evidence standard and the dead ends recorded in
`CLAUDE.md` (`BUY_LAND`, a denser crew — both tested twice, both losses).

For **who's submitting what and when**, see the live thread:
**[Issue #4](https://github.com/Kinjuriu/washamba_bots/issues/4)**. This
document is the process; Issue #4 is the schedule. Don't duplicate one into
the other.

## The sequence

```
OBSERVE
  → FORM HYPOTHESIS
  → DEFINE METRIC
  → FREEZE CONTROL
  → CHANGE ONE THING
  → TEST
  → RUN SELF-PLAY
  → RUN SEEDED BATCH
  → ANALYSE ACTION-LEVEL DIAGNOSTICS
  → COMPARE AGAINST CONTROL
  → ACCEPT / REJECT
  → DOCUMENT
  → ONLY THEN CONSIDER KAGGLE SUBMISSION
```

### OBSERVE

Something in a replay, a diagnostic, or a benchmark output looks off —
weeds piling up, a market crashing, a counter that never moves. Note the
commit you observed it on (see `CONTRIBUTING.md`: "measurements go stale").

### FORM HYPOTHESIS

State what you think is happening and why, in one or two sentences. "Melon
scores last because X" is a hypothesis; "melon seems bad" is not — it has no
falsifiable claim to test.

### DEFINE METRIC

**Before writing code**, name the exact number this change is expected to
move, and in which direction. This is the single most-skipped step and the
one that turns "the mean went up, ship it" into an actual test of the
hypothesis. See the mechanism-matching examples below.

### FREEZE CONTROL

Pick the checkpoint (see `CHECKPOINTS.md`) you're comparing against and treat
it as read-only for the duration of this experiment. If no checkpoint is
currently marked `frozen`, that's step zero — tag one before starting.

### CHANGE ONE THING

**Do not change multiple strategic variables in the same experiment unless
the experiment is explicitly testing an interaction between them.** If you
touch crop scoring and the hire schedule in the same diff, a result can't be
attributed to either one. `CHECKPOINTS.md`'s own V1 entry is a worked example
of what happens when this rule is skipped after the fact — the merge that
produced V1 bundled the animal-loop gain with a separate bug-fix wash, and
untangling which number came from which change took re-reading three PR
descriptions.

If a real experiment needs two changes at once (an interaction test), say so
explicitly in the write-up and don't also claim either change works in
isolation.

### TEST

```bash
.venv/Scripts/python.exe -m unittest discover -s tests
```

Must be green. A green suite is necessary, never sufficient —
`CONTRIBUTING.md` has a documented case of a fix that passed every test while
leaving the actual bug (`FEED` stuck at 15) untouched.

### RUN SELF-PLAY

```bash
.venv/Scripts/python.exe experiments/selfplay_bench.py
```

This is the number that predicts the ladder. `pass`/`random`/`starter` never
sell, so they leave the market pristine and inflate every result by roughly
1.5x — self-play is the only local setup where a second trader is competing
for the same order book.

### RUN SEEDED BATCH

```bash
.venv/Scripts/python.exe experiments/seeded_batch.py
```

12 seeds × 3 built-in opponents, ~4 minutes. Useful because it's cheap,
seed-reproducible against `pass`/`starter` (not `random` — its own RNG isn't
seed-controlled), and catches regressions self-play alone might not surface
on a single seed set. Report mean, stdev, and win-rate — never a single
episode's score.

### ANALYSE ACTION-LEVEL DIAGNOSTICS

```bash
.venv/Scripts/python.exe experiments/replay_diagnostics.py
```

Or the notebook (`notebooks/washamba_bots_experiments_v0.ipynb`, section 7,
"Behavioural diagnostics") for the fuller charts: action histogram,
bank trajectory, farm composition over time, market sale price over time.

This is where DEFINE METRIC gets checked. **Measure the mechanism the change
was intended to affect, not just the final bank balance** — a bank delta
inside stdev tells you nothing about whether the mechanism moved at all, and
a mechanism that didn't move but the bank did is a coincidence, not a result.

| If you changed... | Measure... |
|---|---|
| feeding logic | `FEED` action count, animal production (`EGG` sold), animal escapes |
| watering logic | `WATER` action count, crop survival / weeds at season end |
| pricing / `choose_crop` | sale price, sale timing, shed inventory, market price trajectory, **and** bank balance |
| hiring / crew size | tiles watered/dug per day, weeds at season end, hire spend |
| planting logic | plants **landed**, not `PLANT` actions issued — the engine silently converts a `PLANT` request to `PASS` when demand exceeds held seeds, so a raw histogram can show a rise as a drop (see `CONTRIBUTING.md`) |

Also check: inventory/shed state (is anything pinned at the 100-item cap or
being discarded?), opponent comparison (built-in table vs self-play — a
change that only wins against opponents who never sell is not proven yet),
and variance/noise (is the delta bigger than stdev?).

### COMPARE AGAINST CONTROL

Put the frozen control's numbers and the treatment's numbers side by side —
self-play mean/stdev, seeded-batch mean/stdev/win-rate, and the targeted
metric from the step above. If the delta on any of these is inside its own
stdev, that's "within noise," not a win — say so.

### ACCEPT / REJECT

- **Accept** if the targeted metric moved in the predicted direction *and*
  self-play/seeded-batch didn't regress outside noise. A wash on bank balance
  can still be an accept if it was explicitly a risk trade (see V1's
  feed-daily fix in `CHECKPOINTS.md`) — but say that's what it is.
  Recommended: promote the accepted state to a new checkpoint (see
  `CHECKPOINTS.md`), and only then treat it as the new frozen control if the
  team is ready to move on from the old one.
- **Reject** if the metric didn't move, or moved but a benchmark regressed
  outside noise. Rejecting is a valid, useful outcome — see `CLAUDE.md`'s
  "Measured dead ends" section. A documented rejection saves the next person
  from re-running the same experiment on intuition.

### DOCUMENT

Write the result — accept or reject — into `CLAUDE.md` if it's a durable
lesson (a dead end, a mechanism discovered), and into a new `CHECKPOINTS.md`
entry if it changes what "current" means. Include the commit SHA the numbers
were measured on. An undocumented negative result gets re-run by the next
person who has the same idea.

### ONLY THEN CONSIDER KAGGLE SUBMISSION

The submission protocol itself lives in
**[Issue #4](https://github.com/Kinjuriu/washamba_bots/issues/4)** and
`CONTRIBUTING.md` — summarized here, not duplicated:

- **5 submissions/day**, and **only the latest 2 stay active** for
  matchmaking and final scoring — an upload can silently evict a better
  agent with no undo.
- **Announce before submitting** — post what changed, the self-play number
  and seed count, and which of the active 2 you expect to displace. Anyone
  can submit; the rule is visibility, not permission.
- Run the test suite and the validation gate first — Kaggle rejects any
  upload that crashes its self-play validation episode regardless of
  strategy:

  ```bash
  .venv/Scripts/python.exe -m unittest discover -s tests
  .venv/Scripts/python.exe -c "
  from kaggle_environments import make
  env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 0})
  env.run(['main.py', 'main.py'])
  print([s.status for s in env.steps[-1]])   # must be ['DONE', 'DONE']
  "
  ```
- Run the seeded batch and have the numbers ready to post — an unmeasured
  submission spends the scarcest resource the team has to learn what four
  minutes locally would have told you.
- **Keep an unchanged control submission active whenever possible**, per the
  team rule established after ladder ratings turned out to be too noisy to
  read as primary checkpoints (see `CHECKPOINTS.md`'s Kaggle rating rule). A
  rating alone — up or down — is never grounds to accept or reject a change;
  the workflow above is.
