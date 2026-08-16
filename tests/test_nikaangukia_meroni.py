"""
Small, focused unit tests for the nikaangukia_meroni V1 agent.

These don't try to simulate a full game - they just check that each
building block behaves sensibly on its own, and that the top-level
agent never crashes on weird input.

Run with:
    python -m unittest discover -s tests
"""

import unittest

from main import (
    MAX_ANIMALS,
    MAX_HANDS_PER_DAY,
    MAX_MARKET_ORDERS_PER_TURN,
    MAX_SELL_PER_TURN,
    carried_animal,
    choose_crop,
    choose_farmer_action,
    choose_unit_action,
    count_owned_animals,
    decide_animal_market_actions,
    decide_hire_orders,
    decide_market_actions,
    has_plantable_seed,
    is_harvestable,
    is_shed_adjacent,
    nearest_shed_tile,
    nikaangukia_meroni,
    scan_animal_structures,
    shed_access_tiles,
    should_build_structure,
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
            # Compare against the engine's 10,000-unit baseline; a small
            # absolute inventory is not a glut.
            inventory={"STRAWBERRY": 30000, "WHEAT": 10000},
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

    def test_preserves_reserved_wheat_for_animal_feed(self):
        private = {"shed": {"WHEAT": 3}, "seeds": {}}
        market_state = self._market(prices={"WHEAT": 25})

        actions = decide_market_actions(
            {"money": 0}, private, market_state, day=5, reserved_wheat=2
        )

        self.assertIn(["SELL", "WHEAT", 1], actions)
        self.assertNotIn(["SELL", "WHEAT", 3], actions)

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


def _ripe_wheat():
    """A WHEAT plant old enough that HARVEST actually works."""
    return {
        "kind": "PLANT",
        "crop": "WHEAT",
        "planted_day": 0,
        "watered_today": True,
        "consecutive_unwatered": 0,
        "yield_units": 3,
    }


class TestHireDecision(unittest.TestCase):
    def _farm(self, tiles, money=3000, hands=None):
        hands = hands or []
        return {
            "money": money,
            "tiles": tiles,
            "farmer": [0, 0],
            "hands": [list(h) for h in hands],
            "unlocked_quadrants": ["NW"],
            "hires_today": len(hands),
        }

    def _work_tiles(self, n):
        """A row of n weeds - every one is a tile that needs a unit's attention."""
        return [[{"kind": "WEED"} for _ in range(n)]]

    def test_no_hire_when_there_is_nothing_to_do(self):
        # An empty tile with no seed in hand is not work - don't pay for hands
        # that would just stand around.
        farm = self._farm(tiles=[[None]])
        self.assertEqual(decide_hire_orders(farm, 1, day=5, hour=0, seeds={}), [])

    def test_hires_when_there_is_plenty_of_work(self):
        farm = self._farm(tiles=self._work_tiles(12))
        orders = decide_hire_orders(farm, 12, day=5, hour=0, seeds={})
        self.assertTrue(orders)
        self.assertEqual(orders[0], ["HIRE"])

    def test_does_not_hire_late_in_the_day(self):
        # Hands vanish at the end of the day, so hiring at hour 20 buys
        # almost no work for the same price as hiring at hour 0.
        farm = self._farm(tiles=self._work_tiles(12))
        self.assertEqual(decide_hire_orders(farm, 12, day=5, hour=20, seeds={}), [])

    def test_respects_the_daily_cap(self):
        # Hire cost is Fibonacci within a day, so it climbs fast - cap it.
        farm = self._farm(tiles=self._work_tiles(100))
        orders = decide_hire_orders(farm, 100, day=5, hour=0, seeds={})
        self.assertLessEqual(len(orders), MAX_HANDS_PER_DAY)

    def test_does_not_hire_when_short_on_money(self):
        farm = self._farm(tiles=self._work_tiles(12), money=0)
        self.assertEqual(decide_hire_orders(farm, 12, day=5, hour=0, seeds={}), [])

    def test_stops_hiring_once_enough_hands_are_already_working(self):
        farm = self._farm(
            tiles=self._work_tiles(12),
            hands=[(4, 4)] * MAX_HANDS_PER_DAY,
        )
        self.assertEqual(decide_hire_orders(farm, 12, day=5, hour=0, seeds={}), [])


class TestHandCoordination(unittest.TestCase):
    def _state(self, tiles, board_size, hands=None):
        hands = hands or []
        return {
            "farm": {
                "money": 3000,
                "tiles": tiles,
                "farmer": [0, 0],
                "hands": [list(h) for h in hands],
                "unlocked_quadrants": ["NW"],
                "hires_today": len(hands),
            },
            "private": {"shed": {}, "seeds": {}},
            "market_state": {"prices": {}, "inventory": {}},
            "board_size": board_size,
            "day": 5,
        }

    def test_two_units_do_not_walk_to_the_same_tile(self):
        # Two ripe crops, two units standing together between them. Without
        # claiming, both would walk to the same crop and one turn is wasted.
        tiles = [[_ripe_wheat(), None, _ripe_wheat()]]
        state = self._state(tiles, board_size=3)

        claimed = set()
        first = choose_unit_action(state, 1, 0, 0, claimed)
        second = choose_unit_action(state, 1, 0, 1, claimed)

        self.assertEqual(len(claimed), 2, "each unit should reserve its own tile")
        self.assertNotEqual(first, second)
        self.assertEqual({tuple(first), tuple(second)}, {("WEST",), ("EAST",)})

    def test_a_unit_claims_the_tile_it_acts_on(self):
        # A unit harvesting where it stands must reserve that tile so a
        # second unit doesn't walk over to harvest the same thing.
        tiles = [[_ripe_wheat()]]
        state = self._state(tiles, board_size=1)

        claimed = set()
        self.assertEqual(choose_unit_action(state, 0, 0, 0, claimed), ["HARVEST"])
        self.assertIn((0, 0), claimed)

    def test_agent_returns_one_action_per_hired_hand(self):
        obs = {
            "player": 0,
            "day": 5,
            "hour": 6,
            "farms": [
                {
                    "money": 3000,
                    "tiles": [[_ripe_wheat(), _ripe_wheat(), None]],
                    "farmer": [0, 0],
                    "hands": [[1, 0], [2, 0]],
                    "unlocked_quadrants": ["NW"],
                    "hires_today": 2,
                }
            ],
            "market": {"prices": {}, "inventory": {}},
            "private": {"shed": {}, "seeds": {}, "inventories": [{}, {}, {}]},
        }
        result = nikaangukia_meroni(obs)
        self.assertEqual(len(result["hands"]), 2)
        for action in result["hands"]:
            self.assertIsInstance(action, list)
            self.assertTrue(action)

    def test_hands_are_empty_when_none_are_hired(self):
        state_obs = {
            "player": 0,
            "day": 5,
            "hour": 6,
            "farms": [
                {
                    "money": 3000,
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
        self.assertEqual(nikaangukia_meroni(state_obs)["hands"], [])


def _unfed_goose_coop(consecutive_unfed=1, fed_today=False, cared_today=False, yield_units=0):
    return {
        "kind": "COOP",
        "animal": "GOOSE",
        "placed_day": 0,
        "yield_units": yield_units,
        "consecutive_unfed": consecutive_unfed,
        "fed_today": fed_today,
        "cared_today": cared_today,
        "fertilizer_available": False,
        "pending_care_bonus": 0,
    }


class TestShedAdjacency(unittest.TestCase):
    def test_shed_access_tiles_are_the_four_inner_corners(self):
        # board_size=10 -> half=5, matching the engine's own formula.
        self.assertEqual(
            set(shed_access_tiles(10)), {(4, 4), (5, 4), (4, 5), (5, 5)}
        )

    def test_is_shed_adjacent_true_and_false(self):
        self.assertTrue(is_shed_adjacent(4, 4, 10))
        self.assertFalse(is_shed_adjacent(0, 0, 10))

    def test_nearest_shed_tile_picks_the_closest_corner(self):
        self.assertEqual(nearest_shed_tile(0, 0, 10), (4, 4))


class TestAnimalCounting(unittest.TestCase):
    def _farm(self, tiles, money=3000):
        return {"money": money, "tiles": tiles, "farmer": [0, 0], "hands": []}

    def test_scan_counts_filled_and_unfilled_separately(self):
        tiles = [[_unfed_goose_coop(), {"kind": "COOP"}, {"kind": "COOP"}]]
        farm = self._farm(tiles)
        self.assertEqual(scan_animal_structures(farm, 1), (1, 2))

    def test_count_owned_animals_sums_shed_carried_and_placed(self):
        tiles = [[_unfed_goose_coop()]]
        farm = self._farm(tiles)
        private = {
            "shed": {"GOOSE": 1},
            "inventories": [{"GOOSE": 1}, {}],
        }
        # 1 placed + 1 in shed + 1 carried = 3.
        self.assertEqual(count_owned_animals(farm, private, 1), 3)


class TestShouldBuildStructure(unittest.TestCase):
    def _farm(self, tiles, money):
        return {"money": money, "tiles": tiles, "farmer": [0, 0], "hands": []}

    def test_builds_when_affordable_and_no_unfilled_structure(self):
        # GOOSE costs 300; ANIMAL_SPEND_CAP_FRACTION=0.5 means we need
        # money >= 600 before committing to one.
        farm = self._farm([[None]], money=1000)
        self.assertTrue(should_build_structure(farm, 1))

    def test_does_not_build_when_unaffordable(self):
        farm = self._farm([[None]], money=100)
        self.assertFalse(should_build_structure(farm, 1))

    def test_does_not_build_when_a_structure_is_already_unfilled(self):
        # One empty coop is already waiting for an animal - don't tie up a
        # second tile before that one's even filled.
        farm = self._farm([[None, {"kind": "COOP"}]], money=10000)
        self.assertFalse(should_build_structure(farm, 1))

    def test_does_not_build_past_the_cap(self):
        tiles = [[_unfed_goose_coop() for _ in range(MAX_ANIMALS)] + [None]]
        farm = self._farm(tiles, money=10000)
        self.assertFalse(should_build_structure(farm, 1))


class TestDecideAnimalMarketActions(unittest.TestCase):
    def _farm(self, tiles, money):
        return {"money": money, "tiles": tiles, "farmer": [0, 0], "hands": []}

    def test_buys_an_animal_when_affordable_and_under_cap(self):
        farm = self._farm([[None]], money=1000)
        private = {"shed": {}, "inventories": [{}]}
        actions = decide_animal_market_actions(farm, private, 1)
        self.assertIn(["BUY_ANIMAL", "GOOSE", 1], actions)

    def test_does_not_buy_past_the_cap(self):
        tiles = [[_unfed_goose_coop() for _ in range(MAX_ANIMALS)]]
        farm = self._farm(tiles, money=10000)
        private = {"shed": {}, "inventories": [{}]}
        actions = decide_animal_market_actions(farm, private, 1)
        self.assertNotIn(["BUY_ANIMAL", "GOOSE", 1], actions)

    def test_buys_wheat_when_reserve_is_empty_and_an_animal_is_placed(self):
        farm = self._farm([[_unfed_goose_coop()]], money=1000)
        private = {"shed": {}, "inventories": [{}]}
        actions = decide_animal_market_actions(farm, private, 1)
        self.assertIn(["BUY_PRODUCT", "WHEAT", 1], actions)

    def test_does_not_buy_wheat_when_no_animal_is_placed_yet(self):
        # Nothing needs feeding yet - no reason to stockpile wheat for it.
        farm = self._farm([[None]], money=1000)
        private = {"shed": {}, "inventories": [{}]}
        actions = decide_animal_market_actions(farm, private, 1)
        self.assertNotIn(["BUY_PRODUCT", "WHEAT", 1], actions)


class TestAnimalPriority(unittest.TestCase):
    def _state(self, tiles, farmer, board_size, private=None, money=3000):
        return {
            "farm": {
                "money": money,
                "tiles": tiles,
                "farmer": list(farmer),
                "hands": [],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
            "private": private or {"shed": {}, "seeds": {}, "inventories": [{}]},
            "market_state": {"prices": {}, "inventory": {}},
            "board_size": board_size,
            "day": 5,
        }

    def test_harvests_a_ripe_animal_under_its_feet(self):
        tiles = [[_unfed_goose_coop(yield_units=2, fed_today=True, cared_today=True)]]
        state = self._state(tiles, farmer=(0, 0), board_size=1)
        self.assertEqual(choose_farmer_action(state), ["HARVEST"])

    def test_feeds_before_caring_when_both_are_needed(self):
        tiles = [[_unfed_goose_coop()]]
        private = {"shed": {}, "seeds": {}, "inventories": [{"WHEAT": 1}]}
        state = self._state(tiles, farmer=(0, 0), board_size=1, private=private)
        self.assertEqual(choose_farmer_action(state), ["FEED"])

    def test_feed_beats_harvest_when_animal_is_at_escape_risk(self):
        # A ready Egg must not distract the unit from rescuing an animal that
        # has already missed one feeding and will escape at the next refresh.
        tiles = [[_unfed_goose_coop(consecutive_unfed=1, yield_units=4)]]
        private = {"shed": {}, "seeds": {}, "inventories": [{"WHEAT": 1}]}
        state = self._state(tiles, farmer=(0, 0), board_size=1, private=private)
        self.assertEqual(choose_farmer_action(state), ["FEED"])

    def test_wheat_carrier_keeps_the_feed_target_from_a_crop_worker(self):
        # The first unit has no Wheat and must not claim the Goose tile for a
        # harvest route; the second unit carries Wheat and gets the rescue.
        tiles = [[None, None, _unfed_goose_coop(consecutive_unfed=1, yield_units=2)]]
        private = {
            "shed": {},
            "seeds": {},
            "inventories": [{}, {"WHEAT": 1}],
        }
        state = self._state(tiles, farmer=(0, 0), board_size=3, private=private)
        claimed = set()
        feed_claimed = set()
        choose_unit_action(state, 0, 0, 0, claimed, [0], feed_claimed)
        self.assertEqual(
            choose_unit_action(state, 0, 1, 1, claimed, [0], feed_claimed),
            ["EAST"],
        )

    def test_collects_nonstacking_fertilizer_before_optional_care(self):
        tiles = [[_unfed_goose_coop(fed_today=True, cared_today=False)]]
        tiles[0][0]["fertilizer_available"] = True
        state = self._state(tiles, farmer=(0, 0), board_size=1)
        self.assertEqual(choose_farmer_action(state), ["COLLECT_FERTILIZER"])

    def test_cares_when_already_fed_but_not_cared_for(self):
        tiles = [[_unfed_goose_coop(fed_today=True, cared_today=False)]]
        state = self._state(tiles, farmer=(0, 0), board_size=1)
        self.assertEqual(choose_farmer_action(state), ["CARE"])

    def test_places_a_carried_animal_on_its_empty_structure(self):
        tiles = [[{"kind": "COOP"}]]
        private = {"shed": {}, "seeds": {}, "inventories": [{"GOOSE": 1}]}
        state = self._state(tiles, farmer=(0, 0), board_size=1, private=private)
        self.assertEqual(choose_farmer_action(state), ["PLACE", "GOOSE"])

    def test_picks_up_a_bought_animal_when_a_home_is_waiting(self):
        # Standing on a shed-access tile (board_size=10 -> (4,4) is one),
        # shed holds a bought GOOSE, and an empty coop is waiting for it.
        tiles = [[None] * 10 for _ in range(10)]
        tiles[4][5] = {"kind": "COOP"}  # empty coop elsewhere on the board
        private = {"shed": {"GOOSE": 1}, "seeds": {}, "inventories": [{}]}
        state = self._state(tiles, farmer=(4, 4), board_size=10, private=private)
        self.assertEqual(choose_farmer_action(state), ["PICKUP", "GOOSE", 1])

    def test_does_not_pick_up_an_animal_with_no_home_waiting(self):
        # Same shed stock, but no coop built anywhere yet - picking it up
        # would just carry it around uselessly.
        tiles = [[None] * 10 for _ in range(10)]
        private = {"shed": {"GOOSE": 1}, "seeds": {}, "inventories": [{}]}
        state = self._state(tiles, farmer=(4, 4), board_size=10, private=private)
        self.assertNotEqual(choose_farmer_action(state), ["PICKUP", "GOOSE", 1])

    def test_walks_toward_empty_structure_when_carrying_an_animal(self):
        tiles = [[None, {"kind": "COOP"}]]
        private = {"shed": {}, "seeds": {}, "inventories": [{"GOOSE": 1}]}
        state = self._state(tiles, farmer=(0, 0), board_size=1, private=private)
        self.assertEqual(choose_farmer_action(state), ["EAST"])

    def test_detours_to_shed_for_wheat_when_an_urgent_animal_needs_feeding(self):
        # An animal one step away already missed a feeding (consecutive_
        # unfed=1); farmer isn't carrying wheat but the shed (standing tile
        # itself, board_size=1 -> shed tile is (0,0)) has some.
        tiles = [[None, _unfed_goose_coop(consecutive_unfed=1)]]
        private = {"shed": {"WHEAT": 5}, "seeds": {}, "inventories": [{}]}
        state = self._state(tiles, farmer=(0, 0), board_size=1, private=private)
        self.assertEqual(choose_farmer_action(state), ["PICKUP", "WHEAT", 1])

    def test_carried_animal_helper_finds_the_held_animal(self):
        self.assertEqual(carried_animal({"GOOSE": 2}), "GOOSE")
        self.assertIsNone(carried_animal({}))
        self.assertIsNone(carried_animal({"GOOSE": 0}))


class TestMarketOrderCap(unittest.TestCase):
    def test_never_exceeds_the_per_turn_order_limit(self):
        # The engine silently drops orders past maxMarketOrdersPerTurn, so
        # going over the cap loses actions with no error to catch.
        shed = {p: 40 for p in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY",
                                "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]}
        obs = {
            "player": 0,
            "day": 5,
            "hour": 0,
            "farms": [
                {
                    "money": 3000,
                    "tiles": [[{"kind": "WEED"} for _ in range(12)]],
                    "farmer": [0, 0],
                    "hands": [],
                    "unlocked_quadrants": ["NW"],
                    "hires_today": 0,
                }
            ],
            "market": {
                "prices": {p: 500 for p in shed},
                "inventory": {p: 10000 for p in shed},
            },
            "private": {"shed": shed, "seeds": {}, "inventories": [{}]},
        }
        result = nikaangukia_meroni(obs)
        self.assertLessEqual(len(result["market"]), MAX_MARKET_ORDERS_PER_TURN)


if __name__ == "__main__":
    unittest.main()
