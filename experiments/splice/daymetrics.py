"""Per-day farm metrics from an exactly simulated episode (instrumented engine).

Builder A, splice build. Shared by top6_extract.py (real ladder replays re-simulated from
their recorded actions; the re-simulation reproduces every recorded step exactly) and
compare.py (a live local episode), so both sides of a comparison are measured by the same
code. Not part of the agent build (build.py concatenates a fixed module list).

Instrumentation wraps engine functions that `interpreter` looks up at call time:
_apply_unit_action (effective unit actions), _commit_unit (executed trades at their
realized prices), _do_hire, _do_buy_land, _end_of_day / _daily_refresh_animals (feed and
care coverage just before the midnight reset). Everything else comes from the recorded
observations at dawn (obs step 24*d).

Day attribution: unit actions use the `day` the engine passes; market events use the step
counter of the interpreter call (the obs step the orders were decided on).
"""
import collections

import kaggle_environments.envs.kaggriculture.kaggriculture as K

from price_model import WB_PriceModel

PM = WB_PriceModel()
PRODUCTS = list(K.PRODUCTS)
CROPS = list(K.CROPS)
SPECIES = list(K.ANIMALS)
DAYS = 30
TPD = 24


class _Recorder:
    def __init__(self):
        self.reset()

    def reset(self):
        self.ev = [collections.defaultdict(collections.Counter) for _ in range(2)]   # seat -> day -> Counter
        self.market_farms = None
        self.market_step = 0
        self.eod_farms = None
        self.unit_seat = -1


REC = _Recorder()
_INSTALLED = False


def _tile_sig(tile):
    return dict(tile) if isinstance(tile, dict) else tile


def install():
    """Patch the engine once per process. Idempotent."""
    global _INSTALLED
    if _INSTALLED:
        return
    o_apply, o_market, o_commit = K._apply_unit_action, K._process_market, K._commit_unit
    o_hire, o_land, o_eod, o_refresh = K._do_hire, K._do_buy_land, K._end_of_day, K._daily_refresh_animals

    def apply(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity=100):
        if idx == 0:
            REC.unit_seat += 1
        seat = min(max(REC.unit_seat, 0), 1)
        c = REC.ev[seat][day]
        c["unit_turns"] += 1
        op = action[0] if isinstance(action, list) and action else None
        pos = K._farmer_position(farm, idx)
        if pos is None:
            return o_apply(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity)
        x, y = pos[0], pos[1]
        invs = private["inventories"]              # read without _farmer_inventory's append
        t0 = _tile_sig(farm["tiles"][y][x])
        inv0 = dict(invs[idx]) if idx < len(invs) else {}
        shed0 = dict(private["shed"])
        o_apply(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity)
        pos1 = K._farmer_position(farm, idx)
        t1 = _tile_sig(farm["tiles"][y][x])
        invs = private["inventories"]
        inv1 = invs[idx] if idx < len(invs) else {}
        if op == "PASS" or op is None:
            c["pass"] += 1
            return
        if tuple(pos1) != (x, y):
            c["move"] += 1
            return
        if t0 == t1 and inv0 == inv1 and shed0 == private["shed"]:
            c["noop"] += 1
            return
        if op == "FEED":
            c["feed"] += 1
        elif op == "CARE":
            c["care"] += 1
        elif op == "COLLECT_FERTILIZER":
            c["fert_collect"] += 1
        elif op == "FERTILIZE":
            c["fert_apply"] += 1
        elif op == "WATER":
            c["water"] += 1
        elif op == "HARVEST":
            for item, n in inv1.items():
                gained = n - inv0.get(item, 0)
                if gained > 0:
                    c["harvest:" + item] += gained
        elif op == "PLANT":
            c["plant:" + (t1.get("crop") if isinstance(t1, dict) else "?")] += 1
        elif op == "DIG":
            c["dig"] += 1
        elif op in ("BUILD_COOP", "BUILD_PASTURE"):
            c[op.lower()] += 1
        elif op == "PLACE" and isinstance(t1, dict) and "animal" in t1 and not (isinstance(t0, dict) and "animal" in t0):
            c["place:" + t1["animal"]] += 1
        else:
            c["shed_op"] += 1                       # DROP / PICKUP / shed PLACE

    def market(state, env):
        REC.market_farms = state[0].observation.farms
        REC.market_step = state[0].observation.get("step", 0)
        try:
            return o_market(state, env)
        finally:
            REC.unit_seat = -1                      # next call's unit actions start at seat 0

    def seat_of(farm, farms):
        return 0 if farms is not None and farm is farms[0] else 1

    def commit(op, item, price, farm, private, market_, shed_capacity=100):
        ok = o_commit(op, item, price, farm, private, market_, shed_capacity)
        if ok:
            c = REC.ev[seat_of(farm, REC.market_farms)][REC.market_step // TPD]
            if op == "SELL":
                c["sold:" + item] += 1
                c["rev:" + item] += price
            else:
                c[{"BUY_PRODUCT": "buy:", "BUY_SEED": "seed:", "BUY_ANIMAL": "animal:"}[op] + item] += 1
                c["spend"] += price
        return ok

    def hire(farm, private, board_size, mult=K.FARM_HAND_COST_MULT):
        n0, m0 = farm["hires_today"], farm["money"]
        o_hire(farm, private, board_size, mult)
        if farm["hires_today"] > n0:
            c = REC.ev[seat_of(farm, REC.market_farms)][REC.market_step // TPD]
            c["hire"] += 1
            c["spend"] += m0 - farm["money"]

    def land(farm, board_size):
        n0, m0 = len(farm["unlocked_quadrants"]), farm["money"]
        o_land(farm, board_size)
        if len(farm["unlocked_quadrants"]) > n0:
            c = REC.ev[seat_of(farm, REC.market_farms)][REC.market_step // TPD]
            c["land"] += 1
            c["spend"] += m0 - farm["money"]

    def eod(state, env, day):
        REC.eod_farms = state[0].observation.farms
        return o_eod(state, env, day)

    def refresh(farm, day):
        c = REC.ev[seat_of(farm, REC.eod_farms)][day]
        for row in farm["tiles"]:
            for t in row:
                if isinstance(t, dict) and "animal" in t:
                    c["eod_animals"] += 1
                    c["eod_fed"] += 1 if t.get("fed_today") else 0
                    c["eod_cared"] += 1 if t.get("cared_today") else 0
                    c["eod_fert_left"] += 1 if t.get("fertilizer_available") else 0
        return o_refresh(farm, day)

    K._apply_unit_action, K._process_market, K._commit_unit = apply, market, commit
    K._do_hire, K._do_buy_land, K._end_of_day, K._daily_refresh_animals = hire, land, eod, refresh
    _INSTALLED = True


def _dawn(obs, seat):
    farm = obs["farms"][seat]
    shed = obs["private"]["shed"]
    out = {"money_dawn": float(farm["money"])}
    owned = planted = empty = weeds = coop = pasture = empty_struct = 0
    crops = collections.Counter()
    animals = collections.Counter()
    for row in farm["tiles"]:
        for t in row:
            if t == "LOCKED":
                continue
            owned += 1
            if t is None:
                empty += 1
            elif t.get("kind") == "PLANT":
                planted += 1
                crops[t["crop"]] += 1
            elif t.get("kind") == "WEED":
                weeds += 1
            elif t.get("kind") in ("COOP", "PASTURE"):
                if t["kind"] == "COOP":
                    coop += 1
                else:
                    pasture += 1
                if "animal" in t:
                    animals[t["animal"]] += 1
                else:
                    empty_struct += 1
    out.update(tiles_owned=owned, tiles_planted=planted, tiles_empty=empty, weeds=weeds,
               coop=coop, pasture=pasture, structures_empty=empty_struct,
               animals_total=sum(animals.values()),
               animals_in_shed=sum(int(shed.get(a, 0)) for a in SPECIES))
    for crop in CROPS:
        out["planted_" + crop] = crops[crop]
    for a in SPECIES:
        out["animals_" + a] = animals[a]
    out.update(drain_by_product(obs["town"]["unlocked_shops"]))
    return out


def drain_by_product(shops):
    """Units per day the town will consume of each product with this shop list (market
    context: a premium price is only comparable between games with similar drain)."""
    shops = list(shops or [])
    return {"drain_" + p: PM.drain_per_day(p, shops) for p in PRODUCTS if p != "FERTILIZER"}


def shops_on_day(final_shops, day, interval=3):
    """The unlocked shop list at dawn of `day`, from the season's final list: one shop is
    appended at the end of every `interval`-th day (end of day 2, 5, ...), up to 8."""
    return list(final_shops)[:min(len(final_shops), day // interval)]


def _events(c, animals_dawn):
    out = {}
    rev_total = 0
    for p in PRODUCTS:
        n, r = c["sold:" + p], c["rev:" + p]
        out["sold_" + p] = n
        out["revenue_" + p] = r
        out["price_" + p] = (r / n) if n else None
        rev_total += r
        out["harvest_" + p] = c["harvest:" + p]
    out["revenue_total"] = rev_total
    for a in SPECIES:
        out["buy_animal_" + a] = c["animal:" + a]
    for crop in CROPS:
        out["buy_seed_" + crop] = c["seed:" + crop]
        out["plant_" + crop] = c["plant:" + crop]
    out["buy_WHEAT"] = c["buy:WHEAT"]
    out["buy_FERTILIZER"] = c["buy:FERTILIZER"]
    out["spend"] = c["spend"]
    out["hires"] = c["hire"]
    out["land_bought"] = c["land"]
    for k in ("feed", "care", "fert_collect", "fert_apply", "water", "dig", "move"):
        out[k] = c[k]
    out["unit_turns"] = c["unit_turns"]
    out["idle_frac"] = (c["pass"] + c["noop"]) / c["unit_turns"] if c["unit_turns"] else None
    animals = c["eod_animals"]
    out["fed_frac"] = c["eod_fed"] / animals if animals else None
    out["cared_frac"] = c["eod_cared"] / animals if animals else None
    out["fert_left"] = c["eod_fert_left"] if animals else None
    base = animals or animals_dawn
    out["feed_per_animal"] = c["feed"] / base if base else None
    out["care_per_animal"] = c["care"] / base if base else None
    return out


def per_day(steps, seat):
    """{metric: [value for day 0..29]} for one seat, from env.steps-shaped `steps`
    (steps[i][seat]["observation"]) plus the events recorded while they were simulated."""
    rows = []
    for d in range(DAYS):
        i = d * TPD
        if i >= len(steps):
            break
        dawn = _dawn(steps[i][seat]["observation"], seat)
        dawn.update(_events(REC.ev[seat][d], dawn["animals_total"]))
        rows.append(dawn)
    out = {k: [r[k] for r in rows] for k in rows[0]}
    return add_cumulative(out)


def add_cumulative(series):
    """Add running totals of the flows (idempotent): robust where a single day depends on
    production phase (cows yield every 2nd day, sheep every 3rd) or on the hour a batch sold."""
    for k in list(series):
        if k.startswith("cum_") or "cum_" + k in series:
            continue
        if k.startswith(("revenue_", "harvest_", "sold_")) or k in ("spend", "hires", "fert_collect", "fert_apply"):
            acc, cum = 0, []
            for v in series[k]:
                acc += v or 0
                cum.append(acc)
            series["cum_" + k] = cum
    return series


# Metrics compare.py ranks by default: the plan (assets, crops) and the outcomes (running
# revenue and harvest totals, realized premium prices), not engine bookkeeping.
HEADLINE = [
    "money_dawn", "tiles_owned", "tiles_planted", "hires", "cum_hires",
    "animals_COW", "animals_SHEEP", "animals_GOOSE", "animals_in_shed", "structures_empty",
    "planted_WHEAT", "planted_CARROT", "planted_TOMATO", "planted_STRAWBERRY", "planted_MELON",
    "cum_harvest_MILK", "cum_harvest_WOOL", "cum_harvest_EGG", "cum_harvest_STRAWBERRY",
    "cum_harvest_TOMATO", "cum_harvest_CARROT", "cum_harvest_WHEAT", "cum_harvest_MELON",
    "cum_revenue_total", "cum_revenue_MILK", "cum_revenue_WOOL", "cum_revenue_EGG",
    "cum_revenue_STRAWBERRY", "cum_revenue_TOMATO", "cum_revenue_CARROT", "cum_revenue_WHEAT",
    "cum_revenue_MELON", "cum_revenue_FERTILIZER", "cum_spend",
    "price_MILK", "price_WOOL", "price_STRAWBERRY",
    "fed_frac", "cared_frac", "cum_fert_collect", "cum_fert_apply", "water", "idle_frac",
]

# Scale floors for "how far outside the band" (the IQR can be 0 on a quiet day).
SCALE_FLOOR = {"money_dawn": 2000.0, "cum_revenue": 1000.0, "cum_spend": 1000.0, "revenue": 300.0,
               "price": 10.0, "spend": 300.0, "frac": 0.05, "per_animal": 0.05}


def scale_floor(metric):
    for key, v in SCALE_FLOOR.items():
        if metric.startswith(key) or metric.endswith(key):
            return v
    return 1.0
