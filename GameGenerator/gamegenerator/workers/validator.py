"""
workers/validator.py – Flutter project validator.

Runs ``flutter pub get`` and ``flutter analyze`` inside the generated
project directory, and optionally ``flutter test``.

If ``auto_fix`` is enabled the Orchestrator calls ``auto_fix()`` which
retries validation up to ``MAX_RETRIES`` times (a hook for an LLM-assisted
patch loop in future iterations).
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


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

    def validate(self, run_tests: bool = False) -> Tuple[bool, str]:
        """
        Run ``flutter pub get`` then ``flutter analyze``.

        Args:
            run_tests: Also run ``flutter test`` when True.

        Returns:
            ``(success, combined_log)`` tuple.
        """
        log_lines: List[str] = []

        for cmd in [["flutter", "pub", "get"], ["flutter", "analyze"]]:
            result = self._run(cmd)
            log_lines.append(f"$ {' '.join(cmd)}")
            log_lines.append(result.stdout or "")
            log_lines.append(result.stderr or "")
            if result.returncode != 0:
                logger.warning("Command failed: %s", " ".join(cmd))
                return False, "\n".join(log_lines)

        if run_tests:
            result = self._run(["flutter", "test"])
            log_lines.append("$ flutter test")
            log_lines.append(result.stdout or "")
            if result.returncode != 0:
                return False, "\n".join(log_lines)

        return True, "\n".join(log_lines)

    def auto_fix(
        self,
        spec: Dict,
        error_logs: str,
        project_files: Dict[str, str],
    ) -> Dict[str, str]:
        """
        Attempt to fix validation errors and return (possibly patched) files.

        Currently retries validation up to ``MAX_RETRIES`` times to catch
        transient errors.  A future version can feed ``error_logs`` back to
        an LLM to generate targeted patches.
        """
        for attempt in range(1, self.MAX_RETRIES + 1):
            logger.info("Auto-fix attempt %d/%d", attempt, self.MAX_RETRIES)
            success, logs = self.validate()
            if success:
                logger.info("Auto-fix succeeded on attempt %d.", attempt)
                return project_files
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
