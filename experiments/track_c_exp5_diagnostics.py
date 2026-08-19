"""
Issue #21, Track C, Experiment 5 diagnostics: paced animal ramp.

Runs self-play (agent vs itself) for the given agent path and extracts, per
seed, everything the experiment brief asked to be recorded: bank, animal
count trajectory, land trajectory, crew trajectory, cash trajectory,
BUY_ANIMAL order days, whether animals survive the season, whether any
pasture is ever built-but-never-filled (stranded), and the sell mix.

Reads env.steps AFTER the episode (not print() from inside the agent -
kaggle_environments does not reliably surface agent stdout, confirmed the
hard way in the previous session), so this works identically whether
debug=True or False.

Usage:
    .venv/Scripts/python.exe experiments/track_c_exp5_diagnostics.py <agent_path> [n_seeds]
"""
import sys
from collections import Counter

from kaggle_environments import make

ANIMAL_STRUCTURE_KINDS = {"COOP", "PASTURE", "PEN", "BARN"}


def _farm_snapshot(obs):
    farm = obs["farms"][obs["player"]]
    tiles = farm.get("tiles") or []
    unlocked_tiles = 0
    filled_animals = 0
    unfilled_structures = 0
    for row in tiles:
        for t in row:
            if t == "LOCKED":
                continue
            unlocked_tiles += 1
            if isinstance(t, dict) and t.get("kind") in ANIMAL_STRUCTURE_KINDS:
                if "animal" in t:
                    filled_animals += 1
                else:
                    unfilled_structures += 1
    private = obs.get("private") or {}
    shed = private.get("shed", {})
    return {
        "money": farm.get("money", 0),
        "tiles": unlocked_tiles,
        "quadrants": len(farm.get("unlocked_quadrants") or ["NW"]),
        "hands": len(farm.get("hands") or []),
        "animals_filled": filled_animals,
        "animals_unfilled_structures": unfilled_structures,
        "wheat_shed": shed.get("WHEAT", 0),
    }


def run(agent_path, n_seeds=6):
    all_finals = []
    worst = None

    for seed in range(n_seeds):
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": seed},
            debug=False,
        )
        env.run([agent_path, agent_path])

        buy_animal_days = []
        sell_counts = Counter()
        max_unfilled_streak = 0
        current_unfilled_streak = 0
        daily_rows = []
        seen_days = set()

        for step in env.steps:
            p0 = step[0]
            obs = p0.get("observation") or {}
            day = obs.get("day")
            hour = obs.get("hour")
            action = p0.get("action") or {}

            for order_list in [action.get("market") or []]:
                for order in order_list:
                    if not order:
                        continue
                    if order[0] == "BUY_ANIMAL":
                        buy_animal_days.append(day)
                    if order[0] == "SELL" and len(order) > 1:
                        sell_counts[order[1]] += order[2] if len(order) > 2 else 1

            if day is not None and hour == 0 and day not in seen_days and obs.get("farms"):
                seen_days.add(day)
                snap = _farm_snapshot(obs)
                daily_rows.append((day, snap))
                if snap["animals_unfilled_structures"] > 0:
                    current_unfilled_streak += 1
                    max_unfilled_streak = max(max_unfilled_streak, current_unfilled_streak)
                else:
                    current_unfilled_streak = 0

        left, right = env.steps[-1]
        final_bank = (left.reward, right.reward)
        final_status = (left.status, right.status)
        final_snap = _farm_snapshot(left.observation)

        mean_final = (
            (final_bank[0] + final_bank[1]) / 2
            if final_bank[0] is not None and final_bank[1] is not None
            else None
        )
        all_finals.append(mean_final)

        print(f"=== seed {seed} ===")
        print(f"  final bank: seat0={final_bank[0]} [{final_status[0]}]  seat1={final_bank[1]} [{final_status[1]}]")
        print(f"  BUY_ANIMAL order days (seat0): {buy_animal_days}")
        print(f"  max consecutive days with a stranded (unfilled) structure: {max_unfilled_streak}")
        print(f"  final state: tiles={final_snap['tiles']} quadrants={final_snap['quadrants']} "
              f"hands={final_snap['hands']} animals_filled={final_snap['animals_filled']} "
              f"animals_unfilled={final_snap['animals_unfilled_structures']} wheat_shed={final_snap['wheat_shed']}")
        print(f"  sell mix (seat0, top 6): {dict(sell_counts.most_common(6))}")
        print("  trajectory (day: money/tiles/quadrants/hands/animals_filled/animals_unfilled/wheat):")
        for day, snap in daily_rows:
            print(
                f"    day {day:2d}: money={snap['money']:>8.0f}  tiles={snap['tiles']:2d}  "
                f"quadrants={snap['quadrants']}  hands={snap['hands']:2d}  "
                f"animals={snap['animals_filled']}  unfilled={snap['animals_unfilled_structures']}  "
                f"wheat={snap['wheat_shed']}"
            )

        if worst is None or (mean_final is not None and mean_final < worst[1]):
            worst = (seed, mean_final)

    valid = [f for f in all_finals if f is not None]
    print("\n=== summary ===")
    print(f"  seeds: {n_seeds}   valid: {len(valid)}")
    if valid:
        print(f"  mean: {sum(valid) / len(valid):.0f}")
        print(f"  min:  {min(valid):.0f}   max: {max(valid):.0f}")
    if worst:
        print(f"  worst seed: {worst[0]} ({worst[1]})")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    agent_path = sys.argv[1]
    n_seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    run(agent_path, n_seeds)


if __name__ == "__main__":
    main()
