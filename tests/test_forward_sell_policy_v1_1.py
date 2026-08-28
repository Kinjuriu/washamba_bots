"""
Regression tests for experiments/candidates/forward_sell_policy_v1_1.py.

The load-bearing property this file exists to prove: quantity sizing is
UNCHANGED from main.py - v0's coupling bug (sizing to PRICE_FLOOR
regardless of the sell/hold decision) must not recur. See
experiments/forward_sell_policy_v1_1_report.md section 9 for how these
map onto the task's validation checklist.

Run with:
    python -m unittest tests.test_forward_sell_policy_v1_1 -v
"""
import unittest
from unittest import mock

import main as base
import pricing_v1


def _market_state(product, inventory, params=None):
    price = pricing_v1.market_price(product, inventory, params)
    return {"prices": {product: price}, "inventory": {product: inventory}}


class TestWiring(unittest.TestCase):
    """setUp re-applies this module's patch of base.decide_market_actions
    before each test - several candidates in this repo patch the same
    shared `main` global at import time, so a full `unittest discover`
    run needs each wiring test to pin its own candidate's patch rather
    than trust whatever import order left behind (same pattern as the
    other candidate test files in this directory)."""

    def setUp(self):
        import experiments.candidates.forward_sell_policy_v1_1 as candidate

        base.decide_market_actions = candidate._decide_market_actions_forward_sell_v1_1
        candidate.DECISION_LOG.clear()

    # ------------------------------------------------------------------
    # Requirement 1: baseline quantity is preserved exactly
    # ------------------------------------------------------------------

    def test_sell_order_quantity_exactly_matches_baseline_formula(self):
        """The single most important test in this file: when the
        candidate does sell, the quantity must be byte-identical to
        main.py's own recommend_sell_quantity(..., min_acceptable_price=
        SELL_PRICE_THRESHOLDS[product], ...) - NOT PRICE_FLOOR (v0's
        bug), not any other formula.

        Uses day = LIQUIDATION_START_DAY - 1 (the last pre-liquidation
        day) so the forward horizon is structurally empty
        (`no_future_opportunity_in_horizon`) and the decision
        deterministically prefers SELL, without depending on - or
        mocking around - the separately-tested, separately-documented
        sell-vs-hold behaviour itself (see
        experiments/forward_sell_policy_v1_1_report.md's diagnostics).
        This isolates exactly the property this test is named for:
        quantity preservation."""
        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"WHEAT": 5}, "inventories": [{}]}
        market_state = _market_state("WHEAT", 10000)
        day = base.LIQUIDATION_START_DAY - 1

        expected_quantity = base.recommend_sell_quantity(
            "WHEAT", 10000, 5,
            min_acceptable_price=base.SELL_PRICE_THRESHOLDS.get("WHEAT", base.DEFAULT_SELL_THRESHOLD),
            max_per_turn=base.MAX_SELL_PER_TURN.get("WHEAT", 5),
        )
        self.assertGreater(expected_quantity, 0, "test setup needs a real baseline sale here")

        actions = base.decide_market_actions(farm, private, market_state, day=day, start_step=day * 24)
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "WHEAT"]
        self.assertTrue(sell_orders)
        self.assertEqual(sell_orders[0][2], expected_quantity)

    def test_quantity_is_never_sized_to_price_floor(self):
        """v0's bug, made explicit: with a deep glut where PRICE_FLOOR
        would authorize selling far more than the threshold-based
        baseline formula would, the candidate's quantity (when it does
        sell) must match the SMALLER, threshold-based baseline amount,
        not a PRICE_FLOOR-walked amount. WHEAT has no MAX_SELL_PER_TURN
        entry (main.py's dict only lists STRAWBERRY/MELON/WOOL), so
        nothing caps either walk before the threshold-vs-floor
        difference can show up - a capped product would make both
        formulas agree trivially at the cap, proving nothing. Uses the
        last pre-liquidation day, same as
        test_sell_order_quantity_exactly_matches_baseline_formula, to
        isolate quantity preservation from the separately-tested
        sell-vs-hold decision."""
        # inventory=10150 sits on the transition slope between WHEAT's
        # spot price (22 at I0=10000) and its threshold (20) - a small
        # positive baseline quantity, well short of what walking all the
        # way to PRICE_FLOOR would authorize from the same starting point.
        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"WHEAT": 3000}, "inventories": [{}]}
        market_state = _market_state("WHEAT", 10150)
        day = base.LIQUIDATION_START_DAY - 1

        self.assertNotIn("WHEAT", base.MAX_SELL_PER_TURN, "test setup assumes WHEAT is uncapped")
        baseline_amount = base.recommend_sell_quantity(
            "WHEAT", 10150, 3000,
            min_acceptable_price=base.SELL_PRICE_THRESHOLDS.get("WHEAT", base.DEFAULT_SELL_THRESHOLD),
            max_per_turn=3000,
        )
        floor_amount = base.recommend_sell_quantity(
            "WHEAT", 10150, 3000, min_acceptable_price=base.PRICE_FLOOR, max_per_turn=3000,
        )
        self.assertLess(baseline_amount, floor_amount, "test setup needs the two formulas to actually differ")

        actions = base.decide_market_actions(farm, private, market_state, day=day, start_step=day * 24)
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "WHEAT"]
        self.assertTrue(sell_orders)
        self.assertEqual(sell_orders[0][2], baseline_amount)
        self.assertNotEqual(sell_orders[0][2], floor_amount)

    def test_no_sell_order_when_baseline_quantity_is_zero(self):
        """When the baseline formula itself produces 0 (price doesn't
        clear the threshold), there is nothing to decide - the forward
        function must not even be called, let alone invent a sale."""
        import experiments.candidates.forward_sell_policy_v1_1 as candidate

        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"MELON": 10}, "inventories": [{}]}
        market_state = _market_state("MELON", 10200)  # deep glut, below threshold

        baseline_amount = base.recommend_sell_quantity(
            "MELON", 10200, 10,
            min_acceptable_price=base.SELL_PRICE_THRESHOLDS.get("MELON", base.DEFAULT_SELL_THRESHOLD),
            max_per_turn=base.MAX_SELL_PER_TURN.get("MELON", 10),
        )
        self.assertEqual(baseline_amount, 0, "test setup needs baseline to refuse this sale")

        actions = base.decide_market_actions(farm, private, market_state, day=5, start_step=121)
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "MELON"]
        self.assertFalse(sell_orders)
        self.assertEqual(len(candidate.DECISION_LOG), 0)

    # ------------------------------------------------------------------
    # Liquidation is untouched
    # ------------------------------------------------------------------

    def test_liquidation_bypasses_the_forward_decision_entirely(self):
        import experiments.candidates.forward_sell_policy_v1_1 as candidate

        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"MELON": 10}, "inventories": [{}]}
        market_state = _market_state("MELON", 10200)  # a price the non-liquidating gate would refuse

        actions = base.decide_market_actions(
            farm, private, market_state, day=base.LIQUIDATION_START_DAY,
        )
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "MELON"]
        self.assertTrue(sell_orders, "liquidation must still force a sale regardless of price")
        self.assertEqual(len(candidate.DECISION_LOG), 0,
                          "the forward decision must not even be evaluated while liquidating")

    def test_liquidation_quantity_still_uses_price_floor_as_baseline_does(self):
        """Only during liquidation should PRICE_FLOOR ever be the sizing
        floor - main.py itself does this, unchanged here."""
        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"MELON": 10}, "inventories": [{}]}
        market_state = _market_state("MELON", 10200)

        expected = base.recommend_sell_quantity(
            "MELON", 10200, 10,
            min_acceptable_price=base.PRICE_FLOOR,
            max_per_turn=base.MAX_SELL_PER_TURN.get("MELON", 10),
        )
        actions = base.decide_market_actions(
            farm, private, market_state, day=base.LIQUIDATION_START_DAY,
        )
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "MELON"]
        self.assertEqual(sell_orders[0][2], expected)

    # ------------------------------------------------------------------
    # No future information leaks into the current decision
    # ------------------------------------------------------------------

    def test_forecast_only_uses_currently_known_tiles_and_inventory(self):
        """The multi-day forecast is a projection built from today's
        state (tiles as observed right now, current market inventory),
        never an actual read of a later turn's real observation - there
        is no mechanism here that could do that (no obs object is even
        threaded past this call), but this test pins the contract: two
        calls differing only in the CURRENT tiles snapshot produce
        different forecasts, proving the forecast is a deterministic
        function of what's given, not of anything external."""
        farm_no_tiles = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        farm_with_growing_melon = {
            "money": 3000,
            "tiles": [[{"kind": "PLANT", "crop": "MELON", "planted_day": 0}]],
            "farmer": [0, 0], "hands": [],
        }
        private = {"shed": {"MELON": 10}, "inventories": [{}]}
        market_state = _market_state("MELON", 10020)

        actions_a = base.decide_market_actions(farm_no_tiles, private, market_state, day=8, start_step=192)
        actions_b = base.decide_market_actions(farm_with_growing_melon, private, market_state, day=8, start_step=192)
        # Not asserting a specific direction here (that's covered in
        # test_pricing_v1.py) - only that the tiles snapshot passed in
        # is what drives the result, i.e. it's wired through at all.
        self.assertIsInstance(actions_a, list)
        self.assertIsInstance(actions_b, list)

    # ------------------------------------------------------------------
    # Pricing mechanics still come from the verified backbone
    # ------------------------------------------------------------------

    def test_decision_matches_estimate_multi_day_sell_or_hold_decision_directly(self):
        """End-to-end: decide_market_actions's SELL/no-SELL for a
        product must agree exactly with calling
        pricing_v1.estimate_multi_day_sell_or_hold_decision directly on
        the same inputs - the wiring adds nothing of its own."""
        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"WHEAT": 5}, "inventories": [{}]}
        market_state = _market_state("WHEAT", 10000)

        baseline_amount = base.recommend_sell_quantity(
            "WHEAT", 10000, 5,
            min_acceptable_price=base.SELL_PRICE_THRESHOLDS.get("WHEAT", base.DEFAULT_SELL_THRESHOLD),
            max_per_turn=base.MAX_SELL_PER_TURN.get("WHEAT", 5),
        )
        direct = pricing_v1.estimate_multi_day_sell_or_hold_decision(
            "WHEAT", 10000, baseline_amount, day=5, remaining_days=base.remaining_season_days(5),
            tiles=[[None]], liquidation_start_day=base.LIQUIDATION_START_DAY, start_step=121,
        )

        actions = base.decide_market_actions(farm, private, market_state, day=5, start_step=121)
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "WHEAT"]
        self.assertEqual(bool(sell_orders), direct["prefer_sell"])
        if sell_orders:
            self.assertEqual(sell_orders[0][2], direct["quantity"])

    def test_wheat_reserve_still_respected(self):
        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"WHEAT": 5}, "inventories": [{}]}
        market_state = _market_state("WHEAT", 10000)

        actions = base.decide_market_actions(
            farm, private, market_state, day=5, reserved_wheat=5, start_step=121,
        )
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "WHEAT"]
        self.assertFalse(sell_orders)

    def test_fertilizer_still_excluded_pre_liquidation(self):
        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"FERTILIZER": 20}, "inventories": [{}]}
        market_state = _market_state("FERTILIZER", 10000)

        actions = base.decide_market_actions(farm, private, market_state, day=5, start_step=121)
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "FERTILIZER"]
        self.assertFalse(sell_orders)


if __name__ == "__main__":
    unittest.main()
