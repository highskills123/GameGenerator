"""
gamedesign_agent – AI-powered NPC dialogue and game design assistant.

Public API
----------
    from gamedesign_agent.agent import GameDesignAgent

    agent = GameDesignAgent(llm_backend="none")
    lines = agent.write_npc_dialogue(npc_type="merchant", num_lines=3, seed=42)
"""

from .agent import GameDesignAgent  # noqa: F401

__all__ = ["GameDesignAgent"]
