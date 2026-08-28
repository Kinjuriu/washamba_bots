"""
Targeted re-test, not a sweep: is the "MAX_ANIMALS=5 collapses to 356" cliff
CLAUDE.md records still present under current main.py, or was it - like the
second-sheep finding CLAUDE.md's own 2026-08-17 correction already
reversed - an artifact of the days 3-7 cash trough that
MIN_CASH_RESERVE_FOR_SEED_BUYING's later retune (100 -> 450) closed?

This is diagnostic-only, feeding docs/architecture_comparison.md's
follow-up causal analysis (experiments/scale_architecture_v0_report.md) -
not itself a submission candidate. ONE constant, ONE step past current
(4 -> 5), nothing else touched.

Usage:
    .venv/Scripts/python.exe experiments/candidates/max_animals_5_retest.py
    .venv/Scripts/python.exe experiments/paired_compare.py main.py experiments/candidates/max_animals_5_retest.py starter 12
"""
import os
import sys


def _find_repo_root():
    candidates = []
    if "__file__" in dir():
        this_dir = os.path.dirname(os.path.abspath(__file__))
        candidates.append(os.path.abspath(os.path.join(this_dir, "..", "..")))
    here = os.getcwd()
    for _ in range(4):
        candidates.append(here)
        here = os.path.dirname(here)
    for c in candidates:
        if os.path.isfile(os.path.join(c, "main.py")):
            return c
    return os.getcwd()


_ROOT = _find_repo_root()
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import main as base  # noqa: E402

base.MAX_ANIMALS = 5


def max_animals_5_retest(obs):
    return base.nikaangukia_meroni(obs)


def _self_test(seeds=(0, 1, 2)):
    from kaggle_environments import make

    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([max_animals_5_retest, max_animals_5_retest])
        a, b = env.steps[-1]
        print(f"seed {seed}: seat0 {a.reward:>8.0f} [{a.status}]   seat1 {b.reward:>8.0f} [{b.status}]")


agent = max_animals_5_retest

if __name__ == "__main__":
    _self_test()
