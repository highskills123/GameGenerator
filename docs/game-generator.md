# Game Generator – Developer Guide

This document explains the internal architecture of the Flutter/Flame game
generator that ships as part of Aibase, and shows how to add new game genres.

## Architecture Overview

```
aibase.py  (CLI entry point)
    └── game_generator/
        ├── __init__.py         re-exports the public API
        ├── spec.py             GameSpec generation (heuristic + optional Ollama)
        ├── scaffolder.py       Full Flutter project scaffolding
        ├── asset_importer.py   Local asset scanner & heuristic mapper
        ├── zip_exporter.py     ZIP bundler
        └── genres/
            ├── __init__.py     Genre plugin registry
            ├── top_down_shooter.py
            └── idle_rpg.py
```

### Pipeline Steps

```
User prompt
    │
    ▼
spec.generate_spec()   ── heuristic (always) or Ollama JSON (if available)
    │
    ▼  GameSpec dict
genres.get_genre_plugin(genre)(spec) ── returns {path: dart_content}
    │
    ▼  genre files + scaffolder.scaffold_project()
       → pubspec.yaml, lib/main.dart, README.md, ASSETS_LICENSE.md
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
  "mechanics":       ["move", "shoot", "dodge", "collect_powerups"],
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
  }
}
```

## Adding a New Genre

### 1. Create `game_generator/genres/<your_genre>.py`

The module must expose one function:

```python
from game_generator.spec import GameSpec
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

### 2. Register the genre in `game_generator/genres/__init__.py`

```python
from . import your_genre as _your_genre

GENRE_REGISTRY: Dict[str, ...] = {
    "top_down_shooter": _shooter.generate_files,
    "idle_rpg":         _idle_rpg.generate_files,
    "your_genre":       _your_genre.generate_files,   # ← add this line
}
```

### 3. Add genre keywords to `game_generator/spec.py`

```python
_GENRE_KEYWORDS: Dict[str, List[str]] = {
    ...
    "your_genre": ["keyword1", "keyword2", "..."],
}
```

And add default mechanics/assets/controls/progression entries to the
corresponding `_default_*` functions.

### 4. Write a test

Add a test case in `tests/test_scaffolder.py` (following existing examples)
that checks:
- `scaffold_project(your_spec())` contains `REQUIRED_FILES`.
- Genre-specific Dart files are present.
- `pubspec.yaml` references Flame.

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
python aibase.py --generate-game
    --prompt   TEXT       Game description (required)
    --out      PATH.zip   Output ZIP path (required)
    --assets-dir PATH     Local assets folder (optional)
    --model    MODEL      Ollama model for AI spec (optional)
    --temperature FLOAT   Ollama temperature (optional)
    --timeout  INT        Ollama request timeout seconds (optional)
```

## Prerequisites for Building the Generated Game

- [Flutter SDK](https://docs.flutter.dev/get-started/install) ≥ 3.10
- Run `flutter pub get` inside the unzipped project before building.
- `flutter analyze` should pass on any generated project.

## Idle RPG UI Screens and Content Personalisation

When the `idle_rpg` genre is selected the generator produces three Flutter
navigation screens in addition to the Flame game itself:

| Screen | File | Data source |
|--------|------|-------------|
| Quest Log | `lib/screens/quest_log_screen.dart` | `assets/data/quests.json` |
| Characters | `lib/screens/characters_screen.dart` | `assets/data/characters.json` |
| Shop | `lib/screens/shop_screen.dart` | `assets/data/items.json` |

A `BottomNavigationBar` in `lib/main.dart` lets players switch between the
Flame battle view and these three screens.

### JSON data files

Four JSON files are written to `assets/data/` and declared in `pubspec.yaml`:

```
assets/data/quests.json      – list of quest objects
assets/data/characters.json  – list of character objects
assets/data/items.json       – list of item objects (shop)
assets/data/locations.json   – list of location objects
```

When `--design-doc` is passed (and Ollama is available), the generator
populates these files with real names, summaries, and lore taken directly from
the generated design document.  Without `--design-doc` the files contain
sensible placeholder data so the project still builds and runs immediately.

### Customising the content

Edit the JSON files in `assets/data/` after generation to add your own quests,
characters, and items.  No code changes are needed – the screens load data via
`rootBundle.loadString` at runtime.

Each quest object supports the following keys:

```json
{
  "title":       "Quest title",
  "summary":     "Short description shown in the list",
  "giver":       "NPC name",
  "level_range": [1, 5],
  "objectives":  ["objective 1", "..."],
  "rewards":     ["reward 1", "..."]
}
```

Each character object:

```json
{
  "name":        "Character Name",
  "role":        "Hero | NPC | Villain",
  "backstory":   "Brief backstory",
  "motivations": ["motivation 1", "..."]
}
```

Each item object:

```json
{
  "name":        "Item Name",
  "type":        "weapon | armor | consumable",
  "rarity":      "common | rare | epic | legendary",
  "description": "Short flavour text",
  "stats":       {"attack": 5}
}
```

## Notes

- Aibase does **not** download assets from itch.io or any other storefront.
  The `--assets-dir` flag is the only way to supply custom assets; everything
  else uses `assets/imported/` as a placeholder directory.
- The Flame dependency pinned in `pubspec.yaml` is `^1.18.0`.  Bump this if
  you need a newer API; check the
  [Flame changelog](https://pub.dev/packages/flame/changelog) for breaking
  changes.
