---
name: delegate
description: |
  Decide whether to do a Kaggriculture task in the main thread or dispatch it
  to a cheaper subagent, and write the brief so the subagent actually
  succeeds. Use before running a seeded benchmark, sweeping a parameter,
  diagnosing a replay, regenerating the notebook, syncing docs, or any other
  long-running mechanical job in this repo. Also use when asked to "delegate
  this", "use a subagent", "don't burn Opus", or "run the benchmarks".
---

# Delegation

Benchmarks in this repo take 3-10 minutes and emit thousands of lines of
noise. Running one in the main thread burns expensive context on output
nobody reads. Delegation is a **context** decision before it is a cost one.

## Contract

- Every delegated job names the interpreter, the exact command, and the
  baseline to compare against
- Every delegated job is told what NOT to touch (submit, push, edit `main.py`)
- Judgement calls stay in the main thread; execution goes out
- Results come back as numbers, never as raw episode output

## Routing

| Task | Where | Why |
|---|---|---|
| Diagnosing why a change helped or hurt | **Main thread** | Needs the whole session's context |
| Designing scoring, economics, priority ladders | **Main thread** | Judgement, not execution |
| Deciding what to measure next | **Main thread** | Judgement |
| Running a seeded batch / self-play benchmark | **Sonnet** | Mechanical, slow, noisy |
| Sweeping one constant across values | **Sonnet** | Mechanical, repetitive |
| Replay diagnosis against a written question | **Sonnet** | Mechanical extraction |
| Regenerating the notebook, syncing docs to numbers | **Sonnet** | Spec-following |
| Rename sweeps, single-file mechanical edits | **Haiku** | Trivial |

Dispatch independent jobs in **one message** so they run concurrently. Run
them in the background and keep working.

## Phases

1. **Decide.** If the task needs session context or a judgement call, keep
   it. If it follows a spec you can write down, delegate it.
2. **Write the brief** using the checklist below.
3. **Keep working** while it runs — never idle-wait on a background agent.
4. **Verify the result.** Subagents have reported confident, wrong
   conclusions in this project. Check the numbers against what you expected;
   if a claim is structural ("X is broken", "the env is Y-backed"), confirm
   it yourself before acting on it.

## The two benchmarks

Both live in the repo, so a brief can name them directly:

```bash
.venv/Scripts/python.exe experiments/seeded_batch.py        # vs the 3 built-ins
.venv/Scripts/python.exe experiments/selfplay_bench.py 6    # agent vs itself
```

Never point a brief at a scratchpad path — those are session-specific and
will not exist for the agent you dispatch.

## Every brief must include

- **Interpreter:** ``.venv/Scripts/python.exe`` — never bare `python`, which
  resolves to a different install with no `kaggle_environments`
- **Working directory:** the repo root
- **Exact commands**, copy-pasteable
- **The baseline numbers** to compare against, or the agent cannot judge
  anything
- **The noise warning:** every command prints hundreds of environment
  registration lines (`zerosum`, `twixt`, `OpenSpiel exception: ...`). Tell
  them to filter: `| grep -viE "^(openspiel|[a-z_0-9]+)$" | tail -12`
- **Timeouts:** at least 900000 ms for a 12-seed batch
- **Hard limits:** do not submit to Kaggle, do not push, do not commit, do
  not edit `main.py` unless that is the job
- **Report shape:** a table of numbers plus a one-line verdict

## Judging results

- **A single episode proves nothing.** Run-to-run spread exceeds 1,400 bank.
  Always a seeded batch.
- **Under ~1000 bank on the built-ins is noise** — stdev is 1300-2900.
- **Self-play is the number that matters.** `pass`, `random` and `starter`
  sell nothing, so they leave every market pristine and flatter us badly. A
  33,000 local score converged to 289 on the real ladder.
- **A/B against `pass`/`starter`, not `random`** — a fixed seed does not
  control the built-in `random` agent's own RNG.

## Anti-patterns

- Running a 12-seed batch in the main thread "just this once" — that is
  thousands of lines of noise into expensive context
- Delegating the decision instead of the execution: "figure out how to make
  the agent better" is not a brief, "sweep X over [1,2,3] and report" is
- Omitting the baseline, so the agent reports numbers with no verdict
- Spawning subagents sequentially when the jobs are independent
- Accepting a subagent's structural claim without checking it
- Blocking on a background agent instead of continuing
