"""
gamedesign_agent/agent.py – NPC dialogue and game design agent.

Supports a lightweight ``llm_backend="none"`` mode that generates
template-based NPC dialogue entirely offline (no external service required).
"""

from __future__ import annotations

import random
from typing import List, Optional

# ---------------------------------------------------------------------------
# Default NPC dialogue templates
# ---------------------------------------------------------------------------

_DIALOGUE_TEMPLATES: dict = {
    "merchant": [
        "Welcome, traveller! Take a look at my wares.",
        "Finest goods in the kingdom, I assure you.",
        "You look like someone who appreciates quality.",
        "Special discount for adventurers today!",
        "Come back anytime. My shop is always open.",
    ],
    "guard": [
        "Halt! State your business.",
        "Move along. Nothing to see here.",
        "The city is under my protection.",
        "Stay out of trouble, traveller.",
        "Report any suspicious activity to the barracks.",
    ],
    "wizard": [
        "Ah, another seeker of arcane knowledge.",
        "The stars whisper secrets to those who listen.",
        "Magic is a double-edged blade. Use it wisely.",
        "I have studied for decades. Ask and I shall answer.",
        "Beware the darkness that stirs to the east.",
    ],
    "quest_giver": [
        "I need your help, adventurer.",
        "There is a task only someone of your skill can accomplish.",
        "The reward will be generous, I promise.",
        "Time is of the essence. Will you accept?",
        "Return to me when the deed is done.",
    ],
    "enemy": [
        "You dare challenge me?!",
        "Foolish hero. Your end is near.",
        "I will grind your bones to dust!",
        "You cannot defeat me!",
        "Curse you, adventurer!",
    ],
    "villager": [
        "Good day to you, traveller.",
        "These are dangerous times.",
        "Have you heard the news from the capital?",
        "Stay safe on the roads.",
        "May fortune smile upon you.",
    ],
}

_DEFAULT_NPC_TYPE = "villager"


class GameDesignAgent:
    """
    Lightweight game design agent for generating NPC dialogue and other
    game content.

    Parameters
    ----------
    llm_backend:
        Backend to use for generation.  Currently only ``"none"`` is
        supported, which uses built-in templates and requires no external
        services.
    """

    def __init__(self, llm_backend: str = "none") -> None:
        self.llm_backend = llm_backend

    def write_npc_dialogue(
        self,
        npc_type: str = "villager",
        num_lines: int = 3,
        seed: Optional[int] = None,
    ) -> List[str]:
        """
        Return a list of dialogue lines for the given NPC type.

        Parameters
        ----------
        npc_type:
            One of ``"merchant"``, ``"guard"``, ``"wizard"``,
            ``"quest_giver"``, ``"enemy"``, or ``"villager"``.
        num_lines:
            Number of dialogue lines to return.
        seed:
            Optional random seed for reproducibility.

        Returns
        -------
        List[str]
            A list of ``num_lines`` dialogue strings.
        """
        rng = random.Random(seed)
        templates = _DIALOGUE_TEMPLATES.get(npc_type, _DIALOGUE_TEMPLATES[_DEFAULT_NPC_TYPE])
        num_lines = max(1, num_lines)
        if num_lines <= len(templates):
            return rng.sample(templates, num_lines)
        # Repeat with shuffling when more lines are requested than templates
        lines: List[str] = []
        while len(lines) < num_lines:
            shuffled = templates[:]
            rng.shuffle(shuffled)
            lines.extend(shuffled)
        return lines[:num_lines]
