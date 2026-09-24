"""Unit tests for the TRIM_SEED overlay on `agents/farm2945_trim.py`.

The overlay is a pure post-processor on the action dict the verbatim public base
already returned: it only ever *lowers the quantity* of a `BUY_SEED` order, never
adds, removes or reorders one. Every test here builds a hand-made observation
plus the market list the base would have emitted and calls `_trim_market`
directly - no 720-turn episode, no call into the 5,766-line base.

Three properties carry the whole design and each has a test below.

1. THE ORDER LIST KEEPS ITS LENGTH AND ITS ORDER. `_process_market` walks both
   players' lists by index in lockstep, so deleting an order moves every later
   order one index earlier and changes when our SELLs price against the
   opponent's. A fully trimmed order is rewritten as quantity 0 (which
   `_parse_order` reads as None and the index loop skips) instead of removed.

2. THE CAP NEVER BINDS BEFORE A CROP'S LAST PLANTABLE DAY. Nothing in the
   growing season is touched.

3. CAPACITY COUNTS THE TILES THAT FREE UP INSIDE THE SAME DAY. `_apply_unit_action`
   clears a non-`ongoing` crop's tile on HARVEST, so the base harvests and
   replants the same tile within a day; a capacity count that saw only the
   already-empty tiles starved a CARROT planting on 7 of 16 self-play seeds
   (docs/ENDGAME/dead_spend.md).
"""

import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_PATH = os.path.join(ROOT, "agents", "farm2945_trim.py")


def _load():
    spec = importlib.util.spec_from_file_location("farm2945_trim", AGENT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TRIM = _load()


def _tiles(empty=0, ready=(), weeds=0, growing=0, locked=0, day=27):
    """10x10 row-major grid.

    `empty` bare tiles, `weeds` WEED tiles, `growing` one-shot plants that are
    NOT harvest-ready, `locked` LOCKED tiles, and one PLANT per entry of
    `ready`, each a (crop, planted_day) that is ready to harvest today.
    """
    grid = [["LOCKED"] * 10 for _ in range(10)]
    cells = [(x, y) for y in range(10) for x in range(10)]
    i = 0

    def put(v):
        nonlocal i
        x, y = cells[i]
        grid[y][x] = v
        i += 1

    for _ in range(empty):
        put(None)
    for crop, planted in ready:
        put({"kind": "PLANT", "crop": crop, "planted_day": planted, "yield_units": 3})
    for _ in range(weeds):
        put({"kind": "WEED"})
    for _ in range(growing):
        put({"kind": "PLANT", "crop": "CARROT", "planted_day": day, "yield_units": 0})
    return grid


def _obs(day, grid, seeds=None, money=50000):
    return {
        "player": 0,
        "day": day,
        "hour": 0,
        "step": day * 24,
        "farms": [{"tiles": grid, "farmer": [4, 4], "hands": [], "money": money}],
        "private": {"seeds": dict(seeds or {}), "shed": {}},
    }


def _action(market, farmer=("PASS",), hands=()):
    return {"farmer": list(farmer),
            "hands": [list(h) for h in hands],
            "market": [list(o) for o in market]}


class TestCapacity(unittest.TestCase):
    def test_counts_empty_weed_and_harvest_ready_one_shot(self):
        grid = _tiles(empty=3, weeds=2, ready=[("CARROT", 25), ("WHEAT", 25)], growing=4)
        farm = {"tiles": grid}
        # 3 empty + 2 weeds + 2 harvest-ready one-shot = 7; the 4 immature
        # CARROTs (planted today) and every LOCKED tile contribute nothing.
        self.assertEqual(TRIM._trim_capacity(farm, 27), 7)

    def test_ongoing_crop_is_not_capacity(self):
        # STRAWBERRY is `ongoing`: HARVEST leaves the tile occupied, so it can
        # never free up for a replant.
        grid = _tiles(empty=1, ready=[("STRAWBERRY", 10)])
        self.assertEqual(TRIM._trim_capacity({"tiles": grid}, 27), 1)


class TestNoOpBeforeLastPlantableDay(unittest.TestCase):
    def test_untouched_mid_season(self):
        # WHEAT's last plantable day is 29 - first_yield_day(2) = 27.
        act = _action([["BUY_SEED", "WHEAT", 40], ["SELL", "MELON", 15]])
        obs = _obs(26, _tiles(empty=0), seeds={"WHEAT": 0})
        out = TRIM._trim_market(obs, act)
        self.assertIs(out, act)
        self.assertEqual(out["market"], [["BUY_SEED", "WHEAT", 40], ["SELL", "MELON", 15]])

    def test_untouched_for_a_crop_whose_window_is_still_open(self):
        # MELON's last plantable day is 29 - 10 = 19; on day 18 nothing is capped.
        act = _action([["BUY_SEED", "MELON", 12]])
        out = TRIM._trim_market(_obs(18, _tiles(empty=0)), act)
        self.assertIs(out, act)


class TestCapBinds(unittest.TestCase):
    def test_trims_down_to_capacity_and_keeps_the_index(self):
        # Day 27 (WHEAT's last plantable day), capacity 1 empty tile + slack 2,
        # already holding 1 seed -> room for 2 more.
        TRIM._TRIM_REPORT.update(dict.fromkeys(TRIM._TRIM_REPORT, 0))
        act = _action([["SELL", "MILK", 9], ["BUY_SEED", "WHEAT", 10], ["HIRE"]])
        out = TRIM._trim_market(_obs(27, _tiles(empty=1), seeds={"WHEAT": 1}), act)
        self.assertEqual(out["market"],
                         [["SELL", "MILK", 9], ["BUY_SEED", "WHEAT", 2], ["HIRE"]])
        self.assertEqual(TRIM._TRIM_REPORT["trim_units"], 8)
        self.assertEqual(TRIM._TRIM_REPORT["trim_cash"], 80)

    def test_zeroes_rather_than_deletes_past_the_last_plantable_day(self):
        # Day 28: a WHEAT planted now first yields on day 30, outside the season,
        # so the cap is 0 regardless of capacity - and the order must stay in the
        # list at index 1 so the HIRE behind it does not move.
        TRIM._TRIM_REPORT.update(dict.fromkeys(TRIM._TRIM_REPORT, 0))
        market = [["SELL", "WOOL", 20], ["BUY_SEED", "CARROT", 8], ["HIRE"],
                  ["SELL", "MILK", 6]]
        out = TRIM._trim_market(_obs(28, _tiles(empty=20)), _action(market))
        self.assertEqual(len(out["market"]), 4)
        self.assertEqual(out["market"][1], ["BUY_SEED", "CARROT", 0])
        self.assertEqual(out["market"][2], ["HIRE"])
        self.assertEqual(TRIM._TRIM_REPORT["trim_zeroed"], 1)
        self.assertEqual(TRIM._TRIM_REPORT["trim_cash"], 160)

    def test_plants_emitted_this_turn_raise_the_room(self):
        # Two units PLANT CARROT this turn; those two seeds are consumed before
        # any later planting, so the buy that replaces them is not dead.
        act = _action([["BUY_SEED", "CARROT", 4]],
                      hands=(["PLANT", "CARROT"], ["PLANT", "CARROT"]))
        out = TRIM._trim_market(_obs(27, _tiles(empty=0), seeds={"CARROT": 2}), act)
        # capacity 0 + slack 2 + 2 planned - 2 held = 2
        self.assertEqual(out["market"], [["BUY_SEED", "CARROT", 2]])

    def test_several_orders_of_one_crop_share_the_same_room(self):
        act = _action([["BUY_SEED", "CARROT", 3], ["BUY_SEED", "CARROT", 3]])
        out = TRIM._trim_market(_obs(27, _tiles(empty=0), seeds={}), act)
        self.assertEqual(out["market"],
                         [["BUY_SEED", "CARROT", 2], ["BUY_SEED", "CARROT", 0]])


class TestNeverStarvesOrMutates(unittest.TestCase):
    def test_a_plant_action_is_never_touched(self):
        act = _action([["BUY_SEED", "CARROT", 8]],
                      farmer=("PLANT", "CARROT"), hands=(["WATER"],))
        out = TRIM._trim_market(_obs(28, _tiles(empty=9)), act)
        self.assertEqual(out["farmer"], ["PLANT", "CARROT"])
        self.assertEqual(out["hands"], [["WATER"]])

    def test_held_seed_never_falls_below_what_the_turn_plants(self):
        # Three PLANT CARROTs this turn against 3 held seeds: the engine drops
        # ALL of them if demand ever exceeds held stock, so the cap must not be
        # able to reduce held stock - it only ever lowers a *purchase*.
        obs = _obs(28, _tiles(empty=0), seeds={"CARROT": 3})
        act = _action([["BUY_SEED", "CARROT", 5]],
                      hands=(["PLANT", "CARROT"], ["PLANT", "CARROT"], ["PLANT", "CARROT"]))
        out = TRIM._trim_market(obs, act)
        self.assertEqual(obs["private"]["seeds"]["CARROT"], 3)
        self.assertEqual(out["market"][0][2], 0)

    def test_non_seed_orders_are_left_alone(self):
        market = [["BUY_PRODUCT", "WHEAT", 6], ["BUY_ANIMAL", "COW", 1],
                  ["BUY_LAND"], ["SELL", "EGG", 2000]]
        out = TRIM._trim_market(_obs(29, _tiles(empty=0)), _action(market))
        self.assertEqual(out["market"], market)

    def test_malformed_quantity_is_passed_through(self):
        out = TRIM._trim_market(_obs(29, _tiles(empty=0)),
                                _action([["BUY_SEED", "CARROT", "x"]]))
        self.assertEqual(out["market"], [["BUY_SEED", "CARROT", "x"]])


class TestFlagOff(unittest.TestCase):
    def test_flag_off_returns_the_base_action_unchanged(self):
        # Stub the base out: `agent` must hand back the parent's exact object
        # when the flag is off, and cap it when it is on.
        act = _action([["BUY_SEED", "CARROT", 8], ["HIRE"]])
        obs = _obs(29, _tiles(empty=9))
        parent = TRIM._TRIM_PARENT
        try:
            TRIM._TRIM_PARENT = lambda o, c=None: act
            TRIM.TRIM_SEED = False
            self.assertIs(TRIM.agent(obs), act)
            TRIM.TRIM_SEED = True
            out = TRIM.agent(obs)
            self.assertIsNot(out, act)
            self.assertEqual(out["market"], [["BUY_SEED", "CARROT", 0], ["HIRE"]])
            self.assertEqual(act["market"], [["BUY_SEED", "CARROT", 8], ["HIRE"]])
        finally:
            TRIM._TRIM_PARENT = parent
            TRIM.TRIM_SEED = True

    def test_agent_is_the_last_callable_in_the_module(self):
        # kaggle_environments/agent.py:64 picks the LAST callable in the module
        # namespace; anything callable defined after `agent` hijacks the entry point.
        names = [k for k, v in vars(TRIM).items() if callable(v)]
        self.assertEqual(names[-1], "agent")


if __name__ == "__main__":
    unittest.main()
