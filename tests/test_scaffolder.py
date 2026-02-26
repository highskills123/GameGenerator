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


# ---------------------------------------------------------------------------
# Mobile-readiness tests (iOS + Android completeness)
# ---------------------------------------------------------------------------

class TestMobileReadiness(unittest.TestCase):
    """Generated project must include all files required to run on iOS and Android."""

    def setUp(self):
        self.files = scaffold_project(_idle_spec())

    # ── iOS ──────────────────────────────────────────────────────────────────

    def test_ios_app_delegate_swift_exists(self):
        self.assertIn("ios/Runner/AppDelegate.swift", self.files)

    def test_ios_app_delegate_swift_content(self):
        content = self.files["ios/Runner/AppDelegate.swift"]
        self.assertIn("FlutterAppDelegate", content)
        self.assertIn("GeneratedPluginRegistrant", content)

    def test_ios_bridging_header_exists(self):
        self.assertIn("ios/Runner/Runner-Bridging-Header.h", self.files)

    def test_ios_podfile_exists(self):
        self.assertIn("ios/Podfile", self.files)

    def test_ios_podfile_platform_ios(self):
        self.assertIn("platform :ios", self.files["ios/Podfile"])

    def test_ios_podfile_has_flutter_install(self):
        self.assertIn("flutter_install_all_ios_pods", self.files["ios/Podfile"])

    def test_ios_launch_screen_storyboard_exists(self):
        self.assertIn("ios/Runner/Base.lproj/LaunchScreen.storyboard", self.files)

    def test_ios_launch_screen_storyboard_valid_xml(self):
        content = self.files["ios/Runner/Base.lproj/LaunchScreen.storyboard"]
        self.assertIn("<?xml", content)
        self.assertIn("document type", content)

    def test_ios_main_storyboard_exists(self):
        self.assertIn("ios/Runner/Base.lproj/Main.storyboard", self.files)

    def test_ios_main_storyboard_uses_flutter_view_controller(self):
        content = self.files["ios/Runner/Base.lproj/Main.storyboard"]
        self.assertIn("FlutterViewController", content)

    def test_ios_assets_contents_json_exists(self):
        self.assertIn("ios/Runner/Assets.xcassets/Contents.json", self.files)

    def test_ios_app_icon_contents_json_exists(self):
        self.assertIn("ios/Runner/Assets.xcassets/AppIcon.appiconset/Contents.json", self.files)

    def test_ios_app_icon_has_universal_entry(self):
        import json
        content = json.loads(
            self.files["ios/Runner/Assets.xcassets/AppIcon.appiconset/Contents.json"]
        )
        self.assertIn("images", content)
        self.assertTrue(len(content["images"]) > 0)

    def test_ios_xcworkspace_exists(self):
        self.assertIn("ios/Runner.xcworkspace/contents.xcworkspacedata", self.files)

    def test_ios_xcworkspace_references_xcodeproj(self):
        content = self.files["ios/Runner.xcworkspace/contents.xcworkspacedata"]
        self.assertIn("Runner.xcodeproj", content)

    def test_ios_pbxproj_exists(self):
        self.assertIn("ios/Runner.xcodeproj/project.pbxproj", self.files)

    def test_ios_pbxproj_has_required_sections(self):
        content = self.files["ios/Runner.xcodeproj/project.pbxproj"]
        for section in [
            "PBXBuildFile",
            "PBXFileReference",
            "PBXNativeTarget",
            "PBXProject",
            "XCBuildConfiguration",
            "XCConfigurationList",
        ]:
            self.assertIn(section, content, f"pbxproj missing section: {section}")

    def test_ios_pbxproj_contains_bundle_identifier(self):
        content = self.files["ios/Runner.xcodeproj/project.pbxproj"]
        self.assertIn("PRODUCT_BUNDLE_IDENTIFIER", content)
        self.assertIn("com.example.", content)

    def test_ios_pbxproj_contains_app_delegate(self):
        content = self.files["ios/Runner.xcodeproj/project.pbxproj"]
        self.assertIn("AppDelegate.swift", content)

    def test_ios_pbxproj_is_deterministic(self):
        """Same spec → identical pbxproj (UUIDs are deterministic)."""
        files2 = scaffold_project(_idle_spec())
        self.assertEqual(
            self.files["ios/Runner.xcodeproj/project.pbxproj"],
            files2["ios/Runner.xcodeproj/project.pbxproj"],
        )

    # ── Android ──────────────────────────────────────────────────────────────

    def test_android_night_styles_exists(self):
        self.assertIn(
            "android/app/src/main/res/values-night/styles.xml", self.files
        )

    def test_android_night_styles_has_launch_theme(self):
        content = self.files["android/app/src/main/res/values-night/styles.xml"]
        self.assertIn("LaunchTheme", content)

    def test_android_mipmap_all_densities(self):
        for density in ("mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"):
            path = f"android/app/src/main/res/mipmap-{density}/ic_launcher.png"
            self.assertIn(path, self.files, f"Missing mipmap density: {density}")

    # ── Developer-experience files ────────────────────────────────────────────

    def test_analysis_options_exists(self):
        self.assertIn("analysis_options.yaml", self.files)

    def test_analysis_options_includes_flutter_lints(self):
        content = self.files["analysis_options.yaml"]
        self.assertIn("flutter_lints", content)

    def test_gitignore_exists(self):
        self.assertIn(".gitignore", self.files)

    def test_gitignore_ignores_local_properties(self):
        self.assertIn("local.properties", self.files[".gitignore"])

    def test_gitignore_ignores_ios_pods(self):
        self.assertIn("ios/Pods/", self.files[".gitignore"])

    def test_gitignore_ignores_build_dir(self):
        self.assertIn("build/", self.files[".gitignore"])

    def test_quickstart_md_exists(self):
        self.assertIn("QUICKSTART.md", self.files)

    def test_quickstart_md_contains_flutter_pub_get(self):
        self.assertIn("flutter pub get", self.files["QUICKSTART.md"])

    def test_quickstart_md_contains_flutter_run(self):
        self.assertIn("flutter run", self.files["QUICKSTART.md"])

    def test_quickstart_md_contains_pod_install(self):
        self.assertIn("pod install", self.files["QUICKSTART.md"])

    def test_quickstart_md_contains_build_apk(self):
        self.assertIn("flutter build apk", self.files["QUICKSTART.md"])

    def test_quickstart_md_contains_build_ipa(self):
        self.assertIn("flutter build ipa", self.files["QUICKSTART.md"])

    def test_quickstart_md_contains_icon_replacement_guide(self):
        self.assertIn("ic_launcher", self.files["QUICKSTART.md"])

    # ── pubspec dev_dependencies ──────────────────────────────────────────────

    def test_pubspec_has_dev_dependencies(self):
        self.assertIn("dev_dependencies:", self.files["pubspec.yaml"])

    def test_pubspec_has_flutter_test(self):
        self.assertIn("flutter_test:", self.files["pubspec.yaml"])

    def test_pubspec_has_flutter_lints(self):
        self.assertIn("flutter_lints:", self.files["pubspec.yaml"])


# ---------------------------------------------------------------------------
# Full idle RPG mobile expansion tests
# ---------------------------------------------------------------------------

class TestIdleRPGExpansion(unittest.TestCase):
    """Tests for dungeon layers, town map, skills, diamonds, IAP, and video ads."""

    def setUp(self):
        self.files = scaffold_project(_idle_spec())

    # ── New data files ────────────────────────────────────────────────────────

    def test_dungeon_layers_json_exists(self):
        self.assertIn("assets/data/dungeon_layers.json", self.files)

    def test_dungeon_layers_has_five_floors(self):
        import json
        data = json.loads(self.files["assets/data/dungeon_layers.json"])
        self.assertEqual(len(data), 5)

    def test_dungeon_layers_each_has_boss(self):
        import json
        data = json.loads(self.files["assets/data/dungeon_layers.json"])
        for floor in data:
            self.assertIn("boss", floor, f"Floor {floor.get('floor')} missing boss")

    def test_dungeon_layers_wave_gated(self):
        import json
        data = json.loads(self.files["assets/data/dungeon_layers.json"])
        self.assertTrue(all("min_wave" in f for f in data))
        # Floor 1 is unlocked from wave 1
        self.assertEqual(data[0]["min_wave"], 1)

    def test_skills_json_exists(self):
        self.assertIn("assets/data/skills.json", self.files)

    def test_skills_json_has_three_paths(self):
        import json
        data = json.loads(self.files["assets/data/skills.json"])
        paths = {s["path"] for s in data}
        self.assertEqual(paths, {"Warrior", "Rogue", "Mage"})

    def test_skills_json_each_has_diamond_cost(self):
        import json
        data = json.loads(self.files["assets/data/skills.json"])
        for skill in data:
            self.assertIn("cost_diamonds", skill)
            self.assertGreater(skill["cost_diamonds"], 0)

    def test_town_map_json_exists(self):
        self.assertIn("assets/data/town_map.json", self.files)

    def test_town_map_has_six_buildings(self):
        import json
        data = json.loads(self.files["assets/data/town_map.json"])
        self.assertEqual(len(data), 6)

    def test_town_map_buildings_have_services(self):
        import json
        data = json.loads(self.files["assets/data/town_map.json"])
        for b in data:
            self.assertIn("services", b)
            self.assertGreater(len(b["services"]), 0)

    # ── New screens ───────────────────────────────────────────────────────────

    def test_dungeon_screen_exists(self):
        self.assertIn("lib/screens/dungeon_screen.dart", self.files)

    def test_dungeon_screen_loads_dungeon_layers_json(self):
        content = self.files["lib/screens/dungeon_screen.dart"]
        self.assertIn("dungeon_layers.json", content)

    def test_dungeon_screen_uses_shared_preferences_for_wave(self):
        content = self.files["lib/screens/dungeon_screen.dart"]
        self.assertIn("save_wave", content)

    def test_dungeon_screen_shows_lock_icon_for_gated_floors(self):
        content = self.files["lib/screens/dungeon_screen.dart"]
        self.assertIn("lock", content.lower())

    def test_town_map_screen_exists(self):
        self.assertIn("lib/screens/town_map_screen.dart", self.files)

    def test_town_map_screen_loads_town_map_json(self):
        content = self.files["lib/screens/town_map_screen.dart"]
        self.assertIn("town_map.json", content)

    def test_town_map_screen_uses_grid(self):
        content = self.files["lib/screens/town_map_screen.dart"]
        self.assertIn("GridView", content)

    def test_town_map_screen_has_bottom_sheet_detail(self):
        content = self.files["lib/screens/town_map_screen.dart"]
        self.assertIn("showModalBottomSheet", content)

    def test_skills_screen_exists(self):
        self.assertIn("lib/screens/skills_screen.dart", self.files)

    def test_skills_screen_loads_skills_json(self):
        content = self.files["lib/screens/skills_screen.dart"]
        self.assertIn("skills.json", content)

    def test_skills_screen_has_three_tabs(self):
        content = self.files["lib/screens/skills_screen.dart"]
        self.assertIn("Warrior", content)
        self.assertIn("Rogue", content)
        self.assertIn("Mage", content)

    def test_skills_screen_reads_diamonds_from_prefs(self):
        content = self.files["lib/screens/skills_screen.dart"]
        self.assertIn("save_diamonds", content)

    def test_store_screen_exists(self):
        self.assertIn("lib/screens/store_screen.dart", self.files)

    def test_store_screen_uses_in_app_purchase(self):
        content = self.files["lib/screens/store_screen.dart"]
        self.assertIn("InAppPurchase", content)

    def test_store_screen_has_product_ids(self):
        content = self.files["lib/screens/store_screen.dart"]
        self.assertIn("diamonds_50", content)
        self.assertIn("diamonds_1200", content)

    def test_store_screen_handles_purchase_status(self):
        content = self.files["lib/screens/store_screen.dart"]
        self.assertIn("PurchaseStatus.purchased", content)

    # ── Ad service ────────────────────────────────────────────────────────────

    def test_ad_service_exists(self):
        self.assertIn("lib/services/ad_service.dart", self.files)

    def test_ad_service_uses_google_mobile_ads(self):
        content = self.files["lib/services/ad_service.dart"]
        self.assertIn("google_mobile_ads", content)

    def test_ad_service_has_rewarded_ad(self):
        content = self.files["lib/services/ad_service.dart"]
        self.assertIn("RewardedAd", content)

    def test_ad_service_uses_test_id(self):
        content = self.files["lib/services/ad_service.dart"]
        self.assertIn("3940256099942544", content)

    def test_ad_service_preloads_next_ad(self):
        """After showing an ad it should reload the next one."""
        content = self.files["lib/services/ad_service.dart"]
        self.assertIn("_loadAd()", content)

    # ── Diamonds currency ─────────────────────────────────────────────────────

    def test_game_dart_has_diamonds_field(self):
        content = self.files["lib/game/game.dart"]
        self.assertIn("int diamonds = 0;", content)

    def test_game_dart_has_dungeon_layer_field(self):
        content = self.files["lib/game/game.dart"]
        self.assertIn("int currentDungeonLayer = 1;", content)

    def test_game_dart_imports_ad_service(self):
        content = self.files["lib/game/game.dart"]
        self.assertIn("ad_service.dart", content)

    def test_game_dart_has_earn_diamonds_method(self):
        content = self.files["lib/game/game.dart"]
        self.assertIn("earnDiamonds", content)

    def test_game_dart_has_watch_ad_for_gold_method(self):
        content = self.files["lib/game/game.dart"]
        self.assertIn("watchAdForGold", content)

    def test_game_dart_awards_diamonds_for_boss(self):
        content = self.files["lib/game/game.dart"]
        self.assertIn("diamonds += 5", content)

    def test_save_manager_has_diamonds(self):
        content = self.files["lib/game/save_manager.dart"]
        self.assertIn("int diamonds = 0;", content)

    def test_save_manager_has_dungeon_layer(self):
        content = self.files["lib/game/save_manager.dart"]
        self.assertIn("currentDungeonLayer", content)

    def test_save_manager_persists_diamonds(self):
        content = self.files["lib/game/save_manager.dart"]
        self.assertIn("save_diamonds", content)

    def test_hud_shows_diamonds(self):
        content = self.files["lib/game/hud.dart"]
        self.assertIn("g.diamonds", content)

    # ── Game over overlay – Watch Ad button ────────────────────────────────────

    def test_game_over_is_stateful_widget(self):
        content = self.files["lib/game/game_over_overlay.dart"]
        self.assertIn("StatefulWidget", content)

    def test_game_over_has_watch_ad_button(self):
        content = self.files["lib/game/game_over_overlay.dart"]
        self.assertIn("Watch Ad", content)

    def test_game_over_calls_watch_ad_for_gold(self):
        content = self.files["lib/game/game_over_overlay.dart"]
        self.assertIn("watchAdForGold", content)

    def test_game_over_shows_diamonds_balance(self):
        content = self.files["lib/game/game_over_overlay.dart"]
        self.assertIn("game.diamonds", content)

    # ── Navigation ────────────────────────────────────────────────────────────

    def test_main_dart_has_eight_nav_items(self):
        main = self.files["lib/main.dart"]
        count = main.count("BottomNavigationBarItem")
        self.assertEqual(count, 8)

    def test_main_dart_imports_new_screens(self):
        main = self.files["lib/main.dart"]
        self.assertIn("dungeon_screen.dart", main)
        self.assertIn("town_map_screen.dart", main)
        self.assertIn("skills_screen.dart", main)
        self.assertIn("store_screen.dart", main)

    def test_main_dart_initializes_mobile_ads(self):
        main = self.files["lib/main.dart"]
        self.assertIn("MobileAds.instance.initialize", main)

    def test_main_dart_imports_google_mobile_ads(self):
        main = self.files["lib/main.dart"]
        self.assertIn("google_mobile_ads", main)

    # ── pubspec – new deps ─────────────────────────────────────────────────────

    def test_pubspec_has_in_app_purchase(self):
        self.assertIn("in_app_purchase", self.files["pubspec.yaml"])

    def test_pubspec_has_google_mobile_ads(self):
        self.assertIn("google_mobile_ads", self.files["pubspec.yaml"])

    # ── Android manifest ──────────────────────────────────────────────────────

    def test_android_manifest_has_internet_permission(self):
        manifest = self.files["android/app/src/main/AndroidManifest.xml"]
        self.assertIn("android.permission.INTERNET", manifest)

    def test_android_manifest_has_billing_permission(self):
        manifest = self.files["android/app/src/main/AndroidManifest.xml"]
        self.assertIn("com.android.vending.BILLING", manifest)

    def test_android_manifest_has_admob_app_id(self):
        manifest = self.files["android/app/src/main/AndroidManifest.xml"]
        self.assertIn("APPLICATION_ID", manifest)


# ---------------------------------------------------------------------------
# MU Online-style visual overhaul tests
# ---------------------------------------------------------------------------

class TestMuOnlineVisuals(unittest.TestCase):
    """Tests for MU Online-style visual changes: dungeon background, knight
    hero sprite, demon enemy sprite, redesigned HUD, skill hotbar, and theme."""

    def setUp(self):
        self.files = scaffold_project(_idle_spec())

    # ── New files ─────────────────────────────────────────────────────────────

    def test_game_background_dart_exists(self):
        self.assertIn("lib/game/game_background.dart", self.files)

    def test_skill_hotbar_widget_exists(self):
        self.assertIn("lib/widgets/skill_hotbar.dart", self.files)

    # ── GameBackground – atmospheric dungeon ─────────────────────────────────

    def test_game_background_draws_sky(self):
        content = self.files["lib/game/game_background.dart"]
        self.assertIn("_drawSky", content)

    def test_game_background_draws_floor(self):
        content = self.files["lib/game/game_background.dart"]
        self.assertIn("_drawFloor", content)

    def test_game_background_draws_walls(self):
        content = self.files["lib/game/game_background.dart"]
        self.assertIn("_drawWalls", content)

    def test_game_background_has_torch_glow(self):
        content = self.files["lib/game/game_background.dart"]
        self.assertIn("_drawTorchGlow", content)

    def test_game_background_has_animated_particles(self):
        content = self.files["lib/game/game_background.dart"]
        self.assertIn("_Particle", content)
        self.assertIn("_drawParticles", content)

    def test_game_background_priority_negative(self):
        """Background must be rendered before all other components."""
        content = self.files["lib/game/game_background.dart"]
        self.assertIn("priority: -10", content)

    # ── game.dart – MP + skill system ────────────────────────────────────────

    def test_game_dart_uses_game_background(self):
        content = self.files["lib/game/game.dart"]
        self.assertIn("GameBackground", content)
        self.assertIn("game_background.dart", content)

    def test_game_dart_no_longer_uses_plain_rectangle_background(self):
        content = self.files["lib/game/game.dart"]
        self.assertNotIn(
            "RectangleComponent(size: size",
            content,
            "Background should be GameBackground, not a plain RectangleComponent",
        )

    def test_game_dart_has_skill_type_enum(self):
        content = self.files["lib/game/game.dart"]
        self.assertIn("enum SkillType", content)
        self.assertIn("fireStrike", content)
        self.assertIn("guard", content)
        self.assertIn("heal", content)

    def test_game_dart_has_mp_fields(self):
        content = self.files["lib/game/game.dart"]
        self.assertIn("int mp = 100;", content)
        self.assertIn("int maxMp = 100;", content)

    def test_game_dart_has_guard_fields(self):
        content = self.files["lib/game/game.dart"]
        self.assertIn("bool isGuardActive = false;", content)
        self.assertIn("_guardTimer", content)

    def test_game_dart_has_skill_activation_method(self):
        content = self.files["lib/game/game.dart"]
        self.assertIn("onActivateSkill", content)

    def test_game_dart_has_tap_skill_attack_method(self):
        content = self.files["lib/game/game.dart"]
        self.assertIn("onTapSkillAttack", content)

    def test_game_dart_has_mp_regen_in_update(self):
        content = self.files["lib/game/game.dart"]
        self.assertIn("mp + dt * 5", content)

    def test_game_dart_guard_reduces_damage(self):
        content = self.files["lib/game/game.dart"]
        self.assertIn("isGuardActive ? (amount * 0.5)", content)

    # ── hero.dart – armored knight sprite ────────────────────────────────────

    def test_hero_dart_has_knight_helmet(self):
        content = self.files["lib/game/hero.dart"]
        self.assertIn("helmPath", content)

    def test_hero_dart_has_visor_glow(self):
        content = self.files["lib/game/hero.dart"]
        # Blue visor colour
        self.assertIn("0xFF00AAFF", content)

    def test_hero_dart_has_golden_sword(self):
        content = self.files["lib/game/hero.dart"]
        self.assertIn("0xFFD4AA00", content)

    def test_hero_dart_has_pauldrons(self):
        content = self.files["lib/game/hero.dart"]
        self.assertIn("pauldron", content.lower())

    def test_hero_dart_has_attack_aura(self):
        """Hero should show a glowing aura when attacking (_isFlashing)."""
        content = self.files["lib/game/hero.dart"]
        self.assertIn("_isFlashing", content)
        self.assertIn("RadialGradient", content)

    def test_hero_dart_has_shadow(self):
        content = self.files["lib/game/hero.dart"]
        self.assertIn("drawOval", content)

    # ── enemy.dart – dark demon sprite ────────────────────────────────────────

    def test_enemy_dart_is_position_component(self):
        content = self.files["lib/game/enemy.dart"]
        self.assertIn("PositionComponent", content)
        self.assertNotIn("RectangleComponent", content)

    def test_enemy_dart_has_render_minion(self):
        content = self.files["lib/game/enemy.dart"]
        self.assertIn("_renderMinion", content)

    def test_enemy_dart_has_render_boss(self):
        content = self.files["lib/game/enemy.dart"]
        self.assertIn("_renderBoss", content)

    def test_enemy_dart_has_horns(self):
        content = self.files["lib/game/enemy.dart"]
        self.assertIn("horn", content.lower())

    def test_enemy_dart_has_glowing_red_eyes(self):
        content = self.files["lib/game/enemy.dart"]
        self.assertIn("0xFFFF2200", content)
        self.assertIn("maskFilter", content)

    def test_enemy_dart_boss_has_crown(self):
        content = self.files["lib/game/enemy.dart"]
        self.assertIn("crown", content.lower())

    def test_enemy_dart_boss_has_wings(self):
        content = self.files["lib/game/enemy.dart"]
        self.assertIn("wing", content.lower())

    def test_enemy_dart_has_animated_eyes(self):
        """Enemy eyes should pulse using time-based animation."""
        content = self.files["lib/game/enemy.dart"]
        self.assertIn("_time", content)

    # ── hud.dart – MU Online-style HUD ───────────────────────────────────────

    def test_hud_has_mu_online_top_bar(self):
        content = self.files["lib/game/hud.dart"]
        self.assertIn("_drawTopBar", content)

    def test_hud_has_minimap(self):
        content = self.files["lib/game/hud.dart"]
        self.assertIn("_drawMinimap", content)

    def test_hud_minimap_shows_hero_dot(self):
        content = self.files["lib/game/hud.dart"]
        self.assertIn("0xFF00AAFF", content)  # hero dot blue

    def test_hud_minimap_shows_enemy_dot(self):
        content = self.files["lib/game/hud.dart"]
        self.assertIn("0xFFFF2200", content)  # enemy dot red

    def test_hud_has_red_hp_bar(self):
        content = self.files["lib/game/hud.dart"]
        self.assertIn("0xFFCC0000", content)

    def test_hud_has_blue_mp_bar(self):
        content = self.files["lib/game/hud.dart"]
        self.assertIn("0xFF0044CC", content)
        self.assertIn("g.mp", content)

    def test_hud_has_purple_xp_bar(self):
        content = self.files["lib/game/hud.dart"]
        self.assertIn("0xFF7722CC", content)

    def test_hud_bars_have_glow_effect(self):
        content = self.files["lib/game/hud.dart"]
        self.assertIn("MaskFilter.blur", content)

    def test_hud_shows_guard_indicator(self):
        content = self.files["lib/game/hud.dart"]
        self.assertIn("isGuardActive", content)

    # ── skill_hotbar.dart ─────────────────────────────────────────────────────

    def test_skill_hotbar_has_four_skills(self):
        content = self.files["lib/widgets/skill_hotbar.dart"]
        for skill in ["Strike", "Fire", "Guard", "Heal"]:
            self.assertIn(skill, content)

    def test_skill_hotbar_has_cooldown_overlay(self):
        content = self.files["lib/widgets/skill_hotbar.dart"]
        self.assertIn("cooldown", content.lower())
        self.assertIn("AnimationController", content)

    def test_skill_hotbar_has_mp_costs(self):
        content = self.files["lib/widgets/skill_hotbar.dart"]
        self.assertIn("mpCost", content)
        self.assertIn("MP", content)

    def test_skill_hotbar_calls_game_methods(self):
        content = self.files["lib/widgets/skill_hotbar.dart"]
        self.assertIn("SkillType.fireStrike", content)
        self.assertIn("SkillType.guard", content)
        self.assertIn("SkillType.heal", content)
        self.assertIn("onTapSkillAttack", content)

    def test_skill_hotbar_has_gold_border_styling(self):
        content = self.files["lib/widgets/skill_hotbar.dart"]
        self.assertIn("B8860B", content)

    # ── main.dart – MU Online theme ───────────────────────────────────────────

    def test_main_dart_imports_skill_hotbar(self):
        content = self.files["lib/main.dart"]
        self.assertIn("skill_hotbar.dart", content)
        self.assertIn("SkillHotbar", content)

    def test_main_dart_embeds_skill_hotbar_in_battle_tab(self):
        content = self.files["lib/main.dart"]
        self.assertIn("SkillHotbar(game: _game)", content)

    def test_main_dart_has_mu_online_theme_data(self):
        content = self.files["lib/main.dart"]
        self.assertIn("ThemeData(", content)
        # Gold colour
        self.assertIn("D4A017", content)

    def test_main_dart_has_dark_nav_bar(self):
        content = self.files["lib/main.dart"]
        self.assertIn("06041A", content)

    def test_main_dart_battle_tab_uses_column_for_skill_hotbar(self):
        """Battle tab should use Column so SkillHotbar sits below game canvas."""
        content = self.files["lib/main.dart"]
        self.assertIn("Column(", content)

    def test_main_dart_still_has_eight_nav_items(self):
        content = self.files["lib/main.dart"]
        self.assertEqual(content.count("BottomNavigationBarItem"), 8)


if __name__ == "__main__":
    unittest.main()
