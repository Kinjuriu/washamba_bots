"""d6-d8 land-gap diagnosis: shed/carried vs $1500 floor, us vs v20.

Usage:
    .venv/Scripts/python.exe experiments/_trace_d7_land.py
    .venv/Scripts/python.exe experiments/_trace_d7_land.py 0 8
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
THROWAWAY = ROOT / "experiments" / "_facts_v20.py"
V20 = str(ROOT / "agents" / "route_v20.py")
SEEDS = (0, 8)
LAND_NEED = 1500


def load_agent():
    spec = importlib.util.spec_from_file_location("facts_v20", THROWAWAY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _obs(raw):
    return dict(raw) if not isinstance(raw, dict) else raw


def shed_carried(priv):
    shed = dict(priv.get("shed") or {})
    carried = {}
    for inv in priv.get("inventories") or []:
        if not isinstance(inv, dict):
            continue
        for k, v in inv.items():
            if v:
                carried[k] = carried.get(k, 0) + int(v)
    return shed, carried


def fmt_inv(d, keys=("FERTILIZER", "WOOL", "MILK", "WHEAT", "MELON", "STRAWBERRY")):
    bits = [f"{k[0]}{int(d.get(k, 0) or 0)}" for k in keys if d.get(k)]
    return ",".join(bits) or "-"


def market_bits(act):
    bits = []
    for o in (act or {}).get("market") or []:
        if o and o[0] in (
            "SELL", "BUY_LAND", "BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT", "HIRE",
        ):
            bits.append(" ".join(str(x) for x in o[:3]))
    return " | ".join(bits) or "-"


def run_seed(mod, seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([str(THROWAWAY), V20])

    print("\n" + "=" * 100)
    print(f"# d6-d8 land gap  seed={seed}")
    print("=" * 100)
    hdr = (
        f"  {'seat':<4} {'dh':>6} {'$':>6} {'gap':>6} {'appG':>4} "
        f"{'shed':<22} {'carry':<18}  market"
    )
    print(hdr)

    prev = [None, None]
    land_days = [{}, {}]
    herd_eod = [{}, {}]
    banks = [0, 0]
    for step in env.steps:
        for seat in (0, 1):
            raw = step[seat]
            obs = _obs(raw.observation)
            act = raw.get("action") if hasattr(raw, "get") else None
            act = act or getattr(raw, "action", None) or {}
            if prev[seat] is None:
                prev[seat] = obs
                continue
            p = prev[seat]
            day = p.get("day", 0)
            hour = p.get("hour", 0)
            farm = (p.get("farms") or [{}, {}])[seat]
            priv = p.get("private") or {}
            if hour == 23:
                n = 0
                for row in farm.get("tiles") or []:
                    for t in row:
                        if isinstance(t, dict) and t.get("animal"):
                            n += 1
                herd_eod[seat][day] = n
            if any(o and o[0] == "BUY_LAND" for o in act.get("market") or []):
                land_days[seat].setdefault("days", []).append((day, hour))
            if 6 <= day <= 8 and (hour in (0, 1, 12, 23) or any(
                o and o[0] in ("BUY_LAND", "SELL", "BUY_SEED", "BUY_ANIMAL")
                for o in act.get("market") or []
            )):
                shed, carried = shed_carried(priv)
                cash = float(farm.get("money", 0))
                apply_gap = mod.count_fertilize_demand(farm, day) if seat == 0 else -1
                print(
                    f"  {seat:<4} d{day}h{hour:02d} {cash:6.0f} {cash - LAND_NEED:6.0f} "
                    f"{apply_gap:4d} {fmt_inv(shed):<22} {fmt_inv(carried):<18}  "
                    f"{market_bits(act)}"
                )
            prev[seat] = obs

    last = env.steps[-1]
    for seat in (0, 1):
        obs = _obs(last[seat].observation)
        farm = (obs.get("farms") or [{}, {}])[seat]
        banks[seat] = int(farm.get("money") or 0)
        n = 0
        for row in farm.get("tiles") or []:
            for t in row:
                if isinstance(t, dict) and t.get("animal"):
                    n += 1
        print(
            f"  seat{seat} bank={banks[seat]} land={land_days[seat].get('days')} "
            f"herd_d6-11={[herd_eod[seat].get(d) for d in range(6, 12)]} end={n}"
        )


def main():
    mod = load_agent()
    seeds = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(SEEDS)
    for seed in seeds:
        run_seed(mod, seed)


if __name__ == "__main__":
    main()
