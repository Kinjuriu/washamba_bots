"""Unit tests for agents/washamba_base_v1_fork.py - the T11 fork overlay.

Stdlib unittest (pytest is not installed in this repo). These pin the overlay's
own invariants: the base is embedded byte-verbatim, `agent` is the last callable
binding, the flags-off build is behaviour-identical to the base, and the flags-on
build emits exactly the recovered fork diff and nothing else. The strategy verdict
is in docs/ENDGAME/fork_results.md, measured on the ladder-replay harness and on
self-play.
"""

import importlib.util
import os
import re
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORK_PATH = os.path.join(ROOT, "agents", "washamba_base_v1_fork.py")
BASE_PATH = os.path.join(ROOT, "agents", "public_farm2945.py")


def _read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FORK = _load(FORK_PATH, "washamba_base_v1_fork_under_test")


def _flags_off_copy(tmpdir):
    """The same file with both flags at the base's own values."""
    src = _read_bytes(FORK_PATH).decode("utf-8")
    src = re.sub(r"^FORK_CA_FEED_DAYS = .*$", "FORK_CA_FEED_DAYS = None", src, flags=re.M)
    src = re.sub(r"^FORK_OPENING = .*$", "FORK_OPENING = False", src, flags=re.M)
    out = os.path.join(tmpdir, "fork_flags_off.py")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(src)
    return out


def _tape(env, seat):
    return [env.steps[i][seat].get("action") for i in range(1, len(env.steps))]


def _play(files, seed=0, steps=120):
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed})
    env.run(list(files))
    return env


class TestFileShape(unittest.TestCase):
    def test_base_is_embedded_byte_verbatim(self):
        base_body = _read_bytes(BASE_PATH).split(b"\n", 2)[2]
        fork_body = _read_bytes(FORK_PATH).split(b"\n", 3)[3]
        self.assertTrue(fork_body.startswith(base_body),
                        "the base body is not byte-verbatim at the top of the fork file")

    def test_agent_is_the_last_callable_binding(self):
        # kaggle_environments/agent.py:64 takes [v for v in env.values() if callable(v)][-1]
        src = _read_bytes(FORK_PATH).decode("utf-8")
        last = src.rstrip().splitlines()[-1].strip()
        self.assertEqual(last, 'agent = globals().pop("agent")')
        self.assertTrue(callable(FORK.agent))

    def test_flags_are_declared_once_at_the_top_of_the_overlay(self):
        src = _read_bytes(FORK_PATH).decode("utf-8")
        self.assertEqual(len(re.findall(r"^FORK_CA_FEED_DAYS = ", src, flags=re.M)), 1)
        self.assertEqual(len(re.findall(r"^FORK_OPENING = ", src, flags=re.M)), 1)


class TestLeverA(unittest.TestCase):
    """The _CA carrot layer's feed reserve - the fork's crop-mix lever."""

    def test_feed_days_is_lowered_to_one(self):
        self.assertEqual(FORK.FORK_CA_FEED_DAYS, 1)
        self.assertEqual(FORK._CA_FEED_DAYS, 1)

    def test_base_ships_two_days(self):
        base = _load(BASE_PATH, "public_farm2945_for_fork_test")
        self.assertEqual(base._CA_FEED_DAYS, 2)

    def test_feed_need_scales_with_the_flag(self):
        # _ca_feed_need counts FEED commands in the route tape over `days` days.
        # _ca_tape needs a live episode to resolve a route, so stub it.
        real = FORK._ca_tape
        FORK._ca_tape = lambda seat, t: {"farmer": ["FEED"], "hands": []}
        try:
            one = FORK._ca_feed_need(0, 240, 1)
            two = FORK._ca_feed_need(0, 240, 2)
        finally:
            FORK._ca_tape = real
        self.assertEqual(one, 25)   # 24 steps + the inclusive endpoint
        self.assertEqual(two, 49)
        self.assertGreater(two, one, "a 2-day reserve must demand more wheat than a 1-day one")


class TestLeverBEmitsExactlyTheForkDiff(unittest.TestCase):
    """The recovered opening: one extra wheat cycle on (2,4) before its pasture."""

    def test_script_matches_the_recorded_fork_tape(self):
        # Recovered from the 9-of-11 majority form of the fork's recorded tapes
        # (docs/ENDGAME/fork_results.md). Index 0 is the farmer.
        self.assertEqual(FORK._FORK_OPEN_SCRIPT[5][3], ["PLANT", "WHEAT"])
        self.assertEqual(FORK._FORK_OPEN_SCRIPT[5][2], (2, 4))
        self.assertEqual(FORK._FORK_OPEN_SCRIPT[29][1], ["BUILD_PASTURE"])
        self.assertEqual(FORK._FORK_OPEN_SCRIPT[29][3], ["WATER"])
        self.assertEqual(FORK._FORK_OPEN_SCRIPT[88][3], ["BUILD_PASTURE"])
        self.assertEqual(sorted(FORK._FORK_OPEN_SCRIPT),
                         [2, 3, 4, 5, 6, 29, 49, 50, 51, 52, 84, 85, 86, 87, 88, 89, 90, 91])

    def _obs(self, step, positions):
        return {"step": step, "player": 0,
                "farms": [{"farmer": list(positions[0]),
                           "hands": [list(p) for p in positions[1:]]}]}

    def test_step_zero_appends_one_wheat_seed(self):
        act = {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 20]]}
        out = FORK._fork_overlay(self._obs(0, [(5, 4)]), act)
        self.assertEqual(out["market"], [["BUY_PRODUCT", "WHEAT", 20], ["BUY_SEED", "WHEAT", 1]])
        self.assertEqual(act["market"], [["BUY_PRODUCT", "WHEAT", 20]],
                         "the input action must not be mutated")

    def test_step_five_plants_wheat_on_the_pasture_tile(self):
        act = {"farmer": ["PASS"], "hands": [["PASS"], ["PASS"]], "market": []}
        out = FORK._fork_overlay(self._obs(5, [(5, 4), (5, 4), (2, 4)]), act)
        self.assertEqual(out["hands"], [["PASS"], ["PLANT", "WHEAT"]])

    def test_step_twentynine_defers_the_pasture(self):
        act = {"farmer": ["PASS"], "hands": [["PASS"], ["PASS"], ["BUILD_PASTURE"]], "market": []}
        out = FORK._fork_overlay(self._obs(29, [(5, 4), (5, 4), (5, 4), (2, 4)]), act)
        self.assertEqual(out["hands"][2], ["WATER"])

    def test_wrong_position_is_a_no_op(self):
        act = {"farmer": ["PASS"], "hands": [["PASS"], ["PASS"]], "market": []}
        out = FORK._fork_overlay(self._obs(5, [(5, 4), (5, 4), (9, 9)]), act)
        self.assertIs(out, act)

    def test_wrong_tape_command_is_a_no_op(self):
        act = {"farmer": ["PASS"], "hands": [["PASS"], ["WATER"]], "market": []}
        out = FORK._fork_overlay(self._obs(5, [(5, 4), (5, 4), (2, 4)]), act)
        self.assertIs(out, act)

    def test_unscripted_step_is_a_no_op(self):
        act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
        out = FORK._fork_overlay(self._obs(200, [(5, 4), (5, 4)]), act)
        self.assertIs(out, act)


class TestEpisodeBehaviour(unittest.TestCase):
    """End-to-end on the real engine: 120 steps, seed 0, self-play."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="fork_test_")
        cls.off = _flags_off_copy(cls.tmp)
        cls.base_env = _play([BASE_PATH, BASE_PATH])
        cls.off_env = _play([cls.off, cls.off])
        cls.on_env = _play([FORK_PATH, FORK_PATH])

    def test_flags_off_is_behaviour_identical_to_the_base(self):
        for seat in (0, 1):
            self.assertEqual(_tape(self.off_env, seat), _tape(self.base_env, seat),
                             "flags off must emit the base's action stream exactly")

    def test_flags_on_diverges_at_step_zero_and_only_where_scripted(self):
        base, on = _tape(self.base_env, 0), _tape(self.on_env, 0)
        diff = [i for i in range(len(base)) if base[i] != on[i]]
        self.assertIn(0, diff, "step 0 must gain the fork's BUY_SEED WHEAT 1")
        self.assertEqual(on[0]["market"][-1], ["BUY_SEED", "WHEAT", 1])
        # The overlay only ever rewrites LABOUR at the scripted steps. Market
        # differences elsewhere are the base's own sell layers reacting to the
        # extra grain - the recorded fork tape shows the same thing at 79/80.
        scripted = set(FORK._FORK_OPEN_SCRIPT) | {0}

        def labour(a):
            return [a.get("farmer")] + list(a.get("hands") or [])

        unscripted = [i for i in diff if i not in scripted and labour(base[i]) != labour(on[i])]
        self.assertEqual(unscripted, [],
                         "the overlay rewrote labour at unscripted steps %s" % unscripted)
        self.assertTrue(set(FORK._FORK_OPEN_SCRIPT).issubset(set(diff)),
                        "every scripted step must actually fire on seed 0")

    def test_no_inert_agent_and_no_crash(self):
        for env in (self.on_env, self.off_env):
            for s in env.steps[-1]:
                self.assertNotEqual(s["reward"], 3000, "agent never acted (see CLAUDE.md)")


if __name__ == "__main__":
    unittest.main()
