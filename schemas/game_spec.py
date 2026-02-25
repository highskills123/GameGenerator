"""
schemas/game_spec.py – Typed model for GameSpec.

Defines the canonical schema for a game specification used throughout
the generator pipeline.

Two representations are provided:

* ``GameSpec`` – a ``TypedDict`` (all fields optional) kept for backward
  compatibility and lightweight type-checking.
* ``GameSpecModel`` – a Pydantic v2 ``BaseModel`` used for boundary
  validation; the 7 core fields are required, everything else is optional.

Version constant
----------------
``GAME_SPEC_SCHEMA_VERSION`` tracks the schema revision.  Bump this when
making breaking changes to required fields or their types.

Usage
-----
    from schemas.game_spec import GameSpecModel, validate_game_spec

    model = validate_game_spec(spec_dict)   # raises ValueError if invalid
    serialisable = model.model_dump()        # includes schema_version
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from typing import TypedDict
except ImportError:  # Python < 3.8
    from typing_extensions import TypedDict  # type: ignore

from pydantic import BaseModel, field_validator

# ---------------------------------------------------------------------------
# Version constant
# ---------------------------------------------------------------------------

GAME_SPEC_SCHEMA_VERSION = "1.0"

# ---------------------------------------------------------------------------
# TypedDict  (kept for backward compatibility and lightweight type hints)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Pydantic model  (used for boundary validation)
# ---------------------------------------------------------------------------

_VALID_GENRES = {"top_down_shooter", "idle_rpg"}


class GameSpecModel(BaseModel):
    """Pydantic model for a validated GameSpec.

    The 7 core fields (``title``, ``genre``, ``mechanics``,
    ``required_assets``, ``screens``, ``controls``, ``progression``) are
    **required**.  All other fields are optional and default to ``None``
    unless otherwise noted.
    """

    schema_version: str = GAME_SPEC_SCHEMA_VERSION

    # --- Required core fields ---
    title: str
    genre: str
    mechanics: List[str]
    required_assets: List[str]
    screens: List[str]
    controls: Dict[str, Any]
    progression: Dict[str, Any]

    # --- Optional generation fields ---
    core_loop: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None
    performance_hints: Optional[List[str]] = None
    art_style: Optional[str] = None
    platform: Optional[str] = None
    scope: Optional[str] = None
    dimension: Optional[str] = None
    orientation: Optional[str] = None
    online: Optional[bool] = None
    assets_dir: Optional[str] = None

    @field_validator("genre")
    @classmethod
    def genre_must_be_known(cls, v: str) -> str:
        if v not in _VALID_GENRES:
            raise ValueError(
                f"'genre' must be one of {sorted(_VALID_GENRES)}, got '{v}'."
            )
        return v

    @field_validator("mechanics", "required_assets", "screens")
    @classmethod
    def list_must_not_be_empty(cls, v: List[str], info: Any) -> List[str]:
        if not v:
            raise ValueError(f"'{info.field_name}' must not be an empty list.")
        return v

    model_config = {"extra": "allow"}


# ---------------------------------------------------------------------------
# Public validator
# ---------------------------------------------------------------------------


def validate_game_spec(data: Dict[str, Any]) -> GameSpecModel:
    """Validate *data* against :class:`GameSpecModel`.

    Args:
        data: Raw game-spec dictionary (e.g. from heuristic or Ollama).

    Returns:
        A :class:`GameSpecModel` instance.

    Raises:
        ValueError: With a human-readable message listing every missing or
            invalid field.
    """
    from pydantic import ValidationError

    try:
        return GameSpecModel(**data)
    except ValidationError as exc:
        messages = []
        for err in exc.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            messages.append(f"  - {field}: {err['msg']}")
        raise ValueError(
            "GameSpec validation failed:\n" + "\n".join(messages)
        ) from exc
