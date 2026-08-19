"""Generic self-play benchmark for Issue #21 (Track C): agent_path vs itself.

selfplay_bench.py hardcodes "main.py" vs "main.py". This is the same idea
parametrized by an arbitrary agent path/module, so a candidate under
experiments/candidates/ can be self-play tested without touching main.py or
the existing harness.

Reports the same shape as selfplay_bench.py (mean/stdev/min/max of the
per-seed average of both sides, since the two sides of a mirror match are
correlated, not independent) plus per-seed structural checks that matter for
Issue #21: unlocked tile count and animal count at episode end, for both
seats, so a collapse shows up as a structural fact (0 animals, 25 tiles) and
not just a low number.

Usage:
    .venv/Scripts/python.exe experiments/selfplay_agent.py <agent_path> [n_seeds]

<agent_path> is anything kaggle_environments' make()/run() accepts: a .py
file path, or (when this script is imported rather than run standalone) a
callable/module already in memory.
"""
import os
import statistics
import sys

from kaggle_environments import make

ANIMAL_STRUCTURE_KINDS = {"COOP", "PASTURE", "PEN", "BARN"}


def _structural_check(obs):
    farm = obs["farms"][obs["player"]]
    tiles = farm.get("tiles") or []
    unlocked = sum(1 for row in tiles for t in row if t != "LOCKED")
    animals = sum(
        1 for row in tiles for t in row
        if isinstance(t, dict) and t.get("kind") in ANIMAL_STRUCTURE_KINDS and "animal" in t
    )
    hands = len(farm.get("hands") or [])
    return unlocked, animals, hands


def run(agent_path, n_seeds=6):
    scores = []
    rows = []

    for seed in range(n_seeds):
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": seed},
            debug=False,
        )
        env.run([agent_path, agent_path])
        left, right = env.steps[-1]
        scores.append((left.reward + right.reward) / 2)

        tiles0, animals0, hands0 = _structural_check(left.observation)
        tiles1, animals1, hands1 = _structural_check(right.observation)
        rows.append(
            f"  seed {seed}: seat0 {left.reward:>8.0f} [{left.status}] "
            f"tiles={tiles0} animals={animals0} hands={hands0}   "
            f"seat1 {right.reward:>8.0f} [{right.status}] "
            f"tiles={tiles1} animals={animals1} hands={hands1}"
        )

    print(f"self-play: {agent_path}  ({n_seeds} seeds)")
    for row in rows:
        print(row)
    print(f"  mean  {statistics.mean(scores):8.0f}")
    if n_seeds > 1:
        print(f"  stdev {statistics.stdev(scores):8.0f}")
    print(f"  min   {min(scores):8.0f}   max {max(scores):8.0f}")
    return scores


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    agent_path = os.path.abspath(sys.argv[1])
    n_seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    run(agent_path, n_seeds)


if __name__ == "__main__":
    main()
