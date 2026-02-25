"""
schemas/game_spec.py – Typed model for GameSpec.

Defines the canonical schema for a game specification used throughout
the generator pipeline.  All fields are optional (``total=False``) so
that partial specs from the heuristic path are still valid.
"""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from typing import TypedDict
except ImportError:  # Python < 3.8
    from typing_extensions import TypedDict  # type: ignore


class ControlsSpec(TypedDict, total=False):
    keyboard: List[str]
    mobile: List[str]


class ProgressionSpec(TypedDict, total=False):
    scoring: str
    levels: int
    difficulty_ramp: str
    prestige: bool


class EntitySpec(TypedDict, total=False):
    name: str
    role: str           # player | enemy | projectile | pickup
    attributes: Dict[str, Any]


class GameSpec(TypedDict, total=False):
    # Core identity
    title: str
    genre: str
    core_loop: str

    # Gameplay
    mechanics: List[str]
    entities: List[EntitySpec]
    controls: ControlsSpec
    screens: List[str]
    progression: ProgressionSpec
    required_assets: List[str]

    # Technical / generation hints
    performance_hints: List[str]
    art_style: str          # pixel-art | vector | hand-drawn
    platform: str           # android | android+ios
    scope: str              # prototype | vertical-slice
    dimension: str          # 2D  (Flame only supports 2D)
    orientation: str        # portrait | landscape
    online: bool
    assets_dir: str         # source directory used during generation
