"""
tests/test_big_generator.py – Tests for the one-shot Idle RPG big generator.

Covers:
  - Template-based design doc fallback (offline, no Ollama)
  - Determinism with --seed
  - Orchestrator --idle-rpg mode (offline path)
  - Codegen output contains all expected files
  - Generated ZIP is valid and includes runnable Flutter project structure
  - idle-rpg-gen CLI entry point is importable and has main()
"""

import importlib
import json
import os
import tempfile
import unittest
import zipfile

from game_generator.ai.design_assistant import (
    REQUIRED_KEYS,
    generate_idle_rpg_design_template,
)
from game_generator.scaffolder import scaffold_project
from game_generator.spec import GameSpec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _idle_spec_with_doc(**kwargs) -> GameSpec:
    from game_generator.ai.design_assistant import generate_idle_rpg_design_template
    doc = generate_idle_rpg_design_template("A dark fantasy idle RPG", seed=1)
    base: GameSpec = {
        "title": "Dark Fantasy Idle",
        "genre": "idle_rpg",
        "mechanics": ["auto_battle", "level_up"],
        "required_assets": ["hero", "enemy"],
        "screens": ["game"],
        "controls": {"keyboard": ["click"], "mobile": ["tap"]},
        "progression": {"scoring": "experience", "levels": 20},
        "orientation": "portrait",
        "design_doc_data": doc,
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# Template fallback design doc tests
# ---------------------------------------------------------------------------


class TestTemplateFallback(unittest.TestCase):
    """generate_idle_rpg_design_template produces a valid design doc offline."""

    def test_returns_dict(self):
        doc = generate_idle_rpg_design_template("test prompt")
        self.assertIsInstance(doc, dict)

    def test_has_all_required_keys(self):
        doc = generate_idle_rpg_design_template("test prompt")
        for key in REQUIRED_KEYS:
            self.assertIn(key, doc, f"Missing required key: {key}")

    def test_world_is_string(self):
        doc = generate_idle_rpg_design_template("test prompt")
        self.assertIsInstance(doc["world"], str)
        self.assertTrue(len(doc["world"]) > 0)

    def test_quests_is_nonempty_list(self):
        doc = generate_idle_rpg_design_template("test prompt")
        self.assertIsInstance(doc["quests"], list)
        self.assertGreater(len(doc["quests"]), 0)

    def test_enemies_is_nonempty_list(self):
        doc = generate_idle_rpg_design_template("test prompt")
        self.assertIsInstance(doc["enemies"], list)
        self.assertGreater(len(doc["enemies"]), 0)

    def test_includes_upgrade_tree(self):
        doc = generate_idle_rpg_design_template("test prompt")
        self.assertIn("upgrade_tree", doc)
        self.assertIsInstance(doc["upgrade_tree"], dict)
        # Must have 3 upgrade categories
        self.assertGreaterEqual(len(doc["upgrade_tree"]), 3)

    def test_includes_idle_loops(self):
        doc = generate_idle_rpg_design_template("test prompt")
        self.assertIn("idle_loops", doc)
        self.assertIsInstance(doc["idle_loops"], list)
        self.assertGreater(len(doc["idle_loops"]), 0)


class TestTemplateFallbackDeterminism(unittest.TestCase):
    """Template fallback is deterministic when seed or prompt is fixed."""

    def test_same_seed_same_result(self):
        doc1 = generate_idle_rpg_design_template("any prompt", seed=42)
        doc2 = generate_idle_rpg_design_template("any prompt", seed=42)
        self.assertEqual(doc1["world"], doc2["world"])
        self.assertEqual(len(doc1["quests"]), len(doc2["quests"]))

    def test_different_seeds_may_differ(self):
        doc1 = generate_idle_rpg_design_template("any prompt", seed=1)
        doc2 = generate_idle_rpg_design_template("any prompt", seed=999)
        # Not guaranteed to differ on every key, but world or quests should differ
        # (probabilistically true given the pool sizes)
        differs = (
            doc1["world"] != doc2["world"]
            or len(doc1["quests"]) != len(doc2["quests"])
            or doc1["enemies"][0]["name"] != doc2["enemies"][0]["name"]
        )
        self.assertTrue(differs, "Expected different seeds to produce different content")

    def test_same_prompt_no_seed_is_deterministic(self):
        """Without an explicit seed, the same prompt produces the same result."""
        prompt = "stable prompt for testing"
        doc1 = generate_idle_rpg_design_template(prompt)
        doc2 = generate_idle_rpg_design_template(prompt)
        self.assertEqual(doc1["world"], doc2["world"])


# ---------------------------------------------------------------------------
# Codegen output tests (idle RPG genre with design doc)
# ---------------------------------------------------------------------------


class TestIdleRPGCodegenFiles(unittest.TestCase):
    """All expected files are generated in the idle RPG project."""

    def setUp(self):
        self.files = scaffold_project(_idle_spec_with_doc())

    # Core Dart game files
    def test_game_dart_exists(self):
        self.assertIn("lib/game/game.dart", self.files)

    def test_hero_dart_exists(self):
        self.assertIn("lib/game/hero.dart", self.files)

    def test_enemy_dart_exists(self):
        self.assertIn("lib/game/enemy.dart", self.files)

    def test_idle_manager_dart_exists(self):
        self.assertIn("lib/game/idle_manager.dart", self.files)

    def test_save_manager_dart_exists(self):
        self.assertIn("lib/game/save_manager.dart", self.files)

    def test_upgrade_overlay_dart_exists(self):
        self.assertIn("lib/game/upgrade_overlay.dart", self.files)

    # Data JSON files
    def test_enemies_json_generated(self):
        self.assertIn("assets/data/enemies.json", self.files)

    def test_enemies_json_is_valid_list(self):
        data = json.loads(self.files["assets/data/enemies.json"])
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_enemies_json_has_name_field(self):
        data = json.loads(self.files["assets/data/enemies.json"])
        for enemy in data:
            self.assertIn("name", enemy)

    # UI screens
    def test_combat_screen_dart_exists(self):
        self.assertIn("lib/screens/combat_screen.dart", self.files)

    def test_settings_screen_dart_exists(self):
        self.assertIn("lib/screens/settings_screen.dart", self.files)

    def test_combat_screen_loads_enemies_json(self):
        dart = self.files["lib/screens/combat_screen.dart"]
        self.assertIn("assets/data/enemies.json", dart)
        self.assertIn("rootBundle.loadString", dart)

    def test_settings_screen_has_reset_option(self):
        dart = self.files["lib/screens/settings_screen.dart"]
        self.assertIn("Reset", dart)

    # Upgrade system
    def test_upgrade_overlay_has_three_categories(self):
        dart = self.files["lib/game/upgrade_overlay.dart"]
        self.assertIn("Combat", dart)
        self.assertIn("Defence", dart)
        self.assertIn("Economy", dart)

    def test_hero_has_defence_level(self):
        dart = self.files["lib/game/hero.dart"]
        self.assertIn("defenceLevel", dart)

    def test_hero_has_economy_level(self):
        dart = self.files["lib/game/hero.dart"]
        self.assertIn("economyLevel", dart)

    # Save/load
    def test_save_manager_has_load_method(self):
        dart = self.files["lib/game/save_manager.dart"]
        self.assertIn("Future<void> load()", dart)

    def test_save_manager_has_save_method(self):
        dart = self.files["lib/game/save_manager.dart"]
        self.assertIn("Future<void> save(", dart)

    def test_save_manager_has_reset_method(self):
        dart = self.files["lib/game/save_manager.dart"]
        self.assertIn("Future<void> reset()", dart)

    # Offline progress catch-up
    def test_idle_manager_has_catch_up_logic(self):
        dart = self.files["lib/game/idle_manager.dart"]
        # The offline progress catch-up method is called _applyCatchUp or applyCatchUp
        self.assertIn("CatchUp", dart)

    # Main nav includes all screens
    def test_main_dart_has_combat_screen(self):
        main = self.files["lib/main.dart"]
        self.assertIn("CombatScreen", main)

    def test_main_dart_has_settings_screen(self):
        main = self.files["lib/main.dart"]
        self.assertIn("SettingsScreen", main)

    def test_main_dart_has_six_nav_items(self):
        main = self.files["lib/main.dart"]
        # Count BottomNavigationBarItem occurrences
        count = main.count("BottomNavigationBarItem")
        self.assertEqual(count, 6)

    # pubspec.yaml includes shared_preferences
    def test_pubspec_has_shared_preferences(self):
        pubspec = self.files["pubspec.yaml"]
        self.assertIn("shared_preferences", pubspec)


# ---------------------------------------------------------------------------
# ZIP output tests
# ---------------------------------------------------------------------------


class TestZipOutput(unittest.TestCase):
    """Generated ZIP is valid and contains expected Flutter project structure."""

    def setUp(self):
        """Run the orchestrator in offline idle_rpg mode and produce a ZIP."""
        from orchestrator.orchestrator import Orchestrator
        self.tmp = tempfile.mkdtemp()
        self.zip_path = os.path.join(self.tmp, "test_idle.zip")
        orchestrator = Orchestrator(interactive=False)
        orchestrator.run(
            prompt="A cursed kingdom idle RPG",
            output_zip=self.zip_path,
            idle_rpg=True,
            seed=7,
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_zip_file_created(self):
        self.assertTrue(os.path.isfile(self.zip_path))

    def test_zip_is_valid(self):
        self.assertTrue(zipfile.is_zipfile(self.zip_path))

    def _zip_names(self):
        with zipfile.ZipFile(self.zip_path) as zf:
            return set(zf.namelist())

    def test_zip_contains_pubspec(self):
        names = self._zip_names()
        self.assertTrue(any("pubspec.yaml" in n for n in names))

    def test_zip_contains_main_dart(self):
        names = self._zip_names()
        self.assertTrue(any("main.dart" in n for n in names))

    def test_zip_contains_enemies_json(self):
        names = self._zip_names()
        self.assertTrue(any("enemies.json" in n for n in names))

    def test_zip_contains_design_doc(self):
        names = self._zip_names()
        # Either design.json or DESIGN.md depending on format
        self.assertTrue(
            any("design.json" in n for n in names) or any("DESIGN.md" in n for n in names)
        )

    def test_zip_contains_save_manager(self):
        names = self._zip_names()
        self.assertTrue(any("save_manager.dart" in n for n in names))


# ---------------------------------------------------------------------------
# CLI entry point test
# ---------------------------------------------------------------------------


class TestIdleRPGGenEntryPoint(unittest.TestCase):
    """idle_rpg_gen module must be importable with a callable main()."""

    def test_module_importable(self):
        mod = importlib.import_module("idle_rpg_gen")
        self.assertIsNotNone(mod)

    def test_has_main(self):
        mod = importlib.import_module("idle_rpg_gen")
        self.assertTrue(callable(getattr(mod, "main", None)))


# ---------------------------------------------------------------------------
# Orchestrator idle_rpg mode (offline fallback)
# ---------------------------------------------------------------------------


class TestOrchestratorIdleRPGMode(unittest.TestCase):
    """Orchestrator with idle_rpg=True uses template fallback when Ollama is absent."""

    def test_idle_rpg_forces_genre(self):
        """Verifies that idle_rpg mode always sets genre to idle_rpg."""
        from game_generator.spec import generate_spec
        spec = generate_spec("a top down space shooter with guns")
        # Without override, spec would be top_down_shooter
        self.assertEqual(spec["genre"], "top_down_shooter")

        # After orchestrator applies idle_rpg override, genre becomes idle_rpg
        from orchestrator.orchestrator import Orchestrator
        import tempfile
        import os
        tmp = tempfile.mkdtemp()
        zip_path = os.path.join(tmp, "out.zip")
        try:
            Orchestrator().run(
                prompt="space shooter with guns",
                output_zip=zip_path,
                idle_rpg=True,
                seed=1,
            )
            import zipfile
            with zipfile.ZipFile(zip_path) as zf:
                names = set(zf.namelist())
            # idle_rpg genre always generates idle_manager.dart
            self.assertTrue(any("idle_manager.dart" in n for n in names))
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
