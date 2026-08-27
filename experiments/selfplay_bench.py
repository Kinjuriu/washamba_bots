"""Self-play benchmark: both sides run main.py.

Why this exists alongside seeded_batch.py: the three built-in opponents
(`pass`, `random`, `starter`) never sell anything. They leave every market
at its pristine starting inventory, so our own sales never compete with a
rival's and prices stay high all season. That flatters us badly - the
built-in numbers are roughly 1.5x what the same agent scores against a
real competitor.

Self-play is the cheapest honest proxy we have: a second copy of us is
farming the same crops and dumping them into the same order book. The
`end price` line is the point of the whole script - watch MELON, which
collapses toward the $1 floor once both sides are selling it. Any strategy
that looks good only because nobody else is trading will show up here.

Usage:
    .venv/Scripts/python.exe experiments/selfplay_bench.py [n_seeds]

Runs 6 seeds by default (~90s). Every seed is fixed, so this is directly
comparable across changes.

One statistical note: each episode produces two banks, but they are the same
agent playing itself and are near-perfectly correlated - often identical to
the rupee. Treating them as two samples would halve the apparent stdev, so
each seed contributes ONE observation (the mean of the pair) and n is the
seed count. Figures recorded before 2026-08-16 pooled both sides and so quote
an optimistic stdev; their means are unaffected.
"""

import statistics
import sys
from collections import Counter
from pathlib import Path

from kaggle_environments import make

# Make `from experiments.seeds import ...` work when this script is run
# directly (`python experiments/selfplay_bench.py ...`). Without this, the
# experiments/ directory is not on sys.path and the import below fails with
# `ModuleNotFoundError: No module named 'experiments'`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments.seeds import DEV_SEEDS, HOLDOUT_SEEDS

# Default seed set for development iteration. Use ``--seed-set holdout`` to
# run against the held-out set after a change is frozen; see experiments/seeds.py.
SEED_SETS = {"dev": DEV_SEEDS, "holdout": HOLDOUT_SEEDS}

# Products worth watching a price on - the plantable crops. Animal goods
# and FERTILIZER are reported in the sold mix instead.
TRACKED_CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    seed_set = "dev"
    if "--seed-set" in sys.argv:
        seed_set = sys.argv[sys.argv.index("--seed-set") + 1]
    if seed_set not in SEED_SETS:
        print(
            f"error: unknown seed set '{seed_set}'. Use one of {list(SEED_SETS)}.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    seeds = list(SEED_SETS[seed_set])
    # Allow an explicit seed count to trim the selected set (e.g. ``--seed-set
    # holdout 6`` for a quick partial run), but never to extend it.
    n_seeds = min(n_seeds, len(seeds))
    seeds = seeds[:n_seeds]

    scores = []
    price_totals = Counter()
    sold = Counter()

    for seed in seeds:
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": seed},
            debug=False,
        )
        env.run(["main.py", "main.py"])
        left, right = env.steps[-1]

        # Both sides are us. Their banks are NOT two independent samples -
        # in a mirror match they are near-perfectly correlated, and on most
        # seeds they come out byte-identical. Pooling them would halve the
        # apparent stdev and overstate our precision, so average the pair
        # into a single per-seed observation and report n = seeds.
        scores.append((left.reward + right.reward) / 2)

        # Sell orders are only read off player 0 - player 1 runs identical
        # code, so this is a representative mix rather than a farm total.
        for step in env.steps:
            orders = (step[0].get("action") or {}).get("market") or []
            for order in orders:
                if order and order[0] == "SELL":
                    sold[order[1]] += order[2] if len(order) > 2 else 1

        for product, price in left.observation["market"]["prices"].items():
            price_totals[product] += price

    print(f"self-play over {n_seeds} seeds (set={seed_set}, mean of both sides per seed)")
    print(f"  mean  {statistics.mean(scores):8.0f}")
    print(f"  stdev {statistics.stdev(scores):8.0f}")
    print(f"  min   {min(scores):8.0f}   max {max(scores):8.0f}")
    print(
        "  mean end price:",
        {
            product: round(total / n_seeds)
            for product, total in price_totals.items()
            if product in TRACKED_CROPS
        },
    )
    print("  sold mix (p0):", dict(sold.most_common(6)))


if __name__ == "__main__":
    main()
