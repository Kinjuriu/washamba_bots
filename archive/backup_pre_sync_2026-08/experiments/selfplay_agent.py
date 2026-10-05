"""Generic self-play benchmark: agent_path vs itself.

selfplay_bench.py hardcodes "main.py" vs "main.py". This is the same idea
parametrized by an arbitrary agent path, so a candidate under
experiments/candidates/ can be self-play tested without touching main.py or
the existing harness.

Usage:
    .venv/Scripts/python.exe experiments/selfplay_agent.py <agent_path> [n_seeds]
"""
import statistics
import sys
import os

from kaggle_environments import make


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
        rows.append(
            f"  seed {seed}: seat0 {left.reward:>8.0f} [{left.status}]   "
            f"seat1 {right.reward:>8.0f} [{right.status}]"
        )

    print(f"self-play: {agent_path}  ({n_seeds} seeds)")
    for row in rows:
        print(row)
    print(f"  mean   {statistics.mean(scores):8.0f}")
    if n_seeds > 1:
        print(f"  stdev  {statistics.stdev(scores):8.0f}")
        print(f"  median {statistics.median(scores):8.0f}")
    print(f"  min    {min(scores):8.0f}   max {max(scores):8.0f}")
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
