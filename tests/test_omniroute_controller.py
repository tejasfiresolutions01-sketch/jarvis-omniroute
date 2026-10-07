"""
Unit tests for OmniRoute Controller and Telemetry Sentinel.
"""

import unittest
from unittest.mock import patch, MagicMock
from tools.omniroute_controller import OmniRouteController

class TestOmniRouteController(unittest.TestCase):

    def setUp(self):
        self.controller = OmniRouteController(
            base_url="http://localhost:20128/v1",
            api_key="test_omniroute_key"
        )

    @patch("requests.get")
    def test_status_online(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [{"id": "auto/best-chat"}, {"id": "auto/best-coding"}]
        }
        mock_get.return_value = mock_resp

        status = self.controller.get_status()
        self.assertTrue(status["online"])
        self.assertEqual(status["model_count"], 2)
        self.assertIn("OmniRoute Gateway active", status["message"])

    @patch("requests.get")
    def test_status_offline(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        status = self.controller.get_status()
        self.assertFalse(status["online"])
        self.assertEqual(status["model_count"], 0)

    @patch.object(OmniRouteController, "get_status")
    def test_butler_summary_online(self, mock_status):
        mock_status.return_value = {
            "online": True,
            "model_count": 498
        }
        summary = self.controller.get_butler_summary()
        self.assertIn("OmniRoute", summary)
        self.assertIn("498 models", summary)
        self.assertIn("operational", summary)

    @patch.object(OmniRouteController, "get_status")
    def test_butler_summary_offline(self, mock_status):
        mock_status.return_value = {
            "online": False,
            "model_count": 0
        }
        summary = self.controller.get_butler_summary()
        self.assertIn("currently offline", summary)
        self.assertIn("Local deterministic matrix", summary)

if __name__ == "__main__":
    unittest.main()
