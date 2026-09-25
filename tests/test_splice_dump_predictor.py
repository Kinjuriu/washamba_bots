"""WB_DumpPredictor (experiments/splice/dump_predictor.py).

The ported market must equal the engine's _process_market; family signatures come from it;
detection, route keying, the prediction window and the audit that switches the predictor
off against a W3-opening non-tape (e.g. our own splice) are checked on synthetic
observations. The generated dump table is checked for shape.

Run with:
    .venv/Scripts/python.exe -m unittest tests.test_splice_dump_predictor -v
"""
import os
import random
import sys
import unittest
from types import SimpleNamespace as NS

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments", "splice"))

import dump_predictor as dpmod  # noqa: E402
from dump_predictor import (WB_DP_OPENINGS, WB_DumpPredictor, WB_dp_signature,  # noqa: E402
                            WB_dp_signatures, _wb_dp_market)
from price_model import WB_PriceModel  # noqa: E402

try:
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
except ImportError:  # pragma: no cover
    K = None

PM = WB_PriceModel()
I0 = 10000


def _engine(orders, inventory, money, sheds, hires=(0, 0)):
    market = {"inventory": dict(inventory), "prices": {p: 0 for p in K.PRODUCTS}}
    farms = [{"money": float(m), "hires_today": h, "hands": [], "farmer": [4, 4],
              "unlocked_quadrants": ["NW"], "tiles": [[None] * 10 for _ in range(10)]}
             for m, h in zip(money, hires)]
    privates = [{"shed": dict(s), "seeds": {}, "inventories": [{}]} for s in sheds]
    state = [NS(observation=NS(market=market, farms=farms, private=privates[i]), action={"market": orders[i]})
             for i in range(2)]
    K._process_market(state, NS(configuration={}))
    return market["inventory"], [f["money"] for f in farms], [p["shed"] for p in privates], [f["hires_today"] for f in farms]


@unittest.skipIf(K is None, "kaggle_environments not installed")
class TestPortedMarketIsExact(unittest.TestCase):
    def test_random_order_mixes(self):
        rng = random.Random(4)
        items = ["WHEAT", "FERTILIZER", "MILK", "WOOL", "MELON", "EGG"]
        for _ in range(400):
            orders = []
            for _seat in (0, 1):
                q = []
                for _ in range(rng.randint(0, 6)):
                    kind = rng.choice(["SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL", "HIRE"])
                    if kind == "HIRE":
                        q.append(["HIRE"])
                    elif kind == "BUY_SEED":
                        q.append(["BUY_SEED", rng.choice(list(dpmod.WB_DP_SEED_COST)), rng.randint(1, 5)])
                    elif kind == "BUY_ANIMAL":
                        q.append(["BUY_ANIMAL", rng.choice(list(dpmod.WB_DP_ANIMAL_COST)), rng.randint(1, 3)])
                    else:
                        q.append([kind, rng.choice(items), rng.randint(1, 30)])
                orders.append(q)
            inv = {p: I0 + rng.randint(-200, 200) for p in K.PRODUCTS}
            money = [rng.choice([50.0, 900.0, 3000.0]), rng.choice([50.0, 900.0, 3000.0])]
            sheds = [{p: rng.randint(0, 12) for p in items} for _ in (0, 1)]
            hires = [rng.randint(0, 4), rng.randint(0, 4)]
            want = _engine(orders, inv, money, sheds, hires)
            got = _wb_dp_market(PM, orders, inv, money, sheds, hires)
            self.assertEqual(got[0], want[0])
            self.assertEqual(got[1], want[1])
            self.assertEqual(got[3], want[3])
            for s in (0, 1):
                self.assertEqual({k: v for k, v in got[2][s].items() if v}, {k: v for k, v in want[2][s].items() if v})


@unittest.skipIf(K is None, "kaggle_environments not installed")
class TestSignatures(unittest.TestCase):
    # Measured on the engine with the real agent files (docs/ENDGAME/splice_dump_predictor.md).
    MEASURED = {"W3": (2854.0, 9989), "W0": (2850.0, 9989), "F2945": (2860.0, 9989), "TOP6": (2460.0, 9989)}
    MEASURED_T2 = {"W3": 1042.0, "W0": 1038.0, "F2945": 1048.0, "TOP6": 581.0}

    def test_turn_one_matches_measured_both_seats(self):
        for fam, sig in self.MEASURED.items():
            for seat in (0, 1):
                self.assertEqual(WB_dp_signature(PM, fam, seat), sig, (fam, seat))

    def test_turn_two_matches_measured(self):
        for seat in (0, 1):
            sigs = WB_dp_signatures(PM, seat)
            for fam, money in self.MEASURED_T2.items():
                self.assertEqual(sigs[fam][1][0], money, (fam, seat))

    def test_families_are_distinguishable(self):
        for seat in (0, 1):
            sigs = WB_dp_signatures(PM, seat)
            self.assertEqual(len({v for v in sigs.values()}), len(WB_DP_OPENINGS))


def _obs(step, player, opp_money, wheat, our_money=1000.0, shops=(), inventory=None):
    inv = {p: I0 for p in PM.params}
    inv["WHEAT"] = wheat
    inv.update(inventory or {})
    farms = [None, None]
    farms[player] = {"money": our_money}
    farms[1 - player] = {"money": opp_money}
    return {"step": step, "player": player, "farms": farms, "market": {"inventory": inv},
            "town": {"unlocked_shops": list(shops)}}


class TestDetection(unittest.TestCase):
    def test_detects_each_family_from_steps_one_and_two(self):
        for seat in (0, 1):
            sigs = WB_dp_signatures(PM, seat)
            for fam, (s1, s2) in sigs.items():
                dp = WB_DumpPredictor(PM, dumps={}, key_route={})
                dp.observe(_obs(0, seat, 3000.0, I0))
                self.assertEqual(dp.observe(_obs(1, seat, s1[0], s1[1])), fam)
                self.assertEqual(dp.observe(_obs(2, seat, s2[0], s2[1])), fam)

    def test_unknown_opening_is_none(self):
        dp = WB_DumpPredictor(PM, dumps={}, key_route={})
        self.assertIsNone(dp.detect([_obs(1, 0, 2777.0, 9989), _obs(2, 0, 900.0, 9989)]))

    def test_contradicting_step_two_is_none(self):
        sigs = WB_dp_signatures(PM, 0)
        dp = WB_DumpPredictor(PM, dumps={}, key_route={})
        dp.observe(_obs(1, 0, *sigs["W3"][0]))
        self.assertEqual(dp.family, "W3")
        self.assertIsNone(dp.observe(_obs(2, 0, sigs["W0"][1][0], sigs["W0"][1][1])))


class TestPrediction(unittest.TestCase):
    DUMPS = {"W3": {105: {"MILK": ((257, 12), (270, 6))}, "any": {"MILK": ((196, 12),)}}}
    KEYS = {("BAKERY", "BRUNCH_SPOT"): 105}

    def _w3(self):
        sigs = WB_dp_signatures(PM, 0)
        dp = WB_DumpPredictor(PM, dumps=self.DUMPS, key_route=self.KEYS)
        dp.observe(_obs(1, 0, *sigs["W3"][0]))
        dp.observe(_obs(2, 0, *sigs["W3"][1]))
        return dp

    def test_window_and_route(self):
        dp = self._w3()
        shops = ("BAKERY", "BRUNCH_SPOT")
        self.assertEqual(dp.upcoming(_obs(250, 0, 0, I0, shops=shops), "MILK", 8), [(257, 12)])
        self.assertEqual(dp.upcoming(_obs(257, 0, 0, I0, shops=shops), "MILK", 8), [])       # this call: too late
        self.assertEqual(dp.upcoming(_obs(250, 0, 0, I0, shops=shops), "MILK", 30), [(257, 12), (270, 6)])
        self.assertEqual(dp.upcoming(_obs(250, 0, 0, I0, shops=shops), "WOOL", 30), [])
        # Unknown key: the family's pooled table.
        self.assertEqual(dp.upcoming(_obs(190, 0, 0, I0, shops=("PET_CAFE", "PET_CAFE")), "MILK", 8), [(196, 12)])

    def test_top_six_and_unknown_are_not_predicted(self):
        sigs = WB_dp_signatures(PM, 0)
        dp = WB_DumpPredictor(PM, dumps=self.DUMPS, key_route=self.KEYS)
        dp.observe(_obs(1, 0, *sigs["TOP6"][0]))
        self.assertEqual(dp.family, "TOP6")
        self.assertEqual(dp.upcoming(_obs(250, 0, 0, I0, shops=("BAKERY", "BRUNCH_SPOT")), "MILK", 8), [])

    def test_route_phases(self):
        dp = self._w3()
        shops = ("BAKERY", "BRUNCH_SPOT")
        self.assertEqual(dp.route(_obs(100, 0, 0, I0, shops=shops)), 0)
        self.assertEqual(dp.route(_obs(300, 0, 0, I0, shops=shops)), 105)
        self.assertEqual(dp.route(_obs(700, 0, 0, I0, shops=shops)), 2)

    def test_rival_key_override(self):
        dp = WB_DumpPredictor(PM, dumps={}, key_route={("BAKERY", "YARN_STORE"): 9})
        dp.readings[2] = (0.0, 9989, 229.0)         # our money 229 at step 2, WHEAT 9989
        self.assertEqual(dp.keyed_route(_obs(300, 0, 0, I0, shops=("BAKERY", "YARN_STORE"))), 128)
        dp.readings[2] = (0.0, 9989, 1042.0)
        self.assertEqual(dp.keyed_route(_obs(300, 0, 0, I0, shops=("BAKERY", "YARN_STORE"))), 9)


class TestAudit(unittest.TestCase):
    """Predicted dumps that never reach the market switch the predictor off."""

    DUMPS = {"W3": {"any": {"MILK": ((200, 12), (210, 12), (220, 12))}}}

    def _run(self, milk_jump):
        sigs = WB_dp_signatures(PM, 0)
        dp = WB_DumpPredictor(PM, dumps=self.DUMPS, key_route={})
        dp.observe(_obs(1, 0, *sigs["W3"][0]))
        dp.observe(_obs(2, 0, *sigs["W3"][1]))
        milk = I0
        for step in range(195, 225):
            if step - 1 in (200, 210, 220):
                milk += milk_jump
            dp.observe(_obs(step, 0, 0, I0, inventory={"MILK": milk}))
        return dp

    def test_tape_that_dumps_stays_on(self):
        dp = self._run(12)
        self.assertFalse(dp.disabled)
        self.assertEqual(dp.hits, 3)

    def test_non_tape_is_switched_off(self):
        dp = self._run(0)
        self.assertTrue(dp.disabled)
        self.assertIsNone(dp.active_family())
        self.assertEqual(dp.upcoming(_obs(205, 0, 0, I0), "MILK", 10), [])


class TestGeneratedTable(unittest.TestCase):
    def test_shape(self):
        self.assertTrue(set(dpmod.WB_DP_TAPE_FAMILIES) <= set(dpmod.WB_DP_DUMPS))
        self.assertEqual(len(dpmod.WB_DP_KEY_ROUTE), 64)
        for fam, routes in dpmod.WB_DP_DUMPS.items():
            self.assertIn("any", routes, fam)
            for route, per in routes.items():
                for product, rows in per.items():
                    steps = [s for s, _ in rows]
                    self.assertEqual(steps, sorted(steps))
                    for s, q in rows:
                        self.assertTrue(180 <= s <= 718 and q >= 4, (fam, route, product, s, q))

    def test_top_level_names_are_prefixed(self):
        for name in vars(dpmod):
            if name.startswith("__") or name == "WB_PriceModel":
                continue
            self.assertTrue(name.startswith(("WB_", "_wb_")), name)


if __name__ == "__main__":
    unittest.main()
