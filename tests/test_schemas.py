"""
Unit tests for schemas.GameSpecModel and schemas.IdleRpgDesignDocModel.

Validates:
  - valid payloads are accepted
  - invalid/missing fields raise ValueError with helpful messages
  - .model_dump() includes schema_version
  - validate_* helpers surface Pydantic errors as plain ValueError
"""

import unittest

from schemas.game_spec import (
    GAME_SPEC_SCHEMA_VERSION,
    GameSpecModel,
    validate_game_spec,
)
from schemas.idle_rpg_design_doc import (
    IDLE_RPG_DESIGN_DOC_SCHEMA_VERSION,
    IdleRpgDesignDocModel,
    validate_idle_rpg_design_doc,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_game_spec(**overrides) -> dict:
    """Return a minimal valid GameSpec dict."""
    base = {
        "title": "Space Blaster",
        "genre": "top_down_shooter",
        "mechanics": ["move", "shoot"],
        "required_assets": ["player", "enemy"],
        "screens": ["main_menu", "game"],
        "controls": {"keyboard": ["WASD"], "mobile": ["joystick"]},
        "progression": {"scoring": "points", "levels": 5},
    }
    base.update(overrides)
    return base


def _minimal_design_doc(**overrides) -> dict:
    """Return a minimal valid IdleRpgDesignDoc dict."""
    base = {
        "world": "A frozen kingdom.",
        "premise": "Heroes break the ice witch's curse.",
        "main_story_beats": ["Act 1", "Act 2"],
        "quests": [{"title": "First Quest", "summary": "Go forth."}],
        "characters": [{"name": "Aria", "role": "protagonist"}],
        "factions": [{"name": "The Order", "alignment": "lawful good"}],
        "locations": [{"name": "Frostholm", "type": "city"}],
        "items": [{"name": "Frost Blade", "type": "weapon"}],
        "enemies": [{"name": "Ice Wolf", "type": "beast"}],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# GameSpecModel tests
# ---------------------------------------------------------------------------


class TestGameSpecModel(unittest.TestCase):
    # --- Valid payloads ---

    def test_valid_minimal_spec_accepted(self):
        model = validate_game_spec(_minimal_game_spec())
        self.assertIsInstance(model, GameSpecModel)

    def test_schema_version_default(self):
        model = validate_game_spec(_minimal_game_spec())
        self.assertEqual(model.schema_version, GAME_SPEC_SCHEMA_VERSION)

    def test_schema_version_constant_value(self):
        self.assertEqual(GAME_SPEC_SCHEMA_VERSION, "1.0")

    def test_model_dump_includes_schema_version(self):
        model = validate_game_spec(_minimal_game_spec())
        dumped = model.model_dump()
        self.assertIn("schema_version", dumped)
        self.assertEqual(dumped["schema_version"], GAME_SPEC_SCHEMA_VERSION)

    def test_model_dump_contains_core_fields(self):
        model = validate_game_spec(_minimal_game_spec())
        dumped = model.model_dump()
        for key in ("title", "genre", "mechanics", "required_assets", "screens", "controls", "progression"):
            self.assertIn(key, dumped)

    def test_optional_fields_accepted(self):
        spec = _minimal_game_spec(
            core_loop="Move → shoot → survive",
            art_style="pixel-art",
            platform="android",
            scope="prototype",
            dimension="2D",
            orientation="landscape",
            online=False,
        )
        model = validate_game_spec(spec)
        self.assertEqual(model.art_style, "pixel-art")
        self.assertEqual(model.orientation, "landscape")

    def test_idle_rpg_genre_accepted(self):
        spec = _minimal_game_spec(genre="idle_rpg")
        model = validate_game_spec(spec)
        self.assertEqual(model.genre, "idle_rpg")

    def test_extra_keys_preserved_in_dump(self):
        spec = _minimal_game_spec(custom_field="custom_value")
        model = validate_game_spec(spec)
        dumped = model.model_dump()
        self.assertEqual(dumped["custom_field"], "custom_value")

    # --- Invalid payloads ---

    def test_missing_required_title_raises(self):
        spec = _minimal_game_spec()
        del spec["title"]
        with self.assertRaises(ValueError) as ctx:
            validate_game_spec(spec)
        self.assertIn("title", str(ctx.exception))

    def test_missing_required_genre_raises(self):
        spec = _minimal_game_spec()
        del spec["genre"]
        with self.assertRaises(ValueError) as ctx:
            validate_game_spec(spec)
        self.assertIn("genre", str(ctx.exception))

    def test_missing_required_mechanics_raises(self):
        spec = _minimal_game_spec()
        del spec["mechanics"]
        with self.assertRaises(ValueError) as ctx:
            validate_game_spec(spec)
        self.assertIn("mechanics", str(ctx.exception))

    def test_missing_required_screens_raises(self):
        spec = _minimal_game_spec()
        del spec["screens"]
        with self.assertRaises(ValueError) as ctx:
            validate_game_spec(spec)
        self.assertIn("screens", str(ctx.exception))

    def test_invalid_genre_raises(self):
        spec = _minimal_game_spec(genre="unknown_genre")
        with self.assertRaises(ValueError) as ctx:
            validate_game_spec(spec)
        self.assertIn("genre", str(ctx.exception))

    def test_empty_mechanics_raises(self):
        spec = _minimal_game_spec(mechanics=[])
        with self.assertRaises(ValueError) as ctx:
            validate_game_spec(spec)
        self.assertIn("mechanics", str(ctx.exception))

    def test_empty_required_assets_raises(self):
        spec = _minimal_game_spec(required_assets=[])
        with self.assertRaises(ValueError) as ctx:
            validate_game_spec(spec)
        self.assertIn("required_assets", str(ctx.exception))

    def test_error_message_lists_field_names(self):
        """ValueError message must name the problematic fields."""
        spec = _minimal_game_spec()
        del spec["title"]
        del spec["mechanics"]
        with self.assertRaises(ValueError) as ctx:
            validate_game_spec(spec)
        msg = str(ctx.exception)
        self.assertIn("GameSpec validation failed", msg)

    def test_multiple_missing_fields_reported(self):
        spec = _minimal_game_spec()
        del spec["title"]
        del spec["screens"]
        with self.assertRaises(ValueError) as ctx:
            validate_game_spec(spec)
        msg = str(ctx.exception)
        self.assertIn("title", msg)
        self.assertIn("screens", msg)


# ---------------------------------------------------------------------------
# IdleRpgDesignDocModel tests
# ---------------------------------------------------------------------------


class TestIdleRpgDesignDocModel(unittest.TestCase):
    # --- Valid payloads ---

    def test_valid_minimal_doc_accepted(self):
        model = validate_idle_rpg_design_doc(_minimal_design_doc())
        self.assertIsInstance(model, IdleRpgDesignDocModel)

    def test_schema_version_default(self):
        model = validate_idle_rpg_design_doc(_minimal_design_doc())
        self.assertEqual(model.schema_version, IDLE_RPG_DESIGN_DOC_SCHEMA_VERSION)

    def test_schema_version_constant_value(self):
        self.assertEqual(IDLE_RPG_DESIGN_DOC_SCHEMA_VERSION, "1.0")

    def test_model_dump_includes_schema_version(self):
        model = validate_idle_rpg_design_doc(_minimal_design_doc())
        dumped = model.model_dump()
        self.assertIn("schema_version", dumped)

    def test_model_dump_contains_core_fields(self):
        model = validate_idle_rpg_design_doc(_minimal_design_doc())
        dumped = model.model_dump()
        for key in ("world", "premise", "main_story_beats", "quests", "characters",
                    "factions", "locations", "items", "enemies"):
            self.assertIn(key, dumped)

    def test_optional_idle_loops_accepted(self):
        doc = _minimal_design_doc(
            idle_loops=[{"name": "Gold Farm", "resource": "gold", "tick_rate_seconds": 5}]
        )
        model = validate_idle_rpg_design_doc(doc)
        self.assertIsNotNone(model.idle_loops)
        self.assertEqual(len(model.idle_loops), 1)

    def test_optional_upgrade_tree_accepted(self):
        doc = _minimal_design_doc(upgrade_tree={"Combat": [{"name": "Power Strike"}]})
        model = validate_idle_rpg_design_doc(doc)
        self.assertIsNotNone(model.upgrade_tree)

    def test_optional_dialogue_samples_accepted(self):
        doc = _minimal_design_doc(
            dialogue_samples=[{"character": "Elder", "lines": ["Beware!"]}]
        )
        model = validate_idle_rpg_design_doc(doc)
        self.assertIsNotNone(model.dialogue_samples)

    def test_extra_keys_preserved_in_dump(self):
        doc = _minimal_design_doc(extra_data="some_value")
        model = validate_idle_rpg_design_doc(doc)
        dumped = model.model_dump()
        self.assertEqual(dumped["extra_data"], "some_value")

    # --- Invalid payloads ---

    def test_missing_required_world_raises(self):
        doc = _minimal_design_doc()
        del doc["world"]
        with self.assertRaises(ValueError) as ctx:
            validate_idle_rpg_design_doc(doc)
        self.assertIn("world", str(ctx.exception))

    def test_missing_required_quests_raises(self):
        doc = _minimal_design_doc()
        del doc["quests"]
        with self.assertRaises(ValueError) as ctx:
            validate_idle_rpg_design_doc(doc)
        self.assertIn("quests", str(ctx.exception))

    def test_missing_required_enemies_raises(self):
        doc = _minimal_design_doc()
        del doc["enemies"]
        with self.assertRaises(ValueError) as ctx:
            validate_idle_rpg_design_doc(doc)
        self.assertIn("enemies", str(ctx.exception))

    def test_blank_world_raises(self):
        doc = _minimal_design_doc(world="   ")
        with self.assertRaises(ValueError) as ctx:
            validate_idle_rpg_design_doc(doc)
        self.assertIn("world", str(ctx.exception))

    def test_blank_premise_raises(self):
        doc = _minimal_design_doc(premise="")
        with self.assertRaises(ValueError) as ctx:
            validate_idle_rpg_design_doc(doc)
        self.assertIn("premise", str(ctx.exception))

    def test_empty_quests_list_raises(self):
        doc = _minimal_design_doc(quests=[])
        with self.assertRaises(ValueError) as ctx:
            validate_idle_rpg_design_doc(doc)
        self.assertIn("quests", str(ctx.exception))

    def test_empty_enemies_list_raises(self):
        doc = _minimal_design_doc(enemies=[])
        with self.assertRaises(ValueError) as ctx:
            validate_idle_rpg_design_doc(doc)
        self.assertIn("enemies", str(ctx.exception))

    def test_error_message_prefix(self):
        doc = _minimal_design_doc()
        del doc["world"]
        with self.assertRaises(ValueError) as ctx:
            validate_idle_rpg_design_doc(doc)
        self.assertIn("IdleRpgDesignDoc validation failed", str(ctx.exception))

    def test_multiple_missing_fields_reported(self):
        doc = _minimal_design_doc()
        del doc["world"]
        del doc["quests"]
        with self.assertRaises(ValueError) as ctx:
            validate_idle_rpg_design_doc(doc)
        msg = str(ctx.exception)
        self.assertIn("world", msg)
        self.assertIn("quests", msg)


if __name__ == "__main__":
    unittest.main()
