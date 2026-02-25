"""
schemas/idle_rpg_design_doc.py – Pydantic model for IdleRpgDesignDoc.

Defines the schema for the design document produced by the AI design
assistant (``game_generator.ai.design_assistant``).

Version constant
----------------
``IDLE_RPG_DESIGN_DOC_SCHEMA_VERSION`` tracks the schema revision.  Bump
this when making breaking changes to required fields or their types.

Usage
-----
    from schemas.idle_rpg_design_doc import (
        IdleRpgDesignDocModel,
        validate_idle_rpg_design_doc,
    )

    model = validate_idle_rpg_design_doc(doc_dict)  # raises ValueError if invalid
    serialisable = model.model_dump()                # includes schema_version
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, field_validator

# ---------------------------------------------------------------------------
# Version constant
# ---------------------------------------------------------------------------

IDLE_RPG_DESIGN_DOC_SCHEMA_VERSION = "1.0"

# ---------------------------------------------------------------------------
# Pydantic model
# ---------------------------------------------------------------------------


class IdleRpgDesignDocModel(BaseModel):
    """Pydantic model for a validated Idle RPG design document.

    The 9 core fields (``world``, ``premise``, ``main_story_beats``,
    ``quests``, ``characters``, ``factions``, ``locations``, ``items``,
    ``enemies``) are **required**.  Optional rich-content fields default to
    ``None``.
    """

    schema_version: str = IDLE_RPG_DESIGN_DOC_SCHEMA_VERSION

    # --- Required core fields ---
    world: str
    premise: str
    main_story_beats: List[str]
    quests: List[Dict[str, Any]]
    characters: List[Dict[str, Any]]
    factions: List[Dict[str, Any]]
    locations: List[Dict[str, Any]]
    items: List[Dict[str, Any]]
    enemies: List[Dict[str, Any]]

    # --- Optional enrichment fields ---
    dialogue_samples: Optional[List[Dict[str, Any]]] = None
    upgrade_tree: Optional[Dict[str, Any]] = None
    idle_loops: Optional[List[Dict[str, Any]]] = None

    @field_validator("world", "premise")
    @classmethod
    def string_must_not_be_blank(cls, v: str, info: Any) -> str:
        if not v.strip():
            raise ValueError(f"'{info.field_name}' must not be blank.")
        return v

    @field_validator(
        "main_story_beats", "quests", "characters", "factions",
        "locations", "items", "enemies",
    )
    @classmethod
    def list_must_not_be_empty(cls, v: list, info: Any) -> list:
        if not v:
            raise ValueError(f"'{info.field_name}' must not be an empty list.")
        return v

    model_config = {"extra": "allow"}


# ---------------------------------------------------------------------------
# Public validator
# ---------------------------------------------------------------------------


def validate_idle_rpg_design_doc(data: Dict[str, Any]) -> IdleRpgDesignDocModel:
    """Validate *data* against :class:`IdleRpgDesignDocModel`.

    Args:
        data: Raw design-document dictionary (e.g. parsed from Ollama output).

    Returns:
        An :class:`IdleRpgDesignDocModel` instance.

    Raises:
        ValueError: With a human-readable message listing every missing or
            invalid field.
    """
    from pydantic import ValidationError

    try:
        return IdleRpgDesignDocModel(**data)
    except ValidationError as exc:
        messages = []
        for err in exc.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            messages.append(f"  - {field}: {err['msg']}")
        raise ValueError(
            "IdleRpgDesignDoc validation failed:\n" + "\n".join(messages)
        ) from exc
