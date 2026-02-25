"""Tests for ArtPromptGenerator – no network or GPU required."""

import pytest
from gamedesign_agent.art_prompting import ArtPromptGenerator, ArtPrompt, GeneratedImage


class TestArtPromptGenerator:
    def setup_method(self):
        self.gen = ArtPromptGenerator(art_backend="none")

    def test_returns_art_prompt(self):
        prompt = self.gen.generate_prompt(seed=1)
        assert isinstance(prompt, ArtPrompt)

    def test_positive_prompt_nonempty(self):
        prompt = self.gen.generate_prompt(seed=2)
        assert prompt.positive.strip() != ""

    def test_negative_prompt_nonempty(self):
        prompt = self.gen.generate_prompt(seed=3)
        assert prompt.negative.strip() != ""

    def test_deterministic_with_same_seed(self):
        p1 = self.gen.generate_prompt(seed=42)
        p2 = self.gen.generate_prompt(seed=42)
        assert p1.positive == p2.positive
        assert p1.negative == p2.negative

    def test_different_seeds_differ(self):
        p1 = self.gen.generate_prompt(seed=1)
        p2 = self.gen.generate_prompt(seed=9999)
        # Extremely high probability they differ
        assert p1.positive != p2.positive

    def test_scene_type_stored(self):
        prompt = self.gen.generate_prompt(scene_type="forest", seed=5)
        assert prompt.scene_type == "forest"

    def test_style_stored(self):
        prompt = self.gen.generate_prompt(style="pixel", seed=6)
        assert prompt.style == "pixel"

    def test_seed_stored(self):
        prompt = self.gen.generate_prompt(seed=7777)
        assert prompt.seed == 7777

    def test_description_included_in_positive(self):
        prompt = self.gen.generate_prompt(description="glowing sword", seed=8)
        assert "glowing sword" in prompt.positive

    def test_extra_tags_included(self):
        prompt = self.gen.generate_prompt(extra_tags=["volumetric lighting"], seed=9)
        assert "volumetric lighting" in prompt.positive

    def test_all_styles_produce_prompts(self):
        for style in self.gen.list_styles():
            p = self.gen.generate_prompt(style=style, seed=0)
            assert p.positive.strip() != ""

    def test_all_scene_types_produce_prompts(self):
        for scene in self.gen.list_scene_types():
            p = self.gen.generate_prompt(scene_type=scene, seed=0)
            assert p.positive.strip() != ""

    def test_unknown_style_falls_back_gracefully(self):
        # Should not raise; falls back to "fantasy" pool
        p = self.gen.generate_prompt(style="unknown_style_xyz", seed=11)
        assert p.positive.strip() != ""

    def test_unknown_scene_falls_back_gracefully(self):
        # Should not raise; uses the scene string itself
        p = self.gen.generate_prompt(scene_type="alien spaceship", seed=12)
        assert p.positive.strip() != ""

    def test_to_dict_keys(self):
        prompt = self.gen.generate_prompt(seed=13)
        d = prompt.to_dict()
        for key in ("positive", "negative", "style", "scene_type", "seed"):
            assert key in d

    def test_generate_image_none_backend_returns_no_image(self):
        prompt = self.gen.generate_prompt(seed=14)
        result = self.gen.generate_image(prompt)
        assert isinstance(result, GeneratedImage)
        assert result.image_path is None
        assert result.image_b64 is None
        assert result.backend_used == "none"

    def test_character_prompt_helper(self):
        p = self.gen.generate_character_prompt(
            character_class="warrior", race="elf", seed=15
        )
        assert "warrior" in p.positive
        assert "elf" in p.positive

    def test_environment_prompt_helper(self):
        p = self.gen.generate_environment_prompt(biome="tundra", seed=16)
        assert "tundra" in p.positive

    def test_prompt_str(self):
        p = self.gen.generate_prompt(seed=17)
        assert str(p) == p.positive
