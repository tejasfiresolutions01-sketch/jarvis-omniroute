"""
Unit tests for human-like voice conversational flow, phonetics normalization,
and multi-turn conversation memory.
"""

import time
import unittest
from core.voice import clean_for_speech, check_is_speaking
from core.conversation_memory import ConversationMemory, conversation_memory

class TestHumanConversation(unittest.TestCase):

    def test_clean_for_speech_markdown_stripping(self):
        raw = "**Certainly, sir!** Here is the `status`: *all systems nominal*.\n\n### Metrics\n- CPU: 24%\n- RAM: 8.5GB"
        cleaned = clean_for_speech(raw)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("*", cleaned)
        self.assertNotIn("`", cleaned)
        self.assertNotIn("###", cleaned)
        self.assertIn("percent", cleaned)
        self.assertIn("gigabytes", cleaned)
        self.assertIn("C P U", cleaned)
        self.assertIn("R A M", cleaned)

    def test_clean_for_speech_unit_expansion(self):
        raw = "Temperature is 42°C with 100MHz speed."
        cleaned = clean_for_speech(raw)
        self.assertIn("degrees Celsius", cleaned)
        self.assertIn("megahertz", cleaned)

    def test_clean_for_speech_emoji_stripping(self):
        raw = "All good! 🚀 Jarvis online 🤖✨"
        cleaned = clean_for_speech(raw)
        self.assertNotIn("🚀", cleaned)
        self.assertNotIn("🤖", cleaned)
        self.assertNotIn("✨", cleaned)
        self.assertIn("All good", cleaned)

    def test_clean_for_speech_urls_and_symbols(self):
        raw = "Check [Dashboard](http://localhost:5050) & let me know."
        cleaned = clean_for_speech(raw)
        self.assertNotIn("http://", cleaned)
        self.assertIn("Dashboard", cleaned)
        self.assertIn("and let me know", cleaned)

    def test_conversation_memory_add_and_retrieve(self):
        mem = ConversationMemory(max_turns=5, idle_timeout_seconds=10)
        mem.add_turn("user", "What is my current battery level?")
        mem.add_turn("assistant", "Your battery is at 85 percent, sir.")
        
        history = mem.get_recent_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")
        
        prompt_block = mem.format_for_system_prompt()
        self.assertIn("User: What is my current battery level?", prompt_block)
        self.assertIn("Assistant: Your battery is at 85 percent, sir.", prompt_block)

    def test_conversation_memory_sliding_window(self):
        mem = ConversationMemory(max_turns=4, idle_timeout_seconds=60)
        mem.add_turn("user", "Turn 1")
        mem.add_turn("assistant", "Response 1")
        mem.add_turn("user", "Turn 2")
        mem.add_turn("assistant", "Response 2")
        mem.add_turn("user", "Turn 3")
        mem.add_turn("assistant", "Response 3")

        history = mem.get_recent_history()
        self.assertEqual(len(history), 4) # 4 messages retained
        self.assertEqual(history[0]["content"], "Turn 2")
        self.assertEqual(history[-1]["content"], "Response 3")

    def test_conversation_memory_idle_expiration(self):
        mem = ConversationMemory(max_turns=5, idle_timeout_seconds=0.1)
        mem.add_turn("user", "Remember this")
        time.sleep(0.2)
        history = mem.get_recent_history()
        self.assertEqual(len(history), 0)

    def test_conversation_memory_clear(self):
        mem = ConversationMemory()
        mem.add_turn("user", "Test")
        self.assertGreater(len(mem.get_recent_history()), 0)
        mem.clear()
        self.assertEqual(len(mem.get_recent_history()), 0)

    def test_check_is_speaking_boolean_type(self):
        self.assertIsInstance(check_is_speaking(), bool)

if __name__ == "__main__":
    unittest.main()
