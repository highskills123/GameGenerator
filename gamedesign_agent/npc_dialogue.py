"""
npc_dialogue.py – NPC dialogue writer.

Generates contextually appropriate dialogue lines for NPCs.

Two modes:
  1. **Template mode** (default, fully offline): rule-based templates with
     variable substitution – no network, no GPU required.
  2. **LLM mode** (optional): delegates generation to the configured LLM
     backend (Ollama or HuggingFace Inference API).
"""

from __future__ import annotations

import random
import textwrap
from typing import Dict, List, Optional

from . import config


# ---------------------------------------------------------------------------
# Dialogue templates
# ---------------------------------------------------------------------------

_TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    # npc_type -> mood -> [template strings]
    "merchant": {
        "friendly": [
            "Welcome, traveler! I have the finest {goods} in {location}.",
            "Ah, a customer! Looking for {goods}? You've come to the right place.",
            "Step right up! My {goods} are the best coin can buy.",
        ],
        "neutral": [
            "What'll it be? I have {goods}.",
            "Browse as you like. Asking price is fair.",
        ],
        "hostile": [
            "I'm watching you. Touch anything without coin and you'll regret it.",
            "Keep your hands where I can see them, {player_class}.",
        ],
    },
    "guard": {
        "friendly": [
            "Safe travels, {player_class}! The road to {location} is clear today.",
            "Ho there! Nothing to report on the {direction} gate.",
        ],
        "neutral": [
            "Move along.",
            "Stay out of trouble.",
            "The {location} is under Lord {lord_name}'s protection.",
        ],
        "hostile": [
            "Halt! State your business in {location}!",
            "You're not welcome here, {player_class}. Turn around.",
            "One more step and I'll call the garrison.",
        ],
    },
    "wizard": {
        "friendly": [
            "Ah, curious mind! The arcane arts hold secrets no mortal fully grasps.",
            "I sense great potential in you, young {player_class}.",
            "The stars foretold your arrival. Welcome to {location}.",
        ],
        "neutral": [
            "Knowledge is power — but power demands sacrifice.",
            "Speak plainly; I have experiments to attend to.",
        ],
        "hostile": [
            "You dare interrupt my research?! Begone!",
            "My patience for interruptions ended three centuries ago.",
        ],
    },
    "villager": {
        "friendly": [
            "Good day! Lovely weather we're having near {location}.",
            "Have you heard? They say the {direction} forest is haunted!",
            "My family's lived here for generations. {location} is home.",
        ],
        "neutral": [
            "Busy day. Can I help you with something?",
            "The harvest's been poor lately, but we manage.",
        ],
        "hostile": [
            "Strangers bring trouble. We don't want any here.",
            "Leave us be!",
        ],
    },
    "enemy": {
        "friendly": [],
        "neutral": [
            "You shouldn't have come here, {player_class}.",
            "This is your last warning.",
        ],
        "hostile": [
            "For {faction}! Charge!",
            "You'll pay for what you did to {location}!",
            "No prisoners!",
            "I've faced worse than you, {player_class}.",
        ],
    },
    "quest_giver": {
        "friendly": [
            "Thank goodness you're here! I have an urgent task – please hear me out.",
            "I've been searching for someone capable. You look like you can handle {quest_type}.",
            "Word of your deeds precedes you, {player_class}. I need your help.",
        ],
        "neutral": [
            "I have a job for someone brave enough. Interested?",
            "The reward is generous. The danger… considerable.",
        ],
        "hostile": [
            "You failed me once. Don't expect another chance.",
        ],
    },
}

_VARIABLE_POOLS: Dict[str, List[str]] = {
    "goods": ["potions", "weapons", "armor", "rare herbs", "enchanted scrolls", "food supplies"],
    "location": ["Riverdale", "Ashfort", "the Northern Keep", "Dawnmere", "the Capital", "Shadowgate"],
    "player_class": ["warrior", "rogue", "mage", "paladin", "ranger", "monk"],
    "direction": ["north", "south", "east", "west"],
    "lord_name": ["Aldric", "Maren", "Vexton", "Oswyn", "Crestfall"],
    "faction": ["the Dark Legion", "the Iron Brotherhood", "the Serpent Cult", "Lord Vexton"],
    "quest_type": ["retrieving a lost relic", "clearing the mines", "escorting the caravan", "finding the missing heir"],
}


def _fill_template(template: str, rng: random.Random, overrides: Optional[Dict[str, str]] = None) -> str:
    """Replace {variable} placeholders in *template* with random pool values."""
    overrides = overrides or {}
    result = template
    for key, pool in _VARIABLE_POOLS.items():
        placeholder = f"{{{key}}}"
        if placeholder in result:
            value = overrides.get(key, rng.choice(pool))
            result = result.replace(placeholder, value)
    # Apply any overrides that didn't appear in the pool map
    for key, value in overrides.items():
        result = result.replace(f"{{{key}}}", value)
    return result


# ---------------------------------------------------------------------------
# NPCDialogueWriter
# ---------------------------------------------------------------------------

class NPCDialogueWriter:
    """
    Generates NPC dialogue lines.

    Parameters
    ----------
    llm_backend : str
        Overrides ``config.LLM_BACKEND``.  Set to ``"none"`` (default) for
        fully offline template-based generation.
    """

    def __init__(self, llm_backend: Optional[str] = None) -> None:
        self._backend = (llm_backend or config.LLM_BACKEND).lower()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        npc_type: str = "villager",
        mood: str = "neutral",
        num_lines: int = 3,
        context: Optional[str] = None,
        variable_overrides: Optional[Dict[str, str]] = None,
        seed: Optional[int] = None,
    ) -> List[str]:
        """
        Generate dialogue lines for an NPC.

        Parameters
        ----------
        npc_type : str
            One of: merchant, guard, wizard, villager, enemy, quest_giver.
        mood : str
            One of: friendly, neutral, hostile.
        num_lines : int
            Number of dialogue lines to generate.
        context : str, optional
            Free-text scene description forwarded to the LLM backend when
            ``llm_backend != "none"``.
        variable_overrides : dict, optional
            Fixed values for template placeholders (e.g. ``{"location": "Castle Grimwall"}``).
        seed : int, optional
            RNG seed for reproducible results.
        """
        if self._backend == "none":
            return self._template_generate(
                npc_type, mood, num_lines, variable_overrides, seed
            )
        elif self._backend == "ollama":
            return self._ollama_generate(npc_type, mood, num_lines, context, seed)
        elif self._backend == "hf_api":
            return self._hf_api_generate(npc_type, mood, num_lines, context, seed)
        else:
            raise ValueError(f"Unknown LLM backend: {self._backend!r}")

    def list_npc_types(self) -> List[str]:
        return list(_TEMPLATES.keys())

    def list_moods(self) -> List[str]:
        return ["friendly", "neutral", "hostile"]

    # ------------------------------------------------------------------
    # Template-based (offline)
    # ------------------------------------------------------------------

    def _template_generate(
        self,
        npc_type: str,
        mood: str,
        num_lines: int,
        variable_overrides: Optional[Dict[str, str]],
        seed: Optional[int],
    ) -> List[str]:
        rng = random.Random(seed)
        npc_type = npc_type.lower()
        mood = mood.lower()

        type_templates = _TEMPLATES.get(npc_type, _TEMPLATES["villager"])
        mood_templates = type_templates.get(mood, type_templates.get("neutral", []))

        # Fall back to neutral if chosen mood has no templates
        if not mood_templates:
            mood_templates = type_templates.get("neutral", [])
        if not mood_templates:
            # Generic fallback
            mood_templates = ["..."]

        pool = mood_templates * max(1, (num_lines // len(mood_templates)) + 1)
        rng.shuffle(pool)
        chosen = pool[:num_lines]
        return [_fill_template(t, rng, variable_overrides) for t in chosen]

    # ------------------------------------------------------------------
    # Ollama (optional, free local LLM)
    # ------------------------------------------------------------------

    def _ollama_generate(
        self,
        npc_type: str,
        mood: str,
        num_lines: int,
        context: Optional[str],
        seed: Optional[int],
    ) -> List[str]:
        try:
            import requests  # type: ignore
        except ImportError as e:
            raise ImportError("Install 'requests' to use the Ollama backend.") from e

        prompt = textwrap.dedent(f"""
            You are writing dialogue for a video game NPC.
            NPC type: {npc_type}
            Mood: {mood}
            Scene context: {context or 'generic fantasy RPG scene'}
            Write exactly {num_lines} short, in-character dialogue line(s).
            Respond with one line per dialogue entry, no numbering.
        """).strip()

        payload: dict = {
            "model": config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }
        if seed is not None:
            payload["options"] = {"seed": seed}

        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        text: str = response.json().get("response", "")
        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
        return lines[:num_lines] if lines else ["..."]

    # ------------------------------------------------------------------
    # HuggingFace Inference API (optional, free tier)
    # ------------------------------------------------------------------

    def _hf_api_generate(
        self,
        npc_type: str,
        mood: str,
        num_lines: int,
        context: Optional[str],
        seed: Optional[int],
    ) -> List[str]:
        try:
            import requests  # type: ignore
        except ImportError as e:
            raise ImportError("Install 'requests' to use the HF API backend.") from e

        if not config.HF_API_TOKEN:
            raise ValueError(
                "Set the HF_API_TOKEN environment variable to use the HuggingFace Inference API."
            )

        prompt = (
            f"[NPC: {npc_type}, mood: {mood}] "
            f"Context: {context or 'generic RPG'}. "
            f"Write {num_lines} dialogue line(s):"
        )
        headers = {"Authorization": f"Bearer {config.HF_API_TOKEN}"}
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 200, "do_sample": True},
        }
        if seed is not None:
            payload["parameters"]["seed"] = seed  # type: ignore[index]

        url = f"https://api-inference.huggingface.co/models/{config.HF_MODEL_ID}"
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        text = data[0].get("generated_text", "") if isinstance(data, list) else ""
        # Strip the prompt prefix if the model echoes it
        if text.startswith(prompt):
            text = text[len(prompt):].strip()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return lines[:num_lines] if lines else ["..."]
