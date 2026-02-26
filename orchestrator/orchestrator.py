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
from typing import Any, Callable, Dict, Optional

from .constraint_resolver import ConstraintResolver
from .run_tracker import RunTracker

logger = logging.getLogger(__name__)


def _enrich_spec_with_dialogue(
    spec: Dict[str, Any],
    design_doc: Dict[str, Any],
    emit: Callable,
) -> None:
    """
    Use GameDesignAgent to generate NPC dialogue for characters in the design doc
    and store it in spec['dialogue_data'] for downstream generators.
    Falls back silently when gamedesign_agent is unavailable.
    """
    characters = design_doc.get("characters", [])
    if not characters:
        return
    try:
        from gamedesign_agent.agent import GameDesignAgent
        agent = GameDesignAgent(llm_backend="none")
        dialogue: Dict[str, Any] = {}
        for char in characters[:5]:  # limit to 5 NPCs to keep generation fast
            name = char.get("name", "NPC")
            role = char.get("role", "villager").lower()
            # Map role to a recognised NPC type
            npc_type = "villager"
            for t in ("merchant", "guard", "wizard", "quest_giver", "enemy"):
                if t in role:
                    npc_type = t
                    break
            lines = agent.write_npc_dialogue(npc_type=npc_type, num_lines=3, seed=42)
            dialogue[name] = {"role": char.get("role", ""), "lines": lines}
        spec["dialogue_data"] = dialogue
        emit("dialogue", f"Generated dialogue for {len(dialogue)} character(s).", percent=37)
        logger.info("NPC dialogue generated for %d characters.", len(dialogue))
    except Exception as exc:
        logger.debug("GameDesignAgent dialogue enrichment skipped: %s", exc)


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
        idle_rpg: bool = False,
        seed: Optional[int] = None,
        run_tracker: Optional[RunTracker] = None,
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
            idle_rpg:             When True, run the one-shot Idle RPG generator
                                  (forces design_doc=True and genre=idle_rpg;
                                  falls back to template-based design doc when
                                  Ollama is unavailable).
            seed:                 Global RNG seed for deterministic output.
                                  Applied to the template fallback when Ollama
                                  is unavailable.
            run_tracker:          Optional :class:`RunTracker` for structured
                                  logging and progress events.
        """
        from game_generator.spec import generate_spec
        from game_generator.scaffolder import scaffold_project
        from game_generator.asset_importer import import_assets
        from game_generator.zip_exporter import export_to_zip
        from workers.validator import ValidatorWorker

        # --idle-rpg implies design_doc and forces idle_rpg genre
        if idle_rpg:
            design_doc = True
            if constraint_overrides is None:
                constraint_overrides = {}
            constraint_overrides["genre_override"] = "idle_rpg"

        # Convenience helper – emit event + print only when tracker is present
        def _emit(stage: str, message: str, percent: Optional[int] = None) -> None:
            if run_tracker is not None:
                run_tracker.emit(stage, message, percent=percent)

        # ── 1. Resolve constraints ──────────────────────────────────────
        _emit("constraints", "Resolving constraints …", percent=0)
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
        _emit("spec", "Generating game spec …", percent=10)
        spec = generate_spec(prompt, translator=translator)
        # Apply genre override from --idle-rpg
        genre_override = (constraint_overrides or {}).pop("genre_override", None)
        if genre_override:
            spec["genre"] = genre_override
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
        _emit("spec", f"Spec ready – title={spec['title']} genre={spec['genre']}", percent=20)

        # ── 2b. Optional design document generation ─────────────────────
        design_doc_content: Optional[str] = None
        resolved_design_doc_path: Optional[str] = None
        if design_doc:
            from game_generator.ai.design_assistant import (
                generate_idle_rpg_design,
                generate_idle_rpg_design_template,
                design_doc_to_markdown,
            )
            print("[1b]  Generating Idle RPG design document …")
            _emit("design_doc", "Generating Idle RPG design document …", percent=25)
            doc = None
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
                print("      Design document generated via Ollama.")
            except (RuntimeError, ImportError) as exc:
                if idle_rpg:
                    # Ollama unavailable – fall back to template
                    print(
                        f"      [WARNING] Ollama unavailable ({exc}); "
                        "using template-based design doc."
                    )
                    _emit("design_doc", "Ollama unavailable; using template fallback.", percent=28)
                    fallback_seed = seed if seed is not None else (ollama_seed if ollama_seed is not None else None)
                    doc = generate_idle_rpg_design_template(prompt, seed=fallback_seed)
                else:
                    import sys
                    print(f"[ERROR] Design document generation failed: {exc}")
                    if run_tracker is not None:
                        run_tracker.error(f"Design document generation failed: {exc}")
                    sys.exit(1)
            except ValueError as exc:
                import sys
                print(f"[ERROR] Design document generation failed: {exc}")
                if run_tracker is not None:
                    run_tracker.error(f"Design document generation failed: {exc}")
                sys.exit(1)

            if design_doc_format == "md":
                design_doc_content = design_doc_to_markdown(doc)
                resolved_design_doc_path = design_doc_path or "DESIGN.md"
            else:
                import json as _json
                design_doc_content = _json.dumps(doc, indent=2)
                resolved_design_doc_path = design_doc_path or "assets/design/design.json"
            # Make design doc data available to the genre generator (e.g. idle_rpg)
            spec["design_doc_data"] = doc
            print(f"      Design doc will be written to: {resolved_design_doc_path}")
            _emit("design_doc", f"Design doc ready → {resolved_design_doc_path}", percent=35)

            # ── 2c. Enrich spec with AI-generated NPC dialogue ───────────
            _enrich_spec_with_dialogue(spec, doc, _emit)

        # ── 3–5. Scaffold, import assets, export ZIP ────────────────────
        with tempfile.TemporaryDirectory(prefix="aibase_game_") as tmp_dir:

            # 3. Import assets
            imported_paths: list = []
            if assets_dir:
                print("[2/4] Importing assets …")
                _emit("assets", "Importing assets …", percent=40)
                imported_paths = import_assets(spec, assets_dir, tmp_dir)
                print(f"      Imported {len(imported_paths)} asset(s).")
                _emit("assets", f"Imported {len(imported_paths)} asset(s).", percent=50)
            else:
                print(
                    "[2/4] No --assets-dir supplied; "
                    "project will reference assets/imported/ (populate manually)."
                )
                _emit("assets", "No assets dir supplied; skipping import.", percent=50)

            # 4. Scaffold
            print("[3/4] Scaffolding Flutter/Flame project …")
            _emit("scaffold", "Scaffolding Flutter/Flame project …", percent=60)
            project_files = scaffold_project(
                spec, imported_asset_paths=imported_paths
            )
            print(f"      Generated {len(project_files)} file(s).")
            _emit("scaffold", f"Generated {len(project_files)} file(s).", percent=75)

            # 4b. Inject design document into project files
            if design_doc_content is not None and resolved_design_doc_path is not None:
                project_files[resolved_design_doc_path] = design_doc_content

            # 4c. Optional validation + auto-fix
            if auto_fix or run_validation:
                print("[3b]  Running Flutter validation …")
                _emit("validation", "Running Flutter validation …", percent=80)
                worker = ValidatorWorker(
                    project_dir=tmp_dir, project_files=project_files
                )
                worker.write_files()
                success, logs = worker.validate(run_smoke_test=smoke_test, smoke_test_mode=smoke_test_mode)
                if not success and auto_fix:
                    print("      Validation failed; attempting auto-fix …")
                    _emit("validation", "Validation failed; attempting auto-fix …", percent=85)
                    project_files = worker.auto_fix(spec, logs, project_files)
                    worker.project_files = project_files
                    worker.write_files()
                _emit("validation", "Validation complete.", percent=90)

            # 5. ZIP
            print("[4/4] Creating ZIP …")
            _emit("zip", "Creating ZIP archive …", percent=95)
            export_to_zip(project_files, tmp_dir, output_zip)
            _emit("zip", f"ZIP created → {output_zip}", percent=100)

        print(f"\nDone!  ZIP: {output_zip}")
        print("  cd <unzipped-folder> && flutter pub get && flutter run\n")
