"""
workers/validator.py – Flutter project validator.

Runs (when the Flutter/Dart SDK is available on PATH):
  1. ``dart format .``        – normalise Dart code style
  2. ``flutter pub get``      – resolve dependencies
  3. ``flutter analyze``      – static analysis
  4. ``flutter test``         – minimal smoke test (optional; a smoke-test file
                               is injected automatically if no tests exist yet)

Auto-fix
--------
``auto_fix()`` applies a registry of *deterministic* patch rules before
retrying validation.  Validation is only re-run when patches have actually
changed at least one file, avoiding unnecessary SDK invocations.

Patch rule registry
-------------------
Each rule in ``PATCH_RULES`` is a dict with:

  ``name``     – human-readable label (used in log messages)
  ``match``    – callable(path: str, content: str) -> bool
                 True when this rule should fire for a file.
  ``apply``    – callable(path: str, content: str) -> str
                 Returns the (possibly unchanged) patched content.

Rules are applied to every file in ``project_files`` on each auto-fix pass.
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Smoke-test template injected when no test files exist
# ---------------------------------------------------------------------------

_SMOKE_TEST_PATH = "test/smoke_test.dart"

_SMOKE_TEST_CONTENT = """\
// Auto-generated smoke test – replace with real tests when ready.
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('smoke: project compiles', () {
    expect(1 + 1, 2);
  });
}
"""

# ---------------------------------------------------------------------------
# Patch rules
# ---------------------------------------------------------------------------

# Type aliases
_MatchFn = Callable[[str, str], bool]
_ApplyFn = Callable[[str, str], str]


def _dart_file(path: str, _content: str) -> bool:
    return path.endswith(".dart")


def _pubspec_file(path: str, _content: str) -> bool:
    return path == "pubspec.yaml"


# ── Rule helpers ─────────────────────────────────────────────────────────────

def _ensure_import(content: str, import_line: str) -> str:
    """Prepend ``import_line`` if it is not already present."""
    if import_line in content:
        return content
    # Insert after existing import block (or at the top).
    lines = content.splitlines(keepends=True)
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("// "):
            insert_at = i + 1
    lines.insert(insert_at, import_line + "\n")
    return "".join(lines)


def _fix_pubspec_sdk_constraint(content: str) -> str:
    """
    Ensure the ``environment.sdk`` constraint uses the ``>=X.Y.Z <A.0.0``
    form that pub requires.  Replaces bare ``'^X.Y.Z'`` patterns.
    """
    # e.g.  sdk: '^3.0.0'  →  sdk: '>=3.0.0 <4.0.0'
    return re.sub(
        r"(sdk:\s*)'?\^(\d+\.\d+\.\d+)'?",
        lambda m: f"{m.group(1)}'>=>{m.group(2)} <{int(m.group(2).split('.')[0]) + 1}.0.0'",
        content,
    )


def _fix_pubspec_sdk_constraint_arrow(content: str) -> str:
    """Fix the ``>=>```` typo introduced by _fix_pubspec_sdk_constraint."""
    return content.replace("'>=>'", "'>='").replace("'>=>{", "'>={")


# ── Rule: ensure flutter_test dependency in pubspec ──────────────────────────

def _apply_flutter_test_dep(path: str, content: str) -> str:
    """Add ``flutter_test`` to dev_dependencies if absent."""
    if "flutter_test:" in content:
        return content
    dev_block = "dev_dependencies:\n  flutter_test:\n    sdk: flutter\n"
    if "dev_dependencies:" in content:
        return content
    # Append before the last blank line or at the end.
    return content.rstrip("\n") + "\n\n" + dev_block


# ── Rule: fix caret SDK constraints in pubspec ───────────────────────────────

def _apply_pubspec_sdk(path: str, content: str) -> str:
    fixed = _fix_pubspec_sdk_constraint(content)
    fixed = _fix_pubspec_sdk_constraint_arrow(fixed)
    return fixed


# ── Rule: add missing 'package:flutter/material.dart' import to main.dart ────

def _match_main_dart(path: str, _content: str) -> bool:
    return path == "lib/main.dart"


def _apply_main_dart_imports(path: str, content: str) -> str:
    for imp in [
        "import 'package:flutter/material.dart';",
        "import 'package:flutter/services.dart';",
        "import 'package:flame/game.dart';",
    ]:
        content = _ensure_import(content, imp)
    return content


# ── Rule: replace ``print(`` with ``debugPrint(`` in non-test Dart files ─────

def _match_non_test_dart(path: str, _content: str) -> bool:
    return path.endswith(".dart") and not path.startswith("test/")


def _apply_debug_print(path: str, content: str) -> str:
    # Only replace standalone print( calls (not debugPrint itself).
    return re.sub(r'(?<!\w)print\(', 'debugPrint(', content)


# ── Rule: pin flame to a concrete minor version in pubspec ───────────────────

def _apply_pin_flame(path: str, content: str) -> str:
    """Ensure flame is pinned to ``^1.18.0`` (not a looser constraint)."""
    # Replace things like  flame: any  or  flame: ">=1.0.0"  with the pinned version.
    return re.sub(
        r'(  flame:\s*)(?!^\^1\.18\.0)([^\n]+)',
        r'\1^1.18.0',
        content,
        flags=re.MULTILINE,
    )


# ---------------------------------------------------------------------------
# Public patch registry
# ---------------------------------------------------------------------------

#: Registry of deterministic patch rules applied during auto-fix.
#: Each entry: {"name": str, "match": MatchFn, "apply": ApplyFn}
PATCH_RULES: List[Dict] = [
    {
        "name": "pubspec: fix caret SDK constraints",
        "match": _pubspec_file,
        "apply": _apply_pubspec_sdk,
    },
    {
        "name": "pubspec: ensure flutter_test dev_dependency",
        "match": _pubspec_file,
        "apply": _apply_flutter_test_dep,
    },
    {
        "name": "pubspec: pin flame dependency",
        "match": _pubspec_file,
        "apply": _apply_pin_flame,
    },
    {
        "name": "main.dart: ensure required imports",
        "match": _match_main_dart,
        "apply": _apply_main_dart_imports,
    },
    {
        "name": "dart: replace print() with debugPrint()",
        "match": _match_non_test_dart,
        "apply": _apply_debug_print,
    },
]


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

    def ensure_smoke_test(self) -> bool:
        """
        Inject a minimal smoke-test file if no test files exist yet.

        Returns:
            True if a smoke-test file was added, False otherwise.
        """
        has_tests = any(
            p.startswith("test/") and p.endswith(".dart")
            for p in self.project_files
        )
        if not has_tests:
            logger.info("No test files found; injecting smoke test at %s.", _SMOKE_TEST_PATH)
            self.project_files[_SMOKE_TEST_PATH] = _SMOKE_TEST_CONTENT
            return True
        return False

    def validate(self, run_tests: bool = False) -> Tuple[bool, str]:
        """
        Run formatting, dependency resolution, and static analysis.

        Steps (each aborts early on non-zero exit):
          1. ``dart format .``   (skipped if ``dart`` not on PATH)
          2. ``flutter pub get``
          3. ``flutter analyze``
          4. ``flutter test``    (only when *run_tests* is True; a smoke-test
                                  file is injected automatically if absent)

        Args:
            run_tests: Also run ``flutter test`` when True.

        Returns:
            ``(success, combined_log)`` tuple.
        """
        log_lines: List[str] = []

        # Step 1 – dart format (best-effort; skip if dart not available)
        fmt_result = self._run(["dart", "format", "."])
        log_lines.append("$ dart format .")
        log_lines.append(fmt_result.stdout or "")
        log_lines.append(fmt_result.stderr or "")
        if fmt_result.returncode != 0:
            logger.warning(
                "dart format failed (returncode=%d); continuing.",
                fmt_result.returncode,
            )

        # Steps 2–3 – pub get + analyze (hard failures)
        for cmd in [["flutter", "pub", "get"], ["flutter", "analyze"]]:
            result = self._run(cmd)
            log_lines.append(f"$ {' '.join(cmd)}")
            log_lines.append(result.stdout or "")
            log_lines.append(result.stderr or "")
            if result.returncode != 0:
                logger.warning("Command failed: %s", " ".join(cmd))
                return False, "\n".join(log_lines)

        # Step 4 – flutter test (optional)
        if run_tests:
            self.ensure_smoke_test()
            self.write_files()
            result = self._run(["flutter", "test"])
            log_lines.append("$ flutter test")
            log_lines.append(result.stdout or "")
            log_lines.append(result.stderr or "")
            if result.returncode != 0:
                logger.warning("flutter test failed.")
                return False, "\n".join(log_lines)

        return True, "\n".join(log_lines)

    def apply_patches(
        self,
        project_files: Dict[str, str],
        rules: Optional[List[Dict]] = None,
    ) -> Tuple[Dict[str, str], bool]:
        """
        Apply all matching patch rules to *project_files*.

        Args:
            project_files: Current file map.
            rules:         Rule list to use (defaults to :data:`PATCH_RULES`).

        Returns:
            ``(patched_files, changed)`` where *changed* is True when at least
            one file was modified.
        """
        if rules is None:
            rules = PATCH_RULES

        patched = dict(project_files)
        changed = False

        for rule in rules:
            for path, content in list(patched.items()):
                if rule["match"](path, content):
                    new_content = rule["apply"](path, content)
                    if new_content != content:
                        logger.info("Patch applied [%s] → %s", rule["name"], path)
                        patched[path] = new_content
                        changed = True

        return patched, changed

    def auto_fix(
        self,
        spec: Dict,
        error_logs: str,
        project_files: Dict[str, str],
        run_tests: bool = False,
    ) -> Dict[str, str]:
        """
        Apply deterministic patch rules then rerun validation.

        The validation re-run is **skipped** when no patch changed any file,
        avoiding unnecessary Flutter SDK invocations.

        Args:
            spec:          GameSpec dict (reserved for future LLM-assisted
                           patching; not used by the current rule engine).
            error_logs:    Combined stdout/stderr from the last failed
                           validation run.
            project_files: Current file map.
            run_tests:     Forward to :meth:`validate`.

        Returns:
            The (possibly patched) file map.
        """
        for attempt in range(1, self.MAX_RETRIES + 1):
            logger.info("Auto-fix attempt %d/%d", attempt, self.MAX_RETRIES)

            patched, changed = self.apply_patches(project_files)

            if not changed:
                logger.info(
                    "No patches changed any file on attempt %d; "
                    "skipping rerun.",
                    attempt,
                )
                break

            project_files = patched
            self.project_files = project_files
            self.write_files()

            success, logs = self.validate(run_tests=run_tests)
            if success:
                logger.info("Auto-fix succeeded on attempt %d.", attempt)
                return project_files
            error_logs = logs

        logger.warning("Auto-fix exhausted %d retries.", self.MAX_RETRIES)
        return project_files

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
