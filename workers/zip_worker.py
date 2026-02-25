"""
workers/zip_worker.py – ZIP export worker.

Bundles a generated Flutter project file tree into a ZIP archive.
"""

from __future__ import annotations

from typing import Dict


class ZipWorker:
    """Packages a Flutter project into a ``.zip`` archive."""

    def __init__(self, output_zip: str):
        self.output_zip = output_zip

    def run(self, project_files: Dict[str, str], project_dir: str) -> None:
        """
        Write the ZIP.

        Args:
            project_files: ``{relative_path: text_content}`` for all generated files.
            project_dir:   Directory that may contain binary assets to include.
        """
        from game_generator.zip_exporter import export_to_zip

        export_to_zip(project_files, project_dir, self.output_zip)
