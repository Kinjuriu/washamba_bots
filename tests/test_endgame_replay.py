"""Tests for the replay-the-ladder harness (experiments/endgame/).

The real gate is `python experiments/endgame/ladder_replay.py gate 30`, which
needs ~30 cached replays and ~20 minutes. These are the cheap invariants the
gate depends on, so a regression in parsing, tape indexing or the generated
tape agent fails here instead of silently mis-reproducing an episode.

Set ENDGAME_EPISODE=<id> to additionally run one real reproduction.

Run with:
    python -m unittest discover -s tests
"""

import json
import os
import tempfile
import unittest

from experiments.endgame import ladder_replay, make_tape_agent, replay_tools

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _fake_replay(seed=12345, n=5):
    """A minimal replay in the host's real shape: `steps[i][seat]['action']` is
    the action decided from `steps[i-1]`'s observation."""
    steps = []
    for i in range(n):
        row = []
        for seat in (0, 1):
            row.append({
                "action": None if i == 0 else {
                    "farmer": ["PASS"], "hands": [], "market": [["SELL", "WHEAT", i + seat]]},
                "observation": {
                    "day": i // 24, "hour": i % 24, "player": seat,
                    "farms": [
                        {"money": 100 + seat, "tiles": [[{"kind": "PASTURE", "animal": "SHEEP"},
                                                         {"kind": "PASTURE"}, None]]},
                        {"money": 200 + seat, "tiles": [[{"kind": "COOP"}, None, "LOCKED"]]},
                    ],
                },
                "reward": 1000.0 * (seat + 1),
                "status": "DONE",
            })
        steps.append(row)
    return {
        "configuration": {"episodeSteps": 720, "seed": None},
        "info": {"EpisodeId": 999, "TeamNames": ["someone_else", replay_tools.OUR_TEAM],
                 "seed": seed},
        "module_version": "1.32.7",
        "rewards": [1000.0, 2000.0],
        "statuses": ["DONE", "DONE"],
        "steps": steps,
        "id": "42f969a4-b5a3-11f1-b207-0242ac130203",
    }


class TestParse(unittest.TestCase):
    def _parsed(self, mutate=None):
        blob = _fake_replay()
        if mutate:
            mutate(blob)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(blob, f)
            return replay_tools.parse(p)

    def test_seed_comes_from_info_not_configuration(self):
        # resolve_episode_seed scrubs configuration.seed to None by design and
        # persists the real value on env.info["seed"].
        r = self._parsed()
        self.assertEqual(r.seed, 12345)
        self.assertEqual(r.seed_source, "info.seed")

    def test_missing_seed_raises_rather_than_defaulting(self):
        def drop(b):
            b["info"].pop("seed")
        with self.assertRaises(ValueError):
            self._parsed(drop)

    def test_episode_id_is_info_episode_id_not_the_run_uuid(self):
        self.assertEqual(self._parsed().episode_id, 999)

    def test_replay_field_wrapper_is_unwrapped(self):
        inner = _fake_replay()
        for wrapped in ({"replay": inner}, {"replay": json.dumps(inner)}):
            with tempfile.TemporaryDirectory() as d:
                p = os.path.join(d, "r.json")
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(wrapped, f)
                self.assertEqual(replay_tools.parse(p).seed, 12345)

    def test_our_seat_from_team_names(self):
        self.assertEqual(self._parsed().our_seat(), 1)

    def test_submission_ids_join_from_the_listing_cache(self):
        # The replay carries only info.TeamNames; submission ids come from the
        # cached ListEpisodes dumps, joined on info.EpisodeId.
        listing = {999: {"seat": 1, "submission": 56202203, "opp_submission": 42}}
        blob = _fake_replay()
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(blob, f)
            r = replay_tools.parse(p, listing_index=listing)
            self.assertEqual([a["submissionId"] for a in r.agents], [42, 56202203])
            # not in the cache -> None, never a wrong id
            r2 = replay_tools.parse(p, listing_index={})
            self.assertEqual([a["submissionId"] for a in r2.agents], [None, None])

    def test_tape_index_convention(self):
        # tape[k] is the action taken AT observation step k, which the host
        # records at steps[k+1]. The last entry has no successor.
        r = self._parsed()
        tape = r.tape(0)
        self.assertEqual(len(tape), len(r.steps))
        self.assertEqual(tape[0], r.steps[1][0]["action"])
        self.assertEqual(tape[0]["market"], [["SELL", "WHEAT", 1]])
        self.assertEqual(tape[-2], r.steps[-1][0]["action"])
        self.assertIsNone(tape[-1])

    def test_structure_counts(self):
        r = self._parsed()
        obs = r.observation(0, 0)
        self.assertEqual(replay_tools.structure_counts(obs, 0),
                         {"structures": 2, "filled": 1})
        self.assertEqual(replay_tools.structure_counts(obs, 1),
                         {"structures": 1, "filled": 0})
        self.assertEqual(replay_tools.money(obs, 0), 100)


class TestMakeTapeAgent(unittest.TestCase):
    def test_roundtrip_and_replay(self):
        tape = [{"farmer": ["WATER"], "hands": [["PASS"], ["WATER"]],
                 "market": [["SELL", "MELON", 3], ["BUY_SEED", "WHEAT", 2]]},
                None,
                {"farmer": ["NORTH"], "hands": [], "market": []}]
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "t.py")
            make_tape_agent.write(tape, out, "generated in a test")
            ns = {}
            with open(out, encoding="utf-8") as f:
                src = f.read()
            exec(compile(src, out, "exec"), ns)
            a = ns["agent"]({"day": 0, "hour": 0, "player": 0,
                             "farms": [{"hands": [{}, {}]}]})
            # market orders are embedded verbatim: lockstep settlement is
            # order-sensitive, so nothing may be sorted or de-duplicated.
            self.assertEqual(a["market"], [["SELL", "MELON", 3], ["BUY_SEED", "WHEAT", 2]])
            self.assertEqual(a["farmer"], ["WATER"])
            self.assertEqual(len(a["hands"]), 2)
            # a None entry replays as an explicit PASS
            b = ns["agent"]({"day": 0, "hour": 1, "player": 0, "farms": [{"hands": []}]})
            self.assertEqual(b, {"farmer": ["PASS"], "hands": [], "market": []})
            # hands are padded to the count the engine actually reports
            c = ns["agent"]({"day": 0, "hour": 2, "player": 0,
                             "farms": [{"hands": [{}, {}, {}]}]})
            self.assertEqual(c["hands"], [["PASS"], ["PASS"], ["PASS"]])

    def test_agent_is_the_last_callable(self):
        # kaggle_environments/agent.py:64 takes the LAST callable in the module
        # namespace as the entrypoint.
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "t.py")
            make_tape_agent.write([{"farmer": ["PASS"], "hands": [], "market": []}], out)
            ns = {}
            with open(out, encoding="utf-8") as f:
                src = f.read()
            exec(compile(src, out, "exec"), ns)
            last = [v for k, v in ns.items() if callable(v) and not k.startswith("__")][-1]
            self.assertIs(last, ns["agent"])

    def test_normalise_leaves_real_actions_alone(self):
        a = {"farmer": ["WATER"], "hands": [["PASS"]], "market": [["SELL", "WOOL", 4]]}
        self.assertEqual(make_tape_agent.normalise(a), a)
        self.assertEqual(make_tape_agent.normalise(None),
                         {"farmer": ["PASS"], "hands": [], "market": []})


class TestDivergence(unittest.TestCase):
    def test_first_divergence(self):
        a = [{"farmer": ["PASS"], "hands": [], "market": []}] * 3
        b = list(a)
        self.assertIsNone(ladder_replay._first_divergence(a, b))
        b[2] = {"farmer": ["WATER"], "hands": [], "market": []}
        self.assertEqual(ladder_replay._first_divergence(a, b), 2)
        # None and an explicit PASS are the same action, not a divergence
        self.assertIsNone(ladder_replay._first_divergence([None], [a[0]]))


class TestReproduce(unittest.TestCase):
    def test_reproduces_recorded_bank(self):
        eid = int(os.environ.get("ENDGAME_EPISODE", "0"))
        if not eid:
            self.skipTest("set ENDGAME_EPISODE to a downloaded episode id")
        r = ladder_replay.reproduce(eid)
        self.assertLessEqual(abs(r["recorded_bank"] - r["replayed_bank"]), 1.0)
        self.assertLessEqual(abs(r["opp_recorded_bank"] - r["opp_replayed_bank"]), 1.0)


if __name__ == "__main__":
    unittest.main()
