"""Self-play benchmark for the forward-pricing crop-selection/selling experiment.

Same self-play methodology as experiments/selfplay_bench.py (main.py vs
main.py - the number that predicts the ladder, per CONTRIBUTING.md), but
also reports median, and is run twice against two different commits of
main.py (V1 baseline, then the forward-pricing treatment) with the exact
same seed set, per docs/EXPERIMENT_WORKFLOW.md's COMPARE AGAINST CONTROL
step. Run it once before the change and once after; this script does not
diff commits itself.

Usage:
    .venv/bin/python experiments/forward_pricing_experiment.py [n_seeds]

Runs 6 seeds by default (12 agent-results, ~90s), matching
experiments/selfplay_bench.py's default so the two are directly
comparable.
"""

import statistics
import sys

from kaggle_environments import make

SEEDS = range(int(sys.argv[1]) if len(sys.argv) > 1 else 6)


def main():
    scores = []
    for seed in SEEDS:
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": seed},
            debug=False,
        )
        env.run(["main.py", "main.py"])
        left, right = env.steps[-1]
        scores += [left.reward, right.reward]

    print(f"self-play over {len(list(SEEDS))} seeds ({len(scores)} agent-results)")
    print(f"  mean   {statistics.mean(scores):8.1f}")
    print(f"  median {statistics.median(scores):8.1f}")
    print(f"  stdev  {statistics.stdev(scores):8.1f}")
    print(f"  min    {min(scores):8.1f}")
    print(f"  max    {max(scores):8.1f}")
    print(f"  raw    {scores}")


if __name__ == "__main__":
    main()
