"""
genres/__init__.py – Genre plugin registry.

Each genre plugin module must expose a single function:

    generate_files(spec: GameSpec) -> Dict[str, str]

Keys are relative file paths within the project (e.g. ``lib/game/player.dart``),
values are the full file contents.
"""

from __future__ import annotations

from typing import Callable, Dict

from ..spec import GameSpec

from . import top_down_shooter as _shooter
from . import idle_rpg as _idle_rpg

# Registry maps genre id -> callable(spec) -> {path: content}
GENRE_REGISTRY: Dict[str, Callable[[GameSpec], Dict[str, str]]] = {
    "top_down_shooter": _shooter.generate_files,
    "idle_rpg": _idle_rpg.generate_files,
}


def list_genres() -> list:
    """Return the list of supported genre ids."""
    return list(GENRE_REGISTRY.keys())


def get_genre_plugin(genre: str) -> Callable[[GameSpec], Dict[str, str]]:
    """
    Return the file-generator callable for *genre*.

    Raises:
        ValueError: if the genre is not registered.
    """
    if genre not in GENRE_REGISTRY:
        raise ValueError(
            f"Unknown genre '{genre}'. Supported: {', '.join(GENRE_REGISTRY)}"
        )
    return GENRE_REGISTRY[genre]
