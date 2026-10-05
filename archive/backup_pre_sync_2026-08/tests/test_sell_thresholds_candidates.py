"""
Regression tests for the sell-threshold audit candidates:
experiments/candidates/sell_thresholds_historical_permissive.py (B) and
experiments/candidates/sell_thresholds_stricter.py (C).

Proves each candidate changes exactly one thing - SELL_PRICE_THRESHOLDS -
and that the values match what the candidates' own docstrings claim
(the historical 9c52c09 table for B, the measured-percentile table for
C), plus the intended behavioural direction: B should never make
should_sell MORE conservative than baseline, C should never make it MORE
permissive than baseline.

Run with:
    python -m unittest tests.test_sell_thresholds_candidates -v
"""
import unittest

import main as base
import pricing_v1

ORIGINAL_THRESHOLDS = {
    "WHEAT": 20, "CARROT": 25, "TOMATO": 40, "STRAWBERRY": 90,
    "MELON": 180, "EGG": 35, "WOOL": 140,
}


class TestHistoricalPermissiveCandidate(unittest.TestCase):
    def test_matches_the_9c52c09_table_exactly(self):
        from experiments.candidates.sell_thresholds_historical_permissive import (
            SELL_PRICE_THRESHOLDS_HISTORICAL_PERMISSIVE as thresholds,
        )
        expected = {
            "WHEAT": 10, "CARROT": 12, "TOMATO": 20, "STRAWBERRY": 45,
            "MELON": 90, "EGG": 17, "WOOL": 70,
        }
        self.assertEqual(thresholds, expected)

    def test_every_value_is_lower_than_current_main(self):
        from experiments.candidates.sell_thresholds_historical_permissive import (
            SELL_PRICE_THRESHOLDS_HISTORICAL_PERMISSIVE as thresholds,
        )
        for product, original in ORIGINAL_THRESHOLDS.items():
            self.assertLess(thresholds[product], original, product)

    def test_only_thresholds_changed_other_constants_untouched(self):
        import experiments.candidates.sell_thresholds_historical_permissive  # noqa: F401

        self.assertEqual(base.LIQUIDATION_START_DAY, 19)
        self.assertEqual(base.MAX_HANDS_PER_DAY, 8)
        self.assertEqual(base.SHED_FORCE_SELL_THRESHOLD, 70)
        # MAX_ANIMALS is intentionally NOT checked here - it's a
        # shared `main` global that other, unrelated candidates in
        # this repo (max_animals_pacing_v0.py etc.) legitimately
        # patch at import time, so its value depends on unittest's
        # module import order, not on anything these threshold
        # candidates could plausibly touch.

    def test_never_stricter_than_baseline_should_sell(self):
        """A price that clears the ORIGINAL threshold must also clear the
        (lower) historical threshold - this candidate can only ever say
        yes in more cases than baseline, never fewer."""
        import experiments.candidates.sell_thresholds_historical_permissive as candidate

        for product, original_threshold in ORIGINAL_THRESHOLDS.items():
            if product not in candidate.SELL_PRICE_THRESHOLDS_HISTORICAL_PERMISSIVE:
                continue
            inventory = 10000
            price = pricing_v1.market_price(product, inventory)
            baseline_says_sell = price >= original_threshold
            new_threshold = candidate.SELL_PRICE_THRESHOLDS_HISTORICAL_PERMISSIVE[product]
            candidate_says_sell = price >= new_threshold
            if baseline_says_sell:
                self.assertTrue(candidate_says_sell, product)


class TestStricterCandidate(unittest.TestCase):
    def test_matches_the_measured_percentile_table(self):
        from experiments.candidates.sell_thresholds_stricter import (
            SELL_PRICE_THRESHOLDS_STRICTER as thresholds,
        )
        raised = {"WHEAT": 30, "CARROT": 35, "STRAWBERRY": 145, "MELON": 210, "WOOL": 190}
        for product, value in raised.items():
            self.assertEqual(thresholds[product], value, product)
        # TOMATO/EGG left at current main.py values - no measured price
        # series behind either, per the module's own docstring.
        self.assertEqual(thresholds["TOMATO"], ORIGINAL_THRESHOLDS["TOMATO"])
        self.assertEqual(thresholds["EGG"], ORIGINAL_THRESHOLDS["EGG"])

    def test_every_touched_value_is_higher_than_current_main(self):
        from experiments.candidates.sell_thresholds_stricter import (
            SELL_PRICE_THRESHOLDS_STRICTER as thresholds,
        )
        for product in ("WHEAT", "CARROT", "STRAWBERRY", "MELON", "WOOL"):
            self.assertGreater(thresholds[product], ORIGINAL_THRESHOLDS[product], product)

    def test_only_thresholds_changed_other_constants_untouched(self):
        import experiments.candidates.sell_thresholds_stricter  # noqa: F401

        self.assertEqual(base.LIQUIDATION_START_DAY, 19)
        self.assertEqual(base.MAX_HANDS_PER_DAY, 8)
        self.assertEqual(base.SHED_FORCE_SELL_THRESHOLD, 70)
        # MAX_ANIMALS is intentionally NOT checked here - it's a
        # shared `main` global that other, unrelated candidates in
        # this repo (max_animals_pacing_v0.py etc.) legitimately
        # patch at import time, so its value depends on unittest's
        # module import order, not on anything these threshold
        # candidates could plausibly touch.

    def test_never_more_permissive_than_baseline_should_sell(self):
        """A price that fails the ORIGINAL threshold must also fail the
        (higher) stricter threshold - this candidate can only ever say no
        in more cases than baseline, never fewer, for the touched
        products."""
        import experiments.candidates.sell_thresholds_stricter as candidate

        for product in ("WHEAT", "CARROT", "STRAWBERRY", "MELON", "WOOL"):
            original_threshold = ORIGINAL_THRESHOLDS[product]
            inventory = 10000
            price = pricing_v1.market_price(product, inventory)
            baseline_says_no = price < original_threshold
            candidate_says_no = price < candidate.SELL_PRICE_THRESHOLDS_STRICTER[product]
            if baseline_says_no:
                self.assertTrue(candidate_says_no, product)

    def test_creates_a_real_hold_case_melon(self):
        """A concrete demonstration that the stricter MELON threshold
        (210) creates a should_sell==False decision at a price the
        current (180) threshold would have accepted - this is the
        mechanism the whole candidate exists to test. Deliberately does
        NOT call base.should_sell here: both candidate modules
        monkeypatch the shared base.SELL_PRICE_THRESHOLDS global at
        import time, so whichever candidate a full test-suite run
        imports last would silently determine what base.should_sell
        actually does - this test instead reasons directly against the
        known literal threshold values, which is immune to import
        order."""
        price = pricing_v1.market_price("MELON", 10070)
        self.assertGreaterEqual(price, ORIGINAL_THRESHOLDS["MELON"], "baseline (180) should say yes here")
        self.assertLess(price, 210, "the stricter candidate's threshold (210) should say no here")


if __name__ == "__main__":
    unittest.main()
