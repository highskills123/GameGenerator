"""
Unit tests for gamegenerator.zip_exporter.export_to_zip.
"""

import os
import tempfile
import unittest
import zipfile
from pathlib import Path

from gamegenerator.zip_exporter import export_to_zip


class TestExportToZip(unittest.TestCase):
    """export_to_zip must produce a valid, complete ZIP archive."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.output_zip = os.path.join(self.tmp_dir, "test_output.zip")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _minimal_project(self):
        return {
            "pubspec.yaml": "name: test_game\n",
            "lib/main.dart": "void main() {}\n",
            "README.md": "# Test\n",
            "ASSETS_LICENSE.md": "No assets.\n",
            "CREDITS.md": "# Credits\n",
        }

    def test_creates_zip_file(self):
        export_to_zip(self._minimal_project(), "", self.output_zip)
        self.assertTrue(Path(self.output_zip).exists())

    def test_zip_is_valid(self):
        export_to_zip(self._minimal_project(), "", self.output_zip)
        self.assertTrue(zipfile.is_zipfile(self.output_zip))

    def test_zip_contains_all_text_files(self):
        project = self._minimal_project()
        export_to_zip(project, "", self.output_zip)
        with zipfile.ZipFile(self.output_zip, "r") as zf:
            names = set(zf.namelist())
        for rel_path in project:
            self.assertIn(rel_path, names)

    def test_zip_file_contents_match(self):
        project = self._minimal_project()
        export_to_zip(project, "", self.output_zip)
        with zipfile.ZipFile(self.output_zip, "r") as zf:
            pubspec = zf.read("pubspec.yaml").decode("utf-8")
        self.assertEqual(pubspec, project["pubspec.yaml"])

    def test_zip_includes_binary_assets_from_dir(self):
        assets_dir = Path(self.tmp_dir) / "proj" / "assets" / "imported"
        assets_dir.mkdir(parents=True)
        (assets_dir / "player.png").write_bytes(b"\x89PNG\r\n\x1a\n")

        export_to_zip(self._minimal_project(), str(Path(self.tmp_dir) / "proj"), self.output_zip)
        with zipfile.ZipFile(self.output_zip, "r") as zf:
            names = zf.namelist()
        self.assertTrue(any("player.png" in n for n in names))

    def test_zip_does_not_duplicate_text_files(self):
        proj_dir = Path(self.tmp_dir) / "proj"
        (proj_dir / "lib").mkdir(parents=True)
        (proj_dir / "lib" / "main.dart").write_text("void main() {}\n", encoding="utf-8")

        project = {"lib/main.dart": "void main() {}\n"}
        export_to_zip(project, str(proj_dir), self.output_zip)
        with zipfile.ZipFile(self.output_zip, "r") as zf:
            count = sum(1 for n in zf.namelist() if n == "lib/main.dart")
        self.assertEqual(count, 1)

    def test_output_directory_created_if_missing(self):
        nested_zip = os.path.join(self.tmp_dir, "a", "b", "game.zip")
        export_to_zip(self._minimal_project(), "", nested_zip)
        self.assertTrue(Path(nested_zip).exists())

    def test_empty_project_files_creates_empty_zip(self):
        export_to_zip({}, "", self.output_zip)
        self.assertTrue(zipfile.is_zipfile(self.output_zip))
        with zipfile.ZipFile(self.output_zip, "r") as zf:
            self.assertEqual(zf.namelist(), [])


if __name__ == "__main__":
    unittest.main()
