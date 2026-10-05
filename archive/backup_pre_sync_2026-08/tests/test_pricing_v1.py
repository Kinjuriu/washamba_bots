"""
Tests for pricing_v1.py (V1 forward price-path research model, RESEARCH ONLY).

Mirrors tests/test_pricing.py's style: check internal consistency (a sale
never raises price, the floor is respected, inventory never goes negative)
and, where possible, cross-check against the engine directly or against an
equivalent function already used by the live agent - the whole point of a
research module built "on top of" pricing.py is that it must never silently
diverge from the mechanics it's built on.

Run with:
    python -m unittest discover -s tests
"""

import unittest

from pricing import MARKET_PARAMS, PRICE_FLOOR, market_price

import pricing_v1 as v1

PLANTABLE_CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]


class TestCropsTableLoaded(unittest.TestCase):
    def test_every_plantable_crop_present(self):
        for crop in PLANTABLE_CROPS:
            self.assertIn(crop, v1.CROPS)

    def test_expected_fields_present(self):
        for crop in PLANTABLE_CROPS:
            info = v1.CROPS[crop]
            for field in ("seed", "first_yield_day", "max_yield_day", "interval", "max_yield", "ongoing"):
                self.assertIn(field, info)


class TestEstimateOwnHarvestUnits(unittest.TestCase):
    """WHEAT/CARROT/MELON are one-shot (window-based); TOMATO/STRAWBERRY are
    ongoing (interval-based). Expected values below are not hand-derived
    from the formula in isolation - they are the exact sequence read off a
    real running episode (WHEAT planted day 0, watered every day) in
    `notebooks/pricing_v1_validation.ipynb`, which is also how this
    module's first draft was caught getting two things wrong: it omitted
    the `+1` baseline `_new_plant` gives every one-shot crop at planting
    (kaggriculture.py:215-226), and it didn't account for an `hour == 0`
    reading only reflecting watering already done through the day before.
    """

    def test_one_shot_crop_starts_at_the_baseline_the_instant_its_planted(self):
        # WHEAT: yield_units=1 immediately at planting (_new_plant), before
        # any watered day inside its window has occurred yet.
        self.assertEqual(v1.estimate_own_harvest_units("WHEAT", 0, 0, 1), 1)
        self.assertEqual(v1.estimate_own_harvest_units("WHEAT", 0, 0, 2), 1)

    def test_one_shot_crop_accrues_one_per_watered_day_in_window(self):
        # WHEAT window is [2, 4] inclusive. Verified against a live episode:
        # day 1/2 -> 1 (baseline only), day 3 -> 2, day 4 -> 3, day 5 -> 4.
        self.assertEqual(v1.estimate_own_harvest_units("WHEAT", 0, 0, 3), 2)
        self.assertEqual(v1.estimate_own_harvest_units("WHEAT", 0, 0, 4), 3)
        self.assertEqual(v1.estimate_own_harvest_units("WHEAT", 0, 0, 5), 4)

    def test_one_shot_crop_caps_and_stops_growing_once_the_window_closes(self):
        # WHEAT's window closes after max_yield_day=4, so the window-derived
        # cap is baseline(1) + (4 - 2 + 1) = 4 - below max_yield=6, and
        # going further in time adds nothing more.
        self.assertEqual(v1.estimate_own_harvest_units("WHEAT", 0, 0, 5), 4)
        self.assertEqual(v1.estimate_own_harvest_units("WHEAT", 0, 0, 30), 4)

    def test_melons_window_start_differs_from_its_first_yield_day(self):
        # MELON: max_yield_day=12 -> window_start=(12+1)//2=6, but
        # first_yield_day=10 is a different, unrelated constant. Confirms
        # the module does NOT gate one-shot accrual on first_yield_day -
        # exactly the distinction the module's docstring calls out.
        info = v1.CROPS["MELON"]
        self.assertNotEqual((info["max_yield_day"] + 1) // 2, info["first_yield_day"])
        # By day 8 (before first_yield_day=10, but inside the window
        # starting at 6), yield should already be accruing.
        self.assertGreater(v1.estimate_own_harvest_units("MELON", 0, 0, 8), 0)

    def test_ongoing_crop_yields_nothing_before_first_yield_day(self):
        # TOMATO: first_yield_day=8.
        self.assertEqual(v1.estimate_own_harvest_units("TOMATO", 0, 0, 7), 0)

    def test_ongoing_crop_accrues_one_per_interval_from_first_yield_day(self):
        # TOMATO: interval=1, so every day from day 8 onward adds one,
        # capped at max_yield=4.
        self.assertEqual(v1.estimate_own_harvest_units("TOMATO", 0, 0, 8), 1)
        self.assertEqual(v1.estimate_own_harvest_units("TOMATO", 0, 0, 9), 2)
        self.assertEqual(v1.estimate_own_harvest_units("TOMATO", 0, 0, 11), 4)
        self.assertEqual(v1.estimate_own_harvest_units("TOMATO", 0, 0, 25), 4)  # capped

    def test_ongoing_crop_respects_its_own_interval_spacing(self):
        # STRAWBERRY: first_yield_day=10, interval=2 - ticks at 10, 12, 14,
        # not every day in between.
        self.assertEqual(v1.estimate_own_harvest_units("STRAWBERRY", 0, 0, 10), 1)
        self.assertEqual(v1.estimate_own_harvest_units("STRAWBERRY", 0, 0, 11), 1)
        self.assertEqual(v1.estimate_own_harvest_units("STRAWBERRY", 0, 0, 12), 2)

    def test_planted_day_offsets_everything(self):
        # Planting later should shift the whole schedule, not change it.
        early = v1.estimate_own_harvest_units("WHEAT", 0, 0, 4)
        late = v1.estimate_own_harvest_units("WHEAT", 10, 10, 14)
        self.assertEqual(early, late)

    def test_unknown_crop_returns_zero(self):
        self.assertEqual(v1.estimate_own_harvest_units("NOT_A_CROP", 0, 0, 10), 0)

    def test_never_negative(self):
        for crop in PLANTABLE_CROPS:
            for horizon in range(0, 5):
                self.assertGreaterEqual(
                    v1.estimate_own_harvest_units(crop, 0, 0, horizon), 0
                )


class TestEstimateOwnPipeline(unittest.TestCase):
    def test_sums_across_multiple_tiles_of_the_same_crop(self):
        tiles = [
            [{"kind": "PLANT", "crop": "WHEAT", "planted_day": 0}],
            [{"kind": "PLANT", "crop": "WHEAT", "planted_day": 0}],
        ]
        total = v1.estimate_own_pipeline(tiles, current_day=0, horizon_day=4)
        self.assertEqual(total["WHEAT"], 6)  # 3 + 3

    def test_ignores_non_plant_tiles(self):
        tiles = [[None, "LOCKED", {"kind": "WEED"}, {"kind": "PASTURE"}]]
        total = v1.estimate_own_pipeline(tiles, current_day=0, horizon_day=10)
        self.assertEqual(total, {})

    def test_groups_by_crop_separately(self):
        tiles = [[
            {"kind": "PLANT", "crop": "WHEAT", "planted_day": 0},
            {"kind": "PLANT", "crop": "MELON", "planted_day": 0},
        ]]
        total = v1.estimate_own_pipeline(tiles, current_day=0, horizon_day=12)
        self.assertIn("WHEAT", total)
        self.assertIn("MELON", total)

    def test_empty_or_none_tiles_returns_empty(self):
        self.assertEqual(v1.estimate_own_pipeline([], 0, 10), {})
        self.assertEqual(v1.estimate_own_pipeline(None, 0, 10), {})


class TestEstimateOpponentPipeline(unittest.TestCase):
    def test_counts_each_plant_tile_at_its_max_yield(self):
        tiles = [[{"kind": "PLANT", "crop": "WHEAT"}]]
        total = v1.estimate_opponent_pipeline(tiles)
        self.assertEqual(total["WHEAT"], v1.CROPS["WHEAT"]["max_yield"])

    def test_matches_main_pys_count_opponent_pipeline_semantics(self):
        # main.py's count_opponent_pipeline uses the same rule (each PLANT
        # tile counted at crop_info["max_yield"]) - cross-checked here so
        # this module's independent implementation can't silently diverge
        # from what the live agent actually computes on the same tiles.
        #
        # Deliberately does NOT call the live main.count_opponent_pipeline
        # here: several experiment candidates in this repo monkeypatch that
        # exact name at import time (opponent-aware sell gate, opponent
        # state v0), so which implementation is bound to it depends on
        # unittest's module import order when the whole suite runs together
        # - not something this cross-check should be sensitive to. Reproduces
        # the ORIGINAL rule directly from main.py's own CROPS table instead,
        # which is what main.count_opponent_pipeline's docstring guarantees
        # regardless of what any candidate does to the live binding.
        import main

        tiles = [[
            {"kind": "PLANT", "crop": "MELON"},
            {"kind": "PLANT", "crop": "MELON"},
            {"kind": "PLANT", "crop": "STRAWBERRY"},
        ]]
        expected = {
            "MELON": 2 * main.CROPS["MELON"]["max_yield"],
            "STRAWBERRY": main.CROPS["STRAWBERRY"]["max_yield"],
        }
        v1_result = v1.estimate_opponent_pipeline(tiles)
        self.assertEqual(expected, v1_result)

    def test_ignores_non_plant_tiles(self):
        tiles = [[None, "LOCKED", {"kind": "WEED"}]]
        self.assertEqual(v1.estimate_opponent_pipeline(tiles), {})


class TestPricePathConcurrent(unittest.TestCase):
    def test_both_sides_get_the_same_price_each_shared_step(self):
        result = v1.price_path_concurrent("MELON", 10000, 3, 3)
        self.assertEqual(result["our_prices"], result["opponent_prices"])

    def test_smaller_order_exhausts_first_larger_continues_alone(self):
        result = v1.price_path_concurrent("MELON", 10000, 5, 2)
        self.assertEqual(len(result["our_prices"]), 5)
        self.assertEqual(len(result["opponent_prices"]), 2)
        # The first 2 steps are shared (same price at each shared step).
        self.assertEqual(result["our_prices"][:2], result["opponent_prices"])

    def test_inventory_increases_once_per_committed_unit(self):
        # 2 units, both sides, both above the floor -> inventory should
        # rise by exactly 2 per shared step (one per committing side).
        result = v1.price_path_concurrent("WHEAT", 10000, 1, 1)
        self.assertEqual(result["ending_inventory"], 10002)

    def test_zero_quantities_is_a_no_op(self):
        result = v1.price_path_concurrent("MELON", 10000, 0, 0)
        self.assertEqual(result["our_prices"], [])
        self.assertEqual(result["opponent_prices"], [])
        self.assertEqual(result["ending_inventory"], 10000)

    def test_one_sided_order_matches_price_path_for_sale(self):
        from pricing import price_path_for_sale

        solo = price_path_for_sale("MELON", 10000, 5)
        concurrent = v1.price_path_concurrent("MELON", 10000, 5, 0)
        self.assertEqual(concurrent["our_prices"], solo["prices"])
        self.assertEqual(concurrent["ending_inventory"], solo["ending_inventory"])

    def test_sales_at_the_floor_do_not_grow_inventory(self):
        # Deep enough glut that price is already pinned at PRICE_FLOOR.
        deep_glut = MARKET_PARAMS["MELON"]["I0"] + 10_000
        result = v1.price_path_concurrent("MELON", deep_glut, 3, 3)
        self.assertEqual(result["ending_inventory"], deep_glut)
        self.assertTrue(all(p == PRICE_FLOOR for p in result["our_prices"]))


class TestExpectedRevenueForSellingN(unittest.TestCase):
    def test_matches_sum_of_price_path(self):
        from pricing import price_path_for_sale

        path = price_path_for_sale("WHEAT", 10000, 7)
        revenue = v1.expected_revenue_for_selling_n("WHEAT", 10000, 7)
        self.assertEqual(revenue, sum(path["prices"]))

    def test_zero_quantity_is_zero_revenue(self):
        self.assertEqual(v1.expected_revenue_for_selling_n("WHEAT", 10000, 0), 0)


class TestCompareImmediateVsDelayedSelling(unittest.TestCase):
    def test_returns_all_expected_keys(self):
        result = v1.compare_immediate_vs_delayed_selling(
            "MELON", 10020, 10, day=5, delay_turns=48
        )
        for key in (
            "revenue_now", "revenue_now_per_unit", "revenue_delayed",
            "revenue_delayed_per_unit", "inventory_at_delay",
            "delay_is_better", "advantage",
        ):
            self.assertIn(key, result)

    def test_waiting_out_a_glut_with_no_new_supply_can_improve_revenue(self):
        # A moderate glut, long enough delay for town demand alone to
        # meaningfully recover it, no further supply landing in between.
        result = v1.compare_immediate_vs_delayed_selling(
            "MELON", 10020, 10, day=5, delay_turns=120,
        )
        self.assertTrue(result["delay_is_better"])
        self.assertGreater(result["advantage"], 0)

    def test_advantage_is_the_difference_of_the_two_revenues(self):
        result = v1.compare_immediate_vs_delayed_selling(
            "WHEAT", 10000, 5, day=0, delay_turns=24,
        )
        self.assertEqual(
            result["advantage"], result["revenue_delayed"] - result["revenue_now"]
        )

    def test_zero_quantity_never_favours_delay(self):
        result = v1.compare_immediate_vs_delayed_selling(
            "WHEAT", 10000, 0, day=0, delay_turns=24,
        )
        self.assertEqual(result["revenue_now"], 0)
        self.assertEqual(result["revenue_delayed"], 0)
        self.assertFalse(result["delay_is_better"])


class TestInventoryPressure(unittest.TestCase):
    def test_zero_carried_is_zero_pressure(self):
        self.assertEqual(v1.inventory_pressure(0, 0, remaining_days=10, max_per_turn=15), 0.0)

    def test_pressure_reaches_one_when_carried_equals_capacity(self):
        # capacity = 15 * 10 = 150
        self.assertEqual(v1.inventory_pressure(150, 0, remaining_days=10, max_per_turn=15), 1.0)

    def test_pressure_exceeds_one_when_overcommitted(self):
        pressure = v1.inventory_pressure(300, 0, remaining_days=10, max_per_turn=15)
        self.assertGreater(pressure, 1.0)

    def test_pipeline_supply_adds_to_pressure(self):
        without_pipeline = v1.inventory_pressure(50, 0, remaining_days=10, max_per_turn=15)
        with_pipeline = v1.inventory_pressure(50, 50, remaining_days=10, max_per_turn=15)
        self.assertGreater(with_pipeline, without_pipeline)

    def test_remaining_days_of_zero_does_not_divide_by_zero(self):
        # max(1, ...) guard - should not raise.
        v1.inventory_pressure(10, 0, remaining_days=0, max_per_turn=15)


class TestSeasonUrgency(unittest.TestCase):
    def test_zero_at_day_zero(self):
        self.assertEqual(v1.season_urgency(0, season_days=30), 0.0)

    def test_reaches_one_on_the_last_day(self):
        self.assertEqual(v1.season_urgency(29, season_days=30), 1.0)

    def test_monotonically_non_decreasing(self):
        prev = -1.0
        for day in range(0, 30):
            urgency = v1.season_urgency(day, season_days=30)
            self.assertGreaterEqual(urgency, prev)
            prev = urgency

    def test_clamped_past_the_final_day(self):
        self.assertEqual(v1.season_urgency(100, season_days=30), 1.0)

    def test_never_negative_for_a_negative_day(self):
        self.assertEqual(v1.season_urgency(-5, season_days=30), 0.0)


class TestRecommendSellCadence(unittest.TestCase):
    def test_high_pressure_sells_regardless_of_price(self):
        # Deep glut so price is at/near the floor, but pressure forces a
        # sale anyway because the pile can't be cleared otherwise.
        result = v1.recommend_sell_cadence(
            "MELON",
            current_inventory=MARKET_PARAMS["MELON"]["I0"] + 10_000,
            shed_quantity=100,
            day=10,
            remaining_days=2,
            max_per_turn=15,
            min_acceptable_price=90,
        )
        self.assertEqual(result["reason"], "inventory_pressure")
        self.assertGreaterEqual(result["pressure"], 1.0)
        self.assertGreater(result["quantity"], 0)

    def test_low_pressure_defers_to_the_price_path(self):
        result = v1.recommend_sell_cadence(
            "MELON",
            current_inventory=10000,
            shed_quantity=5,
            day=1,
            remaining_days=28,
            max_per_turn=15,
            min_acceptable_price=90,
        )
        self.assertEqual(result["reason"], "price_path")

    def test_effective_min_price_never_drops_below_the_floor(self):
        result = v1.recommend_sell_cadence(
            "MELON",
            current_inventory=10000,
            shed_quantity=5,
            day=29,
            remaining_days=1,
            max_per_turn=15,
            min_acceptable_price=90,
            season_days=30,
        )
        self.assertGreaterEqual(result["effective_min_price"], PRICE_FLOOR)

    def test_effective_min_price_decreases_as_urgency_rises(self):
        early = v1.recommend_sell_cadence(
            "WHEAT", current_inventory=10000, shed_quantity=5, day=1,
            remaining_days=28, max_per_turn=15, min_acceptable_price=90, season_days=30,
        )
        late = v1.recommend_sell_cadence(
            "WHEAT", current_inventory=10000, shed_quantity=5, day=25,
            remaining_days=4, max_per_turn=15, min_acceptable_price=90, season_days=30,
        )
        self.assertLessEqual(late["effective_min_price"], early["effective_min_price"])


class TestForecast(unittest.TestCase):
    def test_returns_every_required_output_key(self):
        result = v1.forecast(
            "MELON", 10020, day=5, turns_ahead=48,
            our_pipeline_supply=10, opponent_pipeline_supply=5, sell_quantity=8,
        )
        for key in (
            "expected_future_inventory", "expected_future_price",
            "price_path_for_selling_n", "expected_revenue_for_selling_n",
            "spot_price", "spot_inventory",
        ):
            self.assertIn(key, result)

    def test_expected_future_price_is_a_valid_market_price(self):
        result = v1.forecast("WHEAT", 10000, day=0, turns_ahead=24)
        self.assertEqual(
            result["expected_future_price"],
            market_price("WHEAT", result["expected_future_inventory"]),
        )

    def test_price_path_length_matches_sell_quantity(self):
        result = v1.forecast("WHEAT", 10000, day=0, turns_ahead=0, sell_quantity=4)
        self.assertEqual(len(result["price_path_for_selling_n"]), 4)

    def test_zero_sell_quantity_gives_zero_revenue(self):
        result = v1.forecast("WHEAT", 10000, day=0, turns_ahead=24, sell_quantity=0)
        self.assertEqual(result["expected_revenue_for_selling_n"], 0)


class TestEstimateSellOrHoldDecision(unittest.TestCase):
    """experiments/forward_sell_policy_v0_report.md's core building block:
    a genuine sell-now-vs-hold-one-turn value comparison, composed from
    already-tested functions in this module (recommend_sell_quantity,
    compare_immediate_vs_delayed_selling, inventory_pressure,
    season_urgency) - these tests check the composition, not re-derive
    the underlying mechanics (those already have their own test classes
    above)."""

    def test_returns_all_expected_keys(self):
        result = v1.estimate_sell_or_hold_decision(
            "MELON", 10020, shed_quantity=10, day=5, remaining_days=20,
        )
        for key in (
            "quantity", "prefer_sell", "reason", "pressure", "urgency",
            "revenue_now", "revenue_delayed", "advantage",
            "opportunity_cost_of_holding",
        ):
            self.assertIn(key, result)

    def test_zero_shed_quantity_means_nothing_to_sell(self):
        result = v1.estimate_sell_or_hold_decision(
            "MELON", 10020, shed_quantity=0, day=5, remaining_days=20,
        )
        self.assertEqual(result["quantity"], 0)
        self.assertFalse(result["prefer_sell"])
        self.assertEqual(result["reason"], "nothing_to_sell")

    def test_tie_resolves_to_sell(self):
        # No town-demand tick can fire between a start_step and
        # start_step+1 that isn't itself a tick boundary - pick a
        # start_step where neither the default shop nor center interval
        # divides start_step+1, so revenue_now == revenue_delayed exactly
        # and the decision falls through to the tie-break.
        result = v1.estimate_sell_or_hold_decision(
            "WHEAT", 10000, shed_quantity=5, day=5, remaining_days=20,
            start_step=121,  # 122 % 4 != 0, 122 % 24 != 0
        )
        self.assertEqual(result["revenue_now"], result["revenue_delayed"])
        self.assertTrue(result["prefer_sell"])
        self.assertEqual(result["reason"], "sell_now_beats_hold")
        self.assertEqual(result["opportunity_cost_of_holding"], 0.0)

    def test_a_demand_tick_inside_the_hold_window_can_favour_holding(self):
        # start_step=123 -> start_step+1=124, 124 % 4 == 0: a shop-interval
        # tick fires inside the one-turn hold window, recovering price a
        # little with no new supply landing - a genuine (if small) reason
        # to prefer holding, not a tie-break artefact.
        result = v1.estimate_sell_or_hold_decision(
            "MELON", 10020, shed_quantity=10, day=5, remaining_days=20,
            start_step=123,
        )
        self.assertGreaterEqual(result["revenue_delayed"], result["revenue_now"])

    def test_inventory_pressure_forces_sell_regardless_of_forecast(self):
        # Structurally overcommitted: even selling flat-out every
        # remaining day at the cap wouldn't clear this position in time.
        # Mock the comparison to insist delay is better, and confirm the
        # pressure override still wins.
        from unittest import mock

        with mock.patch(
            "pricing_v1.compare_immediate_vs_delayed_selling",
            return_value={
                "revenue_now": 10, "revenue_delayed": 1000, "advantage": 990,
                "delay_is_better": True, "inventory_at_delay": 10000,
                "revenue_now_per_unit": 1, "revenue_delayed_per_unit": 100,
            },
        ):
            result = v1.estimate_sell_or_hold_decision(
                "MELON", 10020, shed_quantity=500, day=5, remaining_days=2,
                max_per_turn=15,
            )
        self.assertGreaterEqual(result["pressure"], 1.0)
        self.assertTrue(result["prefer_sell"])
        self.assertEqual(result["reason"], "inventory_pressure")

    def test_opportunity_cost_is_zero_when_selling_now_is_at_least_as_good(self):
        result = v1.estimate_sell_or_hold_decision(
            "WHEAT", 10000, shed_quantity=5, day=5, remaining_days=20,
            start_step=121,
        )
        self.assertFalse(result["reason"] == "hold_beats_sell_now")
        self.assertEqual(result["opportunity_cost_of_holding"], 0.0)

    def test_opportunity_cost_is_positive_when_holding_wins(self):
        result = v1.estimate_sell_or_hold_decision(
            "MELON", 10020, shed_quantity=10, day=5, remaining_days=20,
            start_step=123,
        )
        if result["reason"] == "hold_beats_sell_now":
            self.assertGreater(result["opportunity_cost_of_holding"], 0.0)

    def test_urgency_and_pressure_are_computed_not_hardcoded(self):
        early = v1.estimate_sell_or_hold_decision(
            "WHEAT", 10000, shed_quantity=5, day=0, remaining_days=29,
        )
        late = v1.estimate_sell_or_hold_decision(
            "WHEAT", 10000, shed_quantity=5, day=25, remaining_days=4,
        )
        self.assertLess(early["urgency"], late["urgency"])

    def test_quantity_never_exceeds_max_per_turn(self):
        result = v1.estimate_sell_or_hold_decision(
            "MELON", 10020, shed_quantity=500, day=5, remaining_days=20,
            max_per_turn=6,
        )
        self.assertLessEqual(result["quantity"], 6)

    def test_quantity_never_exceeds_shed_quantity_when_uncapped(self):
        result = v1.estimate_sell_or_hold_decision(
            "WHEAT", 10000, shed_quantity=3, day=5, remaining_days=20,
        )
        self.assertLessEqual(result["quantity"], 3)


class TestEstimateMultiDaySellOrHoldDecision(unittest.TestCase):
    """experiments/forward_sell_policy_v1_1_report.md's core building
    block: replaces v0's one-turn horizon with a genuine multi-day
    own-supply forecast. `quantity` is always a caller-supplied input
    here, never computed internally - these tests check the multi-day
    composition and the season/liquidation-aware horizon cap, not the
    underlying mechanics (already covered by TestCompareImmediateVsDelayedSelling
    and TestEstimateOwnPipeline above)."""

    def _melon_tile(self, planted_day):
        return {"kind": "PLANT", "crop": "MELON", "planted_day": planted_day}

    def test_zero_quantity_means_nothing_to_sell(self):
        result = v1.estimate_multi_day_sell_or_hold_decision(
            "MELON", 10020, quantity=0, day=5, remaining_days=20,
        )
        self.assertFalse(result["prefer_sell"])
        self.assertEqual(result["reason"], "nothing_to_sell")

    def test_returns_all_expected_keys(self):
        result = v1.estimate_multi_day_sell_or_hold_decision(
            "MELON", 10020, quantity=10, day=5, remaining_days=20,
        )
        for key in (
            "quantity", "prefer_sell", "reason", "revenue_now",
            "best_revenue_delayed", "best_future_day", "advantage",
            "opportunity_cost_of_holding", "per_day",
        ):
            self.assertIn(key, result)

    def test_quantity_in_equals_quantity_out(self):
        """The whole point of v1.1: this function must never change the
        quantity it was given - only decide whether to use it now."""
        result = v1.estimate_multi_day_sell_or_hold_decision(
            "MELON", 10020, quantity=13, day=5, remaining_days=20,
        )
        self.assertEqual(result["quantity"], 13)

    def test_per_day_covers_exactly_the_horizon(self):
        result = v1.estimate_multi_day_sell_or_hold_decision(
            "WHEAT", 10000, quantity=5, day=5, remaining_days=20,
            horizon_days=4,
        )
        self.assertEqual([d["future_day"] for d in result["per_day"]], [6, 7, 8, 9])

    def test_horizon_shrinks_to_remaining_days(self):
        result = v1.estimate_multi_day_sell_or_hold_decision(
            "WHEAT", 10000, quantity=5, day=27, remaining_days=2,
            horizon_days=4, liquidation_start_day=None,
        )
        self.assertEqual([d["future_day"] for d in result["per_day"]], [28, 29])

    def test_horizon_shrinks_to_the_day_before_liquidation(self):
        result = v1.estimate_multi_day_sell_or_hold_decision(
            "WHEAT", 10000, quantity=5, day=17, remaining_days=20,
            horizon_days=4, liquidation_start_day=19,
        )
        # day 17 -> only day 18 is a real, non-liquidating future day
        self.assertEqual([d["future_day"] for d in result["per_day"]], [18])

    def test_no_future_opportunity_on_the_last_pre_liquidation_day(self):
        result = v1.estimate_multi_day_sell_or_hold_decision(
            "WHEAT", 10000, quantity=5, day=18, remaining_days=20,
            horizon_days=4, liquidation_start_day=19,
        )
        self.assertEqual(result["per_day"], [])
        self.assertTrue(result["prefer_sell"])
        self.assertEqual(result["reason"], "no_future_opportunity_in_horizon")

    def test_our_own_growing_tile_is_priced_into_the_forecast(self):
        """A currently-growing MELON tile should make waiting look worse
        (more supply landing) than an otherwise-identical case with no
        tiles at all - this is the exact gap v0 left open (pipeline
        supply pinned at 0) and v1.1 exists to close."""
        tiles = [[self._melon_tile(planted_day=0)]]
        with_tile = v1.estimate_multi_day_sell_or_hold_decision(
            "MELON", 10020, quantity=10, day=8, remaining_days=20, tiles=tiles,
        )
        without_tile = v1.estimate_multi_day_sell_or_hold_decision(
            "MELON", 10020, quantity=10, day=8, remaining_days=20, tiles=None,
        )
        self.assertLessEqual(with_tile["best_revenue_delayed"], without_tile["best_revenue_delayed"])
        self.assertTrue(any(d["our_pipeline_supply"] > 0 for d in with_tile["per_day"]))
        self.assertTrue(all(d["our_pipeline_supply"] == 0 for d in without_tile["per_day"]))

    def test_best_future_day_is_the_max_revenue_day(self):
        result = v1.estimate_multi_day_sell_or_hold_decision(
            "MELON", 10020, quantity=10, day=5, remaining_days=20,
        )
        best = max(result["per_day"], key=lambda d: d["revenue_delayed"])
        self.assertEqual(result["best_future_day"], best["future_day"])
        self.assertEqual(result["best_revenue_delayed"], best["revenue_delayed"])

    def test_ties_resolve_to_sell(self):
        # A deep glut with no town-demand ticks likely to move price much
        # relative to a small quantity is not guaranteed to tie exactly,
        # so this directly forces the comparable case instead: mock
        # compare_immediate_vs_delayed_selling to report identical
        # revenue for every offset and confirm the decision still sells.
        from unittest import mock

        with mock.patch(
            "pricing_v1.compare_immediate_vs_delayed_selling",
            return_value={
                "revenue_now": 100, "revenue_delayed": 100, "advantage": 0,
                "delay_is_better": False, "inventory_at_delay": 10000,
                "revenue_now_per_unit": 10, "revenue_delayed_per_unit": 10,
            },
        ), mock.patch("pricing_v1.expected_revenue_for_selling_n", return_value=100):
            result = v1.estimate_multi_day_sell_or_hold_decision(
                "WHEAT", 10000, quantity=10, day=5, remaining_days=20,
            )
        self.assertTrue(result["prefer_sell"])
        self.assertEqual(result["reason"], "sell_now_beats_every_future_day")

    def test_no_opportunity_cost_when_holding_is_the_right_call(self):
        # opportunity_cost_of_holding measures what holding would cost IF
        # selling now were actually better - when a future day genuinely
        # wins, holding costs nothing (it was the correct choice), so this
        # must be exactly 0, not the (unrelated) size of the gain from
        # holding.
        from unittest import mock

        with mock.patch(
            "pricing_v1.compare_immediate_vs_delayed_selling",
            return_value={
                "revenue_now": 50, "revenue_delayed": 150, "advantage": 100,
                "delay_is_better": True, "inventory_at_delay": 10000,
                "revenue_now_per_unit": 5, "revenue_delayed_per_unit": 15,
            },
        ), mock.patch("pricing_v1.expected_revenue_for_selling_n", return_value=50):
            result = v1.estimate_multi_day_sell_or_hold_decision(
                "WHEAT", 10000, quantity=10, day=5, remaining_days=20,
            )
        self.assertFalse(result["prefer_sell"])
        self.assertEqual(result["opportunity_cost_of_holding"], 0.0)

    def test_opportunity_cost_is_positive_when_selling_now_wins(self):
        from unittest import mock

        with mock.patch(
            "pricing_v1.compare_immediate_vs_delayed_selling",
            return_value={
                "revenue_now": 150, "revenue_delayed": 50, "advantage": -100,
                "delay_is_better": False, "inventory_at_delay": 10000,
                "revenue_now_per_unit": 15, "revenue_delayed_per_unit": 5,
            },
        ), mock.patch("pricing_v1.expected_revenue_for_selling_n", return_value=150):
            result = v1.estimate_multi_day_sell_or_hold_decision(
                "WHEAT", 10000, quantity=10, day=5, remaining_days=20,
            )
        self.assertTrue(result["prefer_sell"])
        self.assertEqual(result["opportunity_cost_of_holding"], 100)


if __name__ == "__main__":
    unittest.main()
