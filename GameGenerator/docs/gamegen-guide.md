# GameGenerator – Architecture & Developer Guide

This document covers the full architecture of the GameGenerator standalone
package, how to run it, how to add a new genre plugin, and the mobile-first
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
GameGenerator/
├── gamegen.py                    ← standalone CLI entry point
├── gamegenerator/                ← Python package
│   ├── spec.py                   GameSpec heuristic + AI generation
│   ├── scaffolder.py             Full project file tree builder
│   ├── asset_importer.py         Asset scanner & heuristic mapper
│   ├── zip_exporter.py           ZIP bundler
│   ├── genres/                   Genre plugin registry
│   │   ├── __init__.py           GENRE_REGISTRY + get_genre_plugin()
│   │   ├── top_down_shooter.py
│   │   └── idle_rpg.py
│   ├── orchestrator/             Constraint resolver + pipeline coordinator
│   │   ├── constraint_resolver.py
│   │   └── orchestrator.py
│   ├── workers/                  Typed pipeline stage workers
│   │   ├── flame_generator.py
│   │   ├── asset_worker.py
│   │   ├── zip_worker.py
│   │   └── validator.py
│   └── schemas/                  GameSpec / AssetSpec / BuildSpec models
│       ├── game_spec.py
│       ├── asset_spec.py
│       └── build_spec.py
├── templates/flutter/            Markdown skeleton templates
│   ├── README.md.tmpl
│   ├── CREDITS.md.tmpl
│   └── ASSETS_LICENSE.md.tmpl
├── tests/                        Unit tests (47 passing)
├── docs/                         Documentation (this file + game-generator.md)
└── outputs/                      Generated ZIPs land here (git-ignored)
```

---

## Pipeline

```
prompt + CLI flags
        │
        ▼  ConstraintResolver
        │  (dimension=2D enforced; interactive prompts optional)
        ▼  spec.generate_spec()
        │  GameSpec dict
        ▼  asset_importer.import_assets()   (optional --assets-dir)
        │  copied assets + relative paths
        ▼  scaffolder.scaffold_project()
        │  {path: content} project tree
        ▼  ValidatorWorker              (optional, --validate / --auto-fix)
        ▼  zip_exporter.export_to_zip()
           output.zip
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

### Building the generated project

```bash
unzip game.zip -d my_game
cd my_game
flutter pub get
flutter run                     # desktop / emulator
flutter run -d <device-id>     # physical Android / iOS device
```

---

## Mobile-Ready Output

Every generated project is **configured for mobile-first play**:

### Screen orientation
`main.dart` calls `SystemChrome.setPreferredOrientations()` at startup:
- `top_down_shooter` → landscape (sensorLandscape on Android)
- `idle_rpg` → portrait (sensorPortrait on Android)

The orientation propagates to `AndroidManifest.xml` and `ios/Runner/Info.plist`.

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
The idle RPG uses `TapCallbacks` for tap-to-attack – natively mobile-ready.
It locks to portrait orientation.

### Android manifest
`android/app/src/main/AndroidManifest.xml` is included with:
- correct `screenOrientation` per genre
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

### 1. Create `gamegenerator/genres/<your_genre>.py`

```python
from gamegenerator.spec import GameSpec
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
- [ ] Add `JoystickComponent` + `HudButtonComponent` for mobile directional input

### 2. Register in `gamegenerator/genres/__init__.py`

```python
from . import your_genre as _your_genre

GENRE_REGISTRY = {
    "top_down_shooter": _shooter.generate_files,
    "idle_rpg":         _idle_rpg.generate_files,
    "your_genre":       _your_genre.generate_files,   # ← add here
}
```

### 3. Add keywords to `gamegenerator/spec.py`

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

Pass `--validate` to run `flutter pub get` + `flutter analyze` after
scaffolding.  Pass `--auto-fix` to retry on failure (up to 3 times).

```bash
python gamegen.py --prompt "space shooter" --out game.zip --auto-fix
```

Requires Flutter SDK on `PATH`.

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

## Running Tests

```bash
python -m pytest tests/ -v
```

Expected: **47 tests pass**.

---

## Notes

- GameGenerator does **not** download assets from itch.io or any online store.
  Use `--assets-dir` to supply your own.
- The Flame dependency is pinned to `^1.18.0`.  Bump in `pubspec.yaml` as
  needed; check the [Flame changelog](https://pub.dev/packages/flame/changelog).
- `outputs/` is git-ignored; generated ZIPs are never committed.
- See [ROADMAP.md](../ROADMAP.md) for the full studio-scale vision.
