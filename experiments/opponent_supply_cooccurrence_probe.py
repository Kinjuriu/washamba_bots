"""Follow-up to opponent_supply_probe.py: does the exact-yield_units signal
still suffer the co-occurrence problem that killed the earlier
opponent_aware_sell_gate experiment (we're stuck holding excess of a crop
AND the opponent shows visible supply of that same crop, at the same turn)?

RESEARCH ONLY. Not wired into main.py/pricing.py.

    .venv/Scripts/python.exe experiments/opponent_supply_cooccurrence_probe.py [n_seeds]
"""
import sys
import statistics

from kaggle_environments import make

try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS
except ImportError:
    CROPS = {}

FOCUS = ["MELON", "STRAWBERRY", "WOOL"]
# "stuck holding excess" proxy: shed quantity for the product above this,
# mirroring the kind of level that would fail should_sell's threshold gate.
SHED_GLUT_THRESHOLD = 10


def opponent_standing_yield(obs, product):
    farms = obs.get("farms") or []
    player = obs.get("player", 0)
    if len(farms) < 2:
        return 0
    opp = farms[1 - player] or {}
    total = 0
    for row in opp.get("tiles") or []:
        for tile in row or []:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT" and tile.get("crop") == product:
                total += tile.get("yield_units", 0)
    return total


LIQUIDATION_START_DAY = 19  # main.py's current constant (verified: main.py:523), mirrored here for the day split only


def run(n_seeds):
    counts = {
        p: {
            "pre": {"glut_turns": 0, "glut_and_opp_positive": 0, "glut_and_opp_units": []},
            "post": {"glut_turns": 0, "glut_and_opp_positive": 0, "glut_and_opp_units": []},
        }
        for p in FOCUS
    }
    for seed in range(n_seeds):
        print(f"seed {seed}...", file=sys.stderr)
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run(["main.py", "main.py"])
        for step in env.steps:
            obs = step[0].observation
            shed = (obs.get("private") or {}).get("shed") or {}
            day = obs.get("day", 0)
            bucket = "pre" if day < LIQUIDATION_START_DAY else "post"
            for product in FOCUS:
                held = shed.get(product, 0)
                if held > SHED_GLUT_THRESHOLD:
                    c = counts[product][bucket]
                    c["glut_turns"] += 1
                    opp_units = opponent_standing_yield(obs, product)
                    c["glut_and_opp_units"].append(opp_units)
                    if opp_units > 0:
                        c["glut_and_opp_positive"] += 1

    print(f"\nco-occurrence check (shed held > {SHED_GLUT_THRESHOLD}), {n_seeds} self-play seeds, "
          f"split at day {LIQUIDATION_START_DAY} (LIQUIDATION_START_DAY):\n")
    for product in FOCUS:
        for bucket_name, label in (("pre", f"day<{LIQUIDATION_START_DAY} (gate active)"),
                                    ("post", f"day>={LIQUIDATION_START_DAY} (gate bypassed - irrelevant to sell-gate question)")):
            c = counts[product][bucket_name]
            glut_turns = c["glut_turns"]
            pos = c["glut_and_opp_positive"]
            units = c["glut_and_opp_units"]
            pct = 100 * pos / glut_turns if glut_turns else float("nan")
            mean_units = statistics.mean(units) if units else float("nan")
            print(f"{product} [{label}]: glut turns (shed>{SHED_GLUT_THRESHOLD}) = {glut_turns}, "
                  f"of those opp_yield>0 on {pos} ({pct:.1f}%), mean opp_yield during glut = {mean_units:.2f}")


if __name__ == "__main__":
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    run(n_seeds)
