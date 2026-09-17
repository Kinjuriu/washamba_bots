"""HORIZON S4-lead d6 wool drawer vs route_v20.

Every d6 hour, both seats: sheep tile yield / care bank, HARVEST,
wool holders + dist-to-shed, assigned runner (us), PLACE, shed vs held,
SELL. Names on-tile vs never-produced vs non-runner held before coding.

Usage:
    .venv/Scripts/python.exe experiments/_trace_horizon_s4_lead_d6_wool.py
    .venv/Scripts/python.exe experiments/_trace_horizon_s4_lead_d6_wool.py 0 8
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import V20, _obs, analyze_episode  # noqa: E402

S4_LEAD = ROOT / "experiments" / "_facts_v20_s4_lead.py"


def load_throwaway(path):
    spec = importlib.util.spec_from_file_location("facts_s4_lead", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _act(raw):
    return (raw.get("action") if hasattr(raw, "get") else None) or getattr(
        raw, "action", None
    ) or {}


def _unit_actions(act):
    farmer = act.get("farmer") or ["PASS"]
    hands = act.get("hands") or []
    if not isinstance(hands, list):
        hands = []
    return [farmer, *hands]


def _sheep_tiles(farm):
    out = []
    for y, row in enumerate(farm.get("tiles") or []):
        for x, t in enumerate(row):
            if isinstance(t, dict) and t.get("animal") == "SHEEP":
                out.append({
                    "x": x,
                    "y": y,
                    "yield": int(t.get("yield_units", 0) or 0),
                    "care": int(t.get("pending_care_bonus", 0) or 0),
                    "cared": bool(t.get("cared_today")),
                    "fed": bool(t.get("fed_today")),
                })
    return out


def _holders(farm, private, board, mod):
    out = []
    for idx, ux, uy in mod.list_units(farm):
        inv = mod.unit_inventory(private, idx)
        w = int(inv.get("WOOL", 0) or 0)
        if w <= 0:
            continue
        sx, sy = mod.nearest_shed_tile(ux, uy, board)
        dist = abs(ux - sx) + abs(uy - sy)
        adj = mod.is_shed_adjacent(ux, uy, board)
        out.append({
            "idx": idx,
            "xy": (ux, uy),
            "wool": w,
            "dist": dist,
            "adj": adj,
        })
    return out


def _harvest_n(act):
    return sum(1 for a in _unit_actions(act) if a and a[0] == "HARVEST")


def _place_wool(act):
    n_ops = 0
    qty = 0
    for a in _unit_actions(act):
        if not (isinstance(a, list) and a and a[0] == "PLACE"):
            continue
        if len(a) > 1 and a[1] == "WOOL":
            n_ops += 1
            qty += int(a[2] if len(a) > 2 else 1)
    return n_ops, qty


def _sell_wool(act):
    n = 0
    for o in act.get("market") or []:
        if o and o[0] == "SELL" and len(o) > 1 and o[1] == "WOOL":
            n += int(o[2] if len(o) > 2 else 1)
    return n


def run_seed(seed, agent=S4_LEAD):
    mod = load_throwaway(agent)
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([str(agent), V20])
    steps = env.steps
    cash = analyze_episode(steps, us_seat=0)

    hours = [[], []]
    prev = [None, None]
    for step in steps:
        obs_list = [_obs(step[p].observation) for p in (0, 1)]
        acts = [_act(step[p]) for p in (0, 1)]
        if prev[0] is None:
            prev = obs_list
            continue
        src = prev
        day = int(src[0].get("day", 0))
        hour = int(src[0].get("hour", 0))
        if day != 6:
            prev = obs_list
            continue
        for p in (0, 1):
            farm = (src[p].get("farms") or [{}])[p]
            priv = src[p].get("private") or {}
            farm_after = (obs_list[p].get("farms") or [{}])[p]
            priv_after = obs_list[p].get("private") or {}
            act = acts[p]
            board = len(farm.get("tiles") or []) or 10
            sheep = _sheep_tiles(farm)
            sheep_after = _sheep_tiles(farm_after)
            holders = _holders(farm, priv, board, mod)
            holders_after = _holders(farm_after, priv_after, board, mod)
            runner = None
            runner_adj = False
            if p == 0:
                runner = mod.assign_wool_runner(farm, priv, board, day)
                if runner is not None:
                    for h in holders:
                        if h["idx"] == runner:
                            runner_adj = h["adj"]
                            break
                    else:
                        for idx, ux, uy in mod.list_units(farm):
                            if idx == runner:
                                runner_adj = mod.is_shed_adjacent(ux, uy, board)
                                break
            place_ops, place_qty = _place_wool(act)
            land = any(o and o[0] == "BUY_LAND" for o in (act.get("market") or []))
            hours[p].append({
                "hour": hour,
                "pre": float(farm.get("money", 0)),
                "post": float(farm_after.get("money", 0)),
                "shed": int((priv.get("shed") or {}).get("WOOL", 0) or 0),
                "held": sum(h["wool"] for h in holders),
                "shed_after": int((priv_after.get("shed") or {}).get("WOOL", 0) or 0),
                "held_after": sum(h["wool"] for h in holders_after),
                "tile_y": sum(s["yield"] for s in sheep),
                "tile_y_after": sum(s["yield"] for s in sheep_after),
                "care": [s["care"] for s in sheep],
                "sheep": sheep,
                "sheep_after": sheep_after,
                "holders": holders,
                "holders_after": holders_after,
                "runner": runner,
                "runner_adj": runner_adj,
                "harvest": _harvest_n(act),
                "place_ops": place_ops,
                "place_qty": place_qty,
                "sell": _sell_wool(act),
                "land": land,
                "pending": mod.pending_first_land(farm),
            })
        prev = obs_list

    return {
        "seed": seed,
        "cash": cash,
        "hours": hours,
        "bank_us": steps[-1][0].reward,
        "bank_v20": steps[-1][1].reward,
    }


def _fmt_sheep(sheep):
    if not sheep:
        return "-"
    parts = []
    for s in sheep:
        parts.append(
            f"({s['x']},{s['y']})y={s['yield']}c={s['care']}"
            f"{'F' if s['fed'] else ''}{'C' if s['cared'] else ''}"
        )
    return " ".join(parts)


def _fmt_holders(holders):
    if not holders:
        return "-"
    return " ".join(
        f"u{h['idx']}@{h['xy']}w={h['wool']}d={h['dist']}"
        f"{' adj' if h['adj'] else ''}"
        for h in holders
    )


def _print_seat(label, rows):
    print(f"\n--- d6 wool every hour {label} ---")
    print(
        f"  {'h':>3} {'$':>6} {'S/H':>6} {'tileY':>5} {'Hrv':>3} "
        f"{'Plc':>5} {'sell':>4} {'run':>4} adj pend land"
    )
    sell_total = 0
    h0 = rows[0] if rows else None
    last_sell = None
    non_runner_held = []
    for r in rows:
        sell_total += r["sell"]
        if r["sell"] or r["place_ops"]:
            last_sell = r
        extra = [h for h in r["holders"] if h["idx"] != r["runner"] and r["runner"] is not None]
        if extra and r["place_ops"]:
            non_runner_held.append((r["hour"], extra))
        mark = []
        if r["land"]:
            mark.append("LAND")
        if r["hour"] == 0:
            mark.append("H0")
        print(
            f"  {r['hour']:3d} {r['pre']:6.0f} {r['shed']:2d}/{r['held']:<2d} "
            f"{r['tile_y']:5d} {r['harvest']:3d} "
            f"{r['place_qty']:2d}x{r['place_ops']:<1d} {r['sell']:4d} "
            f"{str(r['runner'] if r['runner'] is not None else '-'):>4} "
            f"{int(r['runner_adj']):3d} {int(r['pending']):4d} {int(r['land']):4d} "
            f"{' '.join(mark)}"
        )
        interesting = (
            r["hour"] in (0, 4, 5, 7, 10, 11, 23)
            or r["tile_y"] > 0
            or r["harvest"]
            or r["place_ops"]
            or r["sell"]
            or r["holders"]
            or r["land"]
        )
        if interesting:
            print(f"       sheep {_fmt_sheep(r['sheep'])}")
            print(f"       hold  {_fmt_holders(r['holders'])}")
            if r["harvest"] or r["place_ops"] or r["sell"]:
                print(
                    f"       after tileY={r['tile_y_after']} "
                    f"S/H {r['shed_after']}/{r['held_after']} "
                    f"sheep {_fmt_sheep(r['sheep_after'])} "
                    f"hold {_fmt_holders(r['holders_after'])}"
                )
    print(f"  d6 SELL_WOOL order qty {sell_total}")
    if h0:
        print(
            f"  h0 tile yield sum={h0['tile_y']} sheep={_fmt_sheep(h0['sheep'])} "
            f"care={[s['care'] for s in h0['sheep']]}"
        )
    if last_sell:
        print(
            f"  after last PLACE/SELL h{last_sell['hour']}: "
            f"tileY {last_sell['tile_y']}->{last_sell['tile_y_after']} "
            f"held {last_sell['held']}->{last_sell['held_after']}"
        )
    eod = rows[-1] if rows else None
    if eod:
        print(
            f"  EOD d6 tileY={eod['tile_y_after']} S/H {eod['shed_after']}/{eod['held_after']} "
            f"sheep {_fmt_sheep(eod['sheep_after'])}"
        )
    if non_runner_held:
        print(f"  non-runner held on PLACE hours: {non_runner_held}")
    else:
        print("  non-runner held on PLACE hours: none")


def _verdict(us, v20):
    h0u = us[0] if us else None
    h0v = v20[0] if v20 else None
    uy = h0u["tile_y"] if h0u else 0
    vy = h0v["tile_y"] if h0v else 0
    leftover_tile = 0
    leftover_held = 0
    for r in us:
        leftover_tile = r["tile_y_after"]
        leftover_held = r["held_after"]
    print("\n--- drawer ---")
    print(f"  h0 tile yield us={uy} v20={vy}")
    print(f"  EOD leftover on tiles us={leftover_tile} held={leftover_held}")
    if uy >= 12 and leftover_tile >= 3:
        print("  PICK: on-tile — extra HARVEST runner after feed, then PLACE")
    elif uy >= 12 and leftover_tile == 0:
        extra = False
        for r in us:
            others = [h for h in r["holders"] if r["runner"] is not None and h["idx"] != r["runner"]]
            if others and r["place_ops"]:
                extra = True
                break
        if extra:
            print("  PICK: non-runner held — shed-adj PLACE for any holder")
        else:
            print("  PICK: produced 12 then sold/cleared; re-check hours")
    elif uy <= 9 and leftover_tile == 0:
        print(
            "  PICK: never-produced (h0 yield already "
            f"{uy} not 12) — drop wool leftover; do seed restock cap"
        )
    else:
        print(
            f"  PICK: mixed (h0 us={uy} leftover_tile={leftover_tile} "
            f"leftover_held={leftover_held}) — read the hours"
        )


def print_seed(rep):
    cash = rep["cash"]
    print("\n" + "#" * 88)
    print(
        f"# HORIZON S4-lead d6 wool  seed={rep['seed']}  "
        f"bank us={rep['bank_us']:.0f}  v20={rep['bank_v20']:.0f}  "
        f"SELL_WOOL $ us={cash['by_day_us'][6].get('SELL_WOOL', 0):.0f} "
        f"v20={cash['by_day_v20'][6].get('SELL_WOOL', 0):.0f}  "
        f"u {cash.get('by_day_units_us', {}).get(6, {}).get('SELL_WOOL', 0)}/"
        f"{cash.get('by_day_units_v20', {}).get(6, {}).get('SELL_WOOL', 0)}"
    )
    print("#" * 88)
    _print_seat("us", rep["hours"][0])
    _print_seat("v20", rep["hours"][1])
    _verdict(rep["hours"][0], rep["hours"][1])


def main():
    seeds = [int(x) for x in sys.argv[1:] if x.lstrip("-").isdigit()] or [0, 8]
    for seed in seeds:
        print(f"running {S4_LEAD.name} seed {seed}...", flush=True)
        print_seed(run_seed(seed, agent=S4_LEAD))


if __name__ == "__main__":
    main()
