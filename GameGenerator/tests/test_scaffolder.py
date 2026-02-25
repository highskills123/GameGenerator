"""
Unit tests for gamegenerator.scaffolder.scaffold_project.
"""

import unittest

from gamegenerator.scaffolder import scaffold_project, REQUIRED_FILES
from gamegenerator.spec import GameSpec


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
    def test_shooter_contains_required_files(self):
        files = scaffold_project(_shooter_spec())
        for req in REQUIRED_FILES:
            self.assertIn(req, files, f"Missing required file: {req}")

    def test_idle_contains_required_files(self):
        files = scaffold_project(_idle_spec())
        for req in REQUIRED_FILES:
            self.assertIn(req, files, f"Missing required file: {req}")


class TestScaffolderPubspec(unittest.TestCase):
    def test_pubspec_has_flame_dependency(self):
        files = scaffold_project(_shooter_spec())
        self.assertIn("flame:", files["pubspec.yaml"])

    def test_pubspec_has_flutter_dependency(self):
        files = scaffold_project(_shooter_spec())
        self.assertIn("flutter:", files["pubspec.yaml"])

    def test_pubspec_package_name_derived_from_title(self):
        files = scaffold_project(_shooter_spec(title="My Awesome Game"))
        pubspec = files["pubspec.yaml"]
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
    def test_main_dart_has_main_function(self):
        self.assertIn("void main()", scaffold_project(_shooter_spec())["lib/main.dart"])

    def test_main_dart_imports_flame(self):
        self.assertIn("flame", scaffold_project(_shooter_spec())["lib/main.dart"])

    def test_main_dart_has_game_widget(self):
        self.assertIn("GameWidget", scaffold_project(_shooter_spec())["lib/main.dart"])

    def test_main_dart_locks_orientation(self):
        main = scaffold_project(_shooter_spec())["lib/main.dart"]
        self.assertIn("setPreferredOrientations", main)


class TestScaffolderMobile(unittest.TestCase):
    def test_shooter_has_android_manifest(self):
        files = scaffold_project(_shooter_spec())
        self.assertIn("android/app/src/main/AndroidManifest.xml", files)

    def test_shooter_has_ios_plist(self):
        files = scaffold_project(_shooter_spec())
        self.assertIn("ios/Runner/Info.plist", files)

    def test_shooter_has_mobile_controls(self):
        files = scaffold_project(_shooter_spec())
        self.assertIn("lib/game/mobile_controls.dart", files)

    def test_shooter_android_manifest_is_landscape(self):
        files = scaffold_project(_shooter_spec(orientation="landscape"))
        self.assertIn("sensorLandscape", files["android/app/src/main/AndroidManifest.xml"])

    def test_idle_android_manifest_is_portrait(self):
        files = scaffold_project(_idle_spec(orientation="portrait"))
        self.assertIn("sensorPortrait", files["android/app/src/main/AndroidManifest.xml"])


class TestScaffolderGenreFiles(unittest.TestCase):
    def test_shooter_has_player_dart(self):
        self.assertIn("lib/game/player.dart", scaffold_project(_shooter_spec()))

    def test_shooter_has_bullet_dart(self):
        self.assertIn("lib/game/bullet.dart", scaffold_project(_shooter_spec()))

    def test_shooter_has_bullet_pool(self):
        self.assertIn("lib/game/bullet_pool.dart", scaffold_project(_shooter_spec()))

    def test_idle_has_hero_dart(self):
        self.assertIn("lib/game/hero.dart", scaffold_project(_idle_spec()))

    def test_idle_has_idle_manager_dart(self):
        self.assertIn("lib/game/idle_manager.dart", scaffold_project(_idle_spec()))


class TestScaffolderDocFiles(unittest.TestCase):
    def test_readme_mentions_title(self):
        files = scaffold_project(_shooter_spec(title="Galaxy Blaster"))
        self.assertIn("Galaxy Blaster", files["README.md"])

    def test_readme_mentions_flutter_run(self):
        self.assertIn("flutter run", scaffold_project(_shooter_spec())["README.md"])

    def test_credits_md_present(self):
        self.assertIn("CREDITS.md", scaffold_project(_shooter_spec()))

    def test_assets_license_mentions_user_responsibility(self):
        lic = scaffold_project(_shooter_spec())["ASSETS_LICENSE.md"]
        self.assertIn("licence", lic.lower())

    def test_assets_license_no_auto_download_claim(self):
        lic = scaffold_project(_shooter_spec())["ASSETS_LICENSE.md"]
        self.assertIn("not", lic.lower())


class TestScaffolderSpec(unittest.TestCase):
    def test_generate_spec_shooter_keywords(self):
        from gamegenerator.spec import generate_spec
        spec = generate_spec("build a top down space shooter with bullets and enemies")
        self.assertEqual(spec["genre"], "top_down_shooter")

    def test_generate_spec_idle_keywords(self):
        from gamegenerator.spec import generate_spec
        spec = generate_spec("create an idle clicker RPG where heroes level up")
        self.assertEqual(spec["genre"], "idle_rpg")

    def test_generate_spec_has_required_keys(self):
        from gamegenerator.spec import generate_spec
        spec = generate_spec("space shooter")
        for key in ("title", "genre", "mechanics", "required_assets", "screens", "controls", "progression"):
            self.assertIn(key, spec, f"Missing key: {key}")


if __name__ == "__main__":
    unittest.main()
