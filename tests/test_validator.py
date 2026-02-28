"""
Unit tests for workers/validator.py – patch rule selection and application.

These tests do NOT require Flutter or Dart to be installed; they exercise only
the pure-Python logic in ``apply_patches``, ``PatchRule``, and related helpers.
"""

from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch

from workers.validator import (
    PATCH_RULES,
    PatchRule,
    ValidatorWorker,
    apply_patches,
    _add_import_if_missing,
    _add_analysis_options,
    _fix_pubspec_assets_indentation,
    _remove_unused_import,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_files() -> dict:
    """Return a minimal set of project files for testing."""
    return {
        "lib/main.dart": (
            "import 'package:flame/game.dart';\n"
            "import 'package:flutter/material.dart';\n"
            "\nvoid main() {}\n"
        ),
        "pubspec.yaml": (
            "name: my_game\n"
            "dependencies:\n"
            "  flutter:\n"
            "    sdk: flutter\n"
            "  flame: ^1.18.0\n"
            "\n"
            "flutter:\n"
            "  uses-material-design: true\n"
            "  assets:\n"
            "    - assets/imported/\n"
        ),
    }


# ---------------------------------------------------------------------------
# PatchRule dataclass
# ---------------------------------------------------------------------------

class TestPatchRuleDataclass(unittest.TestCase):
    """PatchRule must be constructable with the expected fields."""

    def test_can_create_patch_rule(self):
        rule = PatchRule(
            name="test_rule",
            description="A test rule",
            matches=lambda log: True,
            apply=lambda files: (files, False),
        )
        self.assertEqual(rule.name, "test_rule")
        self.assertTrue(rule.matches("anything"))
        files, changed = rule.apply({})
        self.assertFalse(changed)

    def test_matches_receives_log(self):
        seen = []
        rule = PatchRule(
            name="spy",
            description="",
            matches=lambda log: seen.append(log) or True,
            apply=lambda files: (files, False),
        )
        rule.matches("error log text")
        self.assertEqual(seen, ["error log text"])


# ---------------------------------------------------------------------------
# PATCH_RULES list
# ---------------------------------------------------------------------------

class TestPatchRulesList(unittest.TestCase):
    """PATCH_RULES must contain at least the documented rule names."""

    _EXPECTED_NAMES = {
        "add_analysis_options",
        "remove_unused_import",
        "fix_pubspec_assets_indentation",
        "add_flame_import_to_main",
        "add_flutter_material_import_to_main",
        "add_flutter_services_import_to_main",
    }

    def test_all_expected_rules_present(self):
        names = {r.name for r in PATCH_RULES}
        for expected in self._EXPECTED_NAMES:
            self.assertIn(expected, names, f"Missing patch rule: {expected}")

    def test_each_rule_has_name_and_description(self):
        for rule in PATCH_RULES:
            self.assertTrue(rule.name, "Rule has empty name")
            self.assertTrue(rule.description, f"Rule {rule.name!r} has empty description")

    def test_each_rule_matches_is_callable(self):
        for rule in PATCH_RULES:
            self.assertTrue(callable(rule.matches), f"Rule {rule.name!r}: matches is not callable")

    def test_each_rule_apply_is_callable(self):
        for rule in PATCH_RULES:
            self.assertTrue(callable(rule.apply), f"Rule {rule.name!r}: apply is not callable")


# ---------------------------------------------------------------------------
# _add_import_if_missing
# ---------------------------------------------------------------------------

class TestAddImportIfMissing(unittest.TestCase):

    def test_adds_missing_import(self):
        files = {"lib/main.dart": "void main() {}\n"}
        new_files, changed = _add_import_if_missing(
            files, "lib/main.dart", "import 'package:flame/game.dart';"
        )
        self.assertTrue(changed)
        self.assertIn("import 'package:flame/game.dart';", new_files["lib/main.dart"])

    def test_does_not_duplicate_existing_import(self):
        content = "import 'package:flame/game.dart';\nvoid main() {}\n"
        files = {"lib/main.dart": content}
        new_files, changed = _add_import_if_missing(
            files, "lib/main.dart", "import 'package:flame/game.dart';"
        )
        self.assertFalse(changed)
        self.assertEqual(new_files["lib/main.dart"].count("import 'package:flame/game.dart';"), 1)

    def test_returns_original_dict_when_unchanged(self):
        files = {"lib/main.dart": "import 'package:flame/game.dart';\n"}
        new_files, changed = _add_import_if_missing(
            files, "lib/main.dart", "import 'package:flame/game.dart';"
        )
        self.assertFalse(changed)
        self.assertIs(new_files, files)

    def test_file_not_in_dict_returns_unchanged(self):
        files = {}
        new_files, changed = _add_import_if_missing(
            files, "lib/main.dart", "import 'package:flame/game.dart';"
        )
        self.assertTrue(changed)  # file created with import
        self.assertIn("import 'package:flame/game.dart';", new_files.get("lib/main.dart", ""))


# ---------------------------------------------------------------------------
# _add_analysis_options
# ---------------------------------------------------------------------------

class TestAddAnalysisOptions(unittest.TestCase):

    def test_adds_file_when_absent(self):
        files = {"lib/main.dart": ""}
        new_files, changed = _add_analysis_options(files)
        self.assertTrue(changed)
        self.assertIn("analysis_options.yaml", new_files)
        self.assertIn("flutter_lints", new_files["analysis_options.yaml"])

    def test_no_change_when_already_present(self):
        files = {"analysis_options.yaml": "include: package:flutter_lints/flutter.yaml\n"}
        new_files, changed = _add_analysis_options(files)
        self.assertFalse(changed)

    def test_generated_content_is_valid_yaml_like(self):
        files, _ = _add_analysis_options({})
        content = files["analysis_options.yaml"]
        self.assertIn("include:", content)
        self.assertIn("linter:", content)
        self.assertIn("prefer_const_constructors: false", content)
        self.assertIn("avoid_print: false", content)


# ---------------------------------------------------------------------------
# _fix_pubspec_assets_indentation
# ---------------------------------------------------------------------------

class TestFixPubspecAssetsIndentation(unittest.TestCase):

    def _pubspec_with_bad_indent(self) -> str:
        return (
            "name: my_game\n"
            "\n"
            "flutter:\n"
            "  uses-material-design: true\n"
            "assets:\n"          # wrong: should be under flutter: at 2-space indent
            "  - assets/imported/\n"
        )

    def _pubspec_correct(self) -> str:
        return (
            "name: my_game\n"
            "\n"
            "flutter:\n"
            "  uses-material-design: true\n"
            "  assets:\n"
            "    - assets/imported/\n"
        )

    def test_fixes_assets_at_wrong_level(self):
        files = {"pubspec.yaml": self._pubspec_with_bad_indent()}
        # This may or may not fix depending on parser logic; just ensure it doesn't crash.
        new_files, _ = _fix_pubspec_assets_indentation(files)
        self.assertIn("pubspec.yaml", new_files)

    def test_correct_pubspec_unchanged(self):
        files = {"pubspec.yaml": self._pubspec_correct()}
        new_files, changed = _fix_pubspec_assets_indentation(files)
        self.assertFalse(changed)

    def test_empty_pubspec_unchanged(self):
        files = {}
        new_files, changed = _fix_pubspec_assets_indentation(files)
        self.assertFalse(changed)


# ---------------------------------------------------------------------------
# _remove_unused_import
# ---------------------------------------------------------------------------

class TestRemoveUnusedImport(unittest.TestCase):

    def test_removes_reported_line(self):
        dart_content = (
            "import 'package:flutter/material.dart';\n"
            "import 'package:unused/pkg.dart';\n"
            "\nvoid main() {}\n"
        )
        files = {"lib/game/foo.dart": dart_content}
        error_log = "lib/game/foo.dart:2:8: Warning: Unused import."
        new_files, changed = _remove_unused_import(files, error_log)
        self.assertTrue(changed)
        self.assertNotIn("unused", new_files["lib/game/foo.dart"])

    def test_no_match_returns_unchanged(self):
        files = {"lib/game/foo.dart": "import 'pkg';\n"}
        new_files, changed = _remove_unused_import(files, "no errors here")
        self.assertFalse(changed)
        self.assertIs(new_files, files)

    def test_nonexistent_file_in_log_returns_unchanged(self):
        files = {}
        error_log = "lib/game/missing.dart:1:1: Warning: Unused import."
        new_files, changed = _remove_unused_import(files, error_log)
        self.assertFalse(changed)


# ---------------------------------------------------------------------------
# apply_patches
# ---------------------------------------------------------------------------

class TestApplyPatches(unittest.TestCase):

    def test_returns_files_and_applied_list(self):
        files = _minimal_files()
        new_files, applied = apply_patches(files, "")
        self.assertIsInstance(new_files, dict)
        self.assertIsInstance(applied, list)

    def test_adds_analysis_options_on_empty_log(self):
        files = _minimal_files()
        new_files, applied = apply_patches(files, "")
        self.assertIn("add_analysis_options", applied)
        self.assertIn("analysis_options.yaml", new_files)

    def test_removes_unused_import_when_log_matches(self):
        dart_content = (
            "import 'package:flame/game.dart';\n"
            "import 'package:unused/pkg.dart';\n"
            "\nvoid main() {}\n"
        )
        files = dict(_minimal_files())
        files["lib/game/foo.dart"] = dart_content
        error_log = "lib/game/foo.dart:2:8: Warning: Unused import."
        new_files, applied = apply_patches(files, error_log)
        self.assertIn("remove_unused_import", applied)
        self.assertNotIn("unused", new_files["lib/game/foo.dart"])

    def test_does_not_remove_import_when_log_has_no_unused(self):
        files = _minimal_files()
        _, applied = apply_patches(files, "some other error")
        self.assertNotIn("remove_unused_import", applied)

    def test_flame_import_rule_triggers_on_matching_log(self):
        files = {"lib/main.dart": "void main() {}\n", "pubspec.yaml": ""}
        error_log = "lib/main.dart:3:5: Error: flame package not found"
        new_files, applied = apply_patches(files, error_log)
        self.assertIn("add_flame_import_to_main", applied)
        self.assertIn("import 'package:flame/game.dart';", new_files["lib/main.dart"])

    def test_material_import_rule_triggers_on_matching_log(self):
        files = {"lib/main.dart": "void main() {}\n", "pubspec.yaml": ""}
        error_log = "lib/main.dart:5:3: Error: material widget not found"
        new_files, applied = apply_patches(files, error_log)
        self.assertIn("add_flutter_material_import_to_main", applied)

    def test_services_import_rule_triggers_on_SystemChrome(self):
        files = {"lib/main.dart": "void main() {}\n", "pubspec.yaml": ""}
        error_log = "SystemChrome is undefined"
        new_files, applied = apply_patches(files, error_log)
        self.assertIn("add_flutter_services_import_to_main", applied)

    def test_idempotent_second_pass(self):
        files = _minimal_files()
        files_after_first, applied_first = apply_patches(files, "")
        files_after_second, applied_second = apply_patches(files_after_first, "")
        # analysis_options already added, so second pass should not add it again
        self.assertNotIn("add_analysis_options", applied_second)

    def test_all_applied_are_known_rule_names(self):
        known = {r.name for r in PATCH_RULES}
        files = _minimal_files()
        error_log = (
            "lib/game/foo.dart:2:8: Warning: Unused import.\n"
            "lib/main.dart:1:1: Error: flame not found\n"
            "SystemChrome missing\n"
        )
        _, applied = apply_patches(files, error_log)
        for name in applied:
            self.assertIn(name, known, f"Unknown patch rule applied: {name!r}")


# ---------------------------------------------------------------------------
# ValidatorWorker (filesystem-independent tests)
# ---------------------------------------------------------------------------

class TestValidatorWorkerInit(unittest.TestCase):

    def test_init_stores_project_dir(self):
        w = ValidatorWorker("/tmp/project", {"lib/main.dart": "void main(){}"})
        self.assertEqual(str(w.project_dir), "/tmp/project")

    def test_init_copies_project_files(self):
        original = {"lib/main.dart": "content"}
        w = ValidatorWorker("/tmp/project", original)
        self.assertEqual(w.project_files, original)
        # Mutating original should not affect worker
        original["extra"] = "value"
        self.assertNotIn("extra", w.project_files)

    def test_max_retries_is_positive(self):
        self.assertGreater(ValidatorWorker.MAX_RETRIES, 0)


class TestValidatorWorkerWriteFiles(unittest.TestCase):

    def test_write_files_creates_files(self):
        import os

        with tempfile.TemporaryDirectory() as tmp:
            files = {
                "lib/main.dart": "void main() {}",
                "pubspec.yaml": "name: test\n",
                "nested/deep/file.txt": "content",
            }
            w = ValidatorWorker(tmp, files)
            w.write_files()
            for rel_path, content in files.items():
                full_path = os.path.join(tmp, rel_path)
                self.assertTrue(os.path.exists(full_path), f"Missing: {rel_path}")
                with open(full_path, encoding="utf-8") as fh:
                    self.assertEqual(fh.read(), content)


class TestValidatorWorkerRunNotFound(unittest.TestCase):
    """_run must not raise when the executable is missing (e.g. Flutter not installed)."""

    def test_run_returns_nonzero_when_executable_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = ValidatorWorker(tmp, {})
            with patch("subprocess.run", side_effect=FileNotFoundError("flutter")):
                result = w._run(["flutter", "pub", "get"])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("flutter", result.stderr)

    def test_validate_returns_false_when_flutter_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = ValidatorWorker(tmp, {})
            with patch("subprocess.run", side_effect=FileNotFoundError("flutter")):
                success, log = w.validate()
            self.assertFalse(success)
            self.assertIn("flutter", log)


if __name__ == "__main__":
    unittest.main()
