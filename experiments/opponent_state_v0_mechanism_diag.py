"""Mechanism-analysis diagnostic for experiments/candidates/opponent_state_v0.py.

Runs the candidate in-process (so CROP_DECISION_LOG/ANIMAL_DECISION_LOG are
inspectable afterward) against a named opponent, and reports which
opponent-state facts actually caused a decision to change, not just
aggregate counts. RESEARCH ONLY.

    .venv/Scripts/python.exe experiments/opponent_state_v0_mechanism_diag.py <opponent_path_or_'main.py'> [n_seeds]
"""
import sys
from collections import Counter

from kaggle_environments import make

import experiments.candidates.opponent_state_v0 as candidate


def run(opponent_path, n_seeds):
    candidate.CROP_DECISION_LOG.clear()
    candidate.ANIMAL_DECISION_LOG.clear()

    for seed in range(n_seeds):
        print(f"seed {seed}...", file=sys.stderr)
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run([candidate.agent, opponent_path])

    crop_log = candidate.CROP_DECISION_LOG
    animal_log = candidate.ANIMAL_DECISION_LOG

    print(f"\nopponent: {opponent_path}")
    print(f"crop decisions changed by opponent state: {len(crop_log)}")
    if crop_log:
        by_day = Counter(r["day"] // 5 * 5 for r in crop_log)
        print(f"  by day-bucket: {dict(sorted(by_day.items()))}")
        pairs = Counter((r["baseline_decision"], r["candidate_decision"]) for r in crop_log)
        print(f"  baseline->candidate crop swaps: {dict(pairs)}")
        print("  sample (up to 5):")
        for r in crop_log[:5]:
            print(f"    day={r['day']:2d} baseline_would_plant={r['baseline_decision']} "
                  f"candidate_plants={r['candidate_decision']} "
                  f"exact_supply={r['exact_opponent_supply']} crude_supply={r['crude_opponent_supply']}")

    print(f"\nanimal decisions changed by opponent state: {len(animal_log)}")
    if animal_log:
        pairs = Counter((r["baseline_pick"], r["candidate_pick"]) for r in animal_log)
        print(f"  baseline->candidate species swaps: {dict(pairs)}")
        for r in animal_log[:5]:
            print(f"    owned={r['owned_counts']} opponent={r['opponent_animal_counts']} "
                  f"baseline_pick={r['baseline_pick']} candidate_pick={r['candidate_pick']}")


if __name__ == "__main__":
    opponent_path = sys.argv[1] if len(sys.argv) > 1 else "main.py"
    n_seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    run(opponent_path, n_seeds)
