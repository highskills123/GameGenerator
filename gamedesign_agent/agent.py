"""
agent.py – GameDesignAgent: the multi-turn AI Design Assistant.

Ties together ConversationMemory, ProceduralLevelGenerator,
NPCDialogueWriter, and ArtPromptGenerator into a single chat-style agent.

Supported LLM backends (all free):
  "none"    – rule-based / template responses (fully offline, default)
  "ollama"  – local Ollama server
  "hf_api"  – HuggingFace Inference API (free tier)
"""

from __future__ import annotations

import json
import re
import textwrap
from typing import Dict, List, Optional

from . import config
from .art_prompting import ArtPrompt, ArtPromptGenerator
from .conversation_memory import ConversationMemory
from .level_generation import Level, ProceduralLevelGenerator
from .npc_dialogue import NPCDialogueWriter


# ---------------------------------------------------------------------------
# Intent patterns for rule-based routing (used in "none" backend)
# ---------------------------------------------------------------------------

_INTENT_PATTERNS: List[tuple] = [
    # (intent_name, compiled_regex)
    ("generate_level", re.compile(
        r"\b(level|dungeon|map|room|floor|generate.*level|level.*gen)\b", re.I
    )),
    ("npc_dialogue", re.compile(
        r"\b(dialogue|dialog|npc|character.*say|talk|conversation|quote)\b", re.I
    )),
    ("art_prompt", re.compile(
        r"\b(art|image|picture|sprite|concept art|stable diffusion|dall.?e|prompt|visual)\b", re.I
    )),
    ("game_design_advice", re.compile(
        r"\b(design|mechanic|balance|gameplay|fun|feedback|improve|suggest)\b", re.I
    )),
]

_DESIGN_TIPS: List[str] = [
    "Consider adding a risk-reward trade-off: let players choose between a safe path and a dangerous one with better loot.",
    "Good game feel often comes from responsive controls and satisfying visual/audio feedback rather than complex mechanics.",
    "For level pacing, alternate between tense combat encounters and quiet exploration areas to give players breathing room.",
    "Playtesting early and often is more valuable than polishing mechanics that players might not engage with.",
    "Give NPCs clear visual reads – silhouette, colour palette, and animation should communicate intent at a glance.",
    "Economy design tip: ensure the player always has meaningful choices about how to spend their resources.",
    "Introduce new mechanics one at a time; each should be taught through the environment before being tested.",
    "Emergent gameplay arises when simple rules interact in unexpected ways – look for those interactions deliberately.",
    "For multiplayer balance, start with symmetry and introduce asymmetry only after the base case is solid.",
    "Narrative and gameplay are strongest when they reinforce each other – the theme should be felt in the mechanics.",
]


class GameDesignAgent:
    """
    Multi-turn AI Game Design Assistant.

    Parameters
    ----------
    llm_backend : str, optional
        Override for ``config.LLM_BACKEND``.
    system_prompt : str, optional
        Override for the system-level instructions.
    """

    def __init__(
        self,
        llm_backend: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        self._backend = (llm_backend or config.LLM_BACKEND).lower()
        self.memory = ConversationMemory(system_prompt=system_prompt)
        self._level_gen = ProceduralLevelGenerator()
        self._npc_writer = NPCDialogueWriter(llm_backend=llm_backend or config.LLM_BACKEND)
        self._art_gen = ArtPromptGenerator()
        self._tip_index = 0

    # ------------------------------------------------------------------
    # Multi-turn chat
    # ------------------------------------------------------------------

    def chat(self, user_message: str) -> str:
        """
        Send a user message and receive an assistant reply.
        Conversation history is maintained across calls.
        """
        self.memory.add_message("user", user_message)

        if self._backend == "none":
            response = self._rule_based_response(user_message)
        elif self._backend == "ollama":
            response = self._ollama_response()
        elif self._backend == "hf_api":
            response = self._hf_api_response()
        else:
            raise ValueError(f"Unknown LLM backend: {self._backend!r}")

        self.memory.add_message("assistant", response)
        return response

    def reset(self) -> None:
        """Clear conversation history."""
        self.memory.clear()

    # ------------------------------------------------------------------
    # Convenience wrappers (also usable standalone / from CLI)
    # ------------------------------------------------------------------

    def generate_level(self, seed: Optional[int] = None, **kwargs) -> Level:
        """Generate and return a procedural level."""
        gen = ProceduralLevelGenerator(**kwargs) if kwargs else self._level_gen
        return gen.generate(seed=seed)

    def write_npc_dialogue(
        self,
        npc_type: str = "villager",
        mood: str = "neutral",
        num_lines: int = 3,
        context: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> List[str]:
        """Generate NPC dialogue lines."""
        return self._npc_writer.generate(
            npc_type=npc_type, mood=mood, num_lines=num_lines,
            context=context, seed=seed
        )

    def create_art_prompt(
        self,
        scene_type: str = "dungeon",
        style: str = "fantasy",
        description: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> ArtPrompt:
        """Generate a Stable Diffusion / DALL-E art prompt."""
        return self._art_gen.generate_prompt(
            scene_type=scene_type, style=style,
            description=description, seed=seed
        )

    # ------------------------------------------------------------------
    # Rule-based routing (backend == "none")
    # ------------------------------------------------------------------

    def _rule_based_response(self, user_message: str) -> str:
        intent = self._detect_intent(user_message)

        if intent == "generate_level":
            level = self._level_gen.generate(seed=config.DEFAULT_SEED)
            ascii_map = level.to_ascii()
            return (
                f"Here is a generated dungeon level (seed {level.seed}):\n\n"
                f"```\n{ascii_map}\n```\n\n"
                f"Rooms: {level.metadata['room_count']} | "
                f"Corridors: {level.metadata['corridor_count']}\n"
                "Tip: Pass `--seed <N>` on the CLI to regenerate the same layout."
            )

        if intent == "npc_dialogue":
            lines = self._npc_writer.generate(seed=config.DEFAULT_SEED)
            formatted = "\n".join(f"  • {l}" for l in lines)
            return f"Here are some NPC dialogue lines:\n{formatted}"

        if intent == "art_prompt":
            prompt = self._art_gen.generate_prompt(seed=config.DEFAULT_SEED)
            return (
                f"**Positive prompt:**\n{prompt.positive}\n\n"
                f"**Negative prompt:**\n{prompt.negative}\n\n"
                "Copy these into your Stable Diffusion / DALL-E interface."
            )

        if intent == "game_design_advice":
            tip = _DESIGN_TIPS[self._tip_index % len(_DESIGN_TIPS)]
            self._tip_index += 1
            return f"💡 Game design tip:\n\n{tip}"

        # Generic fallback
        return (
            "I'm your AI Game Design Assistant! I can help you with:\n"
            "  • 🗺️  Procedural level generation\n"
            "  • 💬  NPC dialogue writing\n"
            "  • 🎨  Art prompts for Stable Diffusion / DALL-E\n"
            "  • 🎮  Game design advice\n\n"
            "Try asking: 'Generate a dungeon level', 'Write dialogue for a merchant', "
            "or 'Create an art prompt for a forest scene'."
        )

    def _detect_intent(self, text: str) -> Optional[str]:
        for intent, pattern in _INTENT_PATTERNS:
            if pattern.search(text):
                return intent
        return None

    # ------------------------------------------------------------------
    # Ollama backend
    # ------------------------------------------------------------------

    def _ollama_response(self) -> str:
        try:
            import requests  # type: ignore
        except ImportError as e:
            raise ImportError("Install 'requests' to use the Ollama backend.") from e

        messages = [
            {"role": m.role, "content": m.content}
            for m in self.memory.get_context_window()
        ]
        payload = {
            "model": config.OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
        }
        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "...")

    # ------------------------------------------------------------------
    # HuggingFace Inference API backend
    # ------------------------------------------------------------------

    def _hf_api_response(self) -> str:
        try:
            import requests  # type: ignore
        except ImportError as e:
            raise ImportError("Install 'requests' to use the HF API backend.") from e

        if not config.HF_API_TOKEN:
            raise ValueError("Set HF_API_TOKEN to use the HuggingFace Inference API.")

        # Build a single prompt string from the context window
        context = self.memory.get_context_window()
        prompt = "\n".join(
            f"[{m.role.upper()}]: {m.content}" for m in context
        ) + "\n[ASSISTANT]:"

        headers = {"Authorization": f"Bearer {config.HF_API_TOKEN}"}
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 400, "do_sample": True, "temperature": 0.8},
        }
        url = f"https://api-inference.huggingface.co/models/{config.HF_MODEL_ID}"
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        text = data[0].get("generated_text", "") if isinstance(data, list) else ""
        # Strip echoed prompt
        marker = "[ASSISTANT]:"
        idx = text.rfind(marker)
        if idx >= 0:
            text = text[idx + len(marker):].strip()
        return text or "..."
