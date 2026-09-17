"""Trace d9-11 SW idle: money, seeds, sw_slots. Throwaway."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from kaggle_environments import make

AGENT = ROOT / "_facts_v20.py"
SEEDS = [0, 8]


def run_traced(seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([str(AGENT), "starter"])
    steps = env.steps
    prev = None
    rows = []
    for step in steps:
        obs = step[0].observation
        src = prev if prev is not None else obs
        day = src.get("day", 0)
        hour = src.get("hour", 0)
        if 9 <= day <= 11:
            priv = obs.get("private") or {}
            seeds = priv.get("seeds") or {}
            farm = (src.get("farms") or [{}])[0]
            money = farm.get("money", 0)
            unlocked = farm.get("unlocked_quadrants") or ["NW"]
            sw_empty = 0
            tiles = farm.get("tiles") or []
            bs = len(tiles) or 10
            half = bs // 2
            for y, row in enumerate(tiles):
                for x, t in enumerate(row):
                    if t is not None:
                        continue
                    q = ("N" if y < half else "S") + ("W" if x < half else "E")
                    if q == "SW":
                        sw_empty += 1
            if hour in (0, 12, 23):
                rows.append({
                    "day": day, "hour": hour, "money": money,
                    "straw_seed": seeds.get("STRAWBERRY", 0),
                    "melon_seed": seeds.get("MELON", 0),
                    "unlocked": list(unlocked),
                    "sw_empty": sw_empty,
                })
        prev = obs
    return rows


def main():
    for seed in SEEDS:
        print(f"\n=== seed {seed} ===")
        for r in run_traced(seed):
            print(
                f"  d{r['day']}h{r['hour']:02d} money={r['money']:5.0f} "
                f"STRAW_seed={r['straw_seed']:2d} MELON_seed={r['melon_seed']:2d} "
                f"SW_empty={r['sw_empty']:2d} unlocked={r['unlocked']}"
            )


if __name__ == "__main__":
    main()
