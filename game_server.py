#!/usr/bin/env python3
"""
game_server.py – FastAPI server for asynchronous game generation.

Each POST /generate call starts a background job and returns a run_id.
Use GET /status/{run_id} to poll progress events and the final result.

Usage
-----
    uvicorn game_server:app --reload
    # or
    python game_server.py

Endpoints
---------
    POST /generate           – Start a new game generation run
    GET  /status/{run_id}    – Poll run status and last N progress events
    GET  /health             – Health check
"""

from __future__ import annotations

import os
import threading
import uuid
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from orchestrator.orchestrator import Orchestrator
from orchestrator.run_tracker import RunTracker, load_status

app = FastAPI(
    title="Game Generator API",
    description="Asynchronous Flutter/Flame game generation pipeline",
    version="1.0.0",
)

# Directory that will contain runs/{run_id}/ sub-directories
RUNS_DIR: str = os.environ.get("GAMEGEN_RUNS_DIR", "runs")


# ── request/response models ───────────────────────────────────────────────────


class GenerateRequest(BaseModel):
    """Request body for POST /generate."""

    prompt: str
    platform: str = "android"
    scope: str = "prototype"
    art_style: str = "pixel-art"
    online: bool = False
    auto_fix: bool = False
    json_logs: bool = False


class GenerateResponse(BaseModel):
    """Immediate response returned when a run is queued."""

    run_id: str
    status: str
    runs_dir: str


# ── background job ────────────────────────────────────────────────────────────


def _run_generation(run_id: str, req: GenerateRequest) -> None:
    """Execute the full orchestrator pipeline inside a background thread."""
    output_zip = os.path.join(RUNS_DIR, run_id, "output.zip")
    tracker = RunTracker(run_id=run_id, runs_dir=RUNS_DIR, json_logs=req.json_logs)
    with tracker:
        orch = Orchestrator()
        orch.run(
            prompt=req.prompt,
            output_zip=output_zip,
            platform=req.platform,
            scope=req.scope,
            auto_fix=req.auto_fix,
            constraint_overrides={
                "art_style": req.art_style,
                "online": req.online or None,
            },
            run_tracker=tracker,
        )


# ── endpoints ─────────────────────────────────────────────────────────────────


@app.get("/health", tags=["meta"])
def health() -> Dict[str, str]:
    """Simple health-check endpoint."""
    return {"status": "ok", "service": "game-generator"}


@app.post("/generate", response_model=GenerateResponse, tags=["generation"])
def start_generation(
    request: GenerateRequest, background_tasks: BackgroundTasks
) -> GenerateResponse:
    """Start an asynchronous game generation run.

    Returns a **run_id** immediately.  Poll ``GET /status/{run_id}`` to track
    progress.
    """
    run_id = str(uuid.uuid4())
    background_tasks.add_task(_run_generation, run_id, request)
    return GenerateResponse(run_id=run_id, status="started", runs_dir=RUNS_DIR)


@app.get("/status/{run_id}", tags=["generation"])
def get_status(run_id: str, last: int = 20) -> Dict[str, Any]:
    """Return the current status of a generation run.

    Parameters
    ----------
    run_id:
        The run identifier returned by ``POST /generate``.
    last:
        Maximum number of recent progress events to include (default: 20).
    """
    status = load_status(run_id, runs_dir=RUNS_DIR)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found.")
    # Trim events list to the last *last* entries
    status["events"] = status["events"][-last:]
    return status


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("game_server:app", host="0.0.0.0", port=8000, reload=False)
