"""S3 d5–d6 role snapshot vs route_v20. Contested, not starter.

Prints hourly cash / wool (shed vs held) / owned vs placed / unfed remaining,
plus who holds wool and Manhattan distance to shed. Used to fill HORIZON
before the fact-33 roles card.

Usage:
    .venv/Scripts/python.exe experiments/_trace_d5_d6_roles.py
    .venv/Scripts/python.exe experiments/_trace_d5_d6_roles.py 0 8
"""
from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import V20  # noqa: E402

S3 = ROOT / "experiments" / "_facts_v20_s3.py"
S3ROLES = ROOT / "experiments" / "_facts_v20_s3_roles.py"


def _agent_path(argv):
    for a in argv:
        p = Path(a)
        if p.suffix == ".py" and p.exists():
            return p.resolve()
        cand = ROOT / "experiments" / a
        if cand.suffix == ".py" and cand.exists():
            return cand.resolve()
        cand = ROOT / a
        if cand.suffix == ".py" and cand.exists():
            return cand.resolve()
    return S3ROLES if S3ROLES.exists() else S3


def load_mod(path):
    spec = importlib.util.spec_from_file_location("facts_throwaway", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _act(raw):
    return (raw.get("action") if hasattr(raw, "get") else None) or getattr(
        raw, "action", None
    ) or {}


def _obs(raw):
    obs = raw.observation
    if isinstance(obs, dict):
        return obs
    try:
        return dict(obs)
    except Exception:
        return obs


def unfed_tiles(farm):
    out = []
    for y, row in enumerate(farm.get("tiles") or []):
        for x, t in enumerate(row):
            if isinstance(t, dict) and t.get("animal") and not t.get("fed_today"):
                out.append((x, y, t.get("animal")))
    return out


def placed_count(farm):
    n = 0
    for row in farm.get("tiles") or []:
        for t in row:
            if isinstance(t, dict) and t.get("animal"):
                n += 1
    return n


def run_seed(seed, agent=S3):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([str(agent), V20])
    steps = env.steps
    mod = load_mod(agent)

    first_land = None
    d5_buy = []
    rows = []
    prev = None
    for step in steps:
        obs = _obs(step[0])
        act = _act(step[0])
        if prev is None:
            prev = obs
            continue
        day = prev.get("day", 0)
        hour = prev.get("hour", 0)
        farm = (prev.get("farms") or [{}])[0]
        priv = prev.get("private") or {}
        board = len(farm.get("tiles") or []) or 10
        market = act.get("market") or []

        if first_land is None and any(o and o[0] == "BUY_LAND" for o in market):
            first_land = (day, hour)
        if day == 5:
            for o in market:
                if o and o[0] == "BUY_ANIMAL":
                    d5_buy.append((hour, o[1], o[2] if len(o) > 2 else 1))

        if 5 <= day <= 6:
            owned = mod.count_owned_animals(farm, priv, board)
            placed = placed_count(farm)
            unfed = unfed_tiles(farm)
            shed_wool = int((priv.get("shed") or {}).get("WOOL", 0) or 0)
            farmer = farm.get("farmer") or [0, 0]
            spots = [(0, farmer[0], farmer[1])]
            for i, hand in enumerate(farm.get("hands") or []):
                if isinstance(hand, (list, tuple)) and len(hand) == 2:
                    spots.append((i + 1, hand[0], hand[1]))
            holders = []
            crew = []
            held_wool = 0
            shed_wheat = int((priv.get("shed") or {}).get("WHEAT", 0) or 0)
            for idx, ux, uy in spots:
                inv = mod.unit_inventory(priv, idx)
                w = int(inv.get("WOOL", 0) or 0)
                wheat = int(inv.get("WHEAT", 0) or 0)
                held_wool += w
                sx, sy = mod.nearest_shed_tile(ux, uy, board)
                dist = abs(ux - sx) + abs(uy - sy)
                on_unfed = any((ux, uy) == (ax, ay) for ax, ay, _ in unfed)
                line = (
                    f"u{idx}@({ux},{uy}) wool={w} wheat={wheat} "
                    f"dShed={dist} unfed={int(on_unfed)}"
                )
                crew.append(line)
                if w > 0:
                    holders.append(line)
            reserved = owned * mod.MIN_WHEAT_RESERVE_FOR_FEEDING
            shops = (prev.get("town") or {}).get("unlocked_shops") or ()
            post = mod._estimated_post_sell_cash(
                farm, priv, prev.get("market") or {}, day,
                reserved_wheat=reserved, unlocked_shops=shops,
                sell_fert_for_buy=True, board_size=board,
            )
            rows.append({
                "day": day, "hour": hour,
                "pre": float(farm.get("money", 0)),
                "post": post,
                "owned": owned,
                "placed": placed,
                "unfed": len(unfed),
                "shed_wool": shed_wool,
                "held_wool": held_wool,
                "holders": holders,
                "crew": crew,
                "n_units": len(spots),
                "shed_wheat": shed_wheat,
                "buy_a": [o for o in market if o and o[0] == "BUY_ANIMAL"],
                "land": any(o and o[0] == "BUY_LAND" for o in market),
                "sell_wool": any(
                    o and o[0] == "SELL" and len(o) > 1 and o[1] == "WOOL"
                    for o in market
                ),
            })
        prev = obs

    bank = steps[-1][0].reward
    v20 = steps[-1][1].reward
    print("\n" + "#" * 88)
    print(
        f"# d5-d6 roles  agent={Path(agent).name}  seed={seed}  "
        f"bank us={bank:.0f}  v20={v20:.0f}"
    )
    print("#" * 88)
    print(f"  first BUY_LAND={first_land}  d5 BUY_ANIMAL={d5_buy}")
    print(
        f"  {'d':>3} {'h':>3} {'pre':>6} {'post':>6} {'own/pl':>7} "
        f"{'unfed':>5} {'woolS/H':>8} land wS holders"
    )
    for r in rows:
        print(
            f"  {r['day']:3d} {r['hour']:3d} {r['pre']:6.0f} {r['post']:6.0f} "
            f"{r['owned']:2d}/{r['placed']:<2d} {r['unfed']:5d} "
            f"{r['shed_wool']:3d}/{r['held_wool']:<3d} "
            f"{int(r['land']):4d} {int(r['sell_wool']):2d} "
            f"{r['buy_a'] or '-'}"
        )
        if r["day"] == 6 and r["hour"] in (0, 6, 7, 8):
            print(f"       n_units={r['n_units']} shedWHEAT={r['shed_wheat']}")
            for c in r["crew"]:
                print(f"       {c}")
        elif r["holders"] and (
            r["hour"] in (0, 1, 4, 6, 8, 12, 16, 23)
            or r["land"] or r["held_wool"] >= 4
        ):
            for h in r["holders"]:
                print(f"       {h}")
    return bank, v20


def main():
    agent = _agent_path(sys.argv[1:])
    seeds = [int(x) for x in sys.argv[1:] if x.lstrip("-").isdigit()] or [0, 8]
    for seed in seeds:
        print(f"running {agent.name} seed {seed}...", flush=True)
        run_seed(seed, agent=agent)


if __name__ == "__main__":
    main()
