"""
spec.py – GameSpec generation.

Converts a free-text user prompt into a structured GameSpec dictionary.
Uses a lightweight keyword heuristic to classify the genre, then populates
the spec.  If an Aibase ``AibaseTranslator`` instance is supplied, it tries
to use Ollama for a richer spec; on failure it falls back to the heuristic.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------
GameSpec = Dict[str, Any]

# ---------------------------------------------------------------------------
# Genre keyword map  (genre -> list of keywords found in the prompt)
# ---------------------------------------------------------------------------
_GENRE_KEYWORDS: Dict[str, List[str]] = {
    "top_down_shooter": [
        "shoot", "shooter", "bullet", "enemy", "space", "gun", "blast",
        "missile", "asteroid", "galaga", "shmup", "top down",
    ],
    "idle_rpg": [
        "idle", "rpg", "clicker", "upgrade", "hero", "quest", "adventure",
        "level up", "experience", "skill", "passive", "resource",
    ],
}

_DEFAULT_GENRE = "top_down_shooter"


def _classify_genre(prompt: str) -> str:
    """Return the best-matching genre name based on keyword scoring."""
    lower = prompt.lower()
    scores: Dict[str, int] = {}
    for genre, keywords in _GENRE_KEYWORDS.items():
        scores[genre] = sum(1 for kw in keywords if kw in lower)
    best = max(scores, key=lambda g: scores[g])
    if scores[best] == 0:
        logger.info("No genre keywords found; defaulting to '%s'.", _DEFAULT_GENRE)
        return _DEFAULT_GENRE
    return best


def _heuristic_spec(prompt: str) -> GameSpec:
    """Build a GameSpec dict using pure heuristics (no AI required)."""
    genre = _classify_genre(prompt)

    # Attempt to extract a title from the prompt (first quoted phrase or first N words)
    title_match = re.search(r'"([^"]+)"', prompt)
    if title_match:
        title = title_match.group(1)
    else:
        words = prompt.split()
        title = " ".join(words[:4]).title() if words else "My Game"

    spec: GameSpec = {
        "title": title,
        "genre": genre,
        "mechanics": _default_mechanics(genre),
        "required_assets": _default_assets(genre),
        "screens": ["main_menu", "game", "game_over"],
        "controls": _default_controls(genre),
        "progression": _default_progression(genre),
    }
    return spec


def _default_mechanics(genre: str) -> List[str]:
    return {
        "top_down_shooter": ["move", "shoot", "dodge", "collect_powerups"],
        "idle_rpg": ["auto_battle", "level_up", "upgrade_skills", "collect_resources"],
    }.get(genre, ["move"])


def _default_assets(genre: str) -> List[str]:
    return {
        "top_down_shooter": ["player", "enemy", "bullet", "background", "explosion"],
        "idle_rpg": ["hero", "enemy", "background", "icon", "skill_icon"],
    }.get(genre, ["player", "background"])


def _default_controls(genre: str) -> Dict[str, Any]:
    return {
        "top_down_shooter": {
            "keyboard": ["WASD", "arrows", "space"],
            "mobile": ["joystick", "fire_button"],
        },
        "idle_rpg": {
            "keyboard": ["click"],
            "mobile": ["tap"],
        },
    }.get(genre, {"keyboard": ["arrows"], "mobile": ["tap"]})


def _default_progression(genre: str) -> Dict[str, Any]:
    return {
        "top_down_shooter": {"scoring": "points", "levels": 5, "difficulty_ramp": "wave"},
        "idle_rpg": {"scoring": "experience", "levels": 20, "prestige": False},
    }.get(genre, {"scoring": "points", "levels": 5})


def _ollama_spec(prompt: str, translator: Any) -> Optional[GameSpec]:
    """
    Try to build a GameSpec via Ollama JSON generation.
    Returns None if Ollama is unavailable or produces invalid JSON.
    """
    system_prompt = (
        "You are a game design assistant. Given a game description, produce a JSON object "
        "with EXACTLY these keys: title, genre, mechanics (list), required_assets (list), "
        "screens (list), controls (object), progression (object). "
        "genre must be one of: top_down_shooter, idle_rpg. "
        "Output only valid JSON, no extra text."
    )
    user_prompt = f"Game description: {prompt}\n\nJSON:"
    try:
        raw = translator._generate_ollama(system_prompt, user_prompt)
        # strip potential code fences
        raw = re.sub(r"^```[^\n]*\n?", "", raw.strip())
        raw = re.sub(r"\n?```$", "", raw.strip())
        data = json.loads(raw)
        if not isinstance(data, dict) or "genre" not in data:
            return None
        if data.get("genre") not in _GENRE_KEYWORDS:
            data["genre"] = _classify_genre(prompt)
        return data
    except Exception as exc:
        logger.debug("Ollama spec generation failed (%s); falling back to heuristic.", exc)
        return None


def generate_spec(prompt: str, translator: Any = None) -> GameSpec:
    """
    Generate a GameSpec from a natural-language prompt.

    Args:
        prompt:     Free-text game description from the user.
        translator: Optional AibaseTranslator instance.  If provided and
                    Ollama is reachable, the spec is AI-generated; otherwise
                    a keyword-heuristic spec is produced.

    Returns:
        GameSpec dictionary.
    """
    if translator is not None:
        spec = _ollama_spec(prompt, translator)
        if spec is not None:
            logger.info("GameSpec produced via Ollama for genre '%s'.", spec.get("genre"))
            return spec
    spec = _heuristic_spec(prompt)
    logger.info("GameSpec produced via heuristic for genre '%s'.", spec.get("genre"))
    return spec
