# Contributing

Rules for the Washamba Bots team. Every item here exists because it actually
went wrong on this repo — nothing is here as generic good practice.

`CLAUDE.md` is the deep reference (mechanics, engine gotchas, agent I/O
contract). This file is the short version of **how we work** so we stop
re-losing the same days.

## The one rule

**This repo punishes plausible reasoning. Almost everything that breaks here
breaks silently — no exception, no failing test, no error in the log.**

A change is not done because it looks right, and not because the suite is
green. It is done when you have measured the number the change was supposed
to move.

## Evidence standard

**One episode is not evidence.** Run-to-run spread is enormous: the same
`main.py` vs `random` scored 5228 and 3776 on two unseeded runs, and stdev
scales with score (~±600 at the 5,000 era, ~±1,600-2,200 now). A "+1,000 on
one seed" is noise, not an improvement.

This has cost us real time twice — once concluding the agent "isn't beating
starter" from a single game (a 12-seed batch showed 10/12 wins), and once
writing single lucky runs into the docs as a regression floor.

Before claiming a strategy change works:

```bash
.venv/Scripts/python.exe experiments/seeded_batch.py     # 12 seeds x 3 built-ins, ~4 min
.venv/Scripts/python.exe experiments/selfplay_bench.py   # the honest number
```

Report **mean, stdev and win-rate**, not a best score. If the delta is inside
the stdev, say "within noise" — do not call it a win.

**Built-in opponents inflate everything.** `pass`, `random` and `starter`
never sell, so the market stays pristine and our prices never face a
competitor. Same agent: ~41,000 vs built-ins, ~28,000 in self-play. A/B
against `pass`/`starter` because they are seed-reproducible, but quote
**self-play** as the number that predicts the ladder.

**Verify the metric your fix targets, not just the mean.** We shipped a
"fix" for a low `FEED` count that left the count at exactly 15 — the suite
passed, the mean moved, and the actual bug was untouched. If you are fixing
watering, count `WATER`. Use `experiments/replay_diagnostics.py`.

**Measurements go stale.** A code review reported "93% of PLANT actions
discarded"; on the current build it is 31%. Always state *which commit* a
number was measured on, and re-measure before acting on someone else's.

## Before you open a PR

```bash
.venv/Scripts/python.exe -m unittest discover -s tests    # must be green

# Kaggle validates every upload with a self-play episode. A crash here
# rejects the submission no matter how good the strategy is.
.venv/Scripts/python.exe -c "
from kaggle_environments import make
env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': 0})
env.run(['main.py', 'main.py'])
print([s.status for s in env.steps[-1]])   # must be ['DONE', 'DONE']
"
```

Then the seeded batch above. A PR that changes agent behaviour without
benchmark numbers in the description will be sent back — not out of process
fetishism, but because we cannot tell it from a regression.

## What a PR description must contain

- **What changed and why** — the mechanic, not just the diff.
- **Benchmark table**: mean / stdev / win-rate vs the same seed set, baseline
  and new, plus the commit the baseline was measured on.
- **The metric the change targets**, before and after (e.g. `FEED 15 -> 30`).
- **What you did not do** — known gaps, so the next person doesn't assume
  coverage that isn't there.

## Reviewing

- Check the numbers were measured on the branch, at its current head.
- Re-run the batch yourself if the change is large. It is 4 minutes.
- After merging any branch that touches `main.py`, **re-verify the merge did
  not silently undo something**. A merge once kept a stale `choose_crop`
  docstring describing a formula we had already fixed, and came close to
  reinstating the scoring bug itself. Green tests did not catch it.

## Things that fail silently — check these every time

- **The entrypoint is the last callable in the module**, not the function
  named `agent`. Anything callable added below `agent = nikaangukia_meroni`
  silently becomes the submission; the episode still reports `DONE` and the
  agent finishes on exactly **$3000**. Treat a local score of exactly $3000
  as "my agent never acted", not as a bad strategy.
- **Never commit an OS-specific interpreter path.** The team is split across
  macOS (`.venv/bin/`) and Windows (`.venv/Scripts/`). A hardcoded path in
  `.vscode/settings.json` already broke half the team once — VS Code silently
  falls back to system Python and every `import kaggle_environments` fails.
  Let the Python extension auto-discover `.venv/`; use `sys.executable` in
  committed tooling.
- **Don't commit replay JSONs** (~5 MB each). `.gitignore` covers
  `replay*.json` and `experiments/*.json` — check `git status` anyway.
- **If you quote a number, commit the script that produced it.** Our
  self-play benchmark lived only in a scratch directory for days, so nobody
  else could reproduce the figure we were all quoting.
- **pytest is not installed** and the suite doesn't need it. Match the
  existing stdlib `unittest.TestCase` style — no fixtures, no parametrize.
- **Notebooks**: use the `Python 3.13 (washamba_bots)` kernel and `%pip`,
  never `!pip`. A kernelspec whose `argv[0]` is the bare word `python`
  launches whatever is first on `PATH` — that is how a notebook ends up on
  system Python reporting `No module named kaggle_environments`.

## Submissions — coordinate before you upload

**Only 5 submissions per day, and only your latest 2 stay active for
matchmaking and final scoring.** An uncoordinated upload can evict a better
agent from the active pair and burn quota we can't get back.

Post in the team channel before submitting. One person owns the submission
for a given day.

Final scoring is a single Bradley-Terry tournament roughly two weeks after
the Sept 30 deadline — deliberately, to damp hot streaks. Late-season
leaderboard position is noisy; **don't tune on it.**

## Branches and commits

- Branch per feature: `feat/<thing>`, off `main`.
- Conventional commits: `type(scope): description`.
- Small, frequent commits — change, verify, commit.
- Don't force-push shared branches, and don't rewrite `main`.

## Record what you learn

If you burn an afternoon on something, write the lesson into `CLAUDE.md` —
especially **dead ends**. `BUY_LAND` and a denser crew were both tested twice
and lost both times; that section exists so nobody re-runs them by intuition.
A negative result you documented is worth as much as a feature.
