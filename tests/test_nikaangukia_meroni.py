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
    choose_crop,
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

        chosen = choose_crop(farm, market_state, private)
        self.assertEqual(chosen, "WHEAT")

    def test_returns_none_when_nothing_is_affordable_or_held(self):
        farm = {"money": 0}
        market_state = self._market(prices={}, inventory={})
        private = {"seeds": {}}

        self.assertIsNone(choose_crop(farm, market_state, private))

    def test_can_choose_a_crop_we_already_hold_seeds_for_even_if_broke(self):
        farm = {"money": 0}
        market_state = self._market(prices={"WHEAT": 20}, inventory={"WHEAT": 0})
        private = {"seeds": {"WHEAT": 2}}

        self.assertEqual(choose_crop(farm, market_state, private), "WHEAT")


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
