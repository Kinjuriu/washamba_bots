"""Unit tests for the late-game overlay on `agents/farm2945_late.py`.

The overlay is a pure post-processor: it takes the action dict the verbatim
public base already returned and renames ops in it. So every test here builds a
hand-made observation plus the action the tape would have emitted, calls one
lever directly, and asserts the exact emitted diff - no 720-turn episode, no
call into the 5,766-line base.

The one thing each lever must never do is rename a `BUY_SEED` without renaming
the matching `PLANT`: the engine drops ALL `PLANT` requests for a crop whose
turn demand exceeds held seed (`kaggriculture.py:920-931`), so a half-applied
rename costs the whole turn's planting and leaves a tile the tape then waters
all season for nothing. The guard/abort/seed-short tests below are that rule.
"""

import copy
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_PATH = os.path.join(ROOT, "agents", "farm2945_late.py")


def _load():
    spec = importlib.util.spec_from_file_location("farm2945_late", AGENT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


LATE = _load()


def _grid(strawberry=0, locked=()):
    """10x10 row-major tile grid: `strawberry` live STRAWBERRY plants, plus the
    given (x, y) tiles marked LOCKED. Everything else empty."""
    tiles = [[None] * 10 for _ in range(10)]
    placed = 0
    for y in range(10):
        for x in range(10):
            if placed >= strawberry:
                break
            if (x, y) in locked:
                continue
            tiles[y][x] = {"kind": "PLANT", "crop": "STRAWBERRY"}
            placed += 1
    for (x, y) in locked:
        tiles[y][x] = "LOCKED"
    return tiles


def _obs(day, tiles, money=15000, seeds=None, farmer=(0, 0), hands=()):
    return {
        "player": 0,
        "day": day,
        "step": day * 24,
        "farms": [{"tiles": tiles, "farmer": list(farmer),
                   "hands": [list(h) for h in hands], "money": money}],
        "private": {"seeds": dict(seeds or {}), "shed": {}},
    }


def _action(farmer, hands, market):
    return {"farmer": list(farmer),
            "hands": [list(h) for h in hands],
            "market": [list(o) for o in market]}


class _LeverCase(unittest.TestCase):
    def setUp(self):
        LATE._LATE_STATES.clear()
        for k in LATE._LATE_REPORT:
            LATE._LATE_REPORT[k] = 0
        self.st = LATE._late_state(0)


class TestLever1Tomato(_LeverCase):
    """Day 11: the freshly bought third quadrant goes in as TOMATO."""

    TARGETS = [(1, 5), (2, 5)]

    def _prime_day10(self):
        LATE.late_observe(_obs(10, _grid(20, locked=self.TARGETS)), self.st)
        self.assertEqual(self.st["locked_d10"], set(self.TARGETS))

    def _day11(self, money=15000, seeds=None, strawberry=20):
        return _obs(11, _grid(strawberry), money=money,
                    seeds=seeds if seeds is not None else {"TOMATO": 2},
                    farmer=self.TARGETS[0], hands=[self.TARGETS[1]])

    def test_renames_plant_and_buy_seed_and_nothing_else(self):
        self._prime_day10()
        action = _action(["PLANT", "STRAWBERRY"], [["PLANT", "STRAWBERRY"]],
                         [["BUY_SEED", "STRAWBERRY", 2], ["SELL", "WHEAT", 5],
                          ["HIRE"]])
        before = copy.deepcopy(action)
        out = LATE.late_lever1_tomato(self._day11(), action, self.st)

        self.assertEqual(out["farmer"], ["PLANT", "TOMATO"])
        self.assertEqual(out["hands"], [["PLANT", "TOMATO"]])
        # market renamed 1:1 in place: same length, same indices, same other
        # orders - market orders settle in list-index lockstep, so a prepend or
        # a drop would reindex every later order against the opponent's.
        self.assertEqual(out["market"],
                         [["BUY_SEED", "TOMATO", 2], ["SELL", "WHEAT", 5], ["HIRE"]])
        self.assertEqual(len(out["market"]), len(before["market"]))
        self.assertEqual(action, before, "input action must not be mutated")
        self.assertEqual(LATE._LATE_REPORT["l1_plants"], 2)
        self.assertEqual(LATE._LATE_REPORT["l1_buys"], 2)

    def test_no_op_when_bank_below_guard(self):
        self._prime_day10()
        action = _action(["PLANT", "STRAWBERRY"], [["PLANT", "STRAWBERRY"]],
                         [["BUY_SEED", "STRAWBERRY", 2]])
        before = copy.deepcopy(action)
        out = LATE.late_lever1_tomato(self._day11(money=1999), action, self.st)
        self.assertEqual(out, before)
        self.assertEqual(LATE._LATE_REPORT["l1_blocked"], 1)

    def test_no_op_when_too_few_live_strawberry_tiles(self):
        self._prime_day10()
        out = LATE.late_lever1_tomato(
            self._day11(strawberry=19),
            _action(["PLANT", "STRAWBERRY"], [], [["BUY_SEED", "STRAWBERRY", 1]]),
            self.st)
        self.assertEqual(out["farmer"], ["PLANT", "STRAWBERRY"])
        self.assertEqual(out["market"], [["BUY_SEED", "STRAWBERRY", 1]])

    def test_no_op_on_any_day_but_11(self):
        self._prime_day10()
        for day in (10, 12, 20):
            out = LATE.late_lever1_tomato(
                _obs(day, _grid(20), farmer=self.TARGETS[0]),
                _action(["PLANT", "STRAWBERRY"], [], [["BUY_SEED", "STRAWBERRY", 1]]),
                self.st)
            self.assertEqual(out["farmer"], ["PLANT", "STRAWBERRY"], day)

    def test_aborts_when_a_strawberry_plant_is_off_the_quadrant(self):
        """The whole lever rests on 'every day-11 strawberry plant is on a tile
        that was LOCKED at day 10' (13/13 on 19 of 19 episodes). If that ever
        breaks, rename nothing - the off-quadrant plant would otherwise be
        starved of the seed whose purchase we renamed away."""
        self._prime_day10()
        obs = _obs(11, _grid(20), farmer=self.TARGETS[0], hands=[(9, 9)],
                   seeds={"TOMATO": 2})
        action = _action(["PLANT", "STRAWBERRY"], [["PLANT", "STRAWBERRY"]],
                         [["BUY_SEED", "STRAWBERRY", 2]])
        before = copy.deepcopy(action)
        out = LATE.late_lever1_tomato(obs, action, self.st)
        self.assertEqual(out, before)
        self.assertEqual(LATE._LATE_REPORT["l1_off_quadrant"], 1)
        self.assertTrue(self.st["l1_abort"])

    def test_no_rename_when_tomato_seed_would_not_cover_the_turn(self):
        self._prime_day10()
        obs = self._day11(seeds={"TOMATO": 1})   # two plants, one seed
        action = _action(["PLANT", "STRAWBERRY"], [["PLANT", "STRAWBERRY"]], [])
        before = copy.deepcopy(action)
        out = LATE.late_lever1_tomato(obs, action, self.st)
        self.assertEqual(out, before)
        self.assertEqual(LATE._LATE_REPORT["l1_seed_short"], 2)


class TestLever2Melon(_LeverCase):
    """Day 10: the 7 ex-melon tiles are replanted MELON, not WHEAT."""

    TARGETS = [(3, 1), (4, 1)]

    def _prime_early(self):
        tiles = [[None] * 10 for _ in range(10)]
        for (x, y) in self.TARGETS:
            tiles[y][x] = {"kind": "PLANT", "crop": "MELON"}
        LATE.late_observe(_obs(5, tiles), self.st)
        self.assertEqual(self.st["melon_tiles"], set(self.TARGETS))

    def test_renames_plant_wheat_and_buy_seed_wheat(self):
        self._prime_early()
        obs = _obs(10, _grid(0), money=2500, seeds={"MELON": 2},
                   farmer=self.TARGETS[0], hands=[self.TARGETS[1]])
        action = _action(["PLANT", "WHEAT"], [["PLANT", "WHEAT"]],
                         [["SELL", "MELON", 12], ["BUY_SEED", "WHEAT", 2]])
        out = LATE.late_lever2_melon(obs, action, self.st)
        self.assertEqual(out["farmer"], ["PLANT", "MELON"])
        self.assertEqual(out["hands"], [["PLANT", "MELON"]])
        self.assertEqual(out["market"],
                         [["SELL", "MELON", 12], ["BUY_SEED", "MELON", 2]])

    def test_no_op_when_bank_below_guard(self):
        self._prime_early()
        obs = _obs(10, _grid(0), money=1999, seeds={"MELON": 2},
                   farmer=self.TARGETS[0])
        action = _action(["PLANT", "WHEAT"], [], [["BUY_SEED", "WHEAT", 1]])
        before = copy.deepcopy(action)
        self.assertEqual(LATE.late_lever2_melon(obs, action, self.st), before)
        self.assertEqual(LATE._LATE_REPORT["l2_blocked"], 1)

    def test_leaves_wheat_plants_off_the_melon_block_alone(self):
        self._prime_early()
        obs = _obs(10, _grid(0), money=2500, seeds={"MELON": 1}, farmer=(9, 9))
        action = _action(["PLANT", "WHEAT"], [], [["BUY_SEED", "WHEAT", 1]])
        before = copy.deepcopy(action)
        self.assertEqual(LATE.late_lever2_melon(obs, action, self.st), before)
        self.assertEqual(LATE._LATE_REPORT["l2_off_melon"], 1)


class TestOverlayIsInert(_LeverCase):
    """With both flags off - and on every turn outside the two lever days - the
    overlay must hand the base's action back untouched."""

    def test_both_levers_off_is_byte_identical(self):
        flags = (LATE.LATE_TOMATO_D11, LATE.LATE_MELON_REPLANT)
        LATE.LATE_TOMATO_D11 = LATE.LATE_MELON_REPLANT = False
        try:
            obs = _obs(11, _grid(20), farmer=(1, 5))
            action = _action(["PLANT", "STRAWBERRY"], [],
                             [["BUY_SEED", "STRAWBERRY", 1]])
            before = copy.deepcopy(action)
            st = LATE._late_state(0)
            LATE.late_observe(obs, st)
            out = action
            if LATE.LATE_MELON_REPLANT:
                out = LATE.late_lever2_melon(obs, out, st)
            if LATE.LATE_TOMATO_D11:
                out = LATE.late_lever1_tomato(obs, out, st)
            self.assertIs(out, action)
            self.assertEqual(out, before)
        finally:
            LATE.LATE_TOMATO_D11, LATE.LATE_MELON_REPLANT = flags

    def test_agent_is_the_last_callable_in_the_module(self):
        callables = [name for name, value in vars(LATE).items() if callable(value)]
        self.assertEqual(callables[-1], "agent")

    def test_observe_only_snapshots_up_to_day_10(self):
        st = LATE._late_state(0)
        LATE.late_observe(_obs(11, _grid(0, locked=[(0, 9)])), st)
        self.assertIsNone(st["locked_d10"])
        self.assertIsNone(st["melon_tiles"])


if __name__ == "__main__":
    unittest.main()
