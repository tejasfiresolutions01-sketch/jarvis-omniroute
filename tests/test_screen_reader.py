"""
Unit tests for J.A.R.V.I.S. Context-Aware Screen Reader & Optical Intelligence.
"""

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from tools.screen_reader import ScreenReader

class TestScreenReader(unittest.TestCase):

    def setUp(self):
        self.reader = ScreenReader()

    def test_get_active_window_info(self):
        info = self.reader.get_active_window_info()
        self.assertIn("title", info)
        self.assertIn("process", info)
        self.assertIn("pid", info)
        self.assertIn("rect", info)
        self.assertIn("width", info)
        self.assertIn("height", info)

    def test_extract_text_ocr_missing_file(self):
        fake_path = Path("temp/non_existent_image.png")
        txt = self.reader.extract_text_ocr(fake_path)
        self.assertEqual(txt, "")

    @patch("subprocess.run")
    def test_extract_text_ocr_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="STARK INDUSTRIES SCHEMATIC MARK 85\n")
        
        # Create a real dummy file to pass existence check
        dummy_file = self.reader.temp_dir / "test_ocr_dummy.png"
        dummy_file.write_bytes(b"dummy")

        try:
            txt = self.reader.extract_text_ocr(dummy_file)
            self.assertEqual(txt, "STARK INDUSTRIES SCHEMATIC MARK 85")
        finally:
            if dummy_file.exists():
                dummy_file.unlink()

    @patch.object(ScreenReader, "read_active_window_text", return_value="Traceback (most recent call last):\n  File 'app.py', line 12\nZeroDivisionError: division by zero")
    @patch("core.online_intelligence.online_intelligence.is_online_available", return_value=False)
    def test_analyze_screen_error_detection_offline(self, mock_online, mock_read_win):
        res = self.reader.analyze_screen("What error is on my screen?")
        self.assertIn("Optical inspection indicates an error", res)
        self.assertIn("ZeroDivisionError", res)

    @patch.object(ScreenReader, "read_active_window_text", return_value="Flight telemetry: Altitude 35,000 ft, Mach 2.4")
    @patch("core.online_intelligence.online_intelligence.is_online_available", return_value=True)
    @patch("core.online_intelligence.online_intelligence.query", return_value="You are cruising at Mach 2.4 at 35,000 feet, sir.")
    def test_analyze_screen_online_synthesis(self, mock_query, mock_online, mock_read_win):
        res = self.reader.analyze_screen("Summarize flight data")
        self.assertEqual(res, "You are cruising at Mach 2.4 at 35,000 feet, sir.")

if __name__ == "__main__":
    unittest.main()
