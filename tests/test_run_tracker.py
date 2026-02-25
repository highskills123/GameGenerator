"""
tests/test_run_tracker.py – Tests for RunTracker and the game_server /status endpoint.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path


class TestRunTrackerLogs(unittest.TestCase):
    """RunTracker must write human-readable logs to logs.txt."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _tracker(self, run_id="test-run", json_logs=False):
        from orchestrator.run_tracker import RunTracker
        return RunTracker(run_id=run_id, runs_dir=self.tmp, json_logs=json_logs)

    def test_logs_txt_created(self):
        t = self._tracker()
        t.info("hello")
        t.close()
        log_path = Path(self.tmp) / "test-run" / "logs.txt"
        self.assertTrue(log_path.exists())

    def test_logs_txt_contains_message(self):
        t = self._tracker()
        t.info("test message here")
        t.close()
        content = (Path(self.tmp) / "test-run" / "logs.txt").read_text()
        self.assertIn("test message here", content)

    def test_logs_txt_contains_level(self):
        t = self._tracker()
        t.warning("watch out")
        t.close()
        content = (Path(self.tmp) / "test-run" / "logs.txt").read_text()
        self.assertIn("[WARNING]", content)
        self.assertIn("watch out", content)

    def test_logs_txt_contains_error(self):
        t = self._tracker()
        t.error("something broke")
        t.close()
        content = (Path(self.tmp) / "test-run" / "logs.txt").read_text()
        self.assertIn("[ERROR]", content)

    def test_logs_txt_multiple_lines(self):
        t = self._tracker()
        t.info("line one")
        t.info("line two")
        t.close()
        lines = (Path(self.tmp) / "test-run" / "logs.txt").read_text().splitlines()
        self.assertGreaterEqual(len(lines), 2)

    def test_json_logs_not_created_by_default(self):
        t = self._tracker(json_logs=False)
        t.info("msg")
        t.close()
        self.assertFalse((Path(self.tmp) / "test-run" / "logs.jsonl").exists())

    def test_json_logs_created_when_enabled(self):
        t = self._tracker(json_logs=True)
        t.info("json msg")
        t.close()
        self.assertTrue((Path(self.tmp) / "test-run" / "logs.jsonl").exists())

    def test_json_logs_valid_jsonl(self):
        t = self._tracker(json_logs=True)
        t.info("structured")
        t.close()
        lines = (Path(self.tmp) / "test-run" / "logs.jsonl").read_text().strip().splitlines()
        for line in lines:
            record = json.loads(line)
            self.assertIn("ts", record)
            self.assertIn("level", record)
            self.assertIn("msg", record)

    def test_json_logs_contains_message(self):
        t = self._tracker(json_logs=True)
        t.info("find me")
        t.close()
        lines = (Path(self.tmp) / "test-run" / "logs.jsonl").read_text().strip().splitlines()
        messages = [json.loads(l)["msg"] for l in lines]
        self.assertTrue(any("find me" in m for m in messages))


class TestRunTrackerEvents(unittest.TestCase):
    """RunTracker must write progress events to events.jsonl."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _tracker(self, run_id="ev-run"):
        from orchestrator.run_tracker import RunTracker
        return RunTracker(run_id=run_id, runs_dir=self.tmp)

    def test_events_jsonl_created_on_emit(self):
        t = self._tracker()
        t.emit("spec", "Generating spec")
        t.close()
        self.assertTrue((Path(self.tmp) / "ev-run" / "events.jsonl").exists())

    def test_events_jsonl_valid_json_lines(self):
        t = self._tracker()
        t.emit("spec", "stage one")
        t.emit("scaffold", "stage two")
        t.close()
        lines = (Path(self.tmp) / "ev-run" / "events.jsonl").read_text().strip().splitlines()
        self.assertEqual(len(lines), 2)
        for line in lines:
            record = json.loads(line)
            self.assertIn("ts", record)
            self.assertIn("stage", record)
            self.assertIn("message", record)

    def test_events_contain_stage_name(self):
        t = self._tracker()
        t.emit("scaffold", "Building files …")
        t.close()
        lines = (Path(self.tmp) / "ev-run" / "events.jsonl").read_text().strip().splitlines()
        stages = [json.loads(l)["stage"] for l in lines]
        self.assertIn("scaffold", stages)

    def test_events_contain_percent(self):
        t = self._tracker()
        t.emit("zip", "Zipping", percent=90)
        t.close()
        line = (Path(self.tmp) / "ev-run" / "events.jsonl").read_text().strip()
        record = json.loads(line)
        self.assertEqual(record["percent"], 90)

    def test_events_contain_step_counts(self):
        t = self._tracker()
        t.emit("scaffold", "File 3 of 10", step=3, total_steps=10)
        t.close()
        line = (Path(self.tmp) / "ev-run" / "events.jsonl").read_text().strip()
        record = json.loads(line)
        self.assertEqual(record["step"], 3)
        self.assertEqual(record["total_steps"], 10)

    def test_events_are_append_only(self):
        t = self._tracker()
        t.emit("spec", "first")
        t.emit("scaffold", "second")
        t.emit("zip", "third")
        t.close()
        lines = (Path(self.tmp) / "ev-run" / "events.jsonl").read_text().strip().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertEqual(json.loads(lines[0])["stage"], "spec")
        self.assertEqual(json.loads(lines[2])["stage"], "zip")


class TestRunTrackerStatusJson(unittest.TestCase):
    """RunTracker must keep status.json updated."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _tracker(self, run_id="st-run"):
        from orchestrator.run_tracker import RunTracker
        return RunTracker(run_id=run_id, runs_dir=self.tmp)

    def _read_status(self, run_id="st-run"):
        return json.loads((Path(self.tmp) / run_id / "status.json").read_text())

    def test_status_json_created_on_init(self):
        t = self._tracker()
        t.close()
        self.assertTrue((Path(self.tmp) / "st-run" / "status.json").exists())

    def test_status_running_on_start(self):
        t = self._tracker()
        status = self._read_status()
        self.assertEqual(status["status"], "running")
        t.close()

    def test_status_completed_after_complete(self):
        t = self._tracker()
        t.complete()
        t.close()
        status = self._read_status()
        self.assertEqual(status["status"], "completed")

    def test_status_failed_after_fail(self):
        t = self._tracker()
        t.fail("boom")
        t.close()
        status = self._read_status()
        self.assertEqual(status["status"], "failed")
        self.assertIn("error", status)

    def test_status_contains_run_id(self):
        t = self._tracker()
        t.close()
        status = self._read_status()
        self.assertEqual(status["run_id"], "st-run")

    def test_status_events_updated_on_emit(self):
        t = self._tracker()
        t.emit("spec", "go")
        status = self._read_status()
        self.assertEqual(len(status["events"]), 1)
        self.assertEqual(status["events"][0]["stage"], "spec")
        t.close()

    def test_status_accumulates_events(self):
        t = self._tracker()
        t.emit("spec", "one")
        t.emit("scaffold", "two")
        status = self._read_status()
        self.assertEqual(len(status["events"]), 2)
        t.close()

    def test_status_has_timestamps(self):
        t = self._tracker()
        status = self._read_status()
        self.assertIn("created_at", status)
        self.assertIn("updated_at", status)
        t.close()

    def test_context_manager_completes_on_success(self):
        with self._tracker() as t:
            t.emit("spec", "done")
        status = self._read_status()
        self.assertEqual(status["status"], "completed")

    def test_context_manager_fails_on_exception(self):
        try:
            with self._tracker() as _t:
                raise ValueError("intentional error")
        except ValueError:
            pass
        status = self._read_status()
        self.assertEqual(status["status"], "failed")
        self.assertIn("intentional error", status.get("error", ""))


class TestLoadStatus(unittest.TestCase):
    """load_status() helper must return None for missing runs."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_returns_none_for_missing_run(self):
        from orchestrator.run_tracker import load_status
        result = load_status("nonexistent", runs_dir=self.tmp)
        self.assertIsNone(result)

    def test_returns_dict_for_existing_run(self):
        from orchestrator.run_tracker import RunTracker, load_status
        t = RunTracker(run_id="existing", runs_dir=self.tmp)
        t.close()
        result = load_status("existing", runs_dir=self.tmp)
        self.assertIsNotNone(result)
        self.assertEqual(result["run_id"], "existing")


class TestGetStatusHelper(unittest.TestCase):
    """get_status() must trim events to last_n."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_get_status_trims_to_last_n(self):
        from orchestrator.run_tracker import RunTracker
        t = RunTracker(run_id="trim-run", runs_dir=self.tmp)
        for i in range(10):
            t.emit("stage", f"event {i}")
        status = t.get_status(last_n_events=3)
        self.assertEqual(len(status["events"]), 3)
        self.assertEqual(status["events"][-1]["message"], "event 9")
        t.close()


class TestGameServerStatus(unittest.TestCase):
    """FastAPI /status endpoint must return status for known run_id."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_status_returns_404_for_unknown_run(self):
        from fastapi.testclient import TestClient
        import game_server
        original = game_server.RUNS_DIR
        game_server.RUNS_DIR = self.tmp
        try:
            client = TestClient(game_server.app)
            resp = client.get("/status/does-not-exist")
            self.assertEqual(resp.status_code, 404)
        finally:
            game_server.RUNS_DIR = original

    def test_status_returns_200_for_known_run(self):
        from fastapi.testclient import TestClient
        from orchestrator.run_tracker import RunTracker
        import game_server

        original = game_server.RUNS_DIR
        game_server.RUNS_DIR = self.tmp
        try:
            # Pre-create a run
            t = RunTracker(run_id="known-run", runs_dir=self.tmp)
            t.emit("spec", "test event")
            t.complete()
            t.close()

            client = TestClient(game_server.app)
            resp = client.get("/status/known-run")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["run_id"], "known-run")
            self.assertEqual(data["status"], "completed")
        finally:
            game_server.RUNS_DIR = original

    def test_status_last_param_trims_events(self):
        from fastapi.testclient import TestClient
        from orchestrator.run_tracker import RunTracker
        import game_server

        original = game_server.RUNS_DIR
        game_server.RUNS_DIR = self.tmp
        try:
            t = RunTracker(run_id="many-events", runs_dir=self.tmp)
            for i in range(15):
                t.emit("stage", f"event {i}")
            t.complete()
            t.close()

            client = TestClient(game_server.app)
            resp = client.get("/status/many-events?last=5")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(len(data["events"]), 5)
            self.assertEqual(data["events"][-1]["message"], "event 14")
        finally:
            game_server.RUNS_DIR = original

    def test_health_endpoint(self):
        from fastapi.testclient import TestClient
        import game_server

        client = TestClient(game_server.app)
        resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
