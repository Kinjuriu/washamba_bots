"""Quick paired eval: MAX_ANIMALS=4 (main.py) vs MAX_ANIMALS=5
(experiments/candidates/max_animals_5_retest.py), each played against
route_moon_md, same seeds, both seats. RESEARCH ONLY.

    .venv/Scripts/python.exe experiments/max_animals_5_vs_route_moon_eval.py [n_seeds]
"""
import sys
import statistics

from kaggle_environments import make

BASELINE = "main.py"
CANDIDATE = "experiments/candidates/max_animals_5_retest.py"
OPPONENT = "/tmp/washamba_opponents/route_moon_md.py"


def run_pair(agent_path, seed):
    env_a = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env_a.run([agent_path, OPPONENT])
    a_us, _ = env_a.steps[-1]

    env_b = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env_b.run([OPPONENT, agent_path])
    _, b_us = env_b.steps[-1]

    return (a_us.reward + b_us.reward) / 2


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    deltas = []
    for seed in range(n_seeds):
        print(f"seed {seed}...", file=sys.stderr)
        base_score = run_pair(BASELINE, seed)
        cand_score = run_pair(CANDIDATE, seed)
        delta = cand_score - base_score
        deltas.append(delta)
        print(f"seed {seed}: baseline={base_score:9.0f}  MAX_ANIMALS5={cand_score:9.0f}  delta={delta:+9.0f}")

    print(f"\nmean delta: {statistics.mean(deltas):+.0f}")
    print(f"better on: {sum(1 for d in deltas if d > 0)}/{n_seeds}")


if __name__ == "__main__":
    main()
