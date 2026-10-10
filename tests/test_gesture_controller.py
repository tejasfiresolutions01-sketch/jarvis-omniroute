"""
Unit Tests for J.A.R.V.I.S. Spatial Hand Gesture Engine & Optical Vision Controller.
Validates skin segmentation, trajectory tracking, gesture classification, and HUD dispatch.
"""

import time
import unittest
import numpy as np
import cv2

from tools.gesture_controller import SpatialGestureEngine, spatial_gesture_engine
from tools.camera_tools import start_gesture_control, stop_gesture_control, is_gesture_tracking_active


class TestGestureController(unittest.TestCase):
    def setUp(self):
        self.engine = SpatialGestureEngine()

    def test_blank_frame_handling(self):
        """Must return None and hand_present=False for black/empty frames."""
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        gesture, meta = self.engine.analyze_frame(blank)
        self.assertIsNone(gesture)
        self.assertFalse(meta.get("hand_present", False))

    def test_synthetic_hand_skin_detection(self):
        """Must detect presence and centroid of synthetic hand skin patch."""
        # Create blank frame with skin-colored ellipse (YCrCb skin color in BGR: B=100, G=150, R=220)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.ellipse(frame, (320, 240), (70, 110), 0, 0, 360, (100, 150, 220), -1)

        gesture, meta = self.engine.analyze_frame(frame)
        self.assertTrue(meta.get("hand_present", False))
        cx, cy = meta.get("centroid", (0, 0))
        self.assertAlmostEqual(cx, 320, delta=20)
        self.assertAlmostEqual(cy, 240, delta=20)

    def test_continuous_spatial_velocity_stream(self):
        """Must calculate frame-to-frame optical velocity for continuous 6-DoF tracking."""
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.ellipse(frame1, (300, 240), (70, 110), 0, 0, 360, (100, 150, 220), -1)
        self.engine.analyze_frame(frame1)

        frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.ellipse(frame2, (330, 240), (70, 110), 0, 0, 360, (100, 150, 220), -1)
        _, meta2 = self.engine.analyze_frame(frame2)
        self.assertIn("velocity", meta2)
        vx, vy = meta2["velocity"]
        self.assertGreater(vx, 0.0)

    def test_horizontal_swipe_right_detection(self):
        """Must detect swipe_right gesture when hand moves rapidly to the right."""
        self.engine._history.clear()
        self.engine._last_gesture_time = 0.0

        detected = []
        for x_pos in [200, 240, 290, 350, 400]:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.ellipse(frame, (x_pos, 240), (60, 90), 0, 0, 360, (100, 150, 220), -1)
            g, _ = self.engine.analyze_frame(frame)
            if g:
                detected.append(g)
            time.sleep(0.01)

        self.assertIn("swipe_right", detected)

    def test_horizontal_swipe_left_detection(self):
        """Must detect swipe_left gesture when hand moves rapidly to the left."""
        self.engine._history.clear()
        self.engine._last_gesture_time = 0.0

        detected = []
        for x_pos in [420, 370, 310, 250, 190]:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.ellipse(frame, (x_pos, 240), (60, 90), 0, 0, 360, (100, 150, 220), -1)
            g, _ = self.engine.analyze_frame(frame)
            if g:
                detected.append(g)
            time.sleep(0.01)

        self.assertIn("swipe_left", detected)

    def test_dispatch_hud_action(self):
        """Must translate gestures into corresponding HUD commands."""
        res_r = self.engine.dispatch_hud_action("swipe_right")
        self.assertIn("Rotated 3D Hologram clockwise", res_r)

        res_palm = self.engine.dispatch_hud_action("open_palm")
        self.assertIn("Halted 3D auto-spin", res_palm)

        res_fist = self.engine.dispatch_hud_action("fist")
        self.assertIn("Reset 3D Hologram", res_fist)

    def test_camera_tools_lifecycle(self):
        """Must start and stop gesture tracking daemon cleanly."""
        start_msg = start_gesture_control(camera_index=999)  # Non-existent index test
        self.assertIn("tracking matrix active", start_msg)
        self.assertTrue(is_gesture_tracking_active())

        stop_msg = stop_gesture_control()
        self.assertIn("disarmed", stop_msg)
        self.assertFalse(is_gesture_tracking_active())


if __name__ == "__main__":
    unittest.main()
