# GameGenerator

**GameGenerator** is a standalone Python tool that scaffolds complete, mobile-ready
Flutter/Flame game projects from a single natural-language prompt.

```bash
python gamegen.py --prompt "top down space shooter" --out game.zip
python gamegen.py --prompt "idle RPG with hero upgrades" \
    --assets-dir "C:\Users\me\assets" \
    --out my_game.zip --platform android+ios
```

Unzip the output, run `flutter pub get && flutter run`, and your game is live on
Android or iOS — touch controls, orientation lock, and manifests included.

---

## Features

| Feature | Detail |
|---------|--------|
| 🎮 **Multi-genre** | Top-down shooter & idle RPG (plugin system to add more) |
| 📱 **Mobile-first** | Virtual joystick + fire button; `AndroidManifest.xml`; `ios/Info.plist`; orientation lock |
| 🗂️ **Full project scaffold** | `pubspec.yaml`, `lib/main.dart`, split `lib/game/` files, `README.md`, `CREDITS.md`, `ASSETS_LICENSE.md` |
| 🖼️ **Asset import** | Scans a local folder; heuristic role-matching; copies into `assets/imported/`; updates `pubspec.yaml` |
| 📦 **ZIP export** | One-command ZIP of the complete project |
| ✅ **Flutter validation** | Optional `flutter pub get` + `flutter analyze` + auto-fix loop |
| 🤖 **AI-enhanced spec** | Plug in any Ollama model for richer `GameSpec` generation |
| 🔌 **Plugin architecture** | `orchestrator/`, `workers/`, `schemas/` — add a genre in < 5 min |

---

## Requirements

| Tool | Minimum | Purpose |
|------|---------|---------|
| Python | 3.8 | Run the generator |
| Flutter SDK | 3.10 | Build generated projects |
| Android SDK | API 21 | Android builds |
| Xcode | 15 | iOS builds (macOS) |
| Ollama *(opt)* | any | AI-enhanced GameSpec |

```bash
pip install -r requirements.txt
```

---

## Quick Start

```bash
# Minimal – no assets, no validation
python gamegen.py --prompt "top down space shooter" --out game.zip

# With local assets folder
python gamegen.py \
    --prompt "idle RPG with upgrades" \
    --assets-dir "C:\Users\me\Desktop\MyAssets" \
    --out my_game.zip

# Full options
python gamegen.py \
    --prompt "idle RPG with upgrades" \
    --assets-dir "C:\Users\me\Desktop\MyAssets" \
    --out my_game.zip \
    --platform android+ios \
    --scope vertical-slice \
    --auto-fix

# Interactive constraint prompts
python gamegen.py --prompt "space shooter" --out game.zip --interactive
```

### Build the generated project

```bash
unzip game.zip -d my_game
cd my_game
flutter pub get
flutter run                     # desktop / emulator
flutter run -d <device-id>     # physical Android / iOS device
```

---

## Architecture

```
GameGenerator/
├── gamegen.py                    ← CLI entry point
├── gamegenerator/                ← Python package
│   ├── spec.py                   GameSpec heuristic + Ollama
│   ├── scaffolder.py             Full project file builder
│   ├── asset_importer.py         Asset scanner & mapper
│   ├── zip_exporter.py           ZIP bundler
│   ├── genres/                   Genre plugin registry
│   │   ├── top_down_shooter.py
│   │   └── idle_rpg.py
│   ├── orchestrator/             Constraint resolver + pipeline coordinator
│   ├── workers/                  Typed pipeline stage workers
│   └── schemas/                  GameSpec / AssetSpec / BuildSpec models
├── templates/flutter/            Markdown skeleton templates
├── tests/                        Unit tests (47 passing)
└── outputs/                      Generated ZIPs land here (git-ignored)
```

### Pipeline

```
prompt + CLI flags
      │
      ▼  ConstraintResolver
      │  (dimension=2D enforced; interactive prompts optional)
      ▼  spec.generate_spec()
      │  GameSpec dict
      ▼  asset_importer.import_assets()   (optional)
      │  copied assets + manifest
      ▼  scaffolder.scaffold_project()
      │  {path: content} project tree
      ▼  ValidatorWorker              (optional, --validate / --auto-fix)
      ▼  zip_exporter.export_to_zip()
         output.zip
```

---

## Adding a Genre

1. **Create** `gamegenerator/genres/my_genre.py` with a `generate_files(spec)` function.
2. **Register** it in `gamegenerator/genres/__init__.py`.
3. **Add keywords** to `gamegenerator/spec.py` (`_GENRE_KEYWORDS`, `_default_*` functions).
4. **Write a test** in `tests/test_scaffolder.py`.

See [ROADMAP.md](ROADMAP.md) for the full vision of what to build next.

---

## Running Tests

```bash
python -m pytest tests/ -v
```

Expected: **47 tests pass**.

---

## License

MIT — see `CREDITS.md` in each generated project for third-party attributions.
