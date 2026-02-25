# GameGenerator – Company-Scale Roadmap

> **Goal**: evolve GameGenerator from a single-game scaffolder into a full
> **game-studio creation platform** — the kind of toolchain that powers studios
> like Ubisoft, Blizzard, or EA.  Every section below is a concrete feature
> area with prioritised tasks you can pick up independently.

---

## Vision in one sentence

> *A developer types a prompt, GameGenerator builds a complete, shippable game
> studio: code, assets, backend services, CI/CD, monetisation, analytics, and
> live-ops — all production-ready from day one.*

---

## Phase 1 – Multi-Engine Support  *(already planned)*

The current implementation targets **Flutter/Flame (2D)**. The plugin
architecture is already in place; add an engine adapter by implementing
`generate_files(spec)` for the new engine.

| Engine | Status | Notes |
|--------|--------|-------|
| Flutter/Flame | ✅ Done | Mobile-first, 2D |
| Unity (C#) | 🔲 Next | 2D & 3D; most popular |
| Godot 4 (GDScript) | 🔲 Next | Open-source; great 2D/3D |
| Unreal Engine (C++) | 🔲 Future | AAA-quality 3D |
| Bevy (Rust) | 🔲 Future | High-performance indie 3D |

**What to build:**
- `gamegenerator/engines/unity/` – `generate_files()` produces C# MonoBehaviours,
  `*.unity` scene stubs, `*.asmdef` files, `Packages/manifest.json`.
- `gamegenerator/engines/godot/` – generates `.gd` scripts, `project.godot`,
  `*.tscn` scene files.
- `EngineSpec` schema field: add `engine: str` to `BuildSpec`.
- `ConstraintResolver` asks / enforces per-engine limits (e.g. Godot supports 3D).

---

## Phase 2 – More Genres

Two genres exist today.  Big studios ship dozens.

| Genre | Complexity | Key systems |
|-------|-----------|-------------|
| Platformer | Medium | Physics, ledge grabs, checkpoints |
| Battle Royale | High | Map shrink, loot, 100-player server |
| MOBA | High | Tower defence, minions, abilities |
| Card Game / CCG | Medium | Deck builder, hand management |
| Puzzle (match-3) | Low | Grid, swap, combo chain |
| Tower Defence | Medium | Pathing, wave manager, upgrades |
| Roguelite | Medium | Procedural map, permadeath, run meta |
| Racing | Medium | Physics, lap timer, AI opponents |
| Visual Novel | Low | Dialogue tree, CG, save/load |
| City Builder | High | Economy simulation, building grid |
| Open-World RPG | Very high | Quest system, inventory, AI NPC |

**What to build:**
- One Python file per genre in `gamegenerator/genres/`.
- Each genre must provide: required entities, asset roles, core loop, controls,
  performance hints, and working generated Dart/C#/GDScript code.
- Genre tag a `GameSpec` with `sub_genre` for variants (e.g. `roguelite_shooter`).

---

## Phase 3 – 3D Asset Pipeline

Going beyond 2D sprites requires a proper 3D asset pipeline.

**What to build:**
- `AssetSpec` extensions: `mesh`, `material`, `animation_clip`, `shader`.
- Auto-convert `.fbx` / `.obj` / `.gltf` to engine-native format via
  `assimp` (Python bindings: `pyassimp`).
- Texture atlasing: pack multiple small textures into one atlas to reduce
  draw calls.
- LOD (Level-of-Detail) generator: produce 3 LOD meshes per model.
- Audio normaliser: `pydub` to normalise volumes, convert to `ogg`.
- Sprite-sheet generator: `Pillow` to pack individual frames into atlas.

---

## Phase 4 – AI Game Design Assistant

Extend the existing Ollama integration into a full game-design co-pilot.

**What to build:**
- `GameDesignAgent`: multi-turn chat to refine `GameSpec` before scaffolding.
- **Procedural level generation**: prompt → Ollama → JSON level layout →
  generate tilemap or procedural code.
- **Dialogue writer**: NPC dialogue trees generated from character descriptions.
- **Balance tuner**: feed telemetry data back to the AI → suggest stat changes.
- **Art style prompt generator**: given `art_style=pixel-art`, generate
  Stable Diffusion / DALL-E prompts for every required asset role.
- Pluggable LLM backends: `OllamaBackend`, `OpenAIBackend`, `AnthropicBackend`.

---

## Phase 5 – Backend Services (like Blizzard Battle.net / Ubisoft Connect)

A real game company has cloud infrastructure. Generate it too.

### 5a. Core backend scaffold

- `BackendSpec` schema: authentication, leaderboard, matchmaking, inventory, analytics.
- Generate a **FastAPI** Python backend with:
  - `POST /auth/register`, `POST /auth/login` (JWT)
  - `GET /leaderboard/{game_id}` (Redis sorted set)
  - `POST /match/find` (simple Elo-based matchmaking queue)
  - `GET /player/{id}/inventory`
  - `POST /events` (analytics ingest)
- Generate a **Docker Compose** stack: API + PostgreSQL + Redis.
- Generate a matching **Flutter SDK** that the game calls automatically.

### 5b. Multiplayer (real-time)

- WebSocket server (`python-socketio` or Go) scaffolded by the generator.
- Flame integration: generated `MultiplayerManager` component using `socket_io_client`.
- Room-based lobbies, state sync, lag compensation hints.

### 5c. Live Operations (LiveOps)

- Event calendar system: timed events, seasonal content, limited-time offers.
- Remote config: push game tuning values without an app update.
- A/B testing framework: split players into cohorts, track KPIs.

---

## Phase 6 – Monetisation Systems

Ubisoft and Blizzard earn billions through in-game monetisation.

**What to generate:**
- **Battle Pass** scaffold: season progress, rewards, premium/free tracks.
- **In-App Purchase (IAP)**: `pubspec.yaml` dependency on `in_app_purchase`;
  generated store catalogue, receipt validation against backend.
- **Rewarded ads** integration: `google_mobile_ads` dependency; placement in
  game-over / level-complete screens.
- **Cosmetic shop**: skins, emotes, bundles — no pay-to-win.
- **Virtual currency**: soft currency (coins), hard currency (gems);
  economy balance hints based on genre.

---

## Phase 7 – Analytics & Telemetry

Data-driven studios iterate fast because they measure everything.

**What to build:**
- Event schema generator: `GameEvent` TypedDict → Dart code + backend endpoint.
- Auto-instrument generated games with:
  - Session start/end
  - Level start/end/fail
  - Purchase events
  - Retention triggers (D1, D7, D30)
- Dashboard scaffold: **Grafana** + **ClickHouse** Docker Compose.
- Funnel visualiser: show where players drop off.
- LTV (Lifetime Value) calculator.

---

## Phase 8 – CI/CD Pipeline Generator

Every AAA studio has a build pipeline. Generate it.

**What to build:**
- `CISpec` schema: triggers, platforms, signing, distribution.
- Generate **GitHub Actions** workflows:
  - `flutter test` on every PR.
  - `flutter build apk` + `flutter build ipa` on merge to `main`.
  - Upload to **Firebase App Distribution** or **TestFlight**.
- Generate **fastlane** `Fastfile` for automated store submission.
- Semantic versioning: auto-bump `pubspec.yaml` version on tag.
- Crash reporting: add `firebase_crashlytics` to `pubspec.yaml` + init code.

---

## Phase 9 – Localisation Pipeline

Blizzard ships in 13+ languages from day one.

**What to build:**
- `l10n/` folder generation with `app_en.arb`, `app_fr.arb`, etc.
- Flutter `intl` package scaffolding.
- String extraction: parse generated Dart for hard-coded strings,
  output `.arb` template.
- AI translation: call DeepL / Google Translate API to fill `.arb` files
  for requested locales.
- RTL (right-to-left) layout hints for Arabic / Hebrew.

---

## Phase 10 – QA & Playtesting Tools

**What to build:**
- **Automated play-test bot**: Flutter integration test that drives the game
  with random inputs and reports crashes.
- **Screenshot regression tester**: captures frames at key game states,
  diffs against a golden image.
- **Performance profiler**: integration with `flutter drive --profile` to
  extract FPS, jank, and memory stats.
- **Balance simulator**: Python simulation of the game loop (no rendering)
  to check if the game is winnable in target time.

---

## Phase 11 – Studio Management Portal

The generator itself needs a web UI for non-technical designers.

**What to build:**
- **React/Next.js** web app that wraps the GameGenerator Python API.
- Drag-and-drop genre builder: pick mechanics, entities, art style.
- Asset browser: upload assets, see role assignments.
- Live preview: render a low-fidelity mockup of the game layout.
- Project history: track every generated game, diff specs over time.
- Team collaboration: multiple designers on one `GameSpec`.

---

## Phase 12 – Marketplace & Community

How Ubisoft and Blizzard build ecosystems.

**What to build:**
- **Genre plugin marketplace**: publish and install community genre packs
  (`pip install gamegen-genre-platformer`).
- **Asset pack registry**: index of free/paid asset packs with role metadata.
- **Template gallery**: curated `GameSpec` templates for popular game styles.
- **Studio profiles**: public showcase of games built with GameGenerator.

---

## Implementation Priority Matrix

| Phase | Impact | Effort | Start? |
|-------|--------|--------|--------|
| 1 – Unity engine | 🔴 High | Medium | ✅ Yes |
| 2 – Platformer genre | 🔴 High | Low | ✅ Yes |
| 4 – AI design assistant | 🔴 High | Medium | ✅ Yes |
| 5a – FastAPI backend | 🟠 High | Medium | Soon |
| 7 – Analytics | 🟠 Medium | Low | Soon |
| 8 – CI/CD | 🟠 Medium | Low | Soon |
| 3 – 3D asset pipeline | 🟡 Medium | High | Later |
| 6 – Monetisation | 🟡 Medium | Medium | Later |
| 9 – Localisation | 🟡 Medium | Low | Later |
| 10 – QA tools | 🟡 Medium | Medium | Later |
| 11 – Web portal | 🟢 Low | High | Future |
| 12 – Marketplace | 🟢 Low | Very High | Future |

---

## Nearest Next Steps (pick any)

```
1. Add Unity engine adapter
   gamegenerator/engines/unity/generate_files.py

2. Add Platformer genre
   gamegenerator/genres/platformer.py

3. Add Godot 4 adapter
   gamegenerator/engines/godot/generate_files.py

4. Generate a FastAPI backend alongside the Flutter project
   gamegenerator/backends/fastapi_backend.py

5. Add a `GameDesignAgent` multi-turn chat in orchestrator
   gamegenerator/orchestrator/design_agent.py

6. Add AI asset-prompt generator (Stable Diffusion / DALL-E)
   gamegenerator/ai/asset_prompter.py

7. Generate GitHub Actions CI workflow file
   gamegenerator/ci/github_actions.py

8. Add localization scaffold (flutter_localizations)
   gamegenerator/l10n/localizer.py
```

---

## Summary

The table below maps GameGenerator features to what companies like
Ubisoft and Blizzard actually ship:

| Studio capability | GameGenerator equivalent |
|------------------|--------------------------|
| Multi-title engine pipeline | Multi-engine adapters (Phase 1) |
| Proprietary game engine | Flame / Unity / Godot adapters |
| Level design tools | AI level generator (Phase 4) |
| Asset pipeline | 3D asset tools + atlasing (Phase 3) |
| Online platform (B.net / Ubisoft Connect) | Backend scaffold (Phase 5) |
| Battle Pass / Shop | Monetisation generator (Phase 6) |
| Data analytics team | Analytics scaffold (Phase 7) |
| QA department | Automated playtesting (Phase 10) |
| Localisation team | l10n pipeline (Phase 9) |
| Automated builds | CI/CD generator (Phase 8) |
| Designer tools | Web portal (Phase 11) |
| Modding community | Marketplace (Phase 12) |
