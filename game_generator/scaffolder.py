"""
scaffolder.py – Flutter/Flame project scaffolder.

Given a GameSpec and the genre-specific Dart files, produces a complete
dict of {relative_path: file_content} representing the full Flutter project.
"""

from __future__ import annotations

import os
import string
from pathlib import Path
from typing import Dict, List

from .spec import GameSpec
from .genres import get_genre_plugin

# Directory that contains the Markdown skeleton templates.
_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "flutter"

# Required files that every generated project must contain.
REQUIRED_FILES = {
    "pubspec.yaml",
    "lib/main.dart",
    "README.md",
    "ASSETS_LICENSE.md",
    "CREDITS.md",
}


def scaffold_project(
    spec: GameSpec,
    imported_asset_paths: List[str] | None = None,
) -> Dict[str, str]:
    """
    Build a complete Flutter/Flame project file tree.

    Args:
        spec:                 GameSpec dict (from spec.generate_spec).
        imported_asset_paths: List of asset paths relative to the project root
                              that were copied from the user's assets folder,
                              e.g. ``["assets/imported/player.png", ...]``.

    Returns:
        dict mapping relative file path -> file content (str).
    """
    imported_asset_paths = imported_asset_paths or []

    files: Dict[str, str] = {}

    # 1. Genre-specific Dart game files
    plugin = get_genre_plugin(spec["genre"])
    files.update(plugin(spec))

    # Derive the main game class name from genre files
    game_class = _infer_game_class(spec)

    # 2. main.dart  (only when the genre plugin did not already provide one)
    if "lib/main.dart" not in files:
        files["lib/main.dart"] = _main_dart(spec, game_class)

    # Collect asset paths that the genre plugin generated (e.g. assets/data/*.json)
    generated_asset_paths = [p for p in files if p.startswith("assets/")]

    # 3. pubspec.yaml
    files["pubspec.yaml"] = _pubspec_yaml(spec, imported_asset_paths, generated_asset_paths)

    # 4. README.md  (loaded from template)
    files["README.md"] = _readme_md(spec)

    # 5. ASSETS_LICENSE.md  (loaded from template)
    files["ASSETS_LICENSE.md"] = _assets_license_md(spec)

    # 6. CREDITS.md  (loaded from template)
    files["CREDITS.md"] = _credits_md(spec)

    # 7. Android manifest  (required for mobile play)
    files["android/app/src/main/AndroidManifest.xml"] = _android_manifest(spec)

    # 8. Android build files (required to build/run on Android)
    pkg = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in spec.get("title", "my_game").lower()).strip("_") or "my_game"
    files["android/build.gradle"] = _android_root_build_gradle()
    files["android/app/build.gradle"] = _android_app_build_gradle(pkg)
    files["android/settings.gradle"] = _android_settings_gradle(pkg)
    files["android/gradle.properties"] = _android_gradle_properties()
    files["android/gradle/wrapper/gradle-wrapper.properties"] = _gradle_wrapper_properties()
    files[f"android/app/src/main/kotlin/com/example/{pkg}/MainActivity.kt"] = _main_activity_kt(pkg)
    files["android/app/src/main/res/values/styles.xml"] = _android_styles_xml()
    files["android/app/src/main/res/drawable/launch_background.xml"] = _android_launch_background_xml()
    files["android/app/src/main/res/mipmap-hdpi/ic_launcher.png"] = ""
    files["android/app/src/debug/AndroidManifest.xml"] = _android_debug_manifest()

    # 9. iOS Info.plist  (required for iOS builds)
    files["ios/Runner/Info.plist"] = _ios_info_plist(spec)

    return files


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _infer_game_class(spec: GameSpec) -> str:
    """Derive the Flame game class name from the spec title."""
    title = spec.get("title", "MyGame")
    words = "".join(ch if ch.isalnum() or ch == " " else " " for ch in title).split()
    base = "".join(w.capitalize() for w in words) if words else "MyGame"
    return f"{base}Game"


def _main_dart(spec: GameSpec, game_class: str) -> str:
    title = spec.get("title", "My Game")
    orientation = spec.get("orientation", "portrait")
    if orientation == "landscape":
        orient_values = (
            "DeviceOrientation.landscapeLeft,\n"
            "    DeviceOrientation.landscapeRight,"
        )
    else:
        orient_values = (
            "DeviceOrientation.portraitUp,\n"
            "    DeviceOrientation.portraitDown,"
        )
    return f"""\
import 'package:flame/game.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'game/game.dart';

void main() async {{
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations([
    {orient_values}
  ]);
  runApp(const {game_class}App());
}}

class {game_class}App extends StatelessWidget {{
  const {game_class}App({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{title}',
      debugShowCheckedModeBanner: false,
      home: Scaffold(
        backgroundColor: Colors.black,
        body: GameWidget<{game_class}>(
          game: {game_class}(),
          loadingBuilder: (context) => const Center(
            child: CircularProgressIndicator(),
          ),
        ),
      ),
    );
  }}
}}
"""


def _pubspec_yaml(spec: GameSpec, asset_paths: List[str], generated_asset_paths: List[str] | None = None) -> str:
    title = spec.get("title", "my_game")
    # package name: lowercase, underscores
    pkg = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in title.lower()).strip("_")
    pkg = pkg or "my_game"

    # Merge imported + generated asset paths
    all_paths: List[str] = list(asset_paths or [])
    if generated_asset_paths:
        all_paths.extend(p for p in generated_asset_paths if p not in all_paths)

    asset_lines = ""
    if all_paths:
        # Always include assets/imported/ so Flame sprites are resolvable
        if not any(p == "assets/imported/" or p.startswith("assets/imported/") for p in all_paths):
            all_paths = ["assets/imported/"] + sorted(all_paths)
        else:
            all_paths = sorted(all_paths)
        lines = "\n".join(f"    - {p}" for p in all_paths)
        asset_lines = f"\n  assets:\n{lines}\n"
    else:
        asset_lines = "\n  assets:\n    - assets/imported/\n"

    return f"""\
name: {pkg}
description: A Flutter/Flame game generated by Aibase.
version: 1.0.0+1
publish_to: 'none'

environment:
  sdk: '>=3.0.0 <4.0.0'
  flutter: '>=3.10.0'

dependencies:
  flutter:
    sdk: flutter
  flame: ^1.18.0
  shared_preferences: ^2.2.0

flutter:
  uses-material-design: true
{asset_lines}
"""


def _load_template(name: str) -> str:
    """Load a skeleton template from templates/flutter/. Returns None if missing."""
    path = _TEMPLATES_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def _render_template(name: str, **kwargs) -> str:
    """
    Load a template and substitute $VAR placeholders.

    Uses ``string.Template`` so ``$title``, ``$genre``, etc. are replaced.
    Literal ``$`` signs in the template must be written as ``$$``.
    Falls back to the *fallback* kwarg (a string) if the template file is missing.
    """
    fallback = kwargs.pop("_fallback", "")
    raw = _load_template(name)
    if raw is None:
        return fallback
    return string.Template(raw).safe_substitute(kwargs)


def _readme_md(spec: GameSpec) -> str:
    controls = spec.get("controls", {})
    mechanics = spec.get("mechanics", [])
    return _render_template(
        "README.md.tmpl",
        title=spec.get("title", "My Game"),
        genre=spec.get("genre", "unknown"),
        core_loop=spec.get("core_loop", ""),
        mechanics=", ".join(mechanics),
        kb=", ".join(controls.get("keyboard", [])),
        mobile=", ".join(controls.get("mobile", [])),
        orientation=spec.get("orientation", "portrait"),
        _fallback=_readme_md_fallback(spec),
    )


def _readme_md_fallback(spec: GameSpec) -> str:
    title = spec.get("title", "My Game")
    genre = spec.get("genre", "unknown")
    mechanics = ", ".join(spec.get("mechanics", []))
    controls = spec.get("controls", {})
    kb = ", ".join(controls.get("keyboard", []))
    mobile = ", ".join(controls.get("mobile", []))
    return f"""\
# {title}

Generated by **Aibase** – Flutter/Flame Game Generator.

## Genre
`{genre}`

## Mechanics
{mechanics}

## Controls
- **Keyboard / Desktop**: {kb}
- **Mobile**: {mobile}

## Prerequisites
- [Flutter SDK](https://docs.flutter.dev/get-started/install) ≥ 3.10
- Run `flutter pub get` before building.

## Getting Started
```bash
flutter pub get
flutter run
```

## Asset Licensing
See [ASSETS_LICENSE.md](ASSETS_LICENSE.md) and [CREDITS.md](CREDITS.md).
"""


def _assets_license_md(spec: GameSpec) -> str:
    return _render_template(
        "ASSETS_LICENSE.md.tmpl",
        title=spec.get("title", "My Game"),
        _fallback=_assets_license_md_fallback(spec),
    )


def _assets_license_md_fallback(spec: GameSpec) -> str:
    title = spec.get("title", "My Game")
    return f"""\
# Asset Licensing – {title}

The assets in `assets/imported/` were supplied by the user from a local
folder at project generation time.  **Aibase does not redistribute these assets.**

## Your Responsibilities
- Ensure you hold the appropriate licence for every asset file included here.
- If assets originate from a third-party, consult the relevant licence file
  before distributing your game.
- Aibase does **not** automatically download assets from any online storefront.

## Placeholder Assets
If Aibase could not find a matching asset it may have generated a coloured
rectangle placeholder in code.  Replace these before publishing.
"""


def _credits_md(spec: GameSpec) -> str:
    assets_dir = spec.get("assets_dir", "")
    if assets_dir:
        assets_source_note = f"Assets were imported from: `{assets_dir}`"
    else:
        assets_source_note = (
            "No --assets-dir was supplied; assets/imported/ contains placeholders."
        )
    return _render_template(
        "CREDITS.md.tmpl",
        title=spec.get("title", "My Game"),
        assets_source_note=assets_source_note,
        _fallback=_credits_md_fallback(spec, assets_source_note),
    )


def _credits_md_fallback(spec: GameSpec, assets_source_note: str) -> str:
    title = spec.get("title", "My Game")
    return f"""\
# Credits – {title}

Generated by **Aibase** – Flutter/Flame Game Generator.

## Assets
{assets_source_note}

## Third-Party Libraries
| Package | Version | Licence |
|---------|---------|---------|
| flame   | ^1.18.0 | MIT     |
| flutter | SDK     | BSD-3-Clause |

## Your Responsibilities
Ensure you hold the appropriate licence for every asset in this project.
"""


def _android_manifest(spec: GameSpec) -> str:
    orientation = spec.get("orientation", "portrait")
    android_orient = (
        "sensorLandscape" if orientation == "landscape" else "sensorPortrait"
    )
    title = spec.get("title", "My Game")
    pkg_label = "".join(
        ch if ch.isalnum() or ch == "_" else "_" for ch in title.lower()
    ).strip("_") or "my_game"
    return f"""\
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:label="{pkg_label}"
        android:name="${{applicationName}}"
        android:icon="@mipmap/ic_launcher">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:screenOrientation="{android_orient}"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:hardwareAccelerated="true"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
        <meta-data
            android:name="flutterEmbedding"
            android:value="2" />
    </application>
</manifest>
"""


def _ios_info_plist(spec: GameSpec) -> str:
    orientation = spec.get("orientation", "portrait")
    title = spec.get("title", "My Game")
    if orientation == "landscape":
        supported = """\
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>"""
    else:
        supported = """\
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationPortraitUpsideDown</string>"""
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{title}</string>
    <key>CFBundleIdentifier</key>
    <string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>UILaunchStoryboardName</key>
    <string>LaunchScreen</string>
    <key>UISupportedInterfaceOrientations</key>
    <array>
{supported}
    </array>
    <key>io.flutter.embedded_views_preview</key>
    <true/>
</dict>
</plist>
"""


# ---------------------------------------------------------------------------
# Android build helpers
# ---------------------------------------------------------------------------

def _android_root_build_gradle() -> str:
    return """\
buildscript {
    ext.kotlin_version = '1.9.0'
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.1.0'
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.buildDir = '../build'
subprojects {
    project.buildDir = "${rootProject.buildDir}/${project.name}"
}
subprojects {
    project.evaluationDependsOn(':app')
}

tasks.register("clean", Delete) {
    delete rootProject.buildDir
}
"""


def _android_app_build_gradle(pkg: str) -> str:
    return f"""\
def localProperties = new Properties()
def localPropertiesFile = rootProject.file('local.properties')
if (localPropertiesFile.exists()) {{
    localPropertiesFile.withReader('UTF-8') {{ reader ->
        localProperties.load(reader)
    }}
}}

def flutterRoot = localProperties.getProperty('flutter.sdk')
if (flutterRoot == null) {{
    throw new GradleException("Flutter SDK not found. Define location with flutter.sdk in the local.properties file.")
}}

def flutterVersionCode = localProperties.getProperty('flutter.versionCode')
if (flutterVersionCode == null) {{
    flutterVersionCode = '1'
}}

def flutterVersionName = localProperties.getProperty('flutter.versionName')
if (flutterVersionName == null) {{
    flutterVersionName = '1.0'
}}

apply plugin: 'com.android.application'
apply plugin: 'kotlin-android'
apply from: "$flutterRoot/packages/flutter_tools/gradle/flutter.gradle"

android {{
    namespace 'com.example.{pkg}'
    compileSdkVersion 34
    ndkVersion flutter.ndkVersion

    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }}

    kotlinOptions {{
        jvmTarget = '1.8'
    }}

    sourceSets {{
        main.java.srcDirs += 'src/main/kotlin'
    }}

    defaultConfig {{
        applicationId "com.example.{pkg}"
        minSdkVersion flutter.minSdkVersion
        targetSdkVersion flutter.targetSdkVersion
        versionCode flutterVersionCode.toInteger()
        versionName flutterVersionName
    }}

    buildTypes {{
        release {{
            signingConfig signingConfigs.debug
        }}
    }}
}}

flutter {{
    source '../..'
}}

dependencies {{
    implementation "org.jetbrains.kotlin:kotlin-stdlib-jdk7:$kotlin_version"
}}
"""


def _android_settings_gradle(pkg: str) -> str:
    return f"""\
include ':app'

def localPropertiesFile = new File(rootProject.projectDir, "local.properties")
def properties = new Properties()

assert localPropertiesFile.exists()
localPropertiesFile.withReader("UTF-8") {{ reader -> properties.load(reader) }}

def flutterSdkPath = properties.getProperty("flutter.sdk")
assert flutterSdkPath != null, "flutter.sdk not set in local.properties"
apply from: "${{flutterSdkPath}}/packages/flutter_tools/gradle/app_plugin_loader.gradle"
"""


def _android_gradle_properties() -> str:
    return """\
org.gradle.jvmargs=-Xmx4G -XX:MaxMetaspaceSize=2G -XX:+HeapDumpOnOutOfMemoryError
android.useAndroidX=true
android.enableJetifier=true
"""


def _gradle_wrapper_properties() -> str:
    return """\
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.3-bin.zip
"""


def _main_activity_kt(pkg: str) -> str:
    return f"""\
package com.example.{pkg}

import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity()
"""


def _android_styles_xml() -> str:
    return """\
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="LaunchTheme" parent="@android:style/Theme.Black.NoTitleBar">
        <item name="android:windowBackground">@drawable/launch_background</item>
    </style>
    <style name="NormalTheme" parent="@android:style/Theme.Black.NoTitleBar">
        <item name="android:windowBackground">?android:colorBackground</item>
    </style>
</resources>
"""


def _android_launch_background_xml() -> str:
    return """\
<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@android:color/black" />
</layer-list>
"""


def _android_debug_manifest() -> str:
    return """\
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET"/>
</manifest>
"""
