# GameGenerator

[![CI](https://github.com/highskills123/GameGenerator/actions/workflows/ci.yml/badge.svg)](https://github.com/highskills123/GameGenerator/actions/workflows/ci.yml)

A collection of game generation tools and AI-assisted design utilities.

## Installation

```bash
# Minimal install (no optional deps)
pip install -e .

# With Ollama / HTTP API support (installs requests)
pip install -e ".[ollama]"

# With local image generation via 🤗 diffusers
pip install -e ".[image]"

# Install everything (all optional features)
pip install -e ".[all]"

# Developer install (pytest, ruff, black)
pip install -e ".[dev]"
```

## Entry Points

After installation, the following CLI commands are available:

| Command | Description |
|---------|-------------|
| `gamegen` | Flutter/Flame game generator (main entry point) |
| `gamedesign-agent` | AI Game Design Assistant |
| `idle-rpg-gen` | **One-shot Idle RPG game generator** (design doc + full project) |

```bash
# Generate a game project
gamegen --prompt "top down space shooter" --out game.zip

# Launch the AI Design Assistant
gamedesign-agent

# One-shot Idle RPG: generate design doc + Flutter project in one command
idle-rpg-gen --prompt "A dark fantasy idle RPG set in a cursed kingdom" --out my_idle_rpg.zip
```

## One-Shot Idle RPG Generator

Generate a **complete, runnable Idle RPG game** from a single natural-language
prompt.  One command does everything:

1. **Design document** – generated via Ollama (when available) or a deterministic
   template fallback (fully offline, no paid APIs required).
2. **Flutter/Flame project** – idle auto-battle, upgrades, quests, enemies, save/load.
3. **ZIP archive** – ready to unzip, `flutter pub get`, and run.

### Quick Start (offline, no Ollama)

```bash
pip install -e .
idle-rpg-gen --prompt "A dark fantasy idle RPG set in a cursed kingdom" \
             --out my_idle_rpg.zip
```

### Quick Start (with Ollama for AI-generated content)

```bash
# Prerequisites: install and start Ollama, pull the model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5-coder:7b
ollama serve

pip install -e ".[ollama]"
idle-rpg-gen --prompt "A sci-fi space colony idle RPG" \
             --out space_colony.zip \
             --ollama-model qwen2.5-coder:7b
```

### Deterministic / Seeded Generation

Use `--seed` to make the generated content reproducible:

```bash
idle-rpg-gen --prompt "cursed kingdom idle RPG" --out game.zip --seed 42
```

### Run the Generated Project

```bash
# Prerequisites: Flutter SDK ≥ 3.10
unzip my_idle_rpg.zip -d my_idle_rpg
cd my_idle_rpg
flutter pub get
flutter run
```

### Design Document Formats

| Flag | Format | Default path |
|------|--------|--------------|
| *(none / default)* | JSON | `assets/design/design.json` |
| `--design-doc-format md` | Markdown | `DESIGN.md` |

### Full CLI reference

```
idle-rpg-gen --help
```

### Using `gamegen --idle-rpg` (alternative)

The same functionality is also accessible via the `gamegen` entry point:

```bash
gamegen --prompt "A cursed kingdom idle RPG" --out game.zip --idle-rpg
gamegen --prompt "sci-fi idle RPG" --out game.zip --idle-rpg --seed 42
```

### Generated project features

| Feature | Details |
|---------|---------|
| Idle auto-battle | Configurable tick rate; offline progress catch-up on resume |
| Upgrade system | 3 categories – Combat, Defence, Economy – with cost scaling |
| Combat / encounters | Enemy roster from design doc (`assets/data/enemies.json`) |
| Quests | Loaded from `assets/data/quests.json` (design-doc sourced) |
| Save / load | Persisted via `SharedPreferences`; reset option in Settings |
| UI screens | Battle · Quests · Heroes · Shop · Enemies · Settings |

## Features

### Feature 4 – AI Design Assistant

A free, open-source AI Game Design Assistant. No paid API keys required.

- **Multi-turn chat agent** that maintains conversation state
- **Procedural level generation** (seed-based, deterministic)
- **NPC dialogue writer** (template-based + optional local LLM via Ollama)
- **Art prompt generator** for Stable Diffusion / DALL-E (text prompts)
- **Optional local image generation** via AUTOMATIC1111 API or 🤗 diffusers

```bash
# Quick start (fully offline)
pip install -e .
python -m gamedesign_agent
# or use the installed entry point:
gamedesign-agent
```

For full documentation see [docs/AI_DESIGN_ASSISTANT.md](docs/AI_DESIGN_ASSISTANT.md).

### Idle RPG Design Document Generator (via Ollama)

Generate a complete Idle RPG design document (world, premise, story beats, quests,
characters, factions, locations, items, enemies, and optional dialogue samples,
upgrade tree, idle loops) from a natural-language prompt using a local Ollama LLM.

**Defaults:**
- Base URL: `http://localhost:11434`
- Model: `qwen2.5-coder:7b`

**Prerequisites:**

```bash
# 1. Install Ollama (Linux/macOS):
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull the default model:
ollama pull qwen2.5-coder:7b

# 3. Start Ollama (usually auto-started):
ollama serve
```

**Usage (root gamegen.py):**

```bash
# Generate a project with an Idle RPG design doc (JSON, default)
python gamegen.py \
    --prompt "A dark fantasy idle RPG set in a cursed kingdom overrun by undead" \
    --out my_game.zip \
    --design-doc

# Use Markdown format instead of JSON
python gamegen.py \
    --prompt "A sci-fi idle RPG where you build a space colony" \
    --out game.zip \
    --design-doc \
    --design-doc-format md \
    --design-doc-path DESIGN.md

# Custom Ollama model and tuning options
python gamegen.py \
    --prompt "idle RPG with upgrades" \
    --out game.zip \
    --design-doc \
    --ollama-model qwen2.5-coder:7b \
    --ollama-base-url http://localhost:11434 \
    --ollama-temperature 0.7 \
    --ollama-max-tokens 4096 \
    --ollama-timeout 180 \
    --ollama-seed 42
```

**Usage (GameGenerator/gamegen.py):**

```bash
cd GameGenerator
python gamegen.py \
    --prompt "A dark fantasy idle RPG set in a cursed kingdom" \
    --out my_game.zip \
    --design-doc
```

**Python API:**

```python
from gamegenerator.ai.design_assistant import generate_idle_rpg_design, design_doc_to_markdown

# Generate JSON design document
doc = generate_idle_rpg_design(
    "A dark fantasy idle RPG set in a cursed kingdom",
    model="qwen2.5-coder:7b",          # default
    base_url="http://localhost:11434",   # default
)
print(doc["world"])
print(doc["quests"][0]["title"])

# Convert to Markdown
md = design_doc_to_markdown(doc)
print(md)
```

**Design document schema:**

| Key | Type | Description |
|-----|------|-------------|
| `world` | string | Setting/world description |
| `premise` | string | Core narrative premise |
| `main_story_beats` | list[string] | 5–8 major story milestones |
| `quests` | list[object] | title, summary, objectives, rewards, giver, level_range |
| `characters` | list[object] | name, role, backstory, motivations, relationships |
| `factions` | list[object] | name, description, alignment, goals |
| `locations` | list[object] | name, description, type, notable_features |
| `items` | list[object] | name, type, rarity, description, stats |
| `enemies` | list[object] | name, type, description, abilities, loot |
| `dialogue_samples` *(optional)* | list[object] | character, lines |
| `upgrade_tree` *(optional)* | object | category → list of upgrades |
| `idle_loops` *(optional)* | list[object] | name, description, resource, tick_rate_seconds |
