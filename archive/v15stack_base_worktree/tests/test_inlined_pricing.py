"""The forward-pricing code is inlined into main.py; keep the copies agreeing.

The competition entrypoint is a single `main.py`, so `main.py` cannot
`import pricing` - a bare upload does not carry the module, and the import
fails before the agent is ever called. Locally it works, because running from
the repo root puts `pricing.py` on `sys.path`, which is precisely what makes
the mistake so easy to ship: every local check passes.

So `main.py` carries its own copy and `pricing.py` remains the place to edit.
These tests compare the two **numerically** rather than textually - formatting
or comment changes are fine, a different answer is not.
"""

import ast
import unittest

import main
import pricing

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL")
I0 = 10000


class TestInlinedPricingMatchesModule(unittest.TestCase):
    def test_market_price_agrees_across_the_inventory_range(self):
        for product in PRODUCTS:
            for inventory in range(I0 - 900, I0 + 901, 37):
                self.assertEqual(
                    main.market_price(product, inventory),
                    pricing.market_price(product, inventory),
                    f"{product} at inventory {inventory}",
                )

    def test_price_path_for_sale_agrees(self):
        for product in ("MELON", "STRAWBERRY", "WHEAT"):
            for quantity in (1, 5, 20, 60):
                self.assertEqual(
                    main.price_path_for_sale(product, I0, quantity),
                    pricing.price_path_for_sale(product, I0, quantity),
                    f"{product} x{quantity}",
                )

    def test_estimate_future_price_agrees(self):
        for product in PRODUCTS:
            for horizon in (0, 3, 8, 14):
                self.assertEqual(
                    main.estimate_future_price(product, I0, horizon),
                    pricing.estimate_future_price(product, I0, horizon),
                    f"{product} at horizon {horizon}",
                )

    def test_recommend_sell_quantity_agrees(self):
        for product in ("MELON", "STRAWBERRY", "WOOL", "WHEAT"):
            for held, floor_price in ((10, 50), (60, 150), (200, 20)):
                self.assertEqual(
                    main.recommend_sell_quantity(product, I0, held, floor_price),
                    pricing.recommend_sell_quantity(product, I0, held, floor_price),
                    f"{product} held={held} floor={floor_price}",
                )

    def test_main_does_not_import_pricing(self):
        """The whole point: a bare main.py upload must stand alone.

        Parsed rather than grepped. main.py's own comments explain why the
        import cannot work, so a substring search matches the explanation and
        fails on correct code - which is exactly what happened the first time
        this test was written.
        """
        with open("main.py", encoding="utf-8") as handle:
            tree = ast.parse(handle.read())

        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])

        self.assertNotIn(
            "pricing",
            imported,
            "main.py imports pricing - a bare upload to Kaggle would fail at "
            "import, before the agent is ever called",
        )


if __name__ == "__main__":
    unittest.main()
