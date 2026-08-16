"""
Self-play benchmark: both sides run main.py.

Why this and not experiments/seeded_batch.py: the built-in opponents
(`pass`, `random`, `starter`) sell nothing. They leave every market at its
starting inventory, so our produce always clears at a high price and the
scores look enormous. That is exactly how a 33,000 local score converged to
289 on the real ladder.

Self-play is the cheapest honest proxy for a real opponent competing for the
same market. Treat the mean here as the number that predicts ladder movement,
and treat seeded_batch.py as a regression check rather than a measure of
strength.

Usage:
    .venv/Scripts/python.exe experiments/selfplay_bench.py [seeds]
"""

import statistics
import sys
from collections import Counter

from kaggle_environments import make

TRACKED = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")


def main(seed_count):
    scores = []
    end_prices = Counter()
    sold = Counter()

    for seed in range(seed_count):
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": seed},
            debug=False,
        )
        env.run(["main.py", "main.py"])

        first, second = env.steps[-1]
        scores += [first.reward, second.reward]

        for step in env.steps:
            for order in (step[0].get("action") or {}).get("market") or []:
                if order and order[0] == "SELL":
                    sold[order[1]] += order[2] if len(order) > 2 else 1

        for product, price in first.observation["market"]["prices"].items():
            end_prices[product] += price

    print(f"self-play over {seed_count} seeds ({len(scores)} agent-results)")
    print(f"  mean  {statistics.mean(scores):8.0f}")
    print(f"  stdev {statistics.stdev(scores):8.0f}" if len(scores) > 1 else "")
    print(f"  min   {min(scores):8.0f}   max {max(scores):8.0f}")

    print("  mean end price:",
          {p: round(v / seed_count) for p, v in end_prices.items() if p in TRACKED})
    print("  sold mix (p0):", dict(sold.most_common(6)))

    # A price far below base means we flooded that market ourselves; a price
    # well above base means we left money on the table by ignoring it.
    print("\n  (base prices: WHEAT 25, CARROT 35, TOMATO 60, "
          "STRAWBERRY 120, MELON 250)")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 6)
