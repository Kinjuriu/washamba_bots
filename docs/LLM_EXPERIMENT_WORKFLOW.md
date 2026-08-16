# LLM Experiment Workflow

A separate workflow for evaluating LLM/agentic strategies against the
deterministic agent. **No LLM code exists in this repo yet — this document is
process only, written ahead of that work so the evaluation bar is decided
before the first line is.**

This does not replace **[EXPERIMENT_WORKFLOW.md](EXPERIMENT_WORKFLOW.md)**;
it adds control/treatment structure specific to LLM experiments on top of it.
Every step in that document (self-play, seeded batch, action-level
diagnostics, one-variable-at-a-time) still applies.

## The non-negotiable rule

**The deterministic V1 agent (`nikaangukia_meroni`, see `CHECKPOINTS.md`)
remains the control, permanently.** An LLM-based strategy is a *treatment*
that must beat it on the same benchmarks the team already trusts. It does not
get a separate, easier bar because it's a different kind of agent.

**Do not use an LLM because it sounds more intelligent.** That is not a
hypothesis. Every LLM experiment needs the same thing any other change
needs per `EXPERIMENT_WORKFLOW.md`: a defined metric, stated before the
experiment runs, that the LLM is expected to move — and it must demonstrate
measurable improvement over the frozen deterministic control to be accepted.
If it doesn't beat V1 on that metric, it's a documented rejection, the same
as any other dead end in `CLAUDE.md`.

## CONTROL / TREATMENT

```
CONTROL:
  frozen deterministic V1 (nikaangukia_meroni, per CHECKPOINTS.md)

TREATMENT:
  LLM-enhanced strategy
```

Same seeded batches, same self-play setup, same opponents, same seeds. The
LLM treatment is evaluated exactly like any other experimental checkpoint —
it does not get its own benchmark methodology.

## Workflow

1. **Freeze the deterministic baseline.** Confirm which checkpoint is
   `frozen` in `CHECKPOINTS.md` before starting. If none is frozen yet, that
   is step zero, same as in `EXPERIMENT_WORKFLOW.md`.
2. **Define the decision/problem the LLM is supposed to improve.** Not "make
   the agent smarter" — a specific decision point (e.g. "which crop to plant
   given current market state," "when to liquidate the shed"). A vague scope
   can't be benchmarked against a specific control decision.
3. **Define an explicit interface between the LLM and game state.** What
   subset of `obs` it sees, in what format, and how its output maps back to
   a legal action. This interface is part of the experiment design, not an
   implementation detail to be decided later.
4. **Define allowed actions and safety constraints.** What the LLM can and
   cannot cause the agent to do. Given the **1-second per-turn `actTimeout`**
   and the **no-network-I/O** constraint (`CLAUDE.md`), this also has to
   state up front how those hard constraints are satisfied — not discovered
   at submission time.
5. **Define what information the LLM receives.** A precise list, not "the
   observation" — state, history window (if any), derived features computed
   before the call.
6. **Define what the LLM is allowed to decide.** The scope from step 2, made
   concrete: is it choosing a crop, a full action, a threshold, a plan for
   the day? Narrower is easier to benchmark and easier to fall back from.
7. **Define cost/latency/token constraints, if relevant.** Per-turn budget
   under the 1s `actTimeout` (with the 60s overage bank in mind, per
   `CLAUDE.md`), and any token/cost ceiling for the experiment as a whole.
8. **Run deterministic tests.** `unittest discover -s tests` still must be
   green — the deterministic surface area the LLM wraps or calls into is not
   exempt from the existing suite.
9. **Run seeded self-play.** `experiments/selfplay_bench.py`, same seed
   protocol as any other experiment.
10. **Compare against the frozen deterministic control.** Same benchmarks,
    same seeds, side by side — per `EXPERIMENT_WORKFLOW.md`'s COMPARE AGAINST
    CONTROL step.
11. **Analyse failure modes and action distributions.** LLM treatments have
    failure modes the deterministic agent doesn't: malformed/illegal actions,
    latency spikes near the timeout, decisions that are locally plausible but
    strategically inconsistent turn-to-turn. Use
    `experiments/replay_diagnostics.py` and look specifically for illegal or
    discarded actions, not just the final bank.
12. **Only then consider ladder submission.** Same submission protocol as
    everything else — see `EXPERIMENT_WORKFLOW.md`'s KAGGLE SUBMISSION step
    and [Issue #4](https://github.com/Kinjuriu/washamba_bots/issues/4).

## Reproducibility requirements

Every LLM experiment must record, alongside the standard checkpoint fields
in `CHECKPOINTS.md`:

- **Model name/version** — exact identifier, not "the latest model."
- **Prompt/version** — the literal prompt template, versioned (e.g. in a
  file, with a hash or tag), not paraphrased in a write-up.
- **Temperature/settings**, if applicable.
- **Seed** — both the environment seed and, if the model call itself
  supports one, the sampling seed.
- **State representation** — the exact transformation from `obs` to what the
  model sees (step 3/5 above, as actually implemented).
- **Tool/interface definition** — the exact action schema the model can
  emit, and how it's validated/clamped to legal actions.
- **Benchmark configuration** — same as any checkpoint: seed range,
  `episodeSteps`, opponent set.

Without all of these, the result can't be reproduced or re-verified later —
the same standard `CONTRIBUTING.md` already sets for deterministic changes
("if you quote a number, commit the script that produced it"), extended to
cover what a deterministic script doesn't need to state.
