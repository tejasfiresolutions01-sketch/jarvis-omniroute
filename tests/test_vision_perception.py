import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from PIL import Image, ImageDraw

from tools.vision_tools import (
    get_active_window_title,
    get_active_window_geometry,
    capture_screen,
    extract_screen_ui_hierarchy,
    analyze_visual_layout,
    comprehend_screen,
    capture_and_inspect_display
)
from core.local_intelligence import local_intelligence


class TestVisionPerception(unittest.TestCase):
    """Test suite covering Autonomous Multi-Modal Vision Perception & Screen Comprehension."""

    def test_active_window_title(self):
        title = get_active_window_title()
        self.assertIsInstance(title, str)
        self.assertTrue(len(title) > 0)

    def test_active_window_geometry(self):
        geom = get_active_window_geometry()
        self.assertIsInstance(geom, dict)
        self.assertIn("title", geom)
        self.assertIn("class_name", geom)
        self.assertIn("process_name", geom)
        self.assertIn("pid", geom)
        self.assertIn("rect", geom)
        self.assertIn("state", geom)
        rect = geom["rect"]
        self.assertIn("width", rect)
        self.assertIn("height", rect)
        self.assertGreaterEqual(rect["width"], 0)
        self.assertGreaterEqual(rect["height"], 0)

    def test_capture_screen_execution(self):
        img, (w, h), path_str = capture_screen()
        self.assertIsNotNone(img)
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)
        self.assertTrue(Path(path_str).exists())

    def test_analyze_visual_layout_dark_mode(self):
        # Create dark image (RGB 15, 20, 30)
        dark_img = Image.new("RGB", (640, 480), color=(15, 20, 30))
        layout = analyze_visual_layout(img=dark_img)
        self.assertEqual(layout["theme"], "dark_mode")
        self.assertLess(layout["luminance"], 100)
        self.assertEqual(layout["width"], 640)
        self.assertEqual(layout["height"], 480)

    def test_analyze_visual_layout_light_mode(self):
        # Create light image (RGB 240, 245, 250)
        light_img = Image.new("RGB", (640, 480), color=(240, 245, 250))
        layout = analyze_visual_layout(img=light_img)
        self.assertEqual(layout["theme"], "light_mode")
        self.assertGreater(layout["luminance"], 150)
        self.assertIn("#", layout["dominant_color_hex"])

    def test_analyze_visual_layout_modal_detection(self):
        # Create dark background with centered high-contrast modal dialog box
        w, h = 800, 600
        canvas = Image.new("RGB", (w, h), color=(10, 15, 20))
        draw = ImageDraw.Draw(canvas)
        # Draw centered dialog rectangle (300x200)
        dialog_box = (250, 200, 550, 400)
        draw.rectangle(dialog_box, fill=(230, 235, 240), outline=(255, 255, 255), width=3)
        layout = analyze_visual_layout(img=canvas)

        self.assertIn("quadrant_density", layout)
        self.assertIn("center", layout["quadrant_density"])
        # Should detect regions and modal dialog
        self.assertTrue(layout["regions_detected"] > 0)
        self.assertTrue(layout["modal_dialog_detected"])
        self.assertIsNotNone(layout["modal_bounds"])

    def test_extract_screen_ui_hierarchy_structure(self):
        hierarchy = extract_screen_ui_hierarchy()
        self.assertIsInstance(hierarchy, dict)
        self.assertIn("buttons", hierarchy)
        self.assertIn("inputs", hierarchy)
        self.assertIn("text_elements", hierarchy)
        self.assertIn("all_controls", hierarchy)
        self.assertIn("summary", hierarchy)

    def test_comprehend_screen_general_overview(self):
        res = comprehend_screen("what is on my screen?")
        self.assertTrue(res["success"])
        self.assertIn("speech", res)
        self.assertIn("sir", res["speech"].lower())
        self.assertIn("active_window", res)
        self.assertIn("visual_layout", res)
        self.assertIn("ui_controls", res)

    def test_comprehend_screen_theme_intent(self):
        res = comprehend_screen("is screen dark mode")
        self.assertTrue(res["success"])
        speech = res["speech"].lower()
        self.assertTrue("dark mode" in speech or "light mode" in speech)
        self.assertIn("luminance", speech)

    def test_comprehend_screen_vitals_intent(self):
        res = comprehend_screen("screen vitals")
        self.assertTrue(res["success"])
        speech = res["speech"].lower()
        self.assertIn("resolution", speech)
        self.assertIn("spans", speech)

    def test_comprehend_screen_find_button(self):
        res = comprehend_screen("find button Submit")
        self.assertTrue(res["success"])
        speech = res["speech"].lower()
        self.assertIn("submit", speech)

    def test_comprehend_screen_read_text(self):
        res = comprehend_screen("read text on screen")
        self.assertTrue(res["success"])
        speech = res["speech"].lower()
        self.assertIn("active", speech)

    def test_capture_and_inspect_display_backward_compatibility(self):
        speech = capture_and_inspect_display("Inspect active display")
        self.assertIsInstance(speech, str)
        self.assertGreater(len(speech), 15)
        self.assertIn("sir", speech.lower())

    def test_local_intelligence_screen_directives(self):
        # 1. Screen general query
        handled, resp = local_intelligence.evaluate_and_execute("what is on my screen")
        self.assertTrue(handled)
        self.assertIn("sir", resp.lower())

        # 2. Screen theme query
        handled, resp = local_intelligence.evaluate_and_execute("screen theme")
        self.assertTrue(handled)
        self.assertTrue("dark mode" in resp.lower() or "light mode" in resp.lower())

        # 3. Screen vitals query
        handled, resp = local_intelligence.evaluate_and_execute("display vitals")
        self.assertTrue(handled)
        self.assertIn("resolution", resp.lower())


if __name__ == "__main__":
    unittest.main()
