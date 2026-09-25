"""WB_Controller (experiments/splice/controller.py): planner, executor task generation,
market arbiter and the per-turn exception fallback, on synthetic observations.

Run with:
    .venv/Scripts/python.exe -m unittest tests.test_splice_controller -v
"""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments", "splice"))

import controller as C  # noqa: E402
from price_model import WB_PriceModel  # noqa: E402
from sell_engine import WB_SellEngine  # noqa: E402

try:
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
except ImportError:  # pragma: no cover
    K = None

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
BASE = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
        "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100}


def _tiles(quads=("NW", "NE", "SW")):
    out = []
    for y in range(10):
        row = []
        for x in range(10):
            q = ("N" if y < 5 else "S") + ("W" if x < 5 else "E")
            row.append(None if q in quads else "LOCKED")
        out.append(row)
    return out


def _animal(kind, placed=0, fed=False, cared=False, unfed=0, yu=0, fert=False, bonus=0):
    st = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}[kind]
    return {"kind": st, "animal": kind, "placed_day": placed, "yield_units": yu,
            "consecutive_unfed": unfed, "fed_today": fed, "cared_today": cared,
            "fertilizer_available": fert, "pending_care_bonus": bonus}


def _plant(crop, planted, watered=False, unwatered=0, yu=None, fert_until=-1):
    ongoing = crop in ("TOMATO", "STRAWBERRY")
    return {"kind": "PLANT", "crop": crop, "planted_day": planted, "watered_today": watered,
            "consecutive_unwatered": unwatered, "yield_units": (0 if ongoing else 1) if yu is None else yu,
            "max_lifespan_step": -1, "fertilized_until_day": fert_until}


def make_obs(step=200, tiles=None, farmer=(4, 4), hands=(), money=5000, shed=None, seeds=None,
             invs=None, shops=(), opp_tiles=None, quads=("NW", "NE", "SW"), market_inv=None):
    tiles = tiles if tiles is not None else _tiles(quads)
    units = [list(farmer)] + [list(h) for h in hands]
    inventories = [dict(x) for x in (invs or [])]
    while len(inventories) < len(units):
        inventories.append({})
    sh = {p: 0 for p in PRODUCTS + ["GOOSE", "COW", "SHEEP"]}
    sh.update(shed or {})
    sd = {c: 0 for c in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")}
    sd.update(seeds or {})
    minv = {p: 10000 for p in PRODUCTS}
    minv.update(market_inv or {})
    pm = WB_PriceModel()
    me = {"money": float(money), "tiles": tiles, "farmer": units[0], "hands": units[1:],
          "unlocked_quads": list(quads), "unlocked_quadrants": list(quads), "hires_today": 0}
    opp = {"money": 3000.0, "tiles": opp_tiles if opp_tiles is not None else _tiles(quads), "farmer": [4, 4],
           "hands": [], "unlocked_quadrants": list(quads), "hires_today": 0}
    return {
        "player": 0, "step": step, "day": step // 24, "hour": step % 24,
        "farms": [me, opp],
        "private": {"shed": sh, "seeds": sd, "inventories": inventories},
        "market": {"inventory": minv, "prices": {p: pm.quote(p, minv[p]) for p in PRODUCTS}},
        "town": {"unlocked_shops": list(shops)},
        "remainingOverageTime": 60,
    }


def new_controller():
    pm = WB_PriceModel()
    return C.WB_Controller(pm, WB_SellEngine(pm))


def unit_actions(out):
    return [out["farmer"]] + list(out["hands"])


class TestActShape(unittest.TestCase):
    def test_returns_one_action_per_unit_and_at_most_ten_orders(self):
        ctrl = new_controller()
        obs = make_obs(hands=[(5, 4), (4, 5)])
        out = ctrl.act(obs)
        self.assertIsNone(ctrl.last_error)
        self.assertEqual(len(out["hands"]), 2)
        self.assertLessEqual(len(out["market"]), 10)
        for a in unit_actions(out):
            self.assertIsInstance(a, list)
            self.assertTrue(a)


class TestFallback(unittest.TestCase):
    def test_exception_falls_back_to_safe_action(self):
        ctrl = new_controller()
        obs = make_obs()
        tiles = obs["farms"][0]["tiles"]
        tiles[4][4] = _plant("WHEAT", planted=8)
        del obs["market"]                        # the controller cannot plan without it
        out = ctrl.act(obs)
        self.assertEqual(ctrl.errors, 1)
        self.assertEqual(out["market"], [])
        self.assertEqual(out["farmer"], ["WATER"])  # waters the unwatered plant it stands on

    def test_fallback_feeds_only_with_wheat(self):
        obs = make_obs(hands=[(5, 4)], invs=[{}, {"WHEAT": 1}])
        tiles = obs["farms"][0]["tiles"]
        tiles[4][4] = _animal("COW")
        tiles[4][5] = _animal("GOOSE")
        out = C._wb_fallback(obs)
        self.assertEqual(out["farmer"], ["CARE"])   # no wheat in hand: care instead of feed
        self.assertEqual(out["hands"], [["FEED"]])


class TestNoDuplicateCare(unittest.TestCase):
    def test_cared_animal_gets_no_care_task(self):
        ctrl = new_controller()
        obs = make_obs(step=200)
        obs["farms"][0]["tiles"][3][4] = _animal("COW", fed=True, cared=True)
        ctrl.act(obs)                             # builds the day plan
        tasks = ctrl._tasks(C._WB_View(obs))
        self.assertFalse([t for t in tasks if t[1] == "CARE"])

    def test_two_units_on_one_uncared_animal_care_it_once(self):
        ctrl = new_controller()
        obs = make_obs(step=200, farmer=(4, 3), hands=[(4, 3), (4, 3)])
        obs["farms"][0]["tiles"][3][4] = _animal("COW", fed=True)
        out = ctrl.act(obs)
        self.assertLessEqual(sum(1 for a in unit_actions(out) if a == ["CARE"]), 1)


class TestPlantAndWater(unittest.TestCase):
    def test_plant_count_never_exceeds_seeds(self):
        ctrl = new_controller()
        obs = make_obs(step=200, farmer=(1, 1), hands=[(2, 1), (3, 1), (1, 2)], seeds={"WHEAT": 1})
        out = ctrl.act(obs)
        plants = [a for a in unit_actions(out) if a[0] == "PLANT"]
        self.assertLessEqual(len(plants), 1)
        for a in plants:
            self.assertEqual(a[1], "WHEAT")

    def test_fresh_planting_is_watered_by_the_unit_standing_on_it(self):
        ctrl = new_controller()
        obs = make_obs(step=200, farmer=(1, 1), seeds={"WHEAT": 1})
        out1 = ctrl.act(obs)
        self.assertEqual(out1["farmer"], ["PLANT", "WHEAT"])
        # apply the planting with the engine's own unit-action code, then ask again
        if K is not None:
            farm = obs["farms"][0]
            priv = obs["private"]
            K._apply_unit_action(farm, priv, 0, out1["farmer"], 10, obs["step"] // 24, 24)
        else:  # pragma: no cover
            obs["farms"][0]["tiles"][1][1] = _plant("WHEAT", planted=obs["step"] // 24, unwatered=1)
        obs2 = copy.deepcopy(obs)
        obs2["step"] += 1
        obs2["hour"] += 1
        out2 = ctrl.act(obs2)
        self.assertEqual(out2["farmer"], ["WATER"])

    def test_no_planting_at_hour_23(self):
        ctrl = new_controller()
        obs = make_obs(step=8 * 24 + 23, farmer=(1, 1), seeds={"WHEAT": 3})
        out = ctrl.act(obs)
        self.assertNotEqual(out["farmer"][0], "PLANT")


class TestStructureMatching(unittest.TestCase):
    def test_goose_is_carried_to_a_coop_not_a_pasture(self):
        ctrl = new_controller()
        obs = make_obs(step=200, farmer=(2, 2), invs=[{"GOOSE": 1}])
        tiles = obs["farms"][0]["tiles"]
        tiles[2][2] = {"kind": "PASTURE"}        # standing on the wrong structure
        tiles[2][4] = {"kind": "COOP"}
        out = ctrl.act(obs)
        self.assertNotEqual(out["farmer"][0], "PLACE")
        self.assertEqual(out["farmer"], ["EAST"])

    def test_goose_is_placed_on_a_coop(self):
        ctrl = new_controller()
        obs = make_obs(step=200, farmer=(2, 2), invs=[{"GOOSE": 1}])
        obs["farms"][0]["tiles"][2][2] = {"kind": "COOP"}
        out = ctrl.act(obs)
        self.assertEqual(out["farmer"], ["PLACE", "GOOSE"])

    def test_herd_plan_builds_matching_structures(self):
        ctrl = new_controller()
        opp = _tiles()
        for x in range(5):
            opp[0][x] = _animal("GOOSE", placed=5)
        obs = make_obs(step=10 * 24, money=20000, opp_tiles=opp, shops=("BAKERY",))
        ctrl.act(obs)
        plan = ctrl.plan
        buy = plan["buy"]
        self.assertGreater(sum(buy.values()), 0)
        kinds = [k for (_x, _y, k) in plan["build"]]
        self.assertEqual(kinds.count("COOP"), buy.get("GOOSE", 0))
        self.assertEqual(kinds.count("PASTURE"), buy.get("COW", 0) + buy.get("SHEEP", 0))


class TestArbiter(unittest.TestCase):
    def test_ten_order_cap_sells_first_critical_buys_kept(self):
        ctrl = new_controller()
        # hour 0 with many wants: hires, seeds, a feed shortfall, goods to sell, land
        tiles = _tiles(("NW", "NE"))
        for x in range(5):
            tiles[3][x] = _animal("GOOSE", placed=2)
        obs = make_obs(step=9 * 24, money=4000, tiles=tiles, quads=("NW", "NE"),
                       shed={"MILK": 20, "WOOL": 10, "EGG": 12, "STRAWBERRY": 8, "FERTILIZER": 9},
                       market_inv={"MILK": 9990, "WOOL": 9990, "EGG": 9990, "STRAWBERRY": 9990})
        out = ctrl.act(obs)
        m = out["market"]
        self.assertLessEqual(len(m), 10)
        kinds = [o[0] for o in m]
        self.assertIn(["BUY_PRODUCT", "WHEAT"], [o[:2] for o in m])     # five unfed geese, no wheat
        first_non_sell = next((i for i, k in enumerate(kinds) if k != "SELL"), len(kinds))
        self.assertTrue(all(k != "SELL" for k in kinds[first_non_sell:]))

    def test_never_buys_the_fourth_quadrant(self):
        ctrl = new_controller()
        obs = make_obs(step=12 * 24, money=50000, quads=("NW", "NE", "SW"))
        out = ctrl.act(obs)
        self.assertNotIn(["BUY_LAND"], out["market"])

    def test_buys_the_third_quadrant_when_affordable(self):
        # land is the lowest priority: morning hires may fill the 10 slots, so check hour 5
        ctrl = new_controller()
        obs = make_obs(step=10 * 24 + 5, money=9000, quads=("NW", "NE"), tiles=_tiles(("NW", "NE")))
        out = ctrl.act(obs)
        self.assertIn(["BUY_LAND"], out["market"])


class TestPlanner(unittest.TestCase):
    def test_tomato_only_where_a_shop_consumes_it(self):
        ctrl = new_controller()
        v = C._WB_View(make_obs(step=14 * 24, shops=("BAKERY", "PET_CAFE")))
        self.assertNotIn("TOMATO", [c for c, _n in ctrl._crop_targets(v, 10)])
        v = C._WB_View(make_obs(step=14 * 24, shops=("PIZZA_SHOP",)))
        tomato = dict(ctrl._crop_targets(v, 10)).get("TOMATO", 0)
        self.assertGreater(tomato, 0)

    def test_strawberry_mirror_stops_after_day_13(self):
        ctrl = new_controller()
        opp = _tiles()
        for x in range(10):
            opp[0][x] = _plant("STRAWBERRY", planted=5)
        v = C._WB_View(make_obs(step=12 * 24, opp_tiles=opp))
        self.assertGreaterEqual(dict(ctrl._crop_targets(v, 10)).get("STRAWBERRY", 0), 10)
        v = C._WB_View(make_obs(step=14 * 24, opp_tiles=opp))
        self.assertNotIn("STRAWBERRY", dict(ctrl._crop_targets(v, 10)))

    def test_no_feed_task_on_day_29(self):
        ctrl = new_controller()
        obs = make_obs(step=29 * 24 + 1, farmer=(4, 3), invs=[{"WHEAT": 3}])
        obs["farms"][0]["tiles"][3][4] = _animal("COW", placed=10)
        ctrl.act(obs)
        tasks = ctrl._tasks(C._WB_View(obs))
        self.assertFalse([t for t in tasks if t[1] in ("FEED", "CARE")])

    def test_escape_risk_animal_is_fed_even_when_product_is_cheap(self):
        ctrl = new_controller()
        obs = make_obs(step=20 * 24 + 5, farmer=(4, 3), invs=[{"WHEAT": 2}],
                       market_inv={"WOOL": 10100})          # wool far above I0: ~$1
        obs["farms"][0]["tiles"][3][4] = _animal("SHEEP", placed=8, unfed=1)
        out = ctrl.act(obs)
        self.assertEqual(out["farmer"], ["FEED"])

    def test_final_day_goods_are_dropped_at_the_shed(self):
        ctrl = new_controller()
        obs = make_obs(step=29 * 24 + 18, farmer=(4, 4), invs=[{"MILK": 4, "EGG": 3}])
        out = ctrl.act(obs)
        self.assertEqual(out["farmer"], ["DROP"])


if __name__ == "__main__":
    unittest.main()
