"""
workers/asset_worker.py – Asset import worker.

Scans a local directory, matches assets to GameSpec roles, and copies
them into the generated project directory.
"""

from __future__ import annotations

from typing import List

from game_generator.spec import GameSpec


class AssetWorker:
    """Imports assets from a local directory into a project directory."""

    def __init__(self, assets_dir: str, dest_dir: str):
        self.assets_dir = assets_dir
        self.dest_dir = dest_dir

    def run(self, spec: GameSpec) -> List[str]:
        """
        Import assets and return a list of relative dest paths.

        Args:
            spec: GameSpec (uses ``spec["required_assets"]`` for role matching).

        Returns:
            List of relative paths like ``["assets/imported/player.png", ...]``.
        """
        from game_generator.asset_importer import import_assets

        return import_assets(spec, self.assets_dir, self.dest_dir)
