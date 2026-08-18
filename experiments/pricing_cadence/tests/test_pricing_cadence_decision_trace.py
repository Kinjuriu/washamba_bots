"""
Tests for pricing_cadence_decision_trace.py's classify_decision() - the one
new deterministic function this round introduces (the rest of the module
is instrumentation/IO around real episodes, not independently testable
pure logic). See pricing_cadence_v1_2_mechanism_audit_report.md, one
directory up.

Experiment-specific test, not part of the production suite - not
discovered by `python -m unittest discover -s tests`. Run directly:
    python -m unittest discover -s experiments/pricing_cadence/tests
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pricing_cadence_decision_trace import classify_decision  # noqa: E402


class TestClassifyDecision(unittest.TestCase):
    def test_nothing_held_is_no_sell(self):
        self.assertEqual(
            classify_decision(desired_sell_quantity=0, cap=10, actual_sell_quantity=0, liquidating=False),
            "no-sell",
        )

    def test_liquidation_overrides_everything_else(self):
        # Even a decision that would otherwise look cap-bound is labelled
        # liquidation - price is not the gate once liquidating.
        self.assertEqual(
            classify_decision(desired_sell_quantity=20, cap=10, actual_sell_quantity=10, liquidating=True),
            "liquidation",
        )

    def test_zero_actual_with_something_held_is_no_sell(self):
        # Held stock existed, but the first unit already priced below
        # the acceptance threshold.
        self.assertEqual(
            classify_decision(desired_sell_quantity=5, cap=10, actual_sell_quantity=0, liquidating=False),
            "no-sell",
        )

    def test_sold_up_to_cap_below_desired_is_cap_bound(self):
        self.assertEqual(
            classify_decision(desired_sell_quantity=20, cap=10, actual_sell_quantity=10, liquidating=False),
            "cap-bound",
        )

    def test_sold_less_than_both_cap_and_desired_is_price_bound(self):
        # Cap (10) and desired (20) both leave room for more, but the
        # price path stopped the order early.
        self.assertEqual(
            classify_decision(desired_sell_quantity=20, cap=10, actual_sell_quantity=6, liquidating=False),
            "price-bound",
        )

    def test_sold_everything_held_with_cap_to_spare_is_inventory_bound(self):
        self.assertEqual(
            classify_decision(desired_sell_quantity=5, cap=10, actual_sell_quantity=5, liquidating=False),
            "inventory-bound",
        )

    def test_cap_equal_to_desired_and_fully_sold_is_inventory_bound_not_cap_bound(self):
        # The cap technically equals what was sold, but it never actually
        # constrained anything - selling everything held is the more
        # informative label when cap and desired coincide.
        self.assertEqual(
            classify_decision(desired_sell_quantity=10, cap=10, actual_sell_quantity=10, liquidating=False),
            "inventory-bound",
        )

    def test_price_bound_takes_priority_when_stopped_before_either_limit(self):
        for desired, cap, actual in [(50, 30, 12), (30, 50, 12)]:
            with self.subTest(desired=desired, cap=cap, actual=actual):
                self.assertEqual(
                    classify_decision(desired, cap, actual, liquidating=False),
                    "price-bound",
                )


if __name__ == "__main__":
    unittest.main()
