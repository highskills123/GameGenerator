# Schema Reference & Versioning Strategy

This document describes the two canonical schemas used in the GameGenerator
pipeline and explains how schema versions are managed.

---

## Table of Contents

1. [Overview](#overview)
2. [GameSpec](#gamespec)
3. [IdleRpgDesignDoc](#idlerpgdesigndoc)
4. [Versioning Strategy](#versioning-strategy)
5. [Validation Integration](#validation-integration)
6. [Serialisation](#serialisation)

---

## Overview

All structured data produced or consumed by the pipeline is validated against
one of two Pydantic v2 models:

| Model | Module | Used by |
|---|---|---|
| `GameSpecModel` | `schemas.game_spec` | `game_generator.spec` (heuristic + Ollama) |
| `IdleRpgDesignDocModel` | `schemas.idle_rpg_design_doc` | `game_generator.ai.design_assistant` |

Both models carry a `schema_version` field so that stored artefacts can be
migrated forward when the schema evolves.

---

## GameSpec

**Module:** `schemas.game_spec`  
**Version constant:** `GAME_SPEC_SCHEMA_VERSION = "1.0"`

### Required fields

| Field | Type | Description |
|---|---|---|
| `title` | `str` | Human-readable game title |
| `genre` | `str` | Must be `top_down_shooter` or `idle_rpg` |
| `mechanics` | `list[str]` | Non-empty list of gameplay mechanics |
| `required_assets` | `list[str]` | Non-empty list of asset role names |
| `screens` | `list[str]` | Non-empty list of screen names |
| `controls` | `dict` | Keyboard and/or mobile control mappings |
| `progression` | `dict` | Scoring, level count, difficulty settings |

### Optional fields

| Field | Type | Default | Description |
|---|---|---|---|
| `schema_version` | `str` | `"1.0"` | Schema revision |
| `core_loop` | `str` | `None` | One-sentence game loop description |
| `entities` | `list[dict]` | `None` | Player, enemy, projectile, pickup entities |
| `performance_hints` | `list[str]` | `None` | Flame/Flutter performance tips |
| `art_style` | `str` | `None` | `pixel-art`, `vector`, or `hand-drawn` |
| `platform` | `str` | `None` | `android` or `android+ios` |
| `scope` | `str` | `None` | `prototype` or `vertical-slice` |
| `dimension` | `str` | `None` | `2D` (Flame only supports 2D) |
| `orientation` | `str` | `None` | `portrait` or `landscape` |
| `online` | `bool` | `None` | Whether the game has online features |
| `assets_dir` | `str` | `None` | Source directory for imported assets |

### Usage

```python
from schemas.game_spec import validate_game_spec, GAME_SPEC_SCHEMA_VERSION

spec = {
    "title": "Space Blaster",
    "genre": "top_down_shooter",
    "mechanics": ["move", "shoot"],
    "required_assets": ["player", "enemy", "bullet"],
    "screens": ["main_menu", "game", "game_over"],
    "controls": {"keyboard": ["WASD", "space"], "mobile": ["joystick"]},
    "progression": {"scoring": "points", "levels": 5},
}

model = validate_game_spec(spec)   # raises ValueError if invalid
data = model.model_dump()          # dict with schema_version included
```

---

## IdleRpgDesignDoc

**Module:** `schemas.idle_rpg_design_doc`  
**Version constant:** `IDLE_RPG_DESIGN_DOC_SCHEMA_VERSION = "1.0"`

### Required fields

| Field | Type | Description |
|---|---|---|
| `world` | `str` | Non-blank world / setting description |
| `premise` | `str` | Non-blank core narrative premise |
| `main_story_beats` | `list[str]` | Non-empty list of story milestones |
| `quests` | `list[dict]` | Non-empty list of quest objects |
| `characters` | `list[dict]` | Non-empty list of character objects |
| `factions` | `list[dict]` | Non-empty list of faction objects |
| `locations` | `list[dict]` | Non-empty list of location objects |
| `items` | `list[dict]` | Non-empty list of item objects |
| `enemies` | `list[dict]` | Non-empty list of enemy objects |

### Optional fields

| Field | Type | Default | Description |
|---|---|---|---|
| `schema_version` | `str` | `"1.0"` | Schema revision |
| `dialogue_samples` | `list[dict]` | `None` | Per-character sample dialogue |
| `upgrade_tree` | `dict` | `None` | Category-keyed upgrade tree |
| `idle_loops` | `list[dict]` | `None` | Idle resource-generation loops |

### Usage

```python
from schemas.idle_rpg_design_doc import (
    validate_idle_rpg_design_doc,
    IDLE_RPG_DESIGN_DOC_SCHEMA_VERSION,
)

doc = { ... }   # parsed from Ollama output
model = validate_idle_rpg_design_doc(doc)   # raises ValueError if invalid
data = model.model_dump()                    # dict with schema_version included
```

---

## Versioning Strategy

Schema versions follow **`MAJOR.MINOR`** (e.g. `"1.0"`).

| Change type | Action |
|---|---|
| Adding a new **optional** field | Bump `MINOR` (e.g. `"1.0"` → `"1.1"`) |
| Adding a new **required** field | Bump `MAJOR` (e.g. `"1.0"` → `"2.0"`) |
| Removing or renaming any field | Bump `MAJOR` |
| Changing a field's type | Bump `MAJOR` |

### How to bump a version

1. Update the version constant in the relevant schema module:
   ```python
   # schemas/game_spec.py
   GAME_SPEC_SCHEMA_VERSION = "1.1"   # was "1.0"
   ```
2. Update the Pydantic model to reflect the change.
3. Update this document.
4. Write a migration helper if stored artefacts need updating.

### Reading the version from stored artefacts

Every serialised dict produced by `.model_dump()` includes `schema_version`.
Use it to detect and migrate old artefacts:

```python
if data.get("schema_version", "1.0") == "1.0":
    # apply migration to 1.1 ...
    data["new_field"] = default_value
    data["schema_version"] = "1.1"
```

---

## Validation Integration

Validation is applied automatically at the two pipeline boundaries:

### `game_generator.spec.generate_spec`

* **Heuristic path** – `_heuristic_spec()` calls `_validate()` before
  returning.  Because the heuristic always produces all required fields this
  should never fail in practice; any future regression in the heuristic will
  surface immediately.

* **Ollama path** – `_ollama_spec()` calls `_validate()` after receiving the
  model output.  If validation fails (e.g. the LLM omitted a required field)
  the function returns `None` and the pipeline falls back to the heuristic.

### `game_generator.ai.design_assistant._parse_and_validate`

After the existing key-presence and type checks, `_parse_and_validate` calls
`validate_idle_rpg_design_doc()`.  Invalid documents raise `ValueError` with
a message that names every problematic field.

---

## Serialisation

Both models use Pydantic's built-in `.model_dump()`:

```python
model = validate_game_spec(spec)
output = model.model_dump()    # plain dict, JSON-serialisable
```

`model_dump()` always includes `schema_version`, making it safe to write
directly to JSON artefacts or pass to downstream workers.

Extra keys not declared in the model are preserved (the models use
`model_config = {"extra": "allow"}`), so adding ad-hoc fields to a spec dict
does not cause validation failures.
