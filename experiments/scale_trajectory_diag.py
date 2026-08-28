"""Economic-scale trajectory comparison: main.py vs a route-based opponent.

Captures, once per in-game day (hour==0), for BOTH sides from the public
`obs["farms"]` object (the only channel that reaches both players - the
opponent's private shed/seeds are never visible, per this repo's own
long-established observability rules, so this script does not attempt to
read them for the opponent side):

  - land tiles owned (non-LOCKED tile count)
  - crop tile count (acreage) and animal tile count
  - hand count (crew size)
  - money (cash - the one field that summarises net economic output over
    time for a side we can't see the shed of, since money only moves via
    BUY/SELL/HIRE transactions)

For OUR OWN side only, also captures private["shed"] totals (inventory)
and seeds, since that channel is only ever visible for the calling player.

RESEARCH ONLY. Does not modify main.py, pricing.py, or any opponent file.

    .venv/Scripts/python.exe experiments/scale_trajectory_diag.py <opponent_path> [n_seeds]
"""
import sys
import statistics
from collections import defaultdict

from kaggle_environments import make


def _public_snapshot(farm):
    tiles = farm.get("tiles") or []
    land = 0
    crop_tiles = 0
    animal_tiles = 0
    for row in tiles:
        for tile in row:
            if tile == "LOCKED":
                continue
            land += 1
            if isinstance(tile, dict):
                if tile.get("kind") == "PLANT":
                    crop_tiles += 1
                elif "animal" in tile:
                    animal_tiles += 1
    return {
        "land": land,
        "crop_tiles": crop_tiles,
        "animal_tiles": animal_tiles,
        "hands": len(farm.get("hands") or []),
        "money": farm.get("money", 0),
    }


def collect(agent_path, opponent_path, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([agent_path, opponent_path])

    rows = []
    last_day = -1
    for step in env.steps:
        obs = step[0].observation
        day = obs.get("day", 0)
        hour = obs.get("hour", 0)
        # hour==0 is the instant after hands are cleared overnight, before
        # that morning's HIRE orders land (main.py hires before
        # HIRE_BEFORE_HOUR=4) - sampling there reads 0 hands for BOTH
        # sides regardless of actual crew size. Sample mid-morning instead,
        # once hiring for the day has had a chance to land.
        if day == last_day or hour != 6:
            continue
        last_day = day

        farms = obs.get("farms") or []
        if len(farms) < 2:
            continue
        player = obs.get("player", 0)
        us = _public_snapshot(farms[player])
        opp = _public_snapshot(farms[1 - player])

        private = obs.get("private") or {}
        shed = private.get("shed") or {}
        our_inventory_total = sum(v for v in shed.values() if isinstance(v, (int, float)))

        rows.append({
            "day": day, "us": us, "opp": opp,
            "our_inventory_total": our_inventory_total,
        })

    final_reward = env.steps[-1][0].reward
    return rows, final_reward


def main():
    opponent_path = sys.argv[1]
    n_seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    all_rows = defaultdict(list)  # day -> list of (us, opp, inv) dicts across seeds
    final_rewards = []

    for seed in range(n_seeds):
        print(f"seed {seed}...", file=sys.stderr)
        rows, final_reward = collect("main.py", opponent_path, seed)
        final_rewards.append(final_reward)
        for r in rows:
            all_rows[r["day"]].append(r)

    print(f"\nopponent: {opponent_path}, {n_seeds} seeds")
    print(f"our final reward (mean): {statistics.mean(final_rewards):.0f}\n")

    header = (f"{'day':>3} | {'land':>10} | {'crop_ac':>10} | {'animals':>10} | "
              f"{'hands':>10} | {'money':>12} | {'our_inv':>8}")
    print(header)
    print("-" * len(header))
    for day in sorted(all_rows):
        rows = all_rows[day]
        us_land = statistics.mean(r["us"]["land"] for r in rows)
        opp_land = statistics.mean(r["opp"]["land"] for r in rows)
        us_crop = statistics.mean(r["us"]["crop_tiles"] for r in rows)
        opp_crop = statistics.mean(r["opp"]["crop_tiles"] for r in rows)
        us_animal = statistics.mean(r["us"]["animal_tiles"] for r in rows)
        opp_animal = statistics.mean(r["opp"]["animal_tiles"] for r in rows)
        us_hands = statistics.mean(r["us"]["hands"] for r in rows)
        opp_hands = statistics.mean(r["opp"]["hands"] for r in rows)
        us_money = statistics.mean(r["us"]["money"] for r in rows)
        opp_money = statistics.mean(r["opp"]["money"] for r in rows)
        us_inv = statistics.mean(r["our_inventory_total"] for r in rows)

        print(f"{day:3d} | {us_land:4.0f}/{opp_land:<4.0f} | {us_crop:4.0f}/{opp_crop:<4.0f} | "
              f"{us_animal:4.0f}/{opp_animal:<4.0f} | {us_hands:4.0f}/{opp_hands:<4.0f} | "
              f"{us_money:5.0f}/{opp_money:<5.0f} | {us_inv:8.0f}")


if __name__ == "__main__":
    main()
