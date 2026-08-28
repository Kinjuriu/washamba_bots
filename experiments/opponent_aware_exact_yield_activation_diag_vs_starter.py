"""Same as opponent_aware_exact_yield_activation_diag.py but against the
`starter` built-in instead of self-play, to see whether a differently-
shaped (non-selling) opponent produces different activation counts.
RESEARCH ONLY.

    .venv/Scripts/python.exe -m experiments.opponent_aware_exact_yield_activation_diag_vs_starter [n_seeds]
"""
import sys
from collections import Counter

from kaggle_environments import make

import experiments.candidates.opponent_aware_sell_gate_exact_yield as candidate


def run(n_seeds):
    candidate.ACTIVATION_LOG.clear()
    scores = []
    for seed in range(n_seeds):
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run([candidate.agent, "starter"])
        a, b = env.steps[-1]
        scores.append((a.reward, b.reward))
        print(f"seed {seed}: us {a.reward:>8.0f} [{a.status}]  starter {b.reward:>8.0f} [{b.status}]", file=sys.stderr)

    log = candidate.ACTIVATION_LOG
    print(f"\ntotal activation-log entries (override evaluated): {len(log)}")
    by_product = Counter(r["product"] for r in log)
    print(f"by product (evaluated): {dict(by_product)}")
    signal_available = [r for r in log if r["signal_available"]]
    print(f"signal available: {len(signal_available)} / {len(log)}")
    print(f"by product (signal available): {dict(Counter(r['product'] for r in signal_available))}")
    fired = [r for r in log if r["fired"]]
    print(f"override FIRED: {len(fired)} / {len(log)}")
    print(f"by product (fired): {dict(Counter(r['product'] for r in fired))}")
    if signal_available:
        print("\nsample (up to 15):")
        for r in signal_available[:15]:
            print(f"  day={r['day']:2d} product={r['product']:<10} opp_units={r['opponent_units']:<4} "
                  f"our_qty={r['our_shed_quantity']:<4} spot={r['spot_price']:<5} "
                  f"threshold={r['sell_threshold']:<5} fired={r['fired']}")
    print(f"\nscores: {scores}")


if __name__ == "__main__":
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    run(n_seeds)
