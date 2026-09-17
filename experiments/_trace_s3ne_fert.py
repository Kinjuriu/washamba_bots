"""S3ne vs route_v20: FERTILIZE on STRAW, SELL FERT, shed stock.

Usage:
    .venv/Scripts/python.exe experiments/_trace_s3ne_fert.py
    .venv/Scripts/python.exe experiments/_trace_s3ne_fert.py 0 8
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import V20, _obs, analyze_episode  # noqa: E402

AGENT = str(ROOT / "experiments" / "_facts_v20_s3_ne.py")

# Engine STRAW: first_yield_day=10, interval=2, max_yield=4.
# wants_fertilizer: age 7..15 (cover 3 days, 2 ticks).
STRAW_FERT_AGE_LO = 7
STRAW_FERT_AGE_HI = 15


def _unit_spots(farm, act):
    farmer = farm.get("farmer") or [0, 0]
    spots = [(0, int(farmer[0]), int(farmer[1]))]
    hands = farm.get("hands") or []
    acts_h = act.get("hands") or []
    for i, hand in enumerate(hands):
        if isinstance(hand, (list, tuple)) and len(hand) == 2:
            spots.append((i + 1, int(hand[0]), int(hand[1])))
    while len(acts_h) > len(spots) - 1:
        spots.append((len(spots), 0, 0))
    return spots


def _actions(act):
    farmer = act.get("farmer") or ["PASS"]
    hands = act.get("hands") or []
    if not isinstance(hands, list):
        hands = []
    return [farmer, *hands]


def _tile(farm, x, y):
    tiles = farm.get("tiles") or []
    if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]):
        return tiles[y][x]
    return None


def _straw_tiles(farm, day):
    out = []
    for y, row in enumerate(farm.get("tiles") or []):
        for x, t in enumerate(row):
            if not isinstance(t, dict):
                continue
            if t.get("kind") != "PLANT" or t.get("crop") != "STRAWBERRY":
                continue
            planted = t.get("planted_day", day)
            age = day - planted
            covered = t.get("fertilized_until_day", -1) >= day
            wants = (STRAW_FERT_AGE_LO <= age <= STRAW_FERT_AGE_HI) and not covered
            out.append((x, y, age, covered, wants, planted))
    return out


def run_seed(seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([AGENT, V20])
    cash = analyze_episode(env.steps, us_seat=0)

    fert_by_crop = [Counter(), Counter()]
    fert_day_straw = [Counter(), Counter()]
    fert_day_other = [Counter(), Counter()]
    collect = [Counter(), Counter()]
    plant_straw = [Counter(), Counter()]
    straw_eod = [{}, {}]
    straw_want_eod = [{}, {}]
    straw_cov_eod = [{}, {}]
    shed_fert_eod = [{}, {}]
    applies_per_plant = [Counter(), Counter()]  # key planted_day,x,y -> n
    want_hours = [Counter(), Counter()]  # day -> hours with >=1 wanting STRAW
    apply_when_want = [Counter(), Counter()]

    for step in env.steps:
        for p in (0, 1):
            obs = _obs(step[p].observation)
            act = step[p].action or {}
            day = int(obs.get("day", 0))
            hour = int(obs.get("hour", 0))
            farm = (obs.get("farms") or [{}])[p]
            priv = obs.get("private") or {}
            tiles_straw = _straw_tiles(farm, day)
            n_straw = len(tiles_straw)
            n_want = sum(1 for t in tiles_straw if t[4])
            n_cov = sum(1 for t in tiles_straw if t[3])
            if n_want:
                want_hours[p][day] += 1
            spots = {idx: (x, y) for idx, x, y in _unit_spots(farm, act)}
            acts = _actions(act)
            straw_apply = 0
            for i, a in enumerate(acts):
                if not a:
                    continue
                if a[0] == "PLANT" and len(a) > 1 and a[1] == "STRAWBERRY":
                    plant_straw[p][day] += 1
                if a[0] == "COLLECT_FERTILIZER":
                    collect[p][day] += 1
                if a[0] != "FERTILIZE":
                    continue
                xy = spots.get(i)
                if xy is None:
                    fert_by_crop[p]["?"] += 1
                    continue
                t = _tile(farm, xy[0], xy[1])
                crop = t.get("crop") if isinstance(t, dict) else "?"
                fert_by_crop[p][crop or "?"] += 1
                if crop == "STRAWBERRY":
                    fert_day_straw[p][day] += 1
                    straw_apply += 1
                    planted = t.get("planted_day", day)
                    applies_per_plant[p][(planted, xy[0], xy[1])] += 1
                else:
                    fert_day_other[p][day] += 1
            if n_want:
                apply_when_want[p][day] += straw_apply
            if hour == 23:
                straw_eod[p][day] = n_straw
                straw_want_eod[p][day] = n_want
                straw_cov_eod[p][day] = n_cov
                shed_fert_eod[p][day] = int((priv.get("shed") or {}).get("FERTILIZER", 0) or 0)

    return {
        "seed": seed,
        "cash": cash,
        "fert_by_crop": fert_by_crop,
        "fert_day_straw": fert_day_straw,
        "fert_day_other": fert_day_other,
        "collect": collect,
        "plant_straw": plant_straw,
        "straw_eod": straw_eod,
        "straw_want_eod": straw_want_eod,
        "straw_cov_eod": straw_cov_eod,
        "shed_fert_eod": shed_fert_eod,
        "applies_per_plant": applies_per_plant,
        "want_hours": want_hours,
        "apply_when_want": apply_when_want,
        "bank": (env.steps[-1][0].reward, env.steps[-1][1].reward),
    }


def _usd(cash, seat, day, cat):
    src = cash["by_day_us"] if seat == "us" else cash["by_day_v20"]
    return src[day].get(cat, 0)


def _units(cash, seat, day, cat):
    key = "by_day_units_us" if seat == "us" else "by_day_units_v20"
    return (cash.get(key) or {}).get(day, {}).get(cat, 0)


def print_seed(rep):
    seed = rep["seed"]
    cash = rep["cash"]
    print("\n" + "#" * 80)
    print(
        f"# S3ne fert  seed={seed}  bank us={rep['bank'][0]:.0f}  "
        f"v20={rep['bank'][1]:.0f}"
    )
    print("#" * 80)
    print("  FERTILIZE by crop  us / v20")
    crops = sorted(set(rep["fert_by_crop"][0]) | set(rep["fert_by_crop"][1]))
    for c in crops:
        print(
            f"    {c:<12} {rep['fert_by_crop'][0][c]:5d} / "
            f"{rep['fert_by_crop'][1][c]:5d}"
        )
    print(
        f"  COLLECT season us={sum(rep['collect'][0].values())} "
        f"v20={sum(rep['collect'][1].values())}"
    )
    print(
        f"  SELL_FERT season $ us={cash['season_us'].get('SELL_FERTILIZER', 0):.0f} "
        f"v20={cash['season_v20'].get('SELL_FERTILIZER', 0):.0f}  "
        f"u us={cash['units_us'].get('SELL_FERTILIZER', 0):.0f} "
        f"v20={cash['units_v20'].get('SELL_FERTILIZER', 0):.0f}"
    )
    print(
        f"  BUY_FERT u us={cash['units_us'].get('BUY_PRODUCT_FERTILIZER', 0):.0f} "
        f"v20={cash['units_v20'].get('BUY_PRODUCT_FERTILIZER', 0):.0f}"
    )
    print(
        f"  PLANT STRAW us={sum(rep['plant_straw'][0].values())} "
        f"v20={sum(rep['plant_straw'][1].values())}"
    )

    us_apps = list(rep["applies_per_plant"][0].values())
    v_apps = list(rep["applies_per_plant"][1].values())
    print("  STRAW plants that got >=1 FERTILIZE (keyed planted_day,x,y)")
    print(
        f"    us n={len(us_apps)} applies={sum(us_apps)} "
        f"mean/plant={sum(us_apps)/len(us_apps) if us_apps else 0:.2f} "
        f"max={max(us_apps) if us_apps else 0}"
    )
    print(
        f"    v20 n={len(v_apps)} applies={sum(v_apps)} "
        f"mean/plant={sum(v_apps)/len(v_apps) if v_apps else 0:.2f} "
        f"max={max(v_apps) if v_apps else 0}"
    )
    hist_u = Counter(us_apps)
    hist_v = Counter(v_apps)
    print(f"    us apply-count hist {dict(sorted(hist_u.items()))}")
    print(f"    v20 apply-count hist {dict(sorted(hist_v.items()))}")

    print(
        f"\n  {'d':>3} {'strawF':>7} {'want':>6} {'cov':>5} {'FERT_S':>8} "
        f"{'FERT_o':>6} {'SELL_u':>8} {'shedF':>5} {'COLL':>5}  | v20 "
        f"{'straw':>5} {'FS':>4} {'SELL':>5} {'shed':>4}"
    )
    for day in range(30):
        su = rep["straw_eod"][0].get(day, 0)
        sv = rep["straw_eod"][1].get(day, 0)
        fu = rep["fert_day_straw"][0][day]
        fv = rep["fert_day_straw"][1][day]
        sell_u = _units(cash, "us", day, "SELL_FERTILIZER")
        sell_v = _units(cash, "v20", day, "SELL_FERTILIZER")
        if not (su or sv or fu or fv or sell_u or sell_v or rep["plant_straw"][0][day]):
            continue
        print(
            f"  {day:3d} {su:3d}/{sv:<3d} {rep['straw_want_eod'][0].get(day, 0):6d} "
            f"{rep['straw_cov_eod'][0].get(day, 0):5d} "
            f"{fu:3d}/{fv:<3d} {rep['fert_day_other'][0][day]:6d} "
            f"{sell_u:4.0f}/{sell_v:<3.0f} {rep['shed_fert_eod'][0].get(day, 0):5d} "
            f"{rep['collect'][0][day]:5d}  | "
            f"{sv:5d} {fv:4d} {sell_v:5.0f} {rep['shed_fert_eod'][1].get(day, 0):4d}"
        )


def main():
    args = sys.argv[1:]
    seeds = [int(x) for x in args if x.lstrip("-").isdigit()] or [0, 8]
    for seed in seeds:
        print(f"running S3ne fert seed {seed}...", flush=True)
        print_seed(run_seed(seed))


if __name__ == "__main__":
    main()
