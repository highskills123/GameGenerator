"""Tests for ConversationMemory – no network or GPU required."""

import pytest
from gamedesign_agent.conversation_memory import ConversationMemory, Message


class TestConversationMemory:
    def setup_method(self):
        self.mem = ConversationMemory(max_turns=5)

    def test_initial_history_empty(self):
        assert len(self.mem) == 0

    def test_add_message(self):
        self.mem.add_message("user", "Hello!")
        assert len(self.mem) == 1

    def test_history_preserves_roles(self):
        self.mem.add_message("user", "Hello")
        self.mem.add_message("assistant", "Hi there")
        history = self.mem.get_history()
        assert history[0].role == "user"
        assert history[1].role == "assistant"

    def test_history_preserves_content(self):
        self.mem.add_message("user", "What is a dungeon?")
        history = self.mem.get_history()
        assert history[0].content == "What is a dungeon?"

    def test_context_window_includes_system_prompt(self):
        self.mem.add_message("user", "Hello")
        window = self.mem.get_context_window()
        assert window[0].role == "system"

    def test_context_window_size_limit(self):
        # Add 12 messages (6 turns) when max_turns=5
        for i in range(12):
            role = "user" if i % 2 == 0 else "assistant"
            self.mem.add_message(role, f"msg {i}")
        window = self.mem.get_context_window()
        # system + 10 (5 turns * 2)
        assert len(window) <= 11  # system + max_turns*2

    def test_full_history_retained_beyond_window(self):
        for i in range(20):
            role = "user" if i % 2 == 0 else "assistant"
            self.mem.add_message(role, f"msg {i}")
        assert len(self.mem.get_history()) == 20

    def test_clear_empties_history(self):
        self.mem.add_message("user", "Hello")
        self.mem.clear()
        assert len(self.mem) == 0

    def test_last_assistant_message_none_when_empty(self):
        assert self.mem.last_assistant_message() is None

    def test_last_assistant_message_returns_latest(self):
        self.mem.add_message("user", "Hi")
        self.mem.add_message("assistant", "First reply")
        self.mem.add_message("user", "Follow up")
        self.mem.add_message("assistant", "Second reply")
        assert self.mem.last_assistant_message() == "Second reply"

    def test_invalid_role_raises(self):
        with pytest.raises(ValueError):
            self.mem.add_message("unknown_role", "oops")

    def test_to_dict_list_structure(self):
        self.mem.add_message("user", "hello")
        self.mem.add_message("assistant", "world")
        dicts = self.mem.to_dict_list()
        assert len(dicts) == 2
        assert dicts[0]["role"] == "user"
        assert dicts[1]["role"] == "assistant"
        assert "timestamp" in dicts[0]

    def test_message_dataclass(self):
        msg = Message(role="user", content="test")
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "test"
        assert "timestamp" in d

    def test_custom_system_prompt(self):
        mem = ConversationMemory(system_prompt="Be a pirate.")
        mem.add_message("user", "Hello")
        window = mem.get_context_window()
        assert window[0].content == "Be a pirate."

    def test_repr(self):
        r = repr(self.mem)
        assert "ConversationMemory" in r
