"""
schemas – Typed models for the Aibase game generator pipeline.

Exports:
    GameSpec   – full game design specification
    AssetSpec  – scanned/matched asset manifest
    BuildSpec  – build & output configuration
"""

from .game_spec import GameSpec, EntitySpec, ControlsSpec, ProgressionSpec  # noqa: F401
from .asset_spec import AssetEntry, AssetSpec                                # noqa: F401
from .build_spec import BuildSpec                                            # noqa: F401
