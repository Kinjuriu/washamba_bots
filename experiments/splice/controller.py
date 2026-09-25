"""WB_Controller: the splice's reactive controller from day 8, hour 0 (Builder B).

Contract: docs/ENDGAME/splice_build.md. Spec: docs/research/FABLE_IDEAS.md (section 2,
section 4 "W3", R2.1 herd by day, R2.3 controller, R2.4 engine facts).

build.py concatenates this file after the base agent, price_model.py and sell_engine.py,
so every top-level name carries the WB_ / _wb_ prefix and the only imports are stdlib.
All mutable state lives on the instance: in local self-play both seats share this module.

Layers
  dawn planner (first call of each day): herd purchases valued on the projected price of
    the product (own + opponent's visible supply against shop drain), crops chosen by
    projected price at harvest, land, structures and the day's crew size.
  executor (every turn): a task list read straight off the observation, then a global
    greedy match of units to tasks on value / (travel + 1) with stickiness. A unit that
    plants waters the same tile next turn (the planting is urgent-to-water), so PLANT is
    always paired with a same-day WATER.
  market arbiter: at most 10 orders. Inclusion by priority (critical buys, sells, hires,
    seeds, land); slot order puts sells first so their cash lands before the buys.
"""
import math as _wb_math
import traceback as _wb_traceback

WB_CTRL_VERSION = "b1"

_WB_TPD = 24
_WB_BOARD = 10
_WB_FINAL_STEP = 718           # last obs step whose action the engine processes (720 steps)
_WB_LAST_PROD_DAY = 28         # last day whose end-of-day refresh runs inside the episode
_WB_SHED = ((4, 4), (5, 4), (4, 5), (5, 5))
_WB_MAX_ORDERS = 10
_WB_SHED_CAP = 100

_WB_CROPS = {
    "WHEAT":      {"seed": 10,  "fy": 2,  "my": 4,  "iv": 0, "mx": 6, "on": False},
    "CARROT":     {"seed": 20,  "fy": 2,  "my": 3,  "iv": 0, "mx": 4, "on": False},
    "TOMATO":     {"seed": 50,  "fy": 8,  "my": 8,  "iv": 1, "mx": 4, "on": True},
    "STRAWBERRY": {"seed": 100, "fy": 10, "my": 10, "iv": 2, "mx": 4, "on": True},
    "MELON":      {"seed": 80,  "fy": 10, "my": 12, "iv": 0, "mx": 6, "on": False},
}
_WB_ANIMALS = {
    "GOOSE": {"cost": 300, "st": "COOP",    "fy": 4, "iv": 1, "mx": 4, "prod": "EGG"},
    "COW":   {"cost": 400, "st": "PASTURE", "fy": 8, "iv": 2, "mx": 6, "prod": "MILK"},
    "SHEEP": {"cost": 500, "st": "PASTURE", "fy": 6, "iv": 3, "mx": 6, "prod": "WOOL"},
}
_WB_PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
_WB_SHOP_TABLE = {
    "BAKERY":         ("EGG", "WHEAT"),
    "PIZZA_SHOP":     ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT":    ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE":     ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE":       ("CARROT",),
    "SMOOTHIE_SHOP":  ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
_WB_LAND_PRICES = (1000, 2000, 4000)   # NE, SW, SE in unlock order
_WB_MAX_QUADS = 3                      # never buy the fourth quadrant (SE, 4000)

# Steady-state supply per tile / animal, units per day (daily care assumed for animals).
_WB_CROP_RATE = {"WHEAT": 1.0, "CARROT": 1.0, "TOMATO": 4.0 / 12.0, "STRAWBERRY": 4.0 / 17.0, "MELON": 6.0 / 13.0}
_WB_ANIMAL_RATE = {"GOOSE": 2.0, "COW": 1.5, "SHEEP": 4.0 / 3.0}
# Unit actions a crop needs per planting (plant, waters, harvests, dig) and an animal per day.
_WB_CROP_ACTIONS = {"WHEAT": 6.0, "CARROT": 5.0, "TOMATO": 9.0, "STRAWBERRY": 13.0, "MELON": 10.0}
_WB_ANIMAL_ACTIONS = 3.6

# Executor task weights. Every must-do-today task sits in one tier with nearly equal
# weight, so the unit-task matching on weight / (travel + 1) is nearest-first inside the
# tier: the order of must-do work does not change its value, only the travel it costs.
# Weights escalate late in the day for tasks with a midnight deadline (escape, weed).
WB_W_FEED = 100.0
WB_W_CARE = 92.0
WB_W_COLLECT = 70.0
WB_W_COLLECT_CHEAP = 35.0      # fertilizer quote under 30
WB_W_WATER_URGENT = 100.0      # consecutive_unwatered == 1: weeds tonight otherwise
WB_W_WATER_WINDOW = 88.0       # one-shot crop inside its yield window: +1 unit now
WB_W_WATER_FERT = 80.0         # ongoing crop, fertilized, producing tonight
WB_W_WATER_MAINT = 12.0        # optional: resets the counter a day early
WB_W_HARVEST_DUE = 95.0        # done growing, capping tonight, or decaying
WB_W_HARVEST_OPT = 22.0
WB_FEED_MARGIN = 1.2            # feed when its payout beats this many wheat
WB_W_HARVEST_ONGOING = 70.0     # ongoing crop holding 2+: the tile caps at 4
WB_W_HARVEST_RACE = 600.0      # premium one-shot crop the opponent is about to dump too
WB_W_PLANT = 82.0
WB_W_DIG = 30.0
WB_W_BUILD = 96.0
WB_W_PLACE = 150.0
WB_W_PICKUP_WHEAT = 98.0
WB_W_PICKUP_ANIMAL = 120.0
WB_W_DROP_RACE = 700.0
WB_W_DROP_FINAL = 220.0
WB_W_DROP_AT_SHED = 25.0
WB_DROP_MIN_VALUE = 250.0      # carried premium goods worth a trip to the shed
WB_DROP_FRAC = 0.12
WB_W_DROP_MAX = 150.0
_WB_DROP_ITEMS = ("MILK", "WOOL", "STRAWBERRY", "MELON", "TOMATO", "EGG", "CARROT", "FERTILIZER")
WB_STICKY = 1.2
WB_ACTION_COST = 15.0          # shadow price of one unit action (labour binds at ~12 hands)
WB_PICKUP_CAP = 8              # wheat one unit takes per pickup
WB_MAX_HANDS = 12              # the 13th hire of a day costs 233, the 12th 144
WB_MIN_HANDS = 11              # W3 runs 11; a hand under that costs at most 89 a day
WB_ZONE_OUT = 0.35             # rate factor for a task outside the unit's zone
WB_HERD_PER_HERDER = 4         # animals one herder serves (feed, care, collect, harvest)
WB_CARRIER_FEED = 1.6          # a wheat carrier's feed tasks outrank its other must-dos
WB_W_FERT = 78.0               # apply carried fertilizer where it adds units
WB_W_PICKUP_FERT = 60.0
# Crops the planner may plant after handover. STRAWBERRY and MELON are the opening tapes'
# crops (W3 grows 33 strawberry tiles and dumps 72 melons on day 10), so a new planting
# there sells into a glut the opponent is already building.
WB_PLANT_CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY")
# Unit actions per day one tile or animal needs (watering, harvest, replant, fertilizer),
# and the unit-turns one action costs including travel. Used to cap the day's plantings
# at what the crew can service.
_WB_TILE_LOAD = {"WHEAT": 1.6, "CARROT": 1.7, "TOMATO": 0.9, "STRAWBERRY": 0.9, "MELON": 1.0}
WB_WHEAT_PER_ANIMAL = 1.2      # wheat tiles per animal: feed self-sufficiency plus sales
WB_HERD_CUTOFF = {"GOOSE": 17, "COW": 14, "SHEEP": 13}   # last purchase day per species
WB_GOOSE_EXTRA = 2             # geese above the opponent's count (eggs are glut-proof)
WB_TOMATO_FIRST_DAY = 13       # tomato scarcity builds all season: produce into the spike
WB_TOMATO_LAST_DAY = 18        # a tomato planted later misses most of its 4 productions
WB_STRAWBERRY_EXTRA = 2        # strawberry tiles above the opponent's count
WB_TOMATO_MAX = 20
WB_STRAWBERRY_LAST_DAY = 13    # productions at +9,+11,+13,+15 must land by day 28
WB_STRAWBERRY_MAX = 36
WB_CARROT_MAX = 18
_WB_ANIMAL_LOAD = 3.6
_WB_TURNS_PER_ACTION = 1.85
# Units one planting yields with fertilizer applied (max_yield caps), used when the day's
# fertilizer use is on: wheat 6 (vs 4), carrot 4 (vs 3), tomato 8 (vs 4, two applications).
_WB_FERT_UNITS = {"WHEAT": 6, "CARROT": 4, "TOMATO": 8}
_WB_FERT_NEED = {"WHEAT": 1, "CARROT": 1, "TOMATO": 2}


def _wb_fib(n):
    a, b = 1, 1
    for _ in range(max(0, int(n))):
        a, b = b, a + b
    return a


def _wb_dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _wb_near_shed(pos):
    best = _WB_SHED[0]
    bd = 99
    for s in _WB_SHED:
        d = abs(pos[0] - s[0]) + abs(pos[1] - s[1])
        if d < bd:
            best, bd = s, d
    return best


def _wb_atan2(y, x):
    return _wb_math.atan2(y, x)


def _wb_quadrant(x, y):
    return ("N" if y < _WB_BOARD // 2 else "S") + ("W" if x < _WB_BOARD // 2 else "E")


def _wb_in_window(crop, age):
    c = _WB_CROPS[crop]
    if c["on"]:
        return False
    return (c["my"] + 1) // 2 <= age <= c["my"]


def _wb_animal_prod_tonight(tile, day):
    """True when the end-of-day refresh for `day` is a production day for this animal."""
    a = _WB_ANIMALS[tile["animal"]]
    dsf = day + 1 - int(tile["placed_day"]) - a["fy"]
    return dsf >= 0 and dsf % a["iv"] == 0


def _wb_next_prod_after(tile, day):
    """First production day P > day (production credited at the end of day P)."""
    a = _WB_ANIMALS[tile["animal"]]
    placed = int(tile["placed_day"])
    first = placed + a["fy"] - 1
    if day < first:
        return first
    k = (day - first) // a["iv"] + 1
    return first + k * a["iv"]


def _wb_crop_prod_tonight(tile, day):
    c = _WB_CROPS[tile["crop"]]
    if not c["on"]:
        return False
    dsf = day + 1 - int(tile["planted_day"]) - c["fy"]
    if dsf < 0 or dsf % c["iv"] != 0:
        return False
    return dsf // c["iv"] + 1 <= c["mx"]


def _wb_expected_drain_growth(product, day):
    """Expected extra units/day of drain per future shop unlock (shops drawn uniformly)."""
    tot = 0.0
    for prods in _WB_SHOP_TABLE.values():
        if product in prods:
            tot += 12.0 if len(prods) == 1 else 6.0
    return tot / len(_WB_SHOP_TABLE)


def _wb_shops_unlocked_by(day):
    """Shop instances unlocked at the start of `day` (one per 3 days, capped at 8)."""
    return min(8, (day) // 3)


class _WB_View:
    """Per-turn parse of the observation. Dict access only (obs may be a Struct)."""

    def __init__(self, obs):
        self.obs = obs
        self.me = int(obs["player"])
        self.step = int(obs["step"])
        self.day = self.step // _WB_TPD
        self.hour = self.step % _WB_TPD
        farms = obs["farms"]
        self.farm = farms[self.me]
        self.opp = farms[1 - self.me] if len(farms) > 1 else None
        self.tiles = self.farm["tiles"]
        self.money = float(self.farm["money"])
        self.units = [tuple(self.farm["farmer"])] + [tuple(h) for h in (self.farm.get("hands") or [])]
        priv = obs["private"]
        self.shed = {k: int(v) for k, v in priv["shed"].items()}
        self.seeds = {k: int(v) for k, v in priv["seeds"].items()}
        invs = priv.get("inventories") or [{}]
        self.invs = []
        for i in range(len(self.units)):
            src = invs[i] if i < len(invs) else {}
            self.invs.append({k: int(n) for k, n in src.items() if int(n) > 0})
        self.minv = {k: float(v) for k, v in obs["market"]["inventory"].items()}
        self.prices = {k: float(v) for k, v in obs["market"]["prices"].items()}
        self.shops = list(obs["town"].get("unlocked_shops") or [])
        self.quads = list(self.farm.get("unlocked_quadrants") or ["NW"])
        self.hires_today = int(self.farm.get("hires_today", 0) or 0)
        # tile census
        self.plants, self.animals, self.weeds, self.empty, self.structs = [], [], [], [], []
        for y in range(_WB_BOARD):
            row = self.tiles[y]
            for x in range(_WB_BOARD):
                t = row[x]
                if t is None:
                    self.empty.append((x, y))
                elif isinstance(t, dict):
                    k = t.get("kind")
                    if k == "PLANT":
                        self.plants.append((x, y, t))
                    elif "animal" in t:
                        self.animals.append((x, y, t))
                    elif k == "WEED":
                        self.weeds.append((x, y))
                    elif k in ("COOP", "PASTURE"):
                        self.structs.append((x, y, k))

    def price(self, item):
        return max(1.0, self.prices.get(item, 1.0))

    def shed_total(self):
        return sum(self.shed.values())

    def carried(self, item):
        return sum(inv.get(item, 0) for inv in self.invs)

    def carried_total(self):
        return sum(sum(inv.values()) for inv in self.invs)


def _wb_supply(farm):
    """Units/day per product a farm's board is set up to produce (steady-state rates)."""
    s = {p: 0.0 for p in _WB_PRODUCTS}
    if not farm:
        return s
    for row in farm["tiles"]:
        for t in row:
            if isinstance(t, dict):
                if t.get("kind") == "PLANT":
                    s[t["crop"]] += _WB_CROP_RATE.get(t["crop"], 0.0)
                elif "animal" in t:
                    a = t["animal"]
                    s[_WB_ANIMALS[a]["prod"]] += _WB_ANIMAL_RATE[a]
                    s["FERTILIZER"] += 1.0
    return s


def _wb_herd(farm):
    h = {a: 0 for a in _WB_ANIMALS}
    if not farm:
        return h
    for row in farm["tiles"]:
        for t in row:
            if isinstance(t, dict) and "animal" in t:
                h[t["animal"]] += 1
    return h


def _wb_fallback(obs):
    """Safe action when the controller raised: water/feed/care what the unit stands on,
    else PASS. No movement, no market orders. Never the base tape."""
    me = int(obs["player"])
    farm = obs["farms"][me]
    tiles = farm["tiles"]
    invs = obs["private"].get("inventories") or [{}]
    units = [farm["farmer"]] + list(farm.get("hands") or [])
    out = []
    for i, pos in enumerate(units):
        x, y = int(pos[0]), int(pos[1])
        t = tiles[y][x]
        inv = invs[i] if i < len(invs) else {}
        act = ["PASS"]
        if isinstance(t, dict):
            if t.get("kind") == "PLANT" and not t.get("watered_today"):
                act = ["WATER"]
            elif "animal" in t:
                if not t.get("fed_today") and int(inv.get("WHEAT", 0)) > 0:
                    act = ["FEED"]
                elif not t.get("cared_today"):
                    act = ["CARE"]
                elif t.get("fertilizer_available"):
                    act = ["COLLECT_FERTILIZER"]
        out.append(act)
    return {"farmer": out[0], "hands": out[1:], "market": []}


class WB_Controller:
    """Plays every unit and market order from the handover step on."""

    shadow = False     # dev switch: fixed W3-like plan, to measure the executor alone

    def __init__(self, price_model=None, sell_engine=None):
        self.pm = price_model
        self.se = sell_engine
        self.errors = 0
        self.last_error = None
        self.log = []
        self.plan = None
        self.plan_day = -1
        self.prev = {}
        self.stats = {"turns": 0, "fallback": 0, "sell_err": 0}

    # ------------------------------------------------------------------ entry point
    def act(self, obs):
        self.last_error = None
        self.stats["turns"] += 1
        try:
            return self._act(obs)
        except Exception:
            self.errors += 1
            self.stats["fallback"] += 1
            self.last_error = _wb_traceback.format_exc()[-600:]
            try:
                return _wb_fallback(obs)
            except Exception:
                return {"farmer": ["PASS"], "hands": [], "market": []}

    def _note(self, msg):
        if len(self.log) < 3000:
            self.log.append(msg)

    def _act(self, obs):
        v = _WB_View(obs)
        if v.day != self.plan_day or self.plan is None:
            self.plan_day = v.day
            self.prev = {}
            try:
                self.plan = self._dawn(v)
            except Exception:
                self.errors += 1
                self.last_error = _wb_traceback.format_exc()[-600:]
                self.plan = self._default_plan(v)
        elif v.hour in (6, 12) and self.plan.get("herd_hour") != v.hour and not self.shadow:
            try:
                self.plan["fc"] = self._forecast(v)
                self._plan_herd(v, self.plan)
            except Exception:
                self.errors += 1
                self.last_error = _wb_traceback.format_exc()[-600:]
        actions, info = self._execute(v)
        try:
            market = self._market(v, info)
        except Exception:
            self.errors += 1
            self.last_error = _wb_traceback.format_exc()[-600:]
            market = []
        return {"farmer": actions[0], "hands": actions[1:], "market": market}

    # ------------------------------------------------------------------ price helpers
    def _quote(self, item, inv):
        if self.pm is not None:
            try:
                return float(self.pm.quote(item, inv))
            except Exception:
                pass
        return float(_WB_BASE_FALLBACK.get(item, 1))

    def _drain_day(self, item, shops):
        if self.pm is not None:
            try:
                return float(self.pm.drain_per_day(item, shops))
            except Exception:
                pass
        n = 1.0 if item != "FERTILIZER" else 0.0
        for s in shops:
            prods = _WB_SHOP_TABLE.get(s, ())
            if item in prods:
                n += 12.0 if len(prods) == 1 else 6.0
        return n

    # ------------------------------------------------------------------ dawn planner
    def _default_plan(self, v):
        return {"crop_order": ["WHEAT", "CARROT"], "quota": {}, "buy": {}, "build": [],
                "hands": 8, "land": False, "last_plant_day": 27, "dig_structs": {},
                "plant_value": 20.0, "herd_hour": -1}

    def _forecast(self, v):
        """Projected market inventory per product from what both boards visibly have in
        the pipe (one-shot crops land on their harvest day, ongoing crops per production,
        animals as a daily rate), our own unsold stock, and shop drain including the
        expected drain of shops still to unlock (one every third day, drawn uniformly)."""
        now = v.day + v.hour / 24.0
        cum = {p: [0.0] * 32 for p in _WB_PRODUCTS}
        rate = {p: 0.0 for p in _WB_PRODUCTS}
        for farm in (v.farm, v.opp):
            if not farm:
                continue
            for row in farm["tiles"]:
                for t in row:
                    if not isinstance(t, dict):
                        continue
                    if t.get("kind") == "PLANT":
                        crop = t["crop"]
                        c = _WB_CROPS[crop]
                        pd = int(t["planted_day"])
                        if not c["on"]:
                            hd = pd + (10 if crop == "MELON" else c["my"])
                            full = 6 if crop == "MELON" else min(c["mx"], 1 + c["my"] - (c["my"] + 1) // 2 + 1)
                            units = max(int(t.get("yield_units", 1)), full)
                            dd = min(31, max(v.day, hd) + 1)
                            cum[crop][dd] += units
                        else:
                            for k in range(c["mx"]):
                                pday = pd + c["fy"] - 1 + k * c["iv"]
                                if v.day <= pday <= _WB_LAST_PROD_DAY:
                                    cum[crop][min(31, pday + 1)] += 1
                    elif "animal" in t:
                        a = t["animal"]
                        rate[_WB_ANIMALS[a]["prod"]] += _WB_ANIMAL_RATE[a]
                        rate["FERTILIZER"] += 0.9
                        rate["WHEAT"] -= 1.0      # feed: eaten from own crop or bought
        # our own unsold stock reaches the market soon
        for p in _WB_PRODUCTS:
            held = v.shed.get(p, 0) + v.carried(p)
            if p == "WHEAT":
                held = max(0, held - 2 * len(v.animals))
            cum[p][min(31, v.day + 1)] += held
        for p in _WB_PRODUCTS:
            acc = 0.0
            arr = cum[p]
            for d in range(32):
                acc += arr[d]
                arr[d] = acc
        drain = {p: self._drain_day(p, v.shops) for p in _WB_PRODUCTS}
        grow = {p: (_wb_expected_drain_growth(p, v.day) if p != "FERTILIZER" else 0.0) for p in _WB_PRODUCTS}
        unlocks = [3 * k for k in range(len(v.shops) + 1, 9) if 3 * k > now]
        return {"now": now, "cum": cum, "rate": rate, "drain": drain, "grow": grow,
                "unlocks": unlocks, "inv": dict(v.minv)}

    @staticmethod
    def _proj(fc, p, t, extra=None):
        now = fc["now"]
        if t < now:
            t = now
        inv = fc["inv"].get(p, 10000.0)
        inv += fc["cum"][p][min(31, max(0, int(t)))]
        if extra:
            for (d, u) in extra:
                if d <= t:
                    inv += u
        inv += (fc["rate"][p] - fc["drain"][p]) * (t - now)
        g = fc["grow"][p]
        if g:
            for u in fc["unlocks"]:
                if u < t:
                    inv -= g * (t - u)
        return inv

    def _crop_eval(self, crop, v, fc, extra, fert_use=None):
        """(value, occupancy days, units, sale events) of one planting of `crop` today."""
        c = _WB_CROPS[crop]
        d0 = v.day
        fert = bool(fert_use and fert_use.get(crop))
        fert_cost = fc.get("fert_price", 0.0) * _WB_FERT_NEED.get(crop, 0) if fert else 0.0
        actions = _WB_CROP_ACTIONS[crop] + (_WB_FERT_NEED.get(crop, 0) if fert else 0)
        if not c["on"]:
            if crop == "MELON":
                h = d0 + 10
                full = 6
            else:
                h = d0 + c["my"]
                full = min(c["mx"], 1 + (c["my"] - (c["my"] + 1) // 2 + 1))
                if fert:
                    full = _WB_FERT_UNITS.get(crop, full)
            if h > 29:
                if d0 + c["fy"] > 29:
                    return -1.0, 1, 0, ()
                ws = d0 + (c["my"] + 1) // 2
                units = min(c["mx"], 1 + max(0, 29 - ws + 1) * (2 if fert else 1))
                h = 29
            else:
                units = full
            sale = h + 0.6
            price = self._quote(crop, self._proj(fc, crop, sale, extra.get(crop)) + units * 0.5)
            value = units * price - c["seed"] - WB_ACTION_COST * actions - fert_cost
            return value, max(1, h - d0), units, ((sale, units),)
        prods = [d0 + c["fy"] - 1 + k * c["iv"] for k in range(c["mx"])]
        valid = [p for p in prods if p <= _WB_LAST_PROD_DAY]
        if not valid:
            return -1.0, 1, 0, ()
        per = 2 if fert else 1
        value = -c["seed"] - (WB_ACTION_COST * actions + fert_cost) * len(valid) / c["mx"]
        evs = []
        for p in valid:
            value += per * self._quote(crop, self._proj(fc, crop, p + 1.5, extra.get(crop)))
            evs.append((p + 1.5, per))
        occ = min(29, valid[-1] + 2) - d0
        return value, max(1, occ), per * len(valid), tuple(evs)

    def _animal_eval(self, animal, v, fc, extra, place_day):
        """Net value of buying one `animal` placed on `place_day`, fed and cared daily."""
        a = _WB_ANIMALS[animal]
        prod = a["prod"]
        first = place_day + a["fy"] - 1
        value = -a["cost"]
        evs = []
        p = first
        k = 0
        while p <= _WB_LAST_PROD_DAY:
            units = min(a["mx"], 1 + (p - place_day + 1)) if k == 0 else min(a["mx"], 1 + a["iv"])
            value += units * self._quote(prod, self._proj(fc, prod, p + 1.5, extra.get(prod)) + units * 0.5)
            evs.append((p + 1.5, units))
            p += a["iv"]
            k += 1
        days = max(0, _WB_LAST_PROD_DAY - place_day + 1)
        wheat = self._quote("WHEAT", fc["inv"].get("WHEAT", 10000.0) - 1)
        fert = self._quote("FERTILIZER", self._proj(fc, "FERTILIZER", place_day + days * 0.5))
        value += days * (0.8 * fert - wheat - WB_ACTION_COST * _WB_ANIMAL_ACTIONS)
        return value, tuple(evs)

    def _shadow_plan(self, v):
        """W3-shadow: no economics. Wheat on every free tile, empty pastures refilled with
        cows, 11 hands, land once affordable, no fertilizer use. Measures the executor."""
        plan = self._default_plan(v)
        free = len(v.empty) + len(v.weeds)
        for (x, y, t) in v.plants:
            c = _WB_CROPS[t["crop"]]
            if not c["on"] and v.day - int(t["planted_day"]) >= (10 if t["crop"] == "MELON" else c["my"]):
                free += 1
        plan["quota"] = {"WHEAT": free}
        plan["crop_order"] = ["WHEAT"]
        plan["fert_use"] = {}
        plan["hands"] = 11
        extra_q = len(v.quads) - 1
        plan["land"] = extra_q <= 1 and v.day <= 15
        plan["land_cost"] = _WB_LAND_PRICES[min(extra_q, 2)]
        pastures = sum(1 for (_x, _y, k) in v.structs if k == "PASTURE")
        waiting = v.shed.get("COW", 0) + v.carried("COW")
        n = max(0, pastures - waiting)
        n = min(n, int(max(0.0, v.money - 600) // 400))
        plan["buy"] = {"COW": n} if n > 0 else {}
        plan["build"] = []
        plan["dig_structs"] = {}
        plan["herd_hour"] = v.hour
        self._note(f"d{v.day} SHADOW money={v.money:.0f} free={free} buy={plan['buy']} land={plan['land']}")
        return plan

    def _dawn(self, v):
        if self.shadow:
            return self._shadow_plan(v)
        day = v.day
        fc = self._forecast(v)
        plan = self._default_plan(v)
        herd = _wb_herd(v.farm)
        opp_herd = _wb_herd(v.opp)
        n_animals = sum(herd.values())

        # ---------------- land: the next quadrant, but never the last one (SE, 4000)
        extra_q = len(v.quads) - 1
        plan["land"] = False
        if extra_q <= 1 and day <= 15:
            plan["land_cost"] = _WB_LAND_PRICES[extra_q]
            plan["land"] = True

        # ---------------- fertilizer: apply it where the extra units beat its sale price
        fp = self._quote("FERTILIZER", v.minv.get("FERTILIZER", 10000.0))
        fc["fert_price"] = fp
        fert_use = {}
        for crop in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"):
            gain = {"WHEAT": 2.0, "CARROT": 1.0, "TOMATO": 2.0, "STRAWBERRY": 1.5}[crop]
            fert_use[crop] = gain * v.price(crop) > 1.6 * fp + 2 * WB_ACTION_COST
        plan["fert_use"] = fert_use

        plan["fc"] = fc
        self._plan_herd(v, plan)

        # ---------------- crops: greedy per free tile on projected value per tile-day,
        # capped at the load the largest affordable crew can service
        free = len(v.empty) + len(v.weeds) - len(plan["build"])
        load = (n_animals + sum(plan["buy"].values())) * _WB_ANIMAL_LOAD
        for (x, y, t) in v.plants:
            c = _WB_CROPS[t["crop"]]
            age = day - int(t["planted_day"])
            if not c["on"] and age >= (10 if t["crop"] == "MELON" else c["my"]):
                free += 1          # harvested today, replantable
            else:
                load += _WB_TILE_LOAD.get(t["crop"], 1.0)
        cap = (WB_MAX_HANDS + 1) * 23.0 / _WB_TURNS_PER_ACTION
        targets = self._crop_targets(v, n_animals + sum(plan["buy"].values()))
        ours = {c: 0 for c in _WB_CROPS}
        for (x, y, t) in v.plants:
            c = _WB_CROPS[t["crop"]]
            if c["on"] or day - int(t["planted_day"]) < c["my"]:
                ours[t["crop"]] += 1
        planned = {}
        left = max(0, free)
        for crop, target in targets:
            want = max(0, target - ours.get(crop, 0) - planned.get(crop, 0))
            while want > 0 and left > 0 and load + _WB_TILE_LOAD[crop] <= cap:
                planned[crop] = planned.get(crop, 0) + 1
                load += _WB_TILE_LOAD[crop]
                want -= 1
                left -= 1
        filler = "WHEAT" if day <= 27 else None
        while filler and left > 0 and load + _WB_TILE_LOAD[filler] <= cap:
            planned[filler] = planned.get(filler, 0) + 1
            load += _WB_TILE_LOAD[filler]
            left -= 1
        plan["quota"] = planned
        order = [c for c, _t in targets] + ["WHEAT"]
        plan["crop_order"] = [c for i, c in enumerate(order) if c in planned and c not in order[:i]] or ["WHEAT"]
        plan["targets"] = targets
        plan["last_plant_day"] = 27

        # ---------------- crew size from today's load (plantings day: plant + water extra)
        work = load + sum(planned.values()) * 1.2 + len(v.weeds) + len(plan["build"]) * 2 + 4
        hands = int(work * _WB_TURNS_PER_ACTION / 23.0 + 0.5) - 1
        floor = WB_MIN_HANDS if day >= 10 else WB_MIN_HANDS - 2
        plan["hands"] = max(floor, min(WB_MAX_HANDS, hands))
        plan["work"] = round(work, 1)
        self._note(f"d{day} money={v.money:.0f} herd={herd} opp_herd={opp_herd} buy={plan['buy']} "
                   f"build={len(plan['build'])} quota={planned} hands={plan['hands']} work={work:.0f} "
                   f"land={plan['land']} shops={len(v.shops)}")
        return plan

    def _crop_targets(self, v, n_animals):
        """Ordered (crop, target tile count) list for today's plantings.
        1. WHEAT floor: feed self-sufficiency (WB_WHEAT_PER_ANIMAL tiles per animal).
        2. TOMATO where a shop consumes it: nobody in the tape family supplies it until
           late, the hinge curve spikes with scarcity (seed 1: 611/unit).
        3. STRAWBERRY: mirror the opponent's tiles while a planting still completes its
           four productions. Its market is the opponent's biggest (W3: 21k in self-play,
           47k when uncontested) and every unit we sell first is a unit it sells lower.
        4. CARROT where a shop consumes it, about its drain.
        Whatever is left is WHEAT (deep market, feed)."""
        day = v.day
        opp = {c: 0 for c in _WB_CROPS}
        if v.opp:
            for row in v.opp["tiles"]:
                for t in row:
                    if isinstance(t, dict) and t.get("kind") == "PLANT":
                        opp[t["crop"]] += 1
        out = []
        if day <= WB_STRAWBERRY_LAST_DAY:
            out.append(("STRAWBERRY", min(WB_STRAWBERRY_MAX, opp["STRAWBERRY"] + WB_STRAWBERRY_EXTRA)))
        shop_prods = set()
        for s in v.shops:
            shop_prods.update(_WB_SHOP_TABLE.get(s, ()))
        if WB_TOMATO_FIRST_DAY <= day <= WB_TOMATO_LAST_DAY and "TOMATO" in shop_prods:
            drain = self._drain_day("TOMATO", v.shops) + _wb_expected_drain_growth("TOMATO", day) * 2
            want = int(0.8 * drain / 0.5 + 0.5)
            out.append(("TOMATO", max(opp["TOMATO"], min(WB_TOMATO_MAX, want))))
        out.append(("WHEAT", int(WB_WHEAT_PER_ANIMAL * n_animals + 0.999)))
        if "CARROT" in shop_prods:
            drain = self._drain_day("CARROT", v.shops)
            want = int(0.9 * drain + 0.5)
            out.append(("CARROT", max(0, min(WB_CARROT_MAX, want))))
        return out

    def _plan_herd(self, v, plan):
        """Animal purchases for today, valued on the projected product price; capped by
        the cash on hand now. Re-run during the day when cash has come in."""
        day = v.day
        fc = plan.get("fc") or self._forecast(v)
        herd = _wb_herd(v.farm)
        n_animals = sum(herd.values())
        reserve = 150 + 45 * (n_animals + 2)
        place_day = day if v.hour < 16 else day + 1
        cash = v.money - reserve
        empty_struct = {"COOP": 0, "PASTURE": 0}
        for (_x, _y, k) in v.structs:
            empty_struct[k] += 1
        in_shed = {a: v.shed.get(a, 0) + v.carried(a) for a in _WB_ANIMALS}
        extra = {}
        buy = {}
        budget_n = 6 if day >= 10 else 3
        bought = 0
        # mirror floor: match the opponent's head count per species where a shop wants the
        # product (eggs always: the log curve cannot crash), before its purchase cutoff
        opp_herd = _wb_herd(v.opp)
        mirror = {}
        shop_prods = set()
        for s in v.shops:
            shop_prods.update(_WB_SHOP_TABLE.get(s, ()))
        for a in ("SHEEP", "COW", "GOOSE"):
            prod = _WB_ANIMALS[a]["prod"]
            if day > WB_HERD_CUTOFF[a] or not (prod == "EGG" or prod in shop_prods):
                continue
            target = opp_herd[a] + (WB_GOOSE_EXTRA if a == "GOOSE" else 0)
            short = target - herd[a] - in_shed.get(a, 0)
            cost = _WB_ANIMALS[a]["cost"]
            while short > 0 and bought < budget_n and cost <= cash:
                mirror[a] = mirror.get(a, 0) + 1
                cash -= cost
                bought += 1
                short -= 1
                extra.setdefault(prod, []).append((day + 5.0, 4))
        while bought < budget_n:
            best = None
            for animal in _WB_ANIMALS:
                cost = _WB_ANIMALS[animal]["cost"]
                if cost > cash:
                    continue
                val, evs = self._animal_eval(animal, v, fc, extra, place_day)
                if val > 0.35 * cost and (best is None or val / cost > best[0]):
                    best = (val / cost, animal, evs)
            if best is None:
                break
            animal = best[1]
            buy[animal] = buy.get(animal, 0) + 1
            cash -= _WB_ANIMALS[animal]["cost"]
            extra.setdefault(_WB_ANIMALS[animal]["prod"], []).extend(best[2])
            bought += 1
        for a in list(buy):
            buy[a] = max(0, buy[a] - in_shed.get(a, 0))
        for a, n in mirror.items():
            buy[a] = buy.get(a, 0) + n
        plan["buy"] = buy
        # structures: reuse empty ones first, then build on empty tiles nearest the shed
        need = {"COOP": 0, "PASTURE": 0}
        for a, n in buy.items():
            need[_WB_ANIMALS[a]["st"]] += n
        for a, n in in_shed.items():
            need[_WB_ANIMALS[a]["st"]] += n
        build = []
        cand = list(v.empty) + list(v.weeds)
        for (x, y, t) in v.plants:
            c = _WB_CROPS[t["crop"]]
            if not c["on"] and day - int(t["planted_day"]) >= (10 if t["crop"] == "MELON" else c["my"]):
                cand.append((x, y))
        sites = sorted(cand, key=lambda p: (_wb_dist(p, _wb_near_shed(p)), p[1], p[0]))
        for kind in ("PASTURE", "COOP"):
            short = need[kind] - empty_struct[kind]
            while short > 0 and sites:
                x, y = sites.pop(0)
                build.append((x, y, kind))
                short -= 1
        plan["build"] = build
        plan["need_struct"] = need
        # empty structures nobody will fill get dug for crops once purchases have ended
        plan["dig_structs"] = {k: (need[k] < empty_struct[k] and day >= 13) for k in need}
        plan["herd_hour"] = v.hour

    # ------------------------------------------------------------------ executor
    def _tasks(self, v):
        """Shared tile tasks: (key, kind, x, y, weight, arg)."""
        P = self.plan
        day, hour = v.day, v.hour
        final_day = day >= 29
        late = max(0, hour - 13) * 12.0          # midnight-deadline escalation
        T = []
        build_sites = {(x, y): k for (x, y, k) in P.get("build", [])}
        opp_ripe = self._opp_ripe_premium(v)
        # animals
        for (x, y, t) in v.animals:
            a = _WB_ANIMALS[t["animal"]]
            tonight = day <= _WB_LAST_PROD_DAY and _wb_animal_prod_tonight(t, day)
            feed_useful = day <= _WB_LAST_PROD_DAY - 1 or (day == _WB_LAST_PROD_DAY and (
                tonight or int(t.get("consecutive_unfed", 0)) >= 1))
            # Feeding buys two things: tonight's care-bank payout (production day) and a
            # banked unit from today's CARE. Below a wheat's worth of product, feed only to
            # stop an escape (a second unfed day), and skip CARE (it banks only when fed).
            pp = v.price(a["prod"])
            escape = int(t.get("consecutive_unfed", 0)) >= 1
            care_ok = not t.get("cared_today") and _wb_next_prod_after(t, day) <= _WB_LAST_PROD_DAY
            gain = (int(t.get("pending_care_bonus", 0)) * pp if tonight else 0.0) + (pp if care_ok else 0.0)
            worth = escape or gain >= WB_FEED_MARGIN * v.price("WHEAT")
            if not t.get("fed_today") and feed_useful and worth:
                w = WB_W_FEED + late
                if escape:
                    w += 20.0 + 2 * late
                T.append((("FEED", x, y), "FEED", x, y, w, None))
            if care_ok and feed_useful and (t.get("fed_today") or worth):
                T.append((("CARE", x, y), "CARE", x, y, WB_W_CARE + late * 0.5, None))
            if t.get("fertilizer_available"):
                fp = v.price("FERTILIZER")
                if fp >= 3:
                    w = WB_W_COLLECT if fp >= 30 else WB_W_COLLECT_CHEAP
                    T.append((("COLLECT", x, y), "COLLECT", x, y, w, None))
            yu = int(t.get("yield_units", 0))
            if yu > 0:
                gain = (1 + int(t.get("pending_care_bonus", 0))) if tonight else 0
                if final_day or yu + gain > a["mx"]:
                    w = WB_W_HARVEST_DUE + late * 0.5
                elif yu >= 2:
                    w = WB_W_HARVEST_OPT * 1.5
                else:
                    w = WB_W_HARVEST_OPT
                T.append((("HARVEST", x, y), "HARVEST", x, y, w, None))
        # plants
        fert_use = P.get("fert_use") or {}
        race = self._race_crops(v)
        for (x, y, t) in v.plants:
            crop = t["crop"]
            c = _WB_CROPS[crop]
            age = day - int(t["planted_day"])
            yu = int(t.get("yield_units", 0))
            fert_active = int(t.get("fertilized_until_day", -1)) >= day
            window_open = _wb_in_window(crop, age) and yu < c["mx"]
            racing = crop in race and age >= c["fy"]
            if fert_use.get(crop) and not fert_active and day <= _WB_LAST_PROD_DAY:
                if self._fert_gain(t, crop, c, age, yu, day) > 0:
                    T.append((("FERT", x, y), "FERT", x, y, WB_W_FERT, None))
            if not t.get("watered_today"):
                w = 0.0
                if int(t.get("consecutive_unwatered", 0)) >= 1 and day <= _WB_LAST_PROD_DAY:
                    w = WB_W_WATER_URGENT + late
                if window_open and not (racing and yu >= c["mx"] - 1):
                    w = max(w, WB_W_HARVEST_RACE if racing else WB_W_WATER_WINDOW)
                elif c["on"] and fert_active and day <= _WB_LAST_PROD_DAY and _wb_crop_prod_tonight(t, day):
                    w = max(w, WB_W_WATER_FERT)
                if w == 0 and day <= _WB_LAST_PROD_DAY:
                    w = WB_W_WATER_MAINT
                if w > 0:
                    T.append((("WATER", x, y), "WATER", x, y, w, None))
            if yu > 0 and age >= c["fy"]:
                w = 0.0
                if not c["on"]:
                    done = yu >= c["mx"] or age > c["my"] or (age == c["my"] and (t.get("watered_today") or hour >= 21))
                    if final_day:
                        done = not (window_open and not t.get("watered_today")) or hour >= 20
                    if racing and (t.get("watered_today") or not window_open or yu >= c["mx"] - 1):
                        done = True
                    if done:
                        w = WB_W_HARVEST_RACE if racing else WB_W_HARVEST_DUE
                        if age > c["my"]:
                            w += 30.0
                else:
                    tonight = _wb_crop_prod_tonight(t, day)
                    gain = (2 if (fert_active and t.get("watered_today")) else 1) if tonight else 0
                    decaying = int(t.get("max_lifespan_step", -1)) >= 0
                    if final_day or decaying or yu + gain > c["mx"]:
                        w = WB_W_HARVEST_DUE + late * 0.5
                    elif yu >= 2:
                        w = WB_W_HARVEST_ONGOING
                    else:
                        w = WB_W_HARVEST_OPT
                if w > 0:
                    T.append((("HARVEST", x, y), "HARVEST", x, y, w, None))
            elif c["on"] and yu <= 0 and int(t.get("max_lifespan_step", -1)) >= 0 and day <= 27:
                T.append((("DIG", x, y), "DIG", x, y, WB_W_DIG, None))
        # weeds and unwanted structures
        if day <= 27:
            for (x, y) in v.weeds:
                T.append((("DIG", x, y), "DIG", x, y, WB_W_DIG, None))
            dig_structs = P.get("dig_structs") or {}
            for (x, y, k) in v.structs:
                if dig_structs.get(k):
                    T.append((("DIG", x, y), "DIG", x, y, WB_W_DIG * 0.7, None))
        # empty tiles: build or plant
        can_plant = hour <= 21 and day <= P.get("last_plant_day", 27)
        for (x, y) in v.empty:
            k = build_sites.get((x, y))
            if k is not None:
                T.append((("BUILD", x, y), "BUILD_" + k, x, y, WB_W_BUILD, k))
            elif can_plant:
                T.append((("PLANT", x, y), "PLANT", x, y, WB_W_PLANT, None))
        return T

    def _opp_ripe_premium(self, v):
        """Premium one-shot crops the opponent can harvest today: selling ours first wins
        the top of the curve (MELON is the case that matters: T=300, sq above I0)."""
        out = set()
        if not v.opp:
            return out
        for row in v.opp["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT" and t["crop"] == "MELON":
                    if v.day - int(t["planted_day"]) >= 9:
                        out.add("MELON")
                        return out
        return out

    def _race_crops(self, v):
        """Crops to harvest and ship ahead of the opponent today: MELON while its price is
        still high and the opponent's melons are ripe (the day-10 dump of the opening)."""
        if v.price("MELON") >= 120 and "MELON" in self._opp_ripe_premium(v):
            return ("MELON",)
        return ()

    @staticmethod
    def _fert_gain(t, crop, c, age, yu, day):
        """Extra units one FERTILIZE on this plant today adds (0 when it adds nothing)."""
        if not c["on"]:
            if crop == "MELON" or yu >= c["mx"] or age < 1:
                return 0
            ws = (c["my"] + 1) // 2
            start = age + 1 if t.get("watered_today") else age
            remaining = [a for a in range(max(start, ws), c["my"] + 1) if day + (a - age) <= 29]
            base_final = min(c["mx"], yu + len(remaining))
            covered = [a for a in remaining if a <= age + 2]
            return min(c["mx"], yu + len(remaining) + len(covered)) - base_final
        n = 0
        pd = int(t["planted_day"])
        for k in range(c["mx"]):
            p = pd + c["fy"] - 1 + k * c["iv"]
            if day <= p <= day + 2 and p <= _WB_LAST_PROD_DAY:
                n += 1
        return n

    def _zones(self, v):
        """Soft work zones for the current crew: a polar sweep around the shed cut into
        one wedge per unit with equal expected work (actions plus one move per tile).
        Every wedge starts next to the shed, where all units spawn, so a unit walks
        outward through its own tiles; it serves everything there, animals included, and
        takes its wedge's feed wheat and fertilizer from the shed on the way out.
        Out-of-zone tasks stay available at WB_ZONE_OUT of their rate."""
        n = len(v.units)
        day = v.day
        items = []
        for (x, y, t) in v.animals:
            items.append(((x, y), 4.5))
        for (x, y, t) in v.plants:
            c = _WB_CROPS[t["crop"]]
            age = day - int(t["planted_day"])
            if c["on"]:
                w = 1.0 + (0.5 if int(t.get("consecutive_unwatered", 0)) >= 1 else 0.0)
            else:
                w = 1.0 + (1.0 if age >= (c["my"] + 1) // 2 - 1 or age == 0 else 0.3)
                if age >= (10 if t["crop"] == "MELON" else c["my"]):
                    w += 3.0
            items.append(((x, y), w))
        for p in v.empty:
            items.append((p, 3.0))
        for p in v.weeds:
            items.append((p, 2.0))
        for (x, y, k) in v.structs:
            items.append(((x, y), 0.5))
        self.unit_zone = {i: set() for i in range(n)}
        self.herd_group = {i: set() for i in range(n)}
        if not items:
            return
        ang = [(_wb_atan2(p[1] - 4.5, p[0] - 4.5), p, w) for (p, w) in items]
        ang.sort()
        # start the sweep after the widest angular gap (the locked quadrant)
        best_gap, start = -1.0, 0
        m = len(ang)
        for k in range(m):
            a0 = ang[k][0]
            a1 = ang[(k + 1) % m][0] + (6.283185307179586 if k == m - 1 else 0.0)
            if a1 - a0 > best_gap:
                best_gap, start = a1 - a0, (k + 1) % m
        ang = ang[start:] + ang[:start]
        total = sum(w for (_a, _p, w) in ang)
        per = total / n
        chunks = [[] for _ in range(n)]
        acc = 0.0
        k = 0
        for (_a, p, w) in ang:
            chunks[k].append(p)
            acc += w
            if acc >= per * (k + 1) - 1e-9 and k < n - 1:
                k += 1
        # match units to wedges: nearest first (hands spawn at the shed, the farmer may not)
        pairs = []
        for i in range(n):
            for j, ch in enumerate(chunks):
                if ch:
                    d = min(_wb_dist(v.units[i], p) for p in ch)
                    pairs.append((d, i, j))
        pairs.sort()
        took_u, took_c = set(), set()
        for d, i, j in pairs:
            if i in took_u or j in took_c:
                continue
            took_u.add(i)
            took_c.add(j)
            self.unit_zone[i] = set(chunks[j])
        animal_tiles = {(x, y) for (x, y, t) in v.animals}
        for i in range(n):
            self.herd_group[i] = self.unit_zone[i] & animal_tiles

    def _execute(self, v):
        P = self.plan
        day, hour = v.day, v.hour
        tasks = self._tasks(v)
        n_units = len(v.units)
        if hour == 23:
            left = {}
            for (key, kind, x, y, w, arg) in tasks:
                if kind in ("FEED", "CARE") or (kind == "WATER" and w >= WB_W_WATER_URGENT) or \
                        (kind == "HARVEST" and w >= WB_W_HARVEST_DUE) or (kind == "WATER" and w >= WB_W_WATER_WINDOW):
                    left[kind] = left.get(kind, 0) + 1
            risk = sum(1 for (x, y, t) in v.animals if not t.get("fed_today") and int(t.get("consecutive_unfed", 0)) >= 1)
            self._note(f"d{day}h23 left={left} escape_risk={risk} units={n_units} shed_wheat={v.shed.get('WHEAT', 0)} "
                       f"carried_wheat={v.carried('WHEAT')}")
        # ---- shared resources for this turn
        seeds_left = {c: v.seeds.get(c, 0) for c in _WB_CROPS}
        crop_order = [c for c in P.get("crop_order", []) if c in _WB_CROPS]
        for c in _WB_CROPS:
            if c not in crop_order and seeds_left.get(c, 0) > 0:
                crop_order.append(c)
        unfed_tiles = {(x, y) for (key, kind, x, y, val, arg) in tasks if kind == "FEED"}
        unfed = len(unfed_tiles)
        carried_wheat = v.carried("WHEAT")
        wheat_uncovered = max(0, unfed - carried_wheat)
        shed_wheat = v.shed.get("WHEAT", 0)
        zkey = (day, n_units, len(v.animals))
        if getattr(self, "zone_key", None) != zkey:
            self._zones(v)
            self.zone_key = zkey
        zone = self.unit_zone
        herd_group = self.herd_group
        fert_tiles = [(x, y) for (key, kind, x, y, val, arg) in tasks if kind == "FERT"]
        shed_fert = v.shed.get("FERTILIZER", 0)
        # empty matching structures for animal placement
        free_struct = {"COOP": [], "PASTURE": []}
        for (x, y, k) in v.structs:
            free_struct[k].append((x, y))
        carried_animals = {a: v.carried(a) for a in _WB_ANIMALS}
        pickup_animals = {}
        for a in _WB_ANIMALS:
            st = _WB_ANIMALS[a]["st"]
            room = len(free_struct[st]) - sum(carried_animals[b] for b in _WB_ANIMALS if _WB_ANIMALS[b]["st"] == st)
            pickup_animals[a] = max(0, min(v.shed.get(a, 0), room))
        race_melon = "MELON" in self._opp_ripe_premium(v) or v.price("MELON") >= 150
        goods_value = {}
        for i in range(n_units):
            gv = 0.0
            for item, n in v.invs[i].items():
                if item in _WB_ANIMALS:
                    continue
                gv += n * v.price(item)
            goods_value[i] = gv
        # ---- candidate pairs
        pairs = []
        for i in range(n_units):
            pos = v.units[i]
            inv = v.invs[i]
            has_wheat = inv.get("WHEAT", 0) > 0
            myzone = zone.get(i, ())
            has_fert = inv.get("FERTILIZER", 0) > 0
            for ti, task in enumerate(tasks):
                key, kind, x, y, val, arg = task
                if kind == "FEED":
                    if not has_wheat:
                        continue
                    val = val * WB_CARRIER_FEED
                elif kind == "FERT" and not has_fert:
                    continue
                d = abs(pos[0] - x) + abs(pos[1] - y)
                if day >= 29 and kind in ("HARVEST", "COLLECT"):
                    s = _wb_near_shed((x, y))
                    if hour + d + 1 + _wb_dist((x, y), s) + 1 > 22:
                        continue
                r = val / (d + 1.0)
                if (x, y) not in myzone and val < WB_W_HARVEST_RACE and kind != "FEED":
                    r *= WB_ZONE_OUT
                if self.prev.get(i) == (x, y):
                    r *= WB_STICKY
                pairs.append((r, i, ti, d))
            # unit-specific: animal placement for carriers
            for a in _WB_ANIMALS:
                if inv.get(a, 0) > 0:
                    for (x, y) in free_struct[_WB_ANIMALS[a]["st"]]:
                        d = abs(pos[0] - x) + abs(pos[1] - y)
                        pairs.append((WB_W_PLACE / (d + 1.0), i, ("PLACE", a, x, y), d))
            s = _wb_near_shed(pos)
            ds = abs(pos[0] - s[0]) + abs(pos[1] - s[1])
            # unit-specific: a herder fetches the wheat its own group still needs
            grp = herd_group.get(i)
            if grp and shed_wheat > 0:
                need_i = sum(1 for p in grp if p in unfed_tiles) - inv.get("WHEAT", 0)
                if need_i > 0:
                    w = WB_W_PICKUP_WHEAT + max(0, hour - 13) * 12.0
                    pairs.append((w / (ds + 1.0), i, ("PICKUP_WHEAT", need_i), ds))
            elif wheat_uncovered > 0 and shed_wheat > 0 and not has_wheat and ds == 0:
                # anyone standing at the shed covers animals no carrier's wheat reaches
                w = WB_W_PICKUP_WHEAT + max(0, hour - 13) * 12.0
                pairs.append((w, i, ("PICKUP_WHEAT", min(WB_PICKUP_CAP, wheat_uncovered)), ds))
            # unit-specific: a crop worker standing at the shed takes fertilizer for the
            # targets in its zone (no dedicated trips: dawn spawn is at the shed)
            if shed_fert > 0 and ds == 0:
                need_f = sum(1 for p in fert_tiles if p in myzone) - inv.get("FERTILIZER", 0)
                if need_f > 0:
                    pairs.append((WB_W_PICKUP_FERT / (ds + 1.0), i, ("PICKUP_FERT", need_f), ds))
            # unit-specific: animal pickup
            if sum(pickup_animals.values()) > 0 and not any(inv.get(a, 0) for a in _WB_ANIMALS):
                pairs.append((WB_W_PICKUP_ANIMAL / (ds + 1.0), i, ("PICKUP_ANIMAL",), ds))
            # unit-specific: drop goods at the shed
            gv = goods_value[i]
            if gv > 0:
                w = 0.0
                if day >= 29:
                    w = WB_W_DROP_FINAL if hour >= 12 else (WB_W_DROP_AT_SHED if ds == 0 else 0.0)
                elif inv.get("MELON", 0) >= 1 and race_melon:
                    w = WB_W_DROP_RACE
                else:
                    # premium goods sell better today than after the midnight auto-drop,
                    # when the opponent has already sold into the same market
                    pv = sum(n * v.price(item) for item, n in inv.items() if item in _WB_DROP_ITEMS)
                    grp_unfed = sum(1 for p in (grp or ()) if p in unfed_tiles)
                    if pv >= WB_DROP_MIN_VALUE and not (has_wheat and grp_unfed > 0):
                        w = min(WB_W_DROP_MAX, WB_DROP_FRAC * pv)
                if w > 0:
                    pairs.append((w / (ds + 1.0), i, ("DROP",), ds))
        pairs.sort(key=lambda p: -p[0])
        # ---- greedy matching with resource accounting
        assign = {}
        used = set()
        tile_owner = {}
        wheat_pool = shed_wheat
        fert_pool = shed_fert
        for r, i, ti, d in pairs:
            if i in assign:
                continue
            if isinstance(ti, tuple):
                kind = ti[0]
                if kind == "PLACE":
                    k2 = ("PLACE", ti[2], ti[3])
                    if k2 in used:
                        continue
                    used.add(k2)
                    assign[i] = (ti, d, None)
                elif kind == "PICKUP_WHEAT":
                    if wheat_pool <= 0:
                        continue
                    q = min(int(ti[1]) + (1 if hour <= 2 else 0), WB_PICKUP_CAP, wheat_pool)
                    wheat_pool -= q
                    assign[i] = (ti, d, q)
                elif kind == "PICKUP_FERT":
                    if fert_pool <= 0:
                        continue
                    q = min(int(ti[1]), fert_pool)
                    fert_pool -= q
                    assign[i] = (ti, d, q)
                elif kind == "PICKUP_ANIMAL":
                    pick = None
                    for a in ("COW", "SHEEP", "GOOSE"):
                        if pickup_animals.get(a, 0) > 0:
                            pick = a
                            break
                    if pick is None:
                        continue
                    pickup_animals[pick] -= 1
                    assign[i] = (ti, d, pick)
                else:
                    assign[i] = (ti, d, None)
                continue
            if ti in used:
                continue
            key, kind, x, y, val, arg = tasks[ti]
            own = tile_owner.get((x, y))
            if own is not None and own != i:
                continue          # one unit works a tile: the others would each walk there
            extra = None
            if kind == "PLANT":
                crop = None
                for c in crop_order:
                    if seeds_left.get(c, 0) > 0:
                        crop = c
                        break
                if crop is None:
                    continue
                seeds_left[crop] -= 1
                extra = crop
            used.add(ti)
            tile_owner[(x, y)] = i
            assign[i] = (ti, d, extra)
        # ---- emit actions
        actions = []
        new_prev = {}
        idle = 0
        dropping = {}
        for i in range(n_units):
            pos = v.units[i]
            if i not in assign:
                actions.append(["PASS"])
                idle += 1
                continue
            ti, d, extra = assign[i]
            if isinstance(ti, tuple):
                kind = ti[0]
                if kind == "PLACE":
                    target = (ti[2], ti[3])
                    if d == 0:
                        actions.append(["PLACE", ti[1]])
                    else:
                        actions.append([self._step_toward(pos, target, v)])
                    new_prev[i] = (ti[2], ti[3])
                    continue
                target = _wb_near_shed(pos)
                if d > 0:
                    actions.append([self._step_toward(pos, target, v)])
                    new_prev[i] = (kind,)
                    mk = "move:" + kind
                    self.stats[mk] = self.stats.get(mk, 0) + 1
                    continue
                if kind == "PICKUP_WHEAT":
                    actions.append(["PICKUP", "WHEAT", int(extra)])
                elif kind == "PICKUP_FERT":
                    actions.append(["PICKUP", "FERTILIZER", int(extra)])
                elif kind == "PICKUP_ANIMAL":
                    actions.append(["PICKUP", extra, 1])
                else:
                    actions.append(["DROP"])
                    room = _WB_SHED_CAP - v.shed_total() - sum(dropping.values())
                    for item, n in v.invs[i].items():
                        if item in _WB_PRODUCTS and room > 0:
                            k = min(n, room)
                            dropping[item] = dropping.get(item, 0) + k
                            room -= k
                new_prev[i] = (kind,)
                continue
            key, kind, x, y, val, arg = tasks[ti]
            new_prev[i] = (x, y)
            if d > 0:
                actions.append([self._step_toward(pos, (x, y), v)])
                mk = "move:" + kind + (":h" if i in herd_group else ":c")
                self.stats[mk] = self.stats.get(mk, 0) + 1
                zk = "zone:in" if (x, y) in zone.get(i, ()) else "zone:out"
                self.stats[zk] = self.stats.get(zk, 0) + 1
                continue
            if kind == "PLANT":
                actions.append(["PLANT", extra])
            elif kind == "COLLECT":
                actions.append(["COLLECT_FERTILIZER"])
            elif kind == "FERT":
                actions.append(["FERTILIZE"])
            elif kind in ("BUILD_COOP", "BUILD_PASTURE"):
                actions.append([kind])
            else:
                actions.append([kind])
        self.prev = new_prev
        fert_tomorrow = 0
        fu = P.get("fert_use") or {}
        for (x, y, t) in v.plants:
            if fu.get(t["crop"]) and day - int(t["planted_day"]) == 0:
                fert_tomorrow += 1
        info = {"unfed": unfed, "wheat_uncovered": wheat_uncovered, "idle": idle, "dropping": dropping,
                "pickup_animals": pickup_animals,
                "fert_reserve": max(0, len(fert_tiles) + fert_tomorrow + len(v.empty) // 3 - v.carried("FERTILIZER"))}
        return actions, info

    def _step_toward(self, pos, target, v):
        x, y = pos
        tx, ty = target
        opts = []
        if tx > x:
            opts.append(("EAST", (x + 1, y)))
        elif tx < x:
            opts.append(("WEST", (x - 1, y)))
        if ty > y:
            opts.append(("SOUTH", (x, y + 1)))
        elif ty < y:
            opts.append(("NORTH", (x, y - 1)))
        if not opts:
            return "PASS"
        if len(opts) == 1:
            return opts[0][0]
        # prefer the step onto a tile that has pending work (free pickup of tasks en route)
        best = opts[0][0]
        best_score = -1
        for name, (nx, ny) in opts:
            t = v.tiles[ny][nx]
            score = 0
            if isinstance(t, dict):
                if t.get("kind") == "PLANT" and not t.get("watered_today"):
                    score = 2
                elif "animal" in t and (not t.get("cared_today") or t.get("fertilizer_available")):
                    score = 1
            if score > best_score:
                best, best_score = name, score
        return best

    # ------------------------------------------------------------------ market arbiter
    def _market(self, v, info):
        P = self.plan
        day, hour = v.day, v.hour
        herd = _wb_herd(v.farm)
        n_animals = sum(herd.values())
        cash = v.money
        critical = []
        shed_room = _WB_SHED_CAP - v.shed_total()
        # -- 1. critical buys: feed wheat, then scheduled animals
        unfed = info["unfed"]
        carried_wheat = v.carried("WHEAT")
        shed_wheat = v.shed.get("WHEAT", 0)
        tomorrow = 0
        if day + 1 <= _WB_LAST_PROD_DAY:
            tomorrow = n_animals + sum(P.get("buy", {}).values())
        need_now = max(0, unfed - carried_wheat - shed_wheat)
        need_tomorrow = 0
        if hour >= 18:
            need_tomorrow = max(0, unfed + tomorrow - carried_wheat - shed_wheat)
        need = max(need_now, need_tomorrow)
        if need > 0 and shed_room > 0:
            q = min(need + (2 if hour >= 18 else 0), shed_room)
            cost = self._buy_cost("WHEAT", v, q)
            while q > 0 and cost > cash:
                q -= 1
                cost = self._buy_cost("WHEAT", v, q)
            if q > 0:
                critical.append(["BUY_PRODUCT", "WHEAT", q])
                cash -= cost
                shed_room -= q
        # scheduled animals: buy for empty matching structures, within today's quota
        buy = P.get("buy", {})
        free_struct = {"COOP": 0, "PASTURE": 0}
        for (_x, _y, k) in v.structs:
            free_struct[k] += 1
        waiting = {a: v.shed.get(a, 0) + v.carried(a) for a in _WB_ANIMALS}
        for a in ("GOOSE", "COW", "SHEEP"):
            want = buy.get(a, 0)
            if want <= 0:
                continue
            st = _WB_ANIMALS[a]["st"]
            slots_free = free_struct[st] - sum(waiting[b] for b in _WB_ANIMALS if _WB_ANIMALS[b]["st"] == st)
            n = min(want, slots_free)
            cost = _WB_ANIMALS[a]["cost"]
            reserve = 40 * n_animals
            while n > 0 and (n * cost > cash - reserve or shed_room < n):
                n -= 1
            if n > 0 and hour <= 20:
                critical.append(["BUY_ANIMAL", a, n])
                cash -= n * cost
                shed_room -= n
                buy[a] = want - n
                waiting[a] += n
        # -- 2. sells from the sell engine
        slots = _WB_MAX_ORDERS - len(critical)
        sells = []
        if slots > 0 and self.se is not None:
            sellable = self._sellable(v, info, n_animals)
            try:
                sells = self.se.orders(v.obs, sellable, slots) or []
            except Exception:
                self.stats["sell_err"] += 1
                self.last_error = _wb_traceback.format_exc()[-600:]
                sells = []
            sells = [o for o in sells if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL"][:slots]
        sell_cash = 0.0
        for o in sells:
            try:
                sell_cash += 0.85 * float(self.pm.sell_revenue(o[1], v.minv.get(o[1], 10000.0), int(o[2])))
            except Exception:
                pass
        cash_after_sells = cash + sell_cash
        rest = []
        room = _WB_MAX_ORDERS - len(critical) - len(sells)
        # -- 3. hires in the morning
        want_hands = int(P.get("hands", 0))
        have = len(v.units) - 1
        if hour <= 3 and day <= 29:
            k = v.hires_today
            n_hire = max(0, want_hands - have)
            while n_hire > 0 and room > 0:
                c = _wb_fib(k)
                if c > cash_after_sells - 30:
                    break
                rest.append(["HIRE"])
                cash_after_sells -= c
                k += 1
                n_hire -= 1
                room -= 1
        # -- 4. seeds for today's plantings
        if room > 0 and day <= P.get("last_plant_day", 27) and hour <= 20:
            quota = P.get("quota", {})
            empty_n = len(v.empty) - len(P.get("build", []))
            for c in P.get("crop_order", []):
                if room <= 0:
                    break
                q = quota.get(c, 0)
                have_s = v.seeds.get(c, 0)
                want_s = min(q, max(0, empty_n + 6)) - have_s
                if hour > 0:
                    want_s = min(want_s, max(0, empty_n - sum(v.seeds.values())))
                if want_s <= 0:
                    continue
                price = _WB_CROPS[c]["seed"]
                n = min(want_s, int(max(0.0, cash_after_sells - 60) // price))
                if n > 0:
                    rest.append(["BUY_SEED", c, n])
                    cash_after_sells -= n * price
                    room -= 1
        # -- 5. land
        if room > 0 and P.get("land"):
            cost = P.get("land_cost", 99999)
            if cash_after_sells >= cost + 150 + 40 * n_animals:
                rest.append(["BUY_LAND"])
                P["land"] = False
                room -= 1
        return sells + critical + rest

    def _buy_cost(self, item, v, q):
        if q <= 0:
            return 0.0
        try:
            return float(self.pm.buy_cost(item, v.minv.get(item, 10000.0), q))
        except Exception:
            return 60.0 * q

    def _sellable(self, v, info, n_animals):
        day, hour = v.day, v.hour
        out = {}
        dropping = info.get("dropping") or {}
        for item in _WB_PRODUCTS:
            # units DROPping this turn resolve before the market, so their goods sell now
            n = v.shed.get(item, 0) + dropping.get(item, 0)
            if n <= 0:
                continue
            if item == "WHEAT" and day < 29:
                tomorrow = n_animals if day + 1 <= _WB_LAST_PROD_DAY else 0
                reserve = max(0, info["unfed"] - v.carried("WHEAT")) + tomorrow + 2
                n = max(0, n - reserve)
            elif item == "FERTILIZER" and day < 28:
                n = max(0, n - info.get("fert_reserve", 0))
            if n > 0:
                out[item] = n
        return out


_WB_BASE_FALLBACK = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
                     "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100}
