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

```bash
# Generate a game project
gamegen --prompt "top down space shooter" --out game.zip

# Launch the AI Design Assistant
gamedesign-agent
```

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
