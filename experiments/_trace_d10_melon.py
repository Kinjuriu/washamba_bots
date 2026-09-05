"""Contested d9–12 MELON path diagnosis: throwaway vs v20, seeds 0+8.

Stages: acreage (ripe/field) → crew (HIRE/HARVEST) → shed/inv → SELL_$ + cash.
Reuses lockstep $ attribution from _trace_cashflow_v20.py.

Usage:
    .venv/Scripts/python.exe experiments/_trace_d10_melon.py
    .venv/Scripts/python.exe experiments/_trace_d10_melon.py 0 8
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from _trace_cashflow_v20 import analyze_episode  # noqa: E402

THROWAWAY = str(ROOT / "experiments" / "_facts_v20.py")
V20 = str(ROOT / "agents" / "route_v20.py")
SEEDS = (0, 8)


def is_harvestable_melon(tile, day):
    if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
        return False
    if tile.get("crop") != "MELON":
        return False
    if tile.get("yield_units", 0) <= 0:
        return False
    planted = tile.get("planted_day", day)
    return day - planted >= 10


def quadrant(x, y, board=10):
    half = board // 2
    return ("N" if y < half else "S") + ("W" if x < half else "E")


def scan_melon(farm, day):
    field = ripe = 0
    ripe_q = Counter()
    for y, row in enumerate(farm.get("tiles") or []):
        for x, t in enumerate(row):
            if not isinstance(t, dict) or t.get("crop") != "MELON":
                continue
            field += 1
            if is_harvestable_melon(t, day):
                ripe += 1
                ripe_q[quadrant(x, y)] += 1
    return field, ripe, ripe_q


def unit_held_melon(private):
    held = 0
    for inv in private.get("inventories") or []:
        if isinstance(inv, dict):
            held += int(inv.get("MELON", 0) or 0)
        elif isinstance(inv, (list, tuple)):
            # some shapes are [[item, qty], ...]
            for entry in inv:
                if isinstance(entry, (list, tuple)) and len(entry) >= 2 and entry[0] == "MELON":
                    held += int(entry[1] or 0)
                elif isinstance(entry, dict):
                    held += int(entry.get("MELON", 0) or 0)
    return held


def sell_melon_order_qty(act):
    total = 0
    for o in act.get("market") or []:
        if o and o[0] == "SELL" and len(o) > 2 and o[1] == "MELON":
            total += int(o[2] or 0)
    return total


def hire_order_count(act):
    return sum(1 for o in (act.get("market") or []) if o and o[0] == "HIRE")


def harvest_count(act):
    units = [act.get("farmer") or []] + list(act.get("hands") or [])
    return sum(1 for u in units if u and u[0] == "HARVEST")


def hands_on_board(farm):
    return len(farm.get("hands") or [])


def run_seed(seed):
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run([THROWAWAY, V20])
    cash = analyze_episode(env.steps, us_seat=0)

    # Index cash turns by (day, hour)
    cash_by_dh = {}
    for t in cash["turns"]:
        cash_by_dh[(t["day"], t["hour"])] = t

    day_agg = {
        0: defaultdict(lambda: {
            "hire": 0, "harvest": 0, "sell_qty": 0,
            "sell_dollars": 0.0, "sell_units": 0,
            "money_h0": None, "money_eod": None,
            "field_h0": None, "ripe_h0": None,
            "field_eod": None, "ripe_eod": None,
            "shed_h0": None, "shed_eod": None,
            "held_h0": None, "held_eod": None,
            "hands_h0": None, "hands_max": 0,
        }),
        1: defaultdict(lambda: {
            "hire": 0, "harvest": 0, "sell_qty": 0,
            "sell_dollars": 0.0, "sell_units": 0,
            "money_h0": None, "money_eod": None,
            "field_h0": None, "ripe_h0": None,
            "field_eod": None, "ripe_eod": None,
            "shed_h0": None, "shed_eod": None,
            "held_h0": None, "held_eod": None,
            "hands_h0": None, "hands_max": 0,
        }),
    }
    hour_rows = []  # d10 detail

    prev = [None, None]
    for step in env.steps:
        obs_list = []
        acts = []
        for p in (0, 1):
            raw = step[p]
            obs = raw.observation
            if not isinstance(obs, dict):
                try:
                    obs = dict(obs)
                except Exception:
                    pass
            act = raw.get("action") if hasattr(raw, "get") else None
            act = act or getattr(raw, "action", None) or {}
            obs_list.append(obs)
            acts.append(act)

        if prev[0] is None:
            prev = obs_list
            continue

        src = prev
        day = src[0].get("day", 0)
        hour = src[0].get("hour", 0)

        ct = cash_by_dh.get((day, hour))

        for p in (0, 1):
            farm = (src[p].get("farms") or [{}])[p]
            priv = src[p].get("private") or {}
            field, ripe, ripe_q = scan_melon(farm, day)
            shed = int((priv.get("shed") or {}).get("MELON", 0) or 0)
            held = unit_held_melon(priv)
            money = float(farm.get("money", 0))
            hands = hands_on_board(farm)
            hire_n = hire_order_count(acts[p])
            harv_n = harvest_count(acts[p])
            sell_q = sell_melon_order_qty(acts[p])

            sell_d = 0.0
            sell_u = 0
            if ct is not None:
                led = ct["ledger_us"] if p == 0 else ct["ledger_v20"]
                # units from season is cumulative; per-turn from cash turns
                # cash turns only expose dollars in ledger; units in season_units
                # Reconstruct units from turn ledgers isn't available — use $ only
                # and order qty. For unit exec, approximate: if we have turn units
                # elsewhere. analyze_episode doesn't put units on turns.
                sell_d = float(led.get("SELL_MELON", 0) or 0)

            if 9 <= day <= 12:
                agg = day_agg[p][day]
                agg["hire"] += hire_n
                agg["harvest"] += harv_n
                agg["sell_qty"] += sell_q
                agg["sell_dollars"] += sell_d
                agg["hands_max"] = max(agg["hands_max"], hands + 1)  # +farmer
                if hour == 0:
                    agg["money_h0"] = money
                    agg["field_h0"] = field
                    agg["ripe_h0"] = ripe
                    agg["shed_h0"] = shed
                    agg["held_h0"] = held
                    agg["hands_h0"] = hands + 1
                if hour == 23:
                    agg["money_eod"] = money
                    agg["field_eod"] = field
                    agg["ripe_eod"] = ripe
                    agg["shed_eod"] = shed
                    agg["held_eod"] = held

            if day == 10 and (
                hour % 3 == 0
                or hire_n
                or harv_n
                or sell_q
                or sell_d > 0
            ):
                hour_rows.append({
                    "p": p,
                    "hour": hour,
                    "money": money,
                    "field": field,
                    "ripe": ripe,
                    "ripe_q": dict(ripe_q),
                    "shed": shed,
                    "held": held,
                    "hands": hands + 1,
                    "hire": hire_n,
                    "harv": harv_n,
                    "sell_q": sell_q,
                    "sell_d": sell_d,
                })

        prev = obs_list

    # Day gap widen from cash by_day
    print("\n" + "=" * 88)
    print(f"# MELON path  seed={seed}  bank us={cash['bank_us']:.0f}  v20={cash['bank_v20']:.0f}")
    print(f"# cashflow max|err| us={cash['max_err_us']:.2f} v20={cash['max_err_v20']:.2f}")
    print("=" * 88)

    season_sm = cash["season_us"].get("SELL_MELON", 0)
    season_sv = cash["season_v20"].get("SELL_MELON", 0)
    print(
        f"\nseason SELL_MELON $: us={season_sm:.0f}  v20={season_sv:.0f}  "
        f"gap={season_sm - season_sv:.0f}"
    )

    print("\n--- day rollup d9–12 (us | v20) ---")
    print(
        f"  {'day':>3}  {'field_h0':>16}  {'ripe_h0':>12}  {'HIRE':>10}  "
        f"{'HARV':>10}  {'shed_h0':>12}  {'sell_qty':>14}  {'SELL_$':>16}  "
        f"{'money_h0':>16}  {'money_eod':>16}  {'gap_widen':>10}"
    )

    # Cumulative money gap for widen: (us_eod - v20_eod) - (us_h0 - v20_h0)
    # Better: from cash by_day net signed. Use EOD money gap change.
    prev_gap = None
    for day in range(9, 13):
        u = day_agg[0][day]
        v = day_agg[1][day]
        # day SELL_MELON from cash by_day
        sm_u = cash["by_day_us"].get(day, Counter()).get("SELL_MELON", 0)
        sm_v = cash["by_day_v20"].get(day, Counter()).get("SELL_MELON", 0)
        # Prefer cash by_day for dollars (already aggregated correctly)
        u_sell_d = sm_u
        v_sell_d = sm_v

        mu0 = u["money_h0"] if u["money_h0"] is not None else float("nan")
        mv0 = v["money_h0"] if v["money_h0"] is not None else float("nan")
        mu1 = u["money_eod"] if u["money_eod"] is not None else float("nan")
        mv1 = v["money_eod"] if v["money_eod"] is not None else float("nan")
        gap0 = mu0 - mv0
        gap1 = mu1 - mv1
        widen = gap1 - gap0 if prev_gap is None else gap1 - gap0
        # Also accumulate from start of window
        print(
            f"  d{day:<2}  "
            f"{_pair(u['field_h0'], v['field_h0']):>16}  "
            f"{_pair(u['ripe_h0'], v['ripe_h0']):>12}  "
            f"{_pair(u['hire'], v['hire']):>10}  "
            f"{_pair(u['harvest'], v['harvest']):>10}  "
            f"{_pair(u['shed_h0'], v['shed_h0']):>12}  "
            f"{_pair(u['sell_qty'], v['sell_qty']):>14}  "
            f"{_pair_f(u_sell_d, v_sell_d):>16}  "
            f"{_pair_f(mu0, mv0):>16}  "
            f"{_pair_f(mu1, mv1):>16}  "
            f"{widen:10.0f}"
        )
        # category gap for this day
        print(
            f"       SELL_MELON $ gap us-v20={u_sell_d - v_sell_d:.0f}  "
            f"shed_eod={_pair(u['shed_eod'], v['shed_eod'])}  "
            f"held_h0={_pair(u['held_h0'], v['held_h0'])}  "
            f"hands_h0={_pair(u['hands_h0'], v['hands_h0'])}  "
            f"ripe_eod={_pair(u['ripe_eod'], v['ripe_eod'])}"
        )
        prev_gap = gap1

    # Day-10 widen from full cash day nets
    print("\n--- day-10 category $ (us | v20 | gap) ---")
    cats = sorted(
        set(cash["by_day_us"].get(10, {})) | set(cash["by_day_v20"].get(10, {}))
    )
    for cat in cats:
        a = cash["by_day_us"].get(10, Counter()).get(cat, 0)
        b = cash["by_day_v20"].get(10, Counter()).get(cat, 0)
        if abs(a) < 1 and abs(b) < 1:
            continue
        print(f"  {cat:<22} {a:10.0f} {b:10.0f} {a - b:10.0f}")

    # Money gap at h0 d10 vs EOD d10
    u10 = day_agg[0][10]
    v10 = day_agg[1][10]
    if u10["money_h0"] is not None and v10["money_h0"] is not None:
        g0 = u10["money_h0"] - v10["money_h0"]
        g1 = (u10["money_eod"] or 0) - (v10["money_eod"] or 0)
        print(f"\nd10 money gap h0={g0:.0f}  eod={g1:.0f}  widen={g1 - g0:.0f}")
        print(
            f"d10 SELL_MELON $ gap="
            f"{cash['by_day_us'].get(10, Counter()).get('SELL_MELON', 0) - cash['by_day_v20'].get(10, Counter()).get('SELL_MELON', 0):.0f}"
        )

    print("\n--- d10 hour samples (us then v20) ---")
    for label, pid in (("us", 0), ("v20", 1)):
        print(f"  [{label}]")
        for r in hour_rows:
            if r["p"] != pid:
                continue
            print(
                f"    h{r['hour']:02d} $={r['money']:5.0f} field={r['field']:2d} "
                f"ripe={r['ripe']:2d}{r['ripe_q']} shed={r['shed']:2d} "
                f"held={r['held']:2d} units={r['hands']:2d} "
                f"HIRE={r['hire']} HARV={r['harv']} "
                f"sell_q={r['sell_q']} sell_$={r['sell_d']:.0f}"
            )

    # Bind hint
    print("\n--- bind hint ---")
    u, v = day_agg[0][10], day_agg[1][10]
    ripe_ok = (u["ripe_h0"] or 0) >= max(3, int(0.5 * (v["ripe_h0"] or 0)))
    hire_ok = u["hire"] > 0 and u["harvest"] >= 3
    sell_gap = (
        cash["by_day_us"].get(10, Counter()).get("SELL_MELON", 0)
        - cash["by_day_v20"].get(10, Counter()).get("SELL_MELON", 0)
    )
    if not ripe_ok:
        print("  likely FACT 36 (acreage): ripe/field short vs v20 on d10")
    elif not hire_ok:
        print("  likely FACT 35 (crew): ripe present but HIRE/HARVEST starved")
    elif sell_gap < -3000:
        print(
            f"  likely FACT 34 (sell): crew/ripe ok-ish but SELL_MELON $ gap={sell_gap:.0f}"
        )
        if (u["shed_h0"] or 0) == 0 and (u["harvest"] or 0) > 0:
            print("  note: shed empty morning — same-day harvest may miss force-sell until d11")
    else:
        print("  no classic 34/35/36 bind on d10 — inspect hour samples / new fact")

    return cash


def _pair(a, b):
    aa = "-" if a is None else str(a)
    bb = "-" if b is None else str(b)
    return f"{aa}|{bb}"


def _pair_f(a, b):
    def fmt(x):
        if x is None or (isinstance(x, float) and x != x):
            return "-"
        return f"{x:.0f}"
    return f"{fmt(a)}|{fmt(b)}"


def main():
    seeds = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(SEEDS)
    for seed in seeds:
        run_seed(seed)


if __name__ == "__main__":
    main()
