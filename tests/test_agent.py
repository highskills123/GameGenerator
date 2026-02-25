"""Tests for GameDesignAgent (rule-based / "none" backend) – no network or GPU required."""

import pytest
from gamedesign_agent.agent import GameDesignAgent
from gamedesign_agent.level_generation import Level
from gamedesign_agent.art_prompting import ArtPrompt


class TestGameDesignAgent:
    def setup_method(self):
        self.agent = GameDesignAgent(llm_backend="none")

    def test_chat_returns_string(self):
        response = self.agent.chat("Hello!")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_adds_to_memory(self):
        self.agent.chat("Tell me about level design.")
        assert len(self.agent.memory) == 2  # user + assistant

    def test_chat_level_intent(self):
        response = self.agent.chat("Can you generate a dungeon level for me?")
        assert isinstance(response, str)
        # Should contain map or level info
        assert len(response) > 10

    def test_chat_npc_intent(self):
        response = self.agent.chat("Write some NPC dialogue for a merchant.")
        assert isinstance(response, str)
        assert len(response) > 10

    def test_chat_art_intent(self):
        response = self.agent.chat("Create an art prompt for a stable diffusion image.")
        assert "prompt" in response.lower() or len(response) > 20

    def test_chat_design_advice_intent(self):
        response = self.agent.chat("Give me game design advice on mechanics.")
        assert isinstance(response, str)
        assert len(response) > 10

    def test_reset_clears_memory(self):
        self.agent.chat("Hello")
        self.agent.reset()
        assert len(self.agent.memory) == 0

    def test_generate_level_returns_level(self):
        level = self.agent.generate_level(seed=42)
        assert isinstance(level, Level)

    def test_generate_level_deterministic(self):
        l1 = self.agent.generate_level(seed=42)
        l2 = self.agent.generate_level(seed=42)
        assert l1.to_ascii() == l2.to_ascii()

    def test_write_npc_dialogue_returns_list(self):
        lines = self.agent.write_npc_dialogue(npc_type="guard", mood="hostile", seed=1)
        assert isinstance(lines, list)
        assert len(lines) > 0

    def test_create_art_prompt_returns_prompt(self):
        prompt = self.agent.create_art_prompt(scene_type="castle", style="realistic", seed=5)
        assert isinstance(prompt, ArtPrompt)
        assert prompt.positive.strip() != ""

    def test_multi_turn_conversation(self):
        """Multiple turns should accumulate in memory."""
        self.agent.chat("Hello!")
        self.agent.chat("Generate a level.")
        self.agent.chat("Now write NPC dialogue.")
        assert len(self.agent.memory) == 6  # 3 user + 3 assistant

    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError):
            bad_agent = GameDesignAgent(llm_backend="unknown_backend_xyz")
            bad_agent.chat("hello")
