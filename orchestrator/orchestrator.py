"""
orchestrator/orchestrator.py – Main game generation orchestrator.

Coordinates the full pipeline:
  1. Constraint resolution
  2. GameSpec generation (heuristic or Ollama)
  3. Asset import (optional)
  4. Project scaffolding
  5. ZIP export
  6. Validation + auto-fix (optional)
"""

from __future__ import annotations

import logging
import tempfile
from typing import Any, Dict, Optional

from .constraint_resolver import ConstraintResolver

logger = logging.getLogger(__name__)


class Orchestrator:
    """End-to-end game generation coordinator."""

    def __init__(self, interactive: bool = False):
        self.interactive = interactive

    def run(
        self,
        prompt: str,
        output_zip: str,
        assets_dir: Optional[str] = None,
        platform: str = "android",
        scope: str = "prototype",
        auto_fix: bool = False,
        run_validation: bool = False,
        translator: Any = None,
        constraint_overrides: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Execute the full game generation pipeline.

        Args:
            prompt:               Natural-language game description.
            output_zip:           Destination ZIP file path.
            assets_dir:           Optional local assets folder.
            platform:             "android" or "android+ios".
            scope:                "prototype" or "vertical-slice".
            auto_fix:             Re-run validation after patching (implies
                                  run_validation=True).
            run_validation:       Run ``flutter pub get`` + ``flutter analyze``.
            translator:           Optional AibaseTranslator for Ollama spec.
            constraint_overrides: Extra constraints from the caller.
        """
        from game_generator.spec import generate_spec
        from game_generator.scaffolder import scaffold_project
        from game_generator.asset_importer import import_assets
        from game_generator.zip_exporter import export_to_zip
        from workers.validator import ValidatorWorker

        # ── 1. Resolve constraints ──────────────────────────────────────
        resolver = ConstraintResolver(interactive=self.interactive)
        constraints = resolver.resolve(
            {
                "platform": platform,
                "scope": scope,
                **(constraint_overrides or {}),
            }
        )
        logger.info("Constraints resolved: %s", constraints)

        # ── 2. Generate GameSpec ────────────────────────────────────────
        print("[1/4] Generating game spec …")
        spec = generate_spec(prompt, translator=translator)
        # Merge constraints into spec so downstream workers can read them.
        spec.update(
            {
                "art_style": constraints["art_style"],
                "platform": constraints["platform"],
                "scope": constraints["scope"],
                "dimension": constraints["dimension"],
                "online": constraints["online"],
            }
        )
        if assets_dir:
            spec["assets_dir"] = assets_dir
        print(f"      Title : {spec['title']}")
        print(f"      Genre : {spec['genre']}")

        # ── 3–5. Scaffold, import assets, export ZIP ────────────────────
        with tempfile.TemporaryDirectory(prefix="aibase_game_") as tmp_dir:

            # 3. Import assets
            imported_paths: list = []
            if assets_dir:
                print("[2/4] Importing assets …")
                imported_paths = import_assets(spec, assets_dir, tmp_dir)
                print(f"      Imported {len(imported_paths)} asset(s).")
            else:
                print(
                    "[2/4] No --assets-dir supplied; "
                    "project will reference assets/imported/ (populate manually)."
                )

            # 4. Scaffold
            print("[3/4] Scaffolding Flutter/Flame project …")
            project_files = scaffold_project(
                spec, imported_asset_paths=imported_paths
            )
            print(f"      Generated {len(project_files)} file(s).")

            # 4b. Optional validation + auto-fix
            if auto_fix or run_validation:
                print("[3b]  Running Flutter validation …")
                worker = ValidatorWorker(
                    project_dir=tmp_dir, project_files=project_files
                )
                worker.write_files()
                success, logs = worker.validate()
                if not success and auto_fix:
                    print("      Validation failed; attempting auto-fix …")
                    project_files = worker.auto_fix(spec, logs, project_files)
                    worker.project_files = project_files
                    worker.write_files()

            # 5. ZIP
            print("[4/4] Creating ZIP …")
            export_to_zip(project_files, tmp_dir, output_zip)

        print(f"\nDone!  ZIP: {output_zip}")
        print("  cd <unzipped-folder> && flutter pub get && flutter run\n")
