"""
Unit tests for Sprints 5 & 6:
- HardwareDiagnosticSentinel
- VisionEnhancer
- FrameRateThrottler
Strictly in English.
"""

import time
import unittest
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.hardware_diagnostic_sentinel import HardwareDiagnosticSentinel
from core.vision_enhancer import VisionEnhancer, FrameRateThrottler


class TestSprints5And6(unittest.TestCase):

    def setUp(self):
        self.hw = HardwareDiagnosticSentinel()
        self.enhancer = VisionEnhancer()

    def test_hardware_sentinel_telemetry(self):
        """Verifies hardware diagnostics and telemetry collection."""
        storage = self.hw.inspect_storage("C:")
        self.assertIn("free_gb", storage)
        self.assertIn("total_gb", storage)
        self.assertIn("alert", storage)

        battery = self.hw.inspect_battery()
        self.assertIn("has_battery", battery)
        self.assertIn("power_plugged", battery)

        ram = self.hw.sweep_ram()
        self.assertIn("objects_collected", ram)

        full = self.hw.get_full_telemetry()
        self.assertIn("cpu_percent", full)
        self.assertIn("ram_percent", full)
        self.assertIn("storage", full)

    def test_emergency_kill_switch_protocol(self):
        """Verifies kill switch hook execution and state reset."""
        hook_ran = {"val": False}
        def on_abort():
            hook_ran["val"] = True

        self.hw.register_abort_hook(on_abort)
        self.assertFalse(self.hw.is_kill_switch_active())

        # Trigger
        self.hw.trigger_kill_switch()
        self.assertTrue(self.hw.is_kill_switch_active())
        self.assertTrue(hook_ran["val"])

        # Reset
        self.hw.reset_kill_switch()
        self.assertFalse(self.hw.is_kill_switch_active())

    def test_vision_bounding_box_clustering(self):
        """Verifies spatial clustering of raw word boxes into cohesive lines."""
        raw_boxes = [
            {"text": "Save", "x": 100, "y": 50, "w": 30, "h": 15},
            {"text": "Changes", "x": 135, "y": 50, "w": 50, "h": 15},
            {"text": "Cancel", "x": 200, "y": 50, "w": 40, "h": 15},
            {"text": "Diagnostic", "x": 100, "y": 100, "w": 60, "h": 15},
            {"text": "Report", "x": 165, "y": 100, "w": 45, "h": 15}
        ]

        clustered = self.enhancer.cluster_bounding_boxes(raw_boxes)
        self.assertEqual(len(clustered), 2)
        self.assertIn("Save Changes Cancel", clustered[0]["text"])
        self.assertIn("Diagnostic Report", clustered[1]["text"])

    def test_ui_button_classifier(self):
        """Verifies identification of clickable buttons."""
        elements = [
            {"text": "Save Changes", "x": 100, "y": 50, "w": 85, "h": 15, "center_x": 142.5, "center_y": 57.5},
            {"text": "General Information Header", "x": 100, "y": 10, "w": 200, "h": 20, "center_x": 200, "center_y": 20}
        ]
        buttons = self.enhancer.classify_ui_buttons(elements)
        self.assertEqual(len(buttons), 1)
        self.assertEqual(buttons[0]["text"], "Save Changes")
        self.assertTrue(buttons[0]["is_button"])

    def test_frame_rate_throttler(self):
        """Verifies adaptive frame rate throttling based on activity."""
        throttler = FrameRateThrottler(idle_fps=2.0, active_fps=20.0)
        self.assertTrue(throttler.should_capture_now())
        # Immediate subsequent check should be throttled
        self.assertFalse(throttler.should_capture_now())


if __name__ == "__main__":
    unittest.main()
