"""WB_SellEngine (experiments/splice/sell_engine.py): the contract Builder B relies on.

Hard guarantees: never sells more than `sellable`, never returns more than `slots`
orders, only emits well-formed SELL orders, runs under 20 ms. Behaviour: glut regime
sells the whole release on any turn; healthy markets get FABLE drain+headroom slices on
the cadence turn (obs["step"] % 4 == 1 by default); the mirror-tuned switches
(healthy_phases, contested_dumps); bounded scarcity-taking; endgame; shed valve.

Run with:
    .venv/Scripts/python.exe -m unittest tests.test_splice_sell_engine -v
"""
import os
import random
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments", "splice"))

import sell_engine as semod  # noqa: E402
from price_model import WB_PRODUCTS, WB_SHOPS, WB_PriceModel  # noqa: E402
from sell_engine import WB_SellEngine  # noqa: E402

I0 = 10000
PM = WB_PriceModel()
# Day 9, hour 5: a post-drain turn (step % 4 == 1) whose preceding tick is not a town-centre tick.
EARLY = 9 * 24 + 5


def make_obs(step, inventory=None, shops=(), shed=None, carried=None):
    inv = {p: I0 for p in WB_PRODUCTS}
    inv.update(inventory or {})
    return {
        "step": step,
        "day": step // 24,
        "hour": step % 24,
        "market": {"inventory": inv, "prices": {p: PM.quote(p, inv[p]) for p in WB_PRODUCTS}},
        "town": {"unlocked_shops": list(shops)},
        "private": {"shed": dict(shed or {}), "seeds": {}, "inventories": [dict(c) for c in (carried or [{}])]},
    }


def qty(orders, item):
    return sum(o[2] for o in orders if o[1] == item)


class TestContract(unittest.TestCase):
    def setUp(self):
        self.se = WB_SellEngine(PM)
        self.rng = random.Random(3)

    def _random_case(self):
        step = self.rng.randint(192, 718)
        inv = {p: I0 + self.rng.randint(-400, 300) for p in WB_PRODUCTS}
        shops = [self.rng.choice(sorted(WB_SHOPS)) for _ in range(self.rng.randint(0, 8))]
        sellable = {p: self.rng.randint(0, 60) for p in self.rng.sample(WB_PRODUCTS, self.rng.randint(1, 9))}
        shed = {p: n + self.rng.randint(0, 10) for p, n in sellable.items()}
        shed["WHEAT"] = shed.get("WHEAT", 0) + self.rng.randint(0, 40)
        slots = self.rng.randint(0, 10)
        return make_obs(step, inv, shops, shed), sellable, slots

    def test_never_exceeds_sellable_or_slots(self):
        for phases, dumps in (((1,), False), ((0, 1, 2, 3), True)):
            self.se.healthy_phases, self.se.contested_dumps = phases, dumps
            for _ in range(2000):
                obs, sellable, slots = self._random_case()
                orders = self.se.orders(obs, sellable, slots)
                self.assertLessEqual(len(orders), slots)
                seen = set()
                for o in orders:
                    self.assertEqual(o[0], "SELL")
                    self.assertIsInstance(o[2], int)
                    self.assertGreater(o[2], 0)
                    self.assertNotIn(o[1], seen)            # one order per product
                    seen.add(o[1])
                    self.assertLessEqual(o[2], sellable.get(o[1], 0))

    def test_zero_slots_or_nothing_to_sell(self):
        obs = make_obs(EARLY, shops=["YARN_STORE"], shed={"WOOL": 10})
        self.assertEqual(self.se.orders(obs, {"WOOL": 10}, 0), [])
        self.assertEqual(self.se.orders(obs, {}, 10), [])
        self.assertEqual(self.se.orders(obs, {"WOOL": 0, "SHEEP": 3, "NOPE": 5}, 10), [])

    def test_slot_zero_is_dearest(self):
        obs = make_obs(718, shed={p: 5 for p in WB_PRODUCTS})
        orders = self.se.orders(obs, {p: 5 for p in WB_PRODUCTS}, 10)
        quotes = [PM.quote(o[1], I0) for o in orders]
        self.assertEqual(quotes, sorted(quotes, reverse=True))
        self.assertEqual(orders[0][1], "MELON")

    def test_truncation_keeps_highest_revenue(self):
        obs = make_obs(718, shed={"EGG": 40, "WOOL": 1, "CARROT": 1})
        orders = self.se.orders(obs, {"EGG": 40, "WOOL": 1, "CARROT": 1}, 1)
        self.assertEqual(orders, [["SELL", "EGG", 40]])

    def test_under_20ms(self):
        # Worst case on purpose: every product released, a shed far past the cap (the
        # valve sheds ~500 units), both engine configs. Judged by the median of repeated
        # calls so a scheduler preemption on a loaded box is not mistaken for the cost.
        obs = make_obs(413, {p: I0 - 300 for p in WB_PRODUCTS},
                       ["YARN_STORE", "PIZZA_SHOP", "BAKERY", "FARMERS_MARKET"],
                       {p: 60 for p in WB_PRODUCTS}, [{"WOOL": 30}, {"EGG": 20}])
        obs["player"] = 0
        obs["farms"] = [_farm(), _farm("COW", "SHEEP", "GOOSE", "PLANT:TOMATO")]
        sellable = {p: 60 for p in WB_PRODUCTS}
        for dumps in (False, True):
            self.se.contested_dumps = dumps
            for step in (413, 414, 700, 718):
                obs["step"] = step
                times = []
                for _ in range(25):
                    t = time.perf_counter()
                    self.se.orders(obs, sellable, 10)
                    times.append(time.perf_counter() - t)
                times.sort()
                self.assertLess(times[len(times) // 2], 0.020, (dumps, step))

    def test_instances_do_not_share_state(self):
        a, b = WB_SellEngine(PM), WB_SellEngine(PM)
        a.healthy_phases, a.contested_dumps = (0, 1, 2, 3), True
        self.assertEqual((b.healthy_phases, b.contested_dumps), ((1,), False))
        self.assertEqual((WB_SellEngine.healthy_phases, WB_SellEngine.contested_dumps), ((1,), False))

    def test_top_level_names_are_prefixed(self):
        for name in vars(semod):
            if name.startswith("__") or name in ("WB_PriceModel",):
                continue
            self.assertTrue(name.startswith(("WB_", "_wb_")), name)


class TestCadenceGating(unittest.TestCase):
    """healthy_phases gates the healthy regime by obs["step"] % 4 (phase 1 is the first
    post-drain call); the glut regime ignores it."""

    def test_default_is_phase_one_only(self):
        se = WB_SellEngine(PM)
        shops = ["YARN_STORE", "SMOOTHIE_SHOP"]
        for step in range(240, 260):
            obs = make_obs(step, shops=shops, shed={"WOOL": 12, "MILK": 12})
            orders = se.orders(obs, {"WOOL": 12, "MILK": 12}, 10)
            if step % 4 == 1:
                self.assertGreater(qty(orders, "WOOL"), 0, step)
                self.assertGreater(qty(orders, "MILK"), 0, step)
            else:
                self.assertEqual(orders, [], step)

    def test_skip_pre_drain_phase(self):
        se = WB_SellEngine(PM)
        se.healthy_phases = (1, 2, 3)
        for step in range(240, 252):
            obs = make_obs(step, shops=["YARN_STORE"], shed={"WOOL": 6})
            sold = qty(se.orders(obs, {"WOOL": 6}, 10), "WOOL")
            self.assertEqual(sold == 0, step % 4 == 0, step)

    def test_every_turn_option(self):
        se = WB_SellEngine(PM)
        se.healthy_phases = (0, 1, 2, 3)
        for step in range(240, 248):
            obs = make_obs(step, shops=["YARN_STORE"], shed={"WOOL": 6})
            self.assertGreater(qty(se.orders(obs, {"WOOL": 6}, 10), "WOOL"), 0, step)

    def test_glut_ignores_gating(self):
        se = WB_SellEngine(PM)
        se.healthy_phases = (1,)
        obs = make_obs(EARLY + 1, {"WOOL": I0 + 30}, ["YARN_STORE"], {"WOOL": 17})
        self.assertEqual(se.orders(obs, {"WOOL": 17}, 10), [["SELL", "WOOL", 17]])


class TestHealthySlices(unittest.TestCase):
    """Healthy regime: a consuming shop exists and the market is within half a day of
    drain above I0. FABLE slices: last tick's drain + a share of the headroom below I0."""

    def setUp(self):
        self.se = WB_SellEngine(PM)

    def test_slice_is_drain_sized_at_i0(self):
        # One YARN_STORE drains 2 wool per tick; at I0 there is no headroom to sell into.
        obs = make_obs(EARLY, shops=["YARN_STORE"], shed={"WOOL": 6})
        self.assertEqual(qty(self.se.orders(obs, {"WOOL": 6}, 10), "WOOL"), 2)

    def test_stock_clears_within_hold_windows(self):
        # 30 wool must clear within 6 selling turns: ceil(30 / 6) = 5 > drain 2.
        obs = make_obs(EARLY, shops=["YARN_STORE"], shed={"WOOL": 30})
        self.assertEqual(qty(self.se.orders(obs, {"WOOL": 30}, 10), "WOOL"), 5)

    def test_headroom_share_below_i0(self):
        obs = make_obs(EARLY, {"WOOL": I0 - 40}, ["YARN_STORE"], {"WOOL": 30})
        # tick drain 2 + ceil(0.2 * 40) = 10
        self.assertEqual(qty(self.se.orders(obs, {"WOOL": 30}, 10), "WOOL"), 10)

    def test_off_phase_waits(self):
        obs = make_obs(EARLY + 1, shops=["YARN_STORE"], shed={"WOOL": 6})
        self.assertEqual(self.se.orders(obs, {"WOOL": 6}, 10), [])

    def test_unpaced_staples_sell_whole_release(self):
        obs = make_obs(EARLY, shops=["BAKERY"], shed={"EGG": 45})
        self.assertEqual(qty(self.se.orders(obs, {"EGG": 45}, 10), "EGG"), 45)

    def test_clearance_counts_selling_turns_only(self):
        # Phase-1 turns left from 709: 709 713 717 + final = 4 -> ceil(35 / 4) = 9.
        obs = make_obs(29 * 24 + 13, shops=["YARN_STORE"], shed={"WOOL": 35})
        self.assertEqual(self.se.selling_turns_left(709), 4)
        self.assertEqual(qty(self.se.orders(obs, {"WOOL": 35}, 10), "WOOL"), 9)
        # Every turn: 709..717 + final = 10 turns, capped at hold_windows 6 -> ceil(35 / 6) = 6.
        self.se.healthy_phases = (0, 1, 2, 3)
        self.assertEqual(self.se.selling_turns_left(709), 10)
        self.assertEqual(qty(self.se.orders(obs, {"WOOL": 35}, 10), "WOOL"), 6)


class TestGlutRegime(unittest.TestCase):
    """Glut regime: holding cannot pay, so the whole release goes on any turn."""

    def setUp(self):
        self.se = WB_SellEngine(PM)

    def test_deep_glut_sells_everything(self):
        # One YARN_STORE: 13 a day, glut above I0 + 6.5. At I0 + 30 sell all 17 now.
        obs = make_obs(EARLY + 1, {"WOOL": I0 + 30}, ["YARN_STORE"], {"WOOL": 17})
        self.assertEqual(self.se.orders(obs, {"WOOL": 17}, 10), [["SELL", "WOOL", 17]])

    def test_no_consuming_shop_is_glut(self):
        # No shop takes WOOL: the price never recovers, the first seller wins.
        obs = make_obs(EARLY + 2, shops=["BAKERY"], shed={"WOOL": 20})
        self.assertEqual(self.se.orders(obs, {"WOOL": 20}, 10), [["SELL", "WOOL", 20]])

    def test_boundary_scales_with_drain(self):
        # I0 + 10 is glut with one YARN_STORE (limit 6.5) but healthy with two (limit 12.5).
        self.assertTrue(self.se.is_glut("WOOL", I0 + 10, ["YARN_STORE"]))
        self.assertFalse(self.se.is_glut("WOOL", I0 + 10, ["YARN_STORE", "YARN_STORE"]))
        self.assertFalse(self.se.is_glut("WOOL", I0 - 50, ["YARN_STORE"]))
        self.assertTrue(self.se.is_glut("MELON", I0 - 50, ["FARMERS_MARKET"]))   # no shop wants melon


def _farm(*things):
    """A 10x10 farm holding the given animals ("SHEEP") or crops ("PLANT:MILK" style)."""
    tiles = [[None] * 10 for _ in range(10)]
    for i, t in enumerate(things):
        if t.startswith("PLANT:"):
            tiles[0][i] = {"kind": "PLANT", "crop": t[6:]}
        else:
            tiles[0][i] = {"kind": "PASTURE", "animal": t}
    return {"tiles": tiles}


class TestContested(unittest.TestCase):
    """A rival producer makes holding back a loss: its next batch lands first."""

    def setUp(self):
        self.se = WB_SellEngine(PM)

    def test_rival_producers(self):
        obs = make_obs(EARLY)
        obs["player"] = 1
        obs["farms"] = [_farm("COW", "GOOSE", "PLANT:STRAWBERRY"), _farm("SHEEP", "PLANT:MELON")]
        self.assertEqual(self.se.rival_producers(obs), {"MILK", "EGG", "FERTILIZER", "STRAWBERRY"})

    def _milk_obs(self, ours, theirs, step=EARLY):
        obs = make_obs(step, shops=["SMOOTHIE_SHOP"], shed={"MILK": 20})
        obs["player"] = 0
        obs["farms"] = [ours, theirs]
        return obs

    def test_default_ignores_rivals(self):
        # Spec default: contested milk is still sliced: tick drain 1, clear ceil(20 / 6) = 4.
        obs = self._milk_obs(_farm(), _farm("COW"))
        self.assertEqual(qty(self.se.orders(obs, {"MILK": 20}, 10), "MILK"), 4)

    def test_contested_dumps_sells_the_whole_release_any_turn(self):
        self.se.contested_dumps = True
        obs = self._milk_obs(_farm(), _farm("COW"), step=EARLY + 2)
        self.assertEqual(self.se.orders(obs, {"MILK": 20}, 10), [["SELL", "MILK", 20]])

    def test_contested_dumps_leaves_uncontested_slices(self):
        self.se.contested_dumps = True
        obs = self._milk_obs(_farm("COW"), _farm("SHEEP"))      # our cow does not count
        self.assertEqual(qty(self.se.orders(obs, {"MILK": 20}, 10), "MILK"), 4)


class _StubPredictor:
    """upcoming() returns the dumps it was given that fall in (step, step + horizon]."""

    def __init__(self, dumps):
        self.dumps = dumps              # {product: [(step, qty), ...]}

    def upcoming(self, obs, product, horizon):
        s = int(obs["step"])
        return [(t, q) for t, q in self.dumps.get(product, ()) if s < t <= s + horizon]


class TestFrontRunning(unittest.TestCase):
    """With a predictor, sell ahead of a predicted opponent dump."""

    def setUp(self):
        self.base = WB_SellEngine(PM)

    def _engine(self, dumps):
        return WB_SellEngine(PM, predictor=_StubPredictor(dumps))

    def test_off_by_default(self):
        self.assertIsNone(self.base.predictor)

    def test_sells_ahead_of_a_dump_off_cadence(self):
        # Healthy milk market, off-cadence turn: without a predictor nothing sells.
        step = EARLY + 1
        obs = make_obs(step, shops=["SMOOTHIE_SHOP"], shed={"MILK": 20})
        self.assertEqual(self.base.orders(obs, {"MILK": 20}, 10), [])
        se = self._engine({"MILK": [(step + 3, 12)]})
        q = qty(se.orders(obs, {"MILK": 20}, 10), "MILK")
        # Units whose quote now is >= the quote right after their 12 land; the SMOOTHIE_SHOP
        # tick at step 224 drains 1 before the dump at 225.
        post = PM.quote("MILK", I0 - 1 + 12)
        self.assertEqual(q, PM.units_at_or_above("MILK", I0, post, 20))
        self.assertEqual(q, 12)

    def test_front_run_goes_to_slot_zero(self):
        step = EARLY + 1
        obs = make_obs(step, {"MELON": I0 + 100}, ["SMOOTHIE_SHOP"], {"MILK": 20, "MELON": 5})
        se = self._engine({"MILK": [(step + 2, 12)]})
        orders = se.orders(obs, {"MILK": 20, "MELON": 5}, 10)
        self.assertEqual(orders[0][1], "MILK")          # dearer melon (glut, sold whole) comes after

    def test_ignores_small_or_current_or_far_dumps(self):
        step = EARLY + 1
        obs = make_obs(step, shops=["SMOOTHIE_SHOP"], shed={"MILK": 20})
        for dumps in ({"MILK": [(step + 2, 3)]},        # below front_run_min_qty
                      {"MILK": [(step, 12)]},           # this call: cannot be beaten
                      {"MILK": [(step + 7, 12)]}):      # beyond the horizon
            self.assertEqual(self._engine(dumps).orders(obs, {"MILK": 20}, 10), [], dumps)

    def test_waits_for_the_post_drain_turn_when_there_is_time(self):
        step = EARLY + 3                                # phase 0: pre-drain
        obs = make_obs(step, shops=["SMOOTHIE_SHOP"], shed={"MILK": 20})
        self.assertEqual(self._engine({"MILK": [(step + 3, 12)]}).orders(obs, {"MILK": 20}, 10), [])
        self.assertGreater(qty(self._engine({"MILK": [(step + 1, 12)]}).orders(obs, {"MILK": 20}, 10), "MILK"), 0)

    def test_never_exceeds_sellable(self):
        step = EARLY + 1
        obs = make_obs(step, shops=["SMOOTHIE_SHOP"], shed={"MILK": 5})
        self.assertEqual(qty(self._engine({"MILK": [(step + 2, 40)]}).orders(obs, {"MILK": 5}, 10), "MILK"), 5)

    def test_product_allowlist(self):
        step = EARLY + 1
        obs = make_obs(step, shops=["SMOOTHIE_SHOP"], shed={"MILK": 20})
        se = self._engine({"MILK": [(step + 3, 12)]})
        se.front_run_products = ("MELON", "STRAWBERRY")
        self.assertEqual(se.orders(obs, {"MILK": 20}, 10), [])
        se.front_run_products = ("MILK",)
        self.assertEqual(qty(se.orders(obs, {"MILK": 20}, 10), "MILK"), 12)

    def test_no_front_run_at_the_floor(self):
        step = EARLY + 1
        obs = make_obs(step, {"WOOL": I0 + 80}, ["YARN_STORE"], {"WOOL": 5})
        se = self._engine({"WOOL": [(step + 2, 20)]})
        # Deep glut sells the whole release anyway; the predictor adds nothing on top.
        self.assertEqual(se.orders(obs, {"WOOL": 5}, 10), [["SELL", "WOOL", 5]])


class TestScarcityTaking(unittest.TestCase):
    def setUp(self):
        self.se = WB_SellEngine(PM)

    def test_bounded_at_1_3_base(self):
        # TOMATO quotes 84 (1.4 x base) at 200 below I0. A full 100-item shed of tomatoes
        # stops where the next unit would fetch under 78 (1.3 x base): more than the
        # paced budget (1 + ceil(0.2 * 200) = 41), less than the stock.
        inv = I0 - 200
        self.assertGreaterEqual(PM.quote("TOMATO", inv), 1.4 * 60)
        obs = make_obs(EARLY, {"TOMATO": inv}, ["PIZZA_SHOP"], {"TOMATO": 100})
        q = qty(self.se.orders(obs, {"TOMATO": 100}, 10), "TOMATO")
        path = PM.sell_path("TOMATO", inv, q + 1)
        self.assertGreaterEqual(min(path[:q]), 1.3 * 60)    # every unit sold >= 78
        self.assertLess(path[q], 1.3 * 60)                  # the next one would not be
        self.assertGreater(q, 41)
        self.assertLess(q, 100)

    def test_small_stock_sells_all_into_scarcity(self):
        obs = make_obs(EARLY, {"TOMATO": I0 - 400}, ["PIZZA_SHOP"], {"TOMATO": 12})
        self.assertEqual(qty(self.se.orders(obs, {"TOMATO": 12}, 10), "TOMATO"), 12)

    def test_not_triggered_below_start(self):
        # CARROT at ~1.35 x base: scarcity-taking must not fire; the paced budget applies.
        inv = next(i for i in range(I0, I0 - 2000, -1) if PM.quote("CARROT", i) >= 1.35 * 35)
        self.assertLess(PM.quote("CARROT", inv), 1.4 * 35)
        obs = make_obs(EARLY, {"CARROT": inv}, ["PET_CAFE"], {"CARROT": 60})
        q = qty(self.se.orders(obs, {"CARROT": 60}, 10), "CARROT")
        headroom = I0 - inv
        self.assertEqual(q, 2 + -(-(2 * headroom) // 10))   # PET_CAFE tick (2) + ceil(0.2 * headroom)


class TestEndgame(unittest.TestCase):
    def setUp(self):
        self.se = WB_SellEngine(PM)

    def test_final_turn_sells_everything(self):
        stock = {p: 7 for p in WB_PRODUCTS}
        stock["WOOL"] = 80                              # well past the $1 floor
        obs = make_obs(718, shed=stock)
        orders = self.se.orders(obs, stock, 10)
        self.assertEqual({o[1]: o[2] for o in orders}, stock)

    def test_final_turn_ignores_gating(self):
        self.se.healthy_phases = (1,)                   # 718 % 4 == 2
        obs = make_obs(718, shops=["SMOOTHIE_SHOP"], shed={"MILK": 30})
        self.assertEqual(self.se.orders(obs, {"MILK": 30}, 10), [["SELL", "MILK", 30]])

    def test_floor_priced_stock_goes_on_the_final_turn(self):
        obs = make_obs(718, {"WOOL": I0 + 70}, shed={"WOOL": 25})
        self.assertEqual(self.se.orders(obs, {"WOOL": 25}, 10), [["SELL", "WOOL", 25]])


class TestShedValve(unittest.TestCase):
    def setUp(self):
        self.se = WB_SellEngine(PM)                     # default gating: an off-phase turn sells nothing by itself

    def test_valve_sells_down_off_phase(self):
        shed = {"WHEAT": 30, "EGG": 40, "WOOL": 28}
        obs = make_obs(12 * 24 + 2, shops=["YARN_STORE", "BAKERY"], shed=shed)
        orders = self.se.orders(obs, {"EGG": 40, "WOOL": 28}, 10)
        self.assertEqual(sum(o[2] for o in orders), 98 - self.se.shed_valve_low)

    def test_carried_goods_count(self):
        obs = make_obs(12 * 24 + 2, shops=["BAKERY"], shed={"EGG": 70}, carried=[{}, {"MILK": 25}])
        orders = self.se.orders(obs, {"EGG": 70}, 10)
        self.assertEqual(qty(orders, "EGG"), 95 - self.se.shed_valve_low)

    def test_no_valve_below_high_water(self):
        obs = make_obs(12 * 24 + 2, shops=["BAKERY"], shed={"EGG": 85})
        self.assertEqual(self.se.orders(obs, {"EGG": 85}, 10), [])


if __name__ == "__main__":
    unittest.main()
