"""
Seeded batch evaluation for main.py, per the methodology documented in CLAUDE.md:
run the same seed set against each built-in opponent, report mean/stdev/win-rate
instead of trusting a single unseeded episode.

Does not modify main.py.

Usage:
    .venv/Scripts/python.exe experiments/seeded_batch.py
"""

import statistics as stats
from kaggle_environments import make

OPPONENTS = ["pass", "random", "starter"]
SEEDS = range(12)


def run_one(seed: int, opponent: str):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(["main.py", opponent])
    final = env.steps[-1]
    p0, p1 = final[0].reward, final[1].reward
    status_ok = final[0].status == "DONE" and final[1].status == "DONE"
    return p0, p1, status_ok


def main():
    print(f"Running {len(OPPONENTS)} opponents x {len(list(SEEDS))} seeds = "
          f"{len(OPPONENTS) * len(list(SEEDS))} episodes...\n")

    results = {}
    for opponent in OPPONENTS:
        scores = []
        wins = 0
        losses = 0
        ties = 0
        errors = 0
        for seed in SEEDS:
            p0, p1, ok = run_one(seed, opponent)
            if not ok:
                errors += 1
            scores.append(p0)
            if p0 > p1:
                wins += 1
            elif p0 < p1:
                losses += 1
            else:
                ties += 1
            print(f"  vs {opponent:<8} seed={seed:2d}  main.py={p0:8.1f}  {opponent}={p1:8.1f}  "
                  f"{'WIN' if p0 > p1 else ('LOSS' if p0 < p1 else 'TIE')}{'  [STATUS ERROR]' if not ok else ''}")
        results[opponent] = {
            "mean": stats.mean(scores),
            "stdev": stats.stdev(scores) if len(scores) > 1 else 0.0,
            "min": min(scores),
            "max": max(scores),
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "errors": errors,
            "n": len(scores),
        }
        print()

    print("=== Summary (matches the CLAUDE.md baseline-table format) ===")
    header = f"| {'vs':<8} | {'mean':>7} | {'stdev':>7} | {'min':>6} | {'max':>6} | {'wins':>6} |"
    print(header)
    print("|" + "-" * (len(header) - 2) + "|")
    for opponent in OPPONENTS:
        r = results[opponent]
        print(f"| {opponent:<8} | {r['mean']:7.0f} | ±{r['stdev']:6.0f} | {r['min']:6.0f} | "
              f"{r['max']:6.0f} | {r['wins']:3d}/{r['n']:<2d} |")
    total_errors = sum(r["errors"] for r in results.values())
    if total_errors:
        print(f"\nWARNING: {total_errors} episodes finished with a non-DONE status — investigate before trusting these numbers.")


if __name__ == "__main__":
    main()
