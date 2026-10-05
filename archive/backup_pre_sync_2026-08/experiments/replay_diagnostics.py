"""
Replay diagnostics — main.py vs the built-in "starter" agent.

Does NOT modify main.py. Runs one episode, dumps the full replay JSON (for
the official visualizer / manual inspection), and prints:
  1. A day-by-day money trajectory for both players (where does the gap open?)
  2. An action-type histogram per player (what is starter doing differently?)
  3. Farm footprint at the end of the game (tiles planted, quadrants owned)

Usage:
    .venv/Scripts/python.exe experiments/replay_diagnostics.py
"""

import json
from collections import Counter
from pathlib import Path

from kaggle_environments import make

REPLAY_PATH = Path(__file__).parent / "replay_main_vs_starter.json"


def action_types(action_list):
    """Given e.g. ['WATER'] or ['PLANT', 'WHEAT'] or [] return just the verb."""
    if not action_list:
        return "NONE"
    return action_list[0]


def main():
    env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
    env.run(["main.py", "starter"])

    # --- 1. Dump full replay for the official visualizer / manual digging ---
    with open(REPLAY_PATH, "w") as f:
        json.dump(env.toJSON(), f)
    print(f"Full replay written to {REPLAY_PATH} ({REPLAY_PATH.stat().st_size / 1024:.1f} KB)")

    final = env.steps[-1]
    print(f"\nFinal: main.py reward={final[0].reward} status={final[0].status} | "
          f"starter reward={final[1].reward} status={final[1].status}")

    # --- 2. Day-by-day money trajectory ---
    print("\n=== Money by day (sampled at hour 0 of each day) ===")
    header = f"{'DAY':>4} {'P0 money (main.py)':>20} {'P1 money (starter)':>20} {'DELTA (p0-p1)':>15}"
    print(header)
    print("-" * len(header))
    prev_delta = None
    for step in env.steps:
        obs = step[0].observation
        if obs["hour"] != 0:
            continue
        farms = obs["farms"]
        p0, p1 = farms[0]["money"], farms[1]["money"]
        delta = p0 - p1
        trend = ""
        if prev_delta is not None:
            trend = "  (widening vs p1)" if delta < prev_delta - 1 else ("  (closing)" if delta > prev_delta + 1 else "")
        print(f"{obs['day']:4d} {p0:20.1f} {p1:20.1f} {delta:15.1f}{trend}")
        prev_delta = delta

    # --- 3. Action-type histograms ---
    p0_farmer_actions = Counter()
    p1_farmer_actions = Counter()
    p0_market_orders = Counter()
    p1_market_orders = Counter()
    p0_hand_count_turns = 0
    p1_hand_count_turns = 0

    for step in env.steps:
        a0 = step[0].get("action") or {}
        a1 = step[1].get("action") or {}
        p0_farmer_actions[action_types(a0.get("farmer", []))] += 1
        p1_farmer_actions[action_types(a1.get("farmer", []))] += 1
        for order in a0.get("market", []) or []:
            p0_market_orders[action_types(order)] += 1
        for order in a1.get("market", []) or []:
            p1_market_orders[action_types(order)] += 1
        if a0.get("hands"):
            p0_hand_count_turns += 1
        if a1.get("hands"):
            p1_hand_count_turns += 1

    print("\n=== Farmer action histogram (main action each turn, 720 turns total) ===")
    all_actions = sorted(set(p0_farmer_actions) | set(p1_farmer_actions))
    print(f"{'ACTION':<12} {'main.py':>10} {'starter':>10}")
    for a in all_actions:
        print(f"{a:<12} {p0_farmer_actions.get(a, 0):10d} {p1_farmer_actions.get(a, 0):10d}")

    print("\n=== Market order histogram (total orders queued over the episode) ===")
    all_orders = sorted(set(p0_market_orders) | set(p1_market_orders))
    print(f"{'ORDER':<12} {'main.py':>10} {'starter':>10}")
    for a in all_orders:
        print(f"{a:<12} {p0_market_orders.get(a, 0):10d} {p1_market_orders.get(a, 0):10d}")
    print(f"\nTurns with >=1 hand action queued: main.py={p0_hand_count_turns}, starter={p1_hand_count_turns}")

    # --- 4. End-of-game farm footprint ---
    print("\n=== End-of-game farm footprint ===")
    final_obs = final[0].observation
    for i, label in [(0, "main.py"), (1, "starter")]:
        farm = final_obs["farms"][i]
        tiles = farm["tiles"]
        counts = Counter()
        for row in tiles:
            for t in row:
                if t is None:
                    counts["EMPTY"] += 1
                elif t == "LOCKED":
                    counts["LOCKED"] += 1
                elif isinstance(t, dict):
                    if t.get("kind") == "PLANT":
                        counts[f"PLANT:{t.get('crop')}"] += 1
                    else:
                        counts[f"{t.get('kind')}"] += 1
        print(f"\n{label}: money={farm['money']:.1f} quadrants={farm['unlocked_quadrants']} hires_today={farm['hires_today']}")
        for k, v in sorted(counts.items()):
            print(f"    {k:<20} {v}")


if __name__ == "__main__":
    main()
