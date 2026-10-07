"""
Unit tests for J.A.R.V.I.S. Autonomous Desktop GUI Controller (Computer-Use).
"""

import unittest
from unittest.mock import patch, MagicMock
from tools.gui_controller import GUIController

class TestGUIController(unittest.TestCase):

    def setUp(self):
        self.gui = GUIController()

    def test_get_screen_resolution(self):
        w, h = self.gui.get_screen_resolution()
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)

    @patch("pyautogui.click")
    def test_mouse_click(self, mock_click):
        msg = self.gui.mouse_click(100, 200, clicks=1, button="left")
        mock_click.assert_called_with(x=100, y=200, clicks=1, button="left")
        self.assertIn("(100, 200)", msg)

    @patch("pyautogui.scroll")
    def test_mouse_scroll(self, mock_scroll):
        msg_down = self.gui.mouse_scroll(-300)
        mock_scroll.assert_called_with(-300)
        self.assertIn("down", msg_down)

        msg_up = self.gui.mouse_scroll(300)
        mock_scroll.assert_called_with(300)
        self.assertIn("up", msg_up)

    @patch("pyautogui.hotkey")
    def test_keyboard_hotkey(self, mock_hotkey):
        msg = self.gui.keyboard_hotkey("ctrl", "s")
        mock_hotkey.assert_called_with("ctrl", "s")
        self.assertIn("ctrl+s", msg)

    @patch("pyautogui.write")
    def test_keyboard_type(self, mock_write):
        msg = self.gui.keyboard_type("Stark Industries Protocol")
        mock_write.assert_called_with("Stark Industries Protocol", interval=0.015)
        self.assertIn("Typed", msg)

    @patch("pyautogui.hotkey")
    def test_window_snap(self, mock_hotkey):
        msg = self.gui.window_snap("left")
        mock_hotkey.assert_called_with("win", "left")
        self.assertIn("left split", msg)

        msg_max = self.gui.window_snap("maximize")
        mock_hotkey.assert_called_with("win", "up")
        self.assertIn("maximized", msg_max)

    @patch("pyautogui.hotkey")
    def test_browser_action(self, mock_hotkey):
        msg = self.gui.browser_action("new_tab")
        mock_hotkey.assert_called_with("ctrl", "t")
        self.assertIn("new browser tab", msg)

        msg_close = self.gui.browser_action("close_tab")
        mock_hotkey.assert_called_with("ctrl", "w")
        self.assertIn("Closed current browser tab", msg_close)

    @patch("tools.system_controller.system_controller.launch")
    @patch("pyautogui.hotkey")
    @patch("pyautogui.press")
    @patch("pyperclip.copy")
    @patch("time.sleep")
    def test_open_and_type(self, mock_sleep, mock_copy, mock_press, mock_hotkey, mock_launch):
        msg = self.gui.open_and_type("notepad", "Meeting notes for Tony", save_filename="notes.txt")
        mock_launch.assert_called_with("notepad")
        self.assertIn("Launched notepad", msg)
        self.assertIn("notes.txt", msg)

if __name__ == "__main__":
    unittest.main()
