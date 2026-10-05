"""
Regression tests for
experiments/candidates/opponent_aware_sell_gate_exact_yield.py.

Mirrors tests/test_opponent_aware_sell_gate.py's structure (the previous
candidate's isolation properties), plus one test category that module
didn't need: proving the count_opponent_pipeline wrapper leaves planting
byte-identical to the unpatched baseline, since this candidate's whole
design hinges on that being true - see the module docstring's "how the
exact-yield value reaches the sell gate without touching planting".

Run with:
    python -m unittest tests.test_opponent_aware_sell_gate_exact_yield -v
"""
import unittest
from unittest import mock

import main as base
import pricing_v1
from experiments.candidates.opponent_aware_sell_gate_exact_yield import (
    OPPONENT_AWARE_HORIZON_TURNS,
    exact_opponent_standing_yield,
    should_sell_opponent_aware_exact_yield,
    _original_count_opponent_pipeline,
)


def _market_state(product, inventory, params=None):
    price = pricing_v1.market_price(product, inventory, params)
    return {"prices": {product: price}, "inventory": {product: inventory}}


def _obs_with_opponent_tiles(tiles_row, player=0):
    """A minimal 2-farm obs, player 0's perspective, with the opponent's
    (index 1) tiles set to `tiles_row` - a single row is enough since
    exact_opponent_standing_yield/count_opponent_pipeline both iterate
    every row uniformly."""
    empty_farm = {"tiles": [[None]]}
    opponent_farm = {"tiles": [tiles_row]}
    farms = [empty_farm, opponent_farm] if player == 0 else [opponent_farm, empty_farm]
    return {"player": player, "farms": farms}


class TestExactYieldDefinition(unittest.TestCase):
    """exact_opponent_standing_yield sums the real yield_units field, not
    a flat max_yield ceiling - the whole point of this experiment."""

    def test_sums_real_yield_units_not_max_yield(self):
        tile = {"kind": "PLANT", "crop": "MELON", "yield_units": 2}
        obs = _obs_with_opponent_tiles([tile])
        result = exact_opponent_standing_yield(obs)
        self.assertEqual(result, {"MELON": 2})
        # MELON's max_yield is 6 - a freshly-planted, barely-accrued tile
        # must not read as 6.
        self.assertNotEqual(result["MELON"], 6)

    def test_freshly_planted_tile_with_zero_yield_reads_zero(self):
        # The dict entry is present at 0 rather than omitted - every
        # consumer reads it via .get(product, 0), so this is behaviourally
        # equivalent to "absent"; asserting the actual value, not presence.
        tile = {"kind": "PLANT", "crop": "STRAWBERRY", "yield_units": 0}
        obs = _obs_with_opponent_tiles([tile])
        self.assertEqual(exact_opponent_standing_yield(obs).get("STRAWBERRY", 0), 0)

    def test_sums_across_multiple_tiles_same_crop(self):
        tiles = [
            {"kind": "PLANT", "crop": "WHEAT", "yield_units": 3},
            {"kind": "PLANT", "crop": "WHEAT", "yield_units": 1},
            None,
        ]
        obs = _obs_with_opponent_tiles(tiles)
        self.assertEqual(exact_opponent_standing_yield(obs), {"WHEAT": 4})

    def test_no_opponent_farm_returns_empty(self):
        self.assertEqual(exact_opponent_standing_yield({"player": 0, "farms": [{}]}), {})


class TestPlantingIsUntouched(unittest.TestCase):
    """The count_opponent_pipeline wrapper must return exactly what the
    original, unpatched function would - proving state["opponent_pipeline"]
    (and therefore both choose_crop call sites) never sees the exact-yield
    representation.

    setUp re-applies this module's own patch of base.count_opponent_pipeline
    before each test - a later candidate (experiments/candidates/
    opponent_state_v0.py) also patches that same shared `main` global, so a
    full `unittest discover` run needs this pinned rather than trusting
    whatever import order left behind (same pattern as this repo's other
    cross-candidate wiring tests)."""

    def setUp(self):
        import experiments.candidates.opponent_aware_sell_gate_exact_yield as exact_yield_candidate

        base.count_opponent_pipeline = exact_yield_candidate._count_opponent_pipeline_and_cache_exact_yield

    def test_wrapped_return_value_matches_unpatched_function(self):
        tiles = [
            {"kind": "PLANT", "crop": "MELON", "yield_units": 1},
            {"kind": "PLANT", "crop": "MELON", "yield_units": 1},
        ]
        obs = _obs_with_opponent_tiles(tiles)
        # base.count_opponent_pipeline is now the wrapper (patched at
        # import time); compare its output against the stashed original.
        wrapped_result = base.count_opponent_pipeline(obs)
        original_result = _original_count_opponent_pipeline(obs)
        self.assertEqual(wrapped_result, original_result)
        # And per the OLD semantics, two MELON tiles read as 2*max_yield
        # regardless of accrued yield_units=1 each - the crude ceiling
        # this experiment is deliberately NOT feeding to planting.
        self.assertEqual(wrapped_result, {"MELON": 12})

    def test_wrapper_still_caches_exact_yield_as_a_side_effect(self):
        import experiments.candidates.opponent_aware_sell_gate_exact_yield as candidate

        tiles = [{"kind": "PLANT", "crop": "CARROT", "yield_units": 2}]
        obs = _obs_with_opponent_tiles(tiles)
        base.count_opponent_pipeline(obs)
        self.assertEqual(candidate._last_exact_opponent_yield, {"CARROT": 2})


class TestIdenticalToBaselineWhenOpponentUnitsIsZero(unittest.TestCase):
    def test_matches_baseline_true_case(self):
        market_state = _market_state("MELON", 10000)
        self.assertTrue(base.should_sell("MELON", 10, market_state))
        self.assertEqual(
            should_sell_opponent_aware_exact_yield("MELON", 10, market_state, 0, day=5),
            base.should_sell("MELON", 10, market_state),
        )

    def test_matches_baseline_false_case(self):
        market_state = _market_state("MELON", 10200)
        self.assertFalse(base.should_sell("MELON", 10, market_state))
        self.assertEqual(
            should_sell_opponent_aware_exact_yield("MELON", 10, market_state, 0, day=5),
            base.should_sell("MELON", 10, market_state),
        )


class TestNeverSuppressesAnExistingSell(unittest.TestCase):
    def test_stays_true_regardless_of_opponent_units(self):
        market_state = _market_state("WHEAT", 10000)
        self.assertTrue(base.should_sell("WHEAT", 10, market_state))
        for opponent_units in (0, 1, 50, 500):
            self.assertTrue(
                should_sell_opponent_aware_exact_yield("WHEAT", 10, market_state, opponent_units, day=5)
            )


class TestOverrideFiresWhenDelayIsGenuinelyWorse(unittest.TestCase):
    def test_fires_and_agrees_with_compare_immediate_vs_delayed_selling(self):
        inventory = 10100
        market_state = _market_state("MELON", inventory)
        self.assertFalse(base.should_sell("MELON", 10, market_state))

        opponent_units = 5
        result = should_sell_opponent_aware_exact_yield(
            "MELON", 10, market_state, opponent_units, day=5,
        )
        comparison = pricing_v1.compare_immediate_vs_delayed_selling(
            "MELON", inventory, 10, day=5, delay_turns=OPPONENT_AWARE_HORIZON_TURNS,
            our_pipeline_supply=0, opponent_pipeline_supply=opponent_units,
        )
        self.assertTrue(result)
        self.assertEqual(result, not comparison["delay_is_better"])


class TestOverrideDoesNotFireOnEveryPositiveOpponentSupply(unittest.TestCase):
    def test_defers_to_the_comparison_when_it_says_wait(self):
        market_state = _market_state("MELON", 10200)
        self.assertFalse(base.should_sell("MELON", 10, market_state))

        with mock.patch(
            "experiments.candidates.opponent_aware_sell_gate_exact_yield.pricing_v1"
            ".compare_immediate_vs_delayed_selling",
            return_value={
                "delay_is_better": True, "revenue_now": 10, "revenue_delayed": 20,
                "advantage": 10, "revenue_delayed_per_unit": 2.0,
            },
        ):
            result = should_sell_opponent_aware_exact_yield("MELON", 10, market_state, 3, day=5)
        self.assertFalse(result)


class TestActivationLogging(unittest.TestCase):
    def test_logs_a_record_when_signal_available_and_evaluated(self):
        import experiments.candidates.opponent_aware_sell_gate_exact_yield as candidate

        candidate.ACTIVATION_LOG.clear()
        market_state = _market_state("MELON", 10100)
        should_sell_opponent_aware_exact_yield(
            "MELON", 10, market_state, 5, day=5, log=True,
        )
        self.assertEqual(len(candidate.ACTIVATION_LOG), 1)
        record = candidate.ACTIVATION_LOG[0]
        self.assertEqual(record["product"], "MELON")
        self.assertEqual(record["opponent_units"], 5)
        self.assertTrue(record["signal_available"])

    def test_logs_signal_unavailable_when_opponent_units_zero(self):
        import experiments.candidates.opponent_aware_sell_gate_exact_yield as candidate

        candidate.ACTIVATION_LOG.clear()
        market_state = _market_state("MELON", 10200)
        should_sell_opponent_aware_exact_yield(
            "MELON", 10, market_state, 0, day=5, log=True,
        )
        self.assertEqual(len(candidate.ACTIVATION_LOG), 1)
        self.assertFalse(candidate.ACTIVATION_LOG[0]["signal_available"])
        self.assertFalse(candidate.ACTIVATION_LOG[0]["fired"])

    def test_does_not_log_when_baseline_already_says_sell(self):
        import experiments.candidates.opponent_aware_sell_gate_exact_yield as candidate

        candidate.ACTIVATION_LOG.clear()
        market_state = _market_state("MELON", 10000)
        should_sell_opponent_aware_exact_yield(
            "MELON", 10, market_state, 5, day=5, log=True,
        )
        self.assertEqual(len(candidate.ACTIVATION_LOG), 0)


class TestDecideMarketActionsExactYieldIsWired(unittest.TestCase):
    """setUp re-applies this module's patch of base.decide_market_actions
    immediately before each test - see the matching note in
    tests/test_opponent_aware_sell_gate.py's TestDecideMarketActionsOpponentAwareIsWired
    for why: two candidates patch the same shared `main` global, so a
    full `unittest discover` run needs each wiring test to pin its own
    candidate's patch rather than trust whatever import order left
    behind."""

    def setUp(self):
        import experiments.candidates.opponent_aware_sell_gate_exact_yield as candidate

        base.decide_market_actions = candidate._decide_market_actions_opponent_aware_exact_yield

    def test_sells_a_product_the_baseline_would_have_held(self):
        import experiments.candidates.opponent_aware_sell_gate_exact_yield as candidate

        candidate._last_exact_opponent_yield = {"MELON": 5}
        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"MELON": 10}, "inventories": [{}]}
        market_state = _market_state("MELON", 10100)
        self.assertFalse(base.should_sell("MELON", 10, market_state))

        actions = base.decide_market_actions(
            farm, private, market_state, day=5, opponent_pipeline={"MELON": 999},
        )
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "MELON"]
        self.assertTrue(sell_orders, "expected an exact-yield-aware SELL order")

    def test_no_sell_when_exact_yield_cache_is_zero_even_if_old_pipeline_nonzero(self):
        """Proves the sell gate reads the exact-yield cache, not the
        opponent_pipeline parameter - the parameter here is deliberately
        set to a large nonzero value (what the OLD signal would have
        supplied) while the exact-yield cache is empty, and the override
        must not fire."""
        import experiments.candidates.opponent_aware_sell_gate_exact_yield as candidate

        candidate._last_exact_opponent_yield = {}
        farm = {"money": 3000, "tiles": [[None]], "farmer": [0, 0], "hands": []}
        private = {"shed": {"MELON": 10}, "inventories": [{}]}
        market_state = _market_state("MELON", 10100)

        actions = base.decide_market_actions(
            farm, private, market_state, day=5, opponent_pipeline={"MELON": 999},
        )
        sell_orders = [a for a in actions if a and a[0] == "SELL" and a[1] == "MELON"]
        self.assertFalse(sell_orders, "must not fire when the exact-yield signal is unavailable")


if __name__ == "__main__":
    unittest.main()
