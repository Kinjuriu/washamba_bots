"""Paired A/B of two agent files over the same seed set.

Why this exists, and why you should reach for it before `seeded_batch.py`
when comparing two versions:

`seeded_batch.py` reports a mean and an across-seed stdev. That stdev is
large (~2,000) because *seeds differ enormously from each other* - some
seasons simply have kinder weeds and shop unlocks than others. Judging a
change by "is the delta bigger than that stdev?" throws away the fact that
both versions played the *same* seeds, and it is far too strict: it hides
real gains behind variance that cancels out.

The fix is the standard paired comparison. Run both versions on seed N,
subtract, and look at the spread of the *differences*. Season-to-season
luck is common to both arms and drops out.

It is not a subtle correction. Measured on the fertilizer change:

    across-seed view   +1,764 against a stdev of 2,206  -> "within noise"
    paired view        +1,764 against a stderr of 320,
                       t = 5.5, better on 12 of 12 seeds -> decisive

Same episodes, same numbers, opposite conclusion.

Read `wins` first. If one version is better on 12 of 12 seeds, no
statistics are needed to know something real happened; if it wins 7 of 12,
no t-value rescues it.

Use `pass` or `starter` as the opponent. The built-in `random` agent has
its own uncontrolled RNG, so its episodes are not reproducible per seed and
the pairing is broken (see CLAUDE.md).

Usage:
    # compare working tree against main
    git show main:main.py > /tmp/base_main.py
    .venv/Scripts/python.exe experiments/paired_compare.py /tmp/base_main.py main.py

    # optional: opponent and seed count
    .venv/Scripts/python.exe experiments/paired_compare.py A.py B.py starter 12
"""

import statistics
import sys
from pathlib import Path

from kaggle_environments import make

# Make `from experiments.seeds import ...` work when this script is run
# directly (`python experiments/paired_compare.py ...`). Without this, the
# experiments/ directory is not on sys.path and the import below fails with
# `ModuleNotFoundError: No module named 'experiments'`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments.seeds import DEV_SEEDS, HOLDOUT_SEEDS

# `random` is excluded on purpose: its own RNG is not seed-controlled, so
# the same seed does not reproduce the same episode and pairing is invalid.
PAIRABLE_OPPONENTS = ("pass", "starter")

# Default seed set for development iteration. Use ``--seed-set holdout`` to
# run against the held-out set after a change is frozen; see experiments/seeds.py.
SEED_SETS = {"dev": DEV_SEEDS, "holdout": HOLDOUT_SEEDS}


def run_one(agent_path, opponent, seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([agent_path, opponent])
    return env.steps[-1][0].reward


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)

    baseline_path, candidate_path = sys.argv[1], sys.argv[2]
    opponent = sys.argv[3] if len(sys.argv) > 3 else "starter"
    n_seeds = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    seed_set = "dev"
    if "--seed-set" in sys.argv:
        seed_set = sys.argv[sys.argv.index("--seed-set") + 1]
    if seed_set not in SEED_SETS:
        print(
            f"error: unknown seed set '{seed_set}'. Use one of {list(SEED_SETS)}.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    if opponent not in PAIRABLE_OPPONENTS:
        print(
            f"warning: '{opponent}' is not seed-reproducible, so the pairing is "
            f"invalid. Use one of {PAIRABLE_OPPONENTS}.",
            file=sys.stderr,
        )

    seeds = list(SEED_SETS[seed_set])
    # Allow an explicit seed count to trim the selected set (e.g. ``--seed-set
    # holdout 6`` for a quick partial run), but never to extend it.
    n_seeds = min(n_seeds, len(seeds))
    seeds = seeds[:n_seeds]

    deltas = []
    print(f"vs {opponent}, {len(seeds)} seeds (set={seed_set})\n")
    print(f"{'seed':>4} {'baseline':>9} {'candidate':>10} {'delta':>9}")

    for seed in seeds:
        baseline = run_one(baseline_path, opponent, seed)
        candidate = run_one(candidate_path, opponent, seed)
        delta = candidate - baseline
        deltas.append(delta)
        print(f"{seed:4d} {baseline:9.0f} {candidate:10.0f} {delta:+9.0f}")

    mean_delta = statistics.mean(deltas)
    wins = sum(1 for d in deltas if d > 0)

    print()
    print(f"  paired mean delta  {mean_delta:+9.0f}")
    print(f"  better on          {wins}/{len(deltas)} seeds")

    if len(deltas) > 1:
        spread = statistics.stdev(deltas)
        stderr = spread / len(deltas) ** 0.5
        print(f"  sd of deltas       {spread:9.0f}")
        print(f"  standard error     {stderr:9.0f}")
        if stderr:
            print(f"  t                  {mean_delta / stderr:9.2f}")
            print()
            print("  |t| > ~2.2 with 12 seeds is significant; read `better on` first.")


if __name__ == "__main__":
    main()
