"""Decision-level diagnostic for experiments/candidates/forward_sell_policy_v0.py.

Runs self-play episodes in-process (so DECISION_LOG is inspectable) and
reports: SELL vs HOLD counts, how many decisions were genuine ties
(revenue_now == revenue_delayed, i.e. nothing distinguished the two
turns) vs real differences, per-product breakdown, and a day-bucketed
prefer_sell rate to check whether the policy naturally gets more
sell-leaning as the season shortens (task's "seasonality" question).
RESEARCH ONLY - does not modify main.py or pricing.py.

    .venv/Scripts/python.exe experiments/forward_sell_policy_decision_diag.py [n_seeds]
"""
import sys
import statistics
from collections import Counter, defaultdict

from kaggle_environments import make

import experiments.candidates.forward_sell_policy_v0 as candidate


def run(n_seeds):
    candidate.DECISION_LOG.clear()
    for seed in range(n_seeds):
        print(f"seed {seed}...", file=sys.stderr)
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run([candidate.agent, candidate.agent])

    log = candidate.DECISION_LOG
    print(f"\ntotal decisions logged (both seats, {n_seeds} self-play episodes): {len(log)}")

    reasons = Counter(r["reason"] for r in log)
    print(f"by reason: {dict(reasons)}")

    ties = [r for r in log if r["revenue_now"] == r["revenue_delayed"]]
    genuine_diff = [r for r in log if r["revenue_now"] != r["revenue_delayed"]]
    print(f"ties (revenue_now == revenue_delayed): {len(ties)} ({100*len(ties)/len(log):.1f}%)")
    print(f"genuine differences: {len(genuine_diff)} ({100*len(genuine_diff)/len(log):.1f}%)")
    if genuine_diff:
        diffs = [abs(r["advantage"]) for r in genuine_diff]
        print(f"  mean |advantage| when genuinely different: {statistics.mean(diffs):.2f}")
        print(f"  hold wins among genuine differences: "
              f"{sum(1 for r in genuine_diff if r['reason']=='hold_beats_sell_now')}/{len(genuine_diff)}")

    forced_by_pressure = [r for r in log if r["reason"] == "inventory_pressure"]
    print(f"forced by inventory_pressure >= 1: {len(forced_by_pressure)}")

    print("\nby product:")
    by_product = defaultdict(list)
    for r in log:
        by_product[r["product"]].append(r)
    for product, records in sorted(by_product.items()):
        sell_rate = sum(1 for r in records if r["prefer_sell"]) / len(records)
        mean_qty = statistics.mean(r["quantity"] for r in records)
        print(f"  {product:<10} n={len(records):5d}  sell_rate={sell_rate:5.1%}  mean_qty={mean_qty:6.2f}")

    print("\nseasonality: prefer_sell rate by day-bucket (5-day buckets, pre-liquidation only):")
    by_bucket = defaultdict(list)
    for r in log:
        bucket = (r["day"] // 5) * 5
        by_bucket[bucket].append(r)
    for bucket in sorted(by_bucket):
        records = by_bucket[bucket]
        sell_rate = sum(1 for r in records if r["prefer_sell"]) / len(records)
        mean_urgency = statistics.mean(r["urgency"] for r in records)
        mean_pressure = statistics.mean(r["pressure"] for r in records)
        print(f"  day {bucket:2d}-{bucket+4:2d}: n={len(records):5d}  sell_rate={sell_rate:5.1%}  "
              f"mean_urgency={mean_urgency:.3f}  mean_pressure={mean_pressure:.3f}")


if __name__ == "__main__":
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    run(n_seeds)
