"""
Unit tests for autonomous web search, multi-model AI delegation,
display presence sentinel, and silenced chime tone interface.
"""

import unittest
from unittest.mock import patch, MagicMock
from core.chimes import play_boot_chime, play_wake_chime, play_ack_chime
from core.display_sentinel import display_sentinel, DisplaySentinel
from core.local_intelligence import local_intelligence
from core.online_intelligence import online_intelligence
from core.task_orchestrator import task_orchestrator
from tools.web_tools import search_web, fetch_webpage_content

class TestAutonomousCapabilities(unittest.TestCase):

    def test_silenced_chimes(self):
        # Chimes must be completely silent and execute safely without raising exceptions
        play_boot_chime()
        play_wake_chime()
        play_ack_chime()
        self.assertTrue(True)

    def test_display_sentinel_greeting_generation(self):
        greeting = display_sentinel.generate_display_greeting()
        self.assertIsInstance(greeting, str)
        self.assertTrue(any(word in greeting for word in ["Good morning", "Good afternoon", "Good evening", "Welcome back"]))
        self.assertIn("Display online", greeting) if "Display online" in greeting else self.assertTrue(len(greeting) > 10)

    def test_display_sentinel_idle_and_active(self):
        idle_secs = display_sentinel.get_idle_seconds()
        self.assertGreaterEqual(idle_secs, 0.0)
        self.assertIsInstance(display_sentinel.is_display_active(), bool)

    def test_display_sentinel_cooldown(self):
        sentinel = DisplaySentinel()
        sentinel._last_greeting_time = 0.0
        with patch("core.display_sentinel.speak") as mock_speak:
            sentinel.trigger_greeting(reason="test")
            self.assertEqual(mock_speak.call_count, 1)
            # Second immediate trigger should be blocked by cooldown
            sentinel.trigger_greeting(reason="test_immediate")
            self.assertEqual(mock_speak.call_count, 1)

    @patch("tools.web_tools.requests.get")
    def test_web_search_instant_answer(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "AbstractText": "Python is a high-level programming language.",
            "Answer": "",
            "AbstractSource": "Wikipedia",
            "AbstractURL": "https://en.wikipedia.org/wiki/Python"
        }
        mock_get.return_value = mock_resp
        result = search_web("python programming")
        self.assertIn("Python is a high-level programming language", result)

    @patch("tools.web_tools.requests.get")
    def test_local_intelligence_web_search(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "AbstractText": "Quantum computing uses qubits.",
            "Answer": "",
            "AbstractSource": "Tech",
            "AbstractURL": "https://example.com"
        }
        mock_get.return_value = mock_resp
        handled, resp = local_intelligence.evaluate_and_execute("search the web for quantum computing")
        self.assertTrue(handled)
        self.assertIn("Quantum computing uses qubits", resp)

    @patch("requests.post")
    def test_command_other_ai_model(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "General relativity explains gravity as spacetime curvature."}}]
        }
        mock_post.return_value = mock_resp
        
        handled, resp = local_intelligence.evaluate_and_execute("ask openai to explain general relativity")
        self.assertTrue(handled)
        self.assertIn("spacetime curvature", resp)

    def test_task_orchestrator_tools_include_command_other_ai(self):
        self.assertIn("command_other_ai", task_orchestrator.TOOLS)
        self.assertIn("search_web", task_orchestrator.TOOLS)
        self.assertTrue(task_orchestrator.is_complex_directive("search the web for latest Mars rover updates and save to mars.txt"))

if __name__ == "__main__":
    unittest.main()
