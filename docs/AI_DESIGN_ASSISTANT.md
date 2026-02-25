# AI Design Assistant – Feature 4

A **free, open-source** AI Game Design Assistant integrated into GameGenerator.  
No paid API keys required. Works fully offline out of the box.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Running the Assistant](#running-the-assistant)
5. [Configuration](#configuration)
6. [Connecting a Local LLM (Ollama)](#connecting-a-local-llm-ollama)
7. [Connecting Local Stable Diffusion](#connecting-local-stable-diffusion)
8. [Module Reference](#module-reference)
9. [Running Tests](#running-tests)
10. [Licensing and Model Weights](#licensing-and-model-weights)

---

## Overview

The AI Design Assistant module (`gamedesign_agent/`) provides:

| Feature | Description |
|---------|-------------|
| **Multi-turn GameDesignAgent** | Chat-style assistant that maintains conversation state across turns |
| **Procedural Level Generation** | Seed-based dungeon/map generator with ASCII + JSON output |
| **NPC Dialogue Writer** | Template-based NPC dialogue (+ optional Ollama/HF LLM backend) |
| **Art Prompt Generator** | Generates detailed prompts for Stable Diffusion / DALL-E |
| **Local SD Integration** | Optional adapters for AUTOMATIC1111 API or diffusers |

**Strict constraint**: all code uses only free/open-source libraries.  
The default mode is fully offline – no network calls, no GPU, no API keys.

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/highskills123/GameGenerator
cd GameGenerator

# Install (minimal – no extra deps needed for offline mode)
pip install -e .

# Or install with optional extras:
pip install -e ".[config,llm]"   # .env support + HTTP backends
pip install -e ".[dev]"          # + test tools

# Launch the interactive assistant
python -m gamedesign_agent

# Or use the installed entry-point
gamedesign-agent
```

---

## Installation

### Minimal (fully offline, stdlib only)

```bash
pip install -e .
```

### With `.env` file support

```bash
pip install -e ".[config]"
# or: pip install python-dotenv
```

### With Ollama / HuggingFace API support

```bash
pip install -e ".[llm]"
# or: pip install requests
```

### With local Stable Diffusion (diffusers)

```bash
pip install -e ".[image]"
# or: pip install diffusers transformers accelerate

# Install PyTorch (CPU or CUDA):
pip install torch                      # CPU
# pip install torch --index-url https://download.pytorch.org/whl/cu118  # CUDA 11.8
```

---

## Running the Assistant

### Interactive multi-turn chat

```bash
python -m gamedesign_agent
# or
gamedesign-agent
```

Example session:

```
You: Generate a dungeon level
Assistant: Here is a generated dungeon level (seed 42):

###########################...
#....S...#,...,#....T...###...
...

You: Write dialogue for a hostile guard
Assistant: [GUARD - hostile]
  "Halt! State your business in Riverdale!"
  "One more step and I'll call the garrison."
```

Type `reset` or `clear` to start a fresh conversation. Type `quit` to exit.

### Non-interactive sub-commands

**Level generation:**

```bash
# ASCII map, seed 42, 60x40 grid, 12 rooms
python -m gamedesign_agent level --seed 42 --ascii

# JSON output
python -m gamedesign_agent level --seed 42 --json

# Custom size and room count
python -m gamedesign_agent level --width 80 --height 50 --rooms 18 --seed 7 --ascii
```

**NPC dialogue:**

```bash
python -m gamedesign_agent npc --type merchant --mood friendly --lines 3 --seed 1
python -m gamedesign_agent npc --type enemy --mood hostile --lines 2
```

**Art prompts:**

```bash
python -m gamedesign_agent art --scene dungeon --style fantasy --seed 42
python -m gamedesign_agent art --scene character --style pixel --description "elven archer"

# Submit to AUTOMATIC1111 (requires GAMEDESIGN_ART_BACKEND=auto1111)
GAMEDESIGN_ART_BACKEND=auto1111 python -m gamedesign_agent art --scene forest --generate-image --output out.png
```

**Single chat message:**

```bash
python -m gamedesign_agent chat "Give me game design advice"
python -m gamedesign_agent --backend ollama chat "What makes a great boss fight?"
```

---

## Configuration

All settings are controlled via **environment variables** (or an optional `.env` file
if `python-dotenv` is installed).

| Variable | Default | Description |
|----------|---------|-------------|
| `GAMEDESIGN_LLM_BACKEND` | `none` | `none` / `ollama` / `hf_api` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `mistral` | Ollama model name |
| `HF_API_TOKEN` | _(empty)_ | HuggingFace API token (free tier) |
| `HF_MODEL_ID` | `mistralai/Mistral-7B-Instruct-v0.1` | HF model for inference |
| `GAMEDESIGN_ART_BACKEND` | `none` | `none` / `auto1111` / `diffusers` |
| `AUTO1111_URL` | `http://127.0.0.1:7860` | AUTOMATIC1111 WebUI API URL |
| `DIFFUSERS_MODEL_ID` | `runwayml/stable-diffusion-v1-5` | diffusers model (local path or HF ID) |
| `GAMEDESIGN_CONTEXT_WINDOW` | `20` | Max conversation turns in context |
| `GAMEDESIGN_DEFAULT_SEED` | `42` | Default RNG seed |
| `GAMEDESIGN_OUTPUT_DIR` | `./output` | Directory for generated images |
| `GAMEDESIGN_ENV_FILE` | `.env` | Path to `.env` file |

Example `.env` file:

```dotenv
GAMEDESIGN_LLM_BACKEND=ollama
OLLAMA_MODEL=mistral
GAMEDESIGN_ART_BACKEND=auto1111
AUTO1111_URL=http://127.0.0.1:7860
GAMEDESIGN_DEFAULT_SEED=1234
```

---

## Connecting a Local LLM (Ollama)

[Ollama](https://ollama.com/) runs open-source LLMs locally for free.

```bash
# 1. Install Ollama (Linux/macOS):
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a model (e.g. Mistral 7B):
ollama pull mistral

# 3. Run Ollama server (usually started automatically):
ollama serve

# 4. Configure the assistant:
export GAMEDESIGN_LLM_BACKEND=ollama
export OLLAMA_MODEL=mistral

python -m gamedesign_agent
```

No API keys needed. Ollama is entirely free and runs on CPU or GPU.

---

## Connecting Local Stable Diffusion

### Option A – AUTOMATIC1111 WebUI API

[AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
is a free, open-source Stable Diffusion interface.

```bash
# 1. Clone and install AUTOMATIC1111:
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui
cd stable-diffusion-webui

# 2. Place your model weights in models/Stable-diffusion/
#    (e.g. download a free checkpoint from Civitai or HuggingFace)
#    NOTE: Do NOT commit model weights to this repository.

# 3. Start with the API enabled:
./webui.sh --api

# 4. Configure the assistant:
export GAMEDESIGN_ART_BACKEND=auto1111
export AUTO1111_URL=http://127.0.0.1:7860

# 5. Generate an image:
python -m gamedesign_agent art --scene dungeon --style fantasy --generate-image --output dungeon.png
```

### Option B – diffusers Pipeline

Use the [Hugging Face diffusers](https://github.com/huggingface/diffusers) library
to run Stable Diffusion locally (requires a GPU for reasonable speed).

```bash
# 1. Install dependencies:
pip install diffusers transformers accelerate torch

# 2. Configure (use a local path or a free HF model):
export GAMEDESIGN_ART_BACKEND=diffusers
export DIFFUSERS_MODEL_ID=runwayml/stable-diffusion-v1-5
# or point to a local directory:
# export DIFFUSERS_MODEL_ID=/path/to/your/model

# 3. Generate:
python -m gamedesign_agent art --scene character --style fantasy --generate-image
```

> **Important**: You must supply your own model weights.  
> Do NOT commit large model files (`.ckpt`, `.safetensors`, `*.bin`) to this repository.  
> The `.gitignore` file excludes common model file extensions.

---

## Module Reference

### `gamedesign_agent.GameDesignAgent`

```python
from gamedesign_agent import GameDesignAgent

agent = GameDesignAgent(llm_backend="none")  # fully offline

# Multi-turn chat
reply = agent.chat("Generate a dungeon level for my RPG")

# Direct utility calls
level  = agent.generate_level(seed=42, width=60, height=40, num_rooms=12)
lines  = agent.write_npc_dialogue(npc_type="merchant", mood="friendly", seed=1)
prompt = agent.create_art_prompt(scene_type="castle", style="fantasy", seed=5)

agent.reset()  # clear conversation history
```

### `gamedesign_agent.ProceduralLevelGenerator`

```python
from gamedesign_agent import ProceduralLevelGenerator

gen   = ProceduralLevelGenerator(width=60, height=40, num_rooms=12)
level = gen.generate(seed=42)

print(level.to_ascii())   # ASCII tile map
print(level.to_json())    # JSON with rooms, corridors, metadata
```

Tile symbols:

| Symbol | Meaning |
|--------|---------|
| `#` | Wall |
| `.` | Floor |
| `,` | Corridor |
| `S` | Start room centre |
| `E` | End room centre |
| `B` | Boss room centre |
| `T` | Treasure room centre |

### `gamedesign_agent.NPCDialogueWriter`

```python
from gamedesign_agent import NPCDialogueWriter

writer = NPCDialogueWriter()  # uses GAMEDESIGN_LLM_BACKEND env var
lines  = writer.generate(npc_type="guard", mood="hostile", num_lines=3, seed=42)
```

Supported NPC types: `merchant`, `guard`, `wizard`, `villager`, `enemy`, `quest_giver`  
Supported moods: `friendly`, `neutral`, `hostile`

### `gamedesign_agent.ArtPromptGenerator`

```python
from gamedesign_agent import ArtPromptGenerator

gen    = ArtPromptGenerator()
prompt = gen.generate_prompt(scene_type="dungeon", style="fantasy", seed=42)

print(prompt.positive)  # copy into Stable Diffusion
print(prompt.negative)

# Optionally generate the image (requires configured backend):
result = gen.generate_image(prompt, output_path="out.png")
```

### `gamedesign_agent.ConversationMemory`

```python
from gamedesign_agent import ConversationMemory

mem = ConversationMemory(system_prompt="You are a game design expert.", max_turns=20)
mem.add_message("user", "Hello!")
mem.add_message("assistant", "Hi! How can I help?")

window = mem.get_context_window()  # sliding window for LLM context
mem.clear()
```

---

## Running Tests

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests (no network or GPU required)
pytest

# With coverage
pytest --cov=gamedesign_agent --cov-report=term-missing
```

All tests are deterministic and run fully offline.

---

## Licensing and Model Weights

- **This module's source code** is released under the MIT License.
- **Python dependencies** (pytest, requests, diffusers, etc.) are all free/open-source.
- **Model weights** (Stable Diffusion, Ollama models) are **not included** in this repository.  
  You must download and manage your own model weights in accordance with their respective licenses:
  - Stable Diffusion v1.5: [CreativeML Open RAIL-M License](https://huggingface.co/runwayml/stable-diffusion-v1-5)
  - Mistral 7B: [Apache 2.0 License](https://huggingface.co/mistralai/Mistral-7B-v0.1)
- **No paid API keys are required** at any point. Every feature has a free/offline fallback.
