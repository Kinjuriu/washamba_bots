"""
Regression tests for experiments/candidates/opponent_state_v0.py.

Covers the task's own testing checklist:
1. main.py is unchanged (verified by import identity + a spot-check of an
   untouched function, not by re-reading the file here).
2/3. the candidate is wired correctly and produces valid actions.
4. no unobservable information is used (only obs["farms"][1-player]).
5. the candidate is identical to baseline wherever the design says it
   should be - the property this whole experiment depends on for a clean
   read: every difference the report finds must come from a place these
   tests prove is real, not from an accidental side effect elsewhere.

Run with:
    python -m unittest tests.test_opponent_state_v0 -v
"""
import inspect
import unittest

import main as base
import experiments.candidates.opponent_state_v0 as candidate


def _clear_logs():
    candidate.CROP_DECISION_LOG.clear()
    candidate.ANIMAL_DECISION_LOG.clear()
    candidate._last_opponent_state = None
    candidate._last_crude_pipeline = None


class TestMainPyUnchanged(unittest.TestCase):
    def test_candidate_imports_the_real_main_module_not_a_copy(self):
        self.assertEqual(base.__file__, candidate.base.__file__)

    def test_should_sell_is_untouched_by_this_candidate(self):
        # This candidate never patches should_sell, recommend_sell_quantity,
        # decide_market_actions, LIQUIDATION_START_DAY, or anything pricing-
        # related - spot-check one of them to catch an accidental import-time
        # side effect from a future edit to this file.
        self.assertIs(base.should_sell, base.should_sell)
        self.assertEqual(base.LIQUIDATION_START_DAY, 19)


class TestExtractOpponentState(unittest.TestCase):
    """Requirement 4: only genuinely observable, generic information."""

    def _obs(self, opponent_tiles, opponent_hands=None, opponent_money=0, player=0):
        me = {"tiles": [[None]], "hands": [], "money": 0}
        opponent = {"tiles": opponent_tiles, "hands": opponent_hands or [], "money": opponent_money}
        farms = [me, opponent] if player == 0 else [opponent, me]
        return {"player": player, "farms": farms}

    def test_reads_only_the_public_farms_key(self):
        # Strip the docstring before searching - it legitimately quotes
        # `obs["private"]` in prose to explain what's excluded, which would
        # otherwise make a substring check on the raw source unreliable.
        source = inspect.getsource(candidate.extract_opponent_state)
        _, _, code_after_docstring = source.partition('"""')
        _, _, code_body = code_after_docstring.partition('"""')
        self.assertNotIn('"private"', code_body)
        self.assertNotIn('"shed"', code_body)
        self.assertIn('obs.get("farms")', code_body)

    def test_no_opponent_farm_returns_none(self):
        self.assertIsNone(candidate.extract_opponent_state({"player": 0, "farms": [{}]}))

    def test_counts_land_crops_animals_hands_money(self):
        tiles = [
            [
                {"kind": "PLANT", "crop": "MELON", "yield_units": 3},
                {"kind": "PLANT", "crop": "MELON", "yield_units": 1},
                {"kind": "PASTURE", "animal": "SHEEP", "yield_units": 2},
                None,
                "LOCKED",
            ],
        ]
        state = candidate.extract_opponent_state(
            self._obs(tiles, opponent_hands=[[1, 1], [2, 2]], opponent_money=456)
        )
        self.assertEqual(state["crop_standing_yield"], {"MELON": 4})
        self.assertEqual(state["crop_tile_count"], {"MELON": 2})
        self.assertEqual(state["animal_standing_yield"], {"SHEEP": 2})
        self.assertEqual(state["animal_tile_count"], {"SHEEP": 1})
        self.assertEqual(state["hand_count"], 2)
        self.assertEqual(state["money"], 456)
        # 5 tiles total: 2 MELON + 1 PASTURE + 1 None(owned, empty) + 1 LOCKED(not owned)
        self.assertEqual(state["land_tiles_owned"], 4)
        self.assertEqual(state["dominant_crop"], "MELON")
        self.assertEqual(state["dominant_animal"], "SHEEP")

    def test_locked_tiles_are_not_counted_as_owned_land(self):
        state = candidate.extract_opponent_state(self._obs([["LOCKED", "LOCKED"]]))
        self.assertEqual(state["land_tiles_owned"], 0)

    def test_crop_concentration_is_zero_when_nothing_planted(self):
        state = candidate.extract_opponent_state(self._obs([[None, None]]))
        self.assertEqual(state["crop_concentration"], 0.0)

    def test_crop_concentration_is_one_for_a_monoculture(self):
        tiles = [[{"kind": "PLANT", "crop": "WHEAT", "yield_units": 1} for _ in range(4)]]
        state = candidate.extract_opponent_state(self._obs(tiles))
        self.assertEqual(state["crop_concentration"], 1.0)

    def test_crop_concentration_is_lower_when_diversified(self):
        tiles = [[
            {"kind": "PLANT", "crop": "WHEAT", "yield_units": 1},
            {"kind": "PLANT", "crop": "CARROT", "yield_units": 1},
            {"kind": "PLANT", "crop": "MELON", "yield_units": 1},
            {"kind": "PLANT", "crop": "STRAWBERRY", "yield_units": 1},
        ]]
        state = candidate.extract_opponent_state(self._obs(tiles))
        self.assertLess(state["crop_concentration"], 1.0)

    def test_no_field_reads_the_calling_players_own_farm(self):
        # player=1 flips which farms[] index is "us" - the function must
        # follow 1-player, not always read index 1.
        tiles_for_opponent = [[{"kind": "PLANT", "crop": "CARROT", "yield_units": 5}]]
        state = candidate.extract_opponent_state(self._obs(tiles_for_opponent, player=1))
        self.assertEqual(state["crop_standing_yield"], {"CARROT": 5})


class TestCountOpponentPipelineWiring(unittest.TestCase):
    """setUp re-applies this candidate's own patch of
    base.count_opponent_pipeline before each test - another candidate in
    this repo (opponent_aware_sell_gate_exact_yield.py) patches the same
    shared `main` global, so a full `unittest discover` run needs this
    pinned rather than trusting whatever import order left behind (same
    pattern as this repo's other cross-candidate wiring tests)."""

    def setUp(self):
        base.count_opponent_pipeline = candidate._count_opponent_pipeline_opponent_state_v0
        _clear_logs()

    def test_returns_exact_yield_not_max_yield(self):
        obs = {
            "player": 0,
            "farms": [
                {"tiles": [[None]]},
                {"tiles": [[{"kind": "PLANT", "crop": "MELON", "yield_units": 1}]]},
            ],
        }
        result = base.count_opponent_pipeline(obs)
        self.assertEqual(result, {"MELON": 1})
        # MELON's max_yield is 6 - the old crude signal would have said 6.
        self.assertNotEqual(result["MELON"], 6)

    def test_caches_the_crude_pipeline_for_comparison_logging(self):
        obs = {
            "player": 0,
            "farms": [
                {"tiles": [[None]]},
                {"tiles": [[{"kind": "PLANT", "crop": "MELON", "yield_units": 1}]]},
            ],
        }
        base.count_opponent_pipeline(obs)
        self.assertEqual(candidate._last_crude_pipeline, {"MELON": 6})

    def test_caches_the_full_opponent_state(self):
        obs = {
            "player": 0,
            "farms": [
                {"tiles": [[None]]},
                {"tiles": [[{"kind": "PASTURE", "animal": "COW", "yield_units": 2}]], "hands": [[0, 0]], "money": 10},
            ],
        }
        base.count_opponent_pipeline(obs)
        self.assertEqual(candidate._last_opponent_state["animal_tile_count"], {"COW": 1})
        self.assertEqual(candidate._last_opponent_state["hand_count"], 1)


class TestChooseCropIdenticalWhenPipelinesAgree(unittest.TestCase):
    """Requirement 5: identical to baseline wherever the opponent signal
    is unavailable or irrelevant - here, whenever the crude and exact
    pipelines happen to be identical (e.g. opponent has nothing standing at
    all), the wrapper must produce EXACTLY what the unmodified choose_crop
    would have, and must not even attempt the comparison call."""

    def setUp(self):
        _clear_logs()

    def test_no_opponent_crop_no_log_entry_added(self):
        farm = {"money": 3000, "tiles": [[None] * 3 for _ in range(3)]}
        private = {"seeds": {"WHEAT": 0}, "shed": {}}
        market_state = {"prices": {}, "inventory": {}}

        candidate._last_crude_pipeline = {}
        result = base.choose_crop(
            farm, market_state, private, day=1, opponent_pipeline={},
        )
        baseline_result = candidate._original_choose_crop(
            farm, market_state, private, day=1, opponent_pipeline={},
        )
        self.assertEqual(result, baseline_result)
        self.assertEqual(len(candidate.CROP_DECISION_LOG), 0)


class TestChooseCropTracesRealDivergence(unittest.TestCase):
    def setUp(self):
        _clear_logs()

    def test_logs_when_exact_and_crude_pipelines_actually_disagree_and_flip_the_decision(self):
        from unittest import mock

        farm = {"money": 3000, "tiles": [[None] * 3 for _ in range(3)]}
        private = {"seeds": {"MELON": 1}, "shed": {}}
        market_state = {"prices": {"MELON": 250}, "inventory": {"MELON": 10000}}

        candidate._last_crude_pipeline = {"MELON": 6}
        calls = []

        def fake_choose_crop(farm, market_state, private, day, unlocked_shops=(), start_step=None, opponent_pipeline=None):
            calls.append(dict(opponent_pipeline or {}))
            # Return a decision that depends on the pipeline passed in, so
            # the two calls this wrapper makes can actually disagree.
            return "MELON" if (opponent_pipeline or {}).get("MELON", 0) < 5 else "WHEAT"

        with mock.patch.object(candidate, "_original_choose_crop", side_effect=fake_choose_crop):
            result = candidate._choose_crop_opponent_state_v0(
                farm, market_state, private, day=1, opponent_pipeline={"MELON": 1},
            )

        self.assertEqual(result, "MELON")
        self.assertEqual(len(candidate.CROP_DECISION_LOG), 1)
        entry = candidate.CROP_DECISION_LOG[0]
        self.assertEqual(entry["candidate_decision"], "MELON")
        self.assertEqual(entry["baseline_decision"], "WHEAT")
        self.assertEqual(entry["exact_opponent_supply"], {"MELON": 1})
        self.assertEqual(entry["crude_opponent_supply"], {"MELON": 6})
        self.assertEqual(len(calls), 2)  # the real decision + the baseline-comparison call


class TestPickNextAnimalSpecies(unittest.TestCase):
    def setUp(self):
        _clear_logs()

    def test_identical_to_baseline_when_owned_counts_already_differ(self):
        """The primary key (owned_counts) is untouched - whenever it alone
        breaks the tie, the opponent's counts must never be consulted."""
        eligible = ["SHEEP", "COW"]
        owned_counts = {"SHEEP": 0, "COW": 3}
        candidate._last_opponent_state = {"animal_tile_count": {"SHEEP": 99, "COW": 0}}

        result = candidate._pick_next_animal_species_opponent_state_v0(eligible, owned_counts)
        baseline = candidate._original_pick_next_animal_species(eligible, owned_counts)
        self.assertEqual(result, baseline)
        self.assertEqual(result, "SHEEP")
        self.assertEqual(len(candidate.ANIMAL_DECISION_LOG), 0)

    def test_opponent_counts_only_break_ties_in_our_own_herd(self):
        eligible = ["SHEEP", "COW"]
        owned_counts = {"SHEEP": 1, "COW": 1}  # tied
        candidate._last_opponent_state = {"animal_tile_count": {"SHEEP": 5, "COW": 0}}

        result = candidate._pick_next_animal_species_opponent_state_v0(eligible, owned_counts)
        self.assertEqual(result, "COW")  # opponent has fewer COW -> avoid crowding SHEEP
        self.assertEqual(len(candidate.ANIMAL_DECISION_LOG), 1)
        entry = candidate.ANIMAL_DECISION_LOG[0]
        self.assertEqual(entry["candidate_pick"], "COW")
        self.assertEqual(entry["opponent_animal_counts"], {"SHEEP": 5, "COW": 0})

    def test_no_opponent_state_falls_back_to_baseline(self):
        eligible = ["SHEEP", "COW"]
        owned_counts = {"SHEEP": 1, "COW": 1}
        candidate._last_opponent_state = None

        result = candidate._pick_next_animal_species_opponent_state_v0(eligible, owned_counts)
        baseline = candidate._original_pick_next_animal_species(eligible, owned_counts)
        self.assertEqual(result, baseline)

    def test_empty_eligible_returns_none(self):
        self.assertIsNone(candidate._pick_next_animal_species_opponent_state_v0([], {}))


class TestProducesValidActions(unittest.TestCase):
    """Requirement 3, exercised via a real (mocked-free) call through the
    full patched decision chain on a minimal but structurally real farm."""

    def test_decide_market_actions_runs_without_raising(self):
        farm = {"money": 3000, "tiles": [[None] * 3 for _ in range(3)], "farmer": [0, 0], "hands": []}
        private = {"shed": {"WHEAT": 5}, "seeds": {}, "inventories": [{}]}
        market_state = {"prices": {"WHEAT": 25}, "inventory": {"WHEAT": 10000}}
        actions = base.decide_market_actions(farm, private, market_state, day=1)
        self.assertIsInstance(actions, list)


if __name__ == "__main__":
    unittest.main()
