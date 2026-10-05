"""
Regression tests for experiments/candidates/forward_sell_policy_v0.py.

Tests the wiring (does decide_market_actions actually route through
pricing_v1.estimate_sell_or_hold_decision, does liquidation stay
untouched, is quantity sizing consistent) - not the decision math itself,
which tests/test_pricing_v1.py::TestEstimateSellOrHoldDecision already
covers in isolation.

Run with:
    python -m unittest tests.test_forward_sell_policy_v0 -v
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
    before each test - see tests/test_opponent_aware_sell_gate.py's
    matching note for why: several candidates in this repo patch the same
    shared `main` global at import time, so a full `unittest discover`
    run needs each wiring test to pin its own candidate's patch rather
    than trust whatever import order left behind."""

    def setUp(self):
        import experiments.candidates.forward_sell_policy_v0 as candidate

        base.decide_market_actions = candidate._decide_market_actions_forward_sell
        candidate.DECISION_LOG.clear()

    def test_produces_a_sell_order_when_the_decision_prefers_sell(self):
        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"WHEAT": 5}, "inventories": [{}]}
        market_state = _market_state("WHEAT", 10000)

        actions = base.decide_market_actions(
            farm, private, market_state, day=5, start_step=121,
        )
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "WHEAT"]
        self.assertTrue(sell_orders, "expected a forward-looking SELL order")

    def test_no_sell_order_when_the_decision_prefers_hold(self):
        import experiments.candidates.forward_sell_policy_v0 as candidate

        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"MELON": 10}, "inventories": [{}]}
        market_state = _market_state("MELON", 10020)

        with mock.patch(
            "pricing_v1.compare_immediate_vs_delayed_selling",
            return_value={
                "revenue_now": 10, "revenue_delayed": 1000, "advantage": 990,
                "delay_is_better": True, "inventory_at_delay": 10000,
                "revenue_now_per_unit": 1, "revenue_delayed_per_unit": 100,
            },
        ), mock.patch("pricing_v1.inventory_pressure", return_value=0.0):
            actions = base.decide_market_actions(
                farm, private, market_state, day=5, start_step=121,
            )
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "MELON"]
        self.assertFalse(sell_orders, "hold_beats_sell_now must not produce a SELL order")

    def test_liquidation_bypasses_the_forward_decision_entirely(self):
        """day >= LIQUIDATION_START_DAY must still mean "sell regardless
        of price" - this experiment does not touch or replace that rule,
        and this test proves estimate_sell_or_hold_decision is never even
        called on a liquidating turn."""
        import experiments.candidates.forward_sell_policy_v0 as candidate

        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"MELON": 10}, "inventories": [{}]}
        market_state = _market_state("MELON", 10020)

        actions = base.decide_market_actions(
            farm, private, market_state, day=base.LIQUIDATION_START_DAY,
        )
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "MELON"]
        self.assertTrue(sell_orders, "liquidation must still force a sale")
        self.assertEqual(len(candidate.DECISION_LOG), 0,
                          "the forward decision must not even be evaluated while liquidating")

    def test_wheat_reserve_still_respected(self):
        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"WHEAT": 5}, "inventories": [{}]}
        market_state = _market_state("WHEAT", 10000)

        actions = base.decide_market_actions(
            farm, private, market_state, day=5, reserved_wheat=5, start_step=121,
        )
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "WHEAT"]
        self.assertFalse(sell_orders, "the full reserve must be held back, nothing left to evaluate")

    def test_fertilizer_still_excluded_pre_liquidation(self):
        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"FERTILIZER": 20}, "inventories": [{}]}
        market_state = _market_state("FERTILIZER", 10000)

        actions = base.decide_market_actions(
            farm, private, market_state, day=5, start_step=121,
        )
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "FERTILIZER"]
        self.assertFalse(sell_orders)

    def test_quantity_never_exceeds_max_sell_per_turn(self):
        # MELON has an explicit, tighter-than-"everything held" cap
        # (base.MAX_SELL_PER_TURN["MELON"] == 15) - a product with no
        # entry falls back to `quantity` itself, which would make this
        # check trivially true regardless of whether the cap is honoured.
        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"MELON": 500}, "inventories": [{}]}
        market_state = _market_state("MELON", 10000)

        actions = base.decide_market_actions(
            farm, private, market_state, day=5, start_step=121,
        )
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "MELON"]
        cap = base.MAX_SELL_PER_TURN["MELON"]
        for order in sell_orders:
            self.assertLessEqual(order[2], cap)

    def test_decision_log_records_one_entry_per_evaluated_product(self):
        import experiments.candidates.forward_sell_policy_v0 as candidate

        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"WHEAT": 5, "CARROT": 3}, "inventories": [{}]}
        market_state = {
            "prices": {
                "WHEAT": pricing_v1.market_price("WHEAT", 10000),
                "CARROT": pricing_v1.market_price("CARROT", 10000),
            },
            "inventory": {"WHEAT": 10000, "CARROT": 10000},
        }

        base.decide_market_actions(farm, private, market_state, day=5, start_step=121)
        products_logged = {r["product"] for r in candidate.DECISION_LOG}
        self.assertEqual(products_logged, {"WHEAT", "CARROT"})


if __name__ == "__main__":
    unittest.main()
