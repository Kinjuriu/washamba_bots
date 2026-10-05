"""WB_ValueModel: what one FERTILIZE and one tile-day are worth (Builder A, splice build).

Yield rules, ported from the engine (kaggriculture.py 1.32.7):
- One-shot crops (WHEAT, CARROT, MELON) start at 1 unit. Each WATER on a day inside the
  window [(max_yield_day + 1) // 2, max_yield_day] (plant age in days) adds 1, or 2 if the
  tile's fertilized_until_day >= that day, capped at max_yield. The bonus is decided when
  the WATER happens, so FERTILIZE must come before that day's WATER. Harvest from age
  first_yield_day; the tile decays from the start of day planted + max_yield_day + 1.
- Ongoing crops (TOMATO, STRAWBERRY) produce at the end of day X when
  X + 1 - planted - first_yield_day >= 0 and is a multiple of interval, up to max_yield
  events. An event adds 1, or 2 if the tile was watered on X and fertilized_until_day >= X
  (order within the day does not matter). Held stock caps at max_yield, so harvest between
  events.
- FERTILIZE on day d sets fertilized_until_day = max(current, d + 2): it covers days d..d+2.
- The last end-of-day refresh is day 28's (the episode ends after step 718), so the last
  production event is at the end of day 28 and the last harvest on day 29.

Prices: by default the measured median realized price by day and product (CURVES) in two
markets: 'tape' (tape vs tape: 72 local W3/W0/2945 games) and 'nontape' (real top-six
games vs non-tape opponents, 87 seats). Where a tape never sells a product on a day (e.g.
tomato before day 26), the 'tape' price is projected from the drain with WB_PriceModel.
With a live market, fertilize_value() prices the extra units at the current quote.

Build notes: stdlib only, WB_ / _wb_ prefixes, the import below is dropped by build.py.
"""
from price_model import WB_PriceModel  # noqa: F401  (dropped by build.py)

WB_VM_CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}
WB_VM_LAST_EOD = 28     # last end-of-day refresh the episode processes
WB_VM_LAST_DAY = 29     # last day with actions (steps 696..718)
WB_VM_FERT_PLAN = {"WHEAT": (2,), "CARROT": (2,), "TOMATO": (7, 10), "STRAWBERRY": (9, 13), "MELON": ()}

# Median realized price by day (index = day 0..29), measured; see the module docstring.
# 'tape' TOMATO is a drain-only projection with typical shops: tapes sell tomato only in
# tomato-rich worlds (measured 215-313 there), so price those live from the shops.
WB_VM_CURVES = {
    'tape': {
        'FERTILIZER': [100, 100, 98, 96, 94, 92, 90, 87, 83, 79, 77, 73, 67, 61, 55, 50, 46, 42, 37, 33, 32, 28, 24, 20, 18, 18, 16, 12, 8, 4],
        'WHEAT': [29, 29, 30, 30, 30, 31, 33, 33, 35, 37, 40, 41, 40, 43, 41, 41, 41, 41, 42, 42, 42, 42, 42, 41, 40, 40, 40, 39, 39, 36],
        'CARROT': [36, 36, 36, 36, 36, 36, 36, 36, 36, 36, 42, 42, 42, 42, 42, 58, 58, 58, 58, 59, 60, 61, 64, 57, 60, 62, 60, 60, 52, 44],
        'TOMATO': [60, 60, 60, 60, 60, 61, 61, 61, 61, 61, 62, 63, 64, 64, 65, 66, 67, 68, 69, 70, 72, 73, 75, 76, 78, 80, 81, 83, 84, 87],
        'STRAWBERRY': [211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 211, 207, 203, 197, 187, 173, 143, 78, 40, 11, 38, 37, 43, 30, 30],
        'MELON': [217, 217, 217, 217, 217, 217, 217, 217, 217, 217, 217, 106, 106, 106, 106, 106, 106, 106, 106, 106, 106, 106, 106, 106, 106, 106, 106, 106, 106, 106],
        'MILK': [207, 207, 207, 207, 207, 207, 207, 207, 207, 207, 201, 186, 180, 171, 144, 107, 68, 53, 50, 18, 22, 17, 26, 25, 41, 32, 35, 57, 38, 34],
        'WOOL': [201, 201, 201, 201, 201, 201, 201, 188, 188, 173, 173, 132, 132, 227, 44, 220, 2, 36, 4, 5, 5, 14, 33, 10, 18, 8, 43, 71, 32, 39],
        'EGG': [55, 55, 55, 55, 55, 55, 55, 55, 55, 55, 55, 55, 55, 56, 57, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 53, 54, 54, 54],
    },
    'nontape': {
        'FERTILIZER': [99, 99, 97, 95, 93, 91, 89, 86, 82, 78, 74, 70, 65, 60, 55, 50, 47, 43, 40, 36, 32, 29, 28, 25, 23, 22, 22, 20, 20, 16],
        'WHEAT': [28, 29, 30, 30, 30, 30, 31, 32, 34, 36, 40, 40, 40, 40, 39, 39, 38, 37, 37, 38, 38, 38, 38, 38, 38, 37, 36, 35, 31, 22],
        'CARROT': [48, 48, 48, 48, 48, 48, 48, 48, 48, 48, 48, 48, 48, 44, 44, 44, 43, 44, 43, 45, 46, 45, 46, 45, 44, 44, 42, 42, 40, 36],
        'TOMATO': [72, 72, 72, 72, 72, 72, 72, 72, 72, 72, 72, 72, 72, 72, 72, 72, 72, 77, 74, 75, 73, 72, 70, 69, 67, 67, 67, 66, 64, 62],
        'STRAWBERRY': [191, 191, 191, 191, 191, 191, 191, 191, 191, 191, 191, 191, 191, 191, 189, 187, 181, 170, 159, 134, 105, 101, 104, 96, 90, 92, 93, 91, 99, 90],
        'MELON': [243, 243, 243, 243, 243, 243, 243, 243, 243, 243, 243, 196, 148, 130, 130, 130, 130, 130, 132, 132, 132, 132, 132, 110, 110, 107, 107, 91, 91, 91],
        'MILK': [204, 204, 204, 204, 204, 204, 204, 204, 204, 204, 186, 205, 208, 209, 183, 153, 130, 89, 73, 67, 60, 60, 58, 59, 54, 57, 57, 44, 39, 35],
        'WOOL': [191, 191, 191, 191, 191, 191, 191, 191, 125, 125, 125, 64, 64, 170, 177, 96, 90, 138, 44, 58, 51, 49, 68, 88, 81, 120, 127, 66, 83, 45],
        'EGG': [52, 52, 52, 52, 52, 52, 52, 52, 52, 52, 52, 52, 52, 51, 51, 50, 48, 46, 44, 44, 44, 43, 43, 43, 42, 42, 42, 42, 42, 42],
    },
}
WB_VM_TAPE_SOLD = ("WHEAT", "CARROT", "STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "FERTILIZER")


def WB_vm_harvests(crop, planted_day, day, yield_units=None, fert_until=-1, watered_today=False,
                   fert_days=(), last_eod=WB_VM_LAST_EOD, last_day=WB_VM_LAST_DAY):
    """[(sale_day, units)] this tile still yields from `day` on, if it is watered every
    day (any FERTILIZE applied before that day's WATER) and harvested promptly.
    `fert_days` are the days a FERTILIZE is applied. Exact engine rules."""
    cd = WB_VM_CROPS[crop]
    f = fert_until
    fert = set(fert_days)
    if not cd["ongoing"]:
        y = 1 if yield_units is None else yield_units
        ws = (cd["max_yield_day"] + 1) // 2
        end = min(planted_day + cd["max_yield_day"], last_day)
        for d in range(day, end + 1):
            if d in fert:
                f = max(f, d + 2)
            if d == day and watered_today:
                continue                          # today's WATER already counted
            if ws <= d - planted_day <= cd["max_yield_day"]:
                y = min(cd["max_yield"], y + (2 if f >= d else 1))
        if end - planted_day < cd["first_yield_day"]:
            return []                             # cannot be harvested before the season ends
        return [(end, y)]
    out = []
    if yield_units:
        out.append((day, yield_units))
    for d in range(day, last_eod + 1):
        if d in fert:
            f = max(f, d + 2)
        dsf = d + 1 - planted_day - cd["first_yield_day"]
        if dsf < 0 or dsf % cd["interval"]:
            continue
        if dsf // cd["interval"] + 1 > cd["max_yield"]:
            continue
        out.append((d + 1, 2 if f >= d else 1))
    return out


def WB_vm_marginal_units(crop, age):
    """Extra units from one FERTILIZE at plant age `age` on a fresh, unfertilized,
    daily-watered tile (applied before that day's WATER)."""
    cd = WB_VM_CROPS[crop]
    held = None
    if not cd["ongoing"]:
        ws = (cd["max_yield_day"] + 1) // 2
        held = min(cd["max_yield"], 1 + max(0, min(age, cd["max_yield_day"] + 1) - ws))
    base = sum(u for _, u in WB_vm_harvests(crop, 0, age, yield_units=held))
    more = sum(u for _, u in WB_vm_harvests(crop, 0, age, yield_units=held, fert_days=(age,)))
    return more - base


class WB_ValueModel:
    def __init__(self, price_model, curves=None):
        self.pm = price_model
        self.curves = curves or WB_VM_CURVES

    # ---- prices -------------------------------------------------------------------
    def curve_price(self, product, day, scenario="tape"):
        vals = self.curves[scenario][product]
        return vals[max(0, min(len(vals) - 1, day))]

    def live_price(self, product, day, sale_day, market, shops, supply_per_day=0.0, scenario=None):
        """Drain-only projection of the live market to `sale_day` (plus `supply_per_day`
        units a day entering it), capped by the tape curve for products tapes flood."""
        inv = market["inventory"][product]
        drained = sum(self.pm.drain_per_step(product, shops, s) for s in range(day * 24, sale_day * 24))
        price = self.pm.quote(product, inv - drained + supply_per_day * (sale_day - day))
        if scenario == "tape" and product in WB_VM_TAPE_SOLD and sale_day > day:
            price = min(price, self.curve_price(product, sale_day, "tape"))
        return price

    # ---- item 1: one FERTILIZE ----------------------------------------------------
    def fertilize_value(self, tile_obs, day, market, shops=None, scenario=None):
        """Net value of one FERTILIZE on this tile today, applied before today's WATER.
        {'extra_units', 'gain', 'cost', 'net', 'apply'}: gain prices the extra units at the
        crop's live quote (or the live projection when `scenario` is given); cost is the
        fertilizer's sell quote now - what the unit fetches if sold instead."""
        t = tile_obs
        if not (isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") in WB_VM_CROPS):
            return {"extra_units": 0, "gain": 0.0, "cost": 0.0, "net": 0.0, "apply": False}
        crop = t["crop"]
        kw = dict(yield_units=t.get("yield_units"), fert_until=t.get("fertilized_until_day", -1),
                  watered_today=bool(t.get("watered_today")))
        base = WB_vm_harvests(crop, t["planted_day"], day, **kw)
        more = WB_vm_harvests(crop, t["planted_day"], day, fert_days=(day,), **kw)
        extra = sum(u for _, u in more) - sum(u for _, u in base)
        inv = market["inventory"]
        gain = 0.0
        if extra > 0:
            by_day = {}
            for d, u in more:
                by_day[d] = by_day.get(d, 0) + u
            for d, u in base:
                by_day[d] = by_day.get(d, 0) - u
            for d, u in by_day.items():
                if u > 0:
                    p = (self.pm.quote(crop, inv[crop]) if scenario is None
                         else self.live_price(crop, day, d, market, list(shops or []), scenario=scenario))
                    gain += u * p
        cost = float(self.pm.quote("FERTILIZER", inv["FERTILIZER"]))
        net = gain - cost
        return {"extra_units": extra, "gain": gain, "cost": cost, "net": net, "apply": extra > 0 and net > 0}

    # ---- item 2: one planting -----------------------------------------------------
    def crop_value(self, crop, plant_day, market=None, shops=None, scenario="tape", fertilize=True,
                   supply_per_day=0.0, day=None):
        """Value of planting `crop` on `plant_day`, watered daily and harvested promptly.
        Prices come from the scenario curve, or from the live market projection when
        `market` is given. Fertilizer is applied at WB_VM_FERT_PLAN ages when the extra
        units beat the fertilizer price that day. Returns units, revenue, seed, fert cost,
        net, tile-days, net per tile-day, labor turns and net per labor turn."""
        cd = WB_VM_CROPS[crop]
        today = plant_day if day is None else day

        def price(product, d):
            if market is None:
                return self.curve_price(product, d, scenario)
            return self.live_price(product, today, d, market, list(shops or []), supply_per_day, scenario)

        fert_days = []
        if fertilize:
            for age in WB_VM_FERT_PLAN[crop]:
                fd = plant_day + age
                if fd > WB_VM_LAST_DAY:
                    continue
                base = WB_vm_harvests(crop, plant_day, plant_day, fert_days=tuple(fert_days))
                more = WB_vm_harvests(crop, plant_day, plant_day, fert_days=tuple(fert_days) + (fd,))
                gain = sum(u * price(crop, d) for d, u in more) - sum(u * price(crop, d) for d, u in base)
                if gain > price("FERTILIZER", fd):
                    fert_days.append(fd)
        sales = WB_vm_harvests(crop, plant_day, plant_day, fert_days=tuple(fert_days))
        units = sum(u for _, u in sales)
        revenue = sum(u * price(crop, d) for d, u in sales)
        fert_cost = sum(price("FERTILIZER", d) for d in fert_days)
        net = revenue - cd["seed"] - fert_cost
        if cd["ongoing"]:
            last = max((d for d, _ in sales), default=plant_day)
            tile_days = min(last, WB_VM_LAST_DAY) - plant_day + 1
            waters = (tile_days + 1) // 2 + len(fert_days)          # survival + fertilized days
            labor = waters + 1 + len(sales) + 1 + len(fert_days)     # + PLANT, HARVESTs, DIG
        else:
            end = min(plant_day + cd["max_yield_day"], WB_VM_LAST_DAY)
            tile_days = end - plant_day + 1
            ws = (cd["max_yield_day"] + 1) // 2
            waters = 1 + max(0, end - (plant_day + ws) + 1)          # planting day + window days
            labor = waters + 2 + len(fert_days)                      # + PLANT, HARVEST
        return {"crop": crop, "plant_day": plant_day, "units": units, "revenue": revenue, "seed": cd["seed"],
                "fert_days": fert_days, "fert_cost": fert_cost, "net": net, "tile_days": tile_days,
                "per_tile_day": net / tile_days if tile_days > 0 else 0.0, "labor": labor,
                "per_labor": net / labor if labor else 0.0}
