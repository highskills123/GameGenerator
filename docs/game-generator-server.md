# GameGenerator FastAPI Server

The `game_generator.server` package provides a self-contained FastAPI backend and minimal Web UI for asynchronous Flutter/Flame game generation.

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Start Ollama locally for AI-enhanced specs / design docs
#    https://ollama.com/download
ollama serve
ollama pull qwen2.5-coder:7b   # or any model you prefer

# 3. Start the GameGenerator server
python -m game_generator.server
```

Open **http://localhost:8080/** in your browser.

You can also pass flags:

```bash
python -m game_generator.server --host 127.0.0.1 --port 9000 --reload
```

Or run directly with uvicorn:

```bash
uvicorn game_generator.server.app:app --reload --port 8080
```

---

## Web UI

The server serves a minimal Web UI at `GET /`. It lets you:

1. Describe your game in plain English.
2. Choose platform, scope, and art style.
3. Optionally enable Flutter validation, auto-fix, and design-doc generation.
4. Click **Generate Game** – a background job starts and a real-time progress log appears.

**Progress messages never disappear.** Every status update emitted by the pipeline is appended to the log panel. New messages accumulate at the bottom; nothing is cleared or replaced while the job is running or after it completes.

When generation finishes a **Download ZIP** button appears.

---

## API Endpoints

### `GET /health`

```bash
curl http://localhost:8080/health
# {"status":"ok","service":"game-generator"}
```

### `POST /spec`

Generate a GameSpec from a prompt (synchronous, no background job).

```bash
curl -X POST http://localhost:8080/spec \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"top-down space shooter with waves","platform":"android","scope":"prototype"}'
```

### `POST /design-doc`

Generate an Idle RPG design document via Ollama (synchronous).

```bash
curl -X POST http://localhost:8080/design-doc \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"idle RPG with hero upgrades","ollama_model":"qwen2.5-coder:7b","format":"json"}'
```

### `POST /generate`

Start an asynchronous game generation job.  Returns a `run_id` immediately.

```bash
curl -X POST http://localhost:8080/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "top-down space shooter with power-ups",
    "platform": "android",
    "scope": "prototype",
    "art_style": "pixel-art",
    "auto_fix": false
  }'
# {"run_id":"<uuid>","status":"started","runs_dir":"runs"}
```

### `GET /status/{run_id}`

Poll the status of a generation run.  Returns **all** progress events (nothing is trimmed) so clients can accumulate the full history.

```bash
curl http://localhost:8080/status/<run_id>
```

Response fields:

| Field | Description |
|---|---|
| `status` | `running` / `completed` / `failed` |
| `events` | All progress events (stage, message, percent, timestamp) |
| `error` | Present only when `status` is `failed` |

### `GET /download/{run_id}`

Download the completed output ZIP.

```bash
curl -OJ http://localhost:8080/download/<run_id>
```

Returns `409` if the run is not yet complete, `404` if the ZIP is missing.

---

## Run artifacts

Each job creates a directory under `runs/<run_id>/`:

| File | Contents |
|---|---|
| `request.json` | Normalised request parameters |
| `logs.txt` | Human-readable timestamped log |
| `status.json` | Latest status snapshot (survives restart) |
| `output.zip` | Generated Flutter/Flame project |

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `GAMEGEN_RUNS_DIR` | `runs` | Directory for run artifacts |
