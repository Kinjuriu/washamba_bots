"""Tests for agents/farm2945_rim.py - the sell-advance rim overlay on the 2945 farm.

Three things are pinned here:

1.  The file is agents/public_farm2945.py byte-verbatim below its 8-line header,
    and `agent` is the last callable in the module namespace (kaggle_environments
    takes ``[v for v in env.values() if callable(v)][-1]`` as the entrypoint).

2.  With the shipped flags (RIM_K = None, RIM_OPENING_N = 0) the overlay is inert:
    the base's own constants are untouched and a real seed-0 self-play episode
    returns the base's own banks to the dollar.

3.  The base ALREADY carries a multi-step sell-advance (`_r36_reserve`), a
    quantity-conserving debt ledger (`_r36_suppress`), a sells-to-front reorder
    (`_v224_sales_first`) and the step-0 wheat round trip.  Those facts are
    asserted, because the whole design of this overlay - two knobs rather than a
    second ledger - rests on them.  If a future change removes one of them these
    tests should fail loudly rather than let someone re-add a double-advance.
"""
import os
import unittest
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_PATH = os.path.join(ROOT, "agents", "public_farm2945.py")
RIM_PATH = os.path.join(ROOT, "agents", "farm2945_rim.py")
MARKER = b"# Kaggriculture submission v9/3:"


def _read(path):
    with open(path, "rb") as handle:
        return handle.read()


def _load(path, name, subs=()):
    """Exec an agent file (optionally with source substitutions) as a module."""
    src = _read(path).decode("utf-8")
    for old, new in subs:
        assert old in src, old
        src = src.replace(old, new, 1)
    spec = importlib.util.spec_from_loader(name, loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = path
    exec(compile(src, path, "exec"), mod.__dict__)
    return mod


class TestFileShape(unittest.TestCase):
    def test_base_body_is_byte_verbatim(self):
        base = _read(BASE_PATH)
        rim = _read(RIM_PATH)
        b_off, r_off = base.index(MARKER), rim.index(MARKER)
        body = base[b_off:]
        self.assertEqual(rim[r_off:r_off + len(body)], body,
                         "the base body must be byte-identical below the header")

    def test_only_the_header_and_the_overlay_differ(self):
        base = _read(BASE_PATH)
        rim = _read(RIM_PATH)
        r_off = rim.index(MARKER)
        tail = rim[r_off + len(base) - base.index(MARKER):]
        self.assertIn(b"RIM OVERLAY", tail)
        self.assertNotIn(MARKER, tail, "the overlay must not re-declare base code")

    def test_agent_is_the_last_callable(self):
        names = [k for k, v in vars(RIM).items() if callable(v)]
        self.assertEqual(names[-1], "agent")

    def test_shipped_flags_are_off(self):
        self.assertIsNone(RIM.RIM_K)
        self.assertEqual(RIM.RIM_OPENING_N, 0)

    def test_flags_off_leaves_the_bases_own_race_band_alone(self):
        self.assertEqual((RIM.V9_RACE_DEFAULT, RIM.V9_RACE_MAX), (40, 48))
        self.assertEqual(RIM._RIM_REPORT["rim_k"], -1)


class TestBaseAlreadyHasTheRim(unittest.TestCase):
    """The findings the overlay's design depends on, asserted against the base."""

    def test_the_multi_step_reservation_layer_exists(self):
        self.assertTrue(callable(RIM._r36_reserve))
        self.assertTrue(callable(RIM._r36_suppress))

    def test_the_sells_to_front_reorder_exists(self):
        self.assertTrue(callable(RIM._v224_sales_first))

    def test_sells_to_front_preserves_order_and_respects_the_buy_guard(self):
        act = {"market": [["BUY_SEED", "MELON", 1], ["SELL", "MELON", 3],
                          ["SELL", "WOOL", 2], ["HIRE"]]}
        out = RIM._v224_sales_first(act)["market"]
        self.assertEqual(out, [["SELL", "MELON", 3], ["SELL", "WOOL", 2],
                               ["BUY_SEED", "MELON", 1], ["HIRE"]])
        guarded = {"market": [["BUY_PRODUCT", "WHEAT", 5], ["SELL", "WHEAT", 5]]}
        self.assertEqual(RIM._v224_sales_first(guarded)["market"],
                         [["BUY_PRODUCT", "WHEAT", 5], ["SELL", "WHEAT", 5]])

    def test_the_race_horizon_is_the_bases_own_K_and_it_is_40_to_48(self):
        # min(MAX, max(DEFAULT, lead + MARGIN)) over the reachable lead range.
        seen = {RIM._rim_race_horizon(lead) for lead in range(-20, 120)}
        self.assertEqual(min(seen), 40)
        self.assertEqual(max(seen), 48)

    def test_the_raced_items_are_the_seven_premium_products(self):
        self.assertEqual(set(RIM.V9_RACE_ITEMS),
                         {"CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"})

    def test_the_reservation_window_is_192_to_696(self):
        src = _read(BASE_PATH).decode("utf-8")
        self.assertIn("if not 192<=step<696:return action", src)


class TestHorizonOverride(unittest.TestCase):
    def test_setting_K_collapses_the_race_band_onto_it(self):
        for k in (0, 6, 96):
            mod = _load(RIM_PATH, "rim_k%d" % k, [("\nRIM_K = None\n", "\nRIM_K = %d\n" % k)])
            self.assertEqual((mod.V9_RACE_DEFAULT, mod.V9_RACE_MAX), (k, k))
            self.assertEqual({mod._rim_race_horizon(l) for l in range(-20, 120)}, {k})
            self.assertEqual(mod._RIM_REPORT["rim_k"], k)

    def test_K_zero_disables_the_reservation_entirely(self):
        # _r36_reserve computes end = min(695, step + max(horizon)) and returns
        # immediately when end <= step, so a horizon of 0 is "no advance at all".
        mod = _load(RIM_PATH, "rim_k0x", [("\nRIM_K = None\n", "\nRIM_K = 0\n")])
        self.assertEqual(mod._rim_race_horizon(500), 0)


class TestOpeningMarket(unittest.TestCase):
    BASE_OPEN = [["BUY_PRODUCT", "WHEAT", 20], ["SELL", "WHEAT", 15]]

    def test_resizes_the_existing_round_trip_in_place(self):
        out, applied = RIM._rim_opening_market(self.BASE_OPEN, 30)
        self.assertTrue(applied)
        self.assertEqual(out, [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 15]])

    def test_does_not_mutate_its_input(self):
        original = [list(o) for o in self.BASE_OPEN]
        RIM._rim_opening_market(self.BASE_OPEN, 30)
        self.assertEqual(self.BASE_OPEN, original)

    def test_inserts_the_pair_when_the_base_has_no_wheat_buy(self):
        out, applied = RIM._rim_opening_market([["HIRE"], ["HIRE"]], 30)
        self.assertTrue(applied)
        self.assertEqual(out[:2], [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]])
        self.assertEqual(out[2:], [["HIRE"], ["HIRE"]])

    def test_refuses_rather_than_push_a_base_order_past_index_nine(self):
        market = [["HIRE"]] * 9
        out, applied = RIM._rim_opening_market(market, 30)
        self.assertFalse(applied)
        self.assertEqual(out, market)

    def test_an_empty_market_is_safe(self):
        out, applied = RIM._rim_opening_market([], 30)
        self.assertTrue(applied)
        self.assertEqual(len(out), 2)


class TestControlIsBehaviourIdenticalToTheBase(unittest.TestCase):
    """One real 720-turn episode. Slow (~25s) but it is the only proof that

    matters: the shipped file must reproduce the base's own seed-0 self-play
    banks to the dollar, and must not finish on startingMoney.
    """

    def test_seed_zero_self_play_gate(self):
        from kaggle_environments import make
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 0})
        env.run([RIM_PATH, RIM_PATH])
        left, right = env.steps[-1]
        self.assertEqual([left.status, right.status], ["DONE", "DONE"])
        self.assertNotEqual(left.reward, 3000)
        self.assertNotEqual(right.reward, 3000)
        self.assertEqual((left.reward, right.reward), (72101.0, 72762.0))


RIM = _load(RIM_PATH, "farm2945_rim_under_test")

if __name__ == "__main__":
    unittest.main()
