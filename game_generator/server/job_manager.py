"""
game_generator/server/job_manager.py – In-process job manager for game generation runs.

Each run gets:
    runs/{run_id}/
        request.json   – normalised request parameters
        spec.json      – generated GameSpec (written after spec stage)
        design.json    – design document (if requested)
        logs.txt       – human-readable timestamped log lines
        status.json    – latest status snapshot (survives restart)
        output.zip     – final result (written on completion)

In-memory state is kept in a module-level dict so the same process can serve
status queries for running jobs.  On restart, status is re-hydrated from
status.json so completed/failed jobs remain queryable.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from orchestrator.run_tracker import RunTracker, load_status

_JOBS: Dict[str, RunTracker] = {}
_LOCK = threading.Lock()


def new_run_id() -> str:
    """Return a fresh UUID4 run identifier."""
    return str(uuid.uuid4())


def get_run_dir(run_id: str, runs_dir: str) -> Path:
    """Return (and create) the directory for *run_id*."""
    path = Path(runs_dir) / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_request(run_id: str, runs_dir: str, data: Dict[str, Any]) -> None:
    """Persist the normalised request as ``request.json``."""
    path = get_run_dir(run_id, runs_dir) / "request.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_artifact(run_id: str, runs_dir: str, filename: str, content: str) -> None:
    """Write an arbitrary text artifact into the run directory."""
    path = get_run_dir(run_id, runs_dir) / filename
    path.write_text(content, encoding="utf-8")


def create_tracker(run_id: str, runs_dir: str) -> RunTracker:
    """Create a :class:`RunTracker` for *run_id* and register it in memory."""
    tracker = RunTracker(run_id=run_id, runs_dir=runs_dir)
    with _LOCK:
        _JOBS[run_id] = tracker
    return tracker


def get_status(run_id: str, runs_dir: str) -> Optional[Dict[str, Any]]:
    """
    Return the status dict for *run_id*.

    Checks in-memory first (for live runs), then falls back to
    ``status.json`` on disk (for completed / restarted runs).
    Returns *None* when the run is completely unknown.
    """
    with _LOCK:
        tracker = _JOBS.get(run_id)
    if tracker is not None:
        # Return ALL events (no trim) so the UI can accumulate them.
        status = tracker.get_status(last_n_events=10_000)
        return status
    return load_status(run_id, runs_dir=runs_dir)
