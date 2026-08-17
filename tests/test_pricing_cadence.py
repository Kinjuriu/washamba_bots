"""
Tests for experiments/pricing_cadence_lib.py - the sell-now-vs-hold
framework for the selling-cadence experiment
(experiments/pricing_cadence_experiment_report.md). NOT wired into
main.py; these are the three new deterministic functions the experiment
adds (estimate_sell_or_hold_value, inventory_pressure, cadence_urgency).

Run with:
    python -m unittest discover -s tests
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "experiments"))

from pricing_cadence_lib import (  # noqa: E402
    MAX_SELL_PER_TURN,
    cadence_urgency,
    estimate_sell_or_hold_value,
    inventory_pressure,
)

PLANTABLE_CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]


class TestEstimateSellOrHoldValue(unittest.TestCase):
    def test_zero_quantity_is_a_no_op(self):
        result = estimate_sell_or_hold_value("WHEAT", 0, 10000, day=0)
        self.assertEqual(result["value_now"], 0.0)
        self.assertEqual(result["value_hold"], 0.0)
        self.assertFalse(result["hold_is_better"])

    def test_value_now_matches_the_real_price_path(self):
        # Cross-check against price_path_for_sale directly rather than
        # trusting estimate_sell_or_hold_value's own arithmetic.
        from pricing import price_path_for_sale

        result = estimate_sell_or_hold_value("MELON", 10, 10000, day=0)
        path = price_path_for_sale("MELON", 10000, 10)
        self.assertEqual(result["value_now"], sum(path["prices"]))

    def test_heavy_pipeline_makes_holding_worse_not_better(self):
        # A crop with a lot of our own supply already committed should
        # have its forecast price crushed by the time it lands - holding
        # should look worse than selling now, not better.
        for crop in PLANTABLE_CROPS:
            with self.subTest(crop=crop):
                no_pipeline = estimate_sell_or_hold_value(
                    crop, 10, 10000, day=0, pipeline_supply=0
                )
                heavy_pipeline = estimate_sell_or_hold_value(
                    crop, 10, 10000, day=0, pipeline_supply=500
                )
                self.assertLessEqual(
                    heavy_pipeline["value_hold_per_unit"],
                    no_pipeline["value_hold_per_unit"],
                )

    def test_opponent_pipeline_also_depresses_the_hold_value(self):
        no_opponent = estimate_sell_or_hold_value(
            "STRAWBERRY", 10, 10000, day=0, opponent_pipeline_supply=0
        )
        with_opponent = estimate_sell_or_hold_value(
            "STRAWBERRY", 10, 10000, day=0, opponent_pipeline_supply=300
        )
        self.assertLess(
            with_opponent["value_hold_per_unit"], no_opponent["value_hold_per_unit"]
        )

    def test_hold_is_better_flag_matches_the_totals(self):
        for crop in PLANTABLE_CROPS:
            with self.subTest(crop=crop):
                result = estimate_sell_or_hold_value(crop, 5, 10000, day=0)
                self.assertEqual(
                    result["hold_is_better"],
                    result["value_hold"] > result["value_now"],
                )

    def test_longer_horizon_never_undershoots_a_shorter_one_at_baseline(self):
        # At baseline inventory with no supply landing, price only ever
        # drifts toward base as town demand nibbles at it - never crashes
        # further - so a longer hold horizon shouldn't score worse.
        short = estimate_sell_or_hold_value("WHEAT", 5, 10000, day=0, horizon_days=1)
        long = estimate_sell_or_hold_value("WHEAT", 5, 10000, day=0, horizon_days=10)
        self.assertGreaterEqual(long["value_hold_per_unit"], short["value_hold_per_unit"])


class TestInventoryPressure(unittest.TestCase):
    def test_zero_carried_is_zero_pressure(self):
        self.assertEqual(inventory_pressure("MELON", 0, 0, remaining_days=10), 0.0)

    def test_pressure_rises_with_carried_quantity(self):
        low = inventory_pressure("MELON", 10, 0, remaining_days=10)
        high = inventory_pressure("MELON", 200, 0, remaining_days=10)
        self.assertGreater(high, low)

    def test_pressure_falls_as_remaining_days_grow(self):
        # Same pile, more days left to sell it in - less pressure.
        tight = inventory_pressure("MELON", 100, 0, remaining_days=2)
        loose = inventory_pressure("MELON", 100, 0, remaining_days=20)
        self.assertGreater(tight, loose)

    def test_a_pile_bigger_than_capacity_exceeds_one(self):
        # MELON's per-turn cap is 15; carrying 10x that with only 1 day
        # left is a textbook "cannot possibly clear this in time."
        cap = MAX_SELL_PER_TURN["MELON"]
        pressure = inventory_pressure("MELON", cap * 10, 0, remaining_days=1)
        self.assertGreater(pressure, 1.0)

    def test_products_without_a_listed_cap_get_a_generous_ceiling(self):
        # WHEAT has no MAX_SELL_PER_TURN entry - a moderate pile shouldn't
        # register as heavy pressure the way it would for a capped good.
        pressure = inventory_pressure("WHEAT", 50, 0, remaining_days=10)
        self.assertLess(pressure, 0.1)


class TestCadenceUrgency(unittest.TestCase):
    def test_zero_at_day_zero(self):
        self.assertEqual(cadence_urgency(0), 0.0)

    def test_rises_toward_one_near_season_end(self):
        self.assertGreater(cadence_urgency(28), cadence_urgency(10))
        self.assertLessEqual(cadence_urgency(29), 1.0)

    def test_monotonically_non_decreasing_across_the_season(self):
        values = [cadence_urgency(day) for day in range(30)]
        for earlier, later in zip(values, values[1:]):
            self.assertLessEqual(earlier, later)

    def test_never_exceeds_one_past_the_season(self):
        self.assertEqual(cadence_urgency(100), 1.0)

    def test_saturates_before_liquidation_start_day(self):
        # V1.1 finding: agent_d.py's liquidating branch overrides min_price
        # to PRICE_FLOOR from LIQUIDATION_START_DAY (19) on, so
        # CADENCE_URGENCY_PRICE_WEIGHT's effective window is days 0-18, not
        # 0-29 - urgency at day 18 is meaningfully below 1.0, not saturated.
        LIQUIDATION_START_DAY = 19
        self.assertLess(cadence_urgency(LIQUIDATION_START_DAY - 1), 0.7)


class TestCropAsymmetry(unittest.TestCase):
    """V1.1 finding: inventory_pressure's per-turn-cap lookup only has real
    entries for STRAWBERRY/MELON/WOOL (main.py's MAX_SELL_PER_TURN), so two
    of the four D constants are structurally inert for every other product.
    Regression-guards that finding so it isn't rediscovered by accident."""

    def test_capped_goods_reach_meaningful_pressure(self):
        for crop in ("STRAWBERRY", "MELON", "WOOL"):
            with self.subTest(crop=crop):
                cap = MAX_SELL_PER_TURN[crop]
                pressure = inventory_pressure(crop, cap * 5, 0, remaining_days=3)
                self.assertGreater(pressure, 0.5)

    def test_uncapped_goods_never_reach_meaningful_pressure(self):
        # A pile that would be enormous pressure for a capped good barely
        # registers for a product with no MAX_SELL_PER_TURN entry, because
        # inventory_pressure falls back to a 10,000-unit synthetic cap.
        for crop in ("WHEAT", "CARROT", "TOMATO"):
            with self.subTest(crop=crop):
                pressure = inventory_pressure(crop, 500, 0, remaining_days=3)
                self.assertLess(pressure, 0.1)


if __name__ == "__main__":
    unittest.main()
