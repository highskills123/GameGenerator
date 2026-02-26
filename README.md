# GameGenerator

[![CI](https://github.com/highskills123/GameGenerator/actions/workflows/ci.yml/badge.svg)](https://github.com/highskills123/GameGenerator/actions/workflows/ci.yml)

**One-click Flutter/Flame game generator.** Describe your game in plain English and get a complete, runnable project — Android-ready — in a single command.

## What it does

1. Understands your prompt and picks the right genre (top-down shooter or idle RPG).
2. Optionally uses a local AI (Ollama) to generate a rich design document: story, quests, characters, enemies, NPC dialogue, upgrade tree.
3. Scaffolds a complete Flutter/Flame project with all Dart source files, Android build files, assets, and a save system.
4. Packages everything into a ZIP you can unzip and run immediately with `flutter run`.

## Prerequisites

| # | What | Install |
|---|------|---------|
| 1 | **Python 3.9+** | https://www.python.org/downloads/ |
| 2 | **Flutter SDK ≥ 3.10** | https://docs.flutter.dev/get-started/install |
| 3 | **Ollama** *(optional – for AI-enhanced content)* | https://ollama.com |

## Installation

```bash
# Clone the repo
git clone https://github.com/highskills123/GameGenerator.git
cd GameGenerator

# Install (minimal – CLI tools only, no Ollama required)
pip install -e .

# Install with the HTTP API server (FastAPI + Uvicorn)
pip install -e ".[server]"

# Install with Ollama support (AI-enhanced content)
pip install -e ".[ollama]"

# Install everything
pip install -e ".[all]"
```

## Quick Start

### Generate any game (offline, no AI needed)

```bash
# Top-down space shooter
gamegen --prompt "top down space shooter with asteroids" --out shooter.zip

# Idle RPG
gamegen --prompt "idle RPG with hero upgrades and quests" --out idle_rpg.zip --idle-rpg
```

### Generate an Idle RPG with full AI content (requires Ollama)

```bash
# 1. Install and start Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5-coder:7b
ollama serve

# 2. Generate the game
idle-rpg-gen --prompt "A dark fantasy idle RPG in a cursed kingdom" \
             --out my_game.zip \
             --ollama-model qwen2.5-coder:7b
```

### Run the generated game on Android

```bash
# Unzip the project
unzip my_game.zip -d my_game
cd my_game

# Install Flutter dependencies
flutter pub get

# Run on a connected Android device or emulator
flutter run
```

> **Tip (Android build):** The generated project includes all required Android files
> (`build.gradle`, `MainActivity.kt`, `AndroidManifest.xml`, etc.) so `flutter run`
> works out of the box — no extra setup needed.

## CLI Reference

### `gamegen` — main game generator

```
gamegen --prompt "your game description" --out game.zip [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--prompt` | *(required)* | Natural-language game description |
| `--out` | *(required)* | Output ZIP file path |
| `--idle-rpg` | off | Generate an Idle RPG with full design doc |
| `--platform` | `android` | Target platform: `android` or `android+ios` |
| `--scope` | `prototype` | `prototype` or `vertical-slice` |
| `--art-style` | `pixel-art` | Art style hint |
| `--seed` | *(none)* | Integer seed for deterministic offline generation |
| `--model` | *(none)* | Ollama model for AI-enhanced spec |
| `--design-doc` | off | Also generate an Idle RPG design document |
| `--design-doc-format` | `json` | Design doc format: `json` or `md` |
| `--validate` | off | Run `flutter pub get` + `flutter analyze` |
| `--auto-fix` | off | Auto-patch and re-validate on failure |
| `--interactive` | off | Prompt for constraint questions before generating |

```bash
# Examples
gamegen --prompt "space shooter with power-ups" --out shooter.zip
gamegen --prompt "idle RPG with upgrades" --out rpg.zip --idle-rpg --seed 42
gamegen --prompt "space shooter" --out game.zip --model qwen2.5-coder:7b --validate
```

### `idle-rpg-gen` — one-shot Idle RPG generator

```
idle-rpg-gen --prompt "your concept" --out game.zip [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--prompt` | *(required)* | Natural-language Idle RPG description |
| `--out` | *(required)* | Output ZIP file path |
| `--seed` | *(none)* | RNG seed for deterministic offline generation |
| `--platform` | `android` | `android` or `android+ios` |
| `--design-doc-format` | `json` | `json` or `md` |
| `--ollama-model` | `qwen2.5-coder:7b` | Ollama model for AI content |
| `--ollama-base-url` | `http://localhost:11434` | Ollama server URL |
| `--ollama-temperature` | *(none)* | Sampling temperature (0.0–1.0) |
| `--ollama-timeout` | *(none)* | Request timeout in seconds |

```bash
# Offline (no Ollama) – uses template-based content
idle-rpg-gen --prompt "A dark fantasy idle RPG" --out game.zip

# Deterministic with a seed
idle-rpg-gen --prompt "cursed kingdom idle RPG" --out game.zip --seed 42

# AI-enhanced (requires Ollama)
idle-rpg-gen --prompt "sci-fi space colony RPG" --out game.zip \
             --ollama-model qwen2.5-coder:7b
```

## HTTP API Server

An optional **FastAPI** server ships with the package and exposes every generator
feature over HTTP — useful for integrating GameGenerator into a CI pipeline or
web UI.

### Start the server

```bash
# Install server dependencies first
pip install -e ".[server]"

# Start on the default port (8080)
python -m game_generator.server

# Custom host/port, with auto-reload (dev mode)
python -m game_generator.server --host 127.0.0.1 --port 9000 --reload

# Or use uvicorn directly
uvicorn game_generator.server.app:app --reload --port 8080
```

The server honors the `GAMEGEN_RUNS_DIR` environment variable for the run
storage directory (default: `runs/`).

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Minimal web UI |
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `POST` | `/spec` | Generate a `GameSpec` (heuristic or AI) |
| `POST` | `/design-doc` | Generate an Idle RPG design document |
| `POST` | `/generate` | Start a background generation job → returns `run_id` |
| `GET` | `/status/{run_id}` | Poll job status + all progress events |
| `GET` | `/download/{run_id}` | Download the completed output ZIP |

### Example: generate a game via the API

```bash
# Start a generation job
curl -s -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "idle RPG with hero upgrades", "platform": "android"}' \
  | python -m json.tool
# → {"run_id": "abc123", "status": "queued"}

# Poll until complete
curl -s http://localhost:8080/status/abc123 | python -m json.tool

# Download the ZIP
curl -OJ http://localhost:8080/download/abc123
```

Interactive API docs (Swagger UI) are auto-generated at
`http://localhost:8080/docs`.

## Generated Project Features

### Top-Down Shooter

| File | Description |
|------|-------------|
| `lib/game/game.dart` | Main Flame game class, enemy spawning, collision detection |
| `lib/game/player.dart` | Player movement (keyboard + mobile joystick) |
| `lib/game/enemy.dart` | Enemy AI and movement |
| `lib/game/bullet.dart` | Bullet with hitbox |
| `lib/game/bullet_pool.dart` | Object pool (no per-shot allocations) |
| `lib/game/hud.dart` | Score / health HUD overlay |
| `lib/game/mobile_controls.dart` | Virtual joystick + fire button |
| `lib/game/game_over_overlay.dart` | Game-over screen with restart |
| `lib/game/save_manager.dart` | High-score persistence via SharedPreferences |

### Idle RPG

| Feature | Details |
|---------|---------|
| Idle auto-battle | Configurable tick rate; offline progress catch-up on resume |
| Upgrade system | 3 categories – Combat, Defence, Economy – with cost scaling |
| Combat / encounters | Enemy roster from `assets/data/enemies.json` |
| Quests | Loaded from `assets/data/quests.json` |
| NPC dialogue | AI-generated dialogue in `assets/data/dialogue.json` |
| Save / load | Persisted via `SharedPreferences`; reset option in Settings |
| UI screens | Battle · Quests · Heroes · Shop · Settings |
| Design document | World, story beats, factions, locations, items in `assets/design/design.json` |

### Android files (included in every generated project)

The generator outputs a complete Android project so the game builds and runs on
any Android device without extra setup:

- `android/build.gradle` + `android/app/build.gradle`
- `android/settings.gradle` + `android/gradle.properties`
- `android/gradle/wrapper/gradle-wrapper.properties`
- `android/app/src/main/kotlin/…/MainActivity.kt`
- `android/app/src/main/AndroidManifest.xml`
- `android/app/src/main/res/` (styles, launch background)

## Using Ollama for AI-Enhanced Content

When Ollama is available the generator uses it to create richer content.
When Ollama is **not** available it falls back automatically to template-based
content — no error, no paid API required.

```bash
# Install Ollama (Linux/macOS)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the recommended model (~4 GB, one-time download)
ollama pull qwen2.5-coder:7b

# Start Ollama (usually auto-started)
ollama serve
```

Then add `--ollama-model qwen2.5-coder:7b` (or `--model qwen2.5-coder:7b` for `gamegen`)
to any generator command.

## Supported Genres

| Genre | Keywords detected | Description |
|-------|------------------|-------------|
| `top_down_shooter` | shoot, shooter, bullet, space, gun, blast, asteroid | Scrolling top-down shooter with enemy waves |
| `idle_rpg` | idle, rpg, clicker, upgrade, hero, quest, adventure, level up | Idle auto-battle RPG with upgrades and quests |

> More genres coming soon. Use `--idle-rpg` to force the Idle RPG genre regardless of keywords.
