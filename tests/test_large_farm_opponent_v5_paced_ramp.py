"""
Regression tests for experiments/candidates/large_farm_opponent_v5_paced_ramp.py
(Issue #21, Track C, Experiment 5).

Mirrors tests/test_nikaangukia_meroni.py's fixture style (TestChooseAnimalToBuild,
TestDecideAnimalMarketActions) so the paced-ramp behaviour is checked the same
way the baseline animal-purchase logic already is.

Run with:
    python -m unittest tests.test_large_farm_opponent_v5_paced_ramp -v
"""
import unittest

from experiments.candidates.large_farm_opponent_v5_paced_ramp import (
    MAX_ANIMALS_BASE,
    MAX_ANIMALS_CEILING,
    ANIMAL_RAMP_RESERVE_PER_SLOT,
    effective_animal_cap,
    _choose_animal_to_build,
    _decide_animal_market_actions,
    base,
)

TEST_ANIMAL = base.ACTIVE_ANIMALS[0]
TEST_ANIMAL_2 = base.ACTIVE_ANIMALS[1]
TEST_STRUCTURE = base.ANIMALS[TEST_ANIMAL]["structure"]


def _unfed_coop():
    return {
        "kind": TEST_STRUCTURE,
        "animal": TEST_ANIMAL,
        "placed_day": 0,
        "yield_units": 0,
        "consecutive_unfed": 1,
        "fed_today": False,
        "cared_today": False,
        "fertilizer_available": False,
        "pending_care_bonus": 0,
    }


def _farm(tiles, money, quadrants=None):
    return {
        "money": money,
        "tiles": tiles,
        "farmer": [0, 0],
        "hands": [],
        "unlocked_quadrants": quadrants if quadrants is not None else ["NW"],
    }


def _private(**species_shed):
    return {"shed": dict(species_shed), "inventories": [{}]}


LAND_UNBOUGHT = ["NW"]
LAND_FULLY_BOUGHT = ["NW", "NE", "SW"]  # len - 1 == 2 == len(base.LAND_BUY_DAYS)


class TestEffectiveAnimalCap(unittest.TestCase):
    def test_stays_at_base_when_land_not_fully_bought_even_with_huge_cash(self):
        # This is the direct regression test for Exp 3's finding: raising
        # the cap before land is secured is what caused the collapse.
        farm = _farm([[None]], money=1_000_000, quadrants=LAND_UNBOUGHT)
        self.assertEqual(effective_animal_cap(farm), MAX_ANIMALS_BASE)

    def test_stays_at_base_when_land_bought_but_no_reserve_for_slot_five(self):
        farm = _farm([[None]], money=ANIMAL_RAMP_RESERVE_PER_SLOT - 1, quadrants=LAND_FULLY_BOUGHT)
        self.assertEqual(effective_animal_cap(farm), MAX_ANIMALS_BASE)

    def test_opens_slot_five_once_its_own_reserve_is_cleared(self):
        farm = _farm([[None]], money=ANIMAL_RAMP_RESERVE_PER_SLOT, quadrants=LAND_FULLY_BOUGHT)
        self.assertEqual(effective_animal_cap(farm), MAX_ANIMALS_BASE + 1)

    def test_does_not_open_slot_six_until_its_own_larger_reserve_is_cleared(self):
        # A fresh, progressively larger condition per additional animal -
        # not one global gate. Clearing slot 5's bar must not also open 6.
        farm = _farm([[None]], money=ANIMAL_RAMP_RESERVE_PER_SLOT, quadrants=LAND_FULLY_BOUGHT)
        self.assertLess(effective_animal_cap(farm), MAX_ANIMALS_BASE + 2)

        farm = _farm([[None]], money=ANIMAL_RAMP_RESERVE_PER_SLOT * 2, quadrants=LAND_FULLY_BOUGHT)
        self.assertEqual(effective_animal_cap(farm), MAX_ANIMALS_BASE + 2)

    def test_reaches_the_ceiling_once_every_slot_reserve_is_cleared(self):
        n_extra = MAX_ANIMALS_CEILING - MAX_ANIMALS_BASE
        farm = _farm([[None]], money=ANIMAL_RAMP_RESERVE_PER_SLOT * n_extra, quadrants=LAND_FULLY_BOUGHT)
        self.assertEqual(effective_animal_cap(farm), MAX_ANIMALS_CEILING)

    def test_never_exceeds_the_ceiling_regardless_of_cash(self):
        farm = _farm([[None]], money=10_000_000, quadrants=LAND_FULLY_BOUGHT)
        self.assertEqual(effective_animal_cap(farm), MAX_ANIMALS_CEILING)

    def test_cap_retracts_if_cash_later_drops_below_a_cleared_reserve(self):
        # Recomputed fresh every turn from live cash, not memoized - a later
        # dip in cash should stop granting NEW slots (it cannot un-build an
        # animal already bought, since this function only feeds a gate, it
        # doesn't track history).
        rich = _farm([[None]], money=ANIMAL_RAMP_RESERVE_PER_SLOT * 3, quadrants=LAND_FULLY_BOUGHT)
        poor = _farm([[None]], money=50, quadrants=LAND_FULLY_BOUGHT)
        self.assertGreater(effective_animal_cap(rich), MAX_ANIMALS_BASE)
        self.assertEqual(effective_animal_cap(poor), MAX_ANIMALS_BASE)


class TestChooseAnimalToBuildRespectsThePacedCap(unittest.TestCase):
    def test_does_not_build_a_fifth_before_land_is_bought_even_when_rich(self):
        # _unfed_coop() has an "animal" key set, so these 4 count as FILLED
        # structures (scan_animal_structures splits on that key) - the
        # unfilled-structure guard is not what's blocking this test, the
        # paced cap is.
        tiles = [[_unfed_coop() for _ in range(MAX_ANIMALS_BASE)] + [None]]
        farm = _farm(tiles, money=1_000_000, quadrants=LAND_UNBOUGHT)
        self.assertIsNone(_choose_animal_to_build(farm, _private(), 1, day=0))

    def test_builds_a_fifth_once_land_bought_and_slot_five_reserve_cleared(self):
        tiles = [[_unfed_coop() for _ in range(MAX_ANIMALS_BASE)] + [None]]
        farm = _farm(tiles, money=ANIMAL_RAMP_RESERVE_PER_SLOT + 500, quadrants=LAND_FULLY_BOUGHT)
        result = _choose_animal_to_build(farm, _private(), 1, day=0)
        self.assertIn(result, base.ACTIVE_ANIMALS)

    def test_still_refuses_to_build_past_the_ceiling(self):
        tiles = [[_unfed_coop() for _ in range(MAX_ANIMALS_CEILING)] + [None]]
        farm = _farm(tiles, money=10_000_000, quadrants=LAND_FULLY_BOUGHT)
        self.assertIsNone(_choose_animal_to_build(farm, _private(), 1, day=0))

    def test_still_refuses_while_a_structure_sits_unfilled(self):
        # Preserved verbatim from main.choose_animal_to_build - the paced
        # ramp must not bypass the existing "don't strand a tile" guard.
        tiles = [[None, {"kind": TEST_STRUCTURE}]]
        farm = _farm(tiles, money=10_000_000, quadrants=LAND_FULLY_BOUGHT)
        self.assertIsNone(_choose_animal_to_build(farm, _private(), 1, day=0))

    def test_still_picks_the_species_owned_fewer_of(self):
        # Species-selection logic (Issue #20's fix) must be untouched by
        # this experiment.
        tiles = [[_unfed_coop() for _ in range(MAX_ANIMALS_BASE)] + [None]]
        farm = _farm(tiles, money=ANIMAL_RAMP_RESERVE_PER_SLOT + 500, quadrants=LAND_FULLY_BOUGHT)
        private = _private(**{TEST_ANIMAL: 1})
        result = _choose_animal_to_build(farm, private, 1, day=0)
        self.assertEqual(result, TEST_ANIMAL_2)


class TestDecideAnimalMarketActionsRespectsThePacedCap(unittest.TestCase):
    def test_does_not_buy_a_fifth_before_land_is_bought_even_when_rich(self):
        tiles = [[_unfed_coop() for _ in range(MAX_ANIMALS_BASE)]]
        farm = _farm(tiles, money=1_000_000, quadrants=LAND_UNBOUGHT)
        actions = _decide_animal_market_actions(farm, _private(), 1, day=0)
        buy_orders = [a for a in actions if a and a[0] == "BUY_ANIMAL"]
        self.assertEqual(buy_orders, [])

    def test_buys_a_fifth_once_land_bought_and_slot_five_reserve_cleared(self):
        tiles = [[_unfed_coop() for _ in range(MAX_ANIMALS_BASE)]]
        farm = _farm(tiles, money=ANIMAL_RAMP_RESERVE_PER_SLOT + 500, quadrants=LAND_FULLY_BOUGHT)
        actions = _decide_animal_market_actions(farm, _private(), 1, day=0)
        buy_orders = [a for a in actions if a and a[0] == "BUY_ANIMAL"]
        self.assertEqual(len(buy_orders), 1)

    def test_still_buys_wheat_when_reserve_empty_and_an_animal_is_placed(self):
        farm = _farm([[_unfed_coop()]], money=1000, quadrants=LAND_UNBOUGHT)
        actions = _decide_animal_market_actions(farm, _private(), 1, day=0)
        self.assertIn(["BUY_PRODUCT", "WHEAT", 1], actions)


class TestBuildAndBuySagreeOnTheSameCap(unittest.TestCase):
    """
    Direct regression test for the experiment/animal-cliff stranding bug:
    that experiment gated BUY_ANIMAL on a scaling reserve but left
    choose_animal_to_build on the raw (already-raised) MAX_ANIMALS, so a
    pasture could be started for a slot the purchase then refused to fill -
    stranding a tile for the rest of the season. This test constructs the
    exact boundary state (land bought, cash clears the OLD flat gate but not
    the NEW per-slot one) and asserts build and buy make the SAME decision.
    """

    def test_build_and_buy_agree_when_slot_five_reserve_is_not_yet_cleared(self):
        money = ANIMAL_RAMP_RESERVE_PER_SLOT - 1  # land bought, but too poor for slot 5
        build_tiles = [[_unfed_coop() for _ in range(MAX_ANIMALS_BASE)] + [None]]
        build_farm = _farm(build_tiles, money=money, quadrants=LAND_FULLY_BOUGHT)
        will_build = _choose_animal_to_build(build_farm, _private(), 1, day=0) is not None

        buy_tiles = [[_unfed_coop() for _ in range(MAX_ANIMALS_BASE)]]
        buy_farm = _farm(buy_tiles, money=money, quadrants=LAND_FULLY_BOUGHT)
        buy_actions = _decide_animal_market_actions(buy_farm, _private(), 1, day=0)
        will_buy = any(a and a[0] == "BUY_ANIMAL" for a in buy_actions)

        self.assertFalse(will_build)
        self.assertFalse(will_buy)
        self.assertEqual(will_build, will_buy)

    def test_build_and_buy_agree_once_slot_five_reserve_is_cleared(self):
        money = ANIMAL_RAMP_RESERVE_PER_SLOT + 500
        build_tiles = [[_unfed_coop() for _ in range(MAX_ANIMALS_BASE)] + [None]]
        build_farm = _farm(build_tiles, money=money, quadrants=LAND_FULLY_BOUGHT)
        will_build = _choose_animal_to_build(build_farm, _private(), 1, day=0) is not None

        buy_tiles = [[_unfed_coop() for _ in range(MAX_ANIMALS_BASE)]]
        buy_farm = _farm(buy_tiles, money=money, quadrants=LAND_FULLY_BOUGHT)
        buy_actions = _decide_animal_market_actions(buy_farm, _private(), 1, day=0)
        will_buy = any(a and a[0] == "BUY_ANIMAL" for a in buy_actions)

        self.assertTrue(will_build)
        self.assertTrue(will_buy)
        self.assertEqual(will_build, will_buy)


if __name__ == "__main__":
    unittest.main()
