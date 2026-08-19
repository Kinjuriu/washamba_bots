"""
Regression tests for experiments/candidates/shed_animal_keyerror_fix.py
(Issue #21, Track C, Experiment 2, corrected packaging).

The candidate is now a genuinely standalone copy of main.py (no `import
main`, verified safe for Kaggle's module-loading behaviour - see
docs/candidate_reports/track_c_large_farm.md's "packaging correction"
entry) with exactly one change: `if product not in MARKET_PARAMS: continue`
added to both of decide_market_actions's shed-iteration loops. Because it's
a standalone copy rather than a wrapper, these tests import it as its own
module (`experiments.candidates.shed_animal_keyerror_fix`) - locally this
is a distinct module name from `main`, so no self-import collision occurs
in this test context (that collision is specific to Kaggle's uploaded-file
loading, which treats the candidate file itself as "main.py").

Confirms:
- unmodified main.decide_market_actions crashes on a shed containing a live
  animal token (positive control - the bug this fix targets is real); and
- the candidate's decide_market_actions does not, on the identical input;
  and
- on any shed with no animal token in it, the two produce byte-identical
  output (behavioural-equivalence check, i.e. the ONLY difference is the
  guard).

Run with:
    python -m unittest tests.test_shed_animal_keyerror_fix -v
"""
import unittest

import main as base
import experiments.candidates.shed_animal_keyerror_fix as candidate

TEST_ANIMAL = base.ACTIVE_ANIMALS[0]  # "SHEEP" on the current roster


def _farm(tiles=None, money=3000):
    return {"money": money, "tiles": tiles or [[None]], "farmer": [0, 0], "hands": []}


def _market_state(prices=None, inventory=None):
    return {
        "prices": prices or {},
        "inventory": inventory or {p: 10000 for p in base.MARKET_PARAMS},
    }


class TestUnmodifiedMainCrashesOnAnimalInShed(unittest.TestCase):
    """Positive control: confirms the bug this fix targets actually exists
    in unmodified main.py, on the same shed shape observed live in
    Experiment 5's trace (WHEAT, FERTILIZER, and a live animal token)."""

    def test_main_decide_market_actions_raises_keyerror(self):
        private = {
            "shed": {"WHEAT": 2, "FERTILIZER": 1, TEST_ANIMAL: 1},
            "inventories": [{}],
        }
        farm = _farm()
        with self.assertRaises(KeyError):
            base.decide_market_actions(farm, private, _market_state(), day=13)


class TestCandidateDoesNotCrashOnAnimalInShed(unittest.TestCase):
    def test_returns_actions_without_raising(self):
        private = {
            "shed": {"WHEAT": 2, "FERTILIZER": 1, TEST_ANIMAL: 1},
            "inventories": [{}],
        }
        farm = _farm()
        # Must not raise - this is the whole point of the fix.
        actions = candidate.decide_market_actions(farm, private, _market_state(), day=13)
        self.assertIsInstance(actions, list)

    def test_does_not_emit_a_sell_order_for_the_live_animal_token(self):
        private = {
            "shed": {"WHEAT": 2, TEST_ANIMAL: 1},
            "inventories": [{}],
        }
        farm = _farm()
        actions = candidate.decide_market_actions(farm, private, _market_state(), day=13)
        sell_products = {a[1] for a in actions if a and a[0] == "SELL"}
        self.assertNotIn(TEST_ANIMAL, sell_products)

    def test_still_sells_a_real_product_present_in_the_same_shed(self):
        # The fix must skip only the non-market key, not the whole turn's
        # selling - a real, sellable product in the same shed should still
        # be evaluated normally.
        private = {
            "shed": {"WOOL": 20, TEST_ANIMAL: 1},
            "inventories": [{}],
        }
        farm = _farm()
        market_state = _market_state(prices={"WOOL": 300})
        actions = candidate.decide_market_actions(farm, private, market_state, day=13)
        sell_products = {a[1] for a in actions if a and a[0] == "SELL"}
        self.assertIn("WOOL", sell_products)

    def test_force_sell_overflow_loop_also_skips_the_live_animal_token(self):
        # Push shed_total past SHED_FORCE_SELL_THRESHOLD so the overflow
        # loop (the second shed-iteration site the fix touches) runs too.
        private = {
            "shed": {"WHEAT": base.SHED_FORCE_SELL_THRESHOLD + 5, TEST_ANIMAL: 1},
            "inventories": [{}],
        }
        farm = _farm()
        actions = candidate.decide_market_actions(farm, private, _market_state(), day=13)
        sell_products = {a[1] for a in actions if a and a[0] == "SELL"}
        self.assertNotIn(TEST_ANIMAL, sell_products)


class TestCandidateIsEquivalentToMainWhenNoAnimalIsInTheShed(unittest.TestCase):
    """Behavioural-equivalence check: on a shed with no live animal token
    (the common case at main.py's own shipped MAX_ANIMALS=4), the candidate
    must return exactly what unmodified main.py returns."""

    def test_identical_output_on_an_ordinary_shed(self):
        private = {
            "shed": {"WHEAT": 5, "MELON": 10, "FERTILIZER": 2},
            "inventories": [{}],
        }
        farm = _farm()
        market_state = _market_state(prices={"MELON": 90})
        original = base.decide_market_actions(farm, private, market_state, day=13)
        fixed = candidate.decide_market_actions(farm, private, market_state, day=13)
        self.assertEqual(original, fixed)

    def test_identical_output_on_an_empty_shed(self):
        private = {"shed": {}, "inventories": [{}]}
        farm = _farm()
        market_state = _market_state()
        original = base.decide_market_actions(farm, private, market_state, day=0)
        fixed = candidate.decide_market_actions(farm, private, market_state, day=0)
        self.assertEqual(original, fixed)


class TestCandidateExposesTheStandardEntrypoint(unittest.TestCase):
    """Regression test for the packaging bug itself: the candidate must not
    depend on `import main` (invalid once Kaggle treats the uploaded file
    as main.py - see docs/candidate_reports/track_c_large_farm.md) and must
    expose `agent = nikaangukia_meroni` as the last binding, matching
    main.py's own documented I/O contract (kaggle_environments picks the
    LAST callable in the module namespace)."""

    def test_module_source_has_no_self_referential_main_import(self):
        import inspect
        source = inspect.getsource(candidate)
        for line in source.splitlines():
            stripped = line.strip()
            self.assertFalse(
                stripped.startswith("import main") or stripped.startswith("from main"),
                f"candidate must not import 'main': found {stripped!r}",
            )

    def test_agent_is_bound_to_nikaangukia_meroni(self):
        self.assertIs(candidate.agent, candidate.nikaangukia_meroni)

    def test_agent_is_the_last_callable_defined_in_the_module(self):
        # Mirrors kaggle_environments/agent.py's own selection rule:
        # [v for v in env.values() if callable(v)][-1].
        module_globals = vars(candidate)
        callables = [v for v in module_globals.values() if callable(v)]
        self.assertIs(callables[-1], candidate.nikaangukia_meroni)


if __name__ == "__main__":
    unittest.main()
