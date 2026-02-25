"""
config.py – Configuration for the AI Design Assistant.

All settings are read from environment variables with safe defaults.
A config file (~/.gamedesign_agent.env or ./.env) is also supported via
python-dotenv (optional dependency – gracefully skipped when not installed).
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Optional: load a .env file if python-dotenv is installed
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv(dotenv_path=os.environ.get("GAMEDESIGN_ENV_FILE", ".env"), override=False)
except ImportError:
    pass


def _bool(val: str | None, default: bool = False) -> bool:
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# LLM backend – defaults to "none" (template-only mode, fully offline)
# Other supported values:
#   "ollama"   – local Ollama server (http://localhost:11434)
#   "hf_api"   – HuggingFace Inference API (free tier, requires HF_API_TOKEN)
# ---------------------------------------------------------------------------
LLM_BACKEND: str = os.environ.get("GAMEDESIGN_LLM_BACKEND", "none").lower()
OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "mistral")
HF_API_TOKEN: str = os.environ.get("HF_API_TOKEN", "")
HF_MODEL_ID: str = os.environ.get("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.1")

# ---------------------------------------------------------------------------
# Image / art-prompt backend
# "none"       – generate prompt text only (default, fully offline)
# "auto1111"   – call a running AUTOMATIC1111 stable-diffusion-webui API
# "diffusers"  – use local 🤗 diffusers pipeline (requires GPU + model weights)
# ---------------------------------------------------------------------------
ART_BACKEND: str = os.environ.get("GAMEDESIGN_ART_BACKEND", "none").lower()
AUTO1111_URL: str = os.environ.get("AUTO1111_URL", "http://127.0.0.1:7860")
DIFFUSERS_MODEL_ID: str = os.environ.get(
    "DIFFUSERS_MODEL_ID", "runwayml/stable-diffusion-v1-5"
)

# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------
# Maximum number of conversation turns kept in the context window
CONTEXT_WINDOW: int = int(os.environ.get("GAMEDESIGN_CONTEXT_WINDOW", "20"))
# Default seed for deterministic generation (override per-call)
DEFAULT_SEED: int = int(os.environ.get("GAMEDESIGN_DEFAULT_SEED", "42"))

# Output directory for generated images (when art backend != "none")
OUTPUT_DIR: str = os.environ.get("GAMEDESIGN_OUTPUT_DIR", "./output")
