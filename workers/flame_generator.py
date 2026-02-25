"""
workers/flame_generator.py – Flutter/Flame project generator worker.

Thin wrapper around ``game_generator.scaffolder`` for use inside the
Orchestrator pipeline.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from game_generator.spec import GameSpec


class FlameGeneratorWorker:
    """Produces a complete Flutter/Flame project file tree."""

    def generate(
        self,
        spec: GameSpec,
        imported_asset_paths: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Return ``{relative_path: file_content}`` for the full project.

        Args:
            spec:                 Fully-populated GameSpec.
            imported_asset_paths: Relative paths of assets already copied
                                  into the project directory.
        """
        from game_generator.scaffolder import scaffold_project

        return scaffold_project(spec, imported_asset_paths=imported_asset_paths or [])
