"""Full pre-run audit: source checks + episode counters for all FACTS.md rows.

Usage:
    .venv/Scripts/python.exe experiments/_facts_prerun_audit.py
    .venv/Scripts/python.exe experiments/_facts_prerun_audit.py experiments/_facts_v20.py
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv" / "Scripts" / "python.exe"
DEFAULT_AGENT = ROOT / "experiments" / "_facts_v20.py"
SEEDS = (0, 8)


def read_agent(path):
    return Path(path).read_text(encoding="utf-8")


def src_check(fact_ids, name, ok, detail=""):
    return {
        "facts": fact_ids,
        "name": name,
        "ok": ok,
        "detail": detail,
        "kind": "source",
        "optional": False,
    }


def run_src_audit(src):
    checks = []

    fn = re.search(r"def choose_animal_to_build\(.*?\n(.*?)\n\ndef ", src, re.DOTALL)
    raw_body = fn.group(1) if fn else ""
    build_body = re.sub(r'""".*?"""', "", raw_body, flags=re.DOTALL)
    checks.append(src_check(
        [2], "Fact 2: BUILD not cash-gated",
        "Fact 2:" in build_body
        and "ANIMAL_SPEND_CAP_FRACTION" not in build_body
        and "MIN_CASH_RESERVE_FOR_ANIMAL_BUYING" not in build_body,
        "choose_animal_to_build skips purchase cash bars",
    ))
    checks.append(src_check(
        [5, 18], "Fact 5/18: wheat reserve on owned",
        "count_owned_animals" in src
        and re.search(r"reserved_wheat\s*=\s*owned", src) is not None,
        "reserved_wheat = owned * MIN_WHEAT_RESERVE_FOR_FEEDING",
    ))
    checks.append(src_check(
        [15], "Fact 15: calendar prefix hold + d11+ shop mix",
        "day >= 11" in src and "shop_mix_target" in src
        and "day < 11" in src and "return 12" in src,
        "hold 6 through d10; d11+ mix toward ceiling",
    ))
    checks.append(src_check(
        [9, 10, 11, 12, 13], "Facts 9-13: buy-emit market order",
        "unlock_preamble" in src
        and re.search(r"sells \+ .* \+ animals", src) is not None
        and "sell_fert_for_buy" in src,
        "sell->animal->rest on BUY_ANIMAL emit; unlock preamble",
    ))
    checks.append(src_check(
        [16], "Fact 16: parallel pens + home cap gate",
        "pending_builds" in src and "MAX_ANIMALS_ON_HOME_LAND" in src,
        "parallel pending_builds; home cap only pre-land",
    ))
    checks.append(src_check(
        [17], "Fact 17: season cap past 8 (shop-mix ceiling)",
        re.search(r"MAX_ANIMALS\s*=\s*(1[4-8]|18)", src) is not None,
        "MAX_ANIMALS>=14",
    ))
    checks.append(src_check(
        [33], "Fact 33: land timing + land_first; no SE",
        "decide_land_orders" in src
        and "_estimated_post_sell_cash" in src
        and "LAND_BUY_START_DAY = 6" in src
        and re.search(r"MAX_LAND_PURCHASES\s*=\s*2", src) is not None
        and "LAND_PURCHASE_DAY_WINDOWS" in src,
        "d6-10/d11-12 windows; post-sell emit; MAX_LAND_PURCHASES=2",
    ))
    checks.append(src_check(
        [19], "Fact 19: wheat buy in animal path",
        "def decide_animal_market_actions" in src
        and "BUY_PRODUCT" in src
        and "WHEAT" in src,
        "wheat restock lives with animal market actions",
    ))
    checks.append(src_check(
        [20], "Fact 20: feed claim / walk rules",
        "feed_claimed" in src and "preclaim_occupied_feeds" in src,
        "occupied unfed pre-claimed; feed-walk excludes feed_claimed",
    ))
    checks.append(src_check(
        [21], "Fact 21: no BUY_PRODUCT FERTILIZER",
        '["BUY_PRODUCT", "FERTILIZER"' not in src
        and "never BUY_PRODUCT FERTILIZER" in src,
        "no fertilizer buy path",
    ))
    checks.append(src_check(
        [22], "Fact 22: no force-wheat wrapper",
        "force_wheat" not in src.lower() and "force-plant WHEAT" not in src,
        "no dedicated wheat-force wrapper",
    ))
    checks.append(src_check(
        [23], "Fact 23: never plant TOMATO",
        re.search(r'"TOMATO":\s*None', src) is not None,
        "CROP_PLANTING_WINDOWS TOMATO=None",
    ))
    checks.append(src_check(
        [24], "Fact 24: no skip-CARE for crops",
        "skip CARE" not in src.lower() or "Do not skip CARE" in src,
        "no Path-C skip-CARE gate",
    ))
    checks.append(src_check(
        [25], "Fact 25: no hire-density mutation",
        "WORK_TILES_PER_HAND" in src
        and "forced extra" not in src.lower(),
        "WORK_TILES_PER_HAND present; no forced-extra hire spiral",
    ))
    checks.append(src_check(
        [26], "Fact 26: no F8 herd-scaled floor",
        "reserve * (owned" not in src
        and "wheat_stock >=" not in src.replace(" ", ""),
        "no hard buffer-before-scale gate",
    ))
    checks.append(src_check(
        [27, 28], "Fact 27/28: leftover occupant routing",
        "leftover_occupant" in src and "later_extra_quadrants_effective" in src,
        "MELON on NE, STRAW on later extras",
    ))
    checks.append(src_check(
        [29], "Fact 29: K pre-unlock + unlock bypass",
        "LATER_EXTRA_CREW_K" in src
        and "sw_slots = [999]" in src
        and "sw_slots[0]" in src,
        f"K={re.search(r'LATER_EXTRA_CREW_K = (\\d+)', src).group(1) if re.search(r'LATER_EXTRA_CREW_K = (\\d+)', src) else '?'}; unlock->999",
    ))
    checks.append(src_check(
        [30], "Fact 30: STRAW seed cadence fn",
        "fact30_wants_straw_seed" in src,
        "occupant-aware STRAW restock",
    ))
    checks.append(src_check(
        [31], "Fact 31: unlock morning preamble",
        "straw_bulk_restock_quantity" in src
        and "unlock_morning_sell_proceeds" in src
        and ("land_tail = 0" in src or "land_tail = 200" in src),
        "sell->bulk STRAW; unlock land_tail waived/low",
    ))
    checks.append(src_check(
        [32], "Fact 32: SW carpet day",
        "is_sw_carpet_day" in src and "sw_carpet_day" in src,
        "full-crew carpet on unlock day",
    ))
    checks.append(src_check(
        [34], "Fact 34: MELON cash wave",
        "in_melon_cash_wave" in src
        and "MELON_CASH_WAVE_SELL_CAP" in src
        and "force_melon_wave" in src
        and '["DROP", "MELON"' in src
        and "held_product_total" in src
        and "any_unfed_animal" in src
        and "melon_drop_room" in src,
        "d9-12 force-sell shed+held + capped DROP walk d10",
    ))
    checks.append(src_check(
        [35], "Fact 35: MELON-wave hire floor waive",
        "count_ripe_melon" in src
        and "waive_hire_floor" in src
        and "MIN_MONEY_TO_HIRE" in src,
        "waive flat hire floor when ripe MELON exists",
    ))
    checks.append(src_check(
        [36], "Fact 36: early MELON opening seed",
        "MELON_OPENING_SEED" in src
        and "melon_opening_restock_quantity" in src
        and "count_field_crop" in src,
        "day-0 MELON opening bulk + plant_budget credit path",
    ))
    checks.append(src_check(
        [38, 39], "Fact 38/39: NW wheat product + post-MELON claim",
        "fact38_wants_wheat_seed" in src
        and "wheat_product_restock_quantity" in src
        and "fact39_home_wait" in src
        and "pending_second_land(farm)" in src
        and "Fact 39" in src,
        "d13+ home WHEAT; refuse STRAW refill; fact30 unlock halves",
    ))
    checks.append(src_check(
        [41], "Fact 41: post-carpet SW STRAW fert coverage",
        "sw_straw_wants_fert" in src
        and "fact41_post_carpet_fert" in src
        and "prefer_quadrant" in src
        and "try_fert_errand" in src,
        "elevate fert before DIG when post-carpet SW wants fert",
    ))
    checks.append(src_check(
        [1, 3, 4, 6], "Facts 1/3/4/6: d0 batch helpers present",
        "decide_hire_orders" in src
        and "decide_animal_market_actions" in src
        and "MAX_MARKET_ORDERS_PER_TURN" in src,
        "hire + animal market + order-cap symbols present",
    ))
    checks.append(src_check(
        [7, 8], "Facts 7/8: FEED/COLLECT paths",
        '["FEED"]' in src or '["FEED"' in src,
        "FEED action path present",
    ))
    checks.append(src_check(
        [14], "Fact 14: calendar holds d0 at 4",
        "calendar_owned_target" in src and "day < 3" in src,
        "calendar_owned_target gates early owned",
    ))
    return checks


def run_episode(agent, seed):
    proc = subprocess.run(
        [str(PY), str(ROOT / "experiments" / "_facts_leftover.py"), agent, str(seed)],
        cwd=ROOT, capture_output=True, text=True, timeout=180,
    )
    out = proc.stdout + proc.stderr
    if proc.returncode != 0:
        return {"seed": seed, "error": out[-800:]}

    def grab(pat, default=None, cast=str):
        m = re.search(pat, out)
        if not m:
            return default
        try:
            return cast(m.group(1))
        except (TypeError, ValueError):
            return default

    sw_days = {}
    for line in out.splitlines():
        m = re.search(r"^\s+d(\d+) req=\d+ landed=(\d+)", line)
        if m:
            sw_days[int(m.group(1))] = int(m.group(2))

    land_m = re.search(r"BUY_LAND days: (\[[^\]]+\])", out)
    land_days = eval(land_m.group(1)) if land_m else []
    sw_unlock = land_days[1] if len(land_days) >= 2 else None

    held = {}
    hm = re.search(r"held STRAW seed max/day: (.+)", out)
    if hm:
        for part in hm.group(1).split():
            pm = re.match(r"d(\d+)=(\d+)", part)
            if pm:
                held[int(pm.group(1))] = int(pm.group(2))

    straw_buy_days = []
    sb = re.search(r"BUY_SEED STRAW days=(\[[^\]]*\])", out)
    if sb:
        straw_buy_days = eval(sb.group(1))

    emit_rows = []
    for line in out.splitlines():
        m = re.search(
            r"d(\d+)h(\d+) fert_before=(\w+) sell_i=(\w+) buy_i=(\w+)(?: seed_between=(\w+))?",
            line,
        )
        if m:
            emit_rows.append({
                "day": int(m.group(1)),
                "hour": int(m.group(2)),
                "fert_before": m.group(3) == "True",
                "seed_between": m.group(6) == "True" if m.group(6) else False,
            })

    end_m = re.search(r"end pens/herd=(\d+)/(\d+)", out)
    d0_m = re.search(r"d0h23 pens/herd=(\d+)/(\d+)", out)
    d0h0 = {
        "orders": grab(r"d0h0 orders=(\d+)", 0, int),
        "hire": grab(r"d0h0 orders=\d+ HIRE=(\d+)", 0, int),
        "wheat": grab(r"d0h0 orders=\d+ HIRE=\d+ BUY_ANIMAL=\{[^}]*\} WHEAT=(\d+)", 0, int),
    }
    animals_m = re.search(r"d0h0 orders=\d+ HIRE=\d+ BUY_ANIMAL=(\{[^}]*\})", out)
    d0_animals = eval(animals_m.group(1)) if animals_m else {}

    melon_by = {}
    mb = re.search(r"MELON sold d9-11=\d+ by_day=(\{[^}]+\})", out)
    if mb:
        try:
            melon_by = eval(mb.group(1))
        except (SyntaxError, TypeError, ValueError):
            melon_by = {}

    return {
        "seed": seed,
        "bank": grab(r"bank=(\d+)", 0, int),
        "d0_pens": int(d0_m.group(1)) if d0_m else -1,
        "d0_herd": int(d0_m.group(2)) if d0_m else -1,
        "end_pens": int(end_m.group(1)) if end_m else -1,
        "end_herd": int(end_m.group(2)) if end_m else -1,
        "ne_straw_d7_11": grab(r"PLANT NE STRAW d7-11=(\d+)", -1, int),
        "ne_straw_d7_10": grab(r"PLANT NE STRAW d7-10=(\d+)", -1, int),
        "ne_straw_d11_12": grab(r"d11-12=(\d+)", -1, int),
        "ne_melon_season": grab(r"NE MELON season=(\d+)", -1, int),
        "d12_ne_melon": grab(r"d12 NE empty=\d+ MELON=(\d+)", -1, int),
        "sw_straw_season": grab(r"SW STRAW=(\d+)", -1, int),
        "sw_wheat": grab(r"SW WHEAT=(\d+)", -1, int),
        "escapes": grab(r"escapes=(\d+)", -1, int),
        "night_deaths": grab(r"night_deaths=(\d+) WATER_acts", -1, int),
        "unlock_landed": sw_days.get(sw_unlock, 0) if sw_unlock is not None else 0,
        "sw_unlock_day": sw_unlock,
        "land_days": land_days,
        "buy_fert": grab(r"BUY_FERT=(\d+)", -1, int),
        "plant_tomato": grab(r"PLANT_TOMATO=(\d+)", -1, int),
        "collect_fert": grab(r"COLLECT_FERT=(\d+)", -1, int),
        "fertilize": grab(r"COLLECT_FERT=\d+ FERTILIZE=(\d+)", -1, int),
        "fert_sell_units": grab(
            r"COLLECT_FERT=\d+ FERTILIZE=\d+ SELL_FERT_units=(\d+)", -1, int,
        ),
        "feed_acts": grab(r"FEED=(\d+)", -1, int),
        "d7_buy": grab(r"d7 BUY_ANIMAL \(fact 15 hold\): (.+)", "none"),
        "d18_herd": grab(r"EOD d18 herd=(\d+)", -1, int),
        "end_unlocked": grab(r"end unlocked_quads=(\d+)", -1, int),
        "d0h0": d0h0,
        "d0_animals": d0_animals,
        "held_straw": held,
        "straw_buy_days": straw_buy_days,
        "emit_rows": emit_rows,
        "melon_sold_d9_11": grab(r"MELON sold d9-11=(\d+)", -1, int),
        "d11_money": grab(r"EOD d11 herd=\d+ money=(\d+)", -1, int),
        "d10_hire": grab(r"d10 HIRE=(\d+)", -1, int),
        "d10_melon_harvest": grab(r"d10 HIRE=\d+ MELON_HARVEST=(\d+)", -1, int),
        "d10_melon_sold": grab(r"d10 HIRE=\d+ MELON_HARVEST=\d+ MELON_sold=(\d+)", -1, int),
        "melon_sold_by_day": melon_by,
        "melon_buy_d0": grab(r"fact36 d0 BUY_SEED MELON=(\d+)", -1, int),
        "plant_melon_d0": grab(r"fact36 d0 BUY_SEED MELON=\d+ PLANT MELON d0=(\d+)", -1, int),
        "field_melon_d5": grab(
            r"fact36 d0 BUY_SEED MELON=\d+ PLANT MELON d0=\d+ field MELON EOD d5=(\d+)",
            -1, int,
        ),
        "nw_wheat_plant": grab(r"fact38/39 NW PLANT WHEAT=(\d+)", -1, int),
        "nw_straw_plant": grab(r"fact38/39 NW PLANT WHEAT=\d+ NW PLANT STRAW=(\d+)", -1, int),
        "raw": out,
    }


def ctr(fact_ids, name, ok, detail="", seed=None):
    return {
        "facts": fact_ids,
        "name": name,
        "ok": ok,
        "detail": detail,
        "kind": "counter",
        "seed": seed,
        "optional": False,
    }


def run_counter_audit(ep):
    seed = ep["seed"]
    if "error" in ep:
        return [ctr([0], f"seed {seed} episode", False, ep["error"], seed)]

    checks = []
    unlock = ep["sw_unlock_day"]
    land = ep["land_days"]
    d0_animals = ep.get("d0_animals") or {}
    cows = int(d0_animals.get("COW", 0))
    sheep = int(d0_animals.get("SHEEP", 0))
    d0h0 = ep.get("d0h0") or {}

    # Beach-head 1-6
    checks.append(ctr(
        [1], f"seed {seed}: fact1 d0 2C2S batch",
        cows == 2 and sheep == 2,
        f"d0h0 animals={d0_animals}", seed,
    ))
    checks.append(ctr(
        [2, 3], f"seed {seed}: fact2/3 d0 pens/herd 4/4",
        ep["d0_pens"] == 4 and ep["d0_herd"] == 4,
        f"d0h23={ep['d0_pens']}/{ep['d0_herd']}", seed,
    ))
    checks.append(ctr(
        [4], f"seed {seed}: fact4 d0h0 hires>=5",
        d0h0.get("hire", 0) >= 5,
        f"HIRE={d0h0.get('hire')}", seed,
    ))
    checks.append(ctr(
        [5], f"seed {seed}: fact5 d0h0 wheat>0",
        d0h0.get("wheat", 0) > 0,
        f"WHEAT={d0h0.get('wheat')}", seed,
    ))
    checks.append(ctr(
        [6], f"seed {seed}: fact6 d0h0 orders<=10 with 4 animals",
        d0h0.get("orders", 0) <= 10 and cows + sheep == 4,
        f"orders={d0h0.get('orders')} animals={cows + sheep}", seed,
    ))

    # Later buys / calendar
    checks.append(ctr(
        [7], f"seed {seed}: fact7 0 escapes",
        ep["escapes"] == 0, f"escapes={ep['escapes']}", seed,
    ))
    checks.append(ctr(
        [8], f"seed {seed}: fact8 collect fert>0",
        ep["collect_fert"] > 0, f"COLLECT={ep['collect_fert']}", seed,
    ))
    emit = ep.get("emit_rows") or []
    # Fact 9/10: fert sell funds later buys (d3/5/7+). Day 0 has no fert yet;
    # unlock-day preamble is fact 31 (may sell MELON/FERT differently).
    buy_emit_check = [
        e for e in emit
        if e["day"] not in (0, unlock) and e["day"] >= 3
    ]
    fert_ok = all(e["fert_before"] for e in buy_emit_check) if buy_emit_check else False
    checks.append(ctr(
        [9, 10], f"seed {seed}: fact9/10 SELL FERT before BUY_ANIMAL",
        fert_ok,
        f"{sum(1 for e in buy_emit_check if e['fert_before'])}/{len(buy_emit_check)} emit turns",
        seed,
    ))
    seed_between_fail = [
        e for e in buy_emit_check if e.get("seed_between")
    ]
    checks.append(ctr(
        [13], f"seed {seed}: fact13 no BUY_SEED between fert/animal",
        len(seed_between_fail) == 0,
        f"violations={[e['day'] for e in seed_between_fail]} (unlock d{unlock} exempt)",
        seed,
    ))
    d7 = (ep.get("d7_buy") or "none").strip()
    checks.append(ctr(
        [15], f"seed {seed}: fact15 d7 BUY_ANIMAL quiet (hold at 6)",
        d7 == "none", f"d7={d7}", seed,
    ))
    d18_herd = ep.get("d18_herd", -1)
    checks.append(ctr(
        [15], f"seed {seed}: fact15 EOD d18 owned>=12",
        d18_herd >= 12, f"d18_herd={d18_herd}", seed,
    ))
    checks.append(ctr(
        [14, 1], f"seed {seed}: fact14 d0 owned=4 not 5+",
        ep["d0_herd"] == 4, f"d0_herd={ep['d0_herd']}", seed,
    ))
    checks.append(ctr(
        [16, 17], f"seed {seed}: fact16/17 end placed >=12",
        ep["end_herd"] >= 12,
        f"end={ep['end_pens']}/{ep['end_herd']}", seed,
    ))
    end_unlocked = ep.get("end_unlocked", -1)
    checks.append(ctr(
        [33], f"seed {seed}: fact33 unlocked==3 by end (no SE)",
        end_unlocked == 3, f"unlocked={end_unlocked}", seed,
    ))

    # Feed / crop constraints
    checks.append(ctr(
        [18, 19, 20], f"seed {seed}: fact18-20 feed alive (FEED>0, 0 escapes)",
        ep["feed_acts"] > 0 and ep["escapes"] == 0,
        f"FEED={ep['feed_acts']} escapes={ep['escapes']}", seed,
    ))
    checks.append(ctr(
        [21], f"seed {seed}: fact21 BUY_FERT=0",
        ep["buy_fert"] == 0, f"buy_fert={ep['buy_fert']}", seed,
    ))
    checks.append(ctr(
        [22], f"seed {seed}: fact22 SW WHEAT=0",
        ep["sw_wheat"] == 0, f"sw_wheat={ep['sw_wheat']}", seed,
    ))
    checks.append(ctr(
        [23], f"seed {seed}: fact23 PLANT_TOMATO=0",
        ep["plant_tomato"] == 0, f"tomato={ep['plant_tomato']}", seed,
    ))

    # Occupant / SW recipe 27-33
    checks.append(ctr(
        [27], f"seed {seed}: fact27 NE STRAW d7-11=0",
        ep["ne_straw_d7_11"] == 0, f"ne={ep['ne_straw_d7_11']}", seed,
    ))
    checks.append(ctr(
        [27, 29], f"seed {seed}: fact27/29 d12 NE MELON>0",
        ep["d12_ne_melon"] > 0, f"d12_ne_melon={ep['d12_ne_melon']}", seed,
    ))
    checks.append(ctr(
        [27], f"seed {seed}: fact27 NE MELON season>0",
        ep["ne_melon_season"] > 0, f"ne_melon={ep['ne_melon_season']}", seed,
    ))
    checks.append(ctr(
        [28, 29], f"seed {seed}: fact28/29 SW night_deaths=0",
        ep["night_deaths"] == 0, f"deaths={ep['night_deaths']}", seed,
    ))
    held = ep.get("held_straw") or {}
    held_ok_days = [d for d in (9, 10, 11) if held.get(d, 0) > 0]
    checks.append(ctr(
        [30], f"seed {seed}: fact30 held STRAW>0 some d9-11",
        len(held_ok_days) >= 1,
        f"held={ {d: held.get(d, 0) for d in (9, 10, 11)} }", seed,
    ))
    pre_unlock_straw = [
        d for d in ep.get("straw_buy_days") or []
        if unlock is None or d < unlock
    ]
    checks.append(ctr(
        [30], f"seed {seed}: fact30 BUY_SEED STRAW before unlock",
        len(pre_unlock_straw) >= 1,
        f"pre_unlock={pre_unlock_straw} unlock=d{unlock}", seed,
    ))
    checks.append(ctr(
        [32], f"seed {seed}: fact32 unlock-day landed>=14",
        ep["unlock_landed"] >= 14,
        f"d{unlock} landed={ep['unlock_landed']} (bar 14; $100 STRAW + land floor caps seed 0 at 14)",
        seed,
    ))
    checks.append(ctr(
        [33], f"seed {seed}: fact33 sw_unlock<=11",
        unlock is not None and unlock <= 11,
        f"unlock=d{unlock} lands={land}", seed,
    ))
    checks.append(ctr(
        [33], f"seed {seed}: fact33 1st land d6-10",
        len(land) >= 1 and 6 <= land[0] <= 10,
        f"land1=d{land[0] if land else None}", seed,
    ))
    checks.append(ctr(
        [33], f"seed {seed}: fact33 2nd land d11-12",
        len(land) >= 2 and 11 <= land[1] <= 12,
        f"land2=d{land[1] if len(land) > 1 else None}", seed,
    ))
    melon_d9_11 = ep.get("melon_sold_d9_11", -1)
    melon_by = ep.get("melon_sold_by_day") or {}
    has_d10_or_d11_sell = (melon_by.get(10, 0) + melon_by.get(11, 0)) > 0
    checks.append(ctr(
        [34], f"seed {seed}: fact34 MELON sold d9-11 >=20",
        melon_d9_11 >= 20,
        f"sold={melon_d9_11} by_day={melon_by}", seed,
    ))
    checks.append(ctr(
        [34], f"seed {seed}: fact34 SELL MELON on d10 or d11",
        has_d10_or_d11_sell,
        f"d10={melon_by.get(10, 0)} d11={melon_by.get(11, 0)}", seed,
    ))
    d11_money = ep.get("d11_money", -1)
    checks.append(ctr(
        [34], f"seed {seed}: fact34 EOD d11 money >> 20 when wave sold",
        melon_d9_11 < 20 or d11_money > 20,
        f"d11_money={d11_money} sold_d9_11={melon_d9_11}", seed,
    ))
    d10_hire = ep.get("d10_hire", -1)
    d10_harv = ep.get("d10_melon_harvest", -1)
    d10_sold = ep.get("d10_melon_sold", -1)
    checks.append(ctr(
        [35], f"seed {seed}: fact35 d10 HIRE>0",
        d10_hire > 0,
        f"d10_hire={d10_hire}", seed,
    ))
    checks.append(ctr(
        [35], f"seed {seed}: fact35 d10 MELON harvest>=3 or sold>0",
        d10_harv >= 3 or d10_sold > 0,
        f"harvest={d10_harv} sold={d10_sold}", seed,
    ))
    melon_buy_d0 = ep.get("melon_buy_d0", -1)
    plant_melon_d0 = ep.get("plant_melon_d0", -1)
    field_melon_d5 = ep.get("field_melon_d5", -1)
    checks.append(ctr(
        [36], f"seed {seed}: fact36 field MELON EOD d5 >=12",
        field_melon_d5 >= 12,
        f"field_d5={field_melon_d5}", seed,
    ))
    checks.append(ctr(
        [36], f"seed {seed}: fact36 d0 MELON buy>=10 or plant>=10",
        melon_buy_d0 >= 10 or plant_melon_d0 >= 10,
        f"buy_d0={melon_buy_d0} plant_d0={plant_melon_d0}", seed,
    ))
    nw_wheat = ep.get("nw_wheat_plant", -1)
    nw_straw = ep.get("nw_straw_plant", -1)
    checks.append(ctr(
        [38], f"seed {seed}: fact38 NW PLANT WHEAT>0",
        nw_wheat > 0,
        f"nw_wheat={nw_wheat}", seed,
    ))
    checks.append(ctr(
        [39], f"seed {seed}: fact39 NW PLANT STRAW=0 (no home refill)",
        nw_straw == 0,
        f"nw_straw={nw_straw}", seed,
    ))
    return checks


def fact_status(src_checks, counter_checks):
    """Aggregate pass/fail per fact ID across source + counters.

    Facts 1–36 + 38–39 are required. Fact 37 is PARKED (no checks).
    """
    fact_ids = [i for i in range(1, 40) if i != 37]
    by_fact = {i: {"src": [], "ctr": []} for i in fact_ids}
    for c in src_checks:
        for fid in c["facts"]:
            if fid in by_fact:
                by_fact[fid]["src"].append(c)
    for c in counter_checks:
        for fid in c["facts"]:
            if fid in by_fact:
                by_fact[fid]["ctr"].append(c)
    rows = []
    for fid in fact_ids:
        items = by_fact[fid]["src"] + by_fact[fid]["ctr"]
        if not items:
            rows.append((fid, None, "NO CHECK"))
            continue
        ok = all(c["ok"] for c in items)
        fails = [c["name"] for c in items if not c["ok"]]
        rows.append((fid, ok, "ok" if ok else "; ".join(fails)))
    return rows


def print_report(agent, src_checks, counter_checks):
    label = Path(agent).name
    print(f"\n{'=' * 60}")
    print(f"PRE-RUN AUDIT: {label}")
    print(f"{'=' * 60}")

    print("\n--- SOURCE CHECKS ---")
    src_pass = src_fail = 0
    for c in src_checks:
        mark = "PASS" if c["ok"] else "FAIL"
        if c["ok"]:
            src_pass += 1
        else:
            src_fail += 1
        print(f"  [{mark}] {c['name']}: {c['detail']}")

    print("\n--- EPISODE COUNTERS (seeds 0 + 8) ---")
    ctr_pass = ctr_fail = 0
    for c in counter_checks:
        mark = "PASS" if c["ok"] else "FAIL"
        if c["ok"]:
            ctr_pass += 1
        else:
            ctr_fail += 1
        print(f"  [{mark}] {c['name']}: {c['detail']}")

    print("\n--- PER-FACT STATUS ---")
    rows = fact_status(src_checks, counter_checks)
    fact_pass = fact_fail = fact_missing = 0
    for fid, ok, detail in rows:
        if ok is None:
            fact_missing += 1
            mark = "MISS"
        elif ok:
            fact_pass += 1
            mark = "PASS"
        else:
            fact_fail += 1
            mark = "FAIL"
        print(f"  [{mark}] fact {fid:02d}: {detail}")

    print(f"\n--- SUMMARY ---")
    print(f"  Source:  {src_pass}/{len(src_checks)} pass")
    print(f"  Counter: {ctr_pass}/{len(counter_checks)} pass")
    print(f"  Facts:   {fact_pass}/36 pass, {fact_fail} fail, {fact_missing} unchecked")
    shape_ok = fact_fail == 0 and fact_missing == 0
    print(f"  All-facts clear: {'YES' if shape_ok else 'NO'}")
    return shape_ok


def main():
    agents = [sys.argv[1]] if len(sys.argv) > 1 else [str(DEFAULT_AGENT)]

    results = {}
    for agent in agents:
        if not Path(agent).exists():
            print(f"SKIP missing {agent}")
            continue
        src = read_agent(agent)
        src_checks = run_src_audit(src)
        counter_checks = []
        for seed in SEEDS:
            print(f"running leftover {Path(agent).name} seed={seed} ...", flush=True)
            ep = run_episode(agent, seed)
            counter_checks.extend(run_counter_audit(ep))
        ok = print_report(agent, src_checks, counter_checks)
        results[agent] = ok

    if len(results) > 1:
        print(f"\n{'=' * 60}")
        print("COMPARISON")
        for agent, ok in results.items():
            print(f"  {Path(agent).name}: {'CLEAR' if ok else 'FAIL'}")

    # Non-zero exit if any agent fails (for scripting).
    if results and not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
