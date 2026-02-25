# Game Generator – Developer Guide

This document explains the internal architecture of the Flutter/Flame game
generator and shows how to add new game genres.

## Architecture Overview

```
gamegen.py  (CLI entry point)
    └── gamegenerator/
        ├── __init__.py         re-exports the public API
        ├── spec.py             GameSpec generation (heuristic + optional AI)
        ├── scaffolder.py       Full Flutter project scaffolding
        ├── asset_importer.py   Local asset scanner & heuristic mapper
        ├── zip_exporter.py     ZIP bundler
        ├── genres/
        │   ├── __init__.py     Genre plugin registry
        │   ├── top_down_shooter.py
        │   └── idle_rpg.py
        ├── orchestrator/
        │   ├── constraint_resolver.py
        │   └── orchestrator.py
        ├── workers/
        │   ├── flame_generator.py
        │   ├── asset_worker.py
        │   ├── zip_worker.py
        │   └── validator.py
        └── schemas/
            ├── game_spec.py
            ├── asset_spec.py
            └── build_spec.py
```

### Pipeline Steps

```
User prompt
    │
    ▼
spec.generate_spec()   ── heuristic (always) or AI JSON (if Ollama available)
    │
    ▼  GameSpec dict
genres.get_genre_plugin(genre)(spec) ── returns {path: dart_content}
    │
    ▼  genre files + scaffolder.scaffold_project()
       → pubspec.yaml, lib/main.dart, README.md, ASSETS_LICENSE.md, CREDITS.md
       → android/app/src/main/AndroidManifest.xml
       → ios/Runner/Info.plist
    │
    ▼  (optional) asset_importer.import_assets()
       → copies matched files into project_dir/assets/imported/
    │
    ▼  zip_exporter.export_to_zip()
       → output.zip
```

## GameSpec Schema

```json
{
  "title":           "Space Blaster",
  "genre":           "top_down_shooter",
  "core_loop":       "Move ship → shoot enemies → survive waves → earn score",
  "mechanics":       ["move", "shoot", "dodge", "collect_powerups"],
  "entities": [
    {"name": "Player", "role": "player", "attributes": {"speed": 200, "hp": 1}},
    {"name": "Enemy",  "role": "enemy",  "attributes": {"speed": 100, "hp": 1}},
    {"name": "Bullet", "role": "projectile", "attributes": {"speed": 400}}
  ],
  "required_assets": ["player", "enemy", "bullet", "background", "explosion"],
  "screens":         ["main_menu", "game", "game_over"],
  "controls": {
    "keyboard": ["WASD", "arrows", "space"],
    "mobile":   ["joystick", "fire_button"]
  },
  "progression": {
    "scoring":          "points",
    "levels":           5,
    "difficulty_ramp":  "wave"
  },
  "performance_hints": [
    "Preload all sprites in onLoad()",
    "Use BulletPool to avoid per-shot allocations",
    "Prefer RectangleHitbox for collision shapes"
  ],
  "orientation": "landscape",
  "art_style":   "pixel-art",
  "platform":    "android",
  "scope":       "prototype",
  "dimension":   "2D",
  "online":      false
}
```

## Adding a New Genre

### 1. Create `gamegenerator/genres/<your_genre>.py`

The module must expose one function:

```python
from gamegenerator.spec import GameSpec
from typing import Dict

def generate_files(spec: GameSpec) -> Dict[str, str]:
    """Return {relative_dart_path: file_content}."""
    ...
```

All paths should be relative to the project root and start with `lib/game/`.

**Required files** (minimum):
- `lib/game/game.dart` – a `FlameGame` subclass.

**Flame best-practice checklist for generated code:**
- [ ] Preload all sprites in `onLoad()` using `await loadSprite(...)`.
- [ ] No `Vector2(...)` or similar allocations inside `update(double dt)`.
- [ ] Use object pools for frequently created/destroyed objects (bullets etc.).
- [ ] Use `RectangleHitbox` or `CircleHitbox` with `HasCollisionDetection`.
- [ ] `TextComponent` / `TextPaint` for HUD text – avoid rebuilding on every frame.
- [ ] Add `JoystickComponent` + `HudButtonComponent` for mobile directional input
  (see `top_down_shooter.py` → `mobile_controls.dart` for reference).

### 2. Register the genre in `gamegenerator/genres/__init__.py`

```python
from . import your_genre as _your_genre

GENRE_REGISTRY: Dict[str, ...] = {
    "top_down_shooter": _shooter.generate_files,
    "idle_rpg":         _idle_rpg.generate_files,
    "your_genre":       _your_genre.generate_files,   # ← add this line
}
```

### 3. Add genre keywords to `gamegenerator/spec.py`

```python
_GENRE_KEYWORDS: Dict[str, List[str]] = {
    ...
    "your_genre": ["keyword1", "keyword2", "..."],
}
```

And add default mechanics/assets/controls/progression/core_loop/entities/
performance_hints/orientation entries to the corresponding `_default_*`
functions.

### 4. Write a test

Add a test case in `tests/test_scaffolder.py` (following existing examples)
that checks:
- `scaffold_project(your_spec())` contains `REQUIRED_FILES`.
- Genre-specific Dart files are present.
- `pubspec.yaml` references Flame.
- `AndroidManifest.xml` and `ios/Runner/Info.plist` are present.

## Asset Importer

### Scanning

`AssetIndexer.scan()` recursively walks a directory and returns all files whose
extension is in:

```
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg"}
```

### Matching

`AssetIndexer.match_assets(spec)` maps each item in `spec["required_assets"]`
to the best file using a scoring heuristic:

| Signal              | Score |
|---------------------|-------|
| Exact role in stem  | +100  |
| Tag keyword in stem | +50   |
| Image extension     | +10 *(only when score > 0)* |

Add more tags to `_ROLE_TAGS` in `asset_importer.py` for better matching.

## CLI Reference

```
python gamegen.py
    --prompt      TEXT       Game description (required)
    --out         PATH.zip   Output ZIP path (required)
    --assets-dir  PATH       Local assets folder (optional)
    --platform    android|android+ios  (default: android)
    --scope       prototype|vertical-slice  (default: prototype)
    --art-style   TEXT       Art style hint (default: pixel-art)
    --online                 Generate an online-multiplayer game
    --validate               Run flutter pub get + flutter analyze
    --auto-fix               Retry on validation failure (implies --validate)
    --interactive            Prompt for each constraint
    --model       MODEL      AI model for enhanced spec (optional)
    --temperature FLOAT      AI sampling temperature (optional)
    --timeout     INT        AI request timeout seconds (optional)
```

## Prerequisites for Building the Generated Game

- [Flutter SDK](https://docs.flutter.dev/get-started/install) ≥ 3.10
- Android SDK API 21+ for Android builds
- Xcode 15+ for iOS builds (macOS only)
- Run `flutter pub get` inside the unzipped project before building.
- `flutter analyze` should pass on any generated project.

## Notes

- GameGenerator does **not** download assets from itch.io or any other storefront.
  The `--assets-dir` flag is the only way to supply custom assets; everything
  else uses `assets/imported/` as a placeholder directory.
- The Flame dependency pinned in `pubspec.yaml` is `^1.18.0`.  Bump this if
  you need a newer API; check the
  [Flame changelog](https://pub.dev/packages/flame/changelog) for breaking
  changes.
- `outputs/` is git-ignored; generated ZIPs are never committed.
