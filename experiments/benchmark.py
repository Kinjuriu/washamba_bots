"""
experiments/benchmark.py
=========================

Scientific(ish) benchmark for comparing our baseline agent against
reference agents, BEFORE we make any strategy changes to main.py.

This script does not modify main.py or the agent strategy at all - it
only *runs* episodes and reports statistics.

Agents compared
----------------
1. nikaangukia_meroni_v0  - our agent, imported unmodified from main.py.
2. random                 - the environment's built-in "random" agent,
                             referenced by name exactly as shown in the
                             official Kaggriculture starter notebook
                             (e.g. `env.run([agent, "random"])`).
3. melon_maxxer            - the "Melon Maxxer" reference agent from the
                             official Kaggriculture Getting Started
                             notebook, reproduced here unmodified (its
                             private helper functions are simply renamed
                             with an `mm_` prefix so they don't collide
                             with main.py's own helpers of the same
                             shape).

Reproducibility / seeding
--------------------------
We inspected the installed kaggle_environments package
(kaggle_environments/utils.py::resolve_episode_seed, used by the
kaggriculture interpreter) and confirmed that the environment DOES
support an explicit, supported seed mechanism: passing
`configuration={"seed": N}` to `make()` pins that episode's shared
randomness (weed-spawn rolls and which town shop unlocks next). We did
NOT invent this - it's read directly from the configuration the same
way `kaggle_environments` already documents/uses it internally.

We verified this empirically two ways:
  - Two fully deterministic agents (e.g. nikaangukia_meroni_v0 vs
    melon_maxxer) with the same seed produce bit-identical final
    rewards run after run. Seeding works as intended.
  - The environment's own built-in "random" agent (kaggriculture.py::
    random_agent) creates its own `random.Random()` with NO seed on
    every single call, so its actions - and therefore any matchup
    involving "random" - are NOT reproducible even with a fixed
    episode seed. This is a property of the installed environment
    itself, not a bug in this script, and we are not attempting to
    work around it (that would mean inventing behavior the notebook
    never demonstrated).

Each of the 20 games in a matchup still gets its own fixed, distinct
seed (documented below) so that:
  - matchups between two deterministic agents are fully reproducible,
  - and every matchup still samples 20 different weed/shop conditions
    rather than repeating identical conditions 20 times.
  - Matchups involving "random" will vary a little between runs of this
    script regardless, because of the point above - that's expected.

Crash detection
-----------------
By default (debug=False) the environment does NOT raise an exception
when an agent's action errors out - it marks that turn's status as
"ERROR" internally, substitutes a safe default action, and still lets
the episode run to a "DONE" final status. This means checking only the
*final* step's status is not enough to detect a crash: we scan every
step of every episode for an "ERROR" status on either player and count
that game as failed/crashed rather than including its score in the
averages.

Run with:
    python experiments/benchmark.py
"""

import statistics
import sys
from pathlib import Path

from kaggle_environments import make

# main.py lives in the project root, one directory up from experiments/.
# Add it to sys.path so this script can be run directly as
# `python experiments/benchmark.py` from anywhere.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from main import nikaangukia_meroni  # noqa: E402  (import after sys.path fix)

# CROPS metadata is used by melon_maxxer below, exactly like the
# official notebook uses it - not invented.
from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS  # noqa: E402


# =======================================================================
# Melon Maxxer - reference agent, reproduced unmodified from the official
# Kaggriculture Getting Started notebook. Only the private helper names
# have an "mm_" prefix added, purely to avoid shadowing main.py's own
# step_toward()/find_nearest_target() when both modules are imported
# into the same benchmark process. The logic itself is untouched.
# =======================================================================

MELON_SEED_COST = CROPS["MELON"]["seed"]
MELON_MAX_YIELD_DAY = CROPS["MELON"]["max_yield_day"]
SELL_THRESHOLD = 200


def _mm_step_toward(fx, fy, tx, ty):
    if fx > tx:
        return "WEST"
    if fx < tx:
        return "EAST"
    if fy > ty:
        return "NORTH"
    if fy < ty:
        return "SOUTH"
    return None


def _mm_find_target_tile(farm, board_size, have_seed):
    fx, fy = farm["farmer"]
    candidates = []
    for y in range(board_size):
        for x in range(board_size):
            tile = farm["tiles"][y][x]
            if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile["crop"] == "MELON":
                purpose = None
                # Harvest if ripe.
                age_ok = tile["yield_units"] > 0
                if age_ok and tile.get("planted_day") is not None:
                    purpose = "harvest"
                if not tile["watered_today"]:
                    purpose = "water" if purpose is None else purpose
                if purpose:
                    candidates.append((x, y, purpose))
            elif tile is None and have_seed:
                candidates.append((x, y, "plant"))

    if not candidates:
        return None

    priority = {"harvest": 0, "water": 1, "plant": 2}
    candidates.sort(key=lambda c: (priority[c[2]], abs(c[0] - fx) + abs(c[1] - fy)))
    return candidates[0]


def melon_maxxer(obs):
    farms = obs.get("farms", [])
    player = obs.get("player", 0)
    private = obs.get("private", {}) or {}
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    farm = farms[player]
    board_size = len(farm["tiles"])
    fx, fy = farm["farmer"]
    tile = farm["tiles"][fy][fx]
    day = obs.get("day", 0)

    seeds = private.get("seeds", {})
    shed = private.get("shed", {})
    market_prices = (obs.get("market", {}) or {}).get("prices", {})
    melon_price = market_prices.get("MELON", 0)

    market = []
    # Sell melons only when the market is paying enough.
    melons_in_shed = shed.get("MELON", 0)
    if melons_in_shed > 0 and melon_price >= SELL_THRESHOLD:
        market.append(["SELL", "MELON", melons_in_shed])

    # Top up seed inventory so the next empty tile can be planted.
    if seeds.get("MELON", 0) == 0 and farm["money"] >= MELON_SEED_COST:
        market.append(["BUY_SEED", "MELON", 1])

    # Decide farmer action.
    farmer = ["PASS"]

    if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile["crop"] == "MELON":
        age = day - tile["planted_day"]
        if age >= MELON_MAX_YIELD_DAY and tile["yield_units"] > 0:
            farmer = ["HARVEST"]
        elif not tile["watered_today"]:
            farmer = ["WATER"]
        else:
            target = _mm_find_target_tile(farm, board_size, seeds.get("MELON", 0) > 0)
            if target:
                step = _mm_step_toward(fx, fy, target[0], target[1])
                if step:
                    farmer = [step]
    elif tile is None and seeds.get("MELON", 0) > 0:
        farmer = ["PLANT", "MELON"]
    else:
        target = _mm_find_target_tile(farm, board_size, seeds.get("MELON", 0) > 0)
        if target:
            step = _mm_step_toward(fx, fy, target[0], target[1])
            if step:
                farmer = [step]

    return {"farmer": farmer, "hands": [], "market": market}


# =======================================================================
# Benchmark harness
# =======================================================================

GAMES_PER_MATCHUP = 20


def run_episode(seed, agent_0, agent_1):
    """
    Run a single Kaggriculture episode between agent_0 (player 0) and
    agent_1 (player 1), using a fixed seed for reproducibility.

    Never raises: any problem (starting the env, running it, or an
    agent crashing) is caught and reported in the returned dict instead,
    so one bad game can't take down the whole benchmark run.
    """
    outcome = {
        "seed": seed,
        "crashed": False,
        "reward_0": None,
        "reward_1": None,
    }

    try:
        env = make("kaggriculture", configuration={"seed": seed})
        env.run([agent_0, agent_1])

        # A crash mid-episode doesn't raise (see module docstring) - it
        # shows up as an "ERROR" status on some step. Scan every step of
        # this episode for that, on either player.
        any_error = any(
            step[player].status == "ERROR"
            for step in env.steps
            for player in (0, 1)
        )

        final_step = env.steps[-1]
        outcome["crashed"] = any_error
        outcome["reward_0"] = float(final_step[0].reward or 0.0)
        outcome["reward_1"] = float(final_step[1].reward or 0.0)

    except Exception as exc:
        # The environment itself failed to run this episode at all
        # (as opposed to one agent erroring but the episode continuing).
        outcome["crashed"] = True
        outcome["error"] = f"{type(exc).__name__}: {exc}"

    return outcome


def run_matchup(name_0, agent_0, name_1, agent_1, seed_start, games=GAMES_PER_MATCHUP):
    """
    Run `games` independent episodes for one matchup and return a
    summary dict with per-agent scores and crash/completion counts.

    Seeds are `seed_start, seed_start + 1, ..., seed_start + games - 1`
    so every matchup uses its own distinct, reproducible block of seeds.
    """
    scores_0 = []
    scores_1 = []
    crashed_games = 0

    for offset in range(games):
        seed = seed_start + offset
        result = run_episode(seed, agent_0, agent_1)

        if result["crashed"]:
            crashed_games += 1
            continue  # don't let a crashed game's score pollute the stats

        scores_0.append(result["reward_0"])
        scores_1.append(result["reward_1"])

    return {
        "matchup_name": f"{name_0} vs {name_1}",
        "name_0": name_0,
        "name_1": name_1,
        "games": games,
        "completed_games": len(scores_0),
        "crashed_games": crashed_games,
        "scores_0": scores_0,
        "scores_1": scores_1,
    }


def compute_stats(scores):
    """Return {avg, median, min, max} for a list of scores, or None if empty."""
    if not scores:
        return None
    return {
        "avg": statistics.mean(scores),
        "median": statistics.median(scores),
        "min": min(scores),
        "max": max(scores),
    }


def compute_win_rate(scores_winner, scores_other):
    """
    Fraction of paired games where scores_winner[i] > scores_other[i]
    (ties don't count as a win). Returns None if there are no games to
    compare.
    """
    if not scores_winner:
        return None
    wins = sum(1 for a, b in zip(scores_winner, scores_other) if a > b)
    return wins / len(scores_winner)


# =======================================================================
# Reporting
# =======================================================================

def format_stats_row(agent_name, stats):
    """One row of the results table, or a placeholder if there's no data."""
    if stats is None:
        return f"{agent_name:<25} {'N/A':>8} {'N/A':>9} {'N/A':>8} {'N/A':>8}"
    return (
        f"{agent_name:<25} "
        f"{stats['avg']:>8.1f} "
        f"{stats['median']:>9.1f} "
        f"{stats['min']:>8.1f} "
        f"{stats['max']:>8.1f}"
    )


def print_matchup_report(summary, nikaangukia_name=None):
    """Print the results table and headline stats for one matchup."""
    print(f"MATCHUP: {summary['matchup_name']}")
    print()
    print(f"Games:            {summary['games']}")
    print(f"Completed games:  {summary['completed_games']}")
    print(f"Crashed games:    {summary['crashed_games']}")
    print()

    stats_0 = compute_stats(summary["scores_0"])
    stats_1 = compute_stats(summary["scores_1"])

    header = f"{'Agent':<25} {'Avg':>8} {'Median':>9} {'Min':>8} {'Max':>8}"
    print(header)
    print("-" * len(header))
    print(format_stats_row(summary["name_0"], stats_0))
    print(format_stats_row(summary["name_1"], stats_1))
    print()

    if stats_0 and stats_1:
        score_diff = stats_0["avg"] - stats_1["avg"]
        print(
            f"Average score difference ({summary['name_0']} - {summary['name_1']}): "
            f"{score_diff:.1f}"
        )
    else:
        print("Average score difference: N/A (not enough completed games)")

    # Win rate for nikaangukia_meroni_v0, only when it's actually one of
    # the two agents in this matchup.
    if nikaangukia_name == summary["name_0"]:
        win_rate = compute_win_rate(summary["scores_0"], summary["scores_1"])
    elif nikaangukia_name == summary["name_1"]:
        win_rate = compute_win_rate(summary["scores_1"], summary["scores_0"])
    else:
        win_rate = "N/A (nikaangukia_meroni_v0 is not in this matchup)"

    if isinstance(win_rate, float):
        print(f"Win rate ({nikaangukia_name}): {win_rate:.0%}")
    else:
        print(f"Win rate (nikaangukia_meroni_v0): {win_rate}")

    print()
    print("=" * 60)
    print()


def main():
    matchups = [
        # (name_0, agent_0, name_1, agent_1, seed_start)
        # Distinct seed blocks per matchup so nothing overlaps, while
        # each matchup's own games stay reproducible.
        ("nikaangukia_meroni_v0", nikaangukia_meroni, "random", "random", 1000),
        ("nikaangukia_meroni_v0", nikaangukia_meroni, "melon_maxxer", melon_maxxer, 2000),
        ("melon_maxxer", melon_maxxer, "random", "random", 3000),
    ]

    print(f"Kaggriculture baseline benchmark - {GAMES_PER_MATCHUP} games per matchup")
    print("Seeded via configuration={'seed': N}. Matchups between two deterministic")
    print("agents are fully reproducible; matchups involving the built-in 'random'")
    print("agent are not, since it uses its own unseeded RNG internally (see")
    print("module docstring for details) - that variation is expected.")
    print()
    print("=" * 60)
    print()

    for name_0, agent_0, name_1, agent_1, seed_start in matchups:
        summary = run_matchup(name_0, agent_0, name_1, agent_1, seed_start)
        print_matchup_report(summary, nikaangukia_name="nikaangukia_meroni_v0")


if __name__ == "__main__":
    main()
