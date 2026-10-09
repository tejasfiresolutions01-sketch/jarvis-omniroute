"""
Unit Tests for J.A.R.V.I.S. Windows UI Automation (UIA) COM Controller.
Validates programmatic element discovery, invocation, text entry, and GUIController integration.
"""

import unittest
from unittest.mock import MagicMock, patch

from tools.uia_controller import WindowsUIAutomation, windows_uia
from tools.gui_controller import gui_controller


class TestWindowsUIAutomation(unittest.TestCase):
    def setUp(self):
        self.uia = windows_uia

    def test_uia_availability_on_windows(self):
        """UIA COM interface must be available and initialized on Windows."""
        self.assertTrue(self.uia.is_available)
        self.assertIsNotNone(self.uia._uia)

    def test_get_open_windows_structure(self):
        """Must enumerate open windows with valid dictionary schema."""
        wins = self.uia.get_open_windows()
        self.assertIsInstance(wins, list)
        if wins:
            first = wins[0]
            self.assertIn("name", first)
            self.assertIn("class_name", first)
            self.assertIn("process_id", first)

    def test_find_window_nonexistent_graceful(self):
        """Must return None gracefully without exceptions when window does not exist."""
        win = self.uia.find_window("NonExistentWindow_987654321")
        self.assertIsNone(win)

    def test_inspect_window_controls_nonexistent(self):
        """Must return empty list for nonexistent window without raising."""
        controls = self.uia.inspect_window_controls("NonExistentWindow_987654321")
        self.assertEqual(controls, [])

    def test_gui_controller_list_windows(self):
        """gui_controller.list_active_windows must return human-readable summary string."""
        res = gui_controller.list_active_windows()
        self.assertIsInstance(res, str)
        self.assertIn("windows", res.lower())

    def test_gui_controller_inspect_window_graceful(self):
        """gui_controller.inspect_window must return polite message for nonexistent window."""
        res = gui_controller.inspect_window("NonExistentWindow_987654321")
        self.assertIsInstance(res, str)
        self.assertIn("No interactive controls found", res)

    def test_click_element_invoke_pattern(self):
        """Must invoke IUIAutomationInvokePattern when available."""
        mock_elem = MagicMock()
        mock_elem.CurrentName = "Submit"
        mock_pattern = MagicMock()
        mock_elem.GetCurrentPattern.return_value = mock_pattern
        mock_invoke = MagicMock()
        mock_pattern.QueryInterface.return_value = mock_invoke

        with patch.object(self.uia, "find_element", return_value=mock_elem):
            ok, msg = self.uia.click_element("Submit")
            self.assertTrue(ok)
            self.assertIn("Invoke Pattern", msg)
            mock_invoke.Invoke.assert_called_once()

    def test_set_element_text_value_pattern(self):
        """Must set text via IUIAutomationValuePattern when available."""
        mock_elem = MagicMock()
        mock_pattern = MagicMock()
        mock_elem.GetCurrentPattern.return_value = mock_pattern
        mock_val = MagicMock()
        mock_pattern.QueryInterface.return_value = mock_val

        with patch.object(self.uia, "find_element", return_value=mock_elem):
            ok, msg = self.uia.set_element_text("Username", "TonyStark")
            self.assertTrue(ok)
            self.assertIn("Username", msg)
            mock_val.SetValue.assert_called_once_with("TonyStark")


if __name__ == "__main__":
    unittest.main()
