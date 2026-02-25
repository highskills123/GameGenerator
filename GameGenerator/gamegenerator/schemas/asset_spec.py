"""
schemas/asset_spec.py – AssetSpec model.

Describes the result of scanning and matching a local assets directory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class AssetEntry:
    """A single matched asset file."""
    role: str           # logical role, e.g. "player", "enemy"
    source_path: str    # absolute path on the user's machine
    dest_path: str      # relative path inside the generated project
    asset_type: str     # "image" | "audio"


@dataclass
class AssetSpec:
    """Full asset manifest produced by the asset import worker."""
    assets_dir: str
    entries: List[AssetEntry] = field(default_factory=list)
    missing_roles: List[str] = field(default_factory=list)

    @property
    def relative_paths(self) -> List[str]:
        """Return dest_path for every entry (for pubspec.yaml assets section)."""
        return [e.dest_path for e in self.entries]
