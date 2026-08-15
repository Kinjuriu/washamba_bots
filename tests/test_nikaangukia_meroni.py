"""
Small, focused unit tests for the nikaangukia_meroni_v0 baseline agent.

These don't try to simulate a full game - they just check that each
building block behaves sensibly on its own, and that the top-level
agent never crashes on weird input.

Run with:
    python -m unittest discover -s tests
"""

import unittest

from main import (
    MAX_SELL_PER_TURN,
    choose_crop,
    choose_farmer_action,
    decide_market_actions,
    has_plantable_seed,
    is_harvestable,
    nikaangukia_meroni,
    should_sell,
    step_toward,
)


class TestStepToward(unittest.TestCase):
    def test_moves_east_when_target_is_to_the_right(self):
        self.assertEqual(step_toward(0, 0, 5, 0), "EAST")

    def test_moves_west_when_target_is_to_the_left(self):
        self.assertEqual(step_toward(5, 0, 0, 0), "WEST")

    def test_moves_south_when_target_is_below(self):
        # x already matches, so vertical movement kicks in.
        self.assertEqual(step_toward(2, 0, 2, 3), "SOUTH")

    def test_moves_north_when_target_is_above(self):
        self.assertEqual(step_toward(2, 3, 2, 0), "NORTH")

    def test_returns_none_when_already_at_target(self):
        self.assertIsNone(step_toward(4, 4, 4, 4))

    def test_prioritises_horizontal_movement_first(self):
        # When both x and y differ, we move horizontally before vertically.
        self.assertEqual(step_toward(0, 0, 3, 3), "EAST")


class TestChooseCrop(unittest.TestCase):
    def _market(self, prices, inventory):
        return {"prices": prices, "inventory": inventory}

    def test_avoids_oversupplied_high_price_crop(self):
        # Strawberries look tempting on price alone, but the market is
        # already flooded with them - a cheaper, undersupplied crop
        # should win instead.
        farm = {"money": 1000}
        market_state = self._market(
            prices={"STRAWBERRY": 400, "WHEAT": 30},
            inventory={"STRAWBERRY": 200, "WHEAT": 0},
        )
        private = {"seeds": {}}

        chosen = choose_crop(farm, market_state, private, day=0)
        self.assertEqual(chosen, "WHEAT")

    def test_returns_none_when_nothing_is_affordable_or_held(self):
        farm = {"money": 0}
        market_state = self._market(prices={}, inventory={})
        private = {"seeds": {}}

        self.assertIsNone(choose_crop(farm, market_state, private, day=0))

    def test_can_choose_a_crop_we_already_hold_seeds_for_even_if_broke(self):
        farm = {"money": 0}
        market_state = self._market(prices={"WHEAT": 20}, inventory={"WHEAT": 0})
        private = {"seeds": {"WHEAT": 2}}

        self.assertEqual(choose_crop(farm, market_state, private, day=0), "WHEAT")

    def test_skips_a_crop_that_cannot_reach_first_yield_before_season_end(self):
        # WHEAT's first_yield_day is 2. Diagnosed from a real lost game: on
        # day 28 there's only 1 day left (season ends at day 29), so a WHEAT
        # planted now can never be harvested - it should be skipped even
        # though we already hold a seed for it, rather than wasting the plant.
        farm = {"money": 0}
        market_state = self._market(prices={"WHEAT": 20}, inventory={"WHEAT": 0})
        private = {"seeds": {"WHEAT": 2}}

        self.assertIsNone(choose_crop(farm, market_state, private, day=28))

    def test_still_chooses_a_crop_with_exactly_enough_time_left(self):
        # Same crop, one day earlier: remaining_days == first_yield_day, so
        # it can just barely still be harvested before season end.
        farm = {"money": 0}
        market_state = self._market(prices={"WHEAT": 20}, inventory={"WHEAT": 0})
        private = {"seeds": {"WHEAT": 2}}

        self.assertEqual(choose_crop(farm, market_state, private, day=27), "WHEAT")


class TestHasPlantableSeed(unittest.TestCase):
    # Backs the "any" fallback target in find_nearest_target(): a farmer
    # shouldn't wander toward an empty tile on the strength of a seed that
    # choose_crop() would refuse to plant anyway once it got there.

    def test_true_when_a_held_seed_can_still_mature(self):
        # WHEAT's first_yield_day is 2; day=27 leaves 2 remaining days.
        self.assertTrue(has_plantable_seed({"WHEAT": 1}, day=27))

    def test_false_when_every_held_seed_is_too_late_to_mature(self):
        # Same seed, one day later: only 1 remaining day for a 2-day crop.
        self.assertFalse(has_plantable_seed({"WHEAT": 1}, day=28))

    def test_false_when_holding_no_seeds_at_all(self):
        self.assertFalse(has_plantable_seed({}, day=0))

    def test_ignores_zero_count_entries(self):
        self.assertFalse(has_plantable_seed({"WHEAT": 0, "MELON": 0}, day=0))


class TestShouldSell(unittest.TestCase):
    def test_sells_when_price_meets_threshold(self):
        market_state = {"prices": {"MELON": 250}}
        self.assertTrue(should_sell("MELON", 3, market_state))

    def test_holds_when_price_is_below_threshold(self):
        market_state = {"prices": {"MELON": 50}}
        self.assertFalse(should_sell("MELON", 3, market_state))

    def test_never_sells_zero_quantity(self):
        market_state = {"prices": {"MELON": 999}}
        self.assertFalse(should_sell("MELON", 0, market_state))

    def test_unknown_product_uses_default_threshold(self):
        market_state = {"prices": {"MYSTERY_CROP": 100}}
        self.assertTrue(should_sell("MYSTERY_CROP", 1, market_state))
        market_state = {"prices": {"MYSTERY_CROP": 10}}
        self.assertFalse(should_sell("MYSTERY_CROP", 1, market_state))


class TestDecideMarketActions(unittest.TestCase):
    def _market(self, prices, inventory=None):
        return {"prices": prices, "inventory": inventory or {}}

    def test_caps_large_premium_good_sell_to_avoid_crashing_price(self):
        private = {"shed": {"STRAWBERRY": 40}, "seeds": {}}
        market_state = self._market(prices={"STRAWBERRY": 120})

        actions = decide_market_actions({"money": 0}, private, market_state, day=0)

        self.assertIn(["SELL", "STRAWBERRY", MAX_SELL_PER_TURN["STRAWBERRY"]], actions)

    def test_caps_large_melon_sell_to_avoid_crashing_price(self):
        private = {"shed": {"MELON": 50}, "seeds": {}}
        market_state = self._market(prices={"MELON": 250})

        actions = decide_market_actions({"money": 0}, private, market_state, day=0)

        self.assertIn(["SELL", "MELON", MAX_SELL_PER_TURN["MELON"]], actions)

    def test_does_not_cap_a_premium_good_holding_below_the_cap(self):
        private = {"shed": {"STRAWBERRY": 3}, "seeds": {}}
        market_state = self._market(prices={"STRAWBERRY": 120})

        actions = decide_market_actions({"money": 0}, private, market_state, day=0)

        self.assertIn(["SELL", "STRAWBERRY", 3], actions)

    def test_does_not_cap_a_non_premium_good(self):
        private = {"shed": {"WHEAT": 500}, "seeds": {}}
        market_state = self._market(prices={"WHEAT": 25})

        actions = decide_market_actions({"money": 0}, private, market_state, day=0)

        self.assertIn(["SELL", "WHEAT", 500], actions)

    def test_holds_instead_of_selling_below_threshold(self):
        private = {"shed": {"MELON": 50}, "seeds": {}}
        market_state = self._market(prices={"MELON": 10})

        actions = decide_market_actions({"money": 0}, private, market_state, day=0)

        self.assertEqual(actions, [])

    def test_force_sells_below_threshold_when_shed_is_nearly_full(self):
        # 95 items >= SHED_FORCE_SELL_THRESHOLD (90): anything not already
        # selling would be silently discarded once the shed hits its 100 cap,
        # so it should be sold anyway even though the price is below the
        # normal MELON threshold - still capped per MAX_SELL_PER_TURN so the
        # forced dump doesn't crash the price either.
        private = {"shed": {"MELON": 95}, "seeds": {}}
        market_state = self._market(prices={"MELON": 10})

        actions = decide_market_actions({"money": 0}, private, market_state, day=0)

        self.assertIn(["SELL", "MELON", MAX_SELL_PER_TURN["MELON"]], actions)

    def test_does_not_double_sell_a_product_already_selling_above_threshold(self):
        # WHEAT already clears its threshold and gets sold in the normal
        # pass - the near-full-shed pass should not add a second, duplicate
        # SELL order for the same product.
        private = {"shed": {"WHEAT": 95}, "seeds": {}}
        market_state = self._market(prices={"WHEAT": 25})

        actions = decide_market_actions({"money": 0}, private, market_state, day=0)

        self.assertEqual(actions.count(["SELL", "WHEAT", 95]), 1)


class TestWeedReclamation(unittest.TestCase):
    def _farm(self, tiles, farmer):
        return {
            "money": 100,
            "tiles": tiles,
            "farmer": list(farmer),
            "hands": [],
            "unlocked_quadrants": ["NW"],
            "hires_today": 0,
        }

    def _state(self, tiles, farmer, board_size, seeds=None):
        return {
            "farm": self._farm(tiles, farmer),
            "private": {"shed": {}, "seeds": seeds or {}},
            "market_state": {"prices": {}, "inventory": {}},
            "board_size": board_size,
            "day": 5,
        }

    def test_digs_a_weed_under_its_feet(self):
        # A dead tile sitting under the farmer should be reclaimed for free
        # instead of being left as permanently unusable land.
        state = self._state(tiles=[[{"kind": "WEED"}]], farmer=(0, 0), board_size=1)
        self.assertEqual(choose_farmer_action(state), ["DIG"])

    def test_walks_toward_a_weed_when_nothing_more_urgent(self):
        # Standing on empty ground with no seed to plant and nothing else
        # urgent - go reclaim the nearby dead tile rather than PASS.
        tiles = [[None, {"kind": "WEED"}]]
        state = self._state(tiles=tiles, farmer=(0, 0), board_size=1)
        self.assertEqual(choose_farmer_action(state), ["EAST"])

    def test_watering_an_at_risk_crop_still_beats_digging_a_weed(self):
        # Preventing a new weed is worth more than reclaiming an old one -
        # the urgent watering target should win.
        tiles = [
            [
                {"kind": "WEED"},
                {
                    "kind": "PLANT",
                    "crop": "WHEAT",
                    "planted_day": 3,
                    "watered_today": False,
                    "consecutive_unwatered": 1,
                    "yield_units": 0,
                },
            ]
        ]
        state = self._state(tiles=tiles, farmer=(0, 0), board_size=1)
        self.assertEqual(choose_farmer_action(state), ["EAST"])


class TestHarvestReadiness(unittest.TestCase):
    def _farm(self, tiles, farmer):
        return {
            "money": 100,
            "tiles": tiles,
            "farmer": list(farmer),
            "hands": [],
            "unlocked_quadrants": ["NW"],
            "hires_today": 0,
        }

    def _state(self, tiles, farmer, day):
        return {
            "farm": self._farm(tiles, farmer),
            "private": {"shed": {}, "seeds": {}},
            "market_state": {"prices": {}, "inventory": {}},
            "board_size": 1,
            "day": day,
        }

    def test_freshly_planted_crop_is_not_harvestable(self):
        # A non-ongoing crop (WHEAT) starts with yield_units=1 the instant
        # it's planted - that's a payout placeholder, not a "ready" signal.
        # The environment also gates HARVEST on first_yield_day, so a
        # same-day planting must not read as harvestable.
        tile = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 3,
            "watered_today": False,
            "consecutive_unwatered": 1,
            "yield_units": 1,
        }
        self.assertFalse(is_harvestable(tile, day=3))

    def test_becomes_harvestable_once_first_yield_day_arrives(self):
        # WHEAT's first_yield_day is 2.
        tile = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 3,
            "watered_today": True,
            "consecutive_unwatered": 0,
            "yield_units": 1,
        }
        self.assertFalse(is_harvestable(tile, day=4))
        self.assertTrue(is_harvestable(tile, day=5))

    def test_farmer_waters_a_freshly_planted_crop_instead_of_trying_to_harvest_it(self):
        # This is the actual failure mode: without the first_yield_day gate,
        # the farmer would repeatedly issue a HARVEST that silently no-ops,
        # never watering the crop, until it dies two days later.
        tiles = [[{
            "kind": "PLANT",
            "crop": "WHEAT",
            "planted_day": 3,
            "watered_today": False,
            "consecutive_unwatered": 1,
            "yield_units": 1,
        }]]
        state = self._state(tiles=tiles, farmer=(0, 0), day=3)
        self.assertEqual(choose_farmer_action(state), ["WATER"])


class TestSafePassBehaviour(unittest.TestCase):
    def _empty_farm(self):
        return {
            "money": 0,
            "tiles": [[None]],
            "farmer": [0, 0],
            "hands": [],
            "unlocked_quadrants": ["NW"],
            "hires_today": 0,
        }

    def test_passes_when_nothing_useful_and_no_seeds(self):
        obs = {
            "player": 0,
            "day": 0,
            "hour": 0,
            "farms": [self._empty_farm()],
            "market": {"prices": {}, "inventory": {}},
            "town": {"unlocked_shops": []},
            "private": {"shed": {}, "seeds": {}, "inventories": [{}]},
        }
        result = nikaangukia_meroni(obs)
        self.assertEqual(result["farmer"], ["PASS"])
        self.assertEqual(result["hands"], [])
        self.assertEqual(result["market"], [])

    def test_never_crashes_on_completely_empty_observation(self):
        result = nikaangukia_meroni({})
        self.assertEqual(result, {"farmer": ["PASS"], "hands": [], "market": []})

    def test_never_crashes_on_none_observation(self):
        result = nikaangukia_meroni(None)
        self.assertEqual(result, {"farmer": ["PASS"], "hands": [], "market": []})


class TestPartialObservationHandling(unittest.TestCase):
    def test_missing_private_state_falls_back_safely(self):
        obs = {
            "player": 0,
            "farms": [
                {
                    "money": 100,
                    "tiles": [[None]],
                    "farmer": [0, 0],
                    "hands": [],
                    "unlocked_quadrants": ["NW"],
                    "hires_today": 0,
                }
            ],
            "market": {"prices": {}, "inventory": {}},
            # "private" key intentionally missing entirely.
        }
        result = nikaangukia_meroni(obs)
        self.assertIn("farmer", result)
        self.assertIn("hands", result)
        self.assertIn("market", result)

    def test_player_index_out_of_range_falls_back_to_pass(self):
        obs = {
            "player": 5,  # no farm at this index
            "farms": [
                {
                    "money": 100,
                    "tiles": [[None]],
                    "farmer": [0, 0],
                    "hands": [],
                    "unlocked_quadrants": ["NW"],
                    "hires_today": 0,
                }
            ],
            "market": {"prices": {}, "inventory": {}},
            "private": {"shed": {}, "seeds": {}, "inventories": [{}]},
        }
        result = nikaangukia_meroni(obs)
        self.assertEqual(result, {"farmer": ["PASS"], "hands": [], "market": []})

    def test_farmer_standing_on_ripe_crop_harvests(self):
        obs = {
            "player": 0,
            "day": 5,
            "farms": [
                {
                    "money": 100,
                    "tiles": [
                        [
                            {
                                "kind": "PLANT",
                                "crop": "WHEAT",
                                "planted_day": 1,
                                "watered_today": True,
                                "consecutive_unwatered": 0,
                                "yield_units": 3,
                            }
                        ]
                    ],
                    "farmer": [0, 0],
                    "hands": [],
                    "unlocked_quadrants": ["NW"],
                    "hires_today": 0,
                }
            ],
            "market": {"prices": {}, "inventory": {}},
            "private": {"shed": {}, "seeds": {}, "inventories": [{}]},
        }
        result = nikaangukia_meroni(obs)
        self.assertEqual(result["farmer"], ["HARVEST"])


if __name__ == "__main__":
    unittest.main()
