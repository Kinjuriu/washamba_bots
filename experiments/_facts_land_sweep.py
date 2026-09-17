"""Land timing sweep: MIN_CASH_RESERVE_FOR_LAND_BUYING / LAND_BUY_START_DAY. Throwaway."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "_facts_v20.py"
sys.path.insert(0, str(ROOT))

from _facts_leftover import run
from _facts_window_sweep import K, SEEDS, print_quadrant_table, summarize_run

ARMS = {
    "land_first": {"reserve": 500, "start_day": 6, "land_first": True, "defer_animals": False},
    "land_first_no_defer": {
        "reserve": 500, "start_day": 6, "land_first": True,
        "no_post_sell_defer": True,
    },
    "defer_d9_cash": {
        "reserve": 500, "start_day": 6, "land_first": True,
        "defer_animals": "d9_cash",
        "no_post_sell_defer": True,
    },
    "skip_seed_restock": {
        "reserve": 500, "start_day": 6, "land_first": True,
        "skip_seed_restock": True,
    },
    "defer_d9_cash_skip_seed": {
        "reserve": 500, "start_day": 6, "land_first": True,
        "defer_animals": "d9_cash",
        "skip_seed_restock": True,
    },
    "straw_seed_supplement": {
        "reserve": 500, "start_day": 6, "land_first": True,
        "straw_seed_supplement": True,
    },
    "land_first_defer_d9_straw": {
        "reserve": 500, "start_day": 6, "land_first": True,
        "defer_animals": "d9_cash",
        "straw_seed_supplement": True,
    },
    # prior session arms (kept for replay)
    "baseline_no_land_first": {"reserve": 500, "start_day": 6, "land_first": False, "defer_animals": False},
    "land_first_defer": {"reserve": 500, "start_day": 6, "land_first": True, "defer_animals": True},
    "land_first_defer_d9": {
        "reserve": 500, "start_day": 6, "land_first": True,
        "defer_animals": "d9",
    },
    "land_first_defer_9_10": {
        "reserve": 500, "start_day": 6, "land_first": True,
        "defer_animals": "9_10",
    },
}

HELPER_FN = '''
def pending_second_land(farm):
    """NE bought, SW not yet — second BUY_LAND still outstanding."""
    unlocked = farm.get("unlocked_quadrants") or ["NW"]
    n_extra = len(unlocked) - 1
    return n_extra == 1 and n_extra < MAX_LAND_PURCHASES
'''

MARKET_WITHOUT_LAND_FIRST = """        elif buying:
            market = sells + animals + hires + rest_no_sell + land
        else:
            market = hires + rest + animals + land"""

MARKET_WITH_LAND_FIRST = """        elif buying:
            if land and pending_second_land(farm):
                market = sells + land + animals + hires + rest_no_sell
            else:
                market = sells + animals + hires + rest_no_sell + land
        else:
            if land and pending_second_land(farm):
                market = sells + land + hires + rest_no_sell + animals
            else:
                market = hires + rest + animals + land"""

SEED_RESTOCK_MARKER = """    if preferred_crop:
        seed_quantity = seed_restock_quantity(preferred_crop, farm, private)
        if seed_quantity > 0:
            actions.append(["BUY_SEED", preferred_crop, seed_quantity])"""

SEED_RESTOCK_SKIP = """    if preferred_crop and not (
        pending_second_land(farm)
        and farm.get("money", 0) >= LAND_PRICES[1] + MIN_CASH_RESERVE_FOR_LAND_BUYING
    ):
        seed_quantity = seed_restock_quantity(preferred_crop, farm, private)
        if seed_quantity > 0:
            actions.append(["BUY_SEED", preferred_crop, seed_quantity])"""

SEED_BUY_END = """    # Facts 9 / 21: never BUY_PRODUCT FERTILIZER. Collect from placed animals.
    return actions"""

SEED_BUY_STRAW_SUPPLEMENT = """    if (
        has_empty_later_extra_for_occupant(farm, day, board_size, "STRAWBERRY")
        and (private.get("seeds") or {}).get("STRAWBERRY", 0) == 0
    ):
        straw_qty = seed_restock_quantity("STRAWBERRY", farm, private)
        if straw_qty > 0 and not any(
            o and o[0] == "BUY_SEED" and len(o) > 1 and o[1] == "STRAWBERRY"
            for o in actions
        ):
            actions.append(["BUY_SEED", "STRAWBERRY", straw_qty])

    # Facts 9 / 21: never BUY_PRODUCT FERTILIZER. Collect from placed animals.
    return actions"""

DEFER_MARKER = "    elif slots > 0 and day > 0:"

POST_SELL_DEFER = """    if (
        day == 9
        and pending_second_land(farm)
        and not can_afford_pending_second_land_after_sells(
            farm,
            private,
            market_state,
            day,
            reserved_wheat=owned * MIN_WHEAT_RESERVE_FOR_FEEDING,
            unlocked_shops=unlocked_shops or (),
            board_size=board_size,
        )
    ):
        slots = 0

    if slots > 0 and day == 0:"""

POST_SELL_DEFER_OFF = "    if slots > 0 and day == 0:"


def _defer_block(cfg):
    mode = cfg.get("defer_animals")
    if not mode:
        return None
    if mode is True:
        return "    if pending_second_land(farm) and LAND_BUY_START_DAY <= day <= 11:\n        slots = 0\n"
    if mode == "d9":
        return "    if pending_second_land(farm) and day == 9:\n        slots = 0\n"
    if mode == "d9_cash":
        return (
            "    if pending_second_land(farm) and day == 9 and "
            "money < LAND_PRICES[1] + MIN_CASH_RESERVE_FOR_LAND_BUYING:\n"
            "        slots = 0\n"
        )
    if mode == "9_10":
        return "    if pending_second_land(farm) and day in (9, 10):\n        slots = 0\n"
    return None


def patch_agent(arm):
    text = SRC.read_text(encoding="utf-8")
    cfg = ARMS[arm]
    text = re.sub(
        r"MIN_CASH_RESERVE_FOR_LAND_BUYING = \d+",
        f"MIN_CASH_RESERVE_FOR_LAND_BUYING = {cfg['reserve']}",
        text,
        count=1,
    )
    text = re.sub(
        r"LAND_BUY_START_DAY = \d+",
        f"LAND_BUY_START_DAY = {cfg['start_day']}",
        text,
        count=1,
    )
    if not cfg["land_first"]:
        text = text.replace(MARKET_WITH_LAND_FIRST, MARKET_WITHOUT_LAND_FIRST)
    if cfg.get("no_post_sell_defer"):
        text = text.replace(POST_SELL_DEFER, POST_SELL_DEFER_OFF)
    if cfg.get("defer_animals"):
        block = _defer_block(cfg)
        if block and DEFER_MARKER in text and block.strip() not in text:
            text = text.replace(DEFER_MARKER, block + "    elif slots > 0 and day > 0:", 1)
    if cfg.get("skip_seed_restock"):
        text = text.replace(SEED_RESTOCK_MARKER, SEED_RESTOCK_SKIP)
    if cfg.get("straw_seed_supplement"):
        text = text.replace(SEED_BUY_END, SEED_BUY_STRAW_SUPPLEMENT)
    out = ROOT / f"_facts_v20_{arm}.py"
    out.write_text(text, encoding="utf-8")
    return "experiments/" + out.name


def d7_animal_ok(r):
    d7 = dict((r.get("buy_animal_day") or {}).get(7) or {})
    return not d7


def counters_pass(s, r, baseline_eligible=2):
    return (
        s["sw_unlock"] is not None
        and s["sw_unlock"] <= 9
        and s["straw_eligible_days"] >= 4
        and s["straw_eligible_days"] > baseline_eligible
        and s["night_deaths"] == 0
        and s["plant_straw_ne_d7_11"] == 0
        and s["plant_straw_ne_d12_14"] == 0
        and s["d12_ne_melon"] > 0
        and s["escapes"] == 0
        and s["plant_wheat_sw"] == 0
        and d7_animal_ok(r)
    )


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
        cfg = ARMS[arm]
        for seed in seeds:
            print(f"\n======== {arm} seed={seed} ========", flush=True)
            print(
                f"Knobs: reserve={cfg['reserve']} LAND_BUY_START_DAY={cfg['start_day']} "
                f"land_first={cfg['land_first']} defer_animals={cfg.get('defer_animals')} "
                f"skip_seed_restock={cfg.get('skip_seed_restock', False)} "
                f"straw_seed_supplement={cfg.get('straw_seed_supplement', False)}",
                flush=True,
            )
            r = run(agent, seed)
            s = summarize_run(r, k=K)
            s["arm"] = arm
            s["land_days"] = r["land_days"]
            s["d7_buy"] = dict((r.get("buy_animal_day") or {}).get(7) or {})
            s["pass"] = counters_pass(s, r)
            rows.append(s)
            print(
                f"Calendar: SW_unlock=d{s['sw_unlock']} BUY_LAND={r['land_days']} "
                f"eligible={s['straw_eligible_days']} days={s['straw_eligible_list']} "
                f"ceiling~{s['theoretical_ceiling']} landed={s['sw_landed']}",
                flush=True,
            )
            print(
                f"Counters: d12_SW_STRAW={s['d12_sw_straw']} d15_SW_STRAW={s['d15_sw_straw']} "
                f"d12_NE_MELON={s['d12_ne_melon']} d12_NE_weeds={s['d12_ne_weeds']} "
                f"ne_STRAW_d7_11={s['plant_straw_ne_d7_11']} "
                f"ne_STRAW_d12_14={s['plant_straw_ne_d12_14']} "
                f"d7_BUY_ANIMAL={s['d7_buy'] or 'none'} "
                f"night_deaths={s['night_deaths']} bank={s['bank']:.0f} "
                f"escapes={s['escapes']} pass={s['pass']}",
                flush=True,
            )
            if arm in ("baseline_no_land_first",) or s["pass"]:
                print_quadrant_table(r)

    print("\n=== LAND SWEEP SUMMARY ===")
    cols = [
        "arm", "seed", "bank", "sw_unlock", "straw_eligible_days", "sw_landed",
        "night_deaths", "d12_sw_straw", "d15_sw_straw", "d12_ne_melon",
        "d12_ne_weeds", "ne_straw_d7_11", "ne_straw_d12_14", "plant_wheat_sw",
        "escapes", "land_days", "pass",
    ]
    key_map = {
        "ne_straw_d7_11": "plant_straw_ne_d7_11",
        "ne_straw_d12_14": "plant_straw_ne_d12_14",
    }
    print("\t".join(cols))
    for s in rows:
        print("\t".join(str(s.get(key_map.get(c, c), "")) for c in cols))


if __name__ == "__main__":
    main()
