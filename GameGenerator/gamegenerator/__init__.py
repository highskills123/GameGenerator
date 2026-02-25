"""
gamegenerator – Flutter/Flame game project generator.

Pipeline:
  1. spec.py           – Convert a user prompt into a GameSpec dict.
  2. genres/           – Genre plugin registry + per-genre code generators.
  3. scaffolder.py     – Produce the full multi-file Flutter/Flame project.
  4. asset_importer.py – Scan a local assets folder and copy relevant files.
  5. zip_exporter.py   – Bundle the project into a ZIP archive.
"""

from .spec import generate_spec, GameSpec          # noqa: F401
from .scaffolder import scaffold_project           # noqa: F401
from .asset_importer import AssetIndexer           # noqa: F401
from .zip_exporter import export_to_zip            # noqa: F401
from .genres import GENRE_REGISTRY, list_genres    # noqa: F401
