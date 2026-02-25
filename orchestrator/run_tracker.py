"""
orchestrator/run_tracker.py – Structured logging and progress-event tracking.

Each generation run gets a ``runs/{run_id}/`` directory containing:

* ``logs.txt``     – human-readable timestamped log lines
* ``logs.jsonl``   – optional structured JSON-Lines log (one object per line)
* ``events.jsonl`` – append-only progress events (stage / percent / message / timestamp)
* ``status.json``  – current pipeline status (updated on every event)
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class RunTracker:
    """Writes structured logs and progress events for one pipeline run.

    Parameters
    ----------
    run_id:
        Unique identifier for this run (e.g. a UUID).
    runs_dir:
        Base directory under which ``runs/{run_id}/`` is created.
    json_logs:
        When *True*, also write structured JSON-Lines to ``logs.jsonl``.
    """

    def __init__(
        self,
        run_id: str,
        runs_dir: str = "runs",
        json_logs: bool = False,
    ) -> None:
        self.run_id = run_id
        self.run_dir = Path(runs_dir) / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self._json_logs = json_logs
        self._lock = threading.Lock()

        # Open persistent log files
        self._log_fh = open(self.run_dir / "logs.txt", "a", encoding="utf-8")
        self._jsonl_fh: Optional[Any] = (
            open(self.run_dir / "logs.jsonl", "a", encoding="utf-8")
            if json_logs
            else None
        )

        # Initialise in-memory status and persist immediately
        self._status: Dict[str, Any] = {
            "run_id": run_id,
            "status": "running",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "events": [],
        }
        self._flush_status()

    # ── logging ──────────────────────────────────────────────────────────────

    def log(self, level: str, message: str) -> None:
        """Write a log line to ``logs.txt`` (and ``logs.jsonl`` if enabled)."""
        ts = _now_iso()
        line = f"{ts} [{level.upper()}] {message}\n"
        with self._lock:
            self._log_fh.write(line)
            self._log_fh.flush()
            if self._jsonl_fh is not None:
                record = {"ts": ts, "level": level.upper(), "msg": message}
                self._jsonl_fh.write(json.dumps(record) + "\n")
                self._jsonl_fh.flush()

    def info(self, message: str) -> None:
        self.log("INFO", message)

    def warning(self, message: str) -> None:
        self.log("WARNING", message)

    def error(self, message: str) -> None:
        self.log("ERROR", message)

    # ── progress events ──────────────────────────────────────────────────────

    def emit(
        self,
        stage: str,
        message: str,
        percent: Optional[int] = None,
        step: Optional[int] = None,
        total_steps: Optional[int] = None,
    ) -> None:
        """Append a progress event to ``events.jsonl`` and refresh ``status.json``.

        Parameters
        ----------
        stage:
            Pipeline stage name, e.g. ``"spec"`` or ``"scaffold"``.
        message:
            Human-readable description of what is happening.
        percent:
            Optional overall completion percentage (0–100).
        step:
            Optional current step counter within *total_steps*.
        total_steps:
            Optional total number of steps.
        """
        ts = _now_iso()
        event: Dict[str, Any] = {"ts": ts, "stage": stage, "message": message}
        if percent is not None:
            event["percent"] = percent
        if step is not None:
            event["step"] = step
        if total_steps is not None:
            event["total_steps"] = total_steps

        with self._lock:
            # Append to events.jsonl (append-only)
            events_path = self.run_dir / "events.jsonl"
            with open(events_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(event) + "\n")

            # Update in-memory status and persist
            self._status["updated_at"] = ts
            self._status["events"].append(event)
            self._flush_status()

        # Mirror the event as a log line for convenience
        pct_str = f" ({percent}%)" if percent is not None else ""
        self.info(f"[{stage}]{pct_str} {message}")

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def complete(self) -> None:
        """Mark the run as completed and flush ``status.json``."""
        with self._lock:
            self._status["status"] = "completed"
            self._status["updated_at"] = _now_iso()
            self._flush_status()
        self.info("Run completed successfully.")

    def fail(self, reason: str = "") -> None:
        """Mark the run as failed and flush ``status.json``."""
        with self._lock:
            self._status["status"] = "failed"
            self._status["updated_at"] = _now_iso()
            if reason:
                self._status["error"] = reason
            self._flush_status()
        self.error(f"Run failed: {reason}" if reason else "Run failed.")

    def close(self) -> None:
        """Flush and close all open file handles."""
        self._log_fh.close()
        if self._jsonl_fh is not None:
            self._jsonl_fh.close()

    # ── status helpers ────────────────────────────────────────────────────────

    def get_status(self, last_n_events: int = 20) -> Dict[str, Any]:
        """Return a copy of the current status with at most *last_n_events* events."""
        with self._lock:
            status = dict(self._status)
            status["events"] = list(status["events"])
        status["events"] = status["events"][-last_n_events:]
        return status

    def _flush_status(self) -> None:
        """Atomically write ``status.json`` (caller must hold ``self._lock``)."""
        tmp = self.run_dir / "status.json.tmp"
        target = self.run_dir / "status.json"
        tmp.write_text(json.dumps(self._status, indent=2), encoding="utf-8")
        tmp.replace(target)

    # ── context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> "RunTracker":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.fail(str(exc_val))
        else:
            self.complete()
        self.close()


# ── module-level helpers ──────────────────────────────────────────────────────


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string (second precision)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_status(
    run_id: str, runs_dir: str = "runs"
) -> Optional[Dict[str, Any]]:
    """Load ``status.json`` for *run_id*; return *None* if the file is absent."""
    path = Path(runs_dir) / run_id / "status.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
