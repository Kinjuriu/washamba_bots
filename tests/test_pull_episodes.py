"""
Small, mocked unit tests for pull_episodes.py.

No real HTTP calls, no real Kaggle cookies. These check the pieces most
likely to silently corrupt data or leak files into an iCloud-synced folder:
id normalization, malformed/duplicate episode handling, and the download
path's validate-before-trust discipline (temp files, gzip validation,
atomic rename, cached-file re-validation).

Run with:
    python -m unittest discover -s tests
"""

import gzip
import json
import tempfile
import unittest
from pathlib import Path

import requests

from pull_episodes import (
    OutsideAllowedLocation,
    build_manifest_rows,
    download_replay,
    normalize_id,
    resolve_out_dir,
    validate_replay_structure,
)


# ---------------------------------------------------------------------------
# Fakes - no network, no requests_mock dependency.
# ---------------------------------------------------------------------------
class FakeResponse:
    def __init__(self, status_code=200, content_type="application/json",
                 chunks=None, raise_at_chunk=None):
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}
        self._chunks = chunks or []
        self._raise_at_chunk = raise_at_chunk

    def iter_content(self, chunk_size=1024 * 1024):
        for i, chunk in enumerate(self._chunks):
            if self._raise_at_chunk is not None and i == self._raise_at_chunk:
                raise requests.exceptions.ChunkedEncodingError("connection dropped")
            yield chunk

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeSession:
    """Queues one canned response per call to .get()."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def get(self, url, **kwargs):
        self.calls += 1
        return self._responses.pop(0)


VALID_REPLAY = {
    "steps": [
        [{"reward": 3000}, {"reward": 3000}],
        [{"reward": 5000}, {"reward": 4200}],
    ],
    "configuration": {"episodeSteps": 720},
}


def _valid_replay_bytes():
    return json.dumps(VALID_REPLAY).encode("utf-8")


class TestNormalizeId(unittest.TestCase):
    def test_int_passthrough(self):
        self.assertEqual(normalize_id(56409623), 56409623)

    def test_numeric_string_becomes_int(self):
        self.assertEqual(normalize_id("56409623"), 56409623)
        self.assertEqual(normalize_id(56409623), normalize_id("56409623"))

    def test_non_numeric_string_stays_string(self):
        self.assertEqual(normalize_id("abc123"), "abc123")

    def test_none_stays_none(self):
        self.assertIsNone(normalize_id(None))


class TestBuildManifestRows(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.logs_dir = Path(self.tmp.name) / "logs"

    def tearDown(self):
        self.tmp.cleanup()

    def test_normal_episode_produces_one_row(self):
        episodes = [{
            "id": 111,
            "endTime": "2026-09-20T00:00:00Z",
            "state": "DONE",
            "agents": [
                {"submissionId": "56409623", "teamId": 1, "index": 0, "reward": 5000,
                 "initialScore": 600, "updatedScore": 610},
                {"submissionId": 99999999, "teamId": 2, "index": 1, "reward": 4200},
            ],
        }]
        all_teams = {2: {"teamName": "Rival Team"}}
        # sub_id passed as int; agent's submissionId is a string - must still match.
        rows = build_manifest_rows("DSM", 56409623, episodes, all_teams, self.logs_dir)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["episode_id"], 111)
        self.assertEqual(row["player_seat"], 0)
        self.assertEqual(row["won"], 1)
        self.assertEqual(row["opponent_name"], "Rival Team")

    def test_duplicate_episode_across_two_targets(self):
        # Same episode id appears in both players' game lists, each from
        # their own perspective (mirrored seats/rewards).
        ep_from_a = {
            "id": 555, "endTime": "t", "state": "DONE",
            "agents": [
                {"submissionId": 111, "teamId": 1, "index": 0, "reward": 6000},
                {"submissionId": 222, "teamId": 2, "index": 1, "reward": 3000},
            ],
        }
        ep_from_b = {
            "id": 555, "endTime": "t", "state": "DONE",
            "agents": [
                {"submissionId": 111, "teamId": 1, "index": 0, "reward": 6000},
                {"submissionId": 222, "teamId": 2, "index": 1, "reward": 3000},
            ],
        }
        rows_a = build_manifest_rows("PlayerA", 111, [ep_from_a], {}, self.logs_dir)
        rows_b = build_manifest_rows("PlayerB", 222, [ep_from_b], {}, self.logs_dir)
        all_rows = rows_a + rows_b
        eids = [r["episode_id"] for r in all_rows]
        self.assertEqual(eids, [555, 555])
        self.assertEqual(rows_a[0]["player_seat"], 0)
        self.assertEqual(rows_b[0]["player_seat"], 1)
        self.assertEqual({r["player"] for r in all_rows}, {"PlayerA", "PlayerB"})

    def test_missing_target_agent_is_skipped_not_seat_zero(self):
        episodes = [{
            "id": 777,
            "agents": [
                {"submissionId": 111, "teamId": 1, "index": 0, "reward": 6000},
                {"submissionId": 222, "teamId": 2, "index": 1, "reward": 3000},
            ],
        }]
        # sub_id 999 is not among this episode's agents at all.
        rows = build_manifest_rows("Ghost", 999, episodes, {}, self.logs_dir)
        self.assertEqual(rows, [])
        log_path = self.logs_dir / "malformed_episodes.log"
        self.assertTrue(log_path.exists())
        self.assertIn("not found among its agents", log_path.read_text(encoding="utf-8"))

    def test_seat_zero_omitted_from_payload_still_decodes_to_zero(self):
        # Kaggle's ListEpisodes is proto3-JSON: a zero-valued field is
        # omitted rather than sent as 0. An agent with no "index" key at
        # all - but who IS present in `agents` - is seat 0, not missing
        # data. Confirmed against a live payload: no agent ever carries an
        # explicit "index": 0, only an absent key or an explicit 1.
        episodes = [{
            "id": 888,
            "agents": [
                {"submissionId": 111, "teamId": 1, "reward": 6000},  # no "index" key
                {"submissionId": 222, "teamId": 2, "index": 1, "reward": 3000},
            ],
        }]
        rows = build_manifest_rows("PlayerA", 111, episodes, {}, self.logs_dir)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["player_seat"], 0)
        self.assertEqual(rows[0]["opponent_seat"], 1)
        # this is NOT the missing-agent case, so nothing should be logged
        self.assertFalse((self.logs_dir / "malformed_episodes.log").exists())

    def test_episode_missing_id_is_skipped(self):
        rows = build_manifest_rows("DSM", 111, [{"agents": []}], {}, self.logs_dir)
        self.assertEqual(rows, [])
        self.assertTrue((self.logs_dir / "malformed_episodes.log").exists())


class TestOutputPathSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.repo = Path(self.tmp.name) / "repo"
        (self.home / "Desktop").mkdir(parents=True)
        (self.home / "Documents").mkdir(parents=True)
        (self.home / "Library" / "Mobile Documents").mkdir(parents=True)
        self.repo.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_rejects_desktop(self):
        with self.assertRaises(OutsideAllowedLocation):
            resolve_out_dir(str(self.home / "Desktop" / "episodes"),
                             home=self.home, repo_root=self.repo)

    def test_rejects_documents(self):
        with self.assertRaises(OutsideAllowedLocation):
            resolve_out_dir(str(self.home / "Documents" / "episodes"),
                             home=self.home, repo_root=self.repo)

    def test_rejects_icloud_drive(self):
        with self.assertRaises(OutsideAllowedLocation):
            resolve_out_dir(str(self.home / "Library" / "Mobile Documents" / "episodes"),
                             home=self.home, repo_root=self.repo)

    def test_rejects_git_repo(self):
        with self.assertRaises(OutsideAllowedLocation):
            resolve_out_dir(str(self.repo / "data" / "episodes"),
                             home=self.home, repo_root=self.repo)

    def test_accepts_safe_sibling_directory(self):
        safe = self.home / "KagricultureLocalData" / "episodes"
        resolved = resolve_out_dir(str(safe), home=self.home, repo_root=self.repo)
        self.assertEqual(resolved, safe.resolve())


class TestReplayValidation(unittest.TestCase):
    def test_valid_replay_passes(self):
        ok, reason = validate_replay_structure(VALID_REPLAY)
        self.assertTrue(ok, reason)

    def test_html_login_page_fails(self):
        # json.loads would already blow up on real HTML; this covers the
        # case where something upstream still hands us a parsed non-dict.
        ok, reason = validate_replay_structure(["not", "a", "replay"])
        self.assertFalse(ok)

    def test_missing_steps_fails(self):
        ok, reason = validate_replay_structure({"configuration": {}})
        self.assertFalse(ok)
        self.assertIn("steps", reason)

    def test_missing_rewards_fails(self):
        data = {"steps": [[{"observation": {}}]], "configuration": {}}
        ok, reason = validate_replay_structure(data)
        self.assertFalse(ok)


class TestDownloadReplay(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.replay_dir = Path(self.tmp.name) / "replays"
        self.logs_dir = Path(self.tmp.name) / "logs"
        self.replay_dir.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_successful_download_validates_and_atomically_renames(self):
        body = _valid_replay_bytes()
        session = FakeSession([FakeResponse(chunks=[body])])
        status = download_replay(session, "ep1", self.replay_dir, self.logs_dir)
        self.assertTrue(status.endswith("MB"))
        final = self.replay_dir / "ep1.json.gz"
        self.assertTrue(final.exists())
        with gzip.open(final, "rt", encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), VALID_REPLAY)
        # no leftover temp files
        leftovers = [p for p in self.replay_dir.iterdir() if p.name != "ep1.json.gz"]
        self.assertEqual(leftovers, [])

    def test_html_login_page_instead_of_json(self):
        session = FakeSession([FakeResponse(content_type="text/html",
                                             chunks=[b"<html>login</html>"])])
        status = download_replay(session, "ep2", self.replay_dir, self.logs_dir)
        self.assertTrue(status.startswith("ERR"))
        self.assertFalse((self.replay_dir / "ep2.json.gz").exists())
        self.assertTrue((self.logs_dir / "download_failures.log").exists())

    def test_interrupted_download_leaves_no_partial_final_file(self):
        session = FakeSession([
            FakeResponse(chunks=[b'{"steps": [', b'{"reward"'], raise_at_chunk=1),
        ])
        status = download_replay(session, "ep3", self.replay_dir, self.logs_dir, tries=1)
        self.assertTrue(status.startswith("ERR"))
        self.assertFalse((self.replay_dir / "ep3.json.gz").exists())
        leftovers = list(self.replay_dir.iterdir())
        self.assertEqual(leftovers, [], "temp .part files must be cleaned up")

    def test_corrupt_cached_gzip_is_redownloaded(self):
        final = self.replay_dir / "ep4.json.gz"
        final.write_bytes(b"not actually gzip data")
        body = _valid_replay_bytes()
        session = FakeSession([FakeResponse(chunks=[body])])
        status = download_replay(session, "ep4", self.replay_dir, self.logs_dir)
        self.assertTrue(status.endswith("MB"), "should have redownloaded, not stayed ERR/cached")
        with gzip.open(final, "rt", encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), VALID_REPLAY)

    def test_valid_cached_file_is_reused_without_a_network_call(self):
        final = self.replay_dir / "ep5.json.gz"
        with gzip.open(final, "wt", encoding="utf-8") as fh:
            json.dump(VALID_REPLAY, fh)
        session = FakeSession([])  # would raise IndexError if .get() were called
        status = download_replay(session, "ep5", self.replay_dir, self.logs_dir)
        self.assertEqual(status, "cached")
        self.assertEqual(session.calls, 0)


if __name__ == "__main__":
    unittest.main()
