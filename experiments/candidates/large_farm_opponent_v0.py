"""
Issue #21, Track C, Experiment 0: isolate the effect of animal count alone.

experiments/bigfarm_opponent.py already reaches 75 tiles / 15-crew-cap / day-10
selling and is a straight import of main.py with tuning constants overridden -
see its own docstring and CLAUDE.md's "Do not blame market depth" precedent for
why that pattern (import + override, not rewrite) is the trusted one here. It
caps MAX_ANIMALS at 4 because 5 was measured to collapse the OPPONENT's own
bank to $356 against `main.py` (a farm that does not compete for the same
animal feed / cash).

This file changes exactly one thing versus bigfarm_opponent.py: MAX_ANIMALS
4 -> 8, to reach the replay-observed 8-9 animal count. Nothing else moves -
not MAX_HANDS_PER_DAY, not any cash-reserve logic, not land timing. The
purpose is diagnostic: does animal count ALONE reproduce the collapse the
user's brief describes ($589-$4,604 self-play bank), or does the collapse
need land+crew scaling too? That answer decides which of the four suspected
mechanisms (Fibonacci hire cost, day-11 land+crew poverty trap, flat
MIN_MONEY_TO_HIRE, self-play seller competition) to fix first.

Not intended to be economically credible on its own - see
docs/candidate_reports/track_c_large_farm.md for the full experiment log.
"""
import os
import sys


def _find_repo_root():
    """Robust to kaggle_environments' agent loader sometimes exec'ing this
    file into a namespace with no `__file__` at all (observed: identical
    code path, same process, intermittently missing __file__ depending on
    load order - see docs/candidate_reports/track_c_large_farm.md's
    "tooling bug" entry). Falls back to cwd, then walks up from cwd,
    rather than trusting a fixed number of dirname() hops either way -
    a wrong hop count silently breaks `import experiments.x` with
    ModuleNotFoundError only some of the time, which is worse than always.
    """
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

import experiments.bigfarm_opponent as base_opponent  # noqa: E402
import main as base  # noqa: E402

MAX_ANIMALS = 8
base.MAX_ANIMALS = MAX_ANIMALS


def large_farm_opponent_v0(obs):
    return base_opponent.bigfarm_opponent(obs)


def _self_test(seeds=(0, 1, 2)):
    from kaggle_environments import make

    for seed in seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([large_farm_opponent_v0, large_farm_opponent_v0])
        a, b = env.steps[-1][0], env.steps[-1][1]
        obs = env.steps[-1][0].observation
        farm = obs["farms"][0]
        tiles = sum(1 for row in farm["tiles"] for t in row if t != "LOCKED")
        print(
            f"seed {seed}: seat0 {a.reward:>8.0f} [{a.status}]   "
            f"seat1 {b.reward:>8.0f} [{b.status}]   tiles {tiles}"
        )


agent = large_farm_opponent_v0

if __name__ == "__main__":
    _self_test()
