# Pipeline Observability – Logging & Progress Events

This document describes the run-artifacts layout produced by the game
generation pipeline and explains how to tail logs and progress events in
real time.

---

## Artifacts layout

Every pipeline run writes its artifacts to a dedicated directory:

```
runs/
└── {run_id}/
    ├── status.json    – current pipeline status (updated on every event)
    ├── events.jsonl   – append-only progress events (one JSON object per line)
    ├── logs.txt       – human-readable timestamped log lines
    ├── logs.jsonl     – structured JSON-Lines log (optional, see below)
    └── output.zip     – final game ZIP (present after completion)
```

`{run_id}` is a UUID generated automatically when a run starts.

The base directory defaults to `runs/` relative to the working directory and
can be overridden with the environment variable `GAMEGEN_RUNS_DIR`.

---

## File formats

### `status.json`

Updated atomically (via a `.tmp` swap) every time a progress event is emitted
or the pipeline status changes.

```json
{
  "run_id": "a1b2c3d4-...",
  "status": "running",
  "created_at": "2024-01-15T10:00:00+00:00",
  "updated_at": "2024-01-15T10:00:42+00:00",
  "events": [
    {
      "ts": "2024-01-15T10:00:05+00:00",
      "stage": "constraints",
      "message": "Resolving constraints …",
      "percent": 0
    },
    {
      "ts": "2024-01-15T10:00:10+00:00",
      "stage": "spec",
      "message": "Generating game spec …",
      "percent": 10
    }
  ]
}
```

**`status` values**

| Value       | Meaning                                    |
|-------------|--------------------------------------------|
| `running`   | Pipeline is actively executing             |
| `completed` | Pipeline finished successfully             |
| `failed`    | Pipeline encountered a fatal error         |

When `status` is `failed` an additional `"error"` key contains the reason.

### `events.jsonl`

One JSON object per line, appended in strict chronological order.  Each line
is self-contained and can be parsed independently.

```jsonl
{"ts":"2024-01-15T10:00:05+00:00","stage":"constraints","message":"Resolving constraints …","percent":0}
{"ts":"2024-01-15T10:00:10+00:00","stage":"spec","message":"Generating game spec …","percent":10}
{"ts":"2024-01-15T10:00:15+00:00","stage":"spec","message":"Spec ready – title=Space Blaster genre=top_down_shooter","percent":20}
```

**Event fields**

| Field         | Type    | Required | Description                               |
|---------------|---------|----------|-------------------------------------------|
| `ts`          | string  | ✓        | ISO-8601 UTC timestamp (second precision) |
| `stage`       | string  | ✓        | Pipeline stage name                       |
| `message`     | string  | ✓        | Human-readable description                |
| `percent`     | integer | –        | Overall completion (0–100)                |
| `step`        | integer | –        | Current step within a stage               |
| `total_steps` | integer | –        | Total steps in the stage                  |

**Pipeline stages (in order)**

| Stage         | Approximate `percent` |
|---------------|----------------------:|
| `constraints` | 0                     |
| `spec`        | 10–20                 |
| `design_doc`  | 25–35 *(optional)*    |
| `assets`      | 40–50                 |
| `scaffold`    | 60–75                 |
| `validation`  | 80–90 *(optional)*    |
| `zip`         | 95–100                |

### `logs.txt`

Plain-text log file with one line per message:

```
2024-01-15T10:00:05+00:00 [INFO] [constraints] (0%) Resolving constraints …
2024-01-15T10:00:10+00:00 [INFO] [spec] (10%) Generating game spec …
2024-01-15T10:00:42+00:00 [INFO] Run completed successfully.
```

### `logs.jsonl`

Optional structured log (enabled with `json_logs=True` on `RunTracker` or
the `json_logs` field in the `POST /generate` request body).

```jsonl
{"ts":"2024-01-15T10:00:05+00:00","level":"INFO","msg":"[constraints] (0%) Resolving constraints …"}
```

---

## How to tail logs and events in real time

### Tail human-readable logs

```bash
tail -f runs/<run_id>/logs.txt
```

### Stream structured events

```bash
tail -f runs/<run_id>/events.jsonl | while IFS= read -r line; do
    echo "$line" | python3 -c "
import json, sys
e = json.load(sys.stdin)
print(f\"{e['ts']}  [{e['stage']:12}]  {e.get('percent', '--'):>3}%  {e['message']}\")"
done
```

### Poll via the REST API

```bash
# Start a run
RUN_ID=$(curl -s -X POST http://localhost:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"top down space shooter"}' | python3 -c "import json,sys; print(json.load(sys.stdin)['run_id'])")

# Poll status (returns last 20 events by default)
curl http://localhost:8000/status/$RUN_ID

# Limit to last 5 events
curl "http://localhost:8000/status/$RUN_ID?last=5"
```

---

## FastAPI server

Start the game generation server with:

```bash
uvicorn game_server:app --reload
# or
python game_server.py
```

### Endpoints

| Method | Path                 | Description                                    |
|--------|----------------------|------------------------------------------------|
| `GET`  | `/health`            | Health check                                   |
| `POST` | `/generate`          | Start an async game generation run             |
| `GET`  | `/status/{run_id}`   | Poll status + last N events (`?last=20`)       |

### `POST /generate` request body

```json
{
  "prompt":    "idle RPG with upgrades",
  "platform":  "android",
  "scope":     "prototype",
  "art_style": "pixel-art",
  "online":    false,
  "auto_fix":  false,
  "json_logs": false
}
```

Set `json_logs: true` to additionally produce `logs.jsonl` in the run
artifacts directory.

---

## Using `RunTracker` programmatically

```python
from orchestrator.run_tracker import RunTracker

tracker = RunTracker(run_id="my-run", runs_dir="runs", json_logs=True)
with tracker:
    tracker.emit("spec", "Generating game spec …", percent=10)
    tracker.emit("scaffold", "Building files …", percent=60)
    # … do work …
    tracker.emit("zip", "ZIP ready", percent=100)
# On exit: marks status as "completed" and closes file handles.
```

The `RunTracker` can also be used standalone in the CLI by passing it to
`Orchestrator.run()`:

```python
from orchestrator.orchestrator import Orchestrator
from orchestrator.run_tracker import RunTracker

tracker = RunTracker(run_id="cli-run-001", runs_dir="runs", json_logs=True)
with tracker:
    Orchestrator().run(
        prompt="space shooter",
        output_zip="runs/cli-run-001/output.zip",
        run_tracker=tracker,
    )
```
