import unittest
from tools.vision_tools import get_active_window_title, capture_and_inspect_display
from tools.camera_tools import capture_webcam_frame, inspect_physical_camera

class TestVisionTools(unittest.TestCase):
    def test_active_window_title(self):
        title = get_active_window_title()
        self.assertIsInstance(title, str)
        self.assertTrue(len(title) >= 0)

    def test_screen_inspection(self):
        res = capture_and_inspect_display("Test screen inspection")
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 10)

    def test_camera_inspection_handles_gracefully(self):
        # Even if camera is busy or unavailable, returns graceful butler string
        res = inspect_physical_camera("Test camera")
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 5)

if __name__ == "__main__":
    unittest.main()
