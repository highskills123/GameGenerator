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
    files["android/app/src/main/res/values-night/styles.xml"] = _android_styles_night_xml()
    files["android/app/src/main/res/drawable/launch_background.xml"] = _android_launch_background_xml()
    # Launcher icon placeholder stubs for all standard mipmap densities
    for density in ("mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"):
        files[f"android/app/src/main/res/mipmap-{density}/ic_launcher.png"] = ""
    files["android/app/src/debug/AndroidManifest.xml"] = _android_debug_manifest()

    # 9. iOS scaffold  (required for flutter run on iOS)
    bundle_id = f"com.example.{pkg}"
    files["ios/Runner/Info.plist"] = _ios_info_plist(spec)
    files["ios/Runner/AppDelegate.swift"] = _ios_app_delegate_swift()
    files["ios/Runner/Runner-Bridging-Header.h"] = _ios_bridging_header()
    files["ios/Podfile"] = _ios_podfile(pkg)
    files["ios/Runner/Base.lproj/LaunchScreen.storyboard"] = _ios_launch_screen_storyboard()
    files["ios/Runner/Base.lproj/Main.storyboard"] = _ios_main_storyboard()
    files["ios/Runner/Assets.xcassets/Contents.json"] = _ios_assets_contents_json()
    files["ios/Runner/Assets.xcassets/AppIcon.appiconset/Contents.json"] = _ios_app_icon_contents_json()
    files["ios/Runner.xcworkspace/contents.xcworkspacedata"] = _ios_xcworkspace(pkg)
    files["ios/Runner.xcodeproj/project.pbxproj"] = _ios_pbxproj(pkg, bundle_id)

    # 10. Developer-experience files
    files["analysis_options.yaml"] = _analysis_options_yaml()
    files[".gitignore"] = _flutter_gitignore()
    files["QUICKSTART.md"] = _quickstart_md(spec, pkg)

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

    is_idle_rpg = spec.get("genre") == "idle_rpg"
    extra_deps = ""
    if is_idle_rpg:
        extra_deps = """\
  in_app_purchase: ^3.1.11
  google_mobile_ads: ^4.0.0
"""

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
{extra_deps}
dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

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
    is_idle_rpg = spec.get("genre") == "idle_rpg"
    # For idle RPG: INTERNET (ads) and BILLING (IAP) permissions + AdMob app ID.
    # Replace the test AdMob app ID before publishing.
    extra_permissions = ""
    admob_meta = ""
    permissions_block = ""
    if is_idle_rpg:
        permissions_block = """\
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="com.android.vending.BILLING"/>
"""
        admob_meta = """\
        <meta-data
            android:name="com.google.android.gms.ads.APPLICATION_ID"
            android:value="ca-app-pub-3940256099942544~3347511713"/>
"""
    # Build application opening tag with correct indentation
    app_open = f"{permissions_block}    <application" if permissions_block else "    <application"
    return f"""\
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
{app_open}
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
{admob_meta}    </application>
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


def _android_styles_night_xml() -> str:
    """Dark-mode override – identical colours since the game already uses a dark theme."""
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


def _ios_app_delegate_swift() -> str:
    return """\
import UIKit
import Flutter

@UIApplicationMain
@objc class AppDelegate: FlutterAppDelegate {
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    GeneratedPluginRegistrant.register(with: self)
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }
}
"""


def _ios_bridging_header() -> str:
    return """\
// Runner-Bridging-Header.h
// Auto-generated by Flutter – do not edit manually.
// No Objective-C bridging is needed for this project.
"""


def _ios_podfile(pkg: str) -> str:
    return f"""\
# Podfile – CocoaPods integration for Flutter iOS plugins.
# Run `cd ios && pod install` before opening the Xcode workspace.

platform :ios, '13.0'

ENV['COCOAPODS_DISABLE_STATS'] = 'true'

project 'Runner', {{
  'Debug'   => :debug,
  'Profile' => :release,
  'Release' => :release,
}}

def flutter_root
  generated_xcode_build_settings_path = File.expand_path(
    File.join('..', 'Flutter', 'Generated.xcconfig'), __FILE__
  )
  unless File.exist?(generated_xcode_build_settings_path)
    raise "Generated.xcconfig must exist. Run: flutter pub get"
  end
  File.foreach(generated_xcode_build_settings_path) do |line|
    matches = line.match(/FLUTTER_ROOT\\=(.*)/)
    return matches[1].strip if matches
  end
  raise "FLUTTER_ROOT not found in Generated.xcconfig"
end

require File.expand_path(File.join('packages', 'flutter_tools', 'bin', 'podhelper'), flutter_root)

flutter_ios_podfile_setup

target 'Runner' do
  use_frameworks!
  use_modular_headers!

  flutter_install_all_ios_pods File.dirname(File.realpath(__FILE__))

  target 'RunnerTests' do
    inherit! :search_paths
  end
end

post_install do |installer|
  installer.pods_project.targets.each do |target|
    flutter_additional_ios_build_settings(target)
  end
end
"""


def _ios_launch_screen_storyboard() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB"
          version="3.0" toolsVersion="32700.99.1234"
          targetRuntime="AppleCocoa" propertyAccessControl="none"
          useAutolayout="YES" launchScreen="YES"
          useTraitCollections="YES" useSafeAreas="YES"
          colorMatched="YES" initialViewController="01J-lp-oVM">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <deployment identifier="iOS"/>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22685"/>
        <capability name="Safe area layout guides" minToolsVersion="9.0"/>
        <capability name="documents saved in the Xcode 8 format" minToolsVersion="8.0"/>
    </dependencies>
    <scenes>
        <scene sceneID="EHf-IW-A2E">
            <objects>
                <viewController id="01J-lp-oVM" sceneMemberID="viewController">
                    <view key="view" contentMode="scaleToFill" id="Ze5-6b-2t3">
                        <rect key="frame" x="0.0" y="0.0" width="393" height="852"/>
                        <autoresizingMask key="autoresizingMask"
                                         widthSizable="YES" heightSizable="YES"/>
                        <subviews>
                            <label opaque="NO" userInteractionEnabled="NO"
                                   contentMode="left"
                                   text="Idle RPG" textAlignment="center"
                                   numberOfLines="1"
                                   translatesAutoresizingMaskIntoConstraints="NO"
                                   id="GJd-Yh-RWb">
                                <rect key="frame" x="0.0" y="0.0" width="393" height="852"/>
                                <fontDescription key="fontDescription" type="boldSystem"
                                                 pointSize="28"/>
                                <color key="textColor" white="1" alpha="1"
                                       colorSpace="custom"
                                       customColorSpace="genericGamma22GrayColorSpace"/>
                                <nil key="highlightedColor"/>
                            </label>
                        </subviews>
                        <viewLayoutGuide key="safeAreaLayoutGuide" id="Bcu-3y-fUS"/>
                        <color key="backgroundColor" red="0.1" green="0.1" blue="0.18"
                               alpha="1" colorSpace="custom" customColorSpace="sRGB"/>
                        <constraints>
                            <constraint firstItem="GJd-Yh-RWb" firstAttribute="centerY"
                                        secondItem="Ze5-6b-2t3" secondAttribute="centerY"
                                        id="moa-c2-u7t"/>
                            <constraint firstItem="GJd-Yh-RWb" firstAttribute="leading"
                                        secondItem="Ze5-6b-2t3" secondAttribute="leading"
                                        id="4c0-rL-fzv"/>
                            <constraint firstItem="GJd-Yh-RWb" firstAttribute="trailing"
                                        secondItem="Ze5-6b-2t3" secondAttribute="trailing"
                                        id="WGF-zD-mAl"/>
                        </constraints>
                    </view>
                </viewController>
                <placeholder placeholderIdentifier="IBFirstResponder" id="iYj-Kq-Ea1"
                             userLabel="First Responder" sceneMemberID="firstResponder"/>
            </objects>
            <point key="canvasLocation" x="53" y="375"/>
        </scene>
    </scenes>
</document>
"""


def _ios_main_storyboard() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB"
          version="3.0" toolsVersion="32700.99.1234"
          targetRuntime="AppleCocoa" propertyAccessControl="none"
          useAutolayout="YES" useTraitCollections="YES"
          useSafeAreas="YES" colorMatched="YES"
          initialViewController="BYZ-38-t0r">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <deployment identifier="iOS"/>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22685"/>
        <capability name="Safe area layout guides" minToolsVersion="9.0"/>
        <capability name="documents saved in the Xcode 8 format" minToolsVersion="8.0"/>
    </dependencies>
    <scenes>
        <scene sceneID="tne-QT-ifu">
            <objects>
                <viewController id="BYZ-38-t0r"
                                customClass="FlutterViewController"
                                customModule="Flutter"
                                customModuleProvider="target"
                                sceneMemberID="viewController">
                    <layoutGuides>
                        <viewControllerLayoutGuide type="top"    id="y3c-jy-aDJ"/>
                        <viewControllerLayoutGuide type="bottom" id="wfy-db-euE"/>
                    </layoutGuides>
                    <view key="view" contentMode="scaleToFill" id="8bC-Xf-vdC">
                        <rect key="frame" x="0.0" y="0.0" width="393" height="852"/>
                        <autoresizingMask key="autoresizingMask"
                                         widthSizable="YES" heightSizable="YES"/>
                        <color key="backgroundColor" systemColor="systemBackgroundColor"/>
                        <viewLayoutGuide key="safeAreaLayoutGuide" id="H2P-sc-9uM"/>
                    </view>
                </viewController>
                <placeholder placeholderIdentifier="IBFirstResponder" id="dkx-z0-nzr"
                             userLabel="First Responder" sceneMemberID="firstResponder"/>
            </objects>
            <point key="canvasLocation" x="53" y="375"/>
        </scene>
    </scenes>
</document>
"""


def _ios_assets_contents_json() -> str:
    return """\
{
  "info" : {
    "version" : 1,
    "author" : "xcode"
  }
}
"""


def _ios_app_icon_contents_json() -> str:
    """Minimal AppIcon.appiconset/Contents.json – single universal 1024x1024 entry."""
    return """\
{
  "images" : [
    {
      "idiom"    : "universal",
      "platform" : "ios",
      "size"     : "1024x1024"
    }
  ],
  "info" : {
    "author"  : "xcode",
    "version" : 1
  }
}
"""


def _ios_xcworkspace(pkg: str) -> str:
    return """\
<?xml version="1.0" encoding="UTF-8"?>
<Workspace
   version = "1.0">
   <FileRef
      location = "group:Runner.xcodeproj">
   </FileRef>
   <FileRef
      location = "group:Pods/Pods.xcodeproj">
   </FileRef>
</Workspace>
"""


def _ios_pbxproj(pkg: str, bundle_id: str) -> str:
    """
    Minimal but functional Xcode project file for a Flutter iOS app.
    UUIDs are deterministically derived from the package name so the file is
    stable across regenerations with the same spec.
    """
    import hashlib

    def _uid(label: str) -> str:
        return hashlib.md5(f"{pkg}:{label}".encode()).hexdigest()[:24].upper()

    proj      = _uid("project")
    app_tgt   = _uid("app_target")
    sources   = _uid("sources_phase")
    res       = _uid("resources_phase")
    fwk       = _uid("frameworks_phase")
    main_sb   = _uid("main_storyboard")
    launch_sb = _uid("launch_storyboard")
    info_p    = _uid("info_plist")
    appd_sw   = _uid("appdelegate_swift")
    brg_h     = _uid("bridging_header")
    assets_xc = _uid("assets_xcassets")
    grp_root  = _uid("group_root")
    grp_run   = _uid("group_runner")
    cfg_dbg   = _uid("cfg_debug")
    cfg_rel   = _uid("cfg_release")
    xclist    = _uid("xcconfig_list")
    xclist_p  = _uid("xcconfig_list_proj")
    flutter_f = _uid("flutter_framework")
    tgt_dbg   = _uid("tgt_debug")
    tgt_rel   = _uid("tgt_release")
    dbg_xcfg  = _uid("flutter_debug_xcconfig")
    rel_xcfg  = _uid("flutter_release_xcconfig")

    return f"""\
// !$*UTF8*$!
{{
\tarchiveVersion = 1;
\tclasses = {{
\t}};
\tobjectVersion = 56;
\tobjects = {{

/* Begin PBXBuildFile section */
\t\t{appd_sw}AA /* AppDelegate.swift in Sources */ = {{isa = PBXBuildFile; fileRef = {appd_sw}BB /* AppDelegate.swift */; }};
\t\t{main_sb}AA /* Main.storyboard in Resources */ = {{isa = PBXBuildFile; fileRef = {main_sb}BB /* Main.storyboard */; }};
\t\t{assets_xc}AA /* Assets.xcassets in Resources */ = {{isa = PBXBuildFile; fileRef = {assets_xc}BB /* Assets.xcassets */; }};
\t\t{launch_sb}AA /* LaunchScreen.storyboard in Resources */ = {{isa = PBXBuildFile; fileRef = {launch_sb}BB /* LaunchScreen.storyboard */; }};
\t\t{flutter_f}AA /* Flutter.framework in Frameworks */ = {{isa = PBXBuildFile; fileRef = {flutter_f}BB /* Flutter.framework */; }};
/* End PBXBuildFile section */

/* Begin PBXFileReference section */
\t\t{appd_sw}BB /* AppDelegate.swift */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = AppDelegate.swift; sourceTree = "<group>"; }};
\t\t{main_sb}BB /* Main.storyboard */ = {{isa = PBXFileReference; lastKnownFileType = file.storyboard; name = Main.storyboard; path = Base.lproj/Main.storyboard; sourceTree = "<group>"; }};
\t\t{assets_xc}BB /* Assets.xcassets */ = {{isa = PBXFileReference; lastKnownFileType = folder.assetcatalog; path = Assets.xcassets; sourceTree = "<group>"; }};
\t\t{launch_sb}BB /* LaunchScreen.storyboard */ = {{isa = PBXFileReference; lastKnownFileType = file.storyboard; name = LaunchScreen.storyboard; path = Base.lproj/LaunchScreen.storyboard; sourceTree = "<group>"; }};
\t\t{info_p}00 /* Info.plist */ = {{isa = PBXFileReference; lastKnownFileType = text.plist.xml; path = Info.plist; sourceTree = "<group>"; }};
\t\t{brg_h}00 /* Runner-Bridging-Header.h */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.c.h; path = "Runner-Bridging-Header.h"; sourceTree = "<group>"; }};
\t\t{flutter_f}BB /* Flutter.framework */ = {{isa = PBXFileReference; lastKnownFileType = wrapper.framework; name = Flutter.framework; path = Flutter/Flutter.framework; sourceTree = "<group>"; }};
\t\t{app_tgt}PP /* Runner.app */ = {{isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = Runner.app; sourceTree = BUILT_PRODUCTS_DIR; }};
/* End PBXFileReference section */

/* Begin PBXFrameworksBuildPhase section */
\t\t{fwk} /* Frameworks */ = {{
\t\t\tisa = PBXFrameworksBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
\t\t\t\t{flutter_f}AA /* Flutter.framework in Frameworks */,
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t}};
/* End PBXFrameworksBuildPhase section */

/* Begin PBXGroup section */
\t\t{grp_root} = {{
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
\t\t\t\t{grp_run} /* Runner */,
\t\t\t\t{flutter_f}BB /* Flutter.framework */,
\t\t\t\t{app_tgt}PP /* Runner.app */,
\t\t\t);
\t\t\tsourceTree = "<group>";
\t\t}};
\t\t{grp_run} /* Runner */ = {{
\t\t\tisa = PBXGroup;
\t\t\tchildren = (
\t\t\t\t{appd_sw}BB /* AppDelegate.swift */,
\t\t\t\t{main_sb}BB /* Main.storyboard */,
\t\t\t\t{assets_xc}BB /* Assets.xcassets */,
\t\t\t\t{launch_sb}BB /* LaunchScreen.storyboard */,
\t\t\t\t{info_p}00 /* Info.plist */,
\t\t\t\t{brg_h}00 /* Runner-Bridging-Header.h */,
\t\t\t);
\t\t\tpath = Runner;
\t\t\tsourceTree = "<group>";
\t\t}};
/* End PBXGroup section */

/* Begin PBXNativeTarget section */
\t\t{app_tgt} /* Runner */ = {{
\t\t\tisa = PBXNativeTarget;
\t\t\tbuildConfigurationList = {xclist} /* Build configuration list for PBXNativeTarget "Runner" */;
\t\t\tbuildPhases = (
\t\t\t\t{sources} /* Sources */,
\t\t\t\t{res} /* Resources */,
\t\t\t\t{fwk} /* Frameworks */,
\t\t\t);
\t\t\tbuildRules = ();
\t\t\tdependencies = ();
\t\t\tname = Runner;
\t\t\tproductName = Runner;
\t\t\tproductReference = {app_tgt}PP /* Runner.app */;
\t\t\tproductType = "com.apple.product-type.application";
\t\t}};
/* End PBXNativeTarget section */

/* Begin PBXProject section */
\t\t{proj} /* Project object */ = {{
\t\t\tisa = PBXProject;
\t\t\tattributes = {{
\t\t\t\tBuildIndependentTargetsInParallel = YES;
\t\t\t\tLastSwiftUpdateCheck = 1500;
\t\t\t\tLastUpgradeCheck = 1510;
\t\t\t\tORGANIZATION_NAME = "";
\t\t\t\tTargetAttributes = {{
\t\t\t\t\t{app_tgt} = {{
\t\t\t\t\t\tCreatedOnToolsVersion = 14.0;
\t\t\t\t\t\tLastSwiftMigration = 1100;
\t\t\t\t\t}};
\t\t\t\t}};
\t\t\t}};
\t\t\tbuildConfigurationList = {xclist_p} /* Build configuration list for PBXProject "{pkg}" */;
\t\t\tcompatibilityVersion = "Xcode 14.0";
\t\t\tdevelopmentRegion = en;
\t\t\thasScannedForEncodings = 0;
\t\t\tknownRegions = (en, Base);
\t\t\tmainGroup = {grp_root};
\t\t\tprojectDirPath = "";
\t\t\tprojectRoot = "";
\t\t\ttargets = ({app_tgt} /* Runner */);
\t\t}};
/* End PBXProject section */

/* Begin PBXResourcesBuildPhase section */
\t\t{res} /* Resources */ = {{
\t\t\tisa = PBXResourcesBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = (
\t\t\t\t{main_sb}AA /* Main.storyboard in Resources */,
\t\t\t\t{assets_xc}AA /* Assets.xcassets in Resources */,
\t\t\t\t{launch_sb}AA /* LaunchScreen.storyboard in Resources */,
\t\t\t);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t}};
/* End PBXResourcesBuildPhase section */

/* Begin PBXSourcesBuildPhase section */
\t\t{sources} /* Sources */ = {{
\t\t\tisa = PBXSourcesBuildPhase;
\t\t\tbuildActionMask = 2147483647;
\t\t\tfiles = ({appd_sw}AA /* AppDelegate.swift in Sources */);
\t\t\trunOnlyForDeploymentPostprocessing = 0;
\t\t}};
/* End PBXSourcesBuildPhase section */

/* Begin XCBuildConfiguration section */
\t\t{cfg_dbg} /* Debug */ = {{
\t\t\tisa = XCBuildConfiguration;
\t\t\tbaseConfigurationReference = {dbg_xcfg} /* Debug.xcconfig */;
\t\t\tbuildSettings = {{
\t\t\t\tALWAYS_SEARCH_USER_PATHS = NO;
\t\t\t\tCLANG_ENABLE_MODULES = YES;
\t\t\t\tCLANG_ENABLE_OBJC_ARC = YES;
\t\t\t\tDEBUG_INFORMATION_FORMAT = dwarf;
\t\t\t\tENABLE_TESTABILITY = YES;
\t\t\t\tGCC_OPTIMIZATION_LEVEL = 0;
\t\t\t\tGCC_PREPROCESSOR_DEFINITIONS = ("DEBUG=1", "$(inherited)");
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 13.0;
\t\t\t\tMTL_ENABLE_DEBUG_INFO = YES;
\t\t\t\tONLY_ACTIVE_ARCH = YES;
\t\t\t\tSDKROOT = iphoneos;
\t\t\t\tTARGETED_DEVICE_FAMILY = "1,2";
\t\t\t}};
\t\t\tname = Debug;
\t\t}};
\t\t{cfg_rel} /* Release */ = {{
\t\t\tisa = XCBuildConfiguration;
\t\t\tbaseConfigurationReference = {rel_xcfg} /* Release.xcconfig */;
\t\t\tbuildSettings = {{
\t\t\t\tALWAYS_SEARCH_USER_PATHS = NO;
\t\t\t\tCLANG_ENABLE_MODULES = YES;
\t\t\t\tCLANG_ENABLE_OBJC_ARC = YES;
\t\t\t\tCOPY_PHASE_STRIP = NO;
\t\t\t\tDEBUG_INFORMATION_FORMAT = "dwarf-with-dsym";
\t\t\t\tENABLE_NS_ASSERTIONS = NO;
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 13.0;
\t\t\t\tMTL_ENABLE_DEBUG_INFO = NO;
\t\t\t\tSDKROOT = iphoneos;
\t\t\t\tSWIFT_COMPILATION_MODE = wholemodule;
\t\t\t\tSWIFT_OPTIMIZATION_LEVEL = "-O";
\t\t\t\tTARGETED_DEVICE_FAMILY = "1,2";
\t\t\t\tVALIDATE_PRODUCT = YES;
\t\t\t}};
\t\t\tname = Release;
\t\t}};
\t\t{tgt_dbg} /* Debug */ = {{
\t\t\tisa = XCBuildConfiguration;
\t\t\tbaseConfigurationReference = {dbg_xcfg} /* Debug.xcconfig */;
\t\t\tbuildSettings = {{
\t\t\t\tCODE_SIGN_STYLE = Automatic;
\t\t\t\tINFOPLIST_FILE = Runner/Info.plist;
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 13.0;
\t\t\t\tLD_RUNPATH_SEARCH_PATHS = ("$(inherited)", "@executable_path/Frameworks");
\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = {bundle_id};
\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";
\t\t\t\tSWIFT_OBJC_BRIDGING_HEADER = "Runner/Runner-Bridging-Header.h";
\t\t\t\tSWIFT_VERSION = 5.0;
\t\t\t}};
\t\t\tname = Debug;
\t\t}};
\t\t{tgt_rel} /* Release */ = {{
\t\t\tisa = XCBuildConfiguration;
\t\t\tbaseConfigurationReference = {rel_xcfg} /* Release.xcconfig */;
\t\t\tbuildSettings = {{
\t\t\t\tCODE_SIGN_STYLE = Automatic;
\t\t\t\tINFOPLIST_FILE = Runner/Info.plist;
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 13.0;
\t\t\t\tLD_RUNPATH_SEARCH_PATHS = ("$(inherited)", "@executable_path/Frameworks");
\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = {bundle_id};
\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";
\t\t\t\tSWIFT_OBJC_BRIDGING_HEADER = "Runner/Runner-Bridging-Header.h";
\t\t\t\tSWIFT_VERSION = 5.0;
\t\t\t}};
\t\t\tname = Release;
\t\t}};
/* End XCBuildConfiguration section */

/* Begin XCConfigurationList section */
\t\t{xclist_p} /* Build configuration list for PBXProject "{pkg}" */ = {{
\t\t\tisa = XCConfigurationList;
\t\t\tbuildConfigurations = ({cfg_dbg} /* Debug */, {cfg_rel} /* Release */);
\t\t\tdefaultConfigurationIsVisible = 0;
\t\t\tdefaultConfigurationName = Release;
\t\t}};
\t\t{xclist} /* Build configuration list for PBXNativeTarget "Runner" */ = {{
\t\t\tisa = XCConfigurationList;
\t\t\tbuildConfigurations = ({tgt_dbg} /* Debug */, {tgt_rel} /* Release */);
\t\t\tdefaultConfigurationIsVisible = 0;
\t\t\tdefaultConfigurationName = Release;
\t\t}};
/* End XCConfigurationList section */

\t}};
\trootObject = {proj} /* Project object */;
}}
"""


def _analysis_options_yaml() -> str:
    return """\
# analysis_options.yaml – Standard Flutter/Dart lint rules.
# See https://dart.dev/guides/language/analysis-options

include: package:flutter_lints/flutter.yaml

linter:
  rules:
    - prefer_const_constructors
    - prefer_const_literals_to_create_immutables
    - prefer_final_fields
    - avoid_print
    - avoid_dynamic_calls
    - cancel_subscriptions
    - close_sinks

analyzer:
  errors:
    todo: info
"""


def _flutter_gitignore() -> str:
    return """\
# Flutter/Dart
.dart_tool/
.flutter-plugins
.flutter-plugins-dependencies
.packages
.pub-cache/
.pub/
build/
*.iml

# Android
android/.gradle/
android/captures/
android/gradlew
android/gradlew.bat
android/local.properties
android/key.properties
*.jks

# iOS
ios/.symlinks/
ios/Flutter/flutter_export_environment.sh
ios/Pods/
ios/Runner.xcworkspace/xcuserdata/
ios/Flutter/Generated.xcconfig
xcuserdata/
*.pbxuser
!default.pbxuser
*.mode1v3
*.mode2v3
*.perspectivev3
!default.perspectivev3

# macOS
macos/Flutter/GeneratedPluginRegistrant.swift

# General
.DS_Store
*.swp
*.log
coverage/
.idea/
.vscode/settings.json
"""


def _quickstart_md(spec: GameSpec, pkg: str) -> str:
    title = spec.get("title", "My Game")
    orientation = spec.get("orientation", "portrait")
    orient_note = (
        "The game runs in **landscape** mode."
        if orientation == "landscape"
        else "The game runs in **portrait** mode."
    )
    return f"""\
# {title} – Quick-Start Guide

Generated by **Aibase** – Flutter/Flame Game Generator.
{orient_note}

---

## Prerequisites

| Tool | Minimum version | Download |
|------|----------------|---------|
| Flutter SDK | 3.10 | https://docs.flutter.dev/get-started/install |
| Dart SDK | 3.0 | bundled with Flutter |
| Android Studio **or** VS Code | latest | https://developer.android.com/studio |
| Xcode (macOS only, for iOS) | 15 | App Store |
| CocoaPods (macOS only, for iOS) | 1.13 | `sudo gem install cocoapods` |

---

## 1. Get dependencies

```bash
flutter pub get
```

This downloads `flame`, `shared_preferences`, `flutter_lints`, and `flutter_test`.

---

## 2. Run on Android

### Physical device
1. Enable **Developer Options → USB debugging** on your Android phone.
2. Connect via USB and run:
   ```bash
   flutter devices          # confirm your device appears
   flutter run              # debug build
   flutter run --release    # optimised release build
   ```

### Android Emulator
1. Open **Android Studio → Device Manager** and start an emulator (API 26+).
2. Then:
   ```bash
   flutter run
   ```

> **Tip:** The first build downloads Gradle – allow 5–10 minutes.

---

## 3. Run on iOS (macOS only)

```bash
cd ios
pod install          # install CocoaPods plugins (first time or after pub get)
cd ..
flutter run
```

### iPhone Simulator
```bash
open -a Simulator
flutter run
```

### Physical iPhone
1. Open `ios/Runner.xcworkspace` in Xcode.
2. Select **Runner → Signing & Capabilities** and set your Team.
3. Select your device and press **▶ Run**, **or** run:
   ```bash
   flutter run --release
   ```

---

## 4. Build release APK / IPA

```bash
# Android APK
flutter build apk --release
# → build/app/outputs/flutter-apk/app-release.apk

# Android App Bundle (Play Store)
flutter build appbundle --release
# → build/app/outputs/bundle/release/app-release.aab

# iOS IPA (macOS only)
flutter build ipa --release
# → build/ios/ipa/{pkg}.ipa
```

---

## 5. Replace placeholder icons

The generated project uses **empty placeholder** launcher icons.
Replace them before publishing:

| Platform | Path | Required sizes |
|----------|------|---------------|
| Android | `android/app/src/main/res/mipmap-*/ic_launcher.png` | 48/72/96/144/192 px |
| iOS | `ios/Runner/Assets.xcassets/AppIcon.appiconset/` | 1024×1024 px |

Or use [`flutter_launcher_icons`](https://pub.dev/packages/flutter_launcher_icons)
to auto-generate all sizes from a single 1024×1024 source image.

---

## 6. Lint & analyse

```bash
flutter analyze           # static analysis (uses analysis_options.yaml)
flutter test              # unit & widget tests
```

---

## Project layout

```
{pkg}/
├── lib/
│   ├── main.dart                  # entry point + bottom-nav shell
│   ├── game/
│   │   ├── game.dart              # FlameGame root
│   │   ├── hero.dart              # player + XP leveling + crits
│   │   ├── enemy.dart             # enemies (boss every 5th wave)
│   │   ├── idle_manager.dart      # auto-battle + offline catch-up
│   │   ├── hud.dart               # heads-up display
│   │   ├── upgrade_overlay.dart   # wave-complete upgrade shop
│   │   ├── game_over_overlay.dart # hero-fallen screen + prestige
│   │   ├── save_manager.dart      # SharedPreferences persistence
│   │   └── damage_text.dart       # floating crit/damage numbers
│   └── screens/
│       ├── quest_log_screen.dart
│       ├── characters_screen.dart
│       ├── shop_screen.dart
│       ├── combat_screen.dart
│       └── settings_screen.dart
├── assets/data/                   # JSON game data (auto-loaded)
├── android/                       # Android platform scaffold
├── ios/                           # iOS platform scaffold
├── analysis_options.yaml          # Dart lint rules
├── pubspec.yaml
└── QUICKSTART.md  ← you are here
```

---

## Save data keys (SharedPreferences)

| Key | Description |
|-----|-------------|
| `save_gold` | Current gold |
| `save_wave` | Current wave number |
| `save_hero_level` | Hero auto-level |
| `save_xp` | Current XP toward next level |
| `save_prestige` | Number of prestiges completed |
| `save_timestamp` | Unix ms of last save (offline progress) |

Tap **Settings → Reset Save Data** to wipe all save data.

---

*Happy building – and good luck on the boss waves!* 👑
"""
