"""
Shared seed sets used across all experiment harnesses.

DEV_SEEDS  — used during local iteration / development. Every experiment
           tool (seeded_batch.py, paired_compare.py, head_to_head.py,
           selfplay_bench.py) references this as its default ``range(N)``.
HOLDOUT_SEEDS — never used during development iteration. Only touched once
               per candidate bundle, after a change is frozen, to confirm
               that the measured gain survives a held-out seed set.
               Using this set pre-submission converts "positive everywhere,
               convincing nowhere" into a decidable question.

For seeding: always import ``from experiments.seeds import DEV_SEEDS`` (or
``HOLDOUT_SEEDS``) rather than writing ``range(12)`` inline. The whole
point of this module is that there is exactly one source of truth for which
seeds count as "development" and which are held out.
"""

# Development seeds — every experiment tool defaults to this. The 12 seeds
# (0–11) are the ones most of our headroom numbers are measured against.
DEV_SEEDS = range(12)

# Held-out seeds — only touched after a change is frozen. 12 seeds that
# were never used during any local iteration; any claimed gain should be
# verified against these, or the change is not shipped.
#
# We deliberately pick a gap from the dev range so a mischievous edit
# that just writes ``range(12)`` in the held-out script is immediately
# visible as a diff.
HOLDOUT_SEEDS = range(100, 112)  # 100–111 inclusive