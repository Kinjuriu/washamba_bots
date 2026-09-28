"""agents/w3_frontrun.py: W3 byte-verbatim plus a market-only front-running overlay.

Checks: the base text is byte-identical to agents/w3_herdsafe2700.py; the entry point is
the overlay and wraps W3's real entry (its last callable); with the flag off every action
equals W3's on a real episode; with the flag on the overlay only ADDS SELL orders in
front, never touches W3's orders or unit actions, never sells WHEAT/FERTILIZER, never
exceeds 10 orders and never re-sells what W3 already sells this turn.

Run with:
    .venv/Scripts/python.exe -m unittest tests.test_w3_frontrun -v
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS = os.path.join(ROOT, "agents")
FRONTRUN = os.path.join(AGENTS, "w3_frontrun.py")
BASE = os.path.join(AGENTS, "w3_herdsafe2700.py")

try:
    from kaggle_environments import make
except ImportError:  # pragma: no cover
    make = None


def load(path, **flags):
    if AGENTS not in sys.path:
        sys.path.append(AGENTS)
    ns = {}
    exec(compile(open(path, "rb").read().decode("utf-8"), path, "exec"), ns)
    ns.update(flags)
    return ns, [v for v in ns.values() if callable(v)][-1]


class TestStructure(unittest.TestCase):
    def test_base_is_byte_verbatim(self):
        base = open(BASE, "rb").read()
        self.assertEqual(open(FRONTRUN, "rb").read()[:len(base)], base)

    def test_entry_point_and_captured_base(self):
        ns, entry = load(FRONTRUN)
        self.assertEqual(entry.__name__, "w3_frontrun_agent")
        _, w3_entry = load(BASE)
        self.assertEqual(ns["_WB_BASE"].__name__, w3_entry.__name__)   # herdsafe_forecast_agent
        self.assertNotEqual(ns["_WB_BASE"].__name__, "agent")


@unittest.skipIf(make is None, "kaggle_environments not installed")
class TestFlagOffIsW3(unittest.TestCase):
    def test_actions_identical_on_a_real_episode(self):
        def run(path, **flags):
            _, fn = load(path, **flags)
            env = make("kaggriculture", configuration={"episodeSteps": 240, "seed": 7})
            env.run([fn, "pass"])
            return [env.steps[i][0]["action"] for i in range(1, len(env.steps))]
        self.assertEqual(run(FRONTRUN, WB_FRONTRUN_ON=False), run(BASE))


class _Pred:
    def __init__(self, dumps):
        self.dumps = dumps

    def observe(self, obs):
        return "W3"

    def active_family(self):
        return "W3"

    def upcoming(self, obs, product, horizon):
        s = int(obs["step"])
        return [(t, q) for t, q in self.dumps.get(product, ()) if s < t <= s + horizon]


class TestOverlayRules(unittest.TestCase):
    """The overlay function on stubbed turns: W3's action, stock and predictions are fixed."""

    @classmethod
    def setUpClass(cls):
        cls.ns, cls.entry = load(FRONTRUN)

    def setUp(self):
        self.ns["WB_FRONTRUN_ON"] = True
        self.ns["WB_FRONTRUN_K"] = 12

    def turn(self, w3_market, stock, dumps, step=301):
        base = {"farmer": ["WATER"], "hands": [["PICKUP", "WHEAT", 3], ["FEED"]], "market": w3_market}
        self.ns["_WB_BASE"] = lambda obs, cfg=None: base
        self.ns["_WB_FR"] = {0: _Pred(dumps)}
        self.ns["_wb_fr_stock"] = lambda action, obs: dict(stock)
        inv = {p: 10000 for p in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")}
        obs = {"step": step, "player": 0, "market": {"inventory": inv}, "town": {"unlocked_shops": ["SMOOTHIE_SHOP"]}}
        return base, self.ns["w3_frontrun_agent"](obs, None)

    def test_adds_in_front_and_leaves_w3_untouched(self):
        w3 = [["HIRE"], ["BUY_PRODUCT", "WHEAT", 5]]
        base, out = self.turn(w3, {"MILK": 20}, {"MILK": [(304, 12)]})
        self.assertEqual(out["market"][len(out["market"]) - len(w3):], w3)
        self.assertEqual(out["market"][0][:2], ["SELL", "MILK"])
        self.assertGreater(out["market"][0][2], 0)
        self.assertEqual(out["farmer"], base["farmer"])
        self.assertEqual(out["hands"], base["hands"])

    def test_never_wheat_or_fertilizer(self):
        base, out = self.turn([], {"WHEAT": 50, "FERTILIZER": 50},
                              {"WHEAT": [(304, 30)], "FERTILIZER": [(304, 30)]})
        self.assertIs(out, base)

    def test_no_room_no_orders(self):
        full = [["HIRE"]] * 10
        base, out = self.turn(full, {"MILK": 20}, {"MILK": [(304, 12)]})
        self.assertIs(out, base)

    def test_fills_only_the_free_slots(self):
        nine = [["HIRE"]] * 9
        _, out = self.turn(nine, {"MILK": 20, "WOOL": 20}, {"MILK": [(304, 12)], "WOOL": [(304, 12)]})
        self.assertEqual(len(out["market"]), 10)
        self.assertEqual(out["market"][1:], nine)

    def test_does_not_resell_what_w3_already_sells(self):
        # W3 already sells all 12 milk in the shed this turn: nothing left to add.
        w3 = [["SELL", "MILK", 12]]
        base, out = self.turn(w3, {"MILK": 12}, {"MILK": [(304, 12)]})
        self.assertIs(out, base)
        # With 20 in the shed, only units beyond W3's 12 can be added.
        _, out = self.turn(w3, {"MILK": 20}, {"MILK": [(304, 12)]})
        self.assertLessEqual(out["market"][0][2], 8)
        self.assertEqual(out["market"][1:], w3)

    def test_no_prediction_or_flag_off(self):
        base, out = self.turn([], {"MILK": 20}, {})
        self.assertIs(out, base)
        self.ns["WB_FRONTRUN_ON"] = False
        base, out = self.turn([], {"MILK": 20}, {"MILK": [(304, 12)]})
        self.assertIs(out, base)


if __name__ == "__main__":
    unittest.main()
