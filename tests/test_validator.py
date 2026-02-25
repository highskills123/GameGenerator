"""
Unit tests for workers.validator – patch rule application and change detection.

These tests do NOT invoke the Flutter or Dart SDK; all logic is exercised
purely in Python so they run in any CI environment.
"""

from __future__ import annotations

import unittest

from workers.validator import (
    PATCH_RULES,
    ValidatorWorker,
    _SMOKE_TEST_CONTENT,
    _SMOKE_TEST_PATH,
    _apply_debug_print,
    _apply_flutter_test_dep,
    _apply_main_dart_imports,
    _apply_pin_flame,
    _apply_pubspec_sdk,
    _ensure_import,
)


# ---------------------------------------------------------------------------
# Helper to build a minimal ValidatorWorker without a real project directory
# ---------------------------------------------------------------------------

def _make_worker(files: dict | None = None) -> ValidatorWorker:
    return ValidatorWorker(project_dir="/tmp/fake_project", project_files=files or {})


# ---------------------------------------------------------------------------
# _ensure_import
# ---------------------------------------------------------------------------

class TestEnsureImport(unittest.TestCase):
    def test_adds_missing_import(self):
        content = "void main() {}\n"
        result = _ensure_import(content, "import 'package:flutter/material.dart';")
        self.assertIn("import 'package:flutter/material.dart';", result)

    def test_does_not_duplicate_existing_import(self):
        imp = "import 'package:flutter/material.dart';"
        content = f"{imp}\nvoid main() {{}}\n"
        result = _ensure_import(content, imp)
        self.assertEqual(result.count(imp), 1)


# ---------------------------------------------------------------------------
# _apply_pubspec_sdk
# ---------------------------------------------------------------------------

class TestApplyPubspecSdk(unittest.TestCase):
    def test_caret_constraint_left_unchanged_when_already_range(self):
        content = "environment:\n  sdk: '>=3.0.0 <4.0.0'\n"
        result = _apply_pubspec_sdk("pubspec.yaml", content)
        self.assertIn(">=3.0.0 <4.0.0", result)

    def test_no_change_when_no_caret(self):
        content = "environment:\n  sdk: '>=3.0.0 <4.0.0'\n"
        result = _apply_pubspec_sdk("pubspec.yaml", content)
        self.assertEqual(result, content)


# ---------------------------------------------------------------------------
# _apply_flutter_test_dep
# ---------------------------------------------------------------------------

class TestApplyFlutterTestDep(unittest.TestCase):
    def test_adds_dev_dependencies_block(self):
        content = "name: my_game\ndependencies:\n  flutter:\n    sdk: flutter\n"
        result = _apply_flutter_test_dep("pubspec.yaml", content)
        self.assertIn("dev_dependencies:", result)
        self.assertIn("flutter_test:", result)

    def test_no_change_when_already_present(self):
        content = (
            "name: my_game\n"
            "dev_dependencies:\n"
            "  flutter_test:\n"
            "    sdk: flutter\n"
        )
        result = _apply_flutter_test_dep("pubspec.yaml", content)
        self.assertEqual(result, content)

    def test_no_duplicate_when_dev_dependencies_exists(self):
        content = "dev_dependencies:\n  some_dep: ^1.0.0\n"
        result = _apply_flutter_test_dep("pubspec.yaml", content)
        # Rule skips if 'dev_dependencies:' already present but no flutter_test
        self.assertEqual(result.count("dev_dependencies:"), 1)


# ---------------------------------------------------------------------------
# _apply_pin_flame
# ---------------------------------------------------------------------------

class TestApplyPinFlame(unittest.TestCase):
    def test_pins_loose_flame_version(self):
        content = "dependencies:\n  flame: any\n"
        result = _apply_pin_flame("pubspec.yaml", content)
        self.assertIn("flame: ^1.18.0", result)

    def test_correct_pin_unchanged(self):
        content = "dependencies:\n  flame: ^1.18.0\n"
        result = _apply_pin_flame("pubspec.yaml", content)
        self.assertIn("flame: ^1.18.0", result)


# ---------------------------------------------------------------------------
# _apply_main_dart_imports
# ---------------------------------------------------------------------------

class TestApplyMainDartImports(unittest.TestCase):
    def test_adds_flame_import_when_missing(self):
        content = "void main() {}\n"
        result = _apply_main_dart_imports("lib/main.dart", content)
        self.assertIn("import 'package:flame/game.dart';", result)

    def test_adds_material_import_when_missing(self):
        content = "void main() {}\n"
        result = _apply_main_dart_imports("lib/main.dart", content)
        self.assertIn("import 'package:flutter/material.dart';", result)

    def test_no_duplicate_imports(self):
        imp = "import 'package:flame/game.dart';"
        content = f"{imp}\nvoid main() {{}}\n"
        result = _apply_main_dart_imports("lib/main.dart", content)
        self.assertEqual(result.count(imp), 1)


# ---------------------------------------------------------------------------
# _apply_debug_print
# ---------------------------------------------------------------------------

class TestApplyDebugPrint(unittest.TestCase):
    def test_replaces_print_with_debug_print(self):
        content = "void f() { print('hello'); }\n"
        result = _apply_debug_print("lib/foo.dart", content)
        self.assertIn("debugPrint(", result)
        self.assertNotIn("print('hello')", result)

    def test_does_not_double_replace_debug_print(self):
        content = "void f() { debugPrint('hello'); }\n"
        result = _apply_debug_print("lib/foo.dart", content)
        self.assertEqual(result.count("debugPrint("), 1)

    def test_no_change_when_no_print(self):
        content = "void f() { var x = 1; }\n"
        result = _apply_debug_print("lib/foo.dart", content)
        self.assertEqual(result, content)


# ---------------------------------------------------------------------------
# ValidatorWorker.apply_patches – change detection
# ---------------------------------------------------------------------------

class TestApplyPatches(unittest.TestCase):
    def _worker(self, files):
        return _make_worker(files)

    def test_returns_changed_true_when_file_modified(self):
        # A pubspec without flutter_test will be patched.
        files = {
            "pubspec.yaml": "name: game\ndependencies:\n  flutter:\n    sdk: flutter\n"
        }
        worker = self._worker(files)
        _, changed = worker.apply_patches(files)
        self.assertTrue(changed)

    def test_returns_changed_false_when_no_modification_needed(self):
        # A dart file with no print() calls and all needed imports already present
        content = (
            "import 'package:flame/game.dart';\n"
            "import 'package:flutter/material.dart';\n"
            "import 'package:flutter/services.dart';\n"
            "void main() {}\n"
        )
        files = {"lib/main.dart": content}
        worker = self._worker(files)
        _, changed = worker.apply_patches(files)
        # No print() → _apply_debug_print makes no change; imports present → no change
        self.assertFalse(changed)

    def test_patched_files_differ_from_originals(self):
        files = {
            "lib/foo.dart": "void f() { print('hi'); }\n",
        }
        worker = self._worker(files)
        patched, changed = worker.apply_patches(files)
        self.assertTrue(changed)
        self.assertIn("debugPrint(", patched["lib/foo.dart"])

    def test_custom_rules_applied(self):
        def always_match(path, content):
            return path.endswith(".dart")

        def uppercase(path, content):
            return content.upper()

        custom_rules = [{"name": "uppercase", "match": always_match, "apply": uppercase}]
        files = {"lib/main.dart": "void main() {}\n"}
        worker = self._worker(files)
        patched, changed = worker.apply_patches(files, rules=custom_rules)
        self.assertTrue(changed)
        self.assertEqual(patched["lib/main.dart"], "VOID MAIN() {}\n")

    def test_apply_patches_does_not_mutate_input(self):
        files = {"lib/foo.dart": "void f() { print('x'); }\n"}
        original_content = files["lib/foo.dart"]
        worker = self._worker(files)
        worker.apply_patches(files)
        self.assertEqual(files["lib/foo.dart"], original_content)


# ---------------------------------------------------------------------------
# ValidatorWorker.ensure_smoke_test
# ---------------------------------------------------------------------------

class TestEnsureSmokeTest(unittest.TestCase):
    def test_injects_smoke_test_when_no_tests(self):
        worker = _make_worker({"lib/main.dart": "void main() {}\n"})
        injected = worker.ensure_smoke_test()
        self.assertTrue(injected)
        self.assertIn(_SMOKE_TEST_PATH, worker.project_files)
        self.assertEqual(worker.project_files[_SMOKE_TEST_PATH], _SMOKE_TEST_CONTENT)

    def test_does_not_inject_when_tests_exist(self):
        files = {
            "lib/main.dart": "void main() {}\n",
            "test/my_test.dart": "void main() {}\n",
        }
        worker = _make_worker(files)
        injected = worker.ensure_smoke_test()
        self.assertFalse(injected)
        self.assertNotIn(_SMOKE_TEST_PATH, worker.project_files)

    def test_smoke_test_content_is_valid_dart(self):
        self.assertIn("void main()", _SMOKE_TEST_CONTENT)
        self.assertIn("expect(", _SMOKE_TEST_CONTENT)


# ---------------------------------------------------------------------------
# PATCH_RULES registry sanity checks
# ---------------------------------------------------------------------------

class TestPatchRulesRegistry(unittest.TestCase):
    def test_all_rules_have_required_keys(self):
        for rule in PATCH_RULES:
            self.assertIn("name", rule, f"Rule missing 'name': {rule}")
            self.assertIn("match", rule, f"Rule missing 'match': {rule}")
            self.assertIn("apply", rule, f"Rule missing 'apply': {rule}")

    def test_all_rules_have_callable_match_and_apply(self):
        for rule in PATCH_RULES:
            self.assertTrue(callable(rule["match"]), f"'match' not callable in {rule['name']}")
            self.assertTrue(callable(rule["apply"]), f"'apply' not callable in {rule['name']}")

    def test_at_least_one_pubspec_rule(self):
        pubspec_rules = [r for r in PATCH_RULES if "pubspec" in r["name"].lower()]
        self.assertTrue(len(pubspec_rules) >= 1)

    def test_at_least_one_dart_import_rule(self):
        import_rules = [r for r in PATCH_RULES if "import" in r["name"].lower()]
        self.assertTrue(len(import_rules) >= 1)


if __name__ == "__main__":
    unittest.main()
