"""
Live Spatial Hand Gesture & Optical Vision Verification Harness.
Simulates live synthetic optical stream through SpatialGestureEngine.
"""

import os
import sys
import time
import numpy as np
import cv2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.gesture_controller import spatial_gesture_engine
from tools.camera_tools import start_gesture_control, stop_gesture_control, is_gesture_tracking_active


def run_live_gesture_verification():
    print("=" * 65)
    print("J.A.R.V.I.S. Live Spatial Hand Gesture Vision Harness")
    print("=" * 65)

    # 1. Verify Camera Tools Lifecycle
    msg_start = start_gesture_control(camera_index=999)
    print(f"[Spatial Vision]: {msg_start}")
    assert is_gesture_tracking_active(), "Gesture daemon should report active"

    msg_stop = stop_gesture_control()
    print(f"[Spatial Vision]: {msg_stop}")
    assert not is_gesture_tracking_active(), "Gesture daemon should report stopped"

    # 2. Simulate Optical Gesture Processing
    print("\n[Spatial Vision]: Simulating mid-air hand trajectory stream...")
    gestures_detected = []

    # Sweep hand from Left to Right
    for x in range(180, 420, 45):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Draw skin-colored palm
        cv2.ellipse(frame, (x, 240), (65, 95), 0, 0, 360, (100, 150, 220), -1)
        g, meta = spatial_gesture_engine.analyze_frame(frame)
        if g:
            gestures_detected.append(g)
            action_desc = spatial_gesture_engine.dispatch_hud_action(g)
            print(f"  -> Detected Gesture: '{g}' ({action_desc})")
        time.sleep(0.02)

    assert "swipe_right" in gestures_detected, "Failed to recognize mid-air swipe_right gesture!"
    print(" [PASS] Successfully recognized optical Swipe Right trajectory")

    # 3. Simulate Palm vs Fist Classification
    frame_palm = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.ellipse(frame_palm, (320, 240), (80, 110), 0, 0, 360, (100, 150, 220), -1)
    _, meta_palm = spatial_gesture_engine.analyze_frame(frame_palm)
    assert meta_palm.get("hand_present"), "Failed to detect hand geometry!"
    print(f" [PASS] Hand Geometry Telemetry: Centroid={meta_palm['centroid']}, Area={int(meta_palm['area'])}")

    print("=" * 65)
    print("Spatial Gesture Vision Live Verification: ALL TESTS PASSED.")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_live_gesture_verification()
