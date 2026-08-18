"""Unit tests for the two new pure validators in
replay_shape_instrumentation.py (market pressure, feed collapse) added
for the head-to-head/self-validation integration - REJECTED, see
replay_shape_validation_report.md one directory up. Synthetic `days`
lists only - no engine calls, matches this repo's existing
unittest.TestCase convention.

Experiment-specific test, not part of the production suite - not
discovered by `python -m unittest discover -s tests`. Run directly:
    python -m unittest discover -s experiments/replay_shape/tests
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from replay_shape_instrumentation import (  # noqa: E402
    BASE_PRICES,
    validate_market_pressure,
    validate_no_feed_collapse,
)


def make_day(day, animals_placed=None, market_prices=None):
    return {
        "day": day,
        "animals_placed": animals_placed or {},
        "market_prices": market_prices or dict(BASE_PRICES),
    }


class TestValidateMarketPressure(unittest.TestCase):
    def test_passes_when_a_premium_product_crashes(self):
        days = [make_day(0), make_day(29, market_prices={**BASE_PRICES, "MELON": 90})]
        passed, detail = validate_market_pressure(days)
        self.assertTrue(passed)
        self.assertIn("MELON", detail)

    def test_fails_when_all_premium_prices_stay_near_base(self):
        days = [make_day(0), make_day(29, market_prices=dict(BASE_PRICES))]
        passed, _ = validate_market_pressure(days)
        self.assertFalse(passed)

    def test_ignores_non_premium_products(self):
        # WHEAT crashing (base $25, not premium) should not count.
        days = [make_day(0), make_day(29, market_prices={**BASE_PRICES, "WHEAT": 1})]
        passed, _ = validate_market_pressure(days)
        self.assertFalse(passed)


class TestValidateNoFeedCollapse(unittest.TestCase):
    def test_passes_when_animal_count_never_drops(self):
        days = [
            make_day(0, {"COW": 1}),
            make_day(1, {"COW": 2}),
            make_day(2, {"COW": 2, "SHEEP": 1}),
        ]
        passed, _ = validate_no_feed_collapse(days)
        self.assertTrue(passed)

    def test_fails_when_count_drops_below_its_own_peak(self):
        days = [
            make_day(0, {"COW": 1}),
            make_day(1, {"COW": 3, "SHEEP": 2}),  # peak = 5
            make_day(2, {"COW": 2}),  # final = 2, below peak
        ]
        passed, detail = validate_no_feed_collapse(days)
        self.assertFalse(passed)
        self.assertIn("peak placed=5", detail)
        self.assertIn("final placed=2", detail)


if __name__ == "__main__":
    unittest.main()
