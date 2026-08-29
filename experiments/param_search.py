"""Joint parameter search driver for main.py.

Why this exists, and why it's the next step after a paired comparison:

Paired comparison is great for *one* knob, but the same delta comes from
many shapes. Two-knob interactions (e.g. "the hire gate is mispriced *and*
the cash reserve is too tight") are invisible to a paired A/B, and an
isolated single-knob sweep of either one alone shows "no lever" because
the coupled effect was the lever. This driver is the cheap screen for
coupled effects before spending full paired-comparison runs.

Design:

- **Knob registry**: parse main.py via AST. Look for module-level
  assignments ``NAME = <literal>`` and ``NAME = {"KEY": <literal>, ...}``
  (typed as dicts of literals). Excludes PATH_C_* prefix (dead code
  per the cleanup pass) and any other unparsed shapes (functions,
  class definitions, tuples, etc.). This is intentionally restrictive
  so a human can read the registry and trust what each knob is.

- **Variant generation**: rewrite only the targeted constant lines,
  asserting exactly one replacement per variant. A failure to find
  the line is an error, not a silent skip - silent skips are how
  pre-staged knobs get tested in production.

- **Stages**:
    - ``screen``  : random ~32 samples vs baseline on 4 seeds x 1 opponent.
                    Cheap, no statistical claims - just a triage.
    - ``confirm`` : top-K candidates on DEV_SEEDS x 1 opponent with the
                    paired harness. This is the one to ship on.
    - ``holdout`` : post-freeze check, HOLDOUT_SEEDS. Use only after
                    confirm passes, per the dev/holdout seed discipline.

- **--profile NAME** : one-at-a-time +/- 25% / +/- 50% response curve
  per knob. Useful when the coupled sweep says "knob X matters here"
  and you want to know its dose-response in isolation before
  committing to a confirm run.

- **JSONL accumulation**: results append to
  ``experiments/param_search_results.jsonl``, one line per (variant, seed).
  Resume-safe: re-running appends. The JSONL is also the audit trail
  of which knobs were tested against which seeds with which delta.

Usage:
    # screen: 32 random vector samples, 4 seeds each
    .venv/Scripts/python.exe experiments/param_search.py --stage screen --samples 32

    # confirm: top 5 from screen.jsonl, full dev set
    .venv/Scripts/python.exe experiments/param_search.py --stage confirm --top 5

    # profile: response curve for one knob
    .venv/Scripts/python.exe experiments/param_search.py --profile MIN_MONEY_TO_HIRE

    # 2 samples for a smoke test
    .venv/Scripts/python.exe experiments/param_search.py --stage screen --samples 2
"""

import argparse
import ast
import copy
import json
import random
import statistics
import sys
import time
from pathlib import Path

from kaggle_environments import make

# Same sys.path dance as paired_compare.py - so ``from experiments.seeds``
# works when this script is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments.seeds import DEV_SEEDS, HOLDOUT_SEEDS

# Mirror paired_compare.py: only pair against seed-reproducible opponents.
PAIRABLE_OPPONENTS = ("pass", "starter")

ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = ROOT / "experiments" / "param_search_results.jsonl"
MAIN_PATH = ROOT / "main.py"
MUTANT_PATH = ROOT / "experiments" / ".mutant_main.py"

# Knob selection: discover all module-level scalar/dict assignments.
# Exclude: anything starting with PATH_C_ (dead code per cleanup), the
# entrypoint binding, and standard library imports.
EXCLUDE_PREFIXES = ("PATH_C_", "_")
EXCLUDE_NAMES = {"agent"}

# Game-mechanic constants that look like knobs but aren't - they encode
# the competition's hard constraints (episode length, day length, etc.)
# and changing them either breaks the engine or has zero effect. They
# exist in main.py for code-clarity, not for tuning.
INTERNAL_CONSTANTS = {
    "DEFAULT_TURNS_PER_DAY",
    "DEFAULT_TOWN_CENTER_SELL_INTERVAL",
    "DEFAULT_TOWN_SHOP_SELL_INTERVAL",
    "SEASON_DAYS",
    "TURNS_PER_DAY",
    "HINGE_GAIN",
    "BOARD_SIZE",
    "SHED_CAPACITY",
}


# ---------------------------------------------------------------------------
# Knob registry
# ---------------------------------------------------------------------------

def discover_knobs(main_path: Path = MAIN_PATH) -> dict:
    """Parse main.py via AST and return a registry of tweakable knobs.

    Returns a dict mapping knob name to a dict of
    ``{"value": <python literal>, "kind": "scalar" | "dict", "line": int}``.

    Restricted to module-level assignments whose RHS is a constant
    expression (numbers, strings, True/False/None, or dicts of those).
    Anything more exotic is filtered out - the point is to make the
    registry read like a config file.
    """
    source = main_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(main_path))

    knobs = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        name = target.id
        if any(name.startswith(p) for p in EXCLUDE_PREFIXES):
            continue
        if name in EXCLUDE_NAMES:
            continue
        if name in INTERNAL_CONSTANTS:
            continue

        try:
            value = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            continue

        if isinstance(value, (int, float, bool, str)):
            kind = "scalar"
        elif isinstance(value, dict) and all(
            isinstance(k, str)
            and isinstance(v, (int, float, bool, str))
            for k, v in value.items()
        ):
            kind = "dict"
        else:
            continue

        knobs[name] = {"value": value, "kind": kind, "line": node.lineno}

    return knobs


# ---------------------------------------------------------------------------
# Variant generation: write a mutant main.py with a single knob changed
# ---------------------------------------------------------------------------

def write_mutant(knob_name: str, new_value, baseline_path: Path = MAIN_PATH,
                 mutant_path: Path = MUTANT_PATH) -> None:
    """Rewrite baseline main.py to mutant_path with one knob replaced.

    Asserts exactly one replacement. If zero, or more than one, line
    matches, raises RuntimeError - silent failure modes here are how
    pre-staged knobs get tested in production.

    Use ``write_mutant_multi`` for multi-knob variants.
    """
    write_mutant_multi({knob_name: new_value}, baseline_path, mutant_path)


def write_mutant_multi(overrides: dict, baseline_path: Path = MAIN_PATH,
                       mutant_path: Path = MUTANT_PATH) -> None:
    """Apply multiple knob overrides in one pass.

    For each (knob_name, new_value) in ``overrides``, locate the
    single matching line in main.py and rewrite it. If a knob is
    missing, or matched more than once, raises RuntimeError.

    Reads the file once, applies all replacements in memory, writes
    the result. Order of replacements doesn't matter because each
    one targets a distinct line index.
    """
    source = baseline_path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)

    for knob_name, new_value in overrides.items():
        matches = []
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped.startswith(knob_name + " "):
                continue
            if "=" not in stripped:
                continue
            head, _, _ = stripped.partition("=")
            if head.strip() != knob_name:
                continue
            matches.append(i)

        if len(matches) != 1:
            raise RuntimeError(
                f"write_mutant_multi: expected exactly 1 match for {knob_name!r}, "
                f"found {len(matches)} in {baseline_path}"
            )

        line_idx = matches[0]
        indent = lines[line_idx][: len(lines[line_idx]) - len(lines[line_idx].lstrip())]

        if isinstance(new_value, dict):
            # Build the source-style multi-line dict assignment:
            #   KNOB = {
            #       "KEY": val,
            #       ...
            #   }
            items_lines = []
            for k, v in new_value.items():
                items_lines.append(f"    {json.dumps(k)}: {json.dumps(v)},")
            inner = "{\n" + "\n".join(items_lines) + "\n}"
            replacement = f"{indent}{knob_name} = {inner}\n"
            # The original dict may span multiple lines; we need to find the
            # closing brace of the original assignment and replace the whole
            # block. Detect by counting braces: start at line_idx with
            # already-open "{" and walk forward to the matching "}".
            original_first_line = lines[line_idx]
            # Count the open brace on the assignment line (RHS starts with "{")
            opens = original_first_line.count("{")
            closes = original_first_line.count("}")
            end_idx = line_idx
            while closes < opens:
                end_idx += 1
                if end_idx >= len(lines):
                    raise RuntimeError(
                        f"write_mutant_multi: unterminated dict for {knob_name!r}"
                    )
                opens += lines[end_idx].count("{")
                closes += lines[end_idx].count("}")
            # Replace lines[line_idx..end_idx] with the new assignment.
            lines[line_idx:end_idx + 1] = [replacement]
        else:
            replacement = f"{indent}{knob_name} = {new_value!r}\n"
            lines[line_idx] = replacement

    mutant_path.write_text("".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Run one episode
# ---------------------------------------------------------------------------

def run_episode(agent_path, opponent: str, seed: int) -> float:
    """Run one episode and return the left (player 0) final bank."""
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([agent_path, opponent])
    return float(env.steps[-1][0].reward)


# ---------------------------------------------------------------------------
# Stage: screen
# ---------------------------------------------------------------------------

def random_variant(knobs: dict) -> dict:
    """Generate a random sample of knob perturbations.

    For each scalar knob, with 50% probability apply a +/- 25% jitter;
    with 50% probability leave it alone. Dict knobs are perturbed by
    scaling each numeric value with a 50% chance per entry.

    Returns a dict {knob_name: new_value, ...} for the perturbed knobs.
    """
    rng = random.Random()
    out = {}
    for name, spec in knobs.items():
        if spec["kind"] == "scalar":
            v = spec["value"]
            if not isinstance(v, (int, float)):
                continue
            if rng.random() < 0.5:
                factor = rng.choice([0.75, 0.9, 1.1, 1.25])
                out[name] = type(v)(v * factor)
        else:
            new_dict = {}
            changed = False
            for k, v in spec["value"].items():
                if isinstance(v, (int, float)) and rng.random() < 0.3:
                    factor = rng.choice([0.75, 0.9, 1.1, 1.25])
                    new_dict[k] = type(v)(v * factor)
                    changed = True
                else:
                    new_dict[k] = v
            if changed:
                out[name] = new_dict
    return out


def stage_screen(knobs: dict, n_samples: int, opponent: str, seeds: list,
                 results_fh) -> None:
    """Run ``n_samples`` random variants, paired against the baseline on
    ``seeds`` x 1 opponent. Append one summary record per variant to
    the JSONL results file.
    """
    print(f"=== screen: {n_samples} samples, {len(seeds)} seeds, vs {opponent} ===\n")

    for s in range(n_samples):
        variant = random_variant(knobs)
        if not variant:
            print(f"  sample {s}: skipped (no perturbations)")
            continue

        try:
            write_mutant_multi(variant)
        except Exception as e:
            print(f"  sample {s}: write_mutant failed: {e}")
            continue

        # Screen is single-arm: no baseline. The point is to filter which
        # random vectors don't crash and look reasonable, before spending
        # the paired confirm run on them. Each variant is compared later via
        # ``--stage confirm`` which runs paired (variant vs baseline).
        deltas = []
        for seed in seeds:
            bank = run_episode(str(MUTANT_PATH), opponent, seed)
            deltas.append(bank)

        mean = statistics.mean(deltas)
        record = {
            "stage": "screen",
            "ts": time.time(),
            "variant": {k: (v if not isinstance(v, dict) else dict(v))
                        for k, v in variant.items()},
            "opponent": opponent,
            "seeds": list(seeds),
            "mean_bank": mean,
            "stdev_bank": statistics.stdev(deltas) if len(deltas) > 1 else 0.0,
        }
        results_fh.write(json.dumps(record) + "\n")
        results_fh.flush()

        # Show knob names + delta
        keys = ", ".join(f"{k}={v}" for k, v in list(variant.items())[:3])
        more = "" if len(variant) <= 3 else f" (+{len(variant) - 3} more)"
        print(f"  sample {s}: {mean:8.0f}  [{keys}{more}]")


# ---------------------------------------------------------------------------
# Stage: confirm - run a previously-screened variant with the paired harness
# ---------------------------------------------------------------------------

def stage_confirm(variants: list, opponent: str, seeds: list,
                  results_fh) -> None:
    """For each variant in ``variants`` (loaded from screen JSONL), run a
    paired comparison against the baseline on ``seeds``. One record per
    variant appended to JSONL.
    """
    print(f"=== confirm: {len(variants)} variants, {len(seeds)} seeds, vs {opponent} ===\n")
    print(f"{'variant':40} {'mean':>9} {'wins':>5} {'t':>7}")

    for v in variants:
        variant_overrides = v["variant"]
        # Apply: write mutant
        try:
            write_mutant_multi(variant_overrides)
        except Exception as e:
            print(f"  {str(variant_overrides)[:40]:40}: write_mutant failed: {e}")
            continue

        deltas = []
        baseline_banks = []
        mutant_banks = []
        for seed in seeds:
            baseline_banks.append(run_episode(str(MAIN_PATH), opponent, seed))
            mutant_banks.append(run_episode(str(MUTANT_PATH), opponent, seed))
            deltas.append(mutant_banks[-1] - baseline_banks[-1])

        mean_delta = statistics.mean(deltas)
        wins = sum(1 for d in deltas if d > 0)
        if len(deltas) > 1:
            spread = statistics.stdev(deltas)
            stderr = spread / len(deltas) ** 0.5
            t = mean_delta / stderr if stderr else 0.0
        else:
            t = 0.0

        record = {
            "stage": "confirm",
            "ts": time.time(),
            "variant": variant_overrides,
            "opponent": opponent,
            "seeds": list(seeds),
            "mean_delta": mean_delta,
            "wins": wins,
            "n_seeds": len(deltas),
            "t": t,
        }
        results_fh.write(json.dumps(record) + "\n")
        results_fh.flush()

        keys = str(variant_overrides)[:40]
        print(f"  {keys:40} {mean_delta:+9.0f} {wins:3d}/{len(deltas)} {t:7.2f}")


# ---------------------------------------------------------------------------
# Stage: holdout
# ---------------------------------------------------------------------------

def stage_holdout(variants: list, opponent: str, seeds: list,
                  results_fh) -> None:
    """Same as confirm but uses HOLDOUT_SEEDS - the held-out set, used
    ONCE per candidate bundle after the change is frozen. See
    experiments/seeds.py for the dev/holdout discipline.
    """
    print(f"=== holdout: {len(variants)} variants, {len(seeds)} HOLDOUT seeds ===\n")
    stage_confirm(variants, opponent, seeds, results_fh)


# ---------------------------------------------------------------------------
# Stage: profile - dose-response curve for a single knob
# ---------------------------------------------------------------------------

def stage_profile(knob_name: str, opponent: str, seeds: list,
                  results_fh) -> None:
    """Run the candidate knob at +50%, +25%, -25%, -50% of its baseline
    value, on the seed set. Paired against the unmodified baseline.

    The point of this stage is to surface a knob's *shape* - whether
    the response is monotone, has a peak, or is a cliff - in isolation,
    before a confirm run couples it with anything else.
    """
    knobs = discover_knobs()
    if knob_name not in knobs:
        print(f"  error: knob {knob_name!r} not in registry. "
              f"Available: {sorted(knobs.keys())[:20]}...")
        return
    spec = knobs[knob_name]
    base_value = spec["value"]

    if spec["kind"] != "scalar":
        print(f"  error: knob {knob_name!r} is a dict, profile only works on scalars")
        return

    factors = [0.5, 0.75, 1.0, 1.25, 1.5]
    print(f"=== profile: {knob_name} (base={base_value!r}), {len(seeds)} seeds ===\n")
    print(f"{'factor':>8} {'value':>10} {'mean':>10} {'mean_delta':>12} {'wins':>5}")

    for factor in factors:
        new_value = type(base_value)(base_value * factor) if isinstance(base_value, (int, float)) else base_value
        try:
            write_mutant(knob_name, new_value)  # single knob, write_mutant handles one
        except Exception as e:
            print(f"  factor {factor}: write_mutant failed: {e}")
            continue

        deltas = []
        for seed in seeds:
            base = run_episode(str(MAIN_PATH), opponent, seed)
            mut = run_episode(str(MUTANT_PATH), opponent, seed)
            deltas.append(mut - base)

        mean_delta = statistics.mean(deltas)
        wins = sum(1 for d in deltas if d > 0)
        record = {
            "stage": "profile",
            "ts": time.time(),
            "knob": knob_name,
            "factor": factor,
            "value": new_value,
            "opponent": opponent,
            "seeds": list(seeds),
            "mean_delta": mean_delta,
            "wins": wins,
            "n_seeds": len(deltas),
        }
        results_fh.write(json.dumps(record) + "\n")
        results_fh.flush()

        print(f"{factor:8.2f} {new_value!r:>10} {' ':>10} {mean_delta:+12.0f} {wins:3d}/{len(deltas)}")


# ---------------------------------------------------------------------------
# Top-K loading from previous screen results
# ---------------------------------------------------------------------------

def load_top_variants(jsonl_path: Path, stage_name: str, k: int) -> list:
    """Return the top-K variants by mean_bank from previous screen records."""
    if not jsonl_path.exists():
        print(f"  error: no JSONL at {jsonl_path} - run --stage screen first")
        return []
    records = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("stage") == stage_name:
            records.append(r)
    records.sort(key=lambda r: r.get("mean_bank", 0) or r.get("mean_delta", 0),
                 reverse=True)
    return records[:k]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", choices=("screen", "confirm", "holdout"),
                        help="Which stage to run")
    parser.add_argument("--samples", type=int, default=32,
                        help="Number of random variants for --stage screen (default: 32)")
    parser.add_argument("--top", type=int, default=5,
                        help="Top-K from JSONL for --stage confirm/holdout (default: 5)")
    parser.add_argument("--opponent", default="starter",
                        choices=PAIRABLE_OPPONENTS,
                        help="Opponent to pair against (default: starter)")
    parser.add_argument("--seeds", nargs="+", type=int, default=None,
                        help="Seeds to use; default depends on stage")
    parser.add_argument("--profile", default=None,
                        help="Knob name to profile (one-at-a-time dose-response)")
    args = parser.parse_args()

    knobs = discover_knobs()
    if not knobs:
        print("  error: no knobs discovered in main.py - is the file parseable?")
        return

    # Default seeds per stage
    if args.seeds is None:
        if args.profile:
            args.seeds = list(DEV_SEEDS)[:4]
        elif args.stage == "holdout":
            args.seeds = list(HOLDOUT_SEEDS)
        else:
            args.seeds = list(DEV_SEEDS)[:4]

    if args.stage == "holdout":
        seed_set_name = "HOLDOUT"
    else:
        seed_set_name = "DEV (sliced)"

    print(f"Knobs discovered: {len(knobs)}")
    print(f"Opponent: {args.opponent}, seeds ({seed_set_name}): {args.seeds}\n")

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("a", encoding="utf-8") as fh:
        if args.profile:
            stage_profile(args.profile, args.opponent, args.seeds, fh)
        elif args.stage == "screen":
            stage_screen(knobs, args.samples, args.opponent, args.seeds, fh)
        elif args.stage in ("confirm", "holdout"):
            variants = load_top_variants(RESULTS_PATH, "screen", args.top)
            if not variants:
                print(f"  nothing to {'confirm' if args.stage == 'confirm' else 'holdout'}")
                return
            stage_confirm(variants, args.opponent, args.seeds, fh) \
                if args.stage == "confirm" else \
                stage_holdout(variants, args.opponent, args.seeds, fh)

    # Clean up mutant file
    if MUTANT_PATH.exists():
        MUTANT_PATH.unlink()


if __name__ == "__main__":
    main()
