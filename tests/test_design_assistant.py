"""
Unit tests for gamegenerator.ai.design_assistant – JSON parsing/validation utilities.

These tests run entirely offline (no Ollama required) by exercising the internal
_parse_and_validate and _strip_code_fences helpers directly.
"""

import json
import unittest

from game_generator.ai.design_assistant import (
    REQUIRED_KEYS,
    _parse_and_validate,
    _strip_code_fences,
    design_doc_to_markdown,
)


def _minimal_doc(**overrides) -> dict:
    """Return a minimal valid design document dict."""
    base = {
        "world": "A cursed kingdom frozen in eternal winter.",
        "premise": "Heroes rise to break the ice witch's curse.",
        "main_story_beats": ["Act 1: Arrival", "Act 2: Trials", "Act 3: Finale"],
        "quests": [
            {
                "title": "The First Trial",
                "summary": "Prove your worth.",
                "objectives": ["Defeat 10 wolves"],
                "rewards": ["100 gold"],
                "giver": "Elder",
                "level_range": [1, 5],
            }
        ],
        "characters": [
            {
                "name": "Aria",
                "role": "protagonist",
                "backstory": "A wandering knight.",
                "motivations": ["Protect the innocent"],
                "relationships": {"Elder": "mentor"},
            }
        ],
        "factions": [
            {
                "name": "The Order",
                "description": "Knights sworn to protect.",
                "alignment": "lawful good",
                "goals": ["Restore peace"],
            }
        ],
        "locations": [
            {
                "name": "Frostholm",
                "description": "A frozen city.",
                "type": "city",
                "notable_features": ["Ice palace"],
            }
        ],
        "items": [
            {
                "name": "Frost Blade",
                "type": "weapon",
                "rarity": "rare",
                "description": "A blade of eternal ice.",
                "stats": {"attack": 50},
            }
        ],
        "enemies": [
            {
                "name": "Ice Wolf",
                "type": "beast",
                "description": "A wolf made of living ice.",
                "abilities": ["Frost Bite"],
                "loot": ["Wolf Pelt"],
            }
        ],
    }
    base.update(overrides)
    return base


class TestStripCodeFences(unittest.TestCase):
    def test_no_fence_unchanged(self):
        raw = '{"key": "value"}'
        self.assertEqual(_strip_code_fences(raw), raw)

    def test_json_fence_stripped(self):
        raw = '```json\n{"key": "value"}\n```'
        self.assertEqual(_strip_code_fences(raw), '{"key": "value"}')

    def test_plain_fence_stripped(self):
        raw = '```\n{"key": "value"}\n```'
        self.assertEqual(_strip_code_fences(raw), '{"key": "value"}')

    def test_leading_whitespace_stripped(self):
        raw = '  \n```json\n{"x": 1}\n```\n  '
        self.assertEqual(_strip_code_fences(raw), '{"x": 1}')


class TestParseAndValidate(unittest.TestCase):
    def test_valid_doc_passes(self):
        raw = json.dumps(_minimal_doc())
        result = _parse_and_validate(raw)
        self.assertIsInstance(result, dict)
        for key in REQUIRED_KEYS:
            self.assertIn(key, result)

    def test_code_fenced_json_parsed(self):
        raw = "```json\n" + json.dumps(_minimal_doc()) + "\n```"
        result = _parse_and_validate(raw)
        self.assertIsInstance(result, dict)

    def test_invalid_json_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            _parse_and_validate("not valid json {{{")
        self.assertIn("not valid JSON", str(ctx.exception))

    def test_missing_required_key_raises(self):
        doc = _minimal_doc()
        del doc["quests"]
        with self.assertRaises(ValueError) as ctx:
            _parse_and_validate(json.dumps(doc))
        self.assertIn("quests", str(ctx.exception))

    def test_wrong_type_list_raises(self):
        doc = _minimal_doc(quests="not a list")
        with self.assertRaises(ValueError) as ctx:
            _parse_and_validate(json.dumps(doc))
        self.assertIn("quests", str(ctx.exception))

    def test_wrong_type_string_raises(self):
        doc = _minimal_doc(world=42)
        with self.assertRaises(ValueError) as ctx:
            _parse_and_validate(json.dumps(doc))
        self.assertIn("world", str(ctx.exception))

    def test_non_dict_top_level_raises(self):
        with self.assertRaises(ValueError) as ctx:
            _parse_and_validate(json.dumps([1, 2, 3]))
        self.assertIn("JSON object", str(ctx.exception))

    def test_json_with_preamble_extracted(self):
        """If LLM adds text before the JSON object, it should still parse."""
        preamble = "Here is the design document:\n"
        raw = preamble + json.dumps(_minimal_doc())
        result = _parse_and_validate(raw)
        self.assertIn("world", result)

    def test_optional_keys_preserved(self):
        doc = _minimal_doc()
        doc["idle_loops"] = [
            {"name": "Gold Farm", "description": "Earn gold.", "resource": "gold", "tick_rate_seconds": 5}
        ]
        result = _parse_and_validate(json.dumps(doc))
        self.assertIn("idle_loops", result)


class TestDesignDocToMarkdown(unittest.TestCase):
    def setUp(self):
        self.doc = _minimal_doc()
        self.md = design_doc_to_markdown(self.doc)

    def test_returns_string(self):
        self.assertIsInstance(self.md, str)

    def test_contains_world_heading(self):
        self.assertIn("## World", self.md)

    def test_contains_world_content(self):
        self.assertIn("cursed kingdom", self.md)

    def test_contains_quests_heading(self):
        self.assertIn("## Quests", self.md)

    def test_contains_quest_title(self):
        self.assertIn("The First Trial", self.md)

    def test_contains_characters_heading(self):
        self.assertIn("## Characters", self.md)

    def test_contains_character_name(self):
        self.assertIn("Aria", self.md)

    def test_contains_enemies_heading(self):
        self.assertIn("## Enemies", self.md)

    def test_optional_idle_loops_rendered(self):
        doc = _minimal_doc()
        doc["idle_loops"] = [
            {"name": "Gold Farm", "description": "Earn gold automatically.",
             "resource": "gold", "tick_rate_seconds": 5}
        ]
        md = design_doc_to_markdown(doc)
        self.assertIn("## Idle Loops", md)
        self.assertIn("Gold Farm", md)

    def test_optional_upgrade_tree_rendered(self):
        doc = _minimal_doc()
        doc["upgrade_tree"] = {
            "Combat": [{"name": "Power Strike", "description": "Extra damage."}]
        }
        md = design_doc_to_markdown(doc)
        self.assertIn("## Upgrade Tree", md)
        self.assertIn("Power Strike", md)


if __name__ == "__main__":
    unittest.main()
