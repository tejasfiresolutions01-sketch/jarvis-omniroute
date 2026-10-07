"""
Unit tests for J.A.R.V.I.S. Global Hotkey Sentinel.
"""

import unittest
from unittest.mock import patch, MagicMock
from tools.global_hotkey import GlobalHotkeyManager

class TestGlobalHotkey(unittest.TestCase):

    def setUp(self):
        self.mgr = GlobalHotkeyManager()

    def test_initialization(self):
        self.assertFalse(self.mgr.running)
        self.assertEqual(len(self.mgr.registered_ids), 0)
        self.assertIsNone(self.mgr.callback)

    @patch("ctypes.windll.user32.RegisterHotKey", return_value=1)
    @patch("ctypes.windll.user32.UnregisterHotKey", return_value=1)
    def test_start_and_stop_lifecycle(self, mock_unreg, mock_reg):
        invoked = []
        def on_press():
            invoked.append(True)

        self.mgr.start(callback=on_press)
        self.assertTrue(self.mgr.running)
        self.assertEqual(self.mgr.callback, on_press)

        # Stop
        self.mgr.stop()
        self.assertFalse(self.mgr.running)
        self.assertEqual(len(self.mgr.registered_ids), 0)

    @patch("ctypes.windll.user32.RegisterHotKey", return_value=1)
    def test_is_active(self, mock_reg):
        self.mgr.registered_ids = [101, 102]
        self.mgr.running = True
        self.assertTrue(self.mgr.is_active())

        self.mgr.running = False
        self.assertFalse(self.mgr.is_active())


if __name__ == "__main__":
    unittest.main()
