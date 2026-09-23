"""Unit tests for agents/farm2945_v3.py - the T5e "goose tail" overlay on
public_farm2945.

Stdlib unittest (pytest is not installed in this repo). These cover the overlay's
own invariants: the engine facts the lever rests on, the exact emitted diff, the
no-added/no-moved-order rule, the break latch, and byte-identity when the flag is
off. The strategy verdict is in docs/ENDGAME/v3_results.md, measured on
experiments/endgame/ladder_replay.py, self-play and head to head.
"""

import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V3_PATH = os.path.join(ROOT, "agents", "farm2945_v3.py")
BASE_PATH = os.path.join(ROOT, "agents", "public_farm2945.py")
ENGINE_PATH = os.path.join(
    ROOT, ".venv", "Lib", "site-packages", "kaggle_environments", "envs",
    "kaggriculture", "kaggriculture.py")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V3 = _load(V3_PATH, "farm2945_v3_under_test")


class TestOverlayShape(unittest.TestCase):
    """The base must be embedded verbatim and `agent` must be the last callable."""

    def test_base_is_embedded_verbatim(self):
        self.assertIn(_read(BASE_PATH), _read(V3_PATH))

    def test_agent_is_the_last_callable(self):
        # the framework picks [v for v in ns.values() if callable(v)][-1]
        ns = {}
        exec(compile(_read(V3_PATH), "farm2945_v3.py", "exec"), ns)
        last = [v for v in ns.values() if callable(v)][-1]
        self.assertIs(last, ns["agent"])

    def test_ships_with_the_lever_off(self):
        self.assertEqual(V3.V3_GOOSE_TAIL_K, 0)


class TestEngineFactsTheLeverRestsOn(unittest.TestCase):
    """(a), (b) and (c) from the overlay header, checked against the installed
    engine rather than against the docs."""

    @classmethod
    def setUpClass(cls):
        cls.engine = _load(ENGINE_PATH, "kaggriculture_under_test")

    def test_a_goose_needs_a_coop_and_cow_sheep_a_pasture(self):
        animals = self.engine.ANIMALS
        self.assertEqual(animals["GOOSE"]["structure"], "COOP")
        self.assertEqual(animals["COW"]["structure"], "PASTURE")
        self.assertEqual(animals["SHEEP"]["structure"], "PASTURE")

    def _act(self, tile, action, inv, day=10):
        """One unit action through the real engine on a real 10x10 board, with the
        unit at (0, 0) - away from the shed-access tiles, because a PLACE whose
        structure does not match falls through to the SHED-DROP path rather than
        simply returning (kaggriculture.py:377-400).  Signature, verified:
        _apply_unit_action(farm, private, idx, action, board_size, day, turns_per_day)."""
        tiles = [[None] * 10 for _ in range(10)]
        tiles[0][0] = tile
        farm = {"tiles": tiles, "farmer": [0, 0], "hands": [], "money": 0}
        private = {"inventories": [dict(inv)], "shed": {}, "seeds": {}}
        self.engine._apply_unit_action(farm, private, 0, action, 10, day, 24)
        return farm, private["inventories"][0]

    def test_a_place_onto_the_wrong_structure_is_a_silent_no_op(self):
        """This is why the BUILD rename is mandatory and not cosmetic."""
        farm, inv = self._act({"kind": "PASTURE"}, ["PLACE", "GOOSE", 1], {"GOOSE": 1})
        self.assertEqual(farm["tiles"][0][0], {"kind": "PASTURE"})   # unchanged
        self.assertEqual(inv["GOOSE"], 1)                            # not consumed
        farm, inv = self._act({"kind": "COOP"}, ["PLACE", "GOOSE", 1], {"GOOSE": 1})
        self.assertEqual(farm["tiles"][0][0]["animal"], "GOOSE")
        self.assertEqual(inv.get("GOOSE", 0), 0)

    def test_b_production_is_collected_by_an_explicit_harvest_and_capped(self):
        animals = self.engine.ANIMALS
        # cap: GOOSE holds 4, COW/SHEEP 6 - production past the cap is discarded
        self.assertEqual(animals["GOOSE"]["max_held"], 4)
        self.assertEqual(animals["COW"]["max_held"], 6)
        self.assertEqual(animals["SHEEP"]["max_held"], 6)
        # cadence: a goose produces every day, a sheep every third
        self.assertEqual(animals["GOOSE"]["interval"], 1)
        self.assertEqual(animals["SHEEP"]["interval"], 3)
        self.assertEqual(animals["COW"]["interval"], 2)
        # collection is a HARVEST unit action on the animal tile
        tile = self.engine._new_animal("GOOSE", 0)
        tile["yield_units"] = 3
        farm, inv = self._act(tile, ["HARVEST"], {})
        self.assertEqual(inv.get("EGG"), 3)
        self.assertEqual(farm["tiles"][0][0]["yield_units"], 0)

    def test_b_a_goose_on_a_three_day_cadence_strands_production(self):
        """Why the collection cadence matters: a fed+cared goose left uncollected
        holds 4, the cap - a sheep on the same visit pattern banks 6."""
        eng = self.engine
        farm = {"tiles": [[eng._new_animal("GOOSE", 0)]]}
        for day in range(4, 12):
            farm["tiles"][0][0]["fed_today"] = True
            farm["tiles"][0][0]["cared_today"] = True
            eng._daily_refresh_animals(farm, day)
        self.assertEqual(farm["tiles"][0][0]["yield_units"],
                         eng.ANIMALS["GOOSE"]["max_held"])

    def test_c_feed_costs_one_wheat_for_every_species(self):
        for species in ("GOOSE", "COW", "SHEEP"):
            tile = self.engine._new_animal(species, 0)
            farm, inv = self._act(tile, ["FEED"], {"WHEAT": 3}, day=5)
            self.assertEqual(inv["WHEAT"], 2, species)
            self.assertTrue(farm["tiles"][0][0]["fed_today"], species)


# --------------------------------------------------------------------------- #
#  The planner and the emitted diff.  A miniature route tape stands in for the
#  real one so the expected rewrite set can be written out by hand; the shapes
#  are exactly those the real tape uses (see docs/ENDGAME/v3_results.md §2).
# --------------------------------------------------------------------------- #

def _tape_step(farmer=None, hands=(), market=()):
    return {"farmer": list(farmer) if farmer else ["PASS"],
            "hands": [list(h) for h in hands],
            "market": [list(o) for o in market]}


def _mini_tape():
    """A 300-step tape with three animal purchases:
         t=10  BUY_ANIMAL COW 1    -> unit 1 PICKUP t=12, BUILD t=14, PLACE t=15
                                      (clean: same unit, same day)
         t=40  BUY_ANIMAL SHEEP 1  -> unit 1 PICKUP t=42, PLACE t=60 with the
                                      BUILD back on day 1 (NOT clean)
         t=200 BUY_ANIMAL SHEEP 1  -> unit 2 PICKUP t=202, BUILD t=203, PLACE 204
                                      (clean)
    """
    tape = [_tape_step() for _ in range(300)]
    tape[10]["market"] = [["BUY_ANIMAL", "COW", 1]]
    tape[12]["hands"] = [["PICKUP", "COW"]]
    tape[14]["hands"] = [["BUILD_PASTURE"]]
    tape[15]["hands"] = [["PLACE", "COW"]]
    tape[20]["hands"] = [["BUILD_PASTURE"]]                # day 0, for the day-2 sheep
    tape[40]["market"] = [["BUY_ANIMAL", "SHEEP", 1]]
    tape[42]["hands"] = [["PICKUP", "SHEEP"]]
    tape[60]["hands"] = [["PLACE", "SHEEP"]]
    tape[200]["market"] = [["BUY_ANIMAL", "SHEEP", 1]]
    tape[202]["hands"] = [["PASS"], ["PICKUP", "SHEEP"]]
    tape[203]["hands"] = [["PASS"], ["BUILD_PASTURE"]]
    tape[204]["hands"] = [["PASS"], ["PLACE", "SHEEP"]]
    return tape


def _obs(step, hands=(), tiles=None, player=0):
    n = 10
    return {
        "step": step,
        "player": player,
        "farms": [{
            "tiles": tiles or [[None] * n for _ in range(n)],
            "farmer": [4, 4],
            "hands": [list(h) for h in hands],
            "money": 20000,
            "unlocked_quadrants": ["NW"],
            "hires_today": 0,
        }],
        "market": {"prices": {}, "inventory": {}},
        "private": {"seeds": {}, "shed": {}, "inventories": [{}] * (1 + len(hands))},
        "town": {"unlocked_shops": []},
    }


class _MiniTape:
    """Stands in for _IMPL.chassis for the duration of one test."""

    def __init__(self, tape):
        self.routes = {7: tape}
        self.players = {0: {"route": 7}}


class TestPlanner(unittest.TestCase):
    def setUp(self):
        self.tape = _mini_tape()
        self._real = V3._IMPL.chassis
        V3._IMPL.chassis = _MiniTape(self.tape)
        V3._V3_STATE.clear()
        for key in V3._V3_REPORT:
            V3._V3_REPORT[key] = 0 if not isinstance(V3._V3_REPORT[key], str) else ""

    def tearDown(self):
        V3._IMPL.chassis = self._real

    def test_k1_takes_the_last_clean_order_only(self):
        plan = V3._v3_plan(_obs(0, hands=[[4, 4], [4, 4]]), 1)
        self.assertIsNotNone(plan)
        self.assertEqual(V3._V3_REPORT["v3_targets"], "d8:SHEEP*1")
        self.assertEqual(sorted(plan["cmds"]),
                         [(202, 2), (203, 2), (204, 2)])
        self.assertEqual(plan["market"], {200: {"SHEEP"}})

    def test_k2_skips_the_unresolvable_order_and_reaches_the_cow(self):
        """The t=40 sheep's pasture is built on another day, so it cannot be a
        1:1 rename; the walk skips it rather than guessing."""
        plan = V3._v3_plan(_obs(0, hands=[[4, 4], [4, 4]]), 2)
        self.assertIsNotNone(plan)
        self.assertEqual(V3._V3_REPORT["v3_targets"], "d8:SHEEP*1,d0:COW*1")
        self.assertEqual(sorted(plan["cmds"]),
                         [(12, 1), (14, 1), (15, 1), (202, 2), (203, 2), (204, 2)])
        self.assertEqual(plan["market"], {10: {"COW"}, 200: {"SHEEP"}})

    def test_k3_is_unsatisfiable_and_plans_nothing(self):
        self.assertIsNone(V3._v3_plan(_obs(0, hands=[[4, 4], [4, 4]]), 3))
        self.assertIn("short(2/3)", V3._V3_REPORT["v3_targets"])

    def test_a_pickup_carrying_an_animal_we_keep_is_skipped(self):
        """A PICKUP of 2 cannot be split 1:1, so that order is refused and the walk
        falls back to the next resolvable one instead of guessing."""
        self.tape[202]["hands"] = [["PASS"], ["PICKUP", "SHEEP", 2]]
        plan = V3._v3_plan(_obs(0, hands=[[4, 4], [4, 4]]), 1)
        self.assertEqual(V3._V3_REPORT["v3_targets"], "d0:COW*1")
        self.assertEqual(sorted(plan["cmds"]), [(12, 1), (14, 1), (15, 1)])


class TestEmittedDiff(unittest.TestCase):
    """The exact ops that change, and - just as important - that nothing else does."""

    def setUp(self):
        self.tape = _mini_tape()
        self._real = V3._IMPL.chassis
        V3._IMPL.chassis = _MiniTape(self.tape)
        V3._V3_STATE.clear()
        self.plan = V3._v3_plan(_obs(0, hands=[[4, 4], [4, 4]]), 1)
        self.st = {"step": -1, "plan": self.plan, "broken": False,
                   "ready": True, "sites": {}}
        V3._V3_REPORT["v3_rewrites"] = 0

    def tearDown(self):
        V3._IMPL.chassis = self._real

    def _apply(self, step, hands, cmds, market=()):
        obs = _obs(step, hands=hands)
        action = {"farmer": ["PASS"], "hands": [list(c) for c in cmds],
                  "market": [list(o) for o in market]}
        return action, V3._v3_apply(obs, action, self.st)

    def test_buy_order_is_renamed_in_place_and_nothing_is_added_or_moved(self):
        before, after = self._apply(
            200, [[1, 1], [2, 2]], [["PASS"], ["PASS"]],
            market=[["SELL", "WHEAT", 5], ["BUY_ANIMAL", "SHEEP", 1], ["HIRE"]])
        self.assertEqual(after["market"],
                         [["SELL", "WHEAT", 5], ["BUY_ANIMAL", "GOOSE", 1], ["HIRE"]])
        self.assertEqual(len(after["market"]), len(before["market"]))

    def test_the_full_chain_is_four_renames_and_only_four(self):
        _b, a1 = self._apply(202, [[1, 1], [3, 3]], [["PASS"], ["PICKUP", "SHEEP"]])
        self.assertEqual(a1["hands"], [["PASS"], ["PICKUP", "GOOSE"]])
        _b, a2 = self._apply(203, [[1, 1], [3, 3]], [["PASS"], ["BUILD_PASTURE"]])
        self.assertEqual(a2["hands"], [["PASS"], ["BUILD_COOP"]])
        _b, a3 = self._apply(204, [[1, 1], [3, 3]], [["PASS"], ["PLACE", "SHEEP"]])
        self.assertEqual(a3["hands"], [["PASS"], ["PLACE", "GOOSE"]])
        self.assertFalse(self.st["broken"])
        self.assertEqual(V3._V3_REPORT["v3_rewrites"], 3)
        self.assertEqual(self.st["sites"], {(3, 3): 204 // 24})

    def test_untargeted_steps_return_the_base_action_object_unchanged(self):
        action, out = self._apply(150, [[1, 1], [3, 3]],
                                  [["WATER"], ["HARVEST"]], market=[["SELL", "EGG", 2]])
        self.assertIs(out, action)

    def test_a_moved_unit_latches_broken_instead_of_placing_onto_a_pasture(self):
        """If the unit is not standing where it built, PLACE GOOSE would silently
        no-op - the lever must refuse rather than spend the money."""
        self._apply(203, [[1, 1], [3, 3]], [["PASS"], ["BUILD_PASTURE"]])
        _b, out = self._apply(204, [[1, 1], [9, 9]], [["PASS"], ["PLACE", "SHEEP"]])
        self.assertTrue(self.st["broken"])
        self.assertEqual(out["hands"], [["PASS"], ["PLACE", "SHEEP"]])

    def test_an_unexpected_command_at_a_planned_key_latches_broken(self):
        _b, out = self._apply(203, [[1, 1], [3, 3]], [["PASS"], ["WATER"]])
        self.assertTrue(self.st["broken"])
        self.assertEqual(out["hands"], [["PASS"], ["WATER"]])


class TestIdentityWhenOff(unittest.TestCase):
    """With the flag at 0 the overlay must hand back the base's own action object
    before touching any state - that is what makes the shipped file bit-identical
    to agents/public_farm2945.py."""

    def setUp(self):
        self._base = V3._V3_BASE_AGENT
        self._k = V3.V3_GOOSE_TAIL_K
        V3._V3_STATE.clear()

    def tearDown(self):
        V3._V3_BASE_AGENT = self._base
        V3.V3_GOOSE_TAIL_K = self._k

    def test_returns_the_base_object_and_keeps_no_state(self):
        sentinel = {"farmer": ["PASS"], "hands": [], "market": []}
        calls = []

        def fake(observation, configuration=None):
            calls.append(int(observation["step"]))
            return sentinel

        V3._V3_BASE_AGENT = fake
        V3.V3_GOOSE_TAIL_K = 0
        for step in (0, 1, 200, 204):
            self.assertIs(V3.agent(_obs(step), None), sentinel)
        self.assertEqual(calls, [0, 1, 200, 204])
        self.assertEqual(V3._V3_STATE, {})

    def test_the_lever_on_does_reach_the_planner(self):
        sentinel = {"farmer": ["PASS"], "hands": [], "market": []}
        V3._V3_BASE_AGENT = lambda observation, configuration=None: sentinel
        V3.V3_GOOSE_TAIL_K = 2
        real, V3._IMPL.chassis = V3._IMPL.chassis, _MiniTape(_mini_tape())
        try:
            V3.agent(_obs(0, hands=[[4, 4], [4, 4]]), None)
            self.assertIn(0, V3._V3_STATE)
            self.assertIsNotNone(V3._V3_STATE[0]["plan"])
        finally:
            V3._IMPL.chassis = real


if __name__ == "__main__":
    unittest.main()
