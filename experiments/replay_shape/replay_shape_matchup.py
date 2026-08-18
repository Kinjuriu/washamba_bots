"""Track C, Issue #21 - evaluate against the large-farm reference opponent.

Two things this script runs, both built on top of
experiments/replay_shape_instrumentation.py's trace_both() (one env.run()
per episode, both seats' trajectories read out of it - no duplicated game
logic, no new agent-loading path):

1. SELF-VALIDATION: replay_shape_agent.py vs itself. The reference
   opponent has to prove its own shape is real before it's trusted to
   grade anything else - see replay_shape_spec.md and
   replay_shape_validation_report.md, both of which only tested it
   against non-selling built-ins (`pass`). Both seats are checked
   separately (head_to_head.py's own finding: seats are not symmetric).

2. AGENT VS REFERENCE: current agent (default main.py) vs the reference
   opponent, seat-swapped like head_to_head.py so seat bias cancels, over
   multiple seeds, with the full trajectory/paired-stats report the task
   asked for.

Usage:
    .venv/Scripts/python.exe experiments/replay_shape_matchup.py self [n_seeds]
    .venv/Scripts/python.exe experiments/replay_shape_matchup.py vs [agent_path] [n_seeds]
    .venv/Scripts/python.exe experiments/replay_shape_matchup.py both [agent_path] [n_seeds]

Does not touch main.py, does not merge, does not submit. Read `wins`
before any t-value, same as every other harness in this repo.
"""
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from replay_shape_instrumentation import (  # noqa: E402
    BASE_PRICES,
    run_validation_report,
    trace_both,
)

REFERENCE = str(Path(__file__).resolve().parent / "replay_shape_agent.py")


# =======================================================================
# 1. Self-validation
# =======================================================================

def self_validation(n_seeds):
    """replay-shape vs replay-shape, both seats checked independently ->
    2*n_seeds runs of run_validation_report()."""
    runs = []  # list of (seed, seat, days, report)
    for seed in range(n_seeds):
        days_a, days_b = trace_both(REFERENCE, REFERENCE, seed)
        for seat, days in ((0, days_a), (1, days_b)):
            runs.append((seed, seat, days, run_validation_report(days)))
    return runs


def print_self_validation(runs):
    n = len(runs)
    checks = list(runs[0][3].keys())
    print(f"replay-shape vs replay-shape self-validation, {n} (seed,seat) runs\n")

    banks = [days[-1]["cumulative_bank"] for _, _, days, _ in runs]
    print(f"  final bank: mean={statistics.mean(banks):,.0f}  "
          f"min={min(banks):,.0f}  max={max(banks):,.0f}")
    print()

    for check in checks:
        passed = sum(1 for _, _, _, r in runs if r[check][0])
        print(f"  [{passed:>2}/{n}] {check}")
        # show one failing example's detail, if any, so a MISS is actionable
        for seed, seat, _, r in runs:
            if not r[check][0]:
                print(f"           e.g. seed={seed} seat={seat}: {r[check][1]}")
                break

    print()
    print("Requirement checklist (from this task's validation requirements):")
    labels = {
        1: "final_bank (SOFT, corrected range)",
        2: "farm_scale (HARD)",
        3: "crew_scale (SOFT)",
        4: "animal_scale (SOFT)",
        5: "selling_throughput (SOFT)",  # ramps from ~day 10 - covers 5 and 6 together
        6: "selling_throughput (SOFT)",
        7: "market_pressure (SOFT, self-play only)",
        8: "no_feed_collapse (HARD behavioural)",
    }
    texts = {
        1: "1. approx target bank range",
        2: "2. approx 75 tiles",
        3: "3. approx 13-15 crew",
        4: "4. approx 8-9 animals",
        5: "5. sells heavily from ~day 10",
        6: "6. no day-22 liquidation cliff",
        7: "7. meaningful market pressure",
        8: "8. no feed-bill collapse",
    }
    for i in range(1, 9):
        check = labels[i]
        passed = sum(1 for _, _, _, r in runs if r[check][0])
        mark = "PASS" if passed == n else ("PARTIAL" if passed > 0 else "FAIL")
        print(f"  [{mark:>7}] {texts[i]}  ({passed}/{n})")


# =======================================================================
# 2. Agent vs reference
# =======================================================================

def agent_vs_reference(agent_path, n_seeds):
    """Seat-swapped like head_to_head.py: agent in seat 0 then seat 1,
    same seed, so seat bias cancels rather than getting attributed to
    either side. Each trace_both() call is one episode - two calls per
    seed, matching head_to_head.py's own convention exactly."""
    rows = []
    for seed in range(n_seeds):
        agent_at_0, ref_at_1 = trace_both(agent_path, REFERENCE, seed)
        ref_at_0, agent_at_1 = trace_both(REFERENCE, agent_path, seed)
        for agent_days, ref_days, seat_label in (
            (agent_at_0, ref_at_1, "agent@seat0"),
            (agent_at_1, ref_at_0, "agent@seat1"),
        ):
            our_bank = agent_days[-1]["cumulative_bank"]
            ref_bank = ref_days[-1]["cumulative_bank"]
            rows.append({
                "seed": seed,
                "seat": seat_label,
                "agent_days": agent_days,
                "ref_days": ref_days,
                "our_bank": our_bank,
                "ref_bank": ref_bank,
                "diff": our_bank - ref_bank,
                "win": our_bank > ref_bank,
            })
    return rows


def _trajectory_table(agent_days, ref_days, sample_days=(0, 5, 10, 15, 20, 25, 29)):
    lines = []
    header = f"{'day':>3} | {'our$':>8} {'land':>4} {'crew':>4} {'animl':>5} {'sold':>5} {'rev':>7} | {'ref$':>8} {'land':>4} {'crew':>4} {'animl':>5} {'sold':>5} {'rev':>7}"
    lines.append(header)
    lines.append("-" * len(header))
    by_day_a = {d["day"]: d for d in agent_days}
    by_day_r = {d["day"]: d for d in ref_days}
    for day in sample_days:
        a = by_day_a.get(day)
        r = by_day_r.get(day)
        if a is None or r is None:
            continue
        a_animals = sum(a["animals_placed"].values())
        r_animals = sum(r["animals_placed"].values())
        lines.append(
            f"{day:>3} | {a['cash']:>8.0f} {a['land_tiles']:>4} {a['crew']:>4} {a_animals:>5} "
            f"{a['units_sold_today']:>5} {a['revenue_today']:>7.0f} | "
            f"{r['cash']:>8.0f} {r['land_tiles']:>4} {r['crew']:>4} {r_animals:>5} "
            f"{r['units_sold_today']:>5} {r['revenue_today']:>7.0f}"
        )
    return "\n".join(lines)


def print_agent_vs_reference(agent_path, rows):
    n_seeds = len({r["seed"] for r in rows})
    matches = len(rows)
    print(f"{agent_path}  vs  {REFERENCE}")
    print(f"  {n_seeds} seeds x 2 seats = {matches} matches\n")

    print(f"{'seed':>4} {'seat':>11} {'our bank':>10} {'ref bank':>10} {'diff':>9}  win")
    for r in rows:
        print(f"{r['seed']:4d} {r['seat']:>11} {r['our_bank']:10,.0f} {r['ref_bank']:10,.0f} "
              f"{r['diff']:+9,.0f}  {'W' if r['win'] else 'L'}")

    diffs = [r["diff"] for r in rows]
    wins = sum(1 for r in rows if r["win"])
    mean_diff = statistics.mean(diffs)
    print()
    print(f"  mean bank difference (ours - reference)  {mean_diff:+9,.0f}")
    print(f"  we won                                    {wins}/{matches}")
    if len(diffs) > 1:
        spread = statistics.stdev(diffs)
        stderr = spread / len(diffs) ** 0.5
        print(f"  sd of diffs                              {spread:9,.0f}")
        print(f"  standard error                           {stderr:9,.0f}")
        if stderr:
            print(f"  t                                        {mean_diff / stderr:9.2f}")

    # Detailed trajectory for the first match only - full per-turn dumps for
    # every seed/seat would bury the paired stats above in noise.
    first = rows[0]
    print(f"\nTrajectory detail (seed={first['seed']}, {first['seat']}):")
    print(_trajectory_table(first["agent_days"], first["ref_days"]))

    # End-of-season inventory + market snapshot for the same match.
    a_shed = first["agent_days"][-1]["shed_inventory"]
    r_shed = first["ref_days"][-1]["shed_inventory"]
    print(f"\nFinal shed inventory - ours: {a_shed}")
    print(f"Final shed inventory - reference: {r_shed}")
    print(f"Final premium market prices (base in parens): "
          + ", ".join(f"{p}={first['ref_days'][-1]['market_prices'][p]} (${b})" for p, b in BASE_PRICES.items() if b > 100))

    total_units_sold_ours = sum(d["units_sold_today"] for d in first["agent_days"])
    total_units_sold_ref = sum(d["units_sold_today"] for d in first["ref_days"])
    total_revenue_ours = sum(d["revenue_today"] for d in first["agent_days"])
    total_revenue_ref = sum(d["revenue_today"] for d in first["ref_days"])
    print(f"\nSeason totals (seed={first['seed']}) - ours: {total_units_sold_ours} units sold, "
          f"${total_revenue_ours:,.0f} revenue")
    print(f"Season totals (seed={first['seed']}) - reference: {total_units_sold_ref} units sold, "
          f"${total_revenue_ref:,.0f} revenue")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("self", "vs", "both"):
        print(__doc__)
        raise SystemExit(2)

    mode = sys.argv[1]
    if mode == "self":
        n_seeds = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        print_self_validation(self_validation(n_seeds))
        return

    if mode == "vs":
        agent_path = sys.argv[2] if len(sys.argv) > 2 else "main.py"
        n_seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 4
        print_agent_vs_reference(agent_path, agent_vs_reference(agent_path, n_seeds))
        return

    if mode == "both":
        agent_path = sys.argv[2] if len(sys.argv) > 2 else "main.py"
        n_seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 4
        print_self_validation(self_validation(n_seeds))
        print("\n" + "=" * 78 + "\n")
        print_agent_vs_reference(agent_path, agent_vs_reference(agent_path, n_seeds))


if __name__ == "__main__":
    main()
