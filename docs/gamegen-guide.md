# Game Generator – Architecture & Developer Guide

This document covers the full architecture of the Aibase Flutter/Flame game
generator, how to run it, how to add a new genre plugin, and the mobile-first
design choices.

---

## Prerequisites

| Tool | Minimum version | Purpose |
|------|-----------------|---------|
| Python | 3.8 | Generator runtime |
| Flutter SDK | 3.10 | Build generated projects |
| Android SDK | API 21 (Android 5) | Android builds |
| Xcode | 15 | iOS builds (macOS only) |
| Ollama *(optional)* | any | AI-enhanced GameSpec |

Install Python deps:
```bash
pip install -r requirements.txt
```

---

## Directory Layout

```
Aibase/
├── aibase.py                  existing CLI (code translator + --generate-game)
├── gamegen.py                 ← NEW standalone game generator CLI
│
├── orchestrator/              coordinator + constraint resolver
│   ├── __init__.py
│   ├── constraint_resolver.py
│   └── orchestrator.py
│
├── workers/                   individual pipeline stages
│   ├── flame_generator.py     scaffold Flutter/Flame project
│   ├── asset_worker.py        import local assets
│   ├── zip_worker.py          create ZIP archive
│   └── validator.py           flutter analyze + auto-fix loop
│
├── schemas/                   typed models
│   ├── game_spec.py           GameSpec (TypedDict)
│   ├── asset_spec.py          AssetSpec (dataclass)
│   └── build_spec.py          BuildSpec (dataclass)
│
├── templates/flutter/         Markdown skeleton templates used by scaffolder
│   ├── README.md.tmpl
│   ├── CREDITS.md.tmpl
│   └── ASSETS_LICENSE.md.tmpl
│
├── game_generator/            core generator package (unchanged public API)
│   ├── spec.py                GameSpec heuristic + Ollama generation
│   ├── scaffolder.py          full project file tree builder
│   ├── asset_importer.py      asset scanner & heuristic mapper
│   ├── zip_exporter.py        ZIP bundler
│   └── genres/
│       ├── __init__.py        genre plugin registry
│       ├── top_down_shooter.py
│       └── idle_rpg.py
│
├── outputs/                   generated projects land here (git-ignored)
├── docs/                      documentation
└── tests/                     Python unit tests
```

---

## Pipeline

```
User prompt + CLI flags
        │
        ▼
ConstraintResolver.resolve()   ← interactive prompts or CLI defaults
        │  {dimension, art_style, online, platform, scope}
        ▼
spec.generate_spec()           ← heuristic or Ollama JSON
        │  GameSpec dict
        ▼
asset_importer.import_assets() ← scan --assets-dir, copy to project_dir
        │  [relative asset paths]
        ▼
scaffolder.scaffold_project()  ← genre plugin + boilerplate files
        │  {path: content}
        ▼
ValidatorWorker (optional)     ← flutter pub get + flutter analyze [+ auto-fix]
        │
        ▼
zip_exporter.export_to_zip()   ← output.zip
```

---

## Running the Generator

### Quick start

```bash
# Minimal – uses heuristics, no assets, no validation
python gamegen.py --prompt "top down space shooter" --out game.zip

# With local assets folder
python gamegen.py --prompt "idle RPG with upgrades" \
    --assets-dir "C:\Users\me\Desktop\MyAssets" \
    --out my_game.zip

# Full options
python gamegen.py \
    --prompt "idle RPG with upgrades" \
    --assets-dir "C:\Users\me\Desktop\MyAssets" \
    --out my_game.zip \
    --platform android+ios \
    --scope vertical-slice \
    --art-style pixel-art \
    --auto-fix

# Interactive constraint prompts
python gamegen.py --prompt "space shooter" --out game.zip --interactive

# AI-enhanced spec (requires Ollama)
python gamegen.py --prompt "idle RPG" --out game.zip --model qwen2.5-coder:7b
```

The existing entry point also works:
```bash
python aibase.py --generate-game --prompt "top down space shooter" --out game.zip
```

### Building the generated project

```bash
unzip game.zip -d my_game
cd my_game
flutter pub get
flutter run          # desktop/emulator
flutter run -d <device-id>   # physical Android/iOS device
```

---

## Mobile-Ready Output

Every generated project is **configured for mobile-first play**:

### Screen orientation
`main.dart` calls `SystemChrome.setPreferredOrientations()` at startup:
- `top_down_shooter` → landscape (sensorLandscape)
- `idle_rpg` → portrait (sensorPortrait)

The orientation also propagates to `AndroidManifest.xml` and `ios/Runner/Info.plist`.

### Touch controls (top-down shooter)
`lib/game/mobile_controls.dart` adds:
- **Virtual joystick** (bottom-left) – `JoystickComponent` with 55 px background radius
- **Fire button** (bottom-right) – `HudButtonComponent`, triggers `player.shoot()`

`Player.update()` checks keyboard first then falls back to the joystick:
```dart
if (_keyDir.length2 > 0) {
  position.addScaled(_keyDir.normalized(), _speed * dt);
} else if (game.joystick.relativeDelta.length2 > 0) {
  position.addScaled(game.joystick.relativeDelta, _speed * dt);
}
```

### Touch controls (idle RPG)
The idle RPG already uses `TapCallbacks` for tap-to-attack – it is
natively mobile-ready. The game locks to portrait orientation.

### Android manifest
`android/app/src/main/AndroidManifest.xml` is included with:
- correct `screenOrientation`
- `hardwareAccelerated="true"`
- Flutter embedding v2

### iOS Info.plist
`ios/Runner/Info.plist` is included with `UISupportedInterfaceOrientations`
set to match the genre orientation.

---

## GameSpec Schema

```json
{
  "title":            "Space Blaster",
  "genre":            "top_down_shooter",
  "core_loop":        "Move ship → shoot enemies → survive waves → earn score",
  "mechanics":        ["move", "shoot", "dodge", "collect_powerups"],
  "entities": [
    {"name": "Player", "role": "player", "attributes": {"speed": 200, "hp": 1}},
    {"name": "Enemy",  "role": "enemy",  "attributes": {"speed": 100, "hp": 1}},
    {"name": "Bullet", "role": "projectile", "attributes": {"speed": 400}}
  ],
  "required_assets":  ["player", "enemy", "bullet", "background", "explosion"],
  "screens":          ["main_menu", "game", "game_over"],
  "controls": {
    "keyboard": ["WASD", "arrows", "space"],
    "mobile":   ["joystick", "fire_button"]
  },
  "progression": {
    "scoring":         "points",
    "levels":          5,
    "difficulty_ramp": "wave"
  },
  "performance_hints": [
    "Preload all sprites in onLoad()",
    "Use BulletPool to avoid per-shot allocations",
    "Prefer RectangleHitbox for collision shapes"
  ],
  "orientation":  "landscape",
  "art_style":    "pixel-art",
  "platform":     "android",
  "scope":        "prototype",
  "dimension":    "2D",
  "online":       false
}
```

---

## Adding a New Genre Plugin

### 1. Create `game_generator/genres/<your_genre>.py`

```python
from game_generator.spec import GameSpec
from typing import Dict

def generate_files(spec: GameSpec) -> Dict[str, str]:
    """Return {relative_path: dart_content}."""
    name = _safe_class_name(spec.get("title", "MyGame"))
    return {
        "lib/game/game.dart": _game_dart(name),
        # add more files …
    }

def _safe_class_name(title: str) -> str:
    words = "".join(ch if ch.isalnum() or ch == " " else " " for ch in title).split()
    return "".join(w.capitalize() for w in words) or "MyGame"

def _game_dart(name: str) -> str:
    return f"""
import 'package:flame/game.dart';
class {name}Game extends FlameGame {{
  @override
  Future<void> onLoad() async {{ await super.onLoad(); }}
}}
"""
```

**Flame best-practice checklist:**
- [ ] Preload all sprites in `onLoad()` – `await loadSprite(...)`
- [ ] No `Vector2(...)` or `Paint()` allocations inside `update(double dt)`
- [ ] Object pool for bullets / projectiles
- [ ] `RectangleHitbox` / `CircleHitbox` with `HasCollisionDetection`
- [ ] `TextPaint` for HUD – avoid rebuilding every frame
- [ ] Add `JoystickComponent` + `HudButtonComponent` for mobile if the game
  needs directional input (see `top_down_shooter.py` for reference)

### 2. Register in `game_generator/genres/__init__.py`

```python
from . import your_genre as _your_genre

GENRE_REGISTRY = {
    "top_down_shooter": _shooter.generate_files,
    "idle_rpg":         _idle_rpg.generate_files,
    "your_genre":       _your_genre.generate_files,   # ← add here
}
```

### 3. Add keywords to `game_generator/spec.py`

```python
_GENRE_KEYWORDS = {
    …
    "your_genre": ["keyword1", "keyword2"],
}
```

Add entries to `_default_mechanics`, `_default_assets`, `_default_controls`,
`_default_progression`, `_default_core_loop`, `_default_entities`,
`_default_performance_hints`, and `_default_orientation`.

### 4. Write a test

Add a test case in `tests/test_scaffolder.py`:
```python
def _your_spec(**kwargs) -> GameSpec:
    base = {"title": "My Genre", "genre": "your_genre", …}
    base.update(kwargs)
    return base

class TestYourGenreScaffolder(unittest.TestCase):
    def test_contains_required_files(self):
        for req in REQUIRED_FILES:
            self.assertIn(req, scaffold_project(_your_spec()))
```

---

## Asset Import

`AssetIndexer.scan()` recursively finds files with these extensions:
```
Images: .png .jpg .jpeg .gif .webp
Audio:  .wav .mp3 .ogg
```

`AssetIndexer.match_assets(spec)` maps each `required_assets` role to the
best file using a scoring heuristic:

| Signal              | Score |
|---------------------|-------|
| Exact role in stem  | +100  |
| Tag keyword in stem | +50   |
| Image extension     | +10 *(only when score > 0)* |

Assets are copied to `assets/imported/<role><ext>` and referenced in
`pubspec.yaml`.  Missing roles fall back to placeholder colours in the
generated Dart code.

---

## Validation & Auto-Fix

Pass `--validate` to run the full validation suite after scaffolding.
Pass `--auto-fix` to apply deterministic patch rules and retry on failure.
Pass `--run-tests` to also execute `flutter test` (a minimal smoke-test file
is injected automatically if the project has no test files yet).

```bash
# Validate only
python gamegen.py --prompt "space shooter" --out game.zip --validate

# Auto-fix + validate
python gamegen.py --prompt "space shooter" --out game.zip --auto-fix

# Auto-fix + validate + run tests
python gamegen.py --prompt "space shooter" --out game.zip --auto-fix --run-tests
```

Requires Flutter SDK and Dart SDK on `PATH`.

### What validation runs

| Step | Command | Failure behaviour |
|------|---------|-------------------|
| 1 | `dart format .` | Warning only – continues |
| 2 | `flutter pub get` | Hard failure – stops |
| 3 | `flutter analyze` | Hard failure – stops |
| 4 | `flutter test` | Hard failure – only when `--run-tests` |

### What auto-fix can do

Auto-fix applies a registry of **deterministic patch rules** before each
retry.  If no rule changes any file the retry is skipped (avoiding
unnecessary SDK invocations).

| Rule | File(s) affected | What it fixes |
|------|-----------------|---------------|
| `pubspec: fix caret SDK constraints` | `pubspec.yaml` | Converts `^X.Y.Z` SDK constraints to `>=X.Y.Z <(X+1).0.0` |
| `pubspec: ensure flutter_test dev_dependency` | `pubspec.yaml` | Adds `flutter_test` dev dependency when absent |
| `pubspec: pin flame dependency` | `pubspec.yaml` | Pins `flame` to `^1.18.0` if a looser constraint is found |
| `main.dart: ensure required imports` | `lib/main.dart` | Adds missing `flutter/material.dart`, `flutter/services.dart`, `flame/game.dart` imports |
| `dart: replace print() with debugPrint()` | All non-test `.dart` files | Replaces bare `print(` calls with `debugPrint(` to silence analyzer warnings |

The registry lives in `workers/validator.py` as `PATCH_RULES`.  Add new
entries there to cover additional auto-fixable patterns.

### Smoke-test injection

When `--run-tests` is requested and the generated project has no test files,
`ValidatorWorker.ensure_smoke_test()` writes a tiny `test/smoke_test.dart`
that simply checks `1 + 1 == 2`.  Replace it with real tests before
publishing.

---

## Constraint Resolution

| Flag | Default | Notes |
|------|---------|-------|
| `--platform` | `android` | `android` or `android+ios` |
| `--scope` | `prototype` | `prototype` or `vertical-slice` |
| `--art-style` | `pixel-art` | free-form hint |
| `--online` | *(off)* | flag; default is offline |
| `--interactive` | *(off)* | prompt for each constraint |

`dimension` is always `2D` – Flame does not support 3D.

---

## Notes

- Aibase does **not** download assets from itch.io or any online store.
  Use `--assets-dir` to supply your own.
- The Flame dependency is pinned to `^1.18.0`.  Bump in `pubspec.yaml` as
  needed; check the [Flame changelog](https://pub.dev/packages/flame/changelog).
- `outputs/` is git-ignored; generated ZIPs are never committed.
