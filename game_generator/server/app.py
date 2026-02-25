"""
game_generator/server/app.py – FastAPI application for asynchronous game generation.

Endpoints
---------
    GET  /                            – Minimal Web UI
    POST /spec                        – Generate a GameSpec (heuristic or AI)
    POST /design-doc                  – Generate an Idle RPG design document
    POST /generate                    – Start a background generation job
    GET  /status/{run_id}             – Poll run status + ALL progress events
    GET  /download/{run_id}           – Download the completed output ZIP

Run locally
-----------
    python -m game_generator.server
    # or
    uvicorn game_generator.server.app:app --reload --port 8080
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from . import job_manager

DEFAULT_RUNS_DIR: str = os.environ.get("GAMEGEN_RUNS_DIR", "runs")

app = FastAPI(
    title="GameGenerator API",
    description="Asynchronous Flutter/Flame game generation pipeline",
    version="1.0.0",
)


# ── Pydantic request models ────────────────────────────────────────────────────


class SpecRequest(BaseModel):
    prompt: str
    platform: str = "android"
    scope: str = "prototype"
    art_style: str = "pixel-art"


class DesignDocRequest(BaseModel):
    prompt: str
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    ollama_temperature: Optional[float] = None
    ollama_max_tokens: Optional[int] = None
    ollama_timeout: Optional[int] = None
    ollama_seed: Optional[int] = None
    format: str = "json"


class GenerateRequest(BaseModel):
    prompt: str
    platform: str = "android"
    scope: str = "prototype"
    art_style: str = "pixel-art"
    assets_dir: Optional[str] = None
    online: bool = False
    auto_fix: bool = False
    run_validation: bool = False
    design_doc: bool = False
    design_doc_format: str = "json"
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    ollama_temperature: Optional[float] = None
    ollama_max_tokens: Optional[int] = None
    ollama_timeout: Optional[int] = None
    ollama_seed: Optional[int] = None


# ── Background task ────────────────────────────────────────────────────────────


def _run_generation(run_id: str, req: GenerateRequest, runs_dir: str) -> None:
    """Execute the full orchestrator pipeline in a background thread."""
    output_zip = str(Path(runs_dir) / run_id / "output.zip")
    tracker = job_manager.create_tracker(run_id, runs_dir)
    with tracker:
        from orchestrator.orchestrator import Orchestrator

        orch = Orchestrator()
        orch.run(
            prompt=req.prompt,
            output_zip=output_zip,
            assets_dir=req.assets_dir,
            platform=req.platform,
            scope=req.scope,
            auto_fix=req.auto_fix,
            run_validation=req.run_validation,
            design_doc=req.design_doc,
            design_doc_format=req.design_doc_format,
            ollama_base_url=req.ollama_base_url,
            ollama_model=req.ollama_model,
            ollama_temperature=req.ollama_temperature,
            ollama_max_tokens=req.ollama_max_tokens,
            ollama_timeout=req.ollama_timeout,
            ollama_seed=req.ollama_seed,
            constraint_overrides={
                "art_style": req.art_style,
                "online": req.online or None,
            },
            run_tracker=tracker,
        )


# ── Endpoints ──────────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse, tags=["ui"])
def index() -> str:
    """Serve the minimal game-generation Web UI."""
    return _UI_HTML


@app.post("/spec", tags=["generation"])
def generate_spec(req: SpecRequest) -> Dict[str, Any]:
    """
    Generate a GameSpec from a natural-language prompt.

    Returns the full spec JSON immediately (synchronous, no background job).
    """
    from game_generator.spec import generate_spec as _gen_spec

    spec = _gen_spec(req.prompt)
    spec.update(
        {
            "art_style": req.art_style,
            "platform": req.platform,
            "scope": req.scope,
        }
    )
    return {"success": True, "spec": spec}


@app.post("/design-doc", tags=["generation"])
def generate_design_doc(req: DesignDocRequest) -> Dict[str, Any]:
    """
    Generate an Idle RPG design document via Ollama.

    Returns the document as JSON or Markdown immediately (synchronous).
    """
    try:
        from game_generator.ai.design_assistant import (
            generate_idle_rpg_design,
            design_doc_to_markdown,
        )
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"design_assistant module not available: {exc}",
        )

    try:
        doc = generate_idle_rpg_design(
            req.prompt,
            model=req.ollama_model,
            base_url=req.ollama_base_url,
            temperature=req.ollama_temperature,
            max_tokens=req.ollama_max_tokens,
            timeout=req.ollama_timeout,
            seed=req.ollama_seed,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if req.format == "md":
        content = design_doc_to_markdown(doc)
        return {"success": True, "format": "md", "content": content}
    return {"success": True, "format": "json", "content": doc}


@app.post("/generate", tags=["generation"])
def start_generation(
    req: GenerateRequest, background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Start an asynchronous game generation run.

    Returns a **run_id** immediately.  Poll ``GET /status/{run_id}`` to track
    progress and ``GET /download/{run_id}`` to fetch the ZIP when complete.
    """
    runs_dir = DEFAULT_RUNS_DIR
    run_id = job_manager.new_run_id()

    # Write request.json before the background task starts
    job_manager.write_request(run_id, runs_dir, req.model_dump())

    background_tasks.add_task(_run_generation, run_id, req, runs_dir)
    return {"run_id": run_id, "status": "started", "runs_dir": runs_dir}


@app.get("/status/{run_id}", tags=["generation"])
def get_status(run_id: str) -> Dict[str, Any]:
    """
    Return the current status of a generation run.

    Returns **all** progress events so the client can accumulate them without
    any message being silently dropped or replaced.
    """
    status = job_manager.get_status(run_id, DEFAULT_RUNS_DIR)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found.")
    return status


@app.get("/download/{run_id}", tags=["generation"])
def download_zip(run_id: str) -> FileResponse:
    """Return the completed output ZIP for *run_id*."""
    status = job_manager.get_status(run_id, DEFAULT_RUNS_DIR)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found.")
    if status.get("status") != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"Run {run_id!r} is not yet complete (status={status.get('status')!r}).",
        )
    zip_path = Path(DEFAULT_RUNS_DIR) / run_id / "output.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="output.zip not found for this run.")
    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=f"game_{run_id[:8]}.zip",
    )


@app.get("/health", tags=["meta"])
def health() -> Dict[str, str]:
    """Simple health-check endpoint."""
    return {"status": "ok", "service": "game-generator"}


# ── Minimal Web UI (single-file HTML, no external framework) ──────────────────

_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>GameGenerator</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0f1117;--surface:#1a1d27;--border:#2d3148;
  --accent:#6c63ff;--accent-h:#5a52e0;
  --text:#e2e8f0;--muted:#8892a4;
  --success:#10b981;--error:#fca5a5;--error-bg:#2d1515;
  --radius:10px;--mono:'Cascadia Code','Fira Code',monospace;
}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
     font-size:15px;line-height:1.6;min-height:100vh;display:flex;flex-direction:column}
header{background:var(--surface);border-bottom:1px solid var(--border);padding:.9rem 1.5rem;
       display:flex;align-items:center;gap:.75rem}
header h1{font-size:1.25rem;font-weight:700;letter-spacing:-.02em}
header span{font-size:1.5rem}
main{flex:1;max-width:900px;width:100%;margin:2rem auto;padding:0 1.25rem;display:flex;flex-direction:column;gap:1.5rem}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:1.5rem}
.card h2{font-size:1rem;font-weight:600;margin-bottom:1rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
label{display:block;font-size:.85rem;color:var(--muted);margin-bottom:.3rem}
textarea,input,select{
  width:100%;background:#0f1117;color:var(--text);border:1px solid var(--border);
  border-radius:6px;padding:.55rem .75rem;font-size:.95rem;font-family:inherit;
  outline:none;transition:border-color .15s}
textarea:focus,input:focus,select:focus{border-color:var(--accent)}
textarea{resize:vertical;min-height:90px}
.row{display:flex;gap:1rem;flex-wrap:wrap}
.row .col{flex:1;min-width:140px}
.checks{display:flex;gap:1.5rem;flex-wrap:wrap;margin-top:.25rem}
.checks label{display:flex;align-items:center;gap:.45rem;color:var(--text);font-size:.9rem;cursor:pointer;margin:0}
.checks input[type=checkbox]{width:auto;accent-color:var(--accent)}
.btn{display:inline-flex;align-items:center;gap:.5rem;background:var(--accent);color:#fff;
     border:none;border-radius:8px;padding:.65rem 1.4rem;font-size:.95rem;font-weight:600;
     cursor:pointer;transition:background .15s}
.btn:hover:not(:disabled){background:var(--accent-h)}
.btn:disabled{opacity:.55;cursor:not-allowed}
/* Log area – messages NEVER disappear; new entries append at the bottom */
#log{
  background:#0a0c13;border:1px solid var(--border);border-radius:6px;
  font-family:var(--mono);font-size:.82rem;line-height:1.55;
  padding:.75rem 1rem;min-height:180px;max-height:420px;
  overflow-y:auto;white-space:pre-wrap;word-break:break-word}
.log-info{color:var(--text)}
.log-success{color:var(--success)}
.log-error{color:var(--error)}
.log-stage{color:#a78bfa;font-weight:600}
.progress-bar-wrap{height:6px;background:var(--border);border-radius:3px;margin-bottom:.75rem;overflow:hidden}
.progress-bar{height:100%;background:var(--accent);border-radius:3px;transition:width .4s ease;width:0%}
#dl-section{display:none}
#dl-link{
  display:inline-flex;align-items:center;gap:.5rem;background:var(--success);color:#fff;
  border-radius:8px;padding:.65rem 1.4rem;font-size:.95rem;font-weight:600;
  text-decoration:none;transition:opacity .15s}
#dl-link:hover{opacity:.85}
footer{text-align:center;padding:1rem;color:var(--muted);font-size:.8rem;border-top:1px solid var(--border)}
</style>
</head>
<body>
<header>
  <span>🎮</span>
  <h1>GameGenerator</h1>
</header>
<main>
  <div class="card" id="form-card">
    <h2>New Generation</h2>
    <div style="display:flex;flex-direction:column;gap:1rem">
      <div>
        <label for="prompt">Game description</label>
        <textarea id="prompt" rows="4"
          placeholder="e.g. top-down space shooter with wave enemies and power-ups"></textarea>
      </div>
      <div class="row">
        <div class="col">
          <label for="platform">Platform</label>
          <select id="platform">
            <option value="android">Android</option>
            <option value="android+ios">Android + iOS</option>
          </select>
        </div>
        <div class="col">
          <label for="scope">Scope</label>
          <select id="scope">
            <option value="prototype">Prototype</option>
            <option value="vertical-slice">Vertical Slice</option>
          </select>
        </div>
        <div class="col">
          <label for="art-style">Art style</label>
          <input id="art-style" type="text" value="pixel-art" />
        </div>
      </div>
      <div>
        <label>Options</label>
        <div class="checks">
          <label><input type="checkbox" id="opt-validate" /> Validate (flutter analyze)</label>
          <label><input type="checkbox" id="opt-autofix" /> Auto-fix</label>
          <label><input type="checkbox" id="opt-design-doc" /> Generate design doc</label>
        </div>
      </div>
      <div>
        <button class="btn" id="gen-btn" onclick="startGeneration()">
          ▶ Generate Game
        </button>
      </div>
    </div>
  </div>

  <div class="card" id="status-card" style="display:none">
    <h2>Progress</h2>
    <div class="progress-bar-wrap"><div class="progress-bar" id="pbar"></div></div>
    <!-- Log area: messages are appended and NEVER cleared or replaced -->
    <div id="log"></div>
    <div id="dl-section" style="margin-top:1rem">
      <a id="dl-link" href="#">⬇ Download ZIP</a>
    </div>
  </div>
</main>
<footer>GameGenerator · <a href="/health" style="color:var(--accent)">health</a></footer>

<script>
'use strict';

let _runId = null;
let _pollTimer = null;
let _seenCount = 0;   // number of events already rendered — never decremented

function appendLog(text, cls) {
  const log = document.getElementById('log');
  const line = document.createElement('div');
  line.className = cls || 'log-info';
  line.textContent = text;
  log.appendChild(line);
  // Auto-scroll to the newest message
  log.scrollTop = log.scrollHeight;
}

async function startGeneration() {
  const prompt = document.getElementById('prompt').value.trim();
  if (!prompt) { alert('Please enter a game description.'); return; }

  const body = {
    prompt,
    platform:     document.getElementById('platform').value,
    scope:        document.getElementById('scope').value,
    art_style:    document.getElementById('art-style').value.trim() || 'pixel-art',
    run_validation: document.getElementById('opt-validate').checked,
    auto_fix:       document.getElementById('opt-autofix').checked,
    design_doc:     document.getElementById('opt-design-doc').checked,
  };

  document.getElementById('gen-btn').disabled = true;
  document.getElementById('status-card').style.display = '';
  document.getElementById('dl-section').style.display = 'none';
  // Log area is NOT cleared between runs — messages accumulate
  appendLog('▶ Starting generation…', 'log-stage');
  _seenCount = 0;

  try {
    const res  = await fetch('/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) { appendLog('✗ ' + (data.detail || 'Server error'), 'log-error'); resetBtn(); return; }
    _runId = data.run_id;
    appendLog('Run ID: ' + _runId, 'log-info');
    _pollTimer = setInterval(pollStatus, 1500);
  } catch (err) {
    appendLog('✗ ' + err.message, 'log-error');
    resetBtn();
  }
}

async function pollStatus() {
  if (!_runId) return;
  try {
    const res  = await fetch('/status/' + _runId);
    const data = await res.json();
    if (!res.ok) { appendLog('✗ ' + (data.detail || 'Poll error'), 'log-error'); stopPolling(); return; }

    const events = data.events || [];
    // Only render events we haven't shown yet — messages NEVER disappear
    for (let i = _seenCount; i < events.length; i++) {
      const ev = events[i];
      const pct = ev.percent !== undefined ? ' (' + ev.percent + '%)' : '';
      appendLog('[' + ev.stage + ']' + pct + ' ' + ev.message, 'log-stage');
      if (ev.percent !== undefined) {
        document.getElementById('pbar').style.width = ev.percent + '%';
      }
    }
    _seenCount = events.length;

    if (data.status === 'completed') {
      appendLog('✓ Generation complete!', 'log-success');
      document.getElementById('pbar').style.width = '100%';
      document.getElementById('dl-section').style.display = '';
      document.getElementById('dl-link').href = '/download/' + _runId;
      stopPolling();
      resetBtn();
    } else if (data.status === 'failed') {
      appendLog('✗ Failed: ' + (data.error || 'unknown error'), 'log-error');
      stopPolling();
      resetBtn();
    }
  } catch (err) {
    appendLog('⚠ Poll error: ' + err.message, 'log-error');
  }
}

function stopPolling() {
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
}

function resetBtn() {
  document.getElementById('gen-btn').disabled = false;
}
</script>
</body>
</html>"""
