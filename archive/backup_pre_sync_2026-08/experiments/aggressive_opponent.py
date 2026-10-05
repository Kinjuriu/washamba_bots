"""
Aggressive opponent — a stress-test twin of main.py, for diagnosing whether
real market competition (not the placid `pass`/`random`/`starter` built-ins,
and not the mirror-symmetric case of self-play) can push our own agent into
the "farm goes idle before day 30" pattern reported from live ladder replays.

Why the existing local opponents can't answer this: `pass`/`random`/`starter`
barely touch the market, and self-play is symmetric — both sides make the
exact same forward-looking mistakes in `choose_crop`'s self-supply discount,
so it can't reveal what happens when an *asymmetric*, undercutting competitor
targets the same crops we do. This script builds that competitor by reusing
every function in main.py unchanged (same unit-action ladder, same crop
scoring) and monkey-patching only the tuning constants that control how
*aggressively* it plays:

  - Sells the instant something is harvestable, at any price, uncapped per
    turn - no "wait for a good price" discipline, no premium-good sell cap.
  - Hires a much larger crew, much faster, off a tighter per-hand tile ratio.
  - Keeps a bigger seed stockpile so it never waits on the 1-seed-per-turn
    drip before replanting.

This does NOT modify main.py - it patches its own separate import of the
module (kaggle_environments loads "main.py" as an isolated exec() namespace
per episode, so this process's `import main` is a distinct object with no
shared state; see get_last_callable in kaggle_environments/agent.py).

Usage:
    .venv/Scripts/python.exe experiments/aggressive_opponent.py
"""

import sys
from collections import defaultdict
from pathlib import Path

from kaggle_environments import make

# main.py lives at the project root, one level up from experiments/.
sys.path.insert(0, str(Path(__file__).parent.parent))

import main as base  # noqa: E402  (import after sys.path fix)

base.SELL_PRICE_THRESHOLDS = {crop: 1 for crop in base.SELL_PRICE_THRESHOLDS}
base.DEFAULT_SELL_THRESHOLD = 1
base.MAX_SELL_PER_TURN = {}
base.SHED_FORCE_SELL_THRESHOLD = 1
base.LIQUIDATION_START_DAY = 0

base.MAX_HANDS_PER_DAY = 15
base.WORK_TILES_PER_HAND = 2
base.MAX_HIRES_PER_TURN = 5
base.MIN_MONEY_TO_HIRE = 20

base.MAX_SEED_STOCKPILE = 8


def aggressive_maxxer(obs):
    return base.nikaangukia_meroni(obs)


def _pass_rate_by_quartile(steps, player_idx):
    quartile_pass = defaultdict(lambda: [0, 0])
    for step in steps:
        obs = step[player_idx].observation
        q = min(3, obs["day"] // 8)
        action = step[player_idx].get("action") or {}
        units = [action.get("farmer") or []] + list(action.get("hands") or [])
        for u in units:
            quartile_pass[q][1] += 1
            if not u or u[0] == "PASS":
                quartile_pass[q][0] += 1
    return quartile_pass


def main():
    for seed in [0, 1, 2]:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=True)
        env.run(["main.py", aggressive_maxxer])
        f0, f1 = env.steps[-1][0], env.steps[-1][1]

        q0 = _pass_rate_by_quartile(env.steps, 0)
        rates = " ".join(f"Q{q}={q0[q][0]}/{q0[q][1]}" for q in range(4))

        final_obs = env.steps[-1][0].observation
        farm0 = final_obs["farms"][0]
        empty = sum(1 for row in farm0["tiles"] for t in row if t is None)
        plant = sum(1 for row in farm0["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PLANT")

        print(
            f"seed={seed}: main.py={f0.reward:.1f} status={f0.status} | "
            f"aggressive={f1.reward:.1f} status={f1.status}  "
            f"main.py PASS-rate {rates}  EMPTY={empty} PLANT={plant} hands_now={len(farm0.get('hands') or [])}"
        )


if __name__ == "__main__":
    main()
