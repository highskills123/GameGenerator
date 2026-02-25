"""
Unit tests for gamegenerator.asset_importer.AssetIndexer.
"""

import os
import tempfile
import unittest
from pathlib import Path

from gamegenerator.asset_importer import AssetIndexer, import_assets
from gamegenerator.spec import GameSpec


class TestAssetIndexerScan(unittest.TestCase):
    """Tests for AssetIndexer.scan()."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        asset_files = [
            "player.png",
            "enemy.png",
            "bullet.png",
            "background.jpg",
            "shoot.wav",
            "music.mp3",
        ]
        non_asset_files = [
            "README.txt",
            "level.tmx",
            "config.json",
        ]
        for fname in asset_files + non_asset_files:
            Path(self.tmp, fname).touch()

        sub = Path(self.tmp, "sprites")
        sub.mkdir()
        Path(sub, "icon.webp").touch()
        Path(sub, "notes.md").touch()

        self.expected_count = len(asset_files) + 1  # +1 for icon.webp

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_scan_returns_only_asset_files(self):
        indexer = AssetIndexer(self.tmp)
        found = indexer.scan()
        self.assertEqual(len(found), self.expected_count)
        self.assertTrue(all(isinstance(p, Path) for p in found))

    def test_scan_returns_empty_for_missing_dir(self):
        indexer = AssetIndexer("/nonexistent/path/that/does/not/exist")
        self.assertEqual(indexer.scan(), [])

    def test_scan_extensions_included(self):
        indexer = AssetIndexer(self.tmp)
        found = indexer.scan()
        suffixes = {p.suffix.lower() for p in found}
        from gamegenerator.asset_importer import ASSET_EXTENSIONS
        self.assertTrue(suffixes.issubset(ASSET_EXTENSIONS))

    def test_scan_non_asset_files_excluded(self):
        indexer = AssetIndexer(self.tmp)
        found = indexer.scan()
        names = [p.name for p in found]
        self.assertNotIn("README.txt", names)
        self.assertNotIn("level.tmx", names)
        self.assertNotIn("config.json", names)
        self.assertNotIn("notes.md", names)


class TestAssetIndexerMatch(unittest.TestCase):
    """Tests for AssetIndexer.match_assets()."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        files = [
            "player_idle.png",
            "enemy_walk.png",
            "bullet_small.png",
            "background_sky.jpg",
            "explosion_anim.png",
        ]
        for fname in files:
            Path(self.tmp, fname).touch()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_spec(self, roles):
        return {"title": "Test", "genre": "top_down_shooter", "required_assets": roles}

    def test_matches_player_role(self):
        spec = self._make_spec(["player"])
        indexer = AssetIndexer(self.tmp)
        matches = indexer.match_assets(spec)
        self.assertIn("player", matches)
        self.assertIn("player", matches["player"].stem.lower())

    def test_matches_enemy_role(self):
        spec = self._make_spec(["enemy"])
        indexer = AssetIndexer(self.tmp)
        matches = indexer.match_assets(spec)
        self.assertIn("enemy", matches)

    def test_missing_role_not_in_result(self):
        spec = self._make_spec(["unicorn_not_here"])
        indexer = AssetIndexer(self.tmp)
        matches = indexer.match_assets(spec)
        self.assertNotIn("unicorn_not_here", matches)

    def test_multiple_roles(self):
        spec = self._make_spec(["player", "enemy", "bullet"])
        indexer = AssetIndexer(self.tmp)
        matches = indexer.match_assets(spec)
        self.assertGreaterEqual(len(matches), 2)


class TestImportAssets(unittest.TestCase):
    """Tests for the import_assets convenience function."""

    def setUp(self):
        self.src = tempfile.mkdtemp()
        self.dest = tempfile.mkdtemp()
        Path(self.src, "player.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        Path(self.src, "enemy.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.src, ignore_errors=True)
        shutil.rmtree(self.dest, ignore_errors=True)

    def test_import_copies_files(self):
        spec: GameSpec = {
            "title": "Test Game",
            "genre": "top_down_shooter",
            "required_assets": ["player", "enemy"],
        }
        paths = import_assets(spec, self.src, self.dest)
        self.assertGreater(len(paths), 0)
        for rel in paths:
            self.assertTrue(Path(self.dest, rel).exists(), f"Missing: {rel}")

    def test_import_returns_relative_paths(self):
        spec: GameSpec = {
            "title": "Test Game",
            "genre": "top_down_shooter",
            "required_assets": ["player"],
        }
        paths = import_assets(spec, self.src, self.dest)
        for p in paths:
            self.assertFalse(os.path.isabs(p), f"Path should be relative: {p}")

    def test_import_empty_dir_returns_empty(self):
        empty_dir = tempfile.mkdtemp()
        spec: GameSpec = {"title": "T", "genre": "top_down_shooter", "required_assets": ["player"]}
        try:
            paths = import_assets(spec, empty_dir, self.dest)
            self.assertEqual(paths, [])
        finally:
            import shutil
            shutil.rmtree(empty_dir)


if __name__ == "__main__":
    unittest.main()
