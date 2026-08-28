"""
Regression tests for experiments/candidates/opponent_aware_sell_gate.py
(pricing track, Experiment 3: opponent-supply-aware sell gate).

Tests the new deterministic logic (should_sell_opponent_aware) in
isolation from the evaluation results - see
experiments/opponent_aware_sell_gate_report.md for those. The point of
this file is to prove the isolation properties the module's docstring
claims, not just that the function runs.

Run with:
    python -m unittest tests.test_opponent_aware_sell_gate -v
"""
import unittest
from unittest import mock

import main as base
import pricing_v1
from experiments.candidates.opponent_aware_sell_gate import (
    OPPONENT_AWARE_HORIZON_TURNS,
    should_sell_opponent_aware,
)


def _market_state(product, inventory, params=None):
    price = pricing_v1.market_price(product, inventory, params)
    return {"prices": {product: price}, "inventory": {product: inventory}}


class TestIdenticalToBaselineWhenOpponentUnitsIsZero(unittest.TestCase):
    """The isolation guarantee the whole experiment depends on: zero
    opponent-visible supply must produce byte-identical behaviour to
    unmodified should_sell, in both directions."""

    def test_matches_baseline_true_case(self):
        market_state = _market_state("MELON", 10000)  # spot price clears threshold
        self.assertTrue(base.should_sell("MELON", 10, market_state))
        self.assertEqual(
            should_sell_opponent_aware("MELON", 10, market_state, 0, day=5),
            base.should_sell("MELON", 10, market_state),
        )

    def test_matches_baseline_false_case(self):
        market_state = _market_state("MELON", 10200)  # deep glut, below threshold
        self.assertFalse(base.should_sell("MELON", 10, market_state))
        self.assertEqual(
            should_sell_opponent_aware("MELON", 10, market_state, 0, day=5),
            base.should_sell("MELON", 10, market_state),
        )

    def test_negative_opponent_units_also_treated_as_no_signal(self):
        # Defensive: count_opponent_pipeline never produces negative
        # counts, but the gate must not misbehave if it somehow did.
        market_state = _market_state("MELON", 10200)
        self.assertFalse(should_sell_opponent_aware("MELON", 10, market_state, -5, day=5))


class TestNeverSuppressesAnExistingSell(unittest.TestCase):
    def test_stays_true_regardless_of_opponent_units(self):
        market_state = _market_state("WHEAT", 10000)  # clears threshold on its own
        self.assertTrue(base.should_sell("WHEAT", 10, market_state))
        for opponent_units in (0, 1, 50, 500):
            self.assertTrue(
                should_sell_opponent_aware("WHEAT", 10, market_state, opponent_units, day=5)
            )


class TestOverrideFiresWhenDelayIsGenuinelyWorse(unittest.TestCase):
    """A real, non-mocked case: MELON in a moderate glut (baseline says no),
    where a small amount of opponent supply is enough to make a 1-day wait
    worse than selling now - both directly asserted here, and cross-checked
    against pricing_v1.compare_immediate_vs_delayed_selling on the exact
    same inputs so the two can't silently disagree."""

    def test_fires_and_agrees_with_compare_immediate_vs_delayed_selling(self):
        inventory = 10100
        market_state = _market_state("MELON", inventory)
        self.assertFalse(base.should_sell("MELON", 10, market_state))

        opponent_units = 5
        result = should_sell_opponent_aware(
            "MELON", 10, market_state, opponent_units, day=5,
        )
        comparison = pricing_v1.compare_immediate_vs_delayed_selling(
            "MELON", inventory, 10, day=5, delay_turns=OPPONENT_AWARE_HORIZON_TURNS,
            our_pipeline_supply=0, opponent_pipeline_supply=opponent_units,
        )
        self.assertTrue(result)
        self.assertFalse(comparison["delay_is_better"])
        self.assertEqual(result, not comparison["delay_is_better"])


class TestOverrideDoesNotFireOnEveryPositiveOpponentSupply(unittest.TestCase):
    """Proves this isn't `return opponent_units > 0` in disguise: with the
    comparison mocked to say delay is better, the gate must respect that
    and stay False, even though opponent_units alone is positive. Uses a
    mock rather than searching for a natural numeric case, because at the
    module's 1-day horizon, real market curves in this game make the
    override fire on almost any positive opponent supply once the
    baseline has already failed (see the experiment report's "how often
    does this fire" diagnostic) - which is itself a finding, not a reason
    to skip testing the branch that says no."""

    def test_defers_to_the_comparison_when_it_says_wait(self):
        market_state = _market_state("MELON", 10200)
        self.assertFalse(base.should_sell("MELON", 10, market_state))

        with mock.patch(
            "experiments.candidates.opponent_aware_sell_gate.pricing_v1.compare_immediate_vs_delayed_selling",
            return_value={"delay_is_better": True, "revenue_now": 10, "revenue_delayed": 20, "advantage": 10},
        ):
            result = should_sell_opponent_aware("MELON", 10, market_state, 3, day=5)
        self.assertFalse(result)


class TestQuantityAndDayEdgeCases(unittest.TestCase):
    def test_zero_quantity_is_always_false(self):
        market_state = _market_state("MELON", 10200)
        self.assertFalse(should_sell_opponent_aware("MELON", 0, market_state, 100, day=5))

    def test_start_step_defaults_from_day_when_not_supplied(self):
        # Should not raise, and should match an explicit start_step of
        # day * DEFAULT_TURNS_PER_DAY.
        market_state = _market_state("MELON", 10100)
        implicit = should_sell_opponent_aware("MELON", 10, market_state, 5, day=5)
        explicit = should_sell_opponent_aware(
            "MELON", 10, market_state, 5, day=5, start_step=5 * base.DEFAULT_TURNS_PER_DAY,
        )
        self.assertEqual(implicit, explicit)


class TestDecideMarketActionsOpponentAwareIsWired(unittest.TestCase):
    """Confirms the monkeypatch actually took effect and the copied
    decide_market_actions produces a SELL order in a case where the
    baseline function would not have, given matching opponent supply -
    an end-to-end check one level up from should_sell_opponent_aware
    itself.

    setUp re-applies this module's own patch of base.decide_market_actions
    immediately before each test: both this candidate and
    opponent_aware_sell_gate_exact_yield.py monkeypatch the same shared
    `main.decide_market_actions` global at import time, so whichever
    candidate module a full `unittest discover` run happens to import
    last otherwise silently wins for every test in the suite, not just
    its own - this is test-isolation plumbing only, not a change to
    either candidate's behaviour."""

    def setUp(self):
        from experiments.candidates.opponent_aware_sell_gate import (
            _decide_market_actions_opponent_aware,
        )
        base.decide_market_actions = _decide_market_actions_opponent_aware

    def test_sells_a_product_the_baseline_would_have_held(self):
        # base.decide_market_actions is patched at import time (module
        # docstring) to the opponent-aware version - this test exercises
        # that patched function end-to-end, one level up from
        # should_sell_opponent_aware itself. The baseline (no-opponent)
        # case is already covered directly by
        # TestIdenticalToBaselineWhenOpponentUnitsIsZero, so this test only
        # needs to confirm the wiring: an opponent_pipeline with real
        # units for this product produces a SELL order in a shed/inventory
        # state where should_sell alone would have said no (see
        # TestOverrideFiresWhenDelayIsGenuinelyWorse for that same
        # inventory point).
        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"MELON": 10}, "inventories": [{}]}
        market_state = _market_state("MELON", 10100)
        self.assertFalse(base.should_sell("MELON", 10, market_state))

        actions = base.decide_market_actions(
            farm, private, market_state, day=5, opponent_pipeline={"MELON": 5},
        )
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "MELON"]
        self.assertTrue(sell_orders, "expected an opponent-aware SELL order")


if __name__ == "__main__":
    unittest.main()
