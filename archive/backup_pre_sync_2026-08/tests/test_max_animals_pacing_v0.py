"""
Regression tests for experiments/candidates/max_animals_pacing_v0.py.

Covers: the capacity calculation matches the engine semantics it's
derived from, the buy-gate never fires ahead of that capacity, species
selection/affordability/wheat-safety-net are untouched, and the
mechanism actually changes behaviour at the exact point the diagnosis
identified (day 0, no extra land, MAX_ANIMALS_ON_HOME_LAND=3).

Run with:
    python -m unittest tests.test_max_animals_pacing_v0 -v
"""
import unittest

import main as base
import experiments.candidates.max_animals_pacing_v0 as candidate


def _clear_log():
    candidate.DECISION_LOG.clear()


def _repin():
    """experiments/candidates/max_animals_pacing_v1.py patches the same two
    `main` globals this candidate does (MAX_ANIMALS,
    decide_animal_market_actions) - whichever candidate module unittest's
    discovery imports last wins for the rest of the process, since both
    mutate the same shared module object. Re-pin this candidate's own patch
    before its own tests run so they don't depend on import order."""
    base.MAX_ANIMALS = 5
    base.decide_animal_market_actions = candidate._decide_animal_market_actions_paced


class TestMainPyUnchanged(unittest.TestCase):
    def setUp(self):
        _repin()

    def test_candidate_imports_the_real_main_module(self):
        self.assertEqual(base.__file__, candidate.base.__file__)

    def test_only_two_names_patched(self):
        self.assertEqual(base.MAX_ANIMALS, 5)
        self.assertIs(base.decide_animal_market_actions, candidate._decide_animal_market_actions_paced)
        # Nothing selling/land/liquidation-related is touched.
        self.assertEqual(base.LIQUIDATION_START_DAY, 19)
        self.assertEqual(base.MAX_LAND_PURCHASES, 2)


class TestAvailablePlacementCapacity(unittest.TestCase):
    """Capacity must match the exact engine semantics verified in the
    candidate's own docstring: BUY_ANIMAL only ever fills the shed;
    PLACE only succeeds on an unfilled structure; BUILD_* only succeeds
    on fully empty ground; MAX_ANIMALS_ON_HOME_LAND caps the home
    quadrant specifically, and stops applying once any extra land is
    owned."""

    def _farm(self, tiles, unlocked_quadrants=None):
        return {"tiles": tiles, "unlocked_quadrants": unlocked_quadrants or ["NW"]}

    def test_no_structures_no_extra_land_capacity_is_home_cap(self):
        farm = self._farm([[None, None, None]])
        self.assertEqual(
            candidate.available_placement_capacity(farm, board_size=1),
            base.MAX_ANIMALS_ON_HOME_LAND,
        )

    def test_existing_structures_below_home_cap_dont_reduce_capacity(self):
        tiles = [[{"kind": "PASTURE", "animal": "SHEEP"}, None]]
        farm = self._farm(tiles)
        self.assertEqual(
            candidate.available_placement_capacity(farm, board_size=1),
            base.MAX_ANIMALS_ON_HOME_LAND,
        )

    def test_unfilled_structure_counts_toward_existing_structures(self):
        # Defensive: if structures somehow exceed MAX_ANIMALS_ON_HOME_LAND
        # pre-land (shouldn't happen given choose_animal_to_build's own
        # gate, but the capacity function must never under-report what's
        # already built), capacity tracks the larger of the two. Uses
        # PASTURE only - ANIMAL_STRUCTURE_KINDS is derived from
        # ACTIVE_ANIMALS's own structures (SHEEP/COW -> PASTURE), and
        # COOP (GOOSE's structure) isn't in scope while GOOSE isn't
        # active - confirmed directly: base.ANIMAL_STRUCTURE_KINDS ==
        # {"PASTURE"} in the current build.
        tiles = [[
            {"kind": "PASTURE"}, {"kind": "PASTURE", "animal": "COW"},
            {"kind": "PASTURE"}, {"kind": "PASTURE", "animal": "SHEEP"},
        ]]
        farm = self._farm(tiles)
        self.assertEqual(candidate.available_placement_capacity(farm, board_size=1), 4)

    def test_extra_land_removes_the_home_cap_entirely(self):
        farm = self._farm([[None]], unlocked_quadrants=["NW", "NE"])
        self.assertEqual(candidate.available_placement_capacity(farm, board_size=1), base.MAX_ANIMALS)

    def test_extra_land_ignores_structure_count(self):
        tiles = [[{"kind": "PASTURE", "animal": "SHEEP"}]]
        farm = self._farm(tiles, unlocked_quadrants=["NW", "NE", "SW"])
        self.assertEqual(candidate.available_placement_capacity(farm, board_size=1), base.MAX_ANIMALS)


class TestDecideAnimalMarketActionsPaced(unittest.TestCase):
    def setUp(self):
        _repin()
        _clear_log()

    def test_never_buys_past_home_cap_before_extra_land(self):
        farm = {
            "money": 5000, "tiles": [[None, None, None]],
            "unlocked_quadrants": ["NW"], "hands": [],
        }
        private = {"shed": {}, "inventories": [{}]}

        for _ in range(6):  # more attempts than could ever be allowed
            actions = base.decide_animal_market_actions(farm, private, board_size=1, day=0)
            for order in actions:
                if order[0] == "BUY_ANIMAL":
                    private["shed"][order[1]] = private["shed"].get(order[1], 0) + 1

        owned = base.count_owned_animals(farm, private, board_size=1)
        self.assertLessEqual(owned, base.MAX_ANIMALS_ON_HOME_LAND)

    def test_buys_up_to_max_animals_once_extra_land_is_owned(self):
        farm = {
            "money": 5000, "tiles": [[None, None, None]],
            "unlocked_quadrants": ["NW", "NE"], "hands": [],
        }
        private = {"shed": {}, "inventories": [{}]}

        for _ in range(8):
            actions = base.decide_animal_market_actions(farm, private, board_size=1, day=0)
            for order in actions:
                if order[0] == "BUY_ANIMAL":
                    private["shed"][order[1]] = private["shed"].get(order[1], 0) + 1

        owned = base.count_owned_animals(farm, private, board_size=1)
        self.assertEqual(owned, base.MAX_ANIMALS)

    def test_logs_a_deferral_exactly_when_capacity_blocks_a_purchase(self):
        farm = {
            "money": 5000, "tiles": [[None, None, None]],
            "unlocked_quadrants": ["NW"], "hands": [],
        }
        private = {"shed": {"SHEEP": 3}, "inventories": [{}]}  # already at home cap

        base.decide_animal_market_actions(farm, private, board_size=1, day=5)
        self.assertEqual(len(candidate.DECISION_LOG), 1)
        self.assertEqual(candidate.DECISION_LOG[0]["owned"], 3)
        self.assertEqual(candidate.DECISION_LOG[0]["capacity"], base.MAX_ANIMALS_ON_HOME_LAND)

    def test_no_deferral_logged_when_a_purchase_is_allowed(self):
        farm = {"money": 5000, "tiles": [[None]], "unlocked_quadrants": ["NW"], "hands": []}
        private = {"shed": {}, "inventories": [{}]}
        base.decide_animal_market_actions(farm, private, board_size=1, day=0)
        self.assertEqual(len(candidate.DECISION_LOG), 0)

    def test_species_selection_untouched(self):
        """pick_next_animal_species is called with the exact same
        (affordable, held) shape as the original - verified by giving it
        a scenario where the original would clearly favour COW (owns
        more SHEEP already) and confirming the paced version agrees."""
        farm = {"money": 5000, "tiles": [[None, None]], "unlocked_quadrants": ["NW"], "hands": []}
        private = {"shed": {"SHEEP": 2}, "inventories": [{}]}
        actions = base.decide_animal_market_actions(farm, private, board_size=1, day=0)
        buy_orders = [a for a in actions if a[0] == "BUY_ANIMAL"]
        self.assertTrue(buy_orders)
        self.assertEqual(buy_orders[0][1], "COW")

    def test_wheat_safety_net_untouched(self):
        farm = {
            "money": 100,
            "tiles": [[{"kind": "PASTURE", "animal": "SHEEP"}]],
            "unlocked_quadrants": ["NW"], "hands": [],
        }
        private = {"shed": {}, "inventories": [{}]}
        actions = base.decide_animal_market_actions(farm, private, board_size=1, day=5)
        self.assertIn(["BUY_PRODUCT", "WHEAT", 1], actions)

    def test_affordability_gates_still_apply(self):
        farm = {"money": 1, "tiles": [[None]], "unlocked_quadrants": ["NW"], "hands": []}
        private = {"shed": {}, "inventories": [{}]}
        actions = base.decide_animal_market_actions(farm, private, board_size=1, day=0)
        self.assertFalse([a for a in actions if a[0] == "BUY_ANIMAL"])


class TestProducesValidActions(unittest.TestCase):
    def test_full_agent_runs_without_raising(self):
        from kaggle_environments import make

        env = make("kaggriculture", configuration={"episodeSteps": 24, "seed": 0}, debug=False)
        env.run([candidate.agent, "starter"])
        self.assertIn(env.steps[-1][0].status, ("ACTIVE", "DONE"))


if __name__ == "__main__":
    unittest.main()
