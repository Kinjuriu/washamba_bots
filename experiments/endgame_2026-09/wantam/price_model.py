"""WB_PriceModel: an exact, in-agent port of the Kaggriculture market (engine 1.32.7).

Owner: Builder A (splice build, docs/ENDGAME/splice_build.md). Pure functions of public
observation data: prices from shared market inventory, demand drain from
`obs["town"]["unlocked_shops"]`. No engine import, because the submission cannot rely on
one. tests/test_splice_price_model.py checks every table and formula here against the
installed engine.

Build notes: experiments/splice/build.py concatenates this file after a ~1 MB base agent,
so every top-level name carries the WB_ / _wb_ prefix and the only import is stdlib.

Step convention (verified in experiments/splice/_probe_cadence.py): when an agent decides
on an observation with `obs["step"] == s`, the engine processes that action in the
interpreter call whose step counter is also `s`. Inside that call the unit actions run
first, then the market (`_process_market`), then town consumption (`_town_consume(s)`).
So a SELL chosen at `obs["step"] == s` is quoted on the inventory the agent saw at `s`
(plus any same-turn trades), and the drain for step `s` lands after it.
"""
import math as _wb_math

WB_MARKET_I0 = 10000
WB_PRICE_FLOOR = 1
WB_HINGE_GAIN = 8.0

# Copied verbatim from kaggriculture.py MARKET_PARAMS (engine 1.32.7). A test diffs this
# against the installed engine, so an engine patch fails loudly instead of silently.
WB_MARKET_PARAMS = {
    "WHEAT":      {"base":  25, "I0": WB_MARKET_I0, "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
    "CARROT":     {"base":  35, "I0": WB_MARKET_I0, "T": 450, "below_func": "hinge",  "below_target": 1.00, "above_func": "sqrt",   "above_target": 0.70},
    "TOMATO":     {"base":  60, "I0": WB_MARKET_I0, "T": 200, "below_func": "hinge",  "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": WB_MARKET_I0, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
    "MELON":      {"base": 250, "I0": WB_MARKET_I0, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},
    "EGG":        {"base":  50, "I0": WB_MARKET_I0, "T": 332, "below_func": "hinge",  "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
    "MILK":       {"base": 160, "I0": WB_MARKET_I0, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL":       {"base": 200, "I0": WB_MARKET_I0, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": WB_MARKET_I0, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}

# Copied verbatim from kaggriculture.py SHOPS.
WB_SHOPS = {
    "BAKERY":         ["EGG", "WHEAT"],
    "PIZZA_SHOP":     ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT":    ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE":     ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE":       ["CARROT"],
    "SMOOTHIE_SHOP":  ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}

WB_PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
WB_TOWN_CENTER_PRODUCTS = [p for p in WB_PRODUCTS if p != "FERTILIZER"]
WB_BUYABLE = ("WHEAT", "FERTILIZER")   # the only products BUY_PRODUCT accepts
WB_SHOP_INTERVAL = 4                   # townShopSellInterval default
WB_CENTER_INTERVAL = 24                # townCenterSellInterval default
WB_TURNS_PER_DAY = 24


def _wb_shape(func, x, T=None):
    """Verbatim port of kaggriculture._shape."""
    x = max(0.0, x)
    if func == "linear": return x
    if func == "sq":     return x * x
    if func == "sqrt":   return _wb_math.sqrt(x)
    if func == "log":    return _wb_math.log(1.0 + x)
    if func == "log10":  return _wb_math.log10(1.0 + x)
    if func == "hinge":
        if not T or T <= 0:
            return x
        u = x / T
        return u + WB_HINGE_GAIN * max(0.0, u - 1.0) ** 2
    return x


class WB_PriceModel:
    """Exact market arithmetic. All inventories are the shared market inventory
    (`obs["market"]["inventory"][item]`), not our own stock."""

    def __init__(self, params=None, shops=None,
                 shop_interval=WB_SHOP_INTERVAL, center_interval=WB_CENTER_INTERVAL):
        self.params = params or WB_MARKET_PARAMS
        self.shops = shops or WB_SHOPS
        self.shop_interval = max(1, int(shop_interval))
        self.center_interval = max(1, int(center_interval))
        # amp is computed with the engine's own expression, so the cached float is the
        # same float market_price() computes on every call.
        self._c = {}
        for item, p in self.params.items():
            base, T = p["base"], p["T"]
            bf, af = p["below_func"], p["above_func"]
            bamp = p["below_target"] * base / _wb_shape(bf, T, T)
            aamp = p["above_target"] * base / _wb_shape(af, T, T)
            self._c[item] = (base, p["I0"], T, bf, bamp, af, aamp)

    # ---- prices -------------------------------------------------------------------
    def quote(self, item, inventory):
        """== kaggriculture.market_price(item, inventory), exactly (int, floored at 1)."""
        base, I0, T, bf, bamp, af, aamp = self._c[item]
        if inventory < I0:
            price = base + bamp * _wb_shape(bf, I0 - inventory, T)
        else:
            price = base - aamp * _wb_shape(af, inventory - I0, T)
        return max(WB_PRICE_FLOOR, int(round(price)))

    def base(self, item):
        return self._c[item][0]

    def i0(self, item):
        return self._c[item][1]

    def sell_path(self, item, inventory, qty):
        """Per-unit prices for selling `qty` units alone, as _process_market/_commit_unit
        fill it: each unit is quoted pre-sell, and a unit sold at $1 adds no inventory."""
        out = []
        inv = inventory
        for _ in range(max(0, int(qty))):
            p = self.quote(item, inv)
            out.append(p)
            if p > 1:          # _commit_unit: "Sales at $1 do not increase market supply."
                inv += 1
        return out

    def sell_revenue(self, item, inventory, qty):
        """Revenue of one SELL order of `qty` units with no competing same-slot seller."""
        total = 0
        inv = inventory
        n = max(0, int(qty))
        while n > 0:
            p = self.quote(item, inv)
            if p <= 1:         # at the floor the inventory stops moving: the rest pay $1 each
                return total + n
            total += p
            inv += 1
            n -= 1
        return total

    def inventory_after_sells(self, item, inventory, qty):
        """Market inventory after selling `qty` units alone (floor sales add nothing)."""
        inv = inventory
        for _ in range(max(0, int(qty))):
            if self.quote(item, inv) <= 1:
                break
            inv += 1
        return inv

    def units_at_or_above(self, item, inventory, min_price, max_units):
        """How many of `max_units` can be sold in one order while every unit's pre-sell
        quote is >= min_price. Quotes never rise as we sell, so this is a prefix."""
        n = 0
        inv = inventory
        cap = max(0, int(max_units))
        while n < cap:
            p = self.quote(item, inv)
            if p < min_price:
                break
            if p <= 1:         # floor: every further unit is also $1 and impact-free
                return cap
            inv += 1
            n += 1
        return n

    def buy_cost(self, item, inventory, qty):
        """Cost of one BUY_PRODUCT order of `qty` units: each unit is quoted at the
        post-buy inventory (inventory - 1) and every unit removes one from the market.
        The engine only accepts WHEAT and FERTILIZER (WB_BUYABLE); the curve is computed
        for any item so callers can price hypotheticals."""
        total = 0
        inv = inventory
        for _ in range(max(0, int(qty))):
            total += self.quote(item, inv - 1)
            inv -= 1
        return total

    # ---- demand -------------------------------------------------------------------
    def drain_per_step(self, item, unlocked_shops, step):
        """Units of `item` that _town_consume(step) removes, i.e. the consumption applied
        at the end of the interpreter call that processes actions chosen at
        obs["step"] == step. Every unlocked shop instance counts separately (shops are
        drawn with replacement); a single-product shop consumes 2 per tick; the town
        centre takes 1 of every product except FERTILIZER once a day."""
        n = 0
        if step % self.shop_interval == 0:
            for name in unlocked_shops or ():
                products = self.shops.get(name)
                if products and item in products:
                    n += 2 if len(products) == 1 else 1
        if step % self.center_interval == 0 and item in WB_TOWN_CENTER_PRODUCTS:
            n += 1
        return n

    def drain_per_day(self, item, unlocked_shops):
        """Units a full day (24 steps) of consumption removes with the current shop list."""
        return sum(self.drain_per_step(item, unlocked_shops, s) for s in range(WB_TURNS_PER_DAY))

    def tick_drain(self, item, unlocked_shops, step):
        """Units removed by the most recent shop tick strictly before the call for
        `step` (the drain an order at obs step `step` sees as already applied)."""
        s = step - 1
        s -= s % self.shop_interval
        return self.drain_per_step(item, unlocked_shops, s) if s >= 0 else 0

    def project(self, item, inventory, unlocked_shops, step, horizon):
        """Inventory rolled forward under demand only (no trades), starting from the
        inventory visible at obs step `step`. Element k is the inventory visible at
        obs step `step + k + 1`. Shops that unlock later are not modelled: the shop list
        grows by one instance at the end of every third day (up to 8)."""
        out = []
        inv = inventory
        for k in range(max(0, int(horizon))):
            inv -= self.drain_per_step(item, unlocked_shops, step + k)
            out.append(inv)
        return out
