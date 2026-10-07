"""
J.A.R.V.I.S. Multi-Turn Conversational Memory Matrix.
Maintains immediate context and short-term dialogue history so J.A.R.V.I.S.
can converse like an attentive human, seamlessly tracking pronouns ("he", "that", "it"),
follow-up questions, and conversational threads across turns.
"""

import threading
import time
from typing import List, Dict, Optional, Any

class ConversationMemory:
    """
    Thread-Safe Rolling Dialogue Buffer.
    Preserves recent conversational turns with automatic idle-decay.
    """

    MAX_TURNS = 10         # Keeps last 10 messages (5 dialogue rounds)
    IDLE_TIMEOUT = 300.0   # 5 minutes idle time before fresh conversational slate

    def __init__(self, max_turns: int = MAX_TURNS, idle_timeout: float = IDLE_TIMEOUT, idle_timeout_seconds: Optional[float] = None):
        self.max_turns = max_turns
        self.idle_timeout = idle_timeout_seconds if idle_timeout_seconds is not None else idle_timeout
        self.history: List[Dict[str, str]] = []
        self._lock = threading.Lock()
        self._last_interaction_time = time.time()

    def add_turn(self, role: str, content: str):
        """Adds a speech turn to short-term memory ('user' or 'assistant')."""
        if not content or not content.strip():
            return

        with self._lock:
            # Check for idle expiration
            now = time.time()
            if self.history and (now - self._last_interaction_time > self.idle_timeout):
                self.history.clear()

            self._last_interaction_time = now
            self.history.append({"role": role, "content": content.strip()})

            # Trim to max turns
            if len(self.history) > self.max_turns:
                self.history = self.history[-self.max_turns:]

    def get_messages(self) -> List[Dict[str, str]]:
        """Returns clean list of message dicts formatted for LLM completion payloads."""
        with self._lock:
            now = time.time()
            if self.history and (now - self._last_interaction_time > self.idle_timeout):
                self.history.clear()
                return []
            return list(self.history)

    def get_recent_history(self) -> List[Dict[str, str]]:
        """Alias for get_messages()."""
        return self.get_messages()

    def get_context_string(self) -> str:
        """Formats conversational turns into human-readable dialogue context."""
        with self._lock:
            now = time.time()
            if self.history and (now - self._last_interaction_time > self.idle_timeout):
                self.history.clear()
                return ""

            if not self.history:
                return ""

            lines = []
            for msg in self.history:
                speaker = "Sir" if msg["role"] == "user" else "J.A.R.V.I.S."
                lines.append(f"{speaker}: {msg['content']}")
            return "\n".join(lines)

    def format_for_system_prompt(self) -> str:
        """Formats recent history as a multi-turn context block for LLM prompts."""
        with self._lock:
            now = time.time()
            if self.history and (now - self._last_interaction_time > self.idle_timeout):
                self.history.clear()
                return ""

            if not self.history:
                return ""

            lines = []
            for msg in self.history:
                role_label = "User" if msg["role"] == "user" else "Assistant"
                lines.append(f"{role_label}: {msg['content']}")
            return "\n".join(lines)

    def clear(self):
        """Clears short-term conversation memory on user directive or reset."""
        with self._lock:
            self.history.clear()
            self._last_interaction_time = time.time()

    def is_empty(self) -> bool:
        with self._lock:
            return len(self.history) == 0

# Global singleton
conversation_memory = ConversationMemory()
