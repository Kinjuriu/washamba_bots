"""Small, focused unit tests for replay_shape_agent.py (Track C, Issue #21
reference opponent - REJECTED, see replay_shape_validation_report.md and
replay_shape_v1_1_report.md one directory up).

Targets the pure/deterministic decision functions in isolation, plus the
specific bugs found and fixed during this agent's build (mispriced hire
gate, missing seed-buying, wrong animal-structure capacity math, missing
empty-tile seek target) - regression coverage for each, not just a smoke
test of the happy path.

Experiment-specific test, not part of the production suite - not
discovered by `python -m unittest discover -s tests`. Run directly:
    python -m unittest discover -s experiments/replay_shape/tests
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from replay_shape_agent import (  # noqa: E402
    ACTIVE_ANIMALS,
    MAX_HANDS_TARGET,
    MIN_MONEY_TO_HIRE,
    TARGET_TOTAL_ANIMALS,
    TILES_PER_HAND,
    choose_animal_to_build,
    choose_crop,
    crew_target_for,
    decide_hire_orders,
    decide_land_orders,
    decide_seed_orders,
    find_nearest_target,
    scan_animal_structures,
)


def make_farm(tiles=None, money=1000, hands=None, unlocked_quadrants=None):
    return {
        "tiles": tiles if tiles is not None else [[None] * 10 for _ in range(10)],
        "money": money,
        "hands": hands if hands is not None else [],
        "unlocked_quadrants": unlocked_quadrants if unlocked_quadrants is not None else ["NW"],
    }


class TestCrewTargetFor(unittest.TestCase):
    def test_scales_with_tiles(self):
        self.assertEqual(crew_target_for(25), 5)
        self.assertEqual(crew_target_for(75), 15)

    def test_capped_at_max_hands_target(self):
        self.assertEqual(crew_target_for(10_000), MAX_HANDS_TARGET)

    def test_never_below_one(self):
        self.assertEqual(crew_target_for(0), 1)


class TestDecideHireOrders(unittest.TestCase):
    def test_no_hire_below_min_money(self):
        farm = make_farm(money=MIN_MONEY_TO_HIRE - 1, hands=[])
        self.assertEqual(decide_hire_orders(farm, day=10), [])

    def test_hires_toward_target_when_affordable(self):
        farm = make_farm(money=1000, hands=[], unlocked_quadrants=["NW", "NE", "SW"])
        orders = decide_hire_orders(farm, day=10)
        self.assertTrue(all(o == ["HIRE"] for o in orders))
        self.assertGreater(len(orders), 0)

    def test_no_hire_once_target_met(self):
        # 5x5 NW quadrant owned (25 tiles), rest LOCKED -> target 5, already there.
        tiles = [["LOCKED"] * 10 for _ in range(10)]
        for y in range(5):
            for x in range(5):
                tiles[y][x] = None
        farm = make_farm(tiles=tiles, money=1000, hands=[1, 2, 3, 4, 5])
        self.assertEqual(decide_hire_orders(farm, day=10), [])


class TestDecideHireOrdersCashAware(unittest.TestCase):
    """Regression coverage for the v1.1 cash-aware gate (see
    experiments/replay_shape_v1_1_report.md): each candidate hire is
    priced at its actual fib cost (fib(0)=1, fib(1)=1, fib(2)=2, ...,
    fib(8)=34, fib(9)=55, fib(10)=89) before being queued."""

    def test_cheap_early_hires_go_through_even_near_the_cash_floor(self):
        # 3 candidates at already=0,1,2 cost 1+1+2=4 total - stays above
        # MIN_MONEY_TO_HIRE=20 even starting from just $25.
        farm = make_farm(money=25, hands=[])  # 100 default tiles -> target 15
        orders = decide_hire_orders(farm, day=10)
        self.assertEqual(len(orders), 3)

    def test_expensive_tail_hire_is_refused_even_with_nominal_floor_met(self):
        # already=10 -> next candidate costs fib(10)=89. $100 clears the
        # flat MIN_MONEY_TO_HIRE=20 floor but 100-89=11 < 20, so the old
        # (pre-v1.1) gate would have queued it and this one must not.
        farm = make_farm(money=100, hands=[1] * 10)  # 100 default tiles -> target 15
        self.assertEqual(decide_hire_orders(farm, day=10), [])

    def test_batch_is_truncated_mid_turn_once_unaffordable(self):
        # already=8 -> fib(8)=34 affordable (54-34=20, at the floor exactly),
        # fib(9)=55 is not (20-55<20) - exactly 1 hire, not the full batch.
        farm = make_farm(money=54, hands=[1] * 8)  # 100 default tiles -> target 15
        self.assertEqual(decide_hire_orders(farm, day=10), [["HIRE"]])


class TestDecideLandOrders(unittest.TestCase):
    def test_no_purchase_before_min_day(self):
        farm = make_farm(money=10_000, unlocked_quadrants=["NW"])
        self.assertEqual(decide_land_orders(farm, day=0), [])

    def test_no_purchase_without_cash(self):
        farm = make_farm(money=100, unlocked_quadrants=["NW"])
        self.assertEqual(decide_land_orders(farm, day=6), [])

    def test_buys_second_quadrant_once_eligible(self):
        farm = make_farm(money=10_000, unlocked_quadrants=["NW"])
        self.assertEqual(decide_land_orders(farm, day=6), [["BUY_LAND"]])

    def test_stops_at_target_purchase_count(self):
        farm = make_farm(money=10_000, unlocked_quadrants=["NW", "NE", "SW"])
        self.assertEqual(decide_land_orders(farm, day=20), [])


class TestChooseCrop(unittest.TestCase):
    def test_wheat_is_always_available_fallback(self):
        crop = choose_crop(day=0, seeds={}, money=1000, remaining_days=29)
        self.assertIn(crop, ("MELON", "WHEAT"))

    def test_nothing_returned_when_broke_and_seedless(self):
        crop = choose_crop(day=0, seeds={}, money=0, remaining_days=29)
        self.assertIsNone(crop)

    def test_skips_crops_that_cannot_mature_in_time(self):
        # MELON's first_yield_day (10) can't land with 2 days left; WHEAT's can.
        crop = choose_crop(day=27, seeds={}, money=1000, remaining_days=2)
        self.assertEqual(crop, "WHEAT")

    def test_prefers_already_held_seed_over_buying_a_different_crop(self):
        crop = choose_crop(day=0, seeds={"MELON": 2}, money=0, remaining_days=29)
        self.assertEqual(crop, "MELON")


class TestDecideSeedOrders(unittest.TestCase):
    def test_buys_seed_for_chosen_crop_when_none_held(self):
        farm = make_farm(money=1000)
        private = {"seeds": {}}
        orders = decide_seed_orders(farm, private, day=0)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0][0], "BUY_SEED")

    def test_stops_once_stockpile_cap_reached(self):
        farm = make_farm(money=1000)
        private = {"seeds": {"WHEAT": 3, "MELON": 3, "STRAWBERRY": 3}}
        self.assertEqual(decide_seed_orders(farm, private, day=0), [])

    def test_no_seed_order_when_cannot_afford(self):
        farm = make_farm(money=0)
        private = {"seeds": {}}
        self.assertEqual(decide_seed_orders(farm, private, day=0), [])


class TestChooseAnimalToBuild(unittest.TestCase):
    """Regression coverage for the two bugs found in this function: wrong
    per-structure capacity math (max_held misread as animals-per-structure)
    and a cash gate that blocked housing an already-purchased animal."""

    def test_houses_a_shed_animal_regardless_of_cash(self):
        farm = make_farm(money=0)  # below MIN_CASH_RESERVE_FOR_ANIMALS
        private = {"shed": {"COW": 1}}
        result = choose_animal_to_build(farm, private, board_size=10, day=10, pending_builds=0)
        self.assertEqual(result, "COW")

    def test_no_build_before_min_day(self):
        farm = make_farm(money=10_000)
        private = {"shed": {}}
        result = choose_animal_to_build(farm, private, board_size=10, day=0, pending_builds=0)
        self.assertIsNone(result)

    def test_stops_at_one_structure_per_animal_up_to_target(self):
        # 9 filled structures (== TARGET_TOTAL_ANIMALS) must not request a 10th,
        # even though max_held (a yield-accumulation cap, not headcount) is larger.
        tiles = [[None] * 10 for _ in range(10)]
        for i in range(TARGET_TOTAL_ANIMALS):
            tiles[0][i] = {"kind": "PASTURE", "animal": "COW"}
        farm = make_farm(tiles=tiles, money=10_000)
        private = {"shed": {}}
        result = choose_animal_to_build(farm, private, board_size=10, day=10, pending_builds=0)
        self.assertIsNone(result)

    def test_no_second_pending_build_at_once(self):
        farm = make_farm(money=10_000)
        private = {"shed": {}}
        result = choose_animal_to_build(farm, private, board_size=10, day=10, pending_builds=1)
        self.assertIsNone(result)


class TestScanAnimalStructures(unittest.TestCase):
    def test_counts_filled_and_unfilled_separately(self):
        tiles = [[None] * 4 for _ in range(4)]
        tiles[0][0] = {"kind": "PASTURE", "animal": "COW"}
        tiles[0][1] = {"kind": "PASTURE"}
        farm = make_farm(tiles=tiles)
        filled, unfilled = scan_animal_structures(farm, board_size=4)
        self.assertEqual((filled, unfilled), (1, 1))


class TestFindNearestTargetEmptyTask(unittest.TestCase):
    """Regression coverage: an earlier draft dropped the "empty" task
    entirely, so units only ever planted/built when already standing on
    empty ground by accident (measured: 4-9/75 tiles ever planted)."""

    def test_finds_nearest_empty_tile(self):
        tiles = [[{"kind": "PLANT"}] * 4 for _ in range(4)]
        tiles[2][2] = None
        farm = make_farm(tiles=tiles)
        target = find_nearest_target(farm, board_size=4, fx=0, fy=0, task="empty", day=0)
        self.assertEqual(target, (2, 2))

    def test_no_empty_target_when_fully_occupied(self):
        tiles = [[{"kind": "PLANT"}] * 4 for _ in range(4)]
        farm = make_farm(tiles=tiles)
        target = find_nearest_target(farm, board_size=4, fx=0, fy=0, task="empty", day=0)
        self.assertIsNone(target)


if __name__ == "__main__":
    unittest.main()
