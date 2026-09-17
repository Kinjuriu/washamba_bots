"""Window extension sweep for facts 27/28. Throwaway."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "_facts_v20.py"
sys.path.insert(0, str(ROOT))

from _facts_leftover import run, _eod_at

ARMS = {
    "baseline": {"MELON": (0, 11), "STRAW": (5, 12), "STRAW_NEW_END": 12},
    "A_straw_only": {"MELON": (0, 11), "STRAW": (5, 15), "STRAW_NEW_END": 15},
    "B_paired": {"MELON": (0, 14), "STRAW": (5, 15), "STRAW_NEW_END": 15},
    "C_small": {"MELON": (0, 13), "STRAW": (5, 14), "STRAW_NEW_END": 14},
}
SEEDS = [0, 8]
K = 3
QUADRANTS = ("NW", "NE", "SW", "SE")
KEY_DAYS = (7, 9, 11, 12, 15, 20, 24)


def _quadrant_stats(e, q):
    if not e:
        return {"empty": 0, "planted": 0, "weeds": 0, "fill_pct": 0.0, "crops": {}}
    qc = (e.get("q_crops") or {}).get(q) or {}
    planted = sum(qc.values())
    empty = (e.get("q_empty") or {}).get(q, 0)
    weeds = (e.get("q_weeds") or {}).get(q, 0)
    plantable = empty + planted + weeds
    fill = (planted / plantable * 100.0) if plantable else 0.0
    return {"empty": empty, "planted": planted, "weeds": weeds, "fill_pct": fill, "crops": dict(qc)}


def sw_unlock_day(r):
    for e in r["eod"]:
        sw = _quadrant_stats(e, "SW")
        if sw["empty"] + sw["planted"] + sw["weeds"] > 0:
            return e["day"]
    return None


def straw_eligible_days(r, straw_start=7, straw_end=12):
    unlock = sw_unlock_day(r)
    if unlock is None:
        return 0, []
    days = [d for d in range(straw_start, straw_end + 1) if d >= unlock]
    return len(days), days


def summarize_run(r, straw_start=7, straw_end=12, k=3):
    plant_straw_ne_d7_11 = plant_straw_ne_d12_14 = 0
    plant_straw_sw = plant_wheat_sw = 0
    for day, qs in (r.get("plant_q") or {}).items():
        ne = qs.get("NE") or {}
        sw = qs.get("SW") or {}
        if 7 <= day <= 11:
            plant_straw_ne_d7_11 += ne.get("STRAWBERRY", 0)
        if 12 <= day <= 14:
            plant_straw_ne_d12_14 += ne.get("STRAWBERRY", 0)
        plant_straw_sw += sw.get("STRAWBERRY", 0)
        plant_wheat_sw += sw.get("WHEAT", 0)
    swd = r.get("sw_same_day") or {}
    night_deaths = sum(v.get("night_deaths", 0) for v in swd.values())
    sw_landed = sum(v.get("landed", 0) for v in swd.values())
    d12 = _eod_at(r, 12)
    d14 = _eod_at(r, 14)
    d15 = _eod_at(r, 15)
    d12_ne = _quadrant_stats(d12, "NE")
    d12_sw = _quadrant_stats(d12, "SW")
    d15_sw = _quadrant_stats(d15, "SW")
    d14_ne = _quadrant_stats(d14, "NE")
    elig_n, elig_days = straw_eligible_days(r, straw_start, straw_end)
    return {
        "seed": r["seed"],
        "bank": r["bank"],
        "escapes": r.get("escapes", 0),
        "d0_pens": (r.get("d0") or {}).get("pens"),
        "d0_herd": (r.get("d0") or {}).get("herd"),
        "sw_unlock": sw_unlock_day(r),
        "straw_eligible_days": elig_n,
        "straw_eligible_list": elig_days,
        "theoretical_ceiling": elig_n * 24 * k // 2,
        "sw_landed": sw_landed,
        "night_deaths": night_deaths,
        "plant_straw_ne_d7_11": plant_straw_ne_d7_11,
        "plant_straw_ne_d12_14": plant_straw_ne_d12_14,
        "d12_ne_melon": d12_ne["crops"].get("MELON", 0),
        "d12_ne_straw": d12_ne["crops"].get("STRAWBERRY", 0),
        "d12_ne_weeds": d12_ne["weeds"],
        "d12_sw_straw": d12_sw["crops"].get("STRAWBERRY", 0),
        "d12_sw_empty": d12_sw["empty"],
        "d14_ne_melon": d14_ne["crops"].get("MELON", 0),
        "d15_sw_straw": d15_sw["crops"].get("STRAWBERRY", 0),
        "d15_sw_empty": d15_sw["empty"],
        "plant_straw_sw": plant_straw_sw,
        "plant_wheat_sw": plant_wheat_sw,
    }


def print_quadrant_table(r, days=KEY_DAYS):
    print("Quadrant fill (planted / empty / fill%):")
    hdr = f"  {'day':>3}  " + "  ".join(
        f"{q + '_pl':>5} {q + '_em':>4} {q + '%':>4}" for q in QUADRANTS
    )
    print(hdr)
    for day in days:
        e = _eod_at(r, day)
        if not e:
            continue
        parts = [f"  {day:3d}  "]
        for q in QUADRANTS:
            s = _quadrant_stats(e, q)
            parts.append(f"{s['planted']:5d} {s['empty']:4d} {s['fill_pct']:4.0f}")
        print("  ".join(parts))


def patch_agent(arm):
    text = SRC.read_text(encoding="utf-8")
    cfg = ARMS[arm]
    text = re.sub(r'"MELON": \(\d+, \d+\)', f'"MELON": {cfg["MELON"]}', text, count=1)
    text = re.sub(
        r'"STRAWBERRY": \(\d+, \d+\)',
        f'"STRAWBERRY": {cfg["STRAW"]}',
        text,
        count=1,
    )
    text = re.sub(
        r"STRAW_NEW_LAND_DAY_END = \d+",
        f"STRAW_NEW_LAND_DAY_END = {cfg['STRAW_NEW_END']}",
        text,
        count=1,
    )
    out = ROOT / f"_facts_v20_{arm}.py"
    out.write_text(text, encoding="utf-8")
    return "experiments/" + out.name


def main():
    arms = list(ARMS)
    seeds = list(SEEDS)
    if len(sys.argv) > 1:
        arms = [a for a in sys.argv[1:] if a in ARMS]
    if len(sys.argv) > 2 and sys.argv[-1].isdigit():
        seeds = [int(sys.argv[-1])]
        arms = [a for a in sys.argv[1:-1] if a in ARMS] or arms

    rows = []
    for arm in arms:
        agent = patch_agent(arm)
        straw_end = ARMS[arm]["STRAW_NEW_END"]
        for seed in seeds:
            print(f"\n======== {arm} seed={seed} ========", flush=True)
            r = run(agent, seed)
            s = summarize_run(r, straw_end=straw_end, k=K)
            s["arm"] = arm
            rows.append(s)
            print(
                f"Calendar: SW_unlock=d{s['sw_unlock']} BUY_LAND={r['land_days']} "
                f"eligible={s['straw_eligible_days']} days={s['straw_eligible_list']} "
                f"ceiling~{s['theoretical_ceiling']} landed={s['sw_landed']}"
            )
            print(
                f"Counters: d12_SW_STRAW={s['d12_sw_straw']} d15_SW_STRAW={s['d15_sw_straw']} "
                f"d14_NE_MELON={s['d14_ne_melon']} ne_STRAW_d7_11={s['plant_straw_ne_d7_11']} "
                f"ne_STRAW_d12_14={s['plant_straw_ne_d12_14']} night_deaths={s['night_deaths']} "
                f"bank={s['bank']:.0f} escapes={s['escapes']}"
            )
            if arm == "baseline":
                print_quadrant_table(r)
    print("\n=== SWEEP SUMMARY ===")
    key_map = {
        "ne_straw_d7_11": "plant_straw_ne_d7_11",
        "ne_straw_d12_14": "plant_straw_ne_d12_14",
    }
    cols = [
        "arm", "seed", "bank", "sw_unlock", "straw_eligible_days", "sw_landed",
        "night_deaths", "d12_sw_straw", "d15_sw_straw", "d14_ne_melon",
        "ne_straw_d7_11", "ne_straw_d12_14", "plant_wheat_sw", "escapes",
    ]
    print("\t".join(cols))
    for s in rows:
        print("\t".join(str(s.get(key_map.get(c, c), "")) for c in cols))


if __name__ == "__main__":
    main()
