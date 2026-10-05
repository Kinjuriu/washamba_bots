"""Play two agent files directly against each other, seats swapped.

This is the strictest evaluation we have, and the only one that can see a
market-timing change at all.

`paired_compare.py` pits each version against a built-in opponent. That is
right for anything about farm upkeep, but the built-ins never sell, so the
market stays pristine and any change to *when and how much we sell* looks
free. Put two copies of the agent in the same episode and the order book is
suddenly contested - which is what the ladder actually is.

Seats are not symmetric. Measured with identical code on both sides, seat 0
finishes a few hundred behind seat 1, so every config here plays each seed
from both seats and the two are averaged. Skipping that swap is enough to
invent a result out of nothing.

Read `wins` first: how many of the 2N matches this variant won.

Usage:
    .venv/Scripts/python.exe experiments/head_to_head.py variant.py main.py [seeds]

Always sanity-check a sweep by including the baseline against itself. It
should come out near zero; if it doesn't, the harness is lying to you.
"""

import sys

from kaggle_environments import make


def play(agent_a, agent_b, seed):
    """One episode. Returns (bank of agent_a, bank of agent_b)."""
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([agent_a, agent_b])
    left, right = env.steps[-1]
    return left.reward, right.reward


def compare(variant_path, baseline_path, n_seeds):
    diffs = []
    wins = 0

    for seed in range(n_seeds):
        # Seat 0, then seat 1, so the seat advantage cancels instead of
        # being attributed to the variant.
        variant_first, baseline_second = play(variant_path, baseline_path, seed)
        baseline_first, variant_second = play(baseline_path, variant_path, seed)

        for variant_bank, baseline_bank in (
            (variant_first, baseline_second),
            (variant_second, baseline_first),
        ):
            diffs.append(variant_bank - baseline_bank)
            wins += variant_bank > baseline_bank

    return diffs, wins


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)

    variant_path, baseline_path = sys.argv[1], sys.argv[2]
    n_seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    diffs, wins = compare(variant_path, baseline_path, n_seeds)
    matches = len(diffs)
    mean_diff = sum(diffs) / matches

    print(f"{variant_path}  vs  {baseline_path}")
    print(f"  {n_seeds} seeds x 2 seats = {matches} matches")
    print(f"  mean bank difference  {mean_diff:+9.0f}")
    print(f"  variant won           {wins}/{matches}")


if __name__ == "__main__":
    main()
