"""
Unit tests for J.A.R.V.I.S. Adaptive System Display & Ambient Night Shield Controller.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from tools.display_controller import DisplayController

class TestDisplayController(unittest.TestCase):

    def setUp(self):
        self.controller = DisplayController()

    @patch.object(DisplayController, "_apply_gamma_ramp", return_value=True)
    def test_enable_night_shield(self, mock_gamma):
        res = self.controller.enable_night_shield(warmth=0.65)
        self.assertTrue(self.controller.night_shield_enabled)
        self.assertEqual(self.controller.current_warmth, 0.65)
        self.assertIn("Night Shield engaged, sir", res)
        self.assertIn("35%", res)
        mock_gamma.assert_called_once()

    @patch.object(DisplayController, "_apply_gamma_ramp", return_value=True)
    def test_disable_night_shield(self, mock_gamma):
        self.controller.night_shield_enabled = True
        res = self.controller.disable_night_shield()
        self.assertFalse(self.controller.night_shield_enabled)
        self.assertEqual(self.controller.current_warmth, 1.0)
        self.assertIn("Night Shield disengaged, sir", res)
        mock_gamma.assert_called_once_with(1.0, 1.0, 1.0)

    @patch("subprocess.run")
    def test_set_brightness(self, mock_subproc):
        mock_subproc.return_value = MagicMock(returncode=0)
        res = self.controller.set_brightness(85)
        self.assertEqual(self.controller.current_brightness, 85)
        self.assertIn("calibrated to 85%", res)

        # Clamping test
        self.controller.set_brightness(150)
        self.assertEqual(self.controller.current_brightness, 100)
        self.controller.set_brightness(5)
        self.assertEqual(self.controller.current_brightness, 10)

    @patch.object(DisplayController, "_apply_gamma_ramp", return_value=True)
    @patch("subprocess.run")
    def test_apply_adaptive_ambient_protocols(self, mock_subproc, mock_gamma):
        mock_subproc.return_value = MagicMock(returncode=0)

        # 1. Late Night (23:00)
        with patch("tools.display_controller.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 10, 7, 23, 15)
            res = self.controller.apply_adaptive_ambient()
            self.assertIn("Adaptive Night Protocol", res)
            self.assertEqual(self.controller.current_brightness, 50)
            self.assertTrue(self.controller.night_shield_enabled)

        # 2. Evening (20:00)
        with patch("tools.display_controller.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 10, 7, 20, 30)
            res = self.controller.apply_adaptive_ambient()
            self.assertIn("Adaptive Evening Protocol", res)
            self.assertEqual(self.controller.current_brightness, 75)
            self.assertTrue(self.controller.night_shield_enabled)

        # 3. Daytime (14:00)
        with patch("tools.display_controller.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 10, 7, 14, 0)
            res = self.controller.apply_adaptive_ambient()
            self.assertIn("Adaptive Daylight Protocol", res)
            self.assertEqual(self.controller.current_brightness, 100)
            self.assertFalse(self.controller.night_shield_enabled)

    def test_get_status_and_summary(self):
        status = self.controller.get_status()
        self.assertIn("night_shield_enabled", status)
        self.assertIn("warmth", status)
        self.assertIn("brightness", status)
        self.assertIn("mode", status)

        summary = self.controller.format_status_summary()
        self.assertIn("Display telemetry, sir", summary)
        self.assertIn("Brightness is holding at", summary)

if __name__ == "__main__":
    unittest.main()
