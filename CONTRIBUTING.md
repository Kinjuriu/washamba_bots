# Contributing

Rules for the Washamba Bots team. Every item here exists because it actually
went wrong on this repo — nothing is here as generic good practice.

`CLAUDE.md` is the deep reference (mechanics, engine gotchas, agent I/O
contract). This file is the short version of **how we work** so we stop
re-losing the same days.

> **Status: proposed, not yet adopted.** One item below binds the whole team
> and needs an explicit yes before it's real — the **PR benchmark gate**.
> Everything else is either a description of how this repo actually behaves
> (argue with those on the evidence) or a competition rule we don't get a
> vote on. **Check the Kaggle team-merge section before Sept 23** — that one
> is not optional.

## The one rule

**This repo punishes plausible reasoning. Almost everything that breaks here
breaks silently — no exception, no failing test, no error in the log.**

A change is not done because it looks right, and not because the suite is
green. It is done when you have measured the number the change was supposed
to move.

**Shape vs knob.** From 2026-09-01, an agent-shape change starts in
`mydocs/FACTS.md` (add / remove / supplement a row, then a throwaway).
`docs/EXPERIMENT_WORKFLOW.md` below is how we measure **knobs inside** a
fact-set that already holds. Do not “change one thing” on shipped
`main.py` as a way to discover architecture. See
`mydocs/AGENT_BUILDING_PROTOCOL.md`.

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

Report **mean, stdev and win-rate**, not a best score.

**But do not judge a change by that stdev.** Comparing a mean against the
across-seed spread is the wrong test when both versions ran the *same*
seeds. That spread (~2,000) mostly measures how much seasons differ from
each other — kinder weeds, luckier shop unlocks — and it is common to both
arms, so it cancels. Judging against it is far too strict and hides real
gains.

Use a **paired comparison** instead: run both versions on seed N, subtract,
and look at the spread of the *differences*.

```bash
git show main:main.py > /tmp/base_main.py
.venv/Scripts/python.exe experiments/paired_compare.py /tmp/base_main.py main.py
```

It is not a small correction. The fertilizer change, same episodes both ways:

| view | reading | verdict |
|---|---|---|
| across-seed | +1,764 vs stdev 2,206 | "within noise" |
| **paired** | +1,764 vs stderr 320, t=5.5, **12/12 seeds** | decisive |

**Read the win count first.** Better on 12 of 12 seeds needs no statistics;
better on 7 of 12 is not rescued by any t-value. Only pair against `pass`
or `starter` — `random` has its own uncontrolled RNG, so the same seed does
not reproduce the same episode and the pairing is invalid.

If a change is genuinely inconclusive, say "within noise" — do not call it
a win.

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

**Count the effect, not the attempt.** The engine silently converts a `PLANT`
request to `PASS` when a turn's demand for a crop exceeds held seeds, so an
action histogram counts attempts that never happened. Reading it raw made a
36% *rise* in plants landed look like a 35% drop. Ask what the engine
actually applied.

**A ladder reading is one sample of a noisy process — the same rule as a
single episode.** Every submission is seeded at a rating of **600** before it
has played anything, then drifts as episodes accumulate. One measured
trajectory over 21 minutes:

```
600.0 → 707.8 → 571.6 → 571.6 → 488.5 → 547.8 → 472.1
```

Quoting minute six gives "+28%"; minute twenty-one gives "no change". Same
code. The swing is roughly **±120**, which is wider than any single change
we have ever shipped.

So: **keep an unchanged control submission active** whenever you're testing a
new one. We get two active slots either way, and the control is the only
thing that tells you whether a difference is real — it drifted 467.4 → 452.3
on its own over the same window, which is how we knew a 20-point gap between
two agents was noise. Never quote a rating that is still moving.

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

Then the seeded batch above. **(Proposed)** a PR that changes agent behaviour
without benchmark numbers in the description gets sent back — not out of
process fetishism, but because we genuinely cannot tell it from a regression.

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

## Submissions — anyone can submit, but announce it first

**Only 5 submissions per day, and only the latest 2 stay active for
matchmaking and final scoring.** That second half is the dangerous one: an
upload doesn't just consume quota, it can silently **evict a better agent**
from the active pair. There is no undo, and the ladder signal that agent was
still accumulating is gone with it.

Anyone can submit. The rule is not permission, it's visibility — nobody
should discover a submission by seeing the score move.

**Before you upload, post in the team channel:**

- what changed, in one line;
- the self-play number and the seed count behind it;
- which of the currently active 2 you expect to displace.

**Never submit a change that hasn't been through the seeded batch.** A
submission slot is the scarcest thing we have; spending one on an unmeasured
change costs a day of ladder signal to learn what 4 minutes locally would
have told you.

If two people want to submit the same day, the one with benchmark numbers
goes first.

**Keep one of the two active slots as an unchanged control** while a new
agent is being evaluated. Ratings drift ±120 on their own; without a control
you cannot tell a real gain from the swing. Don't replace both slots at once.

### Everyone contributing must be on the Kaggle team

**Private sharing of competition code outside your team is a rules
violation** (`docs/kaggriculture_context.md:53`) — this repo counts. Anyone
who contributes here has to be entered *and* on the same Kaggle team.

**Verified Aug 16, 2026:** team `washamba_bots` (id 16675684) has four
members — `billygmwangi`, `futurecentaur`, `peterkibetspidey`,
`stephanenjoki`. We're compliant today.

It matters again if someone new joins. **The team merger and entry deadline
is Sept 23, 2026**, a week before final submissions close, and it cannot be
done late — so a contributor added in late September cannot be added to the
team afterwards. Get them on the roster before they push code.

Check the roster in the leaderboard export
(`kaggle competitions leaderboard kaggriculture --download`, the
`TeamMemberUserNames` column) rather than trusting memory.

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
