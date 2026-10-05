"""Activation diagnostic for experiments/candidates/opponent_aware_sell_gate_exact_yield.py.

Runs self-play episodes with the candidate imported IN-PROCESS (not as a
subprocess, unlike selfplay_agent.py) so ACTIVATION_LOG is inspectable
afterward. RESEARCH ONLY - does not modify main.py or pricing.py.

    .venv/Scripts/python.exe experiments/opponent_aware_exact_yield_activation_diag.py [n_seeds]
"""
import sys
from collections import Counter

from kaggle_environments import make

import experiments.candidates.opponent_aware_sell_gate_exact_yield as candidate


def run(n_seeds):
    candidate.ACTIVATION_LOG.clear()
    scores = []
    for seed in range(n_seeds):
        before = len(candidate.ACTIVATION_LOG)
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run([candidate.agent, candidate.agent])
        a, b = env.steps[-1]
        scores.append((a.reward, b.reward))
        after = len(candidate.ACTIVATION_LOG)
        fired_this_seed = sum(1 for r in candidate.ACTIVATION_LOG[before:after] if r["fired"])
        print(f"seed {seed}: seat0 {a.reward:>8.0f} [{a.status}]  seat1 {b.reward:>8.0f} [{b.status}]  "
              f"(evaluated {after-before}, fired {fired_this_seed})", file=sys.stderr)

    log = candidate.ACTIVATION_LOG
    print(f"\ntotal activation-log entries (override evaluated): {len(log)}")

    by_product = Counter(r["product"] for r in log)
    print(f"by product (evaluated): {dict(by_product)}")

    signal_available = [r for r in log if r["signal_available"]]
    print(f"signal available (opponent_units > 0): {len(signal_available)} / {len(log)}")
    by_product_avail = Counter(r["product"] for r in signal_available)
    print(f"by product (signal available): {dict(by_product_avail)}")

    fired = [r for r in log if r["fired"]]
    print(f"override FIRED: {len(fired)} / {len(log)}")
    by_product_fired = Counter(r["product"] for r in fired)
    print(f"by product (fired): {dict(by_product_fired)}")

    if signal_available:
        print("\nsample of signal-available records (up to 15):")
        for r in signal_available[:15]:
            print(f"  day={r['day']:2d} product={r['product']:<10} opp_units={r['opponent_units']:<4} "
                  f"our_qty={r['our_shed_quantity']:<4} spot={r['spot_price']:<5} "
                  f"threshold={r['sell_threshold']:<5} fired={r['fired']} "
                  f"rev_now={r['revenue_now']} rev_delayed={r['revenue_delayed']}")

    print(f"\nscores: {scores}")


if __name__ == "__main__":
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    run(n_seeds)
