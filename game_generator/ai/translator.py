"""
game_generator/ai/translator.py – Lightweight Ollama translator for spec generation.

Provides OllamaTranslator, a minimal Ollama HTTP client used by the game
generator pipeline.  This removes the dependency on aibase.py from gamegen.py.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen2.5-coder:7b"
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2000


class OllamaTranslator:
    """Minimal Ollama HTTP client compatible with the spec.generate_spec() interface."""

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> None:
        self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
        self.temperature = temperature if temperature is not None else DEFAULT_TEMPERATURE
        self.max_tokens = max_tokens or DEFAULT_MAX_TOKENS
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_BASE_URL)
        self.timeout = timeout

    def _generate_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text via the Ollama /api/generate endpoint."""
        try:
            import requests
        except ImportError as exc:
            raise ImportError(
                "The 'requests' package is required. Install it with: pip install requests"
            ) from exc

        url = f"{self.ollama_base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if not resp.ok:
                if resp.status_code == 404:
                    raise RuntimeError(
                        f"Ollama returned 404 for POST {url}. "
                        f"The model '{self.model}' may not be pulled. "
                        f"Run: ollama pull {self.model}"
                    )
                resp.raise_for_status()
            return resp.json()["response"].strip()
        except RuntimeError:
            raise
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.ollama_base_url}. "
                "Make sure Ollama is running (https://ollama.com) and the model is pulled."
            )
        except Exception as exc:
            raise RuntimeError(f"Error during Ollama generation: {exc}") from exc
