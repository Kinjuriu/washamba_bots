"""Behavioral diagnostic for the sell-threshold audit: per-product SELL
actions (count, total units, total revenue, mean realized price), shed
inventory sampled over the season, and cash at key checkpoints, for a
baseline agent and one candidate, on the same seeds. RESEARCH ONLY - does
not modify main.py or pricing.py.

Runs each agent (as file paths, subprocess-free/in-process via
kaggle_environments) against itself is NOT what we want here - we want to
compare baseline's own trajectory to the candidate's own trajectory, each
in self-play, seed by seed, so both play against a symmetric opponent
(rules out "the opponent happened to do something different" as a
confound - both agents only differ in their OWN thresholds).

    .venv/Scripts/python.exe experiments/sell_threshold_behavior_diag.py <candidate_path> [n_seeds]
"""
import sys
import importlib.util
import statistics
from collections import defaultdict

from kaggle_environments import make

FOCUS_PRODUCTS = ["MELON", "STRAWBERRY", "WOOL", "WHEAT", "CARROT"]


def _load_agent(path):
    spec = importlib.util.spec_from_file_location("candidate_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.agent


def _run_and_collect(agent_callable, seed):
    """Runs agent_callable vs itself on `seed`, returns per-turn shed
    quantities (player 0's private.shed) and final reward, plus a
    reconstructed sell log built by diffing consecutive money/shed
    states (the action list itself isn't in the observation - see
    experiments/opponent_supply_forecast_audit.md's observability
    section - so this reconstructs sells from state deltas instead)."""
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([agent_callable, agent_callable])

    shed_series = []  # (day, {product: qty})
    money_series = []  # (day, money)
    price_series = []  # (day, {product: price})
    prev_shed = None
    sells = defaultdict(lambda: {"count": 0, "units": 0})

    for step in env.steps:
        obs = step[0].observation
        day = obs.get("day", 0)
        private = obs.get("private") or {}
        shed = dict(private.get("shed") or {})
        farm = (obs.get("farms") or [{}])[obs.get("player", 0)] or {}
        money = farm.get("money", 0)
        prices = dict((obs.get("market") or {}).get("prices") or {})

        shed_series.append((day, shed))
        money_series.append((day, money))
        price_series.append((day, prices))

        if prev_shed is not None:
            for product in FOCUS_PRODUCTS:
                before = prev_shed.get(product, 0)
                after = shed.get(product, 0)
                # A drop in held quantity that isn't explained by a
                # harvest landing (harvest only adds) is consistent with
                # a sale; this under-counts sells that happen the same
                # turn a harvest also lands (both move shed the same
                # direction net), so treat as a lower bound, not exact -
                # good enough for a relative baseline-vs-candidate
                # comparison on identical seeds/opponents.
                if after < before:
                    sells[product]["count"] += 1
                    sells[product]["units"] += (before - after)
        prev_shed = shed

    final_reward = env.steps[-1][0].reward
    return {
        "final_reward": final_reward,
        "shed_series": shed_series,
        "money_series": money_series,
        "price_series": price_series,
        "sells": dict(sells),
    }


def summarize(label, results):
    rewards = [r["final_reward"] for r in results]
    print(f"\n=== {label} ===")
    print(f"  final reward: mean={statistics.mean(rewards):.0f} "
          f"stdev={statistics.stdev(rewards) if len(rewards) > 1 else 0:.0f} "
          f"min={min(rewards):.0f} max={max(rewards):.0f}")

    for product in FOCUS_PRODUCTS:
        counts = [r["sells"].get(product, {}).get("count", 0) for r in results]
        units = [r["sells"].get(product, {}).get("units", 0) for r in results]
        print(f"  {product:<10} sell-events(mean)={statistics.mean(counts):5.1f}  "
              f"units-moved(mean)={statistics.mean(units):6.1f}")

    # cash at day ~5, ~10, ~19 (liquidation start), ~29 (season end)
    for checkpoint_day in (5, 10, 19, 29):
        vals = []
        for r in results:
            candidates_at_day = [m for d, m in r["money_series"] if d == checkpoint_day]
            if candidates_at_day:
                vals.append(candidates_at_day[0])
        if vals:
            print(f"  cash @ day {checkpoint_day:2d}: mean={statistics.mean(vals):8.0f}")

    # average shed quantity held pre-liquidation (day<19) per product
    for product in FOCUS_PRODUCTS:
        vals = []
        for r in results:
            pre = [shed.get(product, 0) for d, shed in r["shed_series"] if d < 19]
            if pre:
                vals.append(statistics.mean(pre))
        if vals:
            print(f"  {product:<10} avg pre-liq shed qty: {statistics.mean(vals):6.2f}")


def main():
    candidate_path = sys.argv[1]
    n_seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 6

    baseline_agent = _load_agent("main.py")
    candidate_agent = _load_agent(candidate_path)

    baseline_results = []
    candidate_results = []
    for seed in range(n_seeds):
        print(f"seed {seed}: baseline...", file=sys.stderr)
        baseline_results.append(_run_and_collect(baseline_agent, seed))
        print(f"seed {seed}: candidate...", file=sys.stderr)
        candidate_results.append(_run_and_collect(candidate_agent, seed))

    summarize("baseline (main.py, self-play)", baseline_results)
    summarize(f"candidate ({candidate_path}, self-play)", candidate_results)


if __name__ == "__main__":
    main()
