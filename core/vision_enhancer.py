"""
J.A.R.V.I.S. Optical Vision Enhancer & UI Element Classifier.
Features:
1. WinRT OCR Bounding Box Clustering: Combines scattered word bounding boxes into cohesive semantic paragraphs.
2. Visual UI Button Classifier: Locates actionable buttons ("Submit", "Save", "OK", "Cancel", "Quotation") with click centers.
3. Adaptive Optical Frame Rate Throttler: Reduces optical capture load from 30 FPS to 1 FPS during desktop inactivity.
4. 100% Free, local mathematical algorithm with zero cloud dependency.
Strictly in English.
"""

import math
import time
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("VisionEnhancer")

COMMON_BUTTON_TERMS = {
    "submit", "save", "cancel", "ok", "apply", "close", "next",
    "back", "finish", "download", "export", "print", "search",
    "login", "sign in", "refill", "invoice", "calculate", "quote"
}


class VisionEnhancer:
    """
    Enhances raw OCR outputs and optimizes vision pipeline CPU consumption.
    """

    @staticmethod
    def cluster_bounding_boxes(
        boxes: List[Dict[str, Any]],
        line_threshold_y: float = 8.0,
        word_spacing_x: float = 25.0
    ) -> List[Dict[str, Any]]:
        """
        Clusters raw word boxes into formatted text lines and paragraphs.
        Box format expected: {"text": str, "x": float, "y": float, "w": float, "h": float}
        """
        if not boxes:
            return []

        # Sort primarily by Y (top to bottom), then by X (left to right)
        sorted_boxes = sorted(boxes, key=lambda b: (b.get("y", 0), b.get("x", 0)))
        lines: List[List[Dict[str, Any]]] = []

        for b in sorted_boxes:
            placed = False
            for line in lines:
                # Check if box is on the same vertical line
                ref_box = line[-1]
                if abs(b.get("y", 0) - ref_box.get("y", 0)) <= line_threshold_y:
                    # Check horizontal spacing
                    if b.get("x", 0) >= ref_box.get("x", 0):
                        line.append(b)
                        placed = True
                        break
            if not placed:
                lines.append([b])

        clustered_results = []
        for line in lines:
            line_text = " ".join(b.get("text", "") for b in line)
            min_x = min(b.get("x", 0) for b in line)
            min_y = min(b.get("y", 0) for b in line)
            max_r = max(b.get("x", 0) + b.get("w", 0) for b in line)
            max_b = max(b.get("y", 0) + b.get("h", 0) for b in line)

            clustered_results.append({
                "text": line_text,
                "x": min_x,
                "y": min_y,
                "w": max_r - min_x,
                "h": max_b - min_y,
                "center_x": min_x + (max_r - min_x) / 2.0,
                "center_y": min_y + (max_b - min_y) / 2.0
            })

        return clustered_results

    @staticmethod
    def classify_ui_buttons(clustered_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identifies which text elements represent actionable UI buttons."""
        buttons = []
        for elem in clustered_elements:
            text = elem.get("text", "").strip().lower()
            if text in COMMON_BUTTON_TERMS or any(term in text for term in COMMON_BUTTON_TERMS):
                btn_info = dict(elem)
                btn_info["is_button"] = True
                buttons.append(btn_info)
        return buttons


class FrameRateThrottler:
    """Manages adaptive capture intervals based on desktop user motion."""

    def __init__(self, idle_fps: float = 1.0, active_fps: float = 15.0):
        self.idle_interval = 1.0 / max(idle_fps, 0.1)
        self.active_interval = 1.0 / max(active_fps, 1.0)
        self.last_capture_time = 0.0
        self.last_motion_time = time.time()
        self.motion_timeout_sec = 3.0

    def register_motion(self):
        """Signals user activity (mouse movement, keypress, audio)."""
        self.last_motion_time = time.time()

    def should_capture_now(self) -> bool:
        """Determines if enough time has passed to capture the next optical frame."""
        now = time.time()
        is_active = (now - self.last_motion_time) <= self.motion_timeout_sec
        target_interval = self.active_interval if is_active else self.idle_interval

        if now - self.last_capture_time >= target_interval:
            self.last_capture_time = now
            return True
        return False


# Global Singletons
vision_enhancer = VisionEnhancer()
frame_throttler = FrameRateThrottler()
