"""
tests/test_end_to_end_generation.py – End-to-end integration tests that:

1. Use the generator to produce a complete idle RPG project.
2. Validate Dart syntax via `dart format --output=none` (if Dart SDK available).
3. Cross-check every generated file for correctness:
   - No unexpanded Python f-string template variables leak into output
   - All local `import` references resolve to generated files
   - Brace balance in every Dart file
   - All required cross-method / cross-file references are present
   - All JSON data files parse cleanly
4. Test multiple spec configurations: custom title, landscape orientation, no design doc.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from game_generator.scaffolder import scaffold_project
from game_generator.spec import GameSpec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _idle_spec(title: str = "Dark Fantasy Idle RPG", **kwargs) -> GameSpec:
    base: GameSpec = {
        "title": title,
        "genre": "idle_rpg",
        "mechanics": ["auto_battle", "level_up", "prestige"],
        "required_assets": ["hero", "enemy", "dungeon"],
        "screens": ["game"],
        "controls": {"keyboard": ["click"], "mobile": ["tap"]},
        "progression": {"scoring": "experience", "levels": 100},
    }
    base.update(kwargs)
    return base


def _dart_binary() -> str | None:
    """Return path to 'dart' if available, else None."""
    # Check environment variable override first
    env_dart = os.environ.get("DART_SDK_PATH")
    if env_dart:
        dart = os.path.join(env_dart, "dart")
        if os.path.isfile(dart) and os.access(dart, os.X_OK):
            return dart
    dart = shutil.which("dart")
    if dart:
        return dart
    # Try well-known install location used in CI
    ci_dart = "/opt/dart-sdk/bin/dart"
    if os.path.isfile(ci_dart) and os.access(ci_dart, os.X_OK):
        return ci_dart
    return None


def _local_basenames(files: dict) -> set:
    return {p.split("/")[-1] for p in files if p.endswith(".dart")}


# ---------------------------------------------------------------------------
# Suite 1: Full project generation
# ---------------------------------------------------------------------------

class TestFullProjectGeneration(unittest.TestCase):
    """Generate a complete idle RPG and verify the file set is correct."""

    @classmethod
    def setUpClass(cls):
        cls.files = scaffold_project(_idle_spec())

    def test_total_file_count_at_least_60(self):
        self.assertGreaterEqual(
            len(self.files), 60,
            f"Expected ≥60 files, got {len(self.files)}",
        )

    def test_required_dart_files_present(self):
        required = [
            "lib/game/game.dart",
            "lib/game/hero.dart",
            "lib/game/enemy.dart",
            "lib/game/hud.dart",
            "lib/game/idle_manager.dart",
            "lib/game/upgrade_overlay.dart",
            "lib/game/save_manager.dart",
            "lib/game/damage_text.dart",
            "lib/game/game_over_overlay.dart",
            "lib/game/game_background.dart",
            "lib/widgets/skill_hotbar.dart",
            "lib/main.dart",
            "lib/services/ad_service.dart",
        ]
        for path in required:
            self.assertIn(path, self.files, f"Missing: {path}")

    def test_required_screen_files_present(self):
        screens = [
            "lib/screens/dungeon_screen.dart",
            "lib/screens/town_map_screen.dart",
            "lib/screens/skills_screen.dart",
            "lib/screens/store_screen.dart",
            "lib/screens/quest_log_screen.dart",
            "lib/screens/characters_screen.dart",
            "lib/screens/settings_screen.dart",
            "lib/screens/shop_screen.dart",
            "lib/screens/combat_screen.dart",
        ]
        for path in screens:
            self.assertIn(path, self.files, f"Missing screen: {path}")

    def test_required_asset_data_files_present(self):
        data_files = [
            "assets/data/dungeon_layers.json",
            "assets/data/skills.json",
            "assets/data/town_map.json",
            "assets/data/enemies.json",
            "assets/data/quests.json",
            "assets/data/characters.json",
        ]
        for path in data_files:
            self.assertIn(path, self.files, f"Missing data file: {path}")

    def test_pubspec_yaml_present_and_non_empty(self):
        self.assertIn("pubspec.yaml", self.files)
        self.assertGreater(len(self.files["pubspec.yaml"]), 100)

    def test_required_project_files_present(self):
        project_files = [
            "android/app/build.gradle",
            "android/app/src/main/AndroidManifest.xml",
            "ios/Runner/AppDelegate.swift",
            "ios/Runner/Info.plist",
        ]
        for path in project_files:
            self.assertIn(path, self.files, f"Missing project file: {path}")


# ---------------------------------------------------------------------------
# Suite 2: Dart Syntax via `dart format`
# ---------------------------------------------------------------------------

class TestDartSyntax(unittest.TestCase):
    """Use `dart format --output=none` to verify every .dart file parses."""

    @classmethod
    def setUpClass(cls):
        cls.dart = _dart_binary()
        cls.files = scaffold_project(_idle_spec())
        # Write files to a temp directory
        cls.tmpdir = tempfile.mkdtemp(prefix="gamegen_syntax_")
        for path, content in cls.files.items():
            full = os.path.join(cls.tmpdir, path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as f:
                f.write(content)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    @unittest.skipUnless(_dart_binary(), "Dart SDK not available")
    def test_all_dart_files_parse_cleanly(self):
        dart = _dart_binary()
        dart_files = [
            os.path.join(self.tmpdir, p)
            for p in self.files
            if p.endswith(".dart")
        ]
        errors = []
        for fpath in dart_files:
            result = subprocess.run(
                [dart, "format", "--output=none", fpath],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0 or "could not be parsed" in result.stderr:
                errors.append(
                    f"{os.path.relpath(fpath, self.tmpdir)}: {result.stderr[:200]}"
                )
        self.assertEqual(
            errors, [],
            "Dart syntax errors found:\n" + "\n".join(errors),
        )

    @unittest.skipUnless(_dart_binary(), "Dart SDK not available")
    def test_store_screen_dart_parses(self):
        """Specifically test the store_screen with dollar signs and escaped newlines."""
        dart = _dart_binary()
        fpath = os.path.join(self.tmpdir, "lib/screens/store_screen.dart")
        result = subprocess.run(
            [dart, "format", "--output=none", fpath],
            capture_output=True,
            text=True,
        )
        self.assertNotIn(
            "could not be parsed",
            result.stderr,
            f"store_screen.dart parse error: {result.stderr[:300]}",
        )

    @unittest.skipUnless(_dart_binary(), "Dart SDK not available")
    def test_game_background_dart_parses(self):
        dart = _dart_binary()
        fpath = os.path.join(self.tmpdir, "lib/game/game_background.dart")
        result = subprocess.run(
            [dart, "format", "--output=none", fpath],
            capture_output=True, text=True,
        )
        self.assertNotIn("could not be parsed", result.stderr)

    @unittest.skipUnless(_dart_binary(), "Dart SDK not available")
    def test_skill_hotbar_widget_dart_parses(self):
        dart = _dart_binary()
        fpath = os.path.join(self.tmpdir, "lib/widgets/skill_hotbar.dart")
        result = subprocess.run(
            [dart, "format", "--output=none", fpath],
            capture_output=True, text=True,
        )
        self.assertNotIn("could not be parsed", result.stderr)


# ---------------------------------------------------------------------------
# Suite 3: Dart content correctness (without Dart SDK)
# ---------------------------------------------------------------------------

class TestDartContentCorrectness(unittest.TestCase):
    """Deep content checks that don't require Dart SDK."""

    @classmethod
    def setUpClass(cls):
        cls.files = scaffold_project(_idle_spec())

    # ── Template leaks ────────────────────────────────────────────────────

    def test_no_python_template_leaks_in_dart_files(self):
        """No unexpanded {name} template variables should appear in output."""
        # Pattern: lowercase identifier in braces, NOT preceded by $
        template_re = re.compile(r"(?<!\$)\{[a-z][a-zA-Z_]+\}")
        leaks = []
        for path, content in self.files.items():
            if not path.endswith(".dart"):
                continue
            for lineno, line in enumerate(content.split("\n"), 1):
                # Strip Dart ${ } interpolation and string contents first
                stripped = re.sub(r"\$\{[^}]*\}", "", line)
                stripped = re.sub(r'"[^"]*"', '""', stripped)
                stripped = re.sub(r"'[^']*'", "''", stripped)
                m = template_re.search(stripped)
                if m:
                    leaks.append(f"{path}:{lineno}: {line.strip()[:60]}")
        self.assertEqual(leaks, [], "Template variable leaks:\n" + "\n".join(leaks))

    # ── Brace balance ─────────────────────────────────────────────────────

    def test_all_dart_files_have_balanced_braces(self):
        issues = []
        for path, content in self.files.items():
            if not path.endswith(".dart"):
                continue
            depth = 0
            for i, ch in enumerate(content):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                if depth < 0:
                    lineno = content[:i].count("\n") + 1
                    issues.append(f"[UNDERFLOW] {path}:{lineno}")
                    break
            else:
                if depth != 0:
                    issues.append(f"[IMBALANCE] {path}: depth={depth}")
        self.assertEqual(issues, [], "Brace issues:\n" + "\n".join(issues))

    # ── Local import resolution ───────────────────────────────────────────

    def test_all_local_imports_resolve_to_generated_files(self):
        basenames = _local_basenames(self.files)
        missing = []
        for path, content in self.files.items():
            if not path.endswith(".dart"):
                continue
            for lineno, line in enumerate(content.split("\n"), 1):
                m = re.match(r"import '([^']+)'", line)
                if not m:
                    continue
                imp = m.group(1)
                if imp.startswith("package:") or imp.startswith("dart:"):
                    continue
                basename = imp.split("/")[-1]
                if basename not in basenames:
                    missing.append(f"{path}:{lineno}: {imp}")
        self.assertEqual(
            missing, [],
            "Unresolved local imports:\n" + "\n".join(missing),
        )

    # ── Dollar signs escaped in Dart strings ─────────────────────────────

    def test_no_unescaped_dollar_before_digit_in_store_screen(self):
        """'$0.99' is invalid Dart; must be '\\$0.99'."""
        store = self.files.get("lib/screens/store_screen.dart", "")
        # Regex: single-quote, dollar, digit (not preceded by backslash)
        bad = re.findall(r"'[^']*(?<!\\)\$\d[^']*'", store)
        self.assertEqual(bad, [], f"Unescaped dollar+digit in store_screen.dart: {bad}")

    def test_store_screen_fallback_prices_escaped(self):
        store = self.files.get("lib/screens/store_screen.dart", "")
        # All four prices should be present with escaped dollar signs
        for price in [r"\$0.99", r"\$2.99", r"\$7.99", r"\$17.99"]:
            self.assertIn(price, store, f"Missing escaped price: {price}")

    # ── No real newlines inside single-quoted string literals ────────────

    def test_no_embedded_newlines_in_dart_single_quote_strings(self):
        """Strings like 'foo\\nbar' must use \\n, not a real newline.
        Relies on dart format (if available) for accurate detection.
        """
        dart = _dart_binary()
        if dart:
            # dart format --output=none is the authoritative check and is already
            # tested in TestDartSyntax; skip the unreliable heuristic here.
            return

        # Fallback heuristic: look for lines whose first non-whitespace char is `'`
        # (i.e. a standalone string value), that have no closing `'` on the same line.
        # Skip comment lines and lines that end with `,` (multi-line args are OK here).
        issues = []
        for path, content in self.files.items():
            if not path.endswith(".dart"):
                continue
            for lineno, line in enumerate(content.split("\n"), 1):
                stripped = line.strip()
                # Skip comments, empty lines and multi-line string content
                if (not stripped
                        or stripped.startswith("//")
                        or stripped.startswith("/*")
                        or stripped.startswith("*")):
                    continue
                # Detect a line where a string is opened but never closed
                # Use a simple approach: remove escaped quotes then count quotes
                cleaned = stripped.replace("\\'", "").replace('\\"', "").replace("\\\\", "")
                if cleaned.count("'") % 2 == 1 and not cleaned.endswith("'"):
                    # Odd number of unescaped single quotes AND line does not
                    # end with the closing quote means a string crosses line boundary
                    if re.match(r"^\s*['\"]", line) and not stripped.endswith(","):
                        issues.append(f"{path}:{lineno}: possible unclosed string")
        self.assertEqual(
            issues, [],
            "Possible embedded newlines in string literals:\n" + "\n".join(issues[:20]),
        )

    # ── game.dart cross-references ────────────────────────────────────────

    def test_game_dart_defines_skill_type_enum(self):
        g = self.files["lib/game/game.dart"]
        self.assertIn("enum SkillType", g)
        for variant in ["fireStrike", "guard", "heal"]:
            self.assertIn(variant, g)

    def test_game_dart_has_mp_fields(self):
        g = self.files["lib/game/game.dart"]
        self.assertIn("int mp = 100;", g)
        self.assertIn("int maxMp = 100;", g)

    def test_game_dart_has_guard_fields(self):
        g = self.files["lib/game/game.dart"]
        self.assertIn("bool isGuardActive = false;", g)

    def test_game_dart_has_all_required_methods(self):
        g = self.files["lib/game/game.dart"]
        for method in [
            "autoAttack()",
            "enemyCounterAttack()",
            "heroTakeDamage(",
            "onActivateSkill(",
            "onTapSkillAttack()",
            "_checkEnemyDead()",
            "_persist()",
            "_respawnEnemy()",
            "prestige()",
            "tryAgain()",
        ]:
            self.assertIn(method, g, f"game.dart missing: {method}")

    def test_game_dart_guard_reduces_damage(self):
        g = self.files["lib/game/game.dart"]
        self.assertIn("isGuardActive ? (amount * 0.5)", g)

    def test_game_dart_uses_game_background(self):
        g = self.files["lib/game/game.dart"]
        self.assertIn("GameBackground", g)
        self.assertIn("game_background.dart", g)

    def test_game_dart_has_mp_regen_in_update(self):
        g = self.files["lib/game/game.dart"]
        self.assertIn("mp + dt * 5", g)

    # ── idle_manager cross-references ────────────────────────────────────

    def test_idle_manager_calls_auto_attack(self):
        m = self.files["lib/game/idle_manager.dart"]
        self.assertIn("game.autoAttack()", m)

    def test_idle_manager_calls_enemy_counter_attack(self):
        m = self.files["lib/game/idle_manager.dart"]
        self.assertIn("game.enemyCounterAttack()", m)

    # ── hero.dart cross-references ────────────────────────────────────────

    def test_hero_dart_has_knight_rendering(self):
        h = self.files["lib/game/hero.dart"]
        self.assertIn("helmPath", h)
        self.assertIn("0xFF00AAFF", h)  # visor glow
        self.assertIn("0xFFD4AA00", h)  # golden sword

    def test_hero_dart_has_required_methods(self):
        h = self.files["lib/game/hero.dart"]
        for method in ["gainXp(", "attack(", "applyPrestige(", "resetForPrestige(",
                       "upgradeAttack(", "upgradeDefence(", "upgradeEconomy("]:
            self.assertIn(method, h, f"hero.dart missing: {method}")

    # ── enemy.dart ────────────────────────────────────────────────────────

    def test_enemy_dart_extends_position_component_not_rectangle(self):
        e = self.files["lib/game/enemy.dart"]
        self.assertIn("PositionComponent", e)
        self.assertNotIn("RectangleComponent", e)

    def test_enemy_dart_has_demon_rendering(self):
        e = self.files["lib/game/enemy.dart"]
        self.assertIn("_renderMinion", e)
        self.assertIn("_renderBoss", e)
        self.assertIn("horn", e.lower())

    def test_enemy_dart_has_take_damage_method(self):
        e = self.files["lib/game/enemy.dart"]
        self.assertIn("takeDamage(", e)

    # ── hud.dart cross-references ────────────────────────────────────────

    def test_hud_dart_has_minimap(self):
        h = self.files["lib/game/hud.dart"]
        self.assertIn("_drawMinimap", h)

    def test_hud_dart_references_mp(self):
        h = self.files["lib/game/hud.dart"]
        self.assertIn("g.mp", h)

    def test_hud_dart_has_three_stat_bars(self):
        h = self.files["lib/game/hud.dart"]
        # HP (red), MP (blue), XP (purple)
        self.assertIn("0xFFCC0000", h)  # HP red
        self.assertIn("0xFF0044CC", h)  # MP blue
        self.assertIn("0xFF7722CC", h)  # XP purple

    # ── save_manager cross-references ────────────────────────────────────

    def test_save_manager_has_all_fields(self):
        s = self.files["lib/game/save_manager.dart"]
        for field in ["gold", "diamonds", "wave", "heroLevel", "xp",
                      "prestigeCount", "currentDungeonLayer", "lastSaveTime"]:
            self.assertIn(field, s, f"save_manager.dart missing: {field}")

    # ── skill_hotbar widget ───────────────────────────────────────────────

    def test_skill_hotbar_has_all_four_skills(self):
        sh = self.files["lib/widgets/skill_hotbar.dart"]
        for skill in ["Strike", "Fire", "Guard", "Heal"]:
            self.assertIn(skill, sh)

    def test_skill_hotbar_has_cooldown_animation(self):
        sh = self.files["lib/widgets/skill_hotbar.dart"]
        self.assertIn("AnimationController", sh)
        self.assertIn("cooldown", sh.lower())

    def test_skill_hotbar_calls_game_skill_methods(self):
        sh = self.files["lib/widgets/skill_hotbar.dart"]
        self.assertIn("SkillType.fireStrike", sh)
        self.assertIn("SkillType.guard", sh)
        self.assertIn("SkillType.heal", sh)
        self.assertIn("onTapSkillAttack", sh)

    # ── main.dart ────────────────────────────────────────────────────────

    def test_main_dart_embeds_skill_hotbar(self):
        m = self.files["lib/main.dart"]
        self.assertIn("SkillHotbar(game: _game)", m)
        self.assertIn("skill_hotbar.dart", m)

    def test_main_dart_has_mu_online_theme(self):
        m = self.files["lib/main.dart"]
        self.assertIn("D4A017", m)  # gold colour
        self.assertIn("ThemeData(", m)
        self.assertIn("ColorScheme.dark", m)

    def test_main_dart_has_eight_nav_items(self):
        m = self.files["lib/main.dart"]
        self.assertEqual(m.count("BottomNavigationBarItem"), 8)

    # ── game_background.dart ─────────────────────────────────────────────

    def test_game_background_has_all_layers(self):
        bg = self.files["lib/game/game_background.dart"]
        for method in ["_drawSky", "_drawFloor", "_drawWalls",
                       "_drawTorchGlow", "_drawParticles"]:
            self.assertIn(method, bg, f"game_background.dart missing: {method}")

    def test_game_background_has_negative_priority(self):
        bg = self.files["lib/game/game_background.dart"]
        self.assertIn("priority: -10", bg)


# ---------------------------------------------------------------------------
# Suite 4: JSON data validity
# ---------------------------------------------------------------------------

class TestJsonDataFiles(unittest.TestCase):
    """All generated JSON files must parse cleanly."""

    @classmethod
    def setUpClass(cls):
        cls.files = scaffold_project(_idle_spec())

    def test_all_json_files_parse(self):
        errors = []
        for path, content in self.files.items():
            if not (path.startswith("assets/data/") and path.endswith(".json")):
                continue
            if not content or content.strip() in ("", "[]", "{}"):
                continue  # empty is a warning, not an error
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                errors.append(f"{path}: {e}")
        self.assertEqual(errors, [], "JSON parse errors:\n" + "\n".join(errors))

    def test_dungeon_layers_json_has_layers(self):
        d = json.loads(self.files["assets/data/dungeon_layers.json"])
        self.assertIsInstance(d, list)
        self.assertGreater(len(d), 0)
        for layer in d:
            # Each layer must have at least a name and a floor/id key
            self.assertTrue(
                "name" in layer,
                f"Dungeon layer missing 'name': {layer}",
            )
            self.assertTrue(
                "floor" in layer or "id" in layer,
                f"Dungeon layer missing 'floor'/'id': {layer}",
            )

    def test_skills_json_has_skills(self):
        d = json.loads(self.files["assets/data/skills.json"])
        self.assertIsInstance(d, list)
        self.assertGreater(len(d), 0)
        for skill in d:
            self.assertIn("id", skill)
            self.assertIn("name", skill)

    def test_town_map_json_has_buildings(self):
        d = json.loads(self.files["assets/data/town_map.json"])
        # town_map may be a list of buildings OR a dict with a 'buildings' key
        if isinstance(d, dict):
            self.assertIn("buildings", d)
            buildings = d["buildings"]
        else:
            self.assertIsInstance(d, list)
            buildings = d
        self.assertGreater(len(buildings), 0)
        for building in buildings:
            self.assertIn("name", building, f"Building missing 'name': {building}")

    def test_enemies_json_has_enemies(self):
        d = json.loads(self.files["assets/data/enemies.json"])
        self.assertIsInstance(d, list)
        self.assertGreater(len(d), 0)

    def test_quests_json_has_quests(self):
        d = json.loads(self.files["assets/data/quests.json"])
        self.assertIsInstance(d, list)
        self.assertGreater(len(d), 0)


# ---------------------------------------------------------------------------
# Suite 5: Multiple spec configurations
# ---------------------------------------------------------------------------

class TestMultipleSpecConfigurations(unittest.TestCase):
    """Ensure generation is stable across different inputs."""

    def _generate(self, title: str, **kwargs) -> dict:
        return scaffold_project(_idle_spec(title=title, **kwargs))

    def test_landscape_orientation_generates_valid_project(self):
        files = self._generate("Epic Idle Quest", orientation="landscape")
        self.assertIn("lib/main.dart", files)
        main = files["lib/main.dart"]
        self.assertIn("landscapeLeft", main)
        self.assertNotIn("portraitUp", main)

    def test_portrait_orientation_is_default(self):
        files = self._generate("Portrait Idle RPG")
        main = files["lib/main.dart"]
        self.assertIn("portraitUp", main)

    def test_custom_title_reflected_in_class_names(self):
        files = self._generate("My Amazing Idle Adventure")
        main = files["lib/main.dart"]
        # Title becomes class name: MyAmazingIdleAdventureGame
        # Check it appears in a class declaration context
        self.assertRegex(
            main,
            r"class MyAmazingIdleAdventure\w*\b",
            "Expected 'MyAmazingIdleAdventure...' class in main.dart",
        )

    def test_special_characters_in_title_handled_safely(self):
        """Titles with special chars must still generate valid Dart class names.
        The generated class name should only contain alphanumeric characters and
        must not include the original special characters (`:`, `!`, etc.).
        """
        files = self._generate("MU Online: Dark Ages!")
        main = files["lib/main.dart"]
        # Class name should be PascalCase alphanumeric only
        class_matches = re.findall(r"class\s+(\w+)", main)
        self.assertTrue(len(class_matches) > 0, "No class definitions found in main.dart")
        for cls_name in class_matches:
            self.assertNotRegex(
                cls_name,
                r"[^A-Za-z0-9_]",
                f"Class name '{cls_name}' contains invalid characters",
            )
        # Specifically the special chars from the title should not appear in class names
        for cls_name in class_matches:
            self.assertNotIn(":", cls_name)
            self.assertNotIn("!", cls_name)

    def test_minimal_spec_generates_complete_project(self):
        files = scaffold_project({
            "title": "Simple Game",
            "genre": "idle_rpg",
        })
        self.assertIn("lib/game/game.dart", files)
        self.assertIn("lib/main.dart", files)
        self.assertIn("pubspec.yaml", files)

    def test_generation_is_deterministic(self):
        """Same spec must always produce the same output."""
        spec = _idle_spec("Consistent RPG")
        files_a = scaffold_project(spec)
        files_b = scaffold_project(spec)
        self.assertEqual(
            set(files_a.keys()),
            set(files_b.keys()),
        )
        # Key files must be identical
        for key in ["lib/game/game.dart", "lib/main.dart", "pubspec.yaml"]:
            self.assertEqual(
                files_a[key], files_b[key],
                f"Non-deterministic output for {key}",
            )

    def test_no_syntax_errors_in_any_dart_file_across_configs(self):
        """Brace balance check for 3 different spec configurations."""
        specs = [
            _idle_spec("Alpha Game"),
            _idle_spec("Beta Game", orientation="landscape"),
            _idle_spec("Gamma Game"),
        ]
        for spec in specs:
            files = scaffold_project(spec)
            for path, content in files.items():
                if not path.endswith(".dart"):
                    continue
                depth = 0
                for ch in content:
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                self.assertEqual(
                    depth, 0,
                    f"Unbalanced braces in {path} for title '{spec['title']}'",
                )


# ---------------------------------------------------------------------------
# Suite 6: pubspec.yaml validity
# ---------------------------------------------------------------------------

class TestPubspecYaml(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.files = scaffold_project(_idle_spec())
        cls.pubspec = cls.files["pubspec.yaml"]

    def test_pubspec_has_required_dependencies(self):
        for dep in ["flame:", "google_mobile_ads:", "in_app_purchase:",
                    "shared_preferences:"]:
            self.assertIn(dep, self.pubspec, f"pubspec.yaml missing: {dep}")

    def test_pubspec_has_flutter_assets(self):
        for asset in ["assets/data/dungeon_layers.json",
                      "assets/data/skills.json",
                      "assets/data/town_map.json"]:
            self.assertIn(asset, self.pubspec, f"pubspec missing asset: {asset}")

    def test_pubspec_sdk_constraint_is_valid(self):
        self.assertIn("sdk:", self.pubspec)
        self.assertIn(">=3", self.pubspec)

    def test_pubspec_name_derived_from_title(self):
        files = scaffold_project(_idle_spec("Space Battle RPG"))
        pubspec = files["pubspec.yaml"]
        # name should be snake_case version of title
        self.assertIn("space_battle_rpg", pubspec)


# ---------------------------------------------------------------------------
# Suite 7: Android / iOS scaffold
# ---------------------------------------------------------------------------

class TestMobileScaffold(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.files = scaffold_project(_idle_spec())

    def test_android_manifest_has_internet_permission(self):
        manifest = self.files["android/app/src/main/AndroidManifest.xml"]
        self.assertIn("INTERNET", manifest)

    def test_android_manifest_has_billing_permission(self):
        manifest = self.files["android/app/src/main/AndroidManifest.xml"]
        self.assertIn("BILLING", manifest)

    def test_android_manifest_has_admob_app_id(self):
        manifest = self.files["android/app/src/main/AndroidManifest.xml"]
        self.assertIn("APPLICATION_ID", manifest)

    def test_ios_info_plist_has_required_keys(self):
        plist = self.files["ios/Runner/Info.plist"]
        self.assertIn("CFBundleIdentifier", plist)

    def test_ios_appdelegate_is_valid_swift(self):
        swift = self.files["ios/Runner/AppDelegate.swift"]
        self.assertIn("@UIApplicationMain", swift)
        self.assertIn("FlutterAppDelegate", swift)


if __name__ == "__main__":
    unittest.main(verbosity=2)
