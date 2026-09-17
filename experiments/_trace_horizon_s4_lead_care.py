"""HORIZON S4-lead d0–d5 sheep FEED/CARE/COLLECT vs route_v20.

First-wool night: sheep first_yield_day=6, base 1, max_held 6.
d6h0 yield = min(6, 1 + pending_care from fed+cared nights before payout).
Day-5 CARE accrues after that payout. Snapshot before a CARE fact.

Usage:
    .venv/Scripts/python.exe experiments/_trace_horizon_s4_lead_care.py
    .venv/Scripts/python.exe experiments/_trace_horizon_s4_lead_care.py 0 8
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import V20, _obs  # noqa: E402

S4_LEAD = ROOT / "experiments" / "_facts_v20_s4_lead.py"


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


def _list_units(farm):
    farmer = farm.get("farmer") or [0, 0]
    spots = [(0, int(farmer[0]), int(farmer[1]))]
    for i, hand in enumerate(farm.get("hands") or []):
        if isinstance(hand, (list, tuple)) and len(hand) == 2:
            spots.append((i + 1, int(hand[0]), int(hand[1])))
    return spots


def _sheep(farm):
    out = []
    for y, row in enumerate(farm.get("tiles") or []):
        for x, t in enumerate(row):
            if isinstance(t, dict) and t.get("animal") == "SHEEP":
                out.append({
                    "xy": (x, y),
                    "yield": int(t.get("yield_units", 0) or 0),
                    "care": int(t.get("pending_care_bonus", 0) or 0),
                    "cared": bool(t.get("cared_today")),
                    "fed": bool(t.get("fed_today")),
                    "fert": bool(t.get("fertilizer_available")),
                    "placed": int(t.get("placed_day", -1)),
                    "unfed": int(t.get("consecutive_unfed", 0) or 0),
                })
    out.sort(key=lambda s: s["xy"])
    return out


def _on_sheep(units, sheep):
    at = {s["xy"]: [] for s in sheep}
    for idx, ux, uy in units:
        if (ux, uy) in at:
            at[(ux, uy)].append(idx)
    return at


def print_seed(rep):
    print("\n" + "#" * 88)
    print(
        f"# HORIZON CARE  agent={rep['agent']}  seed={rep['seed']}  "
        f"bank us={rep['bank_us']:.0f}  v20={rep['bank_v20']:.0f}"
    )
    print("#" * 88)
    for p, label in ((0, "us"), (1, "v20")):
        recs = rep["days"][p]
        ph = rep["placed_hour"][p]
        d6 = rep["d6h0"][p] or []
        print(f"\n--- {label} ---")
        print(
            f"  d6h0 yield "
            + (" ".join(
                f"{s['xy']} y={s['yield']} c={s['care']}"
                for s in d6
            ) or "(none)")
            + f"  sum={sum(s['yield'] for s in d6)}"
        )
        xys = sorted(recs.keys())
        print(
            f"  {'xy':>7} {'pl':>6} {'d':>2} "
            f"{'F':>2} {'C':>2} {'Col':>3} "
            f"{'fed':>3} {'crd':>3} {'pAM':>3} {'yAM':>3}  hours / stall"
        )
        care_nights = {}
        for xy in xys:
            rec = recs[xy]
            pl = ph.get(xy)
            pl_s = f"d{pl[0]}h{pl[1]}" if pl else "?"
            placed_day = rec.get("placed")
            if placed_day is None and pl:
                placed_day = pl[0]
            by_day = defaultdict(lambda: {"F": [], "C": [], "Col": [], "H": []})
            for kind, key in (
                ("F", "feed_h"),
                ("C", "care_h"),
                ("Col", "collect_h"),
                ("H", "harvest_h"),
            ):
                for item in rec[key]:
                    if isinstance(item, tuple):
                        d, h = item
                        by_day[d][kind].append(h)
            mornings = rec.get("mornings") or {}
            h23s = rec.get("h23s") or {}
            nights_ok = []
            for d in range(6):
                if placed_day is not None and d < int(placed_day):
                    continue
                b = by_day[d]
                m = mornings.get(d)  # morning of d+1
                h23 = h23s.get(d)
                fed = 1 if b["F"] else (1 if h23 and h23.get("fed") else 0)
                crd = 1 if b["C"] else (1 if h23 and h23.get("cared") else 0)
                # Night d accrues if fed+cared that day. Production is end of
                # d5; nights 0-4 feed the d6h0 bonus (if placed_day==0).
                if fed and crd:
                    nights_ok.append(d)
                stall = ""
                if b["Col"] and not b["C"]:
                    stall = " COLLECT-no-CARE"
                elif b["Col"] and b["C"] and min(b["Col"]) < min(b["C"]):
                    stall = " COLLECT-then-CARE"
                elif b["F"] and not b["C"] and not b["Col"]:
                    stall = " FEED-no-CARE"
                elif not b["F"] and not b["C"]:
                    stall = " MISS"
                pam = m["care"] if m else -1
                yam = m["yield"] if m else -1
                print(
                    f"  {str(xy):>7} {pl_s:>6} {d:2d} "
                    f"{len(b['F']):2d} {len(b['C']):2d} {len(b['Col']):3d} "
                    f"{fed:3d} {crd:3d} {pam:3d} {yam:3d} "
                    f"F{b['F']} C{b['C']} Col{b['Col']}{stall}"
                )
            care_nights[xy] = nights_ok
            pre_pay = [d for d in nights_ok if d <= 4]
            print(
                f"         fed+cared nights {nights_ok}  "
                f"pre-payout (d0-4) n={len(pre_pay)} {pre_pay}  "
                f"expect yield min(6,1+{len(pre_pay)})={min(6, 1 + len(pre_pay))}"
            )
        print("  CARE nights vs v20: see other seat")
        wheat = rep["wheat"][p]
        print(
            f"  {'d':>2} {'$0':>5} {'shed0':>5} {'held0':>5} {'buyW':>4} "
            f"{'pkW':>3} {'FEED':>4} {'wh':>4}  buy hours"
        )
        for d in range(6):
            w = wheat.get(d) or {}
            print(
                f"  {d:2d} {w.get('money0', -1):5.0f} {w.get('shed0', -1):5d} "
                f"{w.get('held0', -1):5d} {w.get('buy', 0):4d} "
                f"{w.get('pickup', 0):3d} {w.get('feed', 0):4d} "
                f"{str(w.get('first_shed_h')):>4}  {w.get('buy_h', [])}"
            )


def run_seed(seed, agent=S4_LEAD):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([str(agent), V20])
    steps = env.steps

    days = [defaultdict(lambda: {
        "feed_h": [],
        "care_h": [],
        "collect_h": [],
        "harvest_h": [],
        "placed": None,
        "h23s": {},
        "mornings": {},
    }) for _ in range(2)]
    d6h0 = [None, None]
    placed_hour = [defaultdict(lambda: None) for _ in range(2)]
    wheat = [defaultdict(lambda: {
        "shed0": 0, "held0": 0, "buy": 0, "feed": 0,
        "money0": 0, "pickup": 0, "first_shed_h": None, "buy_h": [],
    }) for _ in range(2)]

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
        nxt_day = int(obs_list[0].get("day", 0))
        if day > 6:
            break
        for p in (0, 1):
            farm = (src[p].get("farms") or [{}])[p]
            farm_after = (obs_list[p].get("farms") or [{}])[p]
            priv = src[p].get("private") or {}
            sheep = _sheep(farm)
            sheep_after = _sheep(farm_after)
            units = _list_units(farm)
            on = _on_sheep(units, sheep)
            actions = _unit_actions(acts[p])
            if day <= 5:
                if hour == 0:
                    wheat[p][day]["shed0"] = int(
                        (priv.get("shed") or {}).get("WHEAT", 0) or 0
                    )
                    wheat[p][day]["money0"] = float(farm.get("money", 0) or 0)
                    held = 0
                    for inv in priv.get("inventories") or []:
                        if isinstance(inv, dict):
                            held += int(inv.get("WHEAT", 0) or 0)
                    wheat[p][day]["held0"] = held
                shed_now = int((priv.get("shed") or {}).get("WHEAT", 0) or 0)
                if shed_now > 0 and wheat[p][day]["first_shed_h"] is None:
                    wheat[p][day]["first_shed_h"] = hour
                for o in acts[p].get("market") or []:
                    if o and o[0] == "BUY_PRODUCT" and len(o) > 1 and o[1] == "WHEAT":
                        q = int(o[2] if len(o) > 2 else 1)
                        wheat[p][day]["buy"] += q
                        wheat[p][day]["buy_h"].append((hour, q))
                wheat[p][day]["feed"] += sum(
                    1 for a in actions if a and a[0] == "FEED"
                )
                wheat[p][day]["pickup"] += sum(
                    1 for a in actions
                    if a and a[0] == "PICKUP" and len(a) > 1 and a[1] == "WHEAT"
                )
                for s in sheep:
                    xy = s["xy"]
                    rec = days[p][xy]
                    if rec["placed"] is None:
                        rec["placed"] = s["placed"]
                    if placed_hour[p][xy] is None:
                        placed_hour[p][xy] = (day, hour)
                    for idx in on.get(xy, []):
                        if idx >= len(actions):
                            continue
                        a = actions[idx]
                        op = a[0] if a else None
                        if op == "FEED":
                            rec["feed_h"].append((day, hour))
                        elif op == "CARE":
                            rec["care_h"].append((day, hour))
                        elif op == "COLLECT_FERTILIZER":
                            rec["collect_h"].append((day, hour))
                        elif op == "HARVEST":
                            rec["harvest_h"].append((day, hour))
                if hour == 23:
                    for s in sheep:
                        days[p][s["xy"]]["h23s"][day] = s
                if nxt_day == day + 1:
                    morning = {s["xy"]: s for s in sheep_after}
                    seen = set(days[p].keys()) | set(morning.keys())
                    for xy in seen:
                        days[p][xy]["mornings"][day] = morning.get(xy)
            if day == 6 and hour == 0:
                d6h0[p] = sheep
        prev = obs_list

    return {
        "agent": Path(agent).name,
        "seed": seed,
        "bank_us": steps[-1][0].reward,
        "bank_v20": steps[-1][1].reward,
        "days": days,
        "d6h0": d6h0,
        "placed_hour": placed_hour,
        "wheat": wheat,
    }


def print_compare(rep):
    print("\n--- drawer ---")
    for p, label in ((0, "us"), (1, "v20")):
        d6 = rep["d6h0"][p] or []
        ys = [s["yield"] for s in d6]
        print(f"  {label} d6h0 yield {ys} sum={sum(ys)}  {[s['xy'] for s in d6]}")
    us = [s["yield"] for s in (rep["d6h0"][0] or [])]
    v20 = [s["yield"] for s in (rep["d6h0"][1] or [])]
    if us == v20 == [6, 6] or (sum(us) == 12 and sum(v20) == 12):
        print("  CARE bank already matches v20")
        return
    print(
        f"  miss vs v20: us {us} vs v20 {v20} — "
        "nights without CARE before payout are the fact"
    )


def main():
    args = sys.argv[1:]
    seeds = [int(x) for x in args if x.lstrip("-").isdigit()] or [0, 8]
    paths = [x for x in args if not x.lstrip("-").isdigit()]
    agent = Path(paths[0]) if paths else S4_LEAD
    if not agent.is_absolute():
        agent = (ROOT / agent).resolve() if not agent.exists() else agent.resolve()
    for seed in seeds:
        print(f"running {agent.name} seed {seed}...", flush=True)
        rep = run_seed(seed, agent=agent)
        print_seed(rep)
        print_compare(rep)


if __name__ == "__main__":
    main()
