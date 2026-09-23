"""Unit tests for agents/farm2945_v2.py - the three T5d overlays on public_farm2945.

Stdlib unittest (pytest is not installed in this repo). These cover the overlay's
own invariants only; the strategy verdict is in docs/ENDGAME/v2_results.md, which
is measured on experiments/endgame/ladder_replay.py and on self-play.
"""

import copy
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2_PATH = os.path.join(ROOT, "agents", "farm2945_v2.py")
BASE_PATH = os.path.join(ROOT, "agents", "public_farm2945.py")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V2 = _load(V2_PATH, "farm2945_v2_under_test")


def _obs(step, tiles, farmer=(0, 0), hands=(), seeds=None, shed=None,
         prices=None, player=0):
    return {
        "step": step,
        "player": player,
        "farms": [{
            "tiles": tiles,
            "farmer": list(farmer),
            "hands": [list(h) for h in hands],
            "money": 20000,
            "unlocked_quadrants": ["NW", "NE", "SW"],
            "hires_today": 0,
        }],
        "market": {"prices": dict(prices or {"MELON": 200})},
        "private": {
            "seeds": dict(seeds or {}),
            "shed": dict(shed or {}),
            "inventories": [{} for _ in range(1 + len(hands))],
        },
        "town": {"unlocked_shops": []},
    }


def _empty_tiles(n=10):
    return [[None] * n for _ in range(n)]


def _melon(planted_day=0, yield_units=6):
    return {"kind": "PLANT", "crop": "MELON", "planted_day": planted_day,
            "watered_today": False, "consecutive_unwatered": 0,
            "yield_units": yield_units, "max_lifespan_step": 13 * 24,
            "fertilized_until_day": -1}


class TestFileShape(unittest.TestCase):
    def test_base_is_embedded_verbatim(self):
        base = _read(BASE_PATH)
        v2 = _read(V2_PATH)
        self.assertIn(base, v2, "the base must be embedded byte-verbatim")

    def test_agent_is_the_last_callable(self):
        ns = {}
        exec(compile(_read(V2_PATH), V2_PATH, "exec"), ns)
        callables = [k for k, v in ns.items() if callable(v)]
        self.assertEqual(callables[-1], "agent")

    def test_shipped_flags_are_the_no_op_configuration(self):
        # No lever met the T5d ship criteria (docs/ENDGAME/v2_results.md), so the
        # file ships behaviour-identical to the base, as farm2945_late.py does.
        self.assertFalse(V2.V2_V219_OFF)
        self.assertFalse(V2.V2_MELON_STAGGER)

    def test_base_file_untouched_by_this_work(self):
        # farm2945_v2.py must never be the thing that edits the base.
        base = _read(BASE_PATH)
        self.assertNotIn("V2_V219_OFF", base)
        self.assertNotIn("_v2_melon_stagger", base)


class TestLeverAV219(unittest.TestCase):
    def test_qualifies_is_rebound_and_short_circuits_when_off(self):
        self.assertIsNot(V2._v219_qualifies, V2._V2_V219_QUALIFIES_BASE)
        old = V2.V2_V219_OFF
        try:
            V2.V2_V219_OFF = True
            # obs/native are never touched on the disabled path, so None is safe
            # and proves the base predicate was not called.
            self.assertFalse(V2._v219_qualifies(None, None))
        finally:
            V2.V2_V219_OFF = old

    def test_flag_off_delegates_to_the_base_predicate(self):
        old = V2.V2_V219_OFF
        calls = []
        base = V2._V2_V219_QUALIFIES_BASE
        try:
            V2.V2_V219_OFF = False
            V2._V2_V219_QUALIFIES_BASE = lambda o, n: calls.append((o, n)) or "sentinel"
            self.assertEqual(V2._v219_qualifies("obs", "native"), "sentinel")
            self.assertEqual(calls, [("obs", "native")])
        finally:
            V2._V2_V219_QUALIFIES_BASE = base
            V2.V2_V219_OFF = old

    def test_v219_wrapper_reads_the_module_global(self):
        # The disable only works because the base looks the name up at call time.
        src = _read(BASE_PATH)
        self.assertIn("state['eligible']=_v219_qualifies(observation,native)", src)


class TestLeverBCarrot(unittest.TestCase):
    def test_overlay_drives_the_bases_own_gate_constants(self):
        self.assertEqual(V2.V9_CARROT_RATIO, V2.V2_CARROT_RATIO)
        self.assertEqual(V2.V9_CARROT_FIRST_DAY, V2.V2_CARROT_FIRST_DAY)
        self.assertEqual(V2.V9_CARROT_LAST_DAY, V2.V2_CARROT_LAST_DAY)

    def test_shipped_values_match_the_base_defaults(self):
        base = _load(BASE_PATH, "farm2945_base_under_test")
        self.assertEqual(V2.V9_CARROT_RATIO, base.V9_CARROT_RATIO)
        self.assertEqual(V2.V9_CARROT_FIRST_DAY, base.V9_CARROT_FIRST_DAY)
        self.assertEqual(V2.V9_CARROT_LAST_DAY, base.V9_CARROT_LAST_DAY)

    def test_widening_never_plants_more_carrot_than_held(self):
        # The base's swap decrements a per-turn counter seeded from held seed, so
        # the engine's atomic-PLANT rule (kaggriculture.py:920-931) can never fire.
        tiles = _empty_tiles()
        obs = _obs(24 * 12, tiles, farmer=(0, 0), hands=[(1, 0), (2, 0), (3, 0)],
                   seeds={"CARROT": 2}, shed={"WHEAT": 60},
                   prices={"CARROT": 100, "WHEAT": 10, "MELON": 200})
        action = {"farmer": ["PLANT", "WHEAT"],
                  "hands": [["PLANT", "WHEAT"], ["PLANT", "WHEAT"], ["PLANT", "WHEAT"]],
                  "market": [["BUY_SEED", "WHEAT", 4]]}
        old = V2.V9_CARROT_RATIO
        try:
            V2.V9_CARROT_RATIO = 1.0
            out = V2._v9_carrot(obs, copy.deepcopy(action), {})
        finally:
            V2.V9_CARROT_RATIO = old
        cmds = [out["farmer"]] + list(out["hands"])
        n_carrot = sum(1 for c in cmds if c[:2] == ["PLANT", "CARROT"])
        self.assertEqual(n_carrot, 2, "must not exceed the 2 held CARROT seeds")
        self.assertEqual(sum(1 for c in cmds if c[:2] == ["PLANT", "WHEAT"]), 2)

    def test_widening_renames_the_seed_buy_one_for_one(self):
        tiles = _empty_tiles()
        obs = _obs(24 * 12, tiles, seeds={"CARROT": 0}, shed={"WHEAT": 60},
                   prices={"CARROT": 100, "WHEAT": 10, "MELON": 200})
        action = {"farmer": ["PASS"], "hands": [],
                  "market": [["BUY_SEED", "WHEAT", 5]]}
        old = V2.V9_CARROT_RATIO
        try:
            V2.V9_CARROT_RATIO = 1.0
            out = V2._v9_carrot(obs, copy.deepcopy(action), {})
        finally:
            V2.V9_CARROT_RATIO = old
        buys = [o for o in out["market"] if o[0] == "BUY_SEED"]
        self.assertEqual(buys, [["BUY_SEED", "CARROT", 5]])
        self.assertEqual(len(out["market"]), len(action["market"]))


class TestLeverCMelon(unittest.TestCase):
    def setUp(self):
        V2._V2_STATES.clear()
        self.st = V2._v2_state(0)
        self.st["melon"] = set(V2.V2_MELON_TILES)

    def _tiles_with_melon(self, planted_day=0, yield_units=6):
        tiles = _empty_tiles()
        for (x, y) in V2.V2_MELON_TILES:
            tiles[y][x] = _melon(planted_day, yield_units)
        return tiles

    def test_day10_harvest_on_a_melon_tile_becomes_pass(self):
        tiles = self._tiles_with_melon()
        obs = _obs(24 * 10 + 6, tiles, farmer=(0, 4), hands=[(9, 9)])
        action = {"farmer": ["HARVEST"], "hands": [["HARVEST"]], "market": []}
        out = V2._v2_melon_stagger(obs, action, self.st)
        self.assertEqual(out["farmer"], ["PASS"])
        self.assertEqual(out["hands"], [["HARVEST"]], "off-tile units untouched")

    def test_day12_water_on_a_ripe_melon_tile_becomes_harvest(self):
        tiles = self._tiles_with_melon()
        obs = _obs(24 * 12 + 20, tiles, farmer=(1, 2))
        action = {"farmer": ["WATER"], "hands": [], "market": []}
        out = V2._v2_melon_stagger(obs, action, self.st)
        self.assertEqual(out["farmer"], ["HARVEST"])

    def test_day12_rescue_skips_an_unripe_melon(self):
        tiles = self._tiles_with_melon(planted_day=5)
        obs = _obs(24 * 12 + 20, tiles, farmer=(1, 2))
        action = {"farmer": ["WATER"], "hands": [], "market": []}
        out = V2._v2_melon_stagger(obs, action, self.st)
        self.assertEqual(out["farmer"], ["WATER"])

    def test_no_edit_on_a_tile_outside_the_remembered_set(self):
        tiles = self._tiles_with_melon()
        tiles[9][9] = _melon()
        obs = _obs(24 * 10 + 6, tiles, farmer=(9, 9))
        action = {"farmer": ["HARVEST"], "hands": [], "market": []}
        out = V2._v2_melon_stagger(obs, action, self.st)
        self.assertEqual(out["farmer"], ["HARVEST"])

    def test_abort_latches_when_the_day0_block_is_not_the_measured_one(self):
        tiles = _empty_tiles()
        tiles[4][0] = _melon()  # only 1 of the 7
        obs = _obs(24 * 10, tiles)
        st = V2._v2_state(1)
        V2._v2_observe(obs, st)
        self.assertTrue(st["abort"])
        action = {"farmer": ["HARVEST"], "hands": [], "market": []}
        obs2 = _obs(24 * 10 + 6, tiles, farmer=(0, 4))
        self.assertIs(V2._v2_melon_stagger(obs2, action, st), action)

    def test_sell_is_appended_last_and_capped(self):
        tiles = _empty_tiles()
        obs = _obs(24 * 13, tiles, shed={"MELON": 40})
        action = {"farmer": ["PASS"], "hands": [],
                  "market": [["SELL", "WHEAT", 3], ["BUY_SEED", "WHEAT", 2]]}
        out = V2._v2_melon_stagger(obs, action, self.st)
        self.assertEqual(out["market"][:2], [["SELL", "WHEAT", 3], ["BUY_SEED", "WHEAT", 2]])
        self.assertEqual(out["market"][-1], ["SELL", "MELON", V2.V2_MELON_SELL_PER_TURN])

    def test_sell_respects_the_ten_order_cap(self):
        tiles = _empty_tiles()
        obs = _obs(24 * 13, tiles, shed={"MELON": 40})
        market = [["SELL", "WHEAT", 1] for _ in range(V2.MAX_ORDERS)]
        action = {"farmer": ["PASS"], "hands": [], "market": market}
        out = V2._v2_melon_stagger(obs, action, self.st)
        self.assertEqual(len(out["market"]), V2.MAX_ORDERS)

    def test_no_double_selling_when_the_tape_already_sells_melon(self):
        tiles = _empty_tiles()
        obs = _obs(24 * 13, tiles, shed={"MELON": 4})
        action = {"farmer": ["PASS"], "hands": [],
                  "market": [["SELL", "MELON", 4]]}
        out = V2._v2_melon_stagger(obs, action, self.st)
        self.assertEqual(out["market"], [["SELL", "MELON", 4]])

    def test_flag_off_is_a_pure_passthrough(self):
        old_flag, old_base = V2.V2_MELON_STAGGER, V2._V2_BASE_AGENT
        try:
            V2.V2_MELON_STAGGER = False
            sentinel = {"farmer": ["HARVEST"], "hands": [], "market": []}
            V2._V2_BASE_AGENT = lambda o, c=None: sentinel
            tiles = self._tiles_with_melon()
            obs = _obs(24 * 10 + 6, tiles, farmer=(0, 4))
            self.assertIs(V2.agent(obs), sentinel)
        finally:
            V2.V2_MELON_STAGGER = old_flag
            V2._V2_BASE_AGENT = old_base


class TestEngineFactsTheLeversRestOn(unittest.TestCase):
    """If the engine is patched again, these fail before a measurement lies."""

    def setUp(self):
        from kaggle_environments.envs.kaggriculture import kaggriculture as K
        self.K = K

    def test_melon_is_not_ongoing_and_dies_after_day_12(self):
        m = self.K.CROPS["MELON"]
        self.assertFalse(m["ongoing"])
        self.assertEqual(m["first_yield_day"], 10)
        self.assertEqual(m["max_yield_day"], 12)
        plant = self.K._new_plant("MELON", 0, 24)
        self.assertEqual(plant["max_lifespan_step"], 13 * 24)

    def test_melon_has_no_shop_sink(self):
        self.assertFalse([s for s, items in self.K.SHOPS.items() if "MELON" in items])

    def test_plant_on_an_occupied_tile_consumes_no_seed(self):
        farm = {"tiles": _empty_tiles(), "farmer": [0, 0], "hands": [], "money": 0}
        farm["tiles"][0][0] = _melon()
        private = {"seeds": {"WHEAT": 3}, "shed": {}, "inventories": [{}]}
        self.K._apply_unit_action(farm, private, 0, ["PLANT", "WHEAT"], 10, 10, 24)
        self.assertEqual(private["seeds"]["WHEAT"], 3)
        self.assertEqual(farm["tiles"][0][0]["crop"], "MELON")

    def test_harvest_on_an_unripe_melon_leaves_the_tile_alone(self):
        farm = {"tiles": _empty_tiles(), "farmer": [0, 0], "hands": [], "money": 0}
        farm["tiles"][0][0] = _melon(planted_day=5, yield_units=1)
        private = {"seeds": {}, "shed": {}, "inventories": [{}]}
        self.K._apply_unit_action(farm, private, 0, ["HARVEST"], 10, 10, 24)
        self.assertEqual(farm["tiles"][0][0]["crop"], "MELON")
        self.assertEqual(private["inventories"][0], {})

    def test_harvest_on_a_ripe_melon_clears_the_tile(self):
        farm = {"tiles": _empty_tiles(), "farmer": [0, 0], "hands": [], "money": 0}
        farm["tiles"][0][0] = _melon(planted_day=0, yield_units=6)
        private = {"seeds": {}, "shed": {}, "inventories": [{}]}
        self.K._apply_unit_action(farm, private, 0, ["HARVEST"], 10, 12, 24)
        self.assertIsNone(farm["tiles"][0][0])
        self.assertEqual(private["inventories"][0]["MELON"], 6)


if __name__ == "__main__":
    unittest.main()
