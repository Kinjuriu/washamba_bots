"""
Tests for the pricing.py research module (forward pricing, RESEARCH ONLY).

These check pricing.py's own internal consistency (a sale never raises
price, town demand never raises price, the floor is respected) and, where
the real engine is importable, cross-check pricing.py's numbers against the
engine's own market_price() directly - the whole point of this module is
to match the engine exactly, so a test that doesn't compare against the
engine isn't proving much.

Run with:
    python -m unittest discover -s tests
"""

import unittest

from pricing import (
    MARKET_PARAMS,
    apply_town_demand,
    estimate_future_price,
    market_price,
    price_path_for_sale,
    recommend_sell_quantity,
    simulate_single_product,
)

try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import (
        market_price as engine_market_price,
    )

    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False

PLANTABLE_CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]


class TestMarketPriceMatchesEngine(unittest.TestCase):
    """The whole point of this module: never drift from the engine."""

    @unittest.skipUnless(ENGINE_AVAILABLE, "kaggle_environments not installed")
    def test_matches_engine_across_inventory_range(self):
        for item in PLANTABLE_CROPS:
            for inventory in (0, 1, 5000, 9999, 10000, 10001, 12000, 20000, 50000):
                with self.subTest(item=item, inventory=inventory):
                    self.assertEqual(
                        market_price(item, inventory),
                        engine_market_price(item, inventory),
                    )

    @unittest.skipUnless(ENGINE_AVAILABLE, "kaggle_environments not installed")
    def test_local_reproduction_path_also_matches_engine(self):
        # Passing params explicitly forces pricing.py's own _shape-based
        # reproduction instead of delegating to the imported engine
        # function - this is the path used if the engine's market_price
        # ever stops being importable.
        for item in PLANTABLE_CROPS:
            for inventory in (0, 9999, 10000, 20000, 50000):
                with self.subTest(item=item, inventory=inventory):
                    self.assertEqual(
                        market_price(item, inventory, params=MARKET_PARAMS),
                        engine_market_price(item, inventory),
                    )


class TestMarketPriceBasics(unittest.TestCase):
    def test_price_at_baseline_inventory_is_base_price(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                base = MARKET_PARAMS[item]["base"]
                I0 = MARKET_PARAMS[item]["I0"]
                self.assertEqual(market_price(item, I0), base)

    def test_price_rises_below_baseline_and_falls_above_it(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                I0 = MARKET_PARAMS[item]["I0"]
                below = market_price(item, I0 - 100)
                at = market_price(item, I0)
                above = market_price(item, I0 + 100)
                self.assertGreater(below, at)
                self.assertLess(above, at)

    def test_price_never_drops_below_floor(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                self.assertEqual(market_price(item, I0 := MARKET_PARAMS[item]["I0"]) >= 1, True)
                self.assertGreaterEqual(market_price(item, I0 + 10_000_000), 1)

    def test_extreme_scarcity_does_not_raise_an_error(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                # Inventory can go negative (town demand has no floor in the
                # engine); the formula must still return a sane positive int.
                price = market_price(item, -500)
                self.assertIsInstance(price, int)
                self.assertGreaterEqual(price, 1)


class TestPricePathForSale(unittest.TestCase):
    def test_zero_quantity_is_a_no_op(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                result = price_path_for_sale(item, MARKET_PARAMS[item]["I0"], 0)
                self.assertEqual(result["prices"], [])
                self.assertEqual(result["ending_inventory"], MARKET_PARAMS[item]["I0"])

    def test_price_path_is_non_increasing(self):
        # Each unit either sells at the same price as the last (both at the
        # floor) or strictly less - never more, since supply only grows.
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                result = price_path_for_sale(item, MARKET_PARAMS[item]["I0"], 20)
                prices = result["prices"]
                for earlier, later in zip(prices, prices[1:]):
                    self.assertLessEqual(later, earlier)

    def test_inventory_grows_by_one_per_unit_above_the_floor(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                start = MARKET_PARAMS[item]["I0"]
                result = price_path_for_sale(item, start, 5)
                # None of these five units should hit the $1 floor from a
                # baseline start, so inventory should have grown by exactly 5.
                self.assertEqual(result["ending_inventory"], start + 5)

    def test_selling_past_the_floor_stops_growing_inventory(self):
        # MELON has the steepest above-I0 curve (above_func "sq") of the
        # five plantable crops, so it's the cheapest way to reach the floor
        # and confirm the "$1 sales don't add supply" rule.
        result = price_path_for_sale("MELON", MARKET_PARAMS["MELON"]["I0"], 500)
        self.assertIn(1, result["prices"])
        floor_index = result["prices"].index(1)
        # Every price at or after the floor is hit should also be the floor.
        self.assertTrue(all(p == 1 for p in result["prices"][floor_index:]))


class TestApplyTownDemand(unittest.TestCase):
    def test_no_turns_is_a_no_op(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                inv = MARKET_PARAMS[item]["I0"]
                self.assertEqual(apply_town_demand(inv, item, 0), inv)

    def test_town_center_alone_drains_one_per_day(self):
        # No shops unlocked: only the Town Center consumes, once every
        # center_interval (24) steps - one day at the default turn rate.
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                inv = MARKET_PARAMS[item]["I0"]
                after_one_day = apply_town_demand(inv, item, 24, unlocked_shops=())
                self.assertEqual(after_one_day, inv - 1)

    def test_shop_demand_adds_on_top_of_town_center(self):
        # FARMERS_MARKET lists WHEAT among 4 products (no single-product
        # 2x multiplier), consumed every shop_interval (4) steps.
        inv = MARKET_PARAMS["WHEAT"]["I0"]
        after_24_steps = apply_town_demand(
            inv, "WHEAT", 24, unlocked_shops=["FARMERS_MARKET"]
        )
        # 24 / 4 = 6 shop ticks (steps 0, 4, 8, 12, 16, 20) + 1 town-centre
        # tick (step 0) = 7 units drained.
        self.assertEqual(after_24_steps, inv - 7)

    def test_single_product_shop_pulls_double(self):
        # YARN_STORE lists only WOOL - the engine doubles single-product
        # shop consumption (kaggriculture.py:741). WOOL isn't one of the
        # five plantable crops this module focuses on, but it's a real
        # product in MARKET_PARAMS and the clearest way to exercise the
        # 2x-multiplier branch at all.
        self.assertIn("WOOL", MARKET_PARAMS)
        inv = MARKET_PARAMS["WOOL"]["I0"]
        after_4_steps = apply_town_demand(
            inv, "WOOL", 4, unlocked_shops=["YARN_STORE"]
        )
        # Step 0 triggers both ticks: the shop (2, single-product) and the
        # Town Center (1, WOOL isn't FERTILIZER) - 3 total over 4 steps.
        self.assertEqual(after_4_steps, inv - 3)


class TestSimulateSingleProduct(unittest.TestCase):
    def test_stages_are_distinct_and_ordered_by_supply(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                I0 = MARKET_PARAMS[item]["I0"]
                result = simulate_single_product(
                    item,
                    I0,
                    our_supply=10,
                    opponent_supply=10,
                    turns_ahead=48,
                    unlocked_shops=(),
                )
                # More supply in the market can only push price down or
                # leave it flat (at the floor), never up.
                self.assertGreaterEqual(
                    result["spot_price"], result["price_after_our_sale"]
                )
                self.assertGreaterEqual(
                    result["price_after_our_sale"],
                    result["price_after_opponent_supply"],
                )

    def test_zero_supply_and_zero_turns_returns_spot_price_everywhere(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                I0 = MARKET_PARAMS[item]["I0"]
                result = simulate_single_product(item, I0)
                spot = market_price(item, I0)
                self.assertEqual(result["spot_price"], spot)
                self.assertEqual(result["price_after_our_sale"], spot)
                self.assertEqual(result["price_after_opponent_supply"], spot)
                self.assertEqual(result["future_price"], spot)

    def test_town_demand_recovers_price_after_a_glut(self):
        # Sell enough to depress price below baseline, then confirm that
        # letting town demand run for a while brings price back up (not
        # necessarily all the way to base - that depends on the crop).
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                I0 = MARKET_PARAMS[item]["I0"]
                glut = simulate_single_product(item, I0, our_supply=30, turns_ahead=0)
                recovered = simulate_single_product(
                    item, I0, our_supply=30, turns_ahead=240, unlocked_shops=()
                )
                self.assertGreaterEqual(
                    recovered["future_price"], glut["price_after_our_sale"]
                )


class TestEstimateFuturePrice(unittest.TestCase):
    def test_returns_future_price_key_for_every_crop(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                I0 = MARKET_PARAMS[item]["I0"]
                result = estimate_future_price(
                    item,
                    I0,
                    turns_ahead=24,
                    our_pipeline_supply=6,
                    opponent_pipeline_supply=6,
                )
                self.assertIn("future_price", result)
                self.assertGreaterEqual(result["future_price"], 1)

    def test_more_turns_ahead_never_reduces_recovery(self):
        # With supply fixed and no further shop unlocks assumed, letting
        # more town-demand turns elapse should never make price lower than
        # a shorter window did (monotonic drain of the same glut).
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                I0 = MARKET_PARAMS[item]["I0"]
                short = estimate_future_price(
                    item, I0, turns_ahead=24, our_pipeline_supply=20,
                    unlocked_shops=(),
                )
                long = estimate_future_price(
                    item, I0, turns_ahead=240, our_pipeline_supply=20,
                    unlocked_shops=(),
                )
                self.assertGreaterEqual(long["future_price"], short["future_price"])


class TestRecommendSellQuantity(unittest.TestCase):
    def test_returns_zero_when_nothing_available(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                I0 = MARKET_PARAMS[item]["I0"]
                self.assertEqual(
                    recommend_sell_quantity(item, I0, 0, min_acceptable_price=10), 0
                )

    def test_respects_available_quantity_cap(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                I0 = MARKET_PARAMS[item]["I0"]
                recommended = recommend_sell_quantity(
                    item, I0, available_quantity=3, min_acceptable_price=1
                )
                self.assertLessEqual(recommended, 3)

    def test_respects_max_per_turn_cap(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                I0 = MARKET_PARAMS[item]["I0"]
                recommended = recommend_sell_quantity(
                    item,
                    I0,
                    available_quantity=1000,
                    min_acceptable_price=1,
                    max_per_turn=15,
                )
                self.assertLessEqual(recommended, 15)

    def test_stops_before_price_drops_below_minimum(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                I0 = MARKET_PARAMS[item]["I0"]
                base = MARKET_PARAMS[item]["base"]
                threshold = max(1, base // 2)
                recommended = recommend_sell_quantity(
                    item, I0, available_quantity=1000, min_acceptable_price=threshold
                )
                path = price_path_for_sale(item, I0, recommended)
                self.assertTrue(all(p >= threshold for p in path["prices"]))
                # One more unit than recommended must drop below threshold
                # (or there was nothing left to sell above it at all).
                if recommended < 1000:
                    next_price = market_price(item, path["ending_inventory"])
                    self.assertLess(next_price, threshold)

    def test_never_recommends_more_than_a_zero_threshold_edge_case(self):
        for item in PLANTABLE_CROPS:
            with self.subTest(item=item):
                I0 = MARKET_PARAMS[item]["I0"]
                self.assertEqual(
                    recommend_sell_quantity(item, I0, 10, min_acceptable_price=0), 0
                )


if __name__ == "__main__":
    unittest.main()
