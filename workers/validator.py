"""
workers/validator.py – Flutter project validator with auto-fix pipeline.

Validation pipeline (when enabled):
  1. ``flutter pub get``
  2. ``dart format`` (auto-formats generated Dart files in-place)
  3. ``flutter analyze``

Auto-fix loop:
  - Applies deterministic ``PatchRule`` patches against the in-memory file dict.
  - Re-runs the full validation pipeline after each patch batch.
  - Stops after ``MAX_RETRIES`` iterations or when all rules have been applied.
  - Records each applied patch name in the returned log.

Optional smoke test (opt-in):
  - ``flutter test``  (if tests exist in the project directory)
  - or ``flutter build apk --debug``  (heavier build check)
"""

from __future__ import annotations

import logging
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Deterministic patch rules
# ---------------------------------------------------------------------------

@dataclass
class PatchRule:
    """A single deterministic patch rule for common Flutter/Flame generation issues."""

    name: str
    description: str
    # Returns True when this rule is applicable given the error log.
    matches: Callable[[str], bool]
    # Receives the current file dict and returns (patched_files, changed).
    apply: Callable[[Dict[str, str]], Tuple[Dict[str, str], bool]]


def _add_import_if_missing(
    files: Dict[str, str], dart_file: str, import_line: str
) -> Tuple[Dict[str, str], bool]:
    """Insert *import_line* near the top of *dart_file* if it is not already present."""
    content = files.get(dart_file, "")
    if import_line in content:
        return files, False
    lines = content.splitlines(keepends=True)
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("//"):
            insert_idx = i + 1
    new_lines = lines[:insert_idx] + [import_line + "\n"] + lines[insert_idx:]
    files = dict(files)
    files[dart_file] = "".join(new_lines)
    return files, True


def _remove_unused_import(
    files: Dict[str, str], error_log: str
) -> Tuple[Dict[str, str], bool]:
    """Remove the first unused import reported by dart analyzer."""
    pattern = re.compile(
        r"(lib/[^\s:]+\.dart):(\d+):\d+:.*[Uu]nused import",
        re.MULTILINE,
    )
    match = pattern.search(error_log)
    if not match:
        return files, False
    rel_path = match.group(1)
    line_no = int(match.group(2)) - 1  # 0-indexed
    content = files.get(rel_path, "")
    if not content:
        return files, False
    lines = content.splitlines(keepends=True)
    if 0 <= line_no < len(lines) and lines[line_no].strip().startswith("import "):
        lines.pop(line_no)
        files = dict(files)
        files[rel_path] = "".join(lines)
        return files, True
    return files, False


def _fix_pubspec_assets_indentation(
    files: Dict[str, str],
) -> Tuple[Dict[str, str], bool]:
    """
    Ensure the ``flutter: / assets:`` block in pubspec.yaml uses 2-space
    indentation for ``assets:`` and 4-space for each asset entry.
    """
    pubspec = files.get("pubspec.yaml", "")
    if not pubspec:
        return files, False

    lines = pubspec.splitlines(keepends=True)
    new_lines: List[str] = []
    changed = False
    in_flutter_section = False
    in_assets_section = False

    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if stripped.rstrip("\n") == "flutter:" and indent == 0:
            in_flutter_section = True
            in_assets_section = False
            new_lines.append(line)
            continue

        if in_flutter_section:
            if indent == 0 and stripped.strip() and not stripped.startswith("#"):
                in_flutter_section = False
                in_assets_section = False
            elif stripped.startswith("assets:") and indent < 4:
                in_assets_section = True
                correct = "  assets:\n"
                if line != correct:
                    line = correct
                    changed = True
                new_lines.append(line)
                continue
            elif in_assets_section and stripped.startswith("- "):
                correct_stripped = stripped.rstrip("\n")
                correct_line = "    " + correct_stripped + "\n"
                if line != correct_line:
                    line = correct_line
                    changed = True
                new_lines.append(line)
                continue

        new_lines.append(line)

    if not changed:
        return files, False
    files = dict(files)
    files["pubspec.yaml"] = "".join(new_lines)
    return files, True


def _add_analysis_options(files: Dict[str, str]) -> Tuple[Dict[str, str], bool]:
    """
    Add a minimal ``analysis_options.yaml`` if one is not present.
    Silences the most common lints that trip up generated code while keeping
    everything else enabled.
    """
    if "analysis_options.yaml" in files:
        return files, False
    files = dict(files)
    files["analysis_options.yaml"] = (
        "include: package:flutter_lints/flutter.yaml\n"
        "\n"
        "linter:\n"
        "  rules:\n"
        "    prefer_const_constructors: false\n"
        "    avoid_print: false\n"
    )
    return files, True


def _make_patch_rules() -> List[PatchRule]:
    """Return the ordered list of deterministic patch rules."""
    return [
        PatchRule(
            name="add_analysis_options",
            description="Add minimal analysis_options.yaml to suppress noisy lints",
            matches=lambda log: True,  # always try; apply() is idempotent
            apply=_add_analysis_options,
        ),
        PatchRule(
            name="remove_unused_import",
            description="Remove the first unused import reported by dart analyze",
            matches=lambda log: bool(re.search(r"[Uu]nused import", log)),
            # apply is a stub; the real logic is handled in apply_patches()
            apply=lambda files: (files, False),
        ),
        PatchRule(
            name="fix_pubspec_assets_indentation",
            description="Fix pubspec.yaml flutter/assets indentation",
            matches=lambda log: True,  # always try; apply() is idempotent
            apply=_fix_pubspec_assets_indentation,
        ),
        PatchRule(
            name="add_flame_import_to_main",
            description="Add missing flame/game.dart import to lib/main.dart",
            matches=lambda log: "flame" in log and "lib/main.dart" in log,
            apply=lambda files: _add_import_if_missing(
                files, "lib/main.dart", "import 'package:flame/game.dart';"
            ),
        ),
        PatchRule(
            name="add_flutter_material_import_to_main",
            description="Add missing flutter/material.dart import to lib/main.dart",
            matches=lambda log: "material" in log and "lib/main.dart" in log,
            apply=lambda files: _add_import_if_missing(
                files, "lib/main.dart", "import 'package:flutter/material.dart';"
            ),
        ),
        PatchRule(
            name="add_flutter_services_import_to_main",
            description="Add missing flutter/services.dart import to lib/main.dart",
            matches=lambda log: "SystemChrome" in log or "DeviceOrientation" in log,
            apply=lambda files: _add_import_if_missing(
                files, "lib/main.dart", "import 'package:flutter/services.dart';"
            ),
        ),
    ]


PATCH_RULES: List[PatchRule] = _make_patch_rules()


def apply_patches(
    files: Dict[str, str],
    error_log: str,
) -> Tuple[Dict[str, str], List[str]]:
    """
    Apply all matching deterministic patch rules to *files*.

    Args:
        files:     Current in-memory project file dict.
        error_log: Combined stdout/stderr from the last failed validation run.

    Returns:
        ``(patched_files, applied_rule_names)``
    """
    applied: List[str] = []
    for rule in PATCH_RULES:
        if not rule.matches(error_log):
            continue
        if rule.name == "remove_unused_import":
            # Special-case: needs the error_log passed in directly.
            new_files, changed = _remove_unused_import(files, error_log)
        else:
            new_files, changed = rule.apply(files)
        if changed:
            files = new_files
            applied.append(rule.name)
            logger.info("Patch applied: %s", rule.name)
    return files, applied


# ---------------------------------------------------------------------------
# ValidatorWorker
# ---------------------------------------------------------------------------

class ValidatorWorker:
    """Validates a generated Flutter project."""

    MAX_RETRIES = 3

    def __init__(self, project_dir: str, project_files: Dict[str, str]):
        self.project_dir = Path(project_dir)
        self.project_files = dict(project_files)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write_files(self) -> None:
        """Write ``project_files`` to ``project_dir`` on disk."""
        for rel_path, content in self.project_files.items():
            dest = self.project_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")

    def validate(
        self,
        run_format: bool = True,
        run_smoke_test: bool = False,
        smoke_test_mode: str = "test",
    ) -> Tuple[bool, str]:
        """
        Run the full validation pipeline.

        Steps:
            1. ``flutter pub get``
            2. ``dart format .``  (when *run_format* is ``True``)
            3. ``flutter analyze``
            4. Smoke test  (when *run_smoke_test* is ``True``)

        Args:
            run_format:      Run ``dart format .`` before ``flutter analyze``.
            run_smoke_test:  Run an optional smoke test after analysis.
            smoke_test_mode: ``"test"`` → ``flutter test``;
                             ``"build"`` → ``flutter build apk --debug``.

        Returns:
            ``(success, combined_log)`` tuple.
        """
        log_lines: List[str] = []

        # 1. flutter pub get
        result = self._run(["flutter", "pub", "get"])
        log_lines.append("$ flutter pub get")
        log_lines.append(result.stdout or "")
        log_lines.append(result.stderr or "")
        if result.returncode != 0:
            logger.warning("flutter pub get failed")
            return False, "\n".join(log_lines)

        # 2. dart format (auto-formats in place; idempotent)
        if run_format:
            result = self._run(["dart", "format", "."])
            log_lines.append("$ dart format .")
            log_lines.append(result.stdout or "")
            log_lines.append(result.stderr or "")
            if result.returncode != 0:
                logger.warning("dart format failed")
                return False, "\n".join(log_lines)

        # 3. flutter analyze
        result = self._run(["flutter", "analyze"])
        log_lines.append("$ flutter analyze")
        log_lines.append(result.stdout or "")
        log_lines.append(result.stderr or "")
        if result.returncode != 0:
            logger.warning("flutter analyze failed")
            return False, "\n".join(log_lines)

        # 4. Optional smoke test
        if run_smoke_test:
            smoke_cmd = (
                ["flutter", "build", "apk", "--debug"]
                if smoke_test_mode == "build"
                else ["flutter", "test"]
            )
            result = self._run(smoke_cmd)
            log_lines.append(f"$ {' '.join(smoke_cmd)}")
            log_lines.append(result.stdout or "")
            log_lines.append(result.stderr or "")
            if result.returncode != 0:
                logger.warning("Smoke test failed: %s", " ".join(smoke_cmd))
                return False, "\n".join(log_lines)

        return True, "\n".join(log_lines)

    def auto_fix(
        self,
        spec: Dict,
        error_logs: str,
        project_files: Dict[str, str],
        run_format: bool = True,
        run_smoke_test: bool = False,
        smoke_test_mode: str = "test",
    ) -> Tuple[Dict[str, str], List[str]]:
        """
        Apply deterministic patches then re-run validation, up to ``MAX_RETRIES``.

        Args:
            spec:             GameSpec dict (reserved for future LLM patches).
            error_logs:       Combined log from the last failed validation run.
            project_files:    Current in-memory project file dict.
            run_format:       Pass through to ``validate()``.
            run_smoke_test:   Pass through to ``validate()``.
            smoke_test_mode:  Pass through to ``validate()``.

        Returns:
            ``(final_project_files, all_applied_patch_names)``
        """
        files = dict(project_files)
        all_applied: List[str] = []
        current_log = error_logs

        for attempt in range(1, self.MAX_RETRIES + 1):
            logger.info("Auto-fix attempt %d/%d", attempt, self.MAX_RETRIES)

            files, applied = apply_patches(files, current_log)
            all_applied.extend(applied)

            if not applied:
                logger.info("No more patches applicable; stopping auto-fix.")
                break

            self.project_files = files
            self.write_files()
            success, current_log = self.validate(
                run_format=run_format,
                run_smoke_test=run_smoke_test,
                smoke_test_mode=smoke_test_mode,
            )
            if success:
                logger.info("Auto-fix succeeded on attempt %d.", attempt)
                break
        else:
            logger.warning("Auto-fix exhausted %d retries.", self.MAX_RETRIES)

        logger.info("Applied patches: %s", all_applied)
        return files, all_applied

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run(self, cmd: List[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd,
            cwd=self.project_dir,
            capture_output=True,
            text=True,
        )
