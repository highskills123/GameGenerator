# GameGenerator

A collection of game generation tools and AI-assisted design utilities.

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
```

For full documentation see [docs/AI_DESIGN_ASSISTANT.md](docs/AI_DESIGN_ASSISTANT.md).
