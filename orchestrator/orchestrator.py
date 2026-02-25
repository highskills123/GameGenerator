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
        smoke_test: bool = False,
        smoke_test_mode: str = "test",
        translator: Any = None,
        constraint_overrides: Optional[Dict[str, Any]] = None,
        design_doc: bool = False,
        design_doc_format: str = "json",
        design_doc_path: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
        ollama_model: Optional[str] = None,
        ollama_temperature: Optional[float] = None,
        ollama_max_tokens: Optional[int] = None,
        ollama_timeout: Optional[int] = None,
        ollama_seed: Optional[int] = None,
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
            smoke_test:           Run an optional smoke test after analysis
                                  (``flutter test`` or ``flutter build apk --debug``).
                                  Opt-in; not enabled by default.
            smoke_test_mode:      ``"test"`` (default) or ``"build"``.
            translator:           Optional AibaseTranslator for Ollama spec.
            constraint_overrides: Extra constraints from the caller.
            design_doc:           When True, generate an Idle RPG design document.
            design_doc_format:    "json" or "md" (default "json").
            design_doc_path:      Path inside the project for the design doc.
            ollama_base_url:      Ollama server base URL.
            ollama_model:         Ollama model name for design doc generation.
            ollama_temperature:   Sampling temperature.
            ollama_max_tokens:    Max tokens to generate.
            ollama_timeout:       HTTP request timeout in seconds.
            ollama_seed:          Random seed for reproducibility.
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

        # ── 2b. Optional design document generation ─────────────────────
        design_doc_content: Optional[str] = None
        resolved_design_doc_path: Optional[str] = None
        if design_doc:
            from game_generator.ai.design_assistant import (
                generate_idle_rpg_design,
                design_doc_to_markdown,
            )
            print("[1b]  Generating Idle RPG design document via Ollama …")
            try:
                doc = generate_idle_rpg_design(
                    prompt,
                    model=ollama_model,
                    base_url=ollama_base_url,
                    temperature=ollama_temperature,
                    max_tokens=ollama_max_tokens,
                    timeout=ollama_timeout,
                    seed=ollama_seed,
                )
            except (RuntimeError, ValueError) as exc:
                import sys
                print(f"[ERROR] Design document generation failed: {exc}")
                sys.exit(1)

            if design_doc_format == "md":
                design_doc_content = design_doc_to_markdown(doc)
                resolved_design_doc_path = design_doc_path or "DESIGN.md"
            else:
                import json as _json
                design_doc_content = _json.dumps(doc, indent=2)
                resolved_design_doc_path = design_doc_path or "assets/design/design.json"
            print(f"      Design doc will be written to: {resolved_design_doc_path}")

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

            # 4b. Inject design document into project files
            if design_doc_content is not None and resolved_design_doc_path is not None:
                project_files[resolved_design_doc_path] = design_doc_content

            # 4c. Optional validation + auto-fix
            if auto_fix or run_validation:
                print("[3b]  Running Flutter validation …")
                worker = ValidatorWorker(
                    project_dir=tmp_dir, project_files=project_files
                )
                worker.write_files()
                success, logs = worker.validate(run_smoke_test=smoke_test, smoke_test_mode=smoke_test_mode)
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
