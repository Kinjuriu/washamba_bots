"""
Focused tests for experiments/reconstruct_current_strategies.py.

The alignment test runs a real (tiny) local episode through the actual
kaggle_environments engine rather than a hand-built fixture - the whole
point of that test is to prove the row-alignment convention against
ground truth, not against our own assumption of it.

Run with:
    python -m unittest discover -s tests
"""

import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "experiments"))
import reconstruct_current_strategies as R  # noqa: E402

try:
    from kaggle_environments import make
    HAVE_ENGINE = True
except ImportError:
    HAVE_ENGINE = False


def _synthetic_replay(seat0_actions, seat1_actions, day_hour=None):
    """A minimal two-agent replay dict shaped like a real toJSON() export,
    just enough for the extraction functions under test."""
    n = len(seat0_actions)
    steps = []
    for i in range(n):
        day, hour = (day_hour[i] if day_hour else (i // 24, i % 24))
        obs0 = {
            "day": day, "hour": hour, "step": i, "player": 0,
            "farms": [
                {"money": 100.0 + i, "farmer": [4, 4], "hands": [],
                 "unlocked_quadrants": ["NW"], "hires_today": 0,
                 "tiles": [[None] * 3 for _ in range(3)]},
                {"money": 50.0, "farmer": [5, 5], "hands": [],
                 "unlocked_quadrants": ["NW"], "hires_today": 0},
            ],
            "private": {"shed": {"WHEAT": max(0, 5 - i)}, "seeds": {}, "inventories": [{}]},
            "town": {"unlocked_shops": ["PIZZA_SHOP"] if i >= 2 else []},
            "market": {"prices": {"WHEAT": 37}, "inventory": {"WHEAT": 10000}},
        }
        obs1 = dict(obs0, player=1)
        steps.append([
            {"observation": obs0, "action": seat0_actions[i], "reward": 3000, "status": "ACTIVE"},
            {"observation": obs1, "action": seat1_actions[i], "reward": 3000, "status": "ACTIVE"},
        ])
    return {
        "steps": steps,
        "configuration": {"episodeSteps": n},
        "rewards": [6000.0, 4000.0],
        "info": {"seed": 42, "EpisodeId": 123456},
    }


class TestReplayAlignment(unittest.TestCase):
    @unittest.skipUnless(HAVE_ENGINE, "kaggle_environments not installed")
    def test_same_index_alignment_against_real_engine(self):
        """Ground truth, not assumption: run a real tiny episode and check
        that row i's action really did land in response to row i's own
        observation - not row i-1's, per the docstring's alignment note."""
        env = make("kaggriculture", configuration={"episodeSteps": 5}, debug=False)
        env.run(["main.py", "random"])
        data = env.toJSON()
        # Row 0's action must be a REAL emitted action, not a placeholder -
        # this is the crux of the row-0-placeholder claim being false.
        row0_action = data["steps"][0][0]["action"]
        self.assertIsInstance(row0_action, dict)
        self.assertIn("farmer", row0_action)
        self.assertTrue(row0_action["farmer"], "row 0's farmer action must not be empty/placeholder")
        # observation.step must equal the row index (same-index, not
        # offset) - checked on seat 0, whose observation copy carries it
        # locally (seat 1's local toJSON() copy omits "step" entirely, an
        # unrelated engine quirk; day/hour below is checked on both seats).
        for i, row in enumerate(data["steps"]):
            self.assertEqual(row[0]["observation"]["step"], i)
            for seat in (0, 1):
                obs = row[seat]["observation"]
                expected_day, expected_hour = i // 24, i % 24
                self.assertEqual((obs["day"], obs["hour"]), (expected_day, expected_hour))

    def test_extract_action_stream_uses_same_index(self):
        seat0 = [{"farmer": ["PASS"], "hands": [], "market": []},
                  {"farmer": ["WATER", 1, 1], "hands": [], "market": []}]
        seat1 = [{"farmer": ["DIG", 2, 2], "hands": [], "market": []},
                  {"farmer": ["PASS"], "hands": [], "market": []}]
        replay = _synthetic_replay(seat0, seat1)
        actions = R.extract_action_stream(replay, 0)
        self.assertEqual(actions, seat0)
        actions1 = R.extract_action_stream(replay, 1)
        self.assertEqual(actions1, seat1)


class TestSeatFromManifestOnly(unittest.TestCase):
    """The reconstruction script must never reassign or default a seat -
    it trusts the manifest's already-normalized player_seat (produced by
    pull_episodes.build_manifest_rows, which itself only assigns a seat
    after positively matching the target agent - see test_pull_episodes.py
    for that guarantee)."""

    def test_build_trajectory_uses_given_seat_verbatim(self):
        seat0 = [{"farmer": ["PASS"], "hands": [], "market": []}] * 3
        seat1 = [{"farmer": ["WATER", 0, 0], "hands": [], "market": []}] * 3
        replay = _synthetic_replay(seat0, seat1)
        row = {"player_seat": 1, "episode_id": 1, "player": "P", "player_submission": 1,
               "opponent_name": "Q", "opponent_submission": 2, "opponent_seat": 0,
               "end_time": "t"}
        traj = R.build_trajectory(row, replay, "sha")
        self.assertEqual(traj.target_seat, 1)
        self.assertEqual(traj.actions, seat1)
        self.assertNotEqual(traj.actions, seat0)


class TestCanonicalHashing(unittest.TestCase):
    def test_hash_stable_across_key_order(self):
        a = {"farmer": ["PLANT", "MELON"], "hands": [], "market": [["SELL", "WHEAT", 3]]}
        b = {"market": [["SELL", "WHEAT", 3]], "hands": [], "farmer": ["PLANT", "MELON"]}
        self.assertEqual(R.turn_digest(a), R.turn_digest(b))

    def test_hash_differs_on_real_difference(self):
        a = {"farmer": ["PLANT", "MELON"], "hands": [], "market": []}
        b = {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []}
        self.assertNotEqual(R.turn_digest(a), R.turn_digest(b))

    def test_nested_dict_key_order_also_stable(self):
        a = {"market": [["BUY_SEED", "MELON", 2]], "farmer": None, "hands": [None, None]}
        b = {"hands": [None, None], "market": [["BUY_SEED", "MELON", 2]], "farmer": None}
        self.assertEqual(R.canonical_bytes(a), R.canonical_bytes(b))


class TestDuplicateAndTwoTargetReplay(unittest.TestCase):
    def test_one_replay_two_target_seats_produce_independent_trajectories(self):
        seat0 = [{"farmer": ["PASS"], "hands": [], "market": []},
                  {"farmer": ["HIRE"], "hands": [], "market": [["HIRE"]]}]
        seat1 = [{"farmer": ["WATER", 1, 1], "hands": [], "market": []},
                  {"farmer": ["DIG", 2, 2], "hands": [], "market": []}]
        replay = _synthetic_replay(seat0, seat1)
        row_a = {"player_seat": 0, "episode_id": 555, "player": "PlayerA",
                 "player_submission": 1, "opponent_name": "PlayerB",
                 "opponent_submission": 2, "opponent_seat": 1, "end_time": "t"}
        row_b = {"player_seat": 1, "episode_id": 555, "player": "PlayerB",
                 "player_submission": 2, "opponent_name": "PlayerA",
                 "opponent_submission": 1, "opponent_seat": 0, "end_time": "t"}
        traj_a = R.build_trajectory(row_a, replay, "shared-sha")
        traj_b = R.build_trajectory(row_b, replay, "shared-sha")
        self.assertEqual(traj_a.episode_id, traj_b.episode_id)
        self.assertEqual(traj_a.replay_sha256, traj_b.replay_sha256)
        self.assertNotEqual(traj_a.trajectory_id, traj_b.trajectory_id)
        self.assertNotEqual(traj_a.action_stream_sha256, traj_b.action_stream_sha256)
        # each trajectory's result must be the mirror of the other's
        self.assertEqual(traj_a.result, "win")
        self.assertEqual(traj_b.result, "loss")


class TestActionAgreement(unittest.TestCase):
    def _traj(self, actions, seat=0, eid=1):
        replay = _synthetic_replay(actions, actions)
        row = {"player_seat": seat, "episode_id": eid, "player": "P",
               "player_submission": 1, "opponent_name": "Q",
               "opponent_submission": 2, "opponent_seat": 1 - seat, "end_time": "t"}
        return R.build_trajectory(row, replay, f"sha{eid}")

    def test_exact_agreement_is_full_hash_equal(self):
        acts = [{"farmer": ["PASS"], "hands": [], "market": []}] * 4
        t1 = self._traj(acts, eid=1)
        t2 = self._traj(list(acts), eid=2)  # identical content, different list object
        self.assertEqual(t1.action_stream_sha256, t2.action_stream_sha256)

    def test_partial_agreement_window(self):
        base = [{"farmer": ["PASS"], "hands": [], "market": []}] * 4
        diverged = list(base)
        diverged[3] = {"farmer": ["DIG", 1, 1], "hands": [], "market": []}
        t1 = self._traj(base, eid=1)
        t2 = self._traj(diverged, eid=2)
        agree_all = R.window_agreement(t1, t2, 0, 3)
        agree_prefix = R.window_agreement(t1, t2, 0, 2)
        self.assertAlmostEqual(agree_all, 0.75)
        self.assertEqual(agree_prefix, 1.0)

    def test_first_divergence_turn(self):
        base = [{"farmer": ["PASS"], "hands": [], "market": []}] * 5
        diverged = list(base)
        diverged[2] = {"farmer": ["WATER", 0, 0], "hands": [], "market": []}
        t1 = self._traj(base, eid=1)
        t2 = self._traj(diverged, eid=2)
        self.assertEqual(R.first_divergence_turn(t1, t2), 2)
        self.assertIsNone(R.first_divergence_turn(t1, self._traj(base, eid=3)))


class TestCorruptGzipRejection(unittest.TestCase):
    def test_load_replay_raises_on_invalid_json(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.json.gz"
            with gzip.open(path, "wb") as fh:
                fh.write(b"not json at all")
            with self.assertRaises(Exception):
                R.load_replay(path)

    def test_load_replay_raises_on_missing_required_fields(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "incomplete.json.gz"
            with gzip.open(path, "wt", encoding="utf-8") as fh:
                json.dump({"steps": []}, fh)  # no configuration, empty steps
            with self.assertRaises(ValueError):
                R.load_replay(path)


class TestCheckpointStateExtraction(unittest.TestCase):
    def test_extracts_expected_fields(self):
        tiles = [
            [{"kind": "PLANT", "crop": "MELON"}, {"kind": "WEED"}, None],
            [{"kind": "PASTURE", "animal": "SHEEP"}, {"kind": "PASTURE"}, "LOCKED"],
            [None, None, None],
        ]
        seat0_actions = [{"farmer": ["PASS"], "hands": [], "market": []}] * 3
        replay = _synthetic_replay(seat0_actions, seat0_actions)
        replay["steps"][2][0]["observation"]["farms"][0]["tiles"] = tiles
        state = R.extract_checkpoint_state(replay, 0, 2, seat0_actions)
        self.assertTrue(state["available"])
        self.assertEqual(state["planted_by_crop"], {"MELON": 1})
        self.assertEqual(state["animals_by_species"], {"SHEEP": 1})
        self.assertEqual(state["weeds"], 1)
        self.assertEqual(state["empty_pastures"], 1)
        self.assertEqual(state["unlocked_shops_in_order"], ["PIZZA_SHOP"])

    def test_unavailable_beyond_replay_length(self):
        seat0_actions = [{"farmer": ["PASS"], "hands": [], "market": []}] * 2
        replay = _synthetic_replay(seat0_actions, seat0_actions)
        state = R.extract_checkpoint_state(replay, 0, 50, seat0_actions)
        self.assertFalse(state["available"])


if __name__ == "__main__":
    unittest.main()
