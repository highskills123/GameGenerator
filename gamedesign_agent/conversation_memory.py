"""
conversation_memory.py – Multi-turn conversation state for GameDesignAgent.

No external dependencies required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timezone

from . import config


@dataclass
class Message:
    """A single turn in a conversation."""

    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content, "timestamp": self.timestamp}


class ConversationMemory:
    """
    Stores the conversation history and provides a sliding context window.

    Parameters
    ----------
    system_prompt : str, optional
        An initial system-level instruction placed at the top of every context.
    max_turns : int
        Maximum *user+assistant* turn-pairs kept in the sliding window.
        Older messages are dropped from the context (but remain in full history).
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        max_turns: int = config.CONTEXT_WINDOW,
    ) -> None:
        self._system_prompt = system_prompt or (
            "You are a helpful AI game design assistant. "
            "You help designers with level design, NPC dialogue, "
            "procedural generation, and art direction."
        )
        self._max_turns = max_turns
        self._history: List[Message] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_message(self, role: str, content: str) -> None:
        """Append a new message to the history."""
        if role not in ("user", "assistant", "system"):
            raise ValueError(f"Invalid role: {role!r}")
        self._history.append(Message(role=role, content=content))

    def get_history(self) -> List[Message]:
        """Return the full (untruncated) conversation history."""
        return list(self._history)

    def get_context_window(self) -> List[Message]:
        """
        Return the messages that fit within the context window, always
        prefixed by the system prompt.
        """
        # Keep at most max_turns * 2 messages (each turn = 1 user + 1 assistant)
        window_size = self._max_turns * 2
        recent = self._history[-window_size:] if len(self._history) > window_size else self._history
        system_msg = Message(role="system", content=self._system_prompt)
        return [system_msg] + list(recent)

    def clear(self) -> None:
        """Erase conversation history (keeps system prompt)."""
        self._history.clear()

    def last_assistant_message(self) -> Optional[str]:
        """Return the content of the most recent assistant turn, or None."""
        for msg in reversed(self._history):
            if msg.role == "assistant":
                return msg.content
        return None

    def to_dict_list(self) -> List[dict]:
        """Serialise the full history to a list of plain dicts."""
        return [m.to_dict() for m in self._history]

    def __len__(self) -> int:
        return len(self._history)

    def __repr__(self) -> str:
        return f"ConversationMemory(turns={len(self._history)}, max_turns={self._max_turns})"
