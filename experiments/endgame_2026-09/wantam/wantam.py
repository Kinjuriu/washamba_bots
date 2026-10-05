"""WANTAM: demand-aware planner (and, later, scheduler) on top of Peter's splice plumbing.

Stage 1 (this file): a new dawn planner. Peter's _market and _execute are reused
unchanged so the day-14 test isolates the planning decisions.

Planner idea: simulate every product's shared market inventory day by day to the end
of the season with the engine's exact price curves. Supply comes from both boards
(visible), demand from the town centre, the unlocked shops and the expected drain of
shops still to unlock. Each free tile goes to the crop with the highest marginal
revenue per tile-day, where marginal revenue is the change in OUR total revenue across
all our units of that product (so our own extra units pushing the price down count).
The same forecast values each animal; an animal whose remaining output is worth less
than its feed and labour is not fed (it escapes after two unfed days).
"""
import math as _wa_math
from controller import (WB_Controller, _WB_View, _WB_CROPS, _WB_ANIMALS, _WB_PRODUCTS,
                        _WB_SHOP_TABLE, _WB_T6, _WB_LAND_PRICES, _wb_herd,
                        _wb_expected_drain_growth, _wb_next_prod_after)
import controller as _wa_ctrl

# Base prices, copied from price_model.py's WB_MARKET_PARAMS (itself copied verbatim from
# the engine). Duplicated as a plain dict rather than imported: this file is concatenated
# into a single self-contained submission by build_wantam.py, and a real `import
# price_model` statement (unlike a name already in scope from concatenation) always tries
# to locate an actual separate module file, which doesn't exist once uploaded.
_WA_BASE_PRICE = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
                  "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100}

WA_LAST_DAY = 29
WA_LAST_PROD_DAY = 28
WA_ACTION_COST = 4.0            # shadow price of one unit action (labour incl. travel)
WA_CROP_ACTIONS = {"WHEAT": 6.0, "CARROT": 5.0, "TOMATO": 9.0, "STRAWBERRY": 13.0, "MELON": 10.0}
WA_ANIMAL_ACTIONS = 3.0         # feed, care, collect, a share of harvest
WA_PLANT_CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
WA_STARVE = True
WA_STARVE_MARGIN = 0.8          # starve only when output is clearly below feed + labour
WA_LAND = False
WA_STARVE_PRICE_MULT = 99.0      # and only while today's output is worth less than its keep
WA_WHEAT_PER_ANIMAL = 0.0       # wheat tiles kept per fed animal (feed self-sufficiency)
WA_RIVAL_ECHO = 0.5             # share of our new scarcity supply a rival answers with
WA_RIVAL_LAG = 3
WA_MIN_RATE = 0.0               # plant only when value per tile-day beats this
WA_HERD_BUY = False
WA_OPP_CARE = 1.0               # share of the opponent's animals assumed cared


def _wa_crop_schedule(crop, day, ignore_after=WA_LAST_DAY):
    """Units a crop planted (and watered daily) at `day` puts on the market, by day,
    and the number of days it occupies the tile."""
    c = _WB_CROPS[crop]
    out = {}
    if not c["on"]:
        ws = (c["my"] + 1) // 2
        h = day + c["my"]
        if crop == "MELON":
            h = day + 10
        if h > ignore_after:
            h = ignore_after
        waters = max(0, min(h, day + c["my"]) - (day + ws) + 1)
        units = min(c["mx"], 1 + waters)
        if h - day >= c["fy"] and units > 0:
            out[h] = units
        return out, max(1, h - day)
    # ongoing: productions credited at end of day day + fy - 1 + k*iv, harvested next day
    last = day
    for k in range(c["mx"]):
        p = day + c["fy"] - 1 + k * c["iv"]
        if p > WA_LAST_PROD_DAY:
            break
        sell = min(ignore_after, p + 1)
        out[sell] = out.get(sell, 0) + 1
        last = sell
    return out, max(1, last - day + 1)


class WantamController(WB_Controller):
    shadow = False

    def __init__(self, price_model=None, sell_engine=None):
        super().__init__(price_model, sell_engine)
        self.starve = set()
        self.fc_cache = None

    # ------------------------------------------------------------------ entry
    def _act(self, obs):
        v = _WB_View(obs)
        if v.day != self.plan_day or self.plan is None:
            self.plan_day = v.day
            self.prev = {}
            try:
                self.plan = self._dawn(v)
            except Exception:
                self.errors += 1
                self.last_error = _wa_ctrl._wb_traceback.format_exc()[-600:]
                self.plan = self._default_plan(v)
        actions, info = self._execute(v)
        try:
            market = self._market(v, info)
        except Exception:
            self.errors += 1
            self.last_error = _wa_ctrl._wb_traceback.format_exc()[-600:]
            market = []
        return {"farmer": actions[0], "hands": actions[1:], "market": market}

    # ------------------------------------------------------------------ supply model
    def _board_supply(self, farm, day, own, skip=()):
        """Units per product per day (dict day -> units) the board will put on the market
        from `day` to the end, maintenance assumed. One-shot tiles are assumed replanted
        with the same crop for the opponent (tapes replant), not for us (the planner
        decides our replants day by day)."""
        sup = {p: {} for p in _WB_PRODUCTS}
        feed = {}
        if not farm:
            return sup, feed

        def add(p, d, n):
            if n > 0 and day <= d <= WA_LAST_DAY:
                sup[p][d] = sup[p].get(d, 0.0) + n

        for y, row in enumerate(farm["tiles"]):
            for x, t in enumerate(row):
                if not isinstance(t, dict):
                    continue
                if t.get("kind") == "PLANT":
                    crop = t["crop"]
                    c = _WB_CROPS[crop]
                    pd = int(t["planted_day"])
                    yu = int(t.get("yield_units", 0))
                    if not c["on"]:
                        h = pd + (10 if crop == "MELON" else c["my"])
                        ws = (c["my"] + 1) // 2
                        h2 = max(day, min(h, WA_LAST_DAY))
                        start = max(day, pd + ws)
                        waters = max(0, min(h2, pd + c["my"]) - start + 1)
                        units = min(c["mx"], yu + waters) if pd + c["fy"] <= h2 else 0
                        add(crop, h2, units)
                        if not own:
                            rate = _wa_ctrl._WB_CROP_RATE.get(crop, 0.0)
                            for d in range(h2 + 1, WA_LAST_DAY + 1):
                                add(crop, d, rate)
                    else:
                        if yu > 0:
                            add(crop, day, yu)
                        for k in range(c["mx"]):
                            p = pd + c["fy"] - 1 + k * c["iv"]
                            if day <= p <= WA_LAST_PROD_DAY:
                                add(crop, min(WA_LAST_DAY, p + 1), 1)
                elif "animal" in t:
                    if own and (x, y) in skip:
                        yu = int(t.get("yield_units", 0))
                        add(_WB_ANIMALS[t["animal"]]["prod"], day, yu)
                        continue
                    a = _WB_ANIMALS[t["animal"]]
                    prod = a["prod"]
                    yu = int(t.get("yield_units", 0))
                    if yu > 0:
                        add(prod, day, yu)
                    care = 1.0 if own else WA_OPP_CARE
                    per = 1 + care * (a["iv"])   # base + care bonus banked over the interval
                    placed = int(t["placed_day"])
                    first = placed + a["fy"] - 1
                    d = first
                    while d <= WA_LAST_PROD_DAY:
                        if d >= day:
                            add(prod, min(WA_LAST_DAY, d + 1), per)
                        d += a["iv"]
                    for d in range(day, WA_LAST_DAY):
                        add("FERTILIZER", d, 1)
                        feed[d] = feed.get(d, 0) + 1
        return sup, feed

    def _demand(self, v, optimistic=False):
        """Units drained per day per product, current shops plus expected future unlocks.
        optimistic: every future unlock is a shop that wants the product (used for the
        irreversible decision to let an animal go)."""
        dem = {p: {} for p in _WB_PRODUCTS}
        n_shops = len(v.shops)
        for p in _WB_PRODUCTS:
            base = self._drain_day(p, v.shops)
            grow = _wb_expected_drain_growth(p, v.day)
            if optimistic:
                grow = max([12.0 if len(pr) == 1 else 6.0 for pr in _WB_SHOP_TABLE.values() if p in pr] or [0.0])
            extra = 0.0
            ns = n_shops
            for d in range(v.day, WA_LAST_DAY + 1):
                if d > v.day and d % 3 == 0 and ns < 8:
                    ns += 1
                    extra += grow
                dem[p][d] = base + extra
        return dem

    def _simulate(self, v, p, ours, opp, dem, want_rival=False):
        """Our revenue from product p given our and the opponent's daily supply.
        Both sell what they produce the day it is available; our wheat net of feed can
        be negative (a purchase). With want_rival, also returns the rival's revenue
        under the same shared price path (their units quoted at the inventory level
        before ours land that day, the mirror of our own half-day offset), so callers
        can score decisions on margin (our revenue delta minus theirs) rather than our
        revenue alone -- our extra supply suppresses the price for both sides."""
        pm = self.pm
        inv = float(v.minv.get(p, 10000.0))
        rev = 0.0
        rev_opp = 0.0
        for d in range(v.day, WA_LAST_DAY + 1):
            o = ours.get(d, 0.0)
            q = opp.get(d, 0.0)
            # half the day's drain happens before a typical sale
            dd = dem[p].get(d, 0.0)
            inv -= 0.5 * dd
            if want_rival and q > 0:
                rev_opp += self._rev_units(p, inv, q)
            if o > 0:
                # price of our units sold after half the opponent's
                start = inv + 0.5 * q
                rev += self._rev_units(p, start, o)
            elif o < 0:
                rev -= self._buy_units(p, inv, -o)
            inv += max(0.0, o) + q
            inv -= 0.5 * dd
            # floor: sales at $1 add no inventory
            inv = min(inv, self._floor_inv(p))
        return (rev, rev_opp) if want_rival else rev

    def _floor_inv(self, p):
        cache = self.__dict__.setdefault("_floor_cache", {})
        if p not in cache:
            lo, hi = 10000.0, 10000.0 + 50000.0
            for _ in range(40):
                mid = (lo + hi) / 2
                if self.pm.quote(p, mid) <= 1:
                    hi = mid
                else:
                    lo = mid
            cache[p] = hi
        return cache[p]

    def _rev_units(self, p, inv, n):
        # continuous approximation of summing quotes for n units starting at inv
        whole = int(n)
        frac = n - whole
        tot = 0.0
        x = inv
        for _ in range(whole):
            tot += self.pm.quote(p, x)
            x += 1
        if frac > 0:
            tot += frac * self.pm.quote(p, x)
        return tot

    def _buy_units(self, p, inv, n):
        whole = int(n)
        frac = n - whole
        tot = 0.0
        x = inv
        for _ in range(whole):
            tot += self.pm.quote(p, x - 1)
            x -= 1
        if frac > 0:
            tot += frac * self.pm.quote(p, x - 1)
        return tot

    # ------------------------------------------------------------------ dawn planner
    def _dawn(self, v):
        day = v.day
        plan = self._default_plan(v)
        plan["buy"] = {}
        plan["build"] = []
        plan["dig_structs"] = {}
        herd = _wb_herd(v.farm)
        n_animals = sum(herd.values())

        dem = self._demand(v)
        dem_opt = self._demand(v, optimistic=True)
        opp_sup, opp_feed = self._board_supply(v.opp, day, own=False)
        # opponent's wheat reaches the market net of its feed
        for d, n in opp_feed.items():
            opp_sup["WHEAT"][d] = opp_sup["WHEAT"].get(d, 0.0) - n
        for d in list(opp_sup["WHEAT"].keys()):
            opp_sup["WHEAT"][d] = max(0.0, opp_sup["WHEAT"][d])

        # ---------------- herd: which animals are worth feeding
        # starving is committed: an animal unfed once is fed again only if it would escape
        # for nothing (never re-fed half way, which wastes the unfed day)
        alive = {(x, y) for (x, y, t) in v.animals}
        self.starve = {p for p in self.starve if p in alive}
        animal_keep = {}   # (x,y) -> KeepValue, for the Step 2 scorer's ValueProtected term
        if WA_STARVE and day >= 1:
            own_sup, own_feed = self._board_supply(v.farm, day, own=True)
            wheat_p = v.price("WHEAT")
            for (x, y, t) in sorted(v.animals, key=lambda a: a[2]["animal"]):
                if (x, y) in self.starve:
                    continue
                a = _WB_ANIMALS[t["animal"]]
                prod = a["prod"]
                base_rev, base_rev_opp = self._simulate(v, prod, own_sup[prod], opp_sup[prod], dem_opt, want_rival=True)
                sup2, _ = self._board_supply(v.farm, day, own=True, skip=self.starve | {(x, y)})
                rev2, rev2_opp = self._simulate(v, prod, sup2[prod], opp_sup[prod], dem_opt, want_rival=True)
                days_left = max(0, WA_LAST_PROD_DAY - day + 1)
                cost = days_left * (wheat_p + WA_ANIMAL_ACTIONS * WA_ACTION_COST)
                # fertilizer: one a day, worth its price (cheap late)
                # margin, not our revenue alone: starving also raises the rival's price on
                # its own remaining/future supply of this product, so keeping the animal fed
                # is worth (our loss if starved) PLUS (the rival's gain if starved).
                gain = (base_rev - rev2) + (base_rev_opp - rev2_opp) + days_left * 0.5 * v.price("FERTILIZER")
                now_p = v.price(prod) * (a["iv"] + 1) / a["iv"]      # product value per animal-day now
                if now_p < WA_STARVE_PRICE_MULT * (wheat_p + WA_ANIMAL_ACTIONS * WA_ACTION_COST) and gain < WA_STARVE_MARGIN * cost:
                    self.starve.add((x, y))
                    own_sup = sup2
                else:
                    animal_keep[(x, y)] = gain - cost   # expected future output minus feed/care/labour
        plan["starve"] = len(self.starve)
        plan["animal_keep"] = animal_keep
        self.__dict__.setdefault("starve_log", {})[day] = set(self.starve)

        # ---------------- crops: greedy marginal value per tile-day
        own_sup, own_feed = self._board_supply(v.farm, day, own=True, skip=self.starve)
        for d, n in own_feed.items():
            own_sup["WHEAT"][d] = own_sup["WHEAT"].get(d, 0.0) - n
        free = len(v.empty) + len(v.weeds)
        for (x, y, t) in v.plants:
            c = _WB_CROPS[t["crop"]]
            age = day - int(t["planted_day"])
            if not c["on"] and age >= (10 if t["crop"] == "MELON" else c["my"]):
                free += 1
        # labour cap: tiles the crew can keep (rough): planner leaves this to the crew size
        echo = {p: {} for p in WA_PLANT_CROPS}
        base_rev = {}
        base_rev_opp = {}
        for p in WA_PLANT_CROPS:
            base_rev[p], base_rev_opp[p] = self._simulate(v, p, own_sup[p], opp_sup[p], dem, want_rival=True)
        planned = {}
        rates = []
        can_plant = day <= 27
        left = free if can_plant else 0
        kept = len(v.animals) - len(self.starve)
        wheat_now = sum(1 for (x, y, t) in v.plants if t["crop"] == "WHEAT"
                        and day - int(t["planted_day"]) < _WB_CROPS["WHEAT"]["my"])
        floor = int(WA_WHEAT_PER_ANIMAL * kept + 0.999) if day <= 25 else 0
        while left > 0 and wheat_now + planned.get("WHEAT", 0) < floor:
            sched, occ = _wa_crop_schedule("WHEAT", day)
            for d, n in sched.items():
                own_sup["WHEAT"][d] = own_sup["WHEAT"].get(d, 0.0) + n
            planned["WHEAT"] = planned.get("WHEAT", 0) + 1
            rates.append(("WHEAT", 999.0))
            left -= 1
        base_rev["WHEAT"], base_rev_opp["WHEAT"] = self._simulate(
            v, "WHEAT", own_sup["WHEAT"], opp_sup["WHEAT"], dem, want_rival=True)
        while left > 0:
            best = None
            for crop in WA_PLANT_CROPS:
                sched, occ = _wa_crop_schedule(crop, day)
                if not sched:
                    continue
                trial = dict(own_sup[crop])
                for d, n in sched.items():
                    trial[d] = trial.get(d, 0.0) + n
                opp_t = opp_sup[crop]
                if WA_RIVAL_ECHO > 0:
                    opp_t = dict(opp_t)
                    for d, n in echo[crop].items():
                        opp_t[d] = opp_t.get(d, 0.0) + n
                    for d, n in sched.items():
                        dd = min(WA_LAST_DAY, d + WA_RIVAL_LAG)
                        opp_t[dd] = opp_t.get(dd, 0.0) + WA_RIVAL_ECHO * n
                r, r_opp = self._simulate(v, crop, trial, opp_t, dem, want_rival=True)
                # margin, not our revenue alone: our extra supply of this crop also
                # suppresses the price the rival gets for its own supply of the same
                # product (through the shared inventory path), so a crop the rival also
                # sells scores higher than the same crop would if the rival grew none of it.
                gain = (r - base_rev[crop]) - (r_opp - base_rev_opp[crop]) \
                    - _WB_CROPS[crop]["seed"] - WA_CROP_ACTIONS[crop] * WA_ACTION_COST
                rate = gain / occ
                if best is None or rate > best[0]:
                    best = (rate, crop, trial, r, r_opp)
            if best is None or best[0] <= WA_MIN_RATE:
                break
            rate, crop, trial, r, r_opp = best
            if WA_RIVAL_ECHO > 0:
                sched, _occ = _wa_crop_schedule(crop, day)
                for d, n in sched.items():
                    dd = min(WA_LAST_DAY, d + WA_RIVAL_LAG)
                    echo[crop][dd] = echo[crop].get(dd, 0.0) + WA_RIVAL_ECHO * n
            own_sup[crop] = trial
            base_rev[crop] = r
            base_rev_opp[crop] = r_opp
            planned[crop] = planned.get(crop, 0) + 1
            rates.append((crop, round(rate, 1)))
            left -= 1
        # Step 2 scorer: last marginal rate (value/tile-day) actually accepted per crop;
        # for crops we stopped planting, the last-tried rate (from `best`, if any this dawn)
        # is still a reasonable marginal-value proxy for "one more unit sold at the plan".
        crop_rate = {c: rt for (c, rt) in rates}
        for crop in WA_PLANT_CROPS:
            crop_rate.setdefault(crop, max(0.0, v.price(crop) - WA_CROP_ACTIONS[crop] * WA_ACTION_COST))
        plan["crop_rate"] = crop_rate
        plan["quota"] = planned
        order = sorted(planned, key=lambda c: -max([rt for (cc, rt) in rates if cc == c] or [0]))
        plan["crop_order"] = order or ["WHEAT"]
        plan["last_plant_day"] = 27
        plan["filler"] = None

        # ---------------- land: next quadrant if its tiles pay for themselves
        extra_q = len(v.quads) - 1
        plan["land"] = False
        if WA_LAND and extra_q < 3 and day <= 22 and rates:
            price = _WB_LAND_PRICES[extra_q]
            # value of 25 more tiles at the marginal rate we just stopped at (conservative)
            marg = max(0.0, min(rt for (_c, rt) in rates[-5:])) if rates else 0.0
            if left <= 0 and marg * 25 * max(0, 27 - day) * 0.5 > price:
                plan["land"] = True
                plan["land_cost"] = price

        # ---------------- fertilizer use: Peter's rule
        fp = self._quote("FERTILIZER", v.minv.get("FERTILIZER", 10000.0))
        fert_use = {}
        for crop in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"):
            g = {"WHEAT": 2.0, "CARROT": 1.0, "TOMATO": 2.0, "STRAWBERRY": 1.5}[crop]
            fert_use[crop] = g * v.price(crop) > 1.6 * fp + 2 * _wa_ctrl.WB_ACTION_COST
        plan["fert_use"] = fert_use

        # ---------------- crew
        load = (n_animals - len(self.starve)) * 3.6
        for (x, y, t) in v.plants:
            load += _wa_ctrl._WB_TILE_LOAD.get(t["crop"], 1.0)
        work = load + sum(planned.values()) * 1.2 + len(v.weeds) + 4
        hands = int(work * _wa_ctrl._WB_TURNS_PER_ACTION / 23.0 + 0.5) - 1
        plan["hands"] = max(_WB_T6["HANDS"][min(29, day)], min(_wa_ctrl.WB_MAX_HANDS, hands))
        self._note(f"d{day} money={v.money:.0f} starve={len(self.starve)} quota={planned} "
                   f"rates={rates[:3]}..{rates[-2:]} hands={plan['hands']} land={plan['land']}")
        return plan

    # ------------------------------------------------------------------ tasks
    def _tasks(self, v):
        T = super()._tasks(v)
        if not self.starve:
            return T
        out = []
        for task in T:
            key, kind, x, y, w, arg = task
            if kind in ("FEED", "CARE") and (x, y) in self.starve:
                continue
            out.append(task)
        return out

    def summary(self):
        return {"log_tail": self.log[-3:]}


def make(pm, se):
    return WantamController(pm, se)


# ====================================================================== executor (layers 2+3)
WX_HORIZON = 9            # turns of work a route is built for before it is extended
WX_ANIMAL_TURNS = 5.0     # unit-turns one animal takes per day incl. travel (herd sizing)
WX_HERDER_TURNS = 21.0    # turns a herder can give its group per day
WX_URGENT_HOUR = 15       # from here a trap-door task preempts the nearest free unit
WX_MIN_DENSITY = 2.0      # visits worth less than this per turn are left for idle time
_WX_MOVES = {(1, 0): "EAST", (-1, 0): "WEST", (0, 1): "SOUTH", (0, -1): "NORTH"}
# action order within one visit: water first (window credit), harvest, replant, water the seedling
_WX_ORDER = {"FEED": 0, "CARE": 1, "COLLECT": 2, "HARVEST": 4, "WATER": 3, "PLANT": 5, "FERT": 6,
             "DIG": 7, "BUILD_COOP": 8, "BUILD_PASTURE": 8}


class WantamExec(WantamController):
    def __init__(self, price_model=None, sell_engine=None):
        super().__init__(price_model, sell_engine)
        self.routes = {}
        self.herd_of = {}
        self.xday = -1
        self.xstats = {"visits": 0, "acts": 0}

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _d(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _step(self, pos, target, v, busy):
        x, y = pos
        tx, ty = target
        opts = []
        if tx != x:
            opts.append((1 if tx > x else -1, 0))
        if ty != y:
            opts.append((0, 1 if ty > y else -1))
        if not opts:
            return "PASS"
        best, bs = opts[0], -1
        for dx, dy in opts:
            nx, ny = x + dx, y + dy
            sc = 1 if (nx, ny) in busy else 0      # prefer passing over tiles with work
            if sc > bs:
                best, bs = (dx, dy), sc
        return _WX_MOVES[best]

    def _dawn_exec(self, v, animal_tiles):
        """Herd groups for today: animals split into angular sectors around the shed,
        one herder per ~WX_HERDER_TURNS/WX_ANIMAL_TURNS animals."""
        self.routes = {}
        self.herd_of = {}
        if not animal_tiles:
            self.herders = []
            return
        per = max(1, int(WX_HERDER_TURNS / WX_ANIMAL_TURNS))
        n = max(1, -(-len(animal_tiles) // per))
        pts = sorted(animal_tiles, key=lambda p: _wa_math.atan2(p[1] - 4.5, p[0] - 4.5))
        # rotate so the widest angular gap is the cut
        if len(pts) > 1:
            ang = [_wa_math.atan2(p[1] - 4.5, p[0] - 4.5) for p in pts]
            gaps = [(ang[(k + 1) % len(ang)] - ang[k]) % (2 * _wa_math.pi) for k in range(len(ang))]
            k = max(range(len(gaps)), key=lambda i: gaps[i])
            pts = pts[k + 1:] + pts[:k + 1]
        self.herd_groups = [pts[i * len(pts) // n:(i + 1) * len(pts) // n] for i in range(n)]
        self.herders = []   # unit indices, filled lazily as units exist

    # ---------------------------------------------------------------- main
    def _execute(self, v):
        P = self.plan
        day, hour = v.day, v.hour
        tasks = self._tasks(v)
        n = len(v.units)
        animal_tiles = [(x, y) for (x, y, t) in v.animals if (x, y) not in self.starve]
        if self.xday != day:
            self.xday = day
            self._dawn_exec(v, animal_tiles)
        # herders: the first units to exist today, one per group
        groups = getattr(self, "herd_groups", [])
        while len(self.herders) < len(groups) and len(self.herders) < n:
            cand = [i for i in range(n) if i not in self.herders]
            self.herders.append(cand[-1] if len(self.herders) else cand[0])
        for gi, u in enumerate(self.herders):
            for p in groups[gi]:
                self.herd_of[p] = u

        # ---- per-tile task lists
        seeds_left = {c: v.seeds.get(c, 0) for c in _WB_CROPS}
        crop_order = [c for c in P.get("crop_order", []) if c in _WB_CROPS]
        for c in _WB_CROPS:
            if c not in crop_order and seeds_left.get(c, 0) > 0:
                crop_order.append(c)
        tile = {}
        for (key, kind, x, y, w, arg) in tasks:
            tile.setdefault((x, y), []).append((kind, w, arg))
        unfed = [(p) for p, L in tile.items() if any(k == "FEED" for k, _w, _a in L)]
        fert_tiles = [p for p, L in tile.items() if any(k == "FERT" for k, _w, _a in L)]

        def doable(i, p, inv, virtual=False):
            """Tasks unit i can do on tile p, with value; FEED needs wheat, FERT fertilizer."""
            out = []
            for kind, w, arg in tile.get(p, ()):
                if kind == "FEED" and inv.get("WHEAT", 0) <= 0 and not virtual:
                    continue
                if kind == "FEED" and virtual and inv.get("WHEAT", 0) <= 0:
                    continue
                if kind == "FERT" and inv.get("FERTILIZER", 0) <= 0:
                    continue
                if kind == "PLANT" and not any(seeds_left.get(c, 0) > 0 for c in crop_order):
                    continue
                out.append((kind, w, arg))
            # a harvest of a one-shot crop frees the tile: replant + water in the same visit
            if any(k == "HARVEST" for k, _w, _a in out):
                t = v.tiles[p[1]][p[0]]
                if isinstance(t, dict) and t.get("kind") == "PLANT" and not _WB_CROPS[t["crop"]]["on"] \
                        and day <= P.get("last_plant_day", 27) and hour <= 21 \
                        and any(seeds_left.get(c, 0) > 0 for c in crop_order):
                    out.append(("PLANT", _wa_ctrl.WB_W_PLANT, None))
                    out.append(("WATER", _wa_ctrl.WB_W_WATER_URGENT, None))
            return out

        def visit_value(i, p, inv):
            L = doable(i, p, inv, virtual=True)
            if not L:
                return 0.0, 0
            return sum(w for _k, w, _a in L), len(L)

        # ---- drop stale routes; claims
        claimed = {}
        for i in range(n):
            r = [p for p in self.routes.get(i, []) if p in tile or (isinstance(p, tuple) and len(p) == 3)]
            self.routes[i] = r
            for p in r:
                if len(p) == 2:
                    claimed[p] = i

        # ---- trap doors late in the day: nearest unit with the means takes it first
        if hour >= WX_URGENT_HOUR:
            urgent = []
            for p, L in tile.items():
                for kind, w, arg in L:
                    if (kind == "FEED" and w >= _wa_ctrl.WB_W_FEED + 20) or \
                            (kind == "WATER" and w >= _wa_ctrl.WB_W_WATER_URGENT):
                        urgent.append((p, kind))
                        break
            for p, kind in urgent:
                owner = claimed.get(p)
                if owner is not None:
                    ahead = self._route_time(v.units[owner], self.routes[owner], p)
                    if hour + ahead < 23:
                        continue
                best = None
                for i in range(n):
                    if kind == "FEED" and v.invs[i].get("WHEAT", 0) <= 0:
                        continue
                    d = self._d(v.units[i], p)
                    if hour + d < 23 and (best is None or d < best[0]):
                        best = (d, i)
                if best:
                    i = best[1]
                    if owner is not None and owner != i and p in self.routes.get(owner, []):
                        self.routes[owner].remove(p)
                    if p in self.routes.get(i, []):
                        self.routes[i].remove(p)
                    self.routes.setdefault(i, []).insert(0, p)
                    claimed[p] = i

        # ---- build routes for units that need one
        wheat_pool = v.shed.get("WHEAT", 0)
        fert_pool = v.shed.get("FERTILIZER", 0)
        actions = [None] * n
        dropping = {}
        pickups = {}
        for i in range(n):
            pos = v.units[i]
            inv = v.invs[i]
            near_shed = pos in _wa_ctrl._WB_SHED
            # dawn logistics at the shed: herders take their group's wheat, crop workers fertilizer
            if near_shed and hour <= 3:
                if i in self.herders:
                    gi = self.herders.index(i)
                    need = sum(1 for p in groups[gi] if p in unfed) - inv.get("WHEAT", 0)
                    if need > 0 and wheat_pool > 0:
                        q = min(need + 1, wheat_pool)
                        wheat_pool -= q
                        actions[i] = ["PICKUP", "WHEAT", int(q)]
                        continue
                elif fert_tiles and fert_pool > 0 and inv.get("FERTILIZER", 0) <= 0:
                    crop_workers = max(1, n - len(self.herders))
                    q = min(fert_pool, -(-len(fert_tiles) // crop_workers))
                    if q > 0:
                        fert_pool -= q
                        actions[i] = ["PICKUP", "FERTILIZER", int(q)]
                        continue
            # final day: bring goods to the shed so the last market turns can sell them
            carried_goods = sum(nn * v.price(it) for it, nn in inv.items() if it in _WB_PRODUCTS and it != "WHEAT")
            if (day >= 29 and hour >= 14 and carried_goods > 0) or (carried_goods >= 600 and self._d(pos, _wa_ctrl._wb_near_shed(pos)) <= 1):
                if near_shed:
                    actions[i] = ["DROP"]
                    room = 100 - v.shed_total() - sum(dropping.values())
                    for it, nn in inv.items():
                        if it in _WB_PRODUCTS and room > 0:
                            k = min(nn, room)
                            dropping[it] = dropping.get(it, 0) + k
                            room -= k
                    continue
                if day >= 29 and hour >= 14:
                    actions[i] = [self._step(pos, _wa_ctrl._wb_near_shed(pos), v, tile)]
                    continue
            # work on the tile we stand on (batching): our route's tile or an unclaimed one
            here = pos if (claimed.get(pos, i) == i) else None
            if here is not None:
                L = doable(i, here, inv)
                if L:
                    L.sort(key=lambda z: (_WX_ORDER.get(z[0], 9), -z[1]))
                    kind, w, arg = L[0]
                    act = self._emit(kind, v, here, seeds_left, crop_order)
                    if act is not None:
                        actions[i] = act
                        claimed[here] = i
                        if here not in self.routes.get(i, []):
                            self.routes.setdefault(i, []).insert(0, here)
                        continue
            # herder out of wheat with unfed animals left in its group: back to the shed
            if i in self.herders and inv.get("WHEAT", 0) <= 0 and wheat_pool > 0:
                gi = self.herders.index(i)
                need = sum(1 for p in groups[gi] if p in unfed)
                if need > 0:
                    if near_shed:
                        q = min(need + 1, wheat_pool)
                        wheat_pool -= q
                        actions[i] = ["PICKUP", "WHEAT", int(q)]
                    else:
                        actions[i] = [self._step(pos, _wa_ctrl._wb_near_shed(pos), v, tile)]
                    continue
            # extend the route if short
            r = [p for p in self.routes.get(i, []) if p != pos and p in tile]
            if self._route_time(pos, r, None) < WX_HORIZON:
                r = self._extend(i, pos, r, tile, claimed, inv, visit_value, v)
            self.routes[i] = r
            for p in r:
                claimed[p] = i
            if r:
                actions[i] = [self._step(pos, r[0], v, tile)]
            else:
                actions[i] = ["PASS"]
        idle = sum(1 for a in actions if a == ["PASS"])
        fert_tomorrow = 0
        fu = P.get("fert_use") or {}
        for (x, y, t) in v.plants:
            if fu.get(t["crop"]) and day - int(t["planted_day"]) == 0:
                fert_tomorrow += 1
        pickup_animals = {a: 0 for a in _WB_ANIMALS}
        info = {"unfed": len(unfed), "wheat_uncovered": max(0, len(unfed) - v.carried("WHEAT")),
                "idle": idle, "dropping": dropping, "pickup_animals": pickup_animals,
                "fert_reserve": max(0, len(fert_tiles) + fert_tomorrow + len(v.empty) // 3 - v.carried("FERTILIZER"))}
        return actions, info

    def _emit(self, kind, v, p, seeds_left, crop_order):
        if kind == "PLANT":
            for c in crop_order:
                if seeds_left.get(c, 0) > 0:
                    seeds_left[c] -= 1
                    return ["PLANT", c]
            return None
        if kind == "COLLECT":
            return ["COLLECT_FERTILIZER"]
        if kind == "FERT":
            return ["FERTILIZE"]
        return [kind]

    def _route_time(self, pos, r, until):
        t, cur = 0, pos
        for p in r:
            t += self._d(cur, p) + 1
            cur = p
            if p == until:
                break
        return t

    def _extend(self, i, pos, r, tile, claimed, inv, visit_value, v):
        cur = r[-1] if r else pos
        t = self._route_time(pos, r, None)
        herd = self.herd_of
        is_herder = i in self.herders
        while t < WX_HORIZON:
            best = None
            for p in tile:
                if claimed.get(p, i) != i or p in r:
                    continue
                owner = herd.get(p)
                val, na = visit_value(i, p, inv)
                if val <= 0:
                    continue
                if owner is not None and owner != i:
                    val *= 0.3              # another herder's animal
                elif owner is None and is_herder and v.hour <= 10:
                    val *= 0.5              # herders do their round first
                d = self._d(cur, p)
                dens = val / (d + na)
                if dens < WX_MIN_DENSITY:
                    continue
                if best is None or dens > best[0]:
                    best = (dens, p, d, na)
            if best is None:
                break
            _dens, p, d, na = best
            r.append(p)
            claimed[p] = i
            t += d + na
            cur = p
        return r


def make_exec(pm, se):
    return WantamExec(pm, se)


# ====================================================================== Step 2: value-aware scoring
# Score_j = (ValueProtected_j + ExpectedMarginalRevenue_j + ScarcityPremium_j)
#           / (Travel_j + Actions_j) * Urgency_j
# The division by (Travel_j + Actions_j) is already done downstream by WantamExec's routing
# (`visit_value`/`_extend`'s `dens = val/(d+na)`, and the immediate-tile case has Travel=0),
# so this class only has to replace the task *weight* -- Peter's fixed WB_W_* constants --
# with the bracketed numerator times Urgency. Task eligibility (which tasks exist at all)
# is left to WB_Controller._tasks; only their value is recomputed here, from the dawn plan's
# own forecasts (plan['crop_rate'], plan['animal_keep']) instead of hand-tuned weights.
WS_URGENT_HOUR = 15          # trap doors escalate from here (mirrors WX_URGENT_HOUR)
WS_URGENT_MULT = 6.0         # multiplier once a task is a true trap door (escape/weed tonight)


class WantamScoreExec(WantamExec):
    def _scarcity(self, p):
        """Extra value from the market sitting below its I0 hinge: current quote above base."""
        base = _WA_BASE_PRICE.get(p, 0.0)
        return max(0.0, self._last_price.get(p, base) - base)

    def _tasks(self, v):
        T = super()._tasks(v)
        self._last_price = {p: v.price(p) for p in _WB_PRODUCTS}
        P = self.plan
        day, hour = v.day, v.hour
        crop_rate = P.get("crop_rate") or {}
        animal_keep = P.get("animal_keep") or {}
        urgent_hour = hour >= WS_URGENT_HOUR
        out = []
        for (key, kind, x, y, w, arg) in T:
            tile = v.tiles[y][x]
            vp = emr = sp = 0.0
            urgency = 1.0
            trap_door = False
            if kind == "FEED":
                escape = isinstance(tile, dict) and int(tile.get("consecutive_unfed", 0)) >= 1
                prod = _WB_ANIMALS[tile["animal"]]["prod"] if isinstance(tile, dict) and "animal" in tile else None
                if escape:
                    trap_door = True
                    vp = max(0.0, animal_keep.get((x, y), 0.0))
                    if urgent_hour:
                        urgency = WS_URGENT_MULT
                if prod:
                    tonight = isinstance(tile, dict) and int(tile.get("pending_care_bonus", 0)) > 0
                    emr = v.price(prod) * (1 + int(tile.get("pending_care_bonus", 0))) if tonight else v.price(prod) * 0.3
                    sp = self._scarcity(prod)
            elif kind == "CARE":
                prod = _WB_ANIMALS[tile["animal"]]["prod"] if isinstance(tile, dict) and "animal" in tile else None
                if prod:
                    emr = v.price(prod) * 0.5   # banked unit, realised later
                    sp = self._scarcity(prod) * 0.5
            elif kind == "COLLECT":
                emr = v.price("FERTILIZER")
            elif kind == "HARVEST":
                if isinstance(tile, dict):
                    yu = int(tile.get("yield_units", 0))
                    prod = (tile.get("crop") if tile.get("kind") == "PLANT"
                            else _WB_ANIMALS.get(tile.get("animal"), {}).get("prod"))
                    if prod:
                        emr = yu * v.price(prod)
                        sp = yu * self._scarcity(prod)
                        decaying = int(tile.get("max_lifespan_step", -1)) >= 0
                        if decaying or day >= 29:
                            trap_door = True
                            vp = emr + sp   # missing tonight loses it outright
                            if urgent_hour:
                                urgency = WS_URGENT_MULT
            elif kind == "WATER":
                crop = tile.get("crop") if isinstance(tile, dict) else None
                rate = crop_rate.get(crop, 0.0) if crop else 0.0
                weeds_tonight = isinstance(tile, dict) and int(tile.get("consecutive_unwatered", 0)) >= 1
                if weeds_tonight:
                    trap_door = True
                    c = _WB_CROPS.get(crop, {})
                    remaining_days = max(1, int(c.get("my", 4)) - (day - int(tile.get("planted_day", day))))
                    vp = max(0.0, rate) * remaining_days
                    if urgent_hour:
                        urgency = WS_URGENT_MULT
                else:
                    emr = max(0.0, rate)
                    sp = self._scarcity(crop) if crop else 0.0
            elif kind == "PLANT":
                best_rate = max(crop_rate.values()) if crop_rate else 0.0
                emr = max(0.0, best_rate)
            elif kind == "FERT":
                emr = w   # Peter's _fert_gain-based weight is already a $ estimate; keep it
            else:
                emr = w   # DIG, BUILD_*: structural/enabling actions, out of scope for this pass
            new_w = (vp + emr + sp) * urgency
            if trap_door:
                # WantamExec._execute's late-hour preemption pass (inherited unchanged)
                # compares raw weight against Peter's fixed WB_W_FEED/WB_W_WATER_URGENT
                # constants to decide whether a trap door steals the nearest free unit.
                # Our $-scaled scores don't share that constant's scale, so floor any real
                # trap door above it -- otherwise a cheap-product animal or crop never
                # triggers the preemption and starves/weeds anyway.
                floor = _wa_ctrl.WB_W_FEED + 21 if kind == "FEED" else _wa_ctrl.WB_W_WATER_URGENT + 1
                new_w = max(new_w, floor)
            elif new_w <= 0 and kind not in ("FEED", "CARE"):
                continue   # a task with no forecast value and no trap door isn't worth a visit
            out.append((key, kind, x, y, max(new_w, 0.01) if kind in ("FEED", "CARE") else new_w, arg))
        return out


def make_score(pm, se):
    return WantamScoreExec(pm, se)
