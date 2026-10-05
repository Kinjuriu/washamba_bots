"""Heterogeneous-opponent evaluation for
experiments/candidates/max_animals_pacing_v0.py.

Same paired-both-seats methodology as
experiments/opponent_state_v0_heterogeneous_eval.py (seat asymmetry with
these route opponents was confirmed large enough to flip conclusions if
not controlled for - see max_animals_cliff_diagnosis.md section 5).
RESEARCH ONLY.

    .venv/Scripts/python.exe experiments/max_animals_pacing_v0_heterogeneous_eval.py [n_seeds] [opponent_name]
"""
import sys
import statistics

from kaggle_environments import make

BASELINE = "main.py"
CANDIDATE = "experiments/candidates/max_animals_pacing_v0.py"
OPPONENTS = {
    "route_moon_md": "/tmp/washamba_opponents/route_moon_md.py",
    "route_moon_tuned": "/tmp/washamba_opponents/route_moon_tuned.py",
    "route_moon_md_r5": "/tmp/washamba_opponents/route_moon_md_r5.py",
    "route_v20": "/tmp/washamba_opponents/route_v20.py",
}


def run_pair(agent_path, opponent_path, seed):
    env_a = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env_a.run([agent_path, opponent_path])
    a_us, _ = env_a.steps[-1]

    env_b = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env_b.run([opponent_path, agent_path])
    _, b_us = env_b.steps[-1]

    return (a_us.reward + b_us.reward) / 2


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    only = sys.argv[2] if len(sys.argv) > 2 else None
    opponents = {only: OPPONENTS[only]} if only else OPPONENTS

    for opp_name, opp_path in opponents.items():
        print(f"=== opponent: {opp_name} ===")
        deltas = []
        for seed in range(n_seeds):
            print(f"  seed {seed}...", file=sys.stderr)
            base_score = run_pair(BASELINE, opp_path, seed)
            cand_score = run_pair(CANDIDATE, opp_path, seed)
            delta = cand_score - base_score
            deltas.append(delta)
            print(f"  seed {seed}: baseline={base_score:9.0f}  candidate={cand_score:9.0f}  delta={delta:+9.0f}")

        print(f"  --- {opp_name} summary ---")
        print(f"  mean delta: {statistics.mean(deltas):+.0f}")
        print(f"  candidate better on {sum(1 for d in deltas if d > 0)}/{n_seeds}")
        if len(deltas) > 1:
            sd = statistics.stdev(deltas)
            se = sd / (n_seeds ** 0.5)
            print(f"  sd of deltas: {sd:.0f}   t = {statistics.mean(deltas)/se:.2f}" if se else "")
        print()


if __name__ == "__main__":
    main()
