"""
tests/test_server.py – Tests for game_generator.server (FastAPI app + job_manager).

Covers:
- run directory creation
- request.json artifact writing
- status persistence (status.json updated correctly)
- GET /health
- POST /spec (returns a GameSpec)
- GET /status/{run_id} – 404 for unknown, 200 for known
- GET /status/{run_id} – all events returned (messages not trimmed / never disappear)
- GET /download/{run_id} – 404 when not completed, 409 when no zip yet
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class _ServerTestBase(unittest.TestCase):
    """Base class that patches DEFAULT_RUNS_DIR to a temp directory."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # Patch the module-level runs dir used by the app
        import game_generator.server.app as server_app
        self._orig_runs_dir = server_app.DEFAULT_RUNS_DIR
        server_app.DEFAULT_RUNS_DIR = self.tmp

    def tearDown(self):
        import game_generator.server.app as server_app
        server_app.DEFAULT_RUNS_DIR = self._orig_runs_dir

    def _client(self):
        from fastapi.testclient import TestClient
        from game_generator.server.app import app
        return TestClient(app)


# ── job_manager unit tests ─────────────────────────────────────────────────────

class TestJobManager(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_new_run_id_is_string(self):
        from game_generator.server.job_manager import new_run_id
        rid = new_run_id()
        self.assertIsInstance(rid, str)
        self.assertTrue(len(rid) > 0)

    def test_new_run_id_unique(self):
        from game_generator.server.job_manager import new_run_id
        ids = {new_run_id() for _ in range(20)}
        self.assertEqual(len(ids), 20)

    def test_get_run_dir_creates_directory(self):
        from game_generator.server.job_manager import get_run_dir, new_run_id
        rid = new_run_id()
        path = get_run_dir(rid, self.tmp)
        self.assertTrue(path.exists())
        self.assertTrue(path.is_dir())

    def test_write_request_creates_file(self):
        from game_generator.server.job_manager import write_request, new_run_id
        rid = new_run_id()
        write_request(rid, self.tmp, {"prompt": "test prompt", "platform": "android"})
        req_path = Path(self.tmp) / rid / "request.json"
        self.assertTrue(req_path.exists())

    def test_write_request_contains_data(self):
        from game_generator.server.job_manager import write_request, new_run_id
        rid = new_run_id()
        write_request(rid, self.tmp, {"prompt": "space shooter"})
        data = json.loads((Path(self.tmp) / rid / "request.json").read_text())
        self.assertEqual(data["prompt"], "space shooter")

    def test_get_status_returns_none_for_unknown(self):
        from game_generator.server.job_manager import get_status
        result = get_status("totally-unknown-id", self.tmp)
        self.assertIsNone(result)

    def test_get_status_reads_disk_for_completed_run(self):
        from game_generator.server.job_manager import get_status
        from orchestrator.run_tracker import RunTracker
        rid = "disk-run"
        t = RunTracker(run_id=rid, runs_dir=self.tmp)
        t.emit("spec", "generating")
        t.complete()
        t.close()
        status = get_status(rid, self.tmp)
        self.assertIsNotNone(status)
        self.assertEqual(status["run_id"], rid)
        self.assertEqual(status["status"], "completed")

    def test_get_status_returns_all_events(self):
        """All events must be returned – messages must not be silently dropped."""
        from game_generator.server.job_manager import get_status, create_tracker
        rid = "all-events-run"
        tracker = create_tracker(rid, self.tmp)
        for i in range(25):
            tracker.emit("stage", f"event {i}")
        status = get_status(rid, self.tmp)
        self.assertEqual(len(status["events"]), 25)
        tracker.close()


# ── API route tests ────────────────────────────────────────────────────────────

class TestHealthEndpoint(_ServerTestBase):

    def test_health_returns_200(self):
        resp = self._client().get("/health")
        self.assertEqual(resp.status_code, 200)

    def test_health_status_ok(self):
        data = self._client().get("/health").json()
        self.assertEqual(data["status"], "ok")


class TestUIEndpoint(_ServerTestBase):

    def test_root_returns_html(self):
        resp = self._client().get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/html", resp.headers["content-type"])

    def test_root_contains_generate_button(self):
        html = self._client().get("/").text
        self.assertIn("Generate Game", html)

    def test_root_log_area_never_cleared_comment(self):
        """The UI source must document that the log is never cleared."""
        html = self._client().get("/").text
        self.assertIn("never", html.lower())


class TestSpecEndpoint(_ServerTestBase):

    def test_spec_returns_200(self):
        resp = self._client().post("/spec", json={"prompt": "top down space shooter"})
        self.assertEqual(resp.status_code, 200)

    def test_spec_contains_spec_key(self):
        data = self._client().post("/spec", json={"prompt": "top down space shooter"}).json()
        self.assertIn("spec", data)
        self.assertTrue(data["success"])

    def test_spec_has_genre(self):
        data = self._client().post("/spec", json={"prompt": "idle rpg with upgrades"}).json()
        self.assertIn("genre", data["spec"])

    def test_spec_platform_override(self):
        data = self._client().post(
            "/spec", json={"prompt": "shooter", "platform": "android+ios"}
        ).json()
        self.assertEqual(data["spec"]["platform"], "android+ios")


class TestStatusEndpoint(_ServerTestBase):

    def _pre_create_run(self, run_id: str, events: int = 3) -> None:
        from orchestrator.run_tracker import RunTracker
        t = RunTracker(run_id=run_id, runs_dir=self.tmp)
        for i in range(events):
            t.emit("spec", f"event {i}")
        t.complete()
        t.close()

    def test_status_404_for_unknown_run(self):
        resp = self._client().get("/status/does-not-exist")
        self.assertEqual(resp.status_code, 404)

    def test_status_200_for_known_run(self):
        self._pre_create_run("known-run")
        resp = self._client().get("/status/known-run")
        self.assertEqual(resp.status_code, 200)

    def test_status_returns_run_id(self):
        self._pre_create_run("id-check-run")
        data = self._client().get("/status/id-check-run").json()
        self.assertEqual(data["run_id"], "id-check-run")

    def test_status_returns_completed(self):
        self._pre_create_run("completed-run")
        data = self._client().get("/status/completed-run").json()
        self.assertEqual(data["status"], "completed")

    def test_status_returns_all_events_not_trimmed(self):
        """GET /status must return ALL events so messages never disappear in the UI."""
        self._pre_create_run("full-run", events=30)
        data = self._client().get("/status/full-run").json()
        # All 30 events must be present — none dropped
        self.assertEqual(len(data["events"]), 30)


class TestDownloadEndpoint(_ServerTestBase):

    def test_download_404_for_unknown_run(self):
        resp = self._client().get("/download/does-not-exist")
        self.assertEqual(resp.status_code, 404)

    def test_download_409_when_not_completed(self):
        from orchestrator.run_tracker import RunTracker
        t = RunTracker(run_id="running-run", runs_dir=self.tmp)
        t.emit("spec", "working")
        # Do NOT call complete — run is still "running"
        t.close()
        resp = self._client().get("/download/running-run")
        self.assertEqual(resp.status_code, 409)

    def test_download_404_when_completed_but_no_zip(self):
        from orchestrator.run_tracker import RunTracker
        t = RunTracker(run_id="no-zip-run", runs_dir=self.tmp)
        t.complete()
        t.close()
        resp = self._client().get("/download/no-zip-run")
        self.assertEqual(resp.status_code, 404)


class TestGenerateEndpoint(_ServerTestBase):

    def test_generate_returns_run_id(self):
        """POST /generate must immediately return a run_id string."""
        with patch("game_generator.server.app._run_generation"):
            resp = self._client().post(
                "/generate",
                json={"prompt": "top down shooter"},
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("run_id", data)
        self.assertIsInstance(data["run_id"], str)

    def test_generate_creates_request_json(self):
        """A request.json artifact must exist immediately after POST /generate."""
        with patch("game_generator.server.app._run_generation"):
            resp = self._client().post(
                "/generate",
                json={"prompt": "idle rpg"},
            )
        run_id = resp.json()["run_id"]
        req_path = Path(self.tmp) / run_id / "request.json"
        self.assertTrue(req_path.exists())


if __name__ == "__main__":
    unittest.main()
