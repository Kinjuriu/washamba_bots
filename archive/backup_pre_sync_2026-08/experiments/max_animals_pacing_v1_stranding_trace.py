"""
Verifies the specific claim v1 is supposed to satisfy: a BUY_ANIMAL issued
once >1 quadrant is owned (candidate.POST_LAND_PURCHASE_LOG) never ends up
PERMANENTLY UNPLACED at season end.

Wraps the candidate agent to snapshot obs["private"]["shed"] every turn (the
same live-obs-tracing technique used in max_animals_cliff_trace.py, using a
plain closure per env.run() call - NOT a bound method, since
kaggle_environments' Agent.act inspects __code__.co_argcount and a bound
method's self still counts, which crashed an earlier trace attempt this
session).

RESEARCH ONLY. Usage:
    .venv/Scripts/python.exe experiments/max_animals_pacing_v1_stranding_trace.py [n_seeds] [opponent_path_or_name]
"""
import sys

from kaggle_environments import make

import experiments.candidates.max_animals_pacing_v1 as candidate

ACTIVE_ANIMALS = candidate.base.ACTIVE_ANIMALS


def make_agent_fn(log):
    def agent_fn(obs):
        actions = candidate.max_animals_pacing_v1(obs)
        private = obs.get("private") or {}
        shed = private.get("shed") or {}
        unplaced = sum(shed.get(a, 0) for a in ACTIVE_ANIMALS)
        farm = (obs.get("farms") or [None, None])[obs.get("player", 0)] or {}
        unlocked = farm.get("unlocked_quadrants") or ["NW"]
        log.append({
            "day": obs.get("day"), "hour": obs.get("hour"),
            "unplaced_in_shed": unplaced,
            "unlocked_quadrants": list(unlocked),
        })
        return actions
    return agent_fn


def trace_one(opponent_path, seed):
    candidate.DECISION_LOG.clear()
    candidate.POST_LAND_PURCHASE_LOG.clear()
    log = []

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([make_agent_fn(log), opponent_path])

    final_unplaced = log[-1]["unplaced_in_shed"] if log else None
    post_land_purchases = len(candidate.POST_LAND_PURCHASE_LOG)
    max_unplaced_after_extra_land = max(
        (e["unplaced_in_shed"] for e in log if len(e["unlocked_quadrants"]) > 1), default=0
    )
    reward = env.steps[-1][0].reward
    return {
        "seed": seed, "reward": reward,
        "final_unplaced_in_shed": final_unplaced,
        "post_land_purchases_issued": post_land_purchases,
        "max_unplaced_while_extra_land_owned": max_unplaced_after_extra_land,
        "stranded_at_season_end": bool(final_unplaced),
    }


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    opponent = sys.argv[2] if len(sys.argv) > 2 else "starter"

    print(f"=== stranding trace: {n_seeds} seeds vs {opponent} ===")
    any_stranded = False
    for seed in range(n_seeds):
        result = trace_one(opponent, seed)
        any_stranded = any_stranded or result["stranded_at_season_end"]
        print(
            f"  seed {seed}: reward={result['reward']:>9.0f}  "
            f"final_unplaced={result['final_unplaced_in_shed']}  "
            f"post_land_purchases={result['post_land_purchases_issued']}  "
            f"max_unplaced_while_extra_land={result['max_unplaced_while_extra_land_owned']}  "
            f"STRANDED={result['stranded_at_season_end']}"
        )
    print()
    print(f"ANY STRANDED AT SEASON END ACROSS {n_seeds} SEEDS: {any_stranded}")


if __name__ == "__main__":
    main()
