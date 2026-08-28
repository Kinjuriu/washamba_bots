"""
Regression tests for experiments/candidates/max_animals_pacing_v1.py.

v1 fixes a gap an independent mechanism audit found in v0: v0's
available_placement_capacity returned a flat MAX_ANIMALS the instant a
second quadrant was purchased, with no check that anything on it was
actually buildable. These tests use a realistic board_size=10 (the
engine's real default - see kaggriculture.json/kaggriculture.py's
`get(cfg, "boardSize", 10)`) because v1's capacity calculation now calls
main.tile_quadrant(x, y, board_size) per tile, and that function is only
meaningful at a realistic board size (tile_quadrant(x, y, 1) degenerates -
half = 1 // 2 = 0, so every tile falls in "SE"). v0's tests used
board_size=1 as a geometry-free shortcut; that shortcut no longer applies
to v1's per-quadrant scan.

Tiles grids below are built sparse (only the positions under test are set)
and rely on available_placement_capacity treating any position missing
from a row as None - which matches the real engine's semantics for an
uninitialized/empty tile and is what the function is built to detect as
"buildable" in the first place.

Run with:
    python -m unittest tests.test_max_animals_pacing_v1 -v
"""
import unittest

import main as base
import experiments.candidates.max_animals_pacing_v1 as candidate

BOARD_SIZE = 10


def _clear_logs():
    candidate.DECISION_LOG.clear()
    candidate.POST_LAND_PURCHASE_LOG.clear()


def _repin():
    """experiments/candidates/max_animals_pacing_v0.py patches the same two
    `main` globals this candidate does (MAX_ANIMALS,
    decide_animal_market_actions) - whichever candidate module unittest's
    discovery imports last wins for the rest of the process, since both
    mutate the same shared module object. Re-pin this candidate's own patch
    before its own tests run so they don't depend on import order."""
    base.MAX_ANIMALS = 5
    base.decide_animal_market_actions = candidate._decide_animal_market_actions_paced


def _board(overrides=None, rows=BOARD_SIZE, cols=BOARD_SIZE):
    """A rows x cols tiles grid, None everywhere except `overrides`
    ({(x, y): tile_dict})."""
    overrides = overrides or {}
    tiles = [[None for _ in range(cols)] for _ in range(rows)]
    for (x, y), tile in overrides.items():
        tiles[y][x] = tile
    return tiles


def _farm(overrides=None, unlocked_quadrants=None, money=5000):
    return {
        "money": money,
        "tiles": _board(overrides),
        "unlocked_quadrants": unlocked_quadrants or ["NW"],
        "hands": [],
    }


PASTURE_EMPTY = {"kind": "PASTURE"}
PASTURE_SHEEP = {"kind": "PASTURE", "animal": "SHEEP"}
PASTURE_COW = {"kind": "PASTURE", "animal": "COW"}
CROP_TILE = {"kind": "WHEAT_PLANT"}  # anything non-None, non-animal-structure


class TestMainPyUnchanged(unittest.TestCase):
    def setUp(self):
        _repin()

    def test_candidate_imports_the_real_main_module(self):
        self.assertEqual(base.__file__, candidate.base.__file__)

    def test_only_two_names_patched(self):
        self.assertEqual(base.MAX_ANIMALS, 5)
        self.assertIs(base.decide_animal_market_actions, candidate._decide_animal_market_actions_paced)
        self.assertEqual(base.LIQUIDATION_START_DAY, 19)
        self.assertEqual(base.MAX_LAND_PURCHASES, 2)


class TestAvailablePlacementCapacityHomeLand(unittest.TestCase):
    """Home-land ("NW") behaviour must be unchanged from v0: capped at
    MAX_ANIMALS_ON_HOME_LAND regardless of how many buildable tiles exist,
    matching choose_animal_to_build's own NW-specific cap exactly."""

    def test_no_structures_capacity_is_home_cap(self):
        farm = _farm()
        self.assertEqual(
            candidate.available_placement_capacity(farm, BOARD_SIZE),
            base.MAX_ANIMALS_ON_HOME_LAND,
        )

    def test_existing_structures_below_home_cap_dont_reduce_capacity(self):
        farm = _farm({(0, 0): PASTURE_SHEEP})
        self.assertEqual(
            candidate.available_placement_capacity(farm, BOARD_SIZE),
            base.MAX_ANIMALS_ON_HOME_LAND,
        )

    def test_existing_structures_at_home_cap_dont_exceed_it(self):
        farm = _farm({
            (0, 0): PASTURE_SHEEP, (1, 0): PASTURE_COW, (2, 0): PASTURE_EMPTY,
        })
        self.assertEqual(
            candidate.available_placement_capacity(farm, BOARD_SIZE),
            base.MAX_ANIMALS_ON_HOME_LAND,
        )

    def test_defensively_never_under_reports_existing_home_structures(self):
        """Pathological state choose_animal_to_build should never allow (4
        structures on NW when the cap is 3) - capacity must still report at
        least what's already built, not silently claim less than reality."""
        farm = _farm({
            (0, 0): PASTURE_SHEEP, (1, 0): PASTURE_COW,
            (2, 0): PASTURE_EMPTY, (3, 0): PASTURE_EMPTY,
        })
        self.assertEqual(candidate.available_placement_capacity(farm, BOARD_SIZE), 4)


class TestAvailablePlacementCapacityExtraLand(unittest.TestCase):
    """The fixed behaviour: capacity on a newly-owned quadrant tracks its
    LIVE buildable-tile count, not a flat MAX_ANIMALS. This is the direct
    regression test for the bug the mechanism audit found in v0."""

    def test_freshly_unlocked_empty_quadrant_gives_large_capacity(self):
        """Right after BUY_LAND, before any crop has claimed the new
        ground, capacity should be large (home cap + ~25 buildable NE
        tiles) - functionally similar to v0's behaviour in this one
        specific moment, which is why v0's narrow evaluation window didn't
        catch the bug."""
        farm = _farm(unlocked_quadrants=["NW", "NE"])
        capacity = candidate.available_placement_capacity(farm, BOARD_SIZE)
        self.assertGreater(capacity, base.MAX_ANIMALS)

    def test_extra_quadrant_fully_claimed_by_crops_gives_no_extra_capacity(self):
        """THE FIX: a second quadrant that crops have already filled (zero
        None tiles, zero animal structures) must contribute ZERO extra
        capacity - v0 would have returned a flat MAX_ANIMALS (5) here
        regardless; v1 must return exactly the home cap (3), because
        nothing on NE can actually hold an animal right now."""
        ne_overrides = {(x, y): CROP_TILE for x in range(5, 10) for y in range(0, 5)}
        farm = _farm(ne_overrides, unlocked_quadrants=["NW", "NE"])
        capacity = candidate.available_placement_capacity(farm, BOARD_SIZE)
        self.assertEqual(capacity, base.MAX_ANIMALS_ON_HOME_LAND)
        self.assertLess(capacity, base.MAX_ANIMALS)

    def test_extra_quadrant_partially_claimed_counts_only_real_remaining_slots(self):
        """NE has 2 unfilled PASTUREs already built plus crops on every
        other tile (zero None tiles left) - extra capacity must be exactly
        2 (the built, empty structures), not 5 and not 25."""
        ne_overrides = {(x, y): CROP_TILE for x in range(5, 10) for y in range(0, 5)}
        ne_overrides[(5, 0)] = PASTURE_EMPTY
        ne_overrides[(6, 0)] = PASTURE_EMPTY
        farm = _farm(ne_overrides, unlocked_quadrants=["NW", "NE"])
        capacity = candidate.available_placement_capacity(farm, BOARD_SIZE)
        self.assertEqual(capacity, base.MAX_ANIMALS_ON_HOME_LAND + 2)

    def test_locked_quadrant_never_contributes_even_if_tiles_are_none(self):
        """A quadrant not in unlocked_quadrants must contribute nothing,
        regardless of what its tiles array happens to hold (real engine
        tiles there are the string "LOCKED", never None, but the function
        must not rely on that incidental fact - the explicit
        unlocked_quadrants filter is what's under test here)."""
        farm = _farm(unlocked_quadrants=["NW"])  # NE/SW/SE tiles default None but are NOT unlocked
        capacity = candidate.available_placement_capacity(farm, BOARD_SIZE)
        self.assertEqual(capacity, base.MAX_ANIMALS_ON_HOME_LAND)

    def test_capacity_shrinks_turn_over_turn_as_crops_claim_ground(self):
        """Live recomputation: the same farm, sampled before and after crops
        claim more of NE, must report shrinking capacity - proves this
        isn't cached or computed once at BUY_LAND time."""
        farm = _farm(unlocked_quadrants=["NW", "NE"])
        capacity_before = candidate.available_placement_capacity(farm, BOARD_SIZE)

        for x in range(5, 10):
            for y in range(0, 5):
                farm["tiles"][y][x] = CROP_TILE
        capacity_after = candidate.available_placement_capacity(farm, BOARD_SIZE)

        self.assertLess(capacity_after, capacity_before)
        self.assertEqual(capacity_after, base.MAX_ANIMALS_ON_HOME_LAND)


class TestDecideAnimalMarketActionsPaced(unittest.TestCase):
    def setUp(self):
        _repin()
        _clear_logs()

    def test_never_buys_past_home_cap_before_extra_land(self):
        farm = _farm(money=5000)
        private = {"shed": {}, "inventories": [{}]}

        for _ in range(6):
            actions = base.decide_animal_market_actions(farm, private, BOARD_SIZE, day=0)
            for order in actions:
                if order[0] == "BUY_ANIMAL":
                    private["shed"][order[1]] = private["shed"].get(order[1], 0) + 1

        owned = base.count_owned_animals(farm, private, BOARD_SIZE)
        self.assertLessEqual(owned, base.MAX_ANIMALS_ON_HOME_LAND)

    def test_blocked_when_extra_land_is_fully_cropped(self):
        """THE regression case: extra land owned, but nothing on it is
        buildable (all crops) - the buy-gate must NOT treat this as
        capacity for 5, only 3 (home)."""
        ne_overrides = {(x, y): CROP_TILE for x in range(5, 10) for y in range(0, 5)}
        farm = _farm(ne_overrides, unlocked_quadrants=["NW", "NE"], money=5000)
        private = {"shed": {"SHEEP": 3}, "inventories": [{}]}  # already at home cap

        actions = base.decide_animal_market_actions(farm, private, BOARD_SIZE, day=10)
        self.assertFalse([a for a in actions if a[0] == "BUY_ANIMAL"])
        self.assertEqual(len(candidate.DECISION_LOG), 1)
        self.assertEqual(candidate.DECISION_LOG[0]["capacity"], base.MAX_ANIMALS_ON_HOME_LAND)

    def test_buys_up_to_max_animals_when_extra_land_has_real_room(self):
        farm = _farm(unlocked_quadrants=["NW", "NE"], money=5000)
        private = {"shed": {}, "inventories": [{}]}

        for _ in range(8):
            actions = base.decide_animal_market_actions(farm, private, BOARD_SIZE, day=10)
            for order in actions:
                if order[0] == "BUY_ANIMAL":
                    private["shed"][order[1]] = private["shed"].get(order[1], 0) + 1

        owned = base.count_owned_animals(farm, private, BOARD_SIZE)
        self.assertEqual(owned, base.MAX_ANIMALS)

    def test_post_land_purchase_purchases_are_logged(self):
        farm = _farm(unlocked_quadrants=["NW", "NE"], money=5000)
        private = {"shed": {"SHEEP": 2, "COW": 1}, "inventories": [{}]}  # 3 owned, home cap reached
        base.decide_animal_market_actions(farm, private, BOARD_SIZE, day=10)
        self.assertEqual(len(candidate.POST_LAND_PURCHASE_LOG), 1)

    def test_species_selection_untouched(self):
        farm = _farm(money=5000)
        private = {"shed": {"SHEEP": 2}, "inventories": [{}]}
        actions = base.decide_animal_market_actions(farm, private, BOARD_SIZE, day=0)
        buy_orders = [a for a in actions if a[0] == "BUY_ANIMAL"]
        self.assertTrue(buy_orders)
        self.assertEqual(buy_orders[0][1], "COW")

    def test_wheat_safety_net_untouched(self):
        farm = _farm({(0, 0): PASTURE_SHEEP}, money=100)
        private = {"shed": {}, "inventories": [{}]}
        actions = base.decide_animal_market_actions(farm, private, BOARD_SIZE, day=5)
        self.assertIn(["BUY_PRODUCT", "WHEAT", 1], actions)

    def test_affordability_gates_still_apply(self):
        farm = _farm(money=1)
        private = {"shed": {}, "inventories": [{}]}
        actions = base.decide_animal_market_actions(farm, private, BOARD_SIZE, day=0)
        self.assertFalse([a for a in actions if a[0] == "BUY_ANIMAL"])


class TestProducesValidActions(unittest.TestCase):
    def test_full_agent_runs_without_raising(self):
        from kaggle_environments import make

        env = make("kaggriculture", configuration={"episodeSteps": 24, "seed": 0}, debug=False)
        env.run([candidate.agent, "starter"])
        self.assertIn(env.steps[-1][0].status, ("ACTIVE", "DONE"))


if __name__ == "__main__":
    unittest.main()
