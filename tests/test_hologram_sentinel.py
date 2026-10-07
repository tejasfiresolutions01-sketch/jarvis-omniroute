"""
Unit tests for J.A.R.V.I.S. Hologram Sentinel & App Lifecycle Daemon.
Validates:
1. Holographic HUD window discovery and foreground elevation.
2. Device display wake integration.
3. Application close detection and cooldown logic.
4. Voice directive recognition for holographic interface summoning/hiding.
"""

import unittest
from unittest.mock import patch, MagicMock
from core.hologram_sentinel import HologramSentinel, hologram_sentinel
from core.display_sentinel import DisplaySentinel
from core.local_intelligence import LocalIntelligence

class TestHologramSentinel(unittest.TestCase):

    def setUp(self):
        self.sentinel = HologramSentinel()

    def test_initialization(self):
        """Verifies sentinel initializes cleanly with cooldowns."""
        self.assertFalse(self.sentinel._running)
        self.assertEqual(self.sentinel.TRIGGER_COOLDOWN_SECONDS, 1.8)
        self.assertEqual(self.sentinel.MIN_WINDOW_LIFETIME, 1.0)

    @patch.object(HologramSentinel, "get_hud_hwnd", return_value=12345)
    def test_is_hologram_visible(self, mock_hwnd):
        """Verifies visibility detection when window exists."""
        self.sentinel.user32.IsWindowVisible = MagicMock(return_value=1)
        self.assertTrue(self.sentinel.is_hologram_visible())

        self.sentinel.user32.IsWindowVisible = MagicMock(return_value=0)
        self.assertFalse(self.sentinel.is_hologram_visible())

    @patch.object(HologramSentinel, "get_hud_hwnd", return_value=54321)
    def test_display_hologram_existing_window(self, mock_hwnd):
        """Verifies window restoration and foreground elevation on existing HUD."""
        self.sentinel.user32.ShowWindow = MagicMock()
        self.sentinel.user32.BringWindowToTop = MagicMock()
        self.sentinel.user32.SetForegroundWindow = MagicMock()
        self.sentinel.user32.SetWindowPos = MagicMock()

        success = self.sentinel.display_hologram(reason="test_elevation")
        self.assertTrue(success)
        self.sentinel.user32.ShowWindow.assert_called_with(54321, 9)
        self.sentinel.user32.BringWindowToTop.assert_called_with(54321)
        self.sentinel.user32.SetForegroundWindow.assert_called_with(54321)

    @patch.object(HologramSentinel, "get_hud_hwnd", return_value=54321)
    def test_display_hologram_cooldown(self, mock_hwnd):
        """Verifies cooldown prevents redundant rapid calls."""
        self.sentinel.user32.ShowWindow = MagicMock()
        self.sentinel.user32.BringWindowToTop = MagicMock()
        self.sentinel.user32.SetForegroundWindow = MagicMock()
        self.sentinel.user32.SetWindowPos = MagicMock()

        # First trigger succeeds
        res1 = self.sentinel.display_hologram(reason="auto_event")
        self.assertTrue(res1)

        # Immediate second trigger rejected by cooldown
        res2 = self.sentinel.display_hologram(reason="auto_event")
        self.assertFalse(res2)

        # Manual trigger bypasses cooldown
        res3 = self.sentinel.display_hologram(reason="manual")
        self.assertTrue(res3)

    @patch.object(HologramSentinel, "get_hud_hwnd", return_value=None)
    @patch("subprocess.Popen")
    def test_display_hologram_spawn(self, mock_popen, mock_hwnd):
        """Verifies subprocess spawn when HUD window is not running."""
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        success = self.sentinel.display_hologram(reason="manual")
        self.assertTrue(success)
        self.assertTrue(mock_popen.called)

    @patch.object(HologramSentinel, "get_hud_hwnd", return_value=99999)
    def test_hide_hologram(self, mock_hwnd):
        """Verifies hiding the HUD into stealth mode."""
        self.sentinel.user32.ShowWindow = MagicMock()
        success = self.sentinel.hide_hologram()
        self.assertTrue(success)
        self.sentinel.user32.ShowWindow.assert_called_with(99999, 0)

    @patch("core.hologram_sentinel.hologram_sentinel.display_hologram")
    @patch("core.display_sentinel.speak")
    def test_display_sentinel_triggers_hologram(self, mock_speak, mock_display_holo):
        """Verifies that DisplaySentinel triggers hologram display when display turns on."""
        disp_sentinel = DisplaySentinel()
        disp_sentinel.trigger_greeting(reason="test_device_on")
        self.assertTrue(mock_display_holo.called)

    @patch("core.hologram_sentinel.hologram_sentinel.display_hologram")
    def test_local_intelligence_show_hologram_intent(self, mock_display_holo):
        """Verifies voice recognition for 'show holographic interface'."""
        local_intel = LocalIntelligence()
        handled, resp = local_intel.evaluate_and_execute("show holographic interface")
        self.assertTrue(handled)
        self.assertIn("Tactical holographic interface restored", resp)
        self.assertTrue(mock_display_holo.called)

    @patch("core.hologram_sentinel.hologram_sentinel.hide_hologram")
    def test_local_intelligence_hide_hologram_intent(self, mock_hide_holo):
        """Verifies voice recognition for 'hide holographic interface'."""
        local_intel = LocalIntelligence()
        handled, resp = local_intel.evaluate_and_execute("hide holographic interface")
        self.assertTrue(handled)
        self.assertIn("The Holographic Tactical HUD is concealed", resp)
        self.assertTrue(mock_hide_holo.called)

if __name__ == "__main__":
    unittest.main()
