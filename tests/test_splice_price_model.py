"""WB_PriceModel (experiments/splice/price_model.py) against the installed engine.

The model's whole job is to equal the engine, so every check here compares with the
engine's own code: market_price for quotes, _process_market for multi-unit orders
(which exercises _commit_unit's "$1 sales add no inventory" rule), and _town_consume
for demand drain.

Run with:
    .venv/Scripts/python.exe -m unittest tests.test_splice_price_model -v
"""
import os
import random
import sys
import unittest
from types import SimpleNamespace as NS

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments", "splice"))

import price_model as pmod  # noqa: E402
from price_model import WB_PriceModel  # noqa: E402

try:
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
except ImportError:  # pragma: no cover
    K = None

I0 = 10000


def _engine_market(orders0, inventory, shed0, money=1e12, orders1=None):
    """Run the engine's _process_market on a minimal two-seat state; return seat 0's
    money delta and the final market inventory."""
    market = {"inventory": dict(inventory), "prices": {p: 0 for p in K.PRODUCTS}}
    farms = [{"money": float(money)}, {"money": float(money)}]
    privates = [{"shed": dict(shed0), "seeds": {}},
                {"shed": {p: 10 ** 6 for p in K.PRODUCTS}, "seeds": {}}]
    state = [NS(observation=NS(market=market, farms=farms, private=privates[0]), action={"market": orders0}),
             NS(observation=NS(market=market, farms=farms, private=privates[1]), action={"market": orders1 or []})]
    K._process_market(state, NS(configuration={}))
    return farms[0]["money"] - float(money), market["inventory"]


def _engine_consume(shops, step, inventory):
    market = {"inventory": dict(inventory), "prices": {p: 0 for p in K.PRODUCTS}}
    state = [NS(observation=NS(market=market, town={"unlocked_shops": list(shops)}))]
    K._town_consume(NS(configuration={}), state, step)
    return market["inventory"]


@unittest.skipIf(K is None, "kaggle_environments not installed")
class TestTablesMatchEngine(unittest.TestCase):
    def test_tables(self):
        self.assertEqual(pmod.WB_MARKET_PARAMS, K.MARKET_PARAMS)
        self.assertEqual(pmod.WB_SHOPS, K.SHOPS)
        self.assertEqual(pmod.WB_PRODUCTS, K.PRODUCTS)
        self.assertEqual(pmod.WB_TOWN_CENTER_PRODUCTS, K.TOWN_CENTER_PRODUCTS)
        self.assertEqual((pmod.WB_MARKET_I0, pmod.WB_PRICE_FLOOR, pmod.WB_HINGE_GAIN),
                         (K.MARKET_I0, K.PRICE_FLOOR, K.HINGE_GAIN))

    def test_top_level_names_are_prefixed(self):
        for name in vars(pmod):
            if name.startswith("__"):
                continue
            self.assertTrue(name.startswith(("WB_", "_wb_")), name)


@unittest.skipIf(K is None, "kaggle_environments not installed")
class TestQuoteExact(unittest.TestCase):
    def setUp(self):
        self.pm = WB_PriceModel()

    def test_every_integer_inventory_near_i0(self):
        for item in K.PRODUCTS:
            for inv in range(I0 - 3000, I0 + 3001):
                self.assertEqual(self.pm.quote(item, inv), K.market_price(item, inv), (item, inv))

    def test_randomized_well_below_to_far_above(self):
        rng = random.Random(20260925)
        for _ in range(60000):
            item = rng.choice(K.PRODUCTS)
            if rng.random() < 0.5:
                inv = rng.randint(-40000, 60000)
            else:
                inv = rng.uniform(-40000, 60000)
            self.assertEqual(self.pm.quote(item, inv), K.market_price(item, inv), (item, inv))

    def test_floor(self):
        far = I0 + 10 ** 7
        for item in K.PRODUCTS:
            self.assertEqual(self.pm.quote(item, far), K.market_price(item, far))
            if K.MARKET_PARAMS[item]["above_func"] != "log":   # log gluts never reach $1
                self.assertEqual(self.pm.quote(item, far), 1, item)
        # First floored unit for the steep premium curves, straight from the engine.
        for item, first_floor in (("WOOL", I0 + 59), ("STRAWBERRY", I0 + 62), ("MILK", I0 + 76)):
            self.assertEqual(self.pm.quote(item, first_floor), 1)
            self.assertGreater(self.pm.quote(item, first_floor - 1), 1)
            self.assertEqual(K.market_price(item, first_floor), 1)

    def test_at_i0_is_base(self):
        for item in K.PRODUCTS:
            self.assertEqual(self.pm.quote(item, I0), K.MARKET_PARAMS[item]["base"])


@unittest.skipIf(K is None, "kaggle_environments not installed")
class TestOrdersWalkTheCurveLikeTheEngine(unittest.TestCase):
    def setUp(self):
        self.pm = WB_PriceModel()
        self.rng = random.Random(7)

    def test_sell_revenue_and_inventory(self):
        for _ in range(400):
            item = self.rng.choice(K.PRODUCTS)
            inv = I0 + self.rng.randint(-500, 400)
            qty = self.rng.randint(1, 150)
            rev, inv_after = _engine_market([["SELL", item, qty]], {p: I0 for p in K.PRODUCTS} | {item: inv},
                                            {item: qty})
            self.assertEqual(self.pm.sell_revenue(item, inv, qty), rev, (item, inv, qty))
            self.assertEqual(sum(self.pm.sell_path(item, inv, qty)), rev)
            self.assertEqual(self.pm.inventory_after_sells(item, inv, qty), inv_after[item], (item, inv, qty))

    def test_floor_sales_add_no_inventory(self):
        # WOOL floors 59 units above I0; 40 more units past that must leave inventory still.
        item, inv = "WOOL", I0 + 55
        rev, inv_after = _engine_market([["SELL", item, 40]], {p: I0 for p in K.PRODUCTS} | {item: inv}, {item: 40})
        self.assertEqual(self.pm.sell_revenue(item, inv, 40), rev)
        self.assertEqual(self.pm.inventory_after_sells(item, inv, 40), inv_after[item])
        self.assertLess(inv_after[item], inv + 40)

    def test_buy_cost(self):
        for _ in range(300):
            item = self.rng.choice(pmod.WB_BUYABLE)
            inv = I0 + self.rng.randint(-600, 600)
            qty = self.rng.randint(1, 60)
            spent, inv_after = _engine_market([["BUY_PRODUCT", item, qty]], {p: I0 for p in K.PRODUCTS} | {item: inv}, {})
            self.assertEqual(self.pm.buy_cost(item, inv, qty), -spent, (item, inv, qty))
            self.assertEqual(inv_after[item], inv - qty)

    def test_units_at_or_above(self):
        for _ in range(300):
            item = self.rng.choice(K.PRODUCTS)
            inv = I0 + self.rng.randint(-300, 200)
            base = K.MARKET_PARAMS[item]["base"]
            min_price = base * self.rng.uniform(0.0, 1.8)
            cap = self.rng.randint(0, 120)
            n = self.pm.units_at_or_above(item, inv, min_price, cap)
            path = self.pm.sell_path(item, inv, cap)
            expect = next((i for i, p in enumerate(path) if p < min_price), cap)
            self.assertEqual(n, expect, (item, inv, min_price, cap))


@unittest.skipIf(K is None, "kaggle_environments not installed")
class TestDrainMatchesTownConsume(unittest.TestCase):
    def setUp(self):
        self.pm = WB_PriceModel()
        self.rng = random.Random(11)

    def _shops(self):
        # Drawn with replacement, up to 8 instances, exactly like _end_of_day.
        return [self.rng.choice(sorted(K.SHOPS)) for _ in range(self.rng.randint(0, 8))]

    def test_drain_per_step(self):
        for _ in range(3000):
            shops = self._shops()
            step = self.rng.randint(0, 719)
            before = {p: I0 for p in K.PRODUCTS}
            after = _engine_consume(shops, step, before)
            for item in K.PRODUCTS:
                self.assertEqual(self.pm.drain_per_step(item, shops, step), before[item] - after[item],
                                 (item, shops, step))

    def test_duplicate_and_single_product_shops(self):
        shops = ["YARN_STORE", "YARN_STORE", "PET_CAFE", "BAKERY"]
        self.assertEqual(self.pm.drain_per_step("WOOL", shops, 4), 4)
        self.assertEqual(self.pm.drain_per_step("WOOL", shops, 24), 5)     # + town centre
        self.assertEqual(self.pm.drain_per_step("WOOL", shops, 5), 0)
        self.assertEqual(self.pm.drain_per_step("CARROT", shops, 8), 2)
        self.assertEqual(self.pm.drain_per_step("FERTILIZER", shops, 0), 0)
        self.assertEqual(self.pm.drain_per_day("WOOL", shops), 4 * 6 + 1)

    def test_project(self):
        for _ in range(200):
            shops = self._shops()
            step = self.rng.randint(0, 700)
            horizon = self.rng.randint(1, 30)
            inv = {p: I0 + self.rng.randint(-200, 200) for p in K.PRODUCTS}
            expect = {p: [] for p in K.PRODUCTS}
            cur = dict(inv)
            for k in range(horizon):
                cur = _engine_consume(shops, step + k, cur)
                for p in K.PRODUCTS:
                    expect[p].append(cur[p])
            for p in K.PRODUCTS:
                self.assertEqual(self.pm.project(p, inv[p], shops, step, horizon), expect[p])

    def test_tick_drain_is_last_tick_before_the_call(self):
        shops = ["YARN_STORE"]
        self.assertEqual(self.pm.tick_drain("WOOL", shops, 5), 2)     # tick at 4: shop only
        self.assertEqual(self.pm.tick_drain("WOOL", shops, 8), 2)     # tick at 4 is still the latest
        self.assertEqual(self.pm.tick_drain("WOOL", shops, 25), 3)    # tick at 24: shop + town centre
        self.assertEqual(self.pm.tick_drain("WOOL", shops, 1), 3)     # tick at 0: shop + town centre
        self.assertEqual(self.pm.tick_drain("WOOL", shops, 4), 3)     # tick at 0 is still the latest
        self.assertEqual(self.pm.tick_drain("WOOL", shops, 0), 0)     # nothing before the first call


if __name__ == "__main__":
    unittest.main()
