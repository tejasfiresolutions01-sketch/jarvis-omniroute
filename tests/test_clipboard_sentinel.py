"""
Unit tests for J.A.R.V.I.S. Smart Windows Clipboard Sentinel.
"""

import unittest
from unittest.mock import patch, MagicMock
from tools.clipboard_sentinel import ClipboardSentinel

class TestClipboardSentinel(unittest.TestCase):

    def setUp(self):
        self.sentinel = ClipboardSentinel()

    def test_classify_content(self):
        self.assertEqual(self.sentinel.classify_content(""), "empty")
        self.assertEqual(self.sentinel.classify_content("https://github.com/omniroute"), "url")
        self.assertEqual(self.sentinel.classify_content('{"key": "value"}'), "json")
        self.assertEqual(self.sentinel.classify_content("git status --short"), "shell_command")
        self.assertEqual(self.sentinel.classify_content("def compute_velocity():\n    return 42"), "python_code")
        self.assertEqual(self.sentinel.classify_content("Traceback (most recent call last):\nValueError: bad input"), "stack_trace")
        self.assertEqual(self.sentinel.classify_content("This is a simple paragraph of text."), "prose")

    @patch("pyperclip.paste", return_value="Traceback (most recent call last):\n  File \"core/brain.py\", line 42\nValueError: invalid input")
    def test_explain_stack_trace(self, mock_paste):
        exp = self.sentinel.explain_clipboard()
        self.assertIn("stack trace", exp)
        self.assertIn("ValueError", exp)
        self.assertIn("line 42", exp)

    @patch("pyperclip.paste", return_value="https://starkindustries.com/schematics")
    def test_explain_url(self, mock_paste):
        exp = self.sentinel.explain_clipboard()
        self.assertIn("starkindustries.com", exp)

    @patch("pyperclip.copy")
    @patch("pyperclip.paste", return_value="def flight_stabilizer(altitude)\n    return altitude * 2")
    def test_fix_clipboard_code(self, mock_paste, mock_copy):
        ok, msg = self.sentinel.fix_clipboard_code()
        self.assertTrue(ok)
        self.assertIn("Syntax corrections applied", msg)
        mock_copy.assert_called_with("def flight_stabilizer(altitude):\n    return altitude * 2")

    @patch("core.vector_memory.vector_memory.store_memory", return_value=99)
    @patch("pyperclip.paste", return_value="Stark Arc-Reactor Mark 85 vibration dampener specs")
    def test_save_clipboard_to_memory(self, mock_paste, mock_store):
        msg = self.sentinel.save_clipboard_to_memory(category="note")
        self.assertIn("committed to long-term neural recall", msg)
        self.assertIn("#99", msg)
        mock_store.assert_called_once()

    @patch("pyperclip.paste", return_value="Short directive")
    def test_summarize_clipboard_short(self, mock_paste):
        summ = self.sentinel.summarize_clipboard()
        self.assertIn("Short directive", summ)


if __name__ == "__main__":
    unittest.main()
