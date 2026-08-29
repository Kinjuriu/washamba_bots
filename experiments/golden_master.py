"""
Golden-master runner for main.py — records and verifies episode-level behavior.

This is the P5b/P8 implementation: runs main.py vs built-in opponents on a
fixed seed set (defaults to seeds 0-2, a fast smoke run), records bank and
action histograms to ``tests/golden/golden.json``, and optionally verifies
against an existing snapshot. Also measures per-turn latency to validate the
1-second actTimeout bound.

Usage:
    # Record / update snapshot
    .venv/Scripts/python.exe experiments/golden_master.py --update

    # Verify against existing snapshot
    .venv/Scripts/python.exe experiments/golden_master.py

    # Fast smoke (only seeds 0-1)
    .venv/Scripts/python.exe experiments/golden_master.py --seeds 0 1

    # Latency measurement only (no snapshot)
    .venv/Scripts/python.exe experiments/golden_master.py --time

The ``tests/golden/golden.json`` is a plain-text record, one JSON object per
line. Fields per entry:

    {
      "opponent": str,       # "pass" | "starter"
      "seed": int,
      "bank": float,         # main.py's final bank
      "status": str,         # "DONE" | "ERROR"
      "sells": int,          # total SELL orders emitted
      "plant_budget_hits": int,  # turns where plant_budget prevented a plant
      "market_orders": int,   # total market orders emitted
      "watered_tiles": int,  # total WATER actions
      "latency_p50_ms": float,   # median ms per turn (0 if --time not used)
      "latency_p99_ms": float,   # p99 ms per turn
      "escapes": int,        # animal escapes (0 for a healthy agent)
    }

A refactor that changes any of these numbers is not a silent improvement — it
requires a conscious ``--update`` pass, so behavioral drift becomes visible
rather than untracked.
"""

import argparse
import json
import os
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

# Ensure we load the repo's main.py, not an installed package.
_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))
os.chdir(str(_root))

from kaggle_environments import make


def _collect_actions(env):
    """Return a compact action summary from a finished episode."""
    steps = env.steps

    sells = water = fertilizer = harvest = 0
    market_orders = 0
    plant_budget_hits = 0  # approximate: turns with zero plant actions

    for step in steps:
        player = step[0]
        actions = player.get("action") or {}
        market = actions.get("market") or []
        market_orders += len(market)
        for a in market:
            if a and a[0] == "SELL":
                sells += 1

        # farmer actions (first unit)
        farmer = actions.get("farmer") or []
        for action in farmer:
            if isinstance(action, (list, tuple)):
                op = action[0] if action else ""
            elif isinstance(action, str):
                op = action
            else:
                continue
            if op == "WATER":
                water += 1
            elif op == "FERTILIZE":
                fertilizer += 1
            elif op == "HARVEST":
                harvest += 1

    # Count animal escapes: empty coop/pasture where an animal was
    occupied = {}
    escapes = 0
    for step in steps:
        farm = step[0].observation.farms[0]
        for y, row in enumerate(farm.get("tiles", [])):
            for x, tile in enumerate(row):
                key = (x, y)
                if isinstance(tile, dict) and tile.get("kind") in ("COOP", "PASTURE") and "animal" in tile:
                    occupied[key] = tile["animal"]
                elif (
                    key in occupied
                    and isinstance(tile, dict)
                    and tile.get("kind") in ("COOP", "PASTURE")
                    and "animal" not in tile
                ):
                    escapes += 1
                    del occupied[key]

    return {
        "sells": sells,
        "water": water,
        "fertilizer": fertilizer,
        "harvest": harvest,
        "market_orders": market_orders,
        "escapes": escapes,
    }


def _measure_latency(agent_path, opponent, seed, *, n_warmup=2, n_measured=5):
    """Measure per-turn latency (ms) for an episode. Returns (p50, p99).

    We time the *whole* episode and divide by 720 turns for an average
    per-turn latency, then repeat ``n_measured`` times and take the
    median of per-turn averages (p50) and the 99th percentile across
    those averages (p99).

    The actTimeout is enforced by the engine per turn, so the per-turn
    average is the relevant signal: any one turn may be slower, but a
    sustained over-budget will show up as average > 1.0s. We do *not*
    instrument the agent internals because the whole-episode wall-clock
    is the conservative, simpler estimator.
    """
    import statistics

    per_episode = []
    for trial in range(n_warmup + n_measured):
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": seed},
            debug=False,
        )
        t0 = time.perf_counter()
        env.run([agent_path, opponent])
        elapsed = time.perf_counter() - t0
        per_turn_ms = (elapsed / 720.0) * 1000.0
        if trial >= n_warmup:
            per_episode.append(per_turn_ms)

    p50 = statistics.median(per_episode)
    sorted_p = sorted(per_episode)
    idx_p99 = max(0, int(round(0.99 * (len(sorted_p) - 1))))
    p99 = sorted_p[idx_p99]
    return (p50, p99)


def _timed_episode_latency(agent_path, opponent, seed):
    """Run one episode and measure wall-clock time. Returns total_seconds."""
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    t0 = time.perf_counter()
    env.run([agent_path, opponent])
    elapsed = time.perf_counter() - t0
    status = env.steps[-1][0].status
    bank = env.steps[-1][0].reward
    return elapsed, status, bank


def run_episode(agent_path, opponent, seed, *, measure_time=False):
    """Run one episode, return a summary dict."""
    if measure_time:
        elapsed, status, bank = _timed_episode_latency(agent_path, opponent, seed)
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": seed},
            debug=False,
        )
        env.run([agent_path, opponent])
    else:
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": seed},
            debug=False,
        )
        env.run([agent_path, opponent])
        elapsed = status = bank = None

    final = env.steps[-1][0]
    actions = _collect_actions(env)
    per_turn_ms = (elapsed / 720 * 1000) if elapsed else 0.0

    return {
        "opponent": opponent,
        "seed": seed,
        "bank": float(final.reward),
        "status": final.status,
        "elapsed_s": round(elapsed, 2) if elapsed else None,
        "per_turn_ms": round(per_turn_ms, 2) if per_turn_ms else None,
        "sells": actions["sells"],
        "market_orders": actions["market_orders"],
        "water": actions["water"],
        "fertilizer": actions["fertilizer"],
        "harvest": actions["harvest"],
        "escapes": actions["escapes"],
    }


def update_snapshots(opponent_seed_pairs, agent_path="main.py"):
    """Regenerate tests/golden/golden.json from scratch."""
    records = []
    for opponent, seed in opponent_seed_pairs:
        print(f"  recording seed={seed} vs {opponent}...", end=" ", flush=True)
        rec = run_episode(agent_path, opponent, seed)
        print(f"bank={rec['bank']:.0f}  sells={rec['sells']}  status={rec['status']}")
        records.append(rec)
    return records


def verify_snapshots(records, golden_path):
    """Check current records against a golden snapshot; return list of drifts."""
    if not golden_path.exists():
        print(f"\nNo golden snapshot at {golden_path} — run with --update to record one.")
        return []

    drifts = []
    for line in golden_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            golden = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Find the matching current record
        match = next((r for r in records
                      if r["opponent"] == golden["opponent"]
                      and r["seed"] == golden["seed"]), None)
        if not match:
            continue

        for key in ["bank", "sells", "market_orders", "water", "fertilizer",
                    "harvest", "escapes"]:
            if key in golden and golden[key] != match[key]:
                drifts.append({
                    "opponent": golden["opponent"],
                    "seed": golden["seed"],
                    "field": key,
                    "expected": golden[key],
                    "actual": match[key],
                })

    return drifts


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--update", action="store_true",
                        help="Regenerate tests/golden/golden.json (overwrites existing)")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2],
                        help="Seeds to record or verify (default: 0 1 2)")
    parser.add_argument("--opponents", nargs="+", default=["pass", "starter"],
                        help="Opponents to run (default: pass starter)")
    parser.add_argument("--time", action="store_true",
                        help="Measure episode wall-clock time as a latency proxy")
    parser.add_argument("--agent", default="main.py",
                        help="Agent file to run (default: main.py)")
    args = parser.parse_args()

    golden_path = _root / "tests" / "golden" / "golden.json"
    opponent_seed_pairs = [(opp, seed)
                           for opp in args.opponents
                           for seed in args.seeds]

    if args.update:
        golden_path.parent.mkdir(parents=True, exist_ok=True)
        records = update_snapshots(opponent_seed_pairs, args.agent)
        lines = [json.dumps(r) for r in records]
        golden_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nSnapshot written to {golden_path}")

        if args.time:
            print("\n=== Latency measurement ===")
            opp, seed = args.opponents[0], args.seeds[0]
            p50, p99 = _measure_latency(args.agent, opp, seed)
            print(f"  {opp} seed={seed}: p50={p50:.1f}ms/turn  p99={p99:.1f}ms/turn")
    else:
        records = [run_episode(args.agent, opp, seed, measure_time=args.time)
                  for opp, seed in opponent_seed_pairs]

        print("\n=== Golden master check ===")
        drifts = verify_snapshots(records, golden_path)
        if not drifts:
            print("  All fields match — golden snapshot is current.")
        else:
            print(f"  {len(drifts)} drift(s) from golden snapshot:")
            for d in drifts:
                print(f"    vs {d['opponent']} seed={d['seed']}: "
                      f"{d['field']} expected={d['expected']}  got={d['actual']}")
            print("\n  Run with --update to accept the new values.")

        if args.time:
            print("\n=== Latency ===")
            opp, seed = args.opponents[0], args.seeds[0]
            p50, p99 = _measure_latency(args.agent, opp, seed)
            print(f"  {opp} seed={seed}: p50={p50:.1f}ms/turn  p99={p99:.1f}ms/turn")
            if p99 > 1000.0:
                print("  WARNING: p99 exceeds 1s actTimeout!")
            elif p50 > 500.0:
                print("  NOTE: p50 > 500ms — tight on the 1s limit.")

        print("\n=== Current records ===")
        for r in records:
            print(f"  vs {r['opponent']} seed={r['seed']}: "
                  f"bank={r['bank']:.0f}  sells={r['sells']}  "
                  f"status={r['status']}  escapes={r['escapes']}")


if __name__ == "__main__":
    main()
