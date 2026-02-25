"""
asset_importer.py – Local asset indexer and heuristic mapper.

Scans a user-supplied folder for image and audio files, then uses a
lightweight filename-matching heuristic to select the assets most
relevant to a given GameSpec.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from .spec import GameSpec

logger = logging.getLogger(__name__)

# Extensions we care about
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg"}
ASSET_EXTENSIONS = IMAGE_EXTENSIONS | AUDIO_EXTENSIONS

# Heuristic tag weights: maps a "role" keyword to candidate filename fragments
# (longest match wins; case-insensitive)
_ROLE_TAGS: Dict[str, List[str]] = {
    "player":     ["player", "hero", "soldier", "character", "protagonist"],
    "enemy":      ["enemy", "orc", "monster", "foe", "villain", "mob"],
    "bullet":     ["bullet", "projectile", "shot", "laser", "arrow"],
    "background": ["background", "bg", "map", "tileset", "floor", "ground"],
    "explosion":  ["explosion", "blast", "boom", "effect", "fx"],
    "icon":       ["icon", "ui", "hud", "button"],
    "skill_icon": ["skill", "ability", "spell", "power"],
    "hero":       ["hero", "player", "soldier", "character"],
}


class AssetIndexer:
    """Scans a directory tree for usable asset files."""

    def __init__(self, assets_dir: str):
        self.assets_dir = Path(assets_dir)

    def scan(self) -> List[Path]:
        """
        Recursively scan ``assets_dir`` and return all asset file paths.

        Returns:
            List of ``pathlib.Path`` objects for every matching file.
        """
        if not self.assets_dir.exists():
            logger.warning("Assets directory not found: %s", self.assets_dir)
            return []

        found: List[Path] = []
        for root, _dirs, files in os.walk(self.assets_dir):
            for fname in files:
                p = Path(root) / fname
                if p.suffix.lower() in ASSET_EXTENSIONS:
                    found.append(p)

        logger.info("AssetIndexer: found %d asset files in '%s'.", len(found), self.assets_dir)
        return found

    def match_assets(
        self,
        spec: GameSpec,
        all_assets: Optional[List[Path]] = None,
    ) -> Dict[str, Path]:
        """
        Match spec ``required_assets`` roles to the best file in *all_assets*.

        Args:
            spec:       GameSpec with a ``required_assets`` list.
            all_assets: Pre-scanned list (calls ``scan()`` if None).

        Returns:
            Dict mapping role name -> best matching Path.
            Missing roles are omitted from the dict.
        """
        if all_assets is None:
            all_assets = self.scan()

        required: List[str] = spec.get("required_assets", [])
        matches: Dict[str, Path] = {}

        for role in required:
            best = _best_match(role, all_assets)
            if best is not None:
                matches[role] = best
                logger.debug("Role '%s' matched to '%s'.", role, best.name)
            else:
                logger.warning(
                    "No asset found for role '%s'; a placeholder will be used.", role
                )

        return matches


def import_assets(
    spec: GameSpec,
    assets_dir: str,
    dest_dir: str,
) -> List[str]:
    """
    Copy matched assets into *dest_dir/assets/imported/* and return a list
    of relative paths (suitable for pubspec.yaml).

    Args:
        spec:       GameSpec.
        assets_dir: Source directory on the user's PC.
        dest_dir:   Root of the generated Flutter project.

    Returns:
        List of relative asset paths, e.g. ``["assets/imported/player.png"]``.
    """
    indexer = AssetIndexer(assets_dir)
    all_assets = indexer.scan()
    matches = indexer.match_assets(spec, all_assets)

    out_dir = Path(dest_dir) / "assets" / "imported"
    out_dir.mkdir(parents=True, exist_ok=True)

    copied: List[str] = []
    for role, src_path in matches.items():
        dest_name = f"{role}{src_path.suffix.lower()}"
        dest_path = out_dir / dest_name
        shutil.copy2(src_path, dest_path)
        rel = str(dest_path.relative_to(dest_dir)).replace(os.sep, "/")
        copied.append(rel)
        logger.info("Copied asset '%s' -> '%s'.", src_path.name, rel)

    if not matches:
        logger.warning(
            "No assets were matched from '%s'. "
            "The project will use placeholder colours in code.",
            assets_dir,
        )

    return copied


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _best_match(role: str, candidates: List[Path]) -> Optional[Path]:
    """
    Return the candidate Path whose filename best matches *role*.

    Strategy:
    1. Score by: exact role name in stem, then tags from _ROLE_TAGS.
    2. Prefer image files over audio for non-audio roles.
    3. Only return a match if score > 0 (at least one substring hit).
    """
    tags = _ROLE_TAGS.get(role, [role])
    best_path: Optional[Path] = None
    best_score = 0  # require at least one positive signal

    for p in candidates:
        stem = p.stem.lower()
        ext = p.suffix.lower()
        score = 0

        # Exact role match
        if role in stem:
            score += 100

        # Tag matches
        for tag in tags:
            if tag in stem:
                score += 50
                break

        # Only prefer images over audio when there's already a semantic match
        if score > 0 and ext in IMAGE_EXTENSIONS:
            score += 10

        if score > best_score:
            best_score = score
            best_path = p

    return best_path
