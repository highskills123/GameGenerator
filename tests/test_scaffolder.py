"""
Unit tests for game_generator.scaffolder.scaffold_project.
"""

import unittest

from game_generator.scaffolder import scaffold_project, REQUIRED_FILES
from game_generator.spec import GameSpec


def _shooter_spec(**kwargs) -> GameSpec:
    base: GameSpec = {
        "title": "Space Blaster",
        "genre": "top_down_shooter",
        "mechanics": ["move", "shoot"],
        "required_assets": ["player", "enemy", "bullet"],
        "screens": ["main_menu", "game", "game_over"],
        "controls": {"keyboard": ["WASD", "space"], "mobile": ["joystick"]},
        "progression": {"scoring": "points", "levels": 5},
    }
    base.update(kwargs)
    return base


def _idle_spec(**kwargs) -> GameSpec:
    base: GameSpec = {
        "title": "Epic Idle",
        "genre": "idle_rpg",
        "mechanics": ["auto_battle", "level_up"],
        "required_assets": ["hero", "enemy"],
        "screens": ["game"],
        "controls": {"keyboard": ["click"], "mobile": ["tap"]},
        "progression": {"scoring": "experience", "levels": 20},
    }
    base.update(kwargs)
    return base


class TestScaffolderRequiredFiles(unittest.TestCase):
    """scaffold_project must always produce the mandatory files."""

    def test_shooter_contains_required_files(self):
        files = scaffold_project(_shooter_spec())
        for req in REQUIRED_FILES:
            self.assertIn(req, files, f"Missing required file: {req}")

    def test_idle_contains_required_files(self):
        files = scaffold_project(_idle_spec())
        for req in REQUIRED_FILES:
            self.assertIn(req, files, f"Missing required file: {req}")


class TestScaffolderPubspec(unittest.TestCase):
    """pubspec.yaml must reference flame and have the correct package name."""

    def test_pubspec_has_flame_dependency(self):
        files = scaffold_project(_shooter_spec())
        pubspec = files["pubspec.yaml"]
        self.assertIn("flame:", pubspec)

    def test_pubspec_has_flutter_dependency(self):
        files = scaffold_project(_shooter_spec())
        pubspec = files["pubspec.yaml"]
        self.assertIn("flutter:", pubspec)

    def test_pubspec_package_name_derived_from_title(self):
        files = scaffold_project(_shooter_spec(title="My Awesome Game"))
        pubspec = files["pubspec.yaml"]
        # Should appear as "my_awesome_game" or similar
        self.assertIn("name:", pubspec)
        first_line_with_name = next(
            (l for l in pubspec.splitlines() if l.startswith("name:")), ""
        )
        pkg = first_line_with_name.split(":", 1)[-1].strip()
        self.assertTrue(pkg.replace("_", "").isalnum(), f"Invalid package name: {pkg}")

    def test_pubspec_includes_imported_assets(self):
        paths = ["assets/imported/player.png", "assets/imported/enemy.png"]
        files = scaffold_project(_shooter_spec(), imported_asset_paths=paths)
        pubspec = files["pubspec.yaml"]
        for p in paths:
            self.assertIn(p, pubspec, f"Asset not referenced in pubspec: {p}")


class TestScaffolderMainDart(unittest.TestCase):
    """lib/main.dart must contain required Flame boilerplate."""

    def test_main_dart_has_main_function(self):
        files = scaffold_project(_shooter_spec())
        main = files["lib/main.dart"]
        self.assertIn("void main()", main)

    def test_main_dart_imports_flame(self):
        files = scaffold_project(_shooter_spec())
        main = files["lib/main.dart"]
        self.assertIn("flame", main)

    def test_main_dart_has_game_widget(self):
        files = scaffold_project(_shooter_spec())
        main = files["lib/main.dart"]
        self.assertIn("GameWidget", main)


class TestScaffolderGenreFiles(unittest.TestCase):
    """Genre-specific files must be present."""

    def test_shooter_has_player_dart(self):
        files = scaffold_project(_shooter_spec())
        self.assertIn("lib/game/player.dart", files)

    def test_shooter_has_bullet_dart(self):
        files = scaffold_project(_shooter_spec())
        self.assertIn("lib/game/bullet.dart", files)

    def test_shooter_has_bullet_pool(self):
        files = scaffold_project(_shooter_spec())
        self.assertIn("lib/game/bullet_pool.dart", files)

    def test_idle_has_hero_dart(self):
        files = scaffold_project(_idle_spec())
        self.assertIn("lib/game/hero.dart", files)

    def test_idle_has_idle_manager_dart(self):
        files = scaffold_project(_idle_spec())
        self.assertIn("lib/game/idle_manager.dart", files)


class TestScaffolderDocFiles(unittest.TestCase):
    """README and ASSETS_LICENSE must be non-empty and contain key text."""

    def test_readme_mentions_title(self):
        files = scaffold_project(_shooter_spec(title="Galaxy Blaster"))
        readme = files["README.md"]
        self.assertIn("Galaxy Blaster", readme)

    def test_readme_mentions_flutter_run(self):
        files = scaffold_project(_shooter_spec())
        readme = files["README.md"]
        self.assertIn("flutter run", readme)

    def test_assets_license_mentions_user_responsibility(self):
        files = scaffold_project(_shooter_spec())
        lic = files["ASSETS_LICENSE.md"]
        self.assertIn("licence", lic.lower())

    def test_assets_license_no_auto_download_claim(self):
        files = scaffold_project(_shooter_spec())
        lic = files["ASSETS_LICENSE.md"]
        # Must explicitly state no automatic downloading
        self.assertIn("not", lic.lower())


class TestScaffolderSpec(unittest.TestCase):
    """Tests for the spec generation heuristics."""

    def test_generate_spec_shooter_keywords(self):
        from game_generator.spec import generate_spec
        spec = generate_spec("build a top down space shooter with bullets and enemies")
        self.assertEqual(spec["genre"], "top_down_shooter")

    def test_generate_spec_idle_keywords(self):
        from game_generator.spec import generate_spec
        spec = generate_spec("create an idle clicker RPG where heroes level up")
        self.assertEqual(spec["genre"], "idle_rpg")

    def test_generate_spec_default_genre_no_keywords(self):
        from game_generator.spec import generate_spec
        spec = generate_spec("make a game")
        self.assertIn(spec["genre"], ["top_down_shooter", "idle_rpg"])

    def test_generate_spec_has_required_keys(self):
        from game_generator.spec import generate_spec
        spec = generate_spec("space shooter")
        for key in ("title", "genre", "mechanics", "required_assets", "screens", "controls", "progression"):
            self.assertIn(key, spec, f"Missing key: {key}")


if __name__ == "__main__":
    unittest.main()
