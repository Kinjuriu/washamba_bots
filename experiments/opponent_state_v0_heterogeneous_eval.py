"""Heterogeneous-opponent evaluation for
experiments/candidates/opponent_state_v0.py.

Per the task's own new evaluation principle: local self-play is a
regression/sanity check only, NOT the primary signal. This script measures
what the task actually asked for - baseline (main.py) vs candidate
(opponent_state_v0.py), each played against a FIXED, genuinely different
third-party opponent, same seeds, both seats, so seat asymmetry and seed
luck are controlled the same way paired_compare.py already controls them
against pass/starter. paired_compare.py itself restricts opponents to
pass/starter (random's own RNG isn't seed-controlled) - Peter's route_moon_*/
route_v20 agents are deterministic per seed (no RNG anywhere in any of the
four architecture reads that produced docs/architecture_comparison.md), so
they are legitimately pairable; this script exists because paired_compare.py
doesn't expose that option, not because the restriction doesn't apply.

RESEARCH ONLY. Does not modify main.py, pricing.py, or any opponent file -
opponent files are read from a scratch extraction, never the tracked repo.

    .venv/Scripts/python.exe experiments/opponent_state_v0_heterogeneous_eval.py [n_seeds]
"""
import sys
import statistics

from kaggle_environments import make

BASELINE = "main.py"
CANDIDATE = "experiments/candidates/opponent_state_v0.py"
OPPONENTS = {
    "route_moon_md": "/tmp/washamba_opponents/route_moon_md.py",
    "route_moon_tuned": "/tmp/washamba_opponents/route_moon_tuned.py",
    "route_moon_md_r5": "/tmp/washamba_opponents/route_moon_md_r5.py",
    "route_v20": "/tmp/washamba_opponents/route_v20.py",
}


def run_pair(agent_path, opponent_path, seed):
    """One seed, both seats, so seat asymmetry cancels the same way
    head_to_head.py/paired_compare.py already do it."""
    env_a = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env_a.run([agent_path, opponent_path])
    a_us_seat0, a_opp_seat1 = env_a.steps[-1]

    env_b = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env_b.run([opponent_path, agent_path])
    b_opp_seat0, b_us_seat1 = env_b.steps[-1]

    return {
        "seat0_us": a_us_seat0.reward, "seat0_opp": a_opp_seat1.reward,
        "seat1_opp": b_opp_seat0.reward, "seat1_us": b_us_seat1.reward,
        "seat0_status": a_us_seat0.status, "seat1_status": b_us_seat1.status,
    }


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    only = sys.argv[2] if len(sys.argv) > 2 else None
    opponents = {only: OPPONENTS[only]} if only else OPPONENTS
    print(f"n_seeds={n_seeds}\n")

    for opp_name, opp_path in opponents.items():
        print(f"=== opponent: {opp_name} ===")
        baseline_scores = []
        candidate_scores = []
        deltas = []
        wins_baseline = 0
        wins_candidate = 0

        for seed in range(n_seeds):
            print(f"  seed {seed}: baseline...", file=sys.stderr)
            base_result = run_pair(BASELINE, opp_path, seed)
            print(f"  seed {seed}: candidate...", file=sys.stderr)
            cand_result = run_pair(CANDIDATE, opp_path, seed)

            base_mean = (base_result["seat0_us"] + base_result["seat1_us"]) / 2
            cand_mean = (cand_result["seat0_us"] + cand_result["seat1_us"]) / 2
            baseline_scores.append(base_mean)
            candidate_scores.append(cand_mean)
            deltas.append(cand_mean - base_mean)
            if cand_mean > base_mean:
                wins_candidate += 1
            elif base_mean > cand_mean:
                wins_baseline += 1

            print(f"  seed {seed}: baseline_mean={base_mean:9.0f}  candidate_mean={cand_mean:9.0f}  "
                  f"delta={cand_mean - base_mean:+9.0f}  "
                  f"[base statuses {base_result['seat0_status']}/{base_result['seat1_status']}, "
                  f"cand statuses {cand_result['seat0_status']}/{cand_result['seat1_status']}]")

        mean_delta = statistics.mean(deltas)
        print(f"  --- {opp_name} summary ---")
        print(f"  baseline mean:  {statistics.mean(baseline_scores):9.0f}")
        print(f"  candidate mean: {statistics.mean(candidate_scores):9.0f}")
        print(f"  mean delta:     {mean_delta:+9.0f}")
        print(f"  candidate better on {wins_candidate}/{n_seeds} seeds, baseline better on {wins_baseline}/{n_seeds}")
        print()


if __name__ == "__main__":
    main()
