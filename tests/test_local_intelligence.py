import unittest
from unittest.mock import patch
from core.local_intelligence import local_intelligence

class TestLocalIntelligence(unittest.TestCase):
    @patch("tools.system_controller.SystemController.launch")
    def test_open_application(self, mock_launch):
        mock_launch.return_value = "Opening Chrome for you now, sir."
        handled, res = local_intelligence.evaluate_and_execute("hey jarvis, open chrome")
        self.assertTrue(handled)
        self.assertIn("Chrome", res)
        mock_launch.assert_called_with("chrome")

    @patch("tools.system_controller.SystemController.close_process")
    def test_close_application(self, mock_close):
        mock_close.return_value = "Closed Notepad, sir."
        handled, res = local_intelligence.evaluate_and_execute("close notepad")
        self.assertTrue(handled)
        self.assertIn("Notepad", res)
        mock_close.assert_called_with("notepad")

    @patch("tools.system_controller.SystemController.volume_up")
    def test_volume_up(self, mock_vol):
        mock_vol.return_value = "Master volume increased, sir."
        handled, res = local_intelligence.evaluate_and_execute("volume up")
        self.assertTrue(handled)
        mock_vol.assert_called_once()

    def test_time_query(self):
        handled, res = local_intelligence.evaluate_and_execute("what time is it")
        self.assertTrue(handled)
        self.assertIn("currently", res)

    def test_date_query(self):
        handled, res = local_intelligence.evaluate_and_execute("what is today's date")
        self.assertTrue(handled)
        self.assertIn("Today is", res)

    def test_vitals_query(self):
        handled, res = local_intelligence.evaluate_and_execute("system vitals")
        self.assertTrue(handled)
        self.assertIn("CPU", res)

    def test_offline_calculation(self):
        handled, res = local_intelligence.evaluate_and_execute("calculate 25 * 4")
        self.assertTrue(handled)
        self.assertIn("100", res)

    def test_butler_identity(self):
        handled, res = local_intelligence.evaluate_and_execute("who are you")
        self.assertTrue(handled)
        self.assertIn("J.A.R.V.I.S.", res)

if __name__ == "__main__":
    unittest.main()
