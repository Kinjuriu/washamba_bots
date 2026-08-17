"""
Scratch instrumentation for the seed-budget / wheat-feed investigation.
Does NOT touch the real main.py. Imports a given main.py-shaped module by
absolute path, wraps its entrypoint with a per-turn trace logger, and runs
one seeded episode vs `starter`.

Usage:
    python trace_run.py <main_py_path> <label> <seed> [max_day]

Writes mydocs/scratch/trace_<label>_seed<seed>.jsonl (one JSON object per
turn, farmer+hands only, days 0..max_day inclusive), and prints a summary
(final bank, sheep status) to stdout.
"""
import importlib.util
import json
import os
import sys

REPO = r"C:\Users\user\OneDrive\Desktop\BFG\Collabs\washamba_bots"
sys.path.insert(0, REPO)

from kaggle_environments import make  # noqa: E402


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_sheep_tile(farm, board_size):
    tiles = farm.get("tiles") or []
    for y in range(board_size):
        row = tiles[y] if y < len(tiles) else []
        for x in range(len(row)):
            tile = row[x]
            if isinstance(tile, dict) and "animal" in tile:
                return (x, y), tile
    return None, None


def make_traced_agent(mod, log, max_day):
    """Wrap mod.nikaangukia_meroni(obs) with a pre-decision state snapshot
    plus the action dict it actually returns, appended to `log`."""

    def traced(obs):
        action = mod.nikaangukia_meroni(obs)
        try:
            state = mod.extract_state(obs)
            farm = state["farm"]
            private = state["private"]
            day = state["day"]
            hour = state["hour"]
            step = state["step"]
            board_size = state["board_size"]

            if farm and day <= max_day:
                units = []
                farmer_pos = farm.get("farmer")
                if farmer_pos:
                    inv = mod.unit_inventory(private, 0)
                    units.append({
                        "idx": 0,
                        "role": "farmer",
                        "pos": list(farmer_pos),
                        "wheat_carried": inv.get("WHEAT", 0),
                        "action": action.get("farmer"),
                    })
                for i, hand in enumerate(farm.get("hands") or []):
                    if isinstance(hand, (list, tuple)) and len(hand) == 2:
                        inv = mod.unit_inventory(private, i + 1)
                        hand_actions = action.get("hands") or []
                        units.append({
                            "idx": i + 1,
                            "role": f"hand{i}",
                            "pos": list(hand),
                            "wheat_carried": inv.get("WHEAT", 0),
                            "action": hand_actions[i] if i < len(hand_actions) else None,
                        })

                sheep_pos, sheep_tile = find_sheep_tile(farm, board_size) if farm else (None, None)
                shed = private.get("shed", {})

                log.append({
                    "step": step,
                    "day": day,
                    "hour": hour,
                    "money": farm.get("money"),
                    "shed_wheat": shed.get("WHEAT", 0),
                    "n_hands": len(farm.get("hands") or []),
                    "sheep_present": sheep_tile is not None,
                    "sheep_pos": list(sheep_pos) if sheep_pos else None,
                    "sheep_fed_today": (sheep_tile or {}).get("fed_today"),
                    "sheep_consecutive_unfed": (sheep_tile or {}).get("consecutive_unfed"),
                    "market_orders": action.get("market"),
                    "units": units,
                })
        except Exception as e:  # pragma: no cover - tracer must never break the run
            log.append({"trace_error": repr(e), "step": obs.get("step")})
        return action

    return traced


def main():
    main_path = sys.argv[1]
    label = sys.argv[2]
    seed = int(sys.argv[3])
    max_day = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    opponent = sys.argv[5] if len(sys.argv) > 5 else "starter"

    mod = load_module(main_path, f"traced_main_{label}_{seed}")
    log = []
    traced_agent = make_traced_agent(mod, log, max_day)

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([traced_agent, opponent])

    final = env.steps[-1][0]
    print(f"label={label} seed={seed} status={final.status} reward={final.reward}")

    out_path = os.path.join(REPO, "mydocs", "scratch", f"trace_{label}_seed{seed}.jsonl")
    with open(out_path, "w") as f:
        for rec in log:
            f.write(json.dumps(rec) + "\n")
    print(f"wrote {len(log)} turn records -> {out_path}")

    # Quick sheep-status summary across the whole traced window.
    escaped_at = None
    for rec in log:
        if "sheep_present" in rec and not rec["sheep_present"]:
            escaped_at = rec["step"]
            break
    print(f"sheep escaped within traced window at step={escaped_at}")


if __name__ == "__main__":
    main()
