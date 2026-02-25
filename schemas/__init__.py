"""
schemas – Typed models for the Aibase game generator pipeline.

Exports:
    GameSpec          – TypedDict for game design specification (backward compat)
    GameSpecModel     – Pydantic model for validated game design specification
    validate_game_spec – Validator function for GameSpec dicts
    GAME_SPEC_SCHEMA_VERSION – Current schema version string

    IdleRpgDesignDocModel     – Pydantic model for validated design documents
    validate_idle_rpg_design_doc – Validator function for design doc dicts
    IDLE_RPG_DESIGN_DOC_SCHEMA_VERSION – Current schema version string

    AssetSpec  – scanned/matched asset manifest
    BuildSpec  – build & output configuration
"""

from .game_spec import (  # noqa: F401
    GameSpec,
    EntitySpec,
    ControlsSpec,
    ProgressionSpec,
    GameSpecModel,
    validate_game_spec,
    GAME_SPEC_SCHEMA_VERSION,
)
from .idle_rpg_design_doc import (  # noqa: F401
    IdleRpgDesignDocModel,
    validate_idle_rpg_design_doc,
    IDLE_RPG_DESIGN_DOC_SCHEMA_VERSION,
)
from .asset_spec import AssetEntry, AssetSpec                                # noqa: F401
from .build_spec import BuildSpec                                            # noqa: F401
