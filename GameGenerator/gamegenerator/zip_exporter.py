"""
zip_exporter.py – Bundle a generated Flutter project into a ZIP archive.
"""

from __future__ import annotations

import logging
import os
import zipfile
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


def export_to_zip(
    project_files: Dict[str, str],
    project_dir: str,
    output_zip: str,
) -> None:
    """
    Write a ZIP archive containing:
      - all files in *project_files* (path -> content),
      - any binary assets already present in *project_dir*.

    Args:
        project_files: Dict mapping relative path -> text content for all
                       generated source/config files.
        project_dir:   Directory that may contain binary assets (e.g. the
                       ``assets/imported/`` tree) which were physically copied
                       there.  Pass an empty string to skip.
        output_zip:    Destination ``.zip`` file path (will be created /
                       overwritten).
    """
    output_path = Path(output_zip)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Write text source files
        for rel_path, content in sorted(project_files.items()):
            logger.debug("ZIP: adding text file '%s'.", rel_path)
            zf.writestr(rel_path, content)

        # Write binary assets from project_dir if it exists
        if project_dir:
            base = Path(project_dir)
            if base.exists():
                for root, _dirs, files in os.walk(base):
                    for fname in files:
                        abs_path = Path(root) / fname
                        rel = str(abs_path.relative_to(base)).replace(os.sep, "/")
                        # Don't duplicate files already added as text
                        if rel not in project_files:
                            logger.debug("ZIP: adding binary asset '%s'.", rel)
                            zf.write(abs_path, rel)

    logger.info("ZIP created: %s (%d bytes).", output_path, output_path.stat().st_size)
    print(f"✅  ZIP exported: {output_path}")
