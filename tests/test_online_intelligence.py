"""
Unit tests for OnlineIntelligence Free Models Cascade and Fallbacks.
"""

import unittest
from unittest.mock import patch, MagicMock
from core.online_intelligence import OnlineIntelligence

class TestOnlineIntelligence(unittest.TestCase):

    def setUp(self):
        self.engine = OnlineIntelligence()

    @patch("requests.get")
    def test_is_online_available(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp
        self.assertTrue(self.engine.is_online_available())

    @patch("requests.post")
    def test_query_success_first_free_model(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "At your service, Sir."}}]
        }
        mock_post.return_value = mock_resp

        ans = self.engine.query("Status report")
        self.assertEqual(ans, "At your service, Sir.")
        self.assertTrue(mock_post.called)

    @patch("requests.post")
    def test_query_cascade_to_second_free_model(self, mock_post):
        # First call fails (502 / error), second call succeeds (200)
        fail_resp = MagicMock()
        fail_resp.status_code = 502

        success_resp = MagicMock()
        success_resp.status_code = 200
        success_resp.json.return_value = {
            "choices": [{"message": {"content": "Fallback free model succeeded, Sir."}}]
        }

        mock_post.side_effect = [fail_resp, success_resp]

        ans = self.engine.query("Hello")
        self.assertEqual(ans, "Fallback free model succeeded, Sir.")
        self.assertGreaterEqual(mock_post.call_count, 2)

    @patch("requests.post")
    def test_query_offline_fallback_when_all_fail(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        ans = self.engine.query("Hello")
        self.assertIsNone(ans)

if __name__ == "__main__":
    unittest.main()
