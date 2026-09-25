"""WB_ValueModel (experiments/splice/value_model.py).

The yield simulation must equal the engine's own rules: every crop, fertilized at every
age, planted early and late, is replayed through kaggriculture._apply_unit_action,
_daily_refresh_plants and _decay_plants and compared unit for unit. Then the decision
helpers: fertilize_value (apply / sell) and crop_value (per tile-day).

Run with:
    .venv/Scripts/python.exe -m unittest tests.test_splice_value_model -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "experiments", "splice"))

import value_model as vmmod  # noqa: E402
from price_model import WB_PriceModel  # noqa: E402
from value_model import (WB_VM_CROPS, WB_ValueModel, WB_vm_harvests,  # noqa: E402
                         WB_vm_marginal_units)

try:
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
except ImportError:  # pragma: no cover
    K = None

PM = WB_PriceModel()
I0 = 10000


def engine_units(crop, fert_ages=(), plant_day=0):
    """Plant on (0,0), FERTILIZE (when scheduled) then WATER every day, harvest one-shot
    crops at max_yield_day or on day 29, ongoing crops daily; run the end-of-day rules."""
    farm = {"money": 0.0, "tiles": [[None] * 10 for _ in range(10)], "farmer": [0, 0], "hands": [],
            "unlocked_quadrants": ["NW"], "hires_today": 0}
    priv = {"shed": {}, "seeds": {crop: 1}, "inventories": [{"FERTILIZER": 10}]}
    total = 0
    K._apply_unit_action(farm, priv, 0, ["PLANT", crop], 10, plant_day, 24)
    cd = K.CROPS[crop]
    for d in range(plant_day, 30):
        tile = farm["tiles"][0][0]
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
            break
        if d - plant_day in fert_ages:
            K._apply_unit_action(farm, priv, 0, ["FERTILIZE"], 10, d, 24)
        K._apply_unit_action(farm, priv, 0, ["WATER"], 10, d, 24)
        last = d == 29 and d - plant_day >= cd["first_yield_day"]
        if cd["ongoing"] or d - plant_day == cd["max_yield_day"] or last:
            inv = priv["inventories"][0]
            before = inv.get(crop, 0)
            K._apply_unit_action(farm, priv, 0, ["HARVEST"], 10, d, 24)
            total += inv.get(crop, 0) - before
        if d <= vmmod.WB_VM_LAST_EOD:
            K._daily_refresh_plants(farm, d, 24)
            K._decay_plants(farm, (d + 1) * 24)
    return total


@unittest.skipIf(K is None, "kaggle_environments not installed")
class TestYieldsMatchEngine(unittest.TestCase):
    def test_tables_match_engine(self):
        for crop, cd in WB_VM_CROPS.items():
            for key in ("seed", "first_yield_day", "max_yield_day", "interval", "max_yield", "ongoing"):
                self.assertEqual(cd[key], K.CROPS[crop][key], (crop, key))

    def test_one_fertilize_at_every_age(self):
        for crop in WB_VM_CROPS:
            base = engine_units(crop)
            for age in range(0, 17):
                self.assertEqual(engine_units(crop, (age,)) - base, WB_vm_marginal_units(crop, age), (crop, age))

    def test_plans_and_late_plantings(self):
        for crop in WB_VM_CROPS:
            plan = vmmod.WB_VM_FERT_PLAN[crop]
            for p in (0, 12, 18, 20, 24, 26, 27):
                want = engine_units(crop, plan, p)
                got = sum(u for _, u in WB_vm_harvests(crop, p, p, fert_days=tuple(p + a for a in plan)))
                self.assertEqual(got, want, (crop, p))

    def test_headline_units(self):
        expect = {"WHEAT": (4, 6), "CARROT": (3, 4), "TOMATO": (4, 8), "STRAWBERRY": (4, 8), "MELON": (6, 6)}
        for crop, (plain, fert) in expect.items():
            self.assertEqual(sum(u for _, u in WB_vm_harvests(crop, 0, 0)), plain)
            plan = vmmod.WB_VM_FERT_PLAN[crop]
            self.assertEqual(sum(u for _, u in WB_vm_harvests(crop, 0, 0, fert_days=plan)), fert)


def market(**prices_at):
    inv = {p: I0 for p in PM.params}
    inv.update(prices_at)
    return {"inventory": inv}


def plant(crop, planted_day, **kw):
    t = {"kind": "PLANT", "crop": crop, "planted_day": planted_day, "watered_today": False,
         "yield_units": 0 if WB_VM_CROPS[crop]["ongoing"] else 1, "fertilized_until_day": -1}
    t.update(kw)
    return t


class TestFertilizeValue(unittest.TestCase):
    def setUp(self):
        self.vm = WB_ValueModel(PM)

    def test_wheat_pays_only_when_fertilizer_is_cheap(self):
        tile = plant("WHEAT", 10, yield_units=1)             # age 2 today, window starts
        dear = self.vm.fertilize_value(tile, 12, market())   # fertilizer 100, wheat 25 -> +2 x 25 < 100
        self.assertEqual(dear["extra_units"], 2)
        self.assertFalse(dear["apply"])
        cheap = self.vm.fertilize_value(tile, 12, market(FERTILIZER=I0 + 400))   # fertilizer 20
        self.assertEqual(cheap["cost"], 20.0)
        self.assertTrue(cheap["apply"])
        self.assertEqual(cheap["gain"], 2 * 25)

    def test_strawberry_production_day_always_pays(self):
        r = self.vm.fertilize_value(plant("STRAWBERRY", 5), 14, market())   # age 9: covers events 9 and 11
        self.assertEqual(r["extra_units"], 2)
        self.assertTrue(r["apply"])

    def test_melon_never(self):
        r = self.vm.fertilize_value(plant("MELON", 5, yield_units=2), 12, market(FERTILIZER=I0 + 480))
        self.assertEqual(r["extra_units"], 0)
        self.assertFalse(r["apply"])

    def test_already_fertilized_or_watered_first(self):
        covered = plant("WHEAT", 10, yield_units=1, fertilized_until_day=14)
        self.assertEqual(self.vm.fertilize_value(covered, 12, market())["extra_units"], 0)
        # Watered already at age 3: today's bonus is spent, the application only covers age 4.
        wet = plant("WHEAT", 10, yield_units=3, watered_today=True)
        self.assertEqual(self.vm.fertilize_value(wet, 13, market())["extra_units"], 1)
        dry = plant("WHEAT", 10, yield_units=2)
        self.assertEqual(self.vm.fertilize_value(dry, 13, market())["extra_units"], 2)

    def test_not_a_plant(self):
        self.assertFalse(self.vm.fertilize_value({"kind": "PASTURE", "animal": "COW"}, 12, market())["apply"])
        self.assertFalse(self.vm.fertilize_value(None, 12, market())["apply"])


class TestCropValue(unittest.TestCase):
    def setUp(self):
        self.vm = WB_ValueModel(PM)

    def test_fields_and_fertilizer_plan(self):
        r = self.vm.crop_value("WHEAT", 16, scenario="tape")
        for key in ("units", "revenue", "net", "tile_days", "per_tile_day", "labor", "per_labor", "fert_days"):
            self.assertIn(key, r)
        self.assertEqual(r["units"], 6)                     # fertilizer at age 2 pays by day 18 (fert 37)
        self.assertEqual(r["fert_days"], [18])
        self.assertEqual(r["tile_days"], 5)

    def test_late_strawberry_loses_to_the_tape_glut(self):
        early = self.vm.crop_value("STRAWBERRY", 8, scenario="tape")["per_tile_day"]
        late = self.vm.crop_value("STRAWBERRY", 14, scenario="tape")["per_tile_day"]
        self.assertGreater(early, 30)
        self.assertLess(late, 10)

    def test_crops_that_cannot_finish_yield_nothing(self):
        self.assertEqual(self.vm.crop_value("TOMATO", 22, scenario="tape")["units"], 0)
        self.assertEqual(self.vm.crop_value("STRAWBERRY", 20, scenario="nontape")["units"], 0)

    def test_live_market_uses_the_shops(self):
        # Three tomato shops drain the tomato market: planting into it beats typical shops.
        m = {"inventory": {"TOMATO": I0 - 250, "FERTILIZER": I0}}
        rich = self.vm.crop_value("TOMATO", 12, market=m, shops=["PIZZA_SHOP", "FARMERS_MARKET", "PIZZA_SHOP"])
        poor = self.vm.crop_value("TOMATO", 12, market=m, shops=[])
        self.assertGreater(rich["per_tile_day"], poor["per_tile_day"])

    def test_top_level_names_are_prefixed(self):
        for name in vars(vmmod):
            if name.startswith("__") or name == "WB_PriceModel":
                continue
            self.assertTrue(name.startswith(("WB_", "_wb_")), name)


if __name__ == "__main__":
    unittest.main()
