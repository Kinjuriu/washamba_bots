"""One-factor-at-a-time sensitivity sweep for variant D's four cadence
constants (experiments/pricing_cadence_v1_1_report.md). Generates
perturbed copies of agent_d.py (one constant changed at a time, everything
else held at D's current value) and screens them against the unmodified
control A with the same paired/seat-swapped methodology as the accepted
benchmark - a small seed count by default, since this is a screen for
obviously poor regions, not the final confirmation.

Root main.py is never touched; agent_d.py itself (the accepted baseline)
is only read, never modified.

Usage:
    .venv/bin/python experiments/pricing_cadence_sensitivity_sweep.py [n_seeds]

Writes generated variants to experiments/pricing_cadence_variants/sweep/
and prints a mean/stdev/worst/wins line per setting.
"""
import json
import pathlib
import statistics
import sys

from kaggle_environments import make

REPO = pathlib.Path(__file__).resolve().parent.parent
VARIANTS_DIR = REPO / "experiments" / "pricing_cadence_variants"
SWEEP_DIR = VARIANTS_DIR / "sweep"
BASELINE = str(VARIANTS_DIR / "agent_a.py")
D_PATH = VARIANTS_DIR / "agent_d.py"

# The 0.75/0.90/1.0/1.10/1.25x grid the experiment report specifies,
# adapted per-constant where a straight multiplier doesn't make sense.
SWEEP_SPEC = {
    "SELL_HORIZON_DAYS": {
        "baseline_src": "3",
        # Day-count constant; 0.75x3=2.25 and 0.90x3=2.7 both round to a
        # value indistinguishable from baseline or each other, so this
        # uses a wider local integer set instead of the literal grid.
        "settings": ["1", "2", "5", "7"],
    },
    "INVENTORY_PRESSURE_WEIGHT": {
        "baseline_src": "1.0",
        "settings": ["0.75", "0.90", "1.10", "1.25"],
    },
    "CADENCE_URGENCY_PRICE_WEIGHT": {
        "baseline_src": "0.6",
        "settings": ["0.45", "0.54", "0.66", "0.75"],
    },
    "CADENCE_URGENCY_CAP_WEIGHT": {
        "baseline_src": "1.0",
        "settings": ["0.75", "0.90", "1.10", "1.25"],
    },
}


def generate_variants():
    SWEEP_DIR.mkdir(exist_ok=True)
    base = D_PATH.read_text()
    written = []
    for const, spec in SWEEP_SPEC.items():
        anchor = f"{const} = {spec['baseline_src']}"
        assert base.count(anchor) == 1, f"anchor not found/unique for {const}"
        for value in spec["settings"]:
            text = base.replace(anchor, f"{const} = {value}", 1)
            fname = f"agent_d__{const}__{value}.py"
            (SWEEP_DIR / fname).write_text(text)
            written.append(SWEEP_DIR / fname)
    return written


def play(agent_a, agent_b, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([agent_a, agent_b])
    left, right = env.steps[-1]
    return left.reward, right.reward


def compare(variant_path, baseline_path, n_seeds):
    all_deltas = []
    wins = 0
    for seed in range(n_seeds):
        variant_first, baseline_second = play(str(variant_path), baseline_path, seed)
        baseline_first, variant_second = play(baseline_path, str(variant_path), seed)
        for variant_bank, baseline_bank in (
            (variant_first, baseline_second),
            (variant_second, baseline_first),
        ):
            d = variant_bank - baseline_bank
            all_deltas.append(d)
            wins += d > 0
    return all_deltas, wins


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    variants = generate_variants()
    variants.append(D_PATH)  # current D, sanity anchor

    results = {}
    for path in sorted(variants, key=lambda p: p.name):
        name = path.stem
        deltas, wins = compare(path, BASELINE, n_seeds)
        matches = len(deltas)
        mean_d = statistics.mean(deltas)
        stdev_d = statistics.stdev(deltas) if matches > 1 else 0.0
        results[name] = {
            "mean": mean_d, "stdev": stdev_d, "worst": min(deltas),
            "best": max(deltas), "wins": wins, "matches": matches, "deltas": deltas,
        }
        print(f"{name:55s} mean={mean_d:+8.1f}  stdev={stdev_d:7.1f}  worst={min(deltas):+7.0f}  wins={wins}/{matches}")

    out = REPO / "experiments" / "pricing_cadence_v1_1_sweep_screen.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()
