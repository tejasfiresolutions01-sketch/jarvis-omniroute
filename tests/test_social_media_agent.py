"""
Unit tests for J.A.R.V.I.S. Social Media Dispatcher and Multi-Platform Publisher.
Validates zero-credential 1-click web intent generation, direct background API fallback,
post formatting, queue history logging, and local voice command routing.
"""

import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.local_intelligence import local_intelligence
from tools.social_media_agent import SocialMediaAgent, social_media_agent


class TestSocialMediaAgent(unittest.TestCase):

    def setUp(self):
        self.agent = social_media_agent

    def test_generate_intent_url_twitter(self):
        """Verifies Twitter/X intent URL formatting."""
        url = self.agent.generate_intent_url("twitter", "Hello World!", url="https://example.com")
        self.assertIn("twitter.com/intent/tweet", url)
        self.assertIn("text=Hello%20World%21", url)
        self.assertIn("url=https%3A%2F%2Fexample.com", url)

        # X alias
        url_x = self.agent.generate_intent_url("x", "Testing X")
        self.assertIn("twitter.com/intent/tweet?text=Testing%20X", url_x)

    def test_generate_intent_url_linkedin(self):
        """Verifies LinkedIn share and feed intent URL generation."""
        url_share = self.agent.generate_intent_url("linkedin", "Check this out", url="https://example.com/blog")
        self.assertIn("linkedin.com/sharing/share-offsite", url_share)
        self.assertIn("url=https%3A%2F%2Fexample.com%2Fblog", url_share)

        url_feed = self.agent.generate_intent_url("linkedin", "Thought leadership post")
        self.assertIn("linkedin.com/feed/?shareActive=true", url_feed)
        self.assertIn("text=Thought%20leadership%20post", url_feed)

    def test_generate_intent_url_facebook(self):
        """Verifies Facebook sharer URL generation."""
        url = self.agent.generate_intent_url("facebook", "Announcing new release", url="https://example.com")
        self.assertIn("facebook.com/sharer/sharer.php", url)
        self.assertIn("quote=Announcing%20new%20release", url)

    def test_generate_intent_url_whatsapp(self):
        """Verifies WhatsApp send URL generation with and without phone number."""
        url_broadcast = self.agent.generate_intent_url("whatsapp", "Meeting alert")
        self.assertIn("api.whatsapp.com/send?text=Meeting%20alert", url_broadcast)

        url_targeted = self.agent.generate_intent_url("whatsapp", "Direct msg", recipient="+1 (234) 567-890")
        self.assertIn("phone=1234567890", url_targeted)
        self.assertIn("text=Direct%20msg", url_targeted)

    def test_generate_intent_url_reddit(self):
        """Verifies Reddit submit URL generation."""
        url = self.agent.generate_intent_url("reddit", "Exciting tech breakthrough in AI systems")
        self.assertIn("reddit.com/submit", url)
        self.assertIn("title=Exciting%20tech%20breakthrough%20in%20AI%20systems", url)

    def test_generate_intent_url_fallback(self):
        """Verifies fallback search query for unknown platforms."""
        url = self.agent.generate_intent_url("unknown_network", "Mysterious post")
        self.assertIn("google.com/search?q=Mysterious%20post", url)

    def test_format_post_constraints(self):
        """Verifies post formatting adapts to platform constraints."""
        long_text = "A" * 350
        tw = self.agent.format_post("twitter", long_text, hashtags=["ai", "tech"])
        self.assertLessEqual(len(tw), 280)
        self.assertIn("#ai", tw)

        li = self.agent.format_post("linkedin", "Modular Microservices")
        self.assertIn("Modular Microservices", li)
        self.assertIn("#Engineering", li)

        fb = self.agent.format_post("facebook", "New Update")
        self.assertIn("New Update", fb)

        wa = self.agent.format_post("whatsapp", "System online")
        self.assertIn("*Update:* System online", wa)

    @patch("webbrowser.open")
    def test_publish_web_intent_mode(self, mock_web_open):
        """Verifies fallback to 1-click web intent when no API tokens are set."""
        with patch.dict(os.environ, {}, clear=True):
            res = self.agent.publish("twitter", "Automated broadcast test", auto_open=True)
            self.assertTrue(res["success"])
            self.assertEqual(res["mode"], "WEB_INTENT")
            self.assertEqual(res["platform"], "twitter")
            self.assertIn("twitter.com/intent/tweet", res["intent_url"])
            mock_web_open.assert_called_once()

    @patch("webbrowser.open")
    def test_publish_no_auto_open(self, mock_web_open):
        """Verifies auto_open=False suppresses browser launching."""
        with patch.dict(os.environ, {}, clear=True):
            res = self.agent.publish("linkedin", "Silent draft", auto_open=False)
            self.assertTrue(res["success"])
            mock_web_open.assert_not_called()

    @patch("requests.post")
    def test_publish_direct_api_success(self, mock_post):
        """Verifies direct API publishing when valid bearer token is configured."""
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_post.return_value = mock_resp

        with patch.dict(os.environ, {"TWITTER_BEARER_TOKEN": "mock_valid_token"}):
            ok, msg = self.agent.publish_direct_api("twitter", "Direct API Tweet")
            self.assertTrue(ok)
            self.assertIn("Tweet published directly via X API v2", msg)
            mock_post.assert_called_once()

    def test_publish_direct_api_unconfigured(self):
        """Verifies direct API returns informative failure when credentials are missing."""
        with patch.dict(os.environ, {}, clear=True):
            ok, msg = self.agent.publish_direct_api("twitter", "Direct API Tweet")
            self.assertFalse(ok)
            self.assertIn("No TWITTER_BEARER_TOKEN", msg)

    def test_get_status_structure(self):
        """Verifies status payload structure."""
        status = self.agent.get_status()
        self.assertIn("supported_platforms", status)
        self.assertIn("history_count", status)
        self.assertIn("recent_posts", status)
        self.assertIn("api_keys_configured", status)
        self.assertIn("twitter", status["api_keys_configured"])

    @patch("webbrowser.open")
    def test_local_intelligence_social_commands(self, mock_web_open):
        """Verifies voice and text command execution in LocalIntelligence."""
        # 1. Social status
        handled, msg = local_intelligence.evaluate_and_execute("social media status")
        self.assertTrue(handled)
        self.assertIn("Social media publisher online", msg)

        # 2. Post to Twitter
        handled, msg = local_intelligence.evaluate_and_execute("post to twitter Hello from unit test")
        self.assertTrue(handled)
        self.assertIn("Twitter composer", msg)

        # 3. Tweet alias
        handled, msg = local_intelligence.evaluate_and_execute("tweet Deploying Mark 85")
        self.assertTrue(handled)
        self.assertIn("Twitter composer", msg)

        # 4. Post to LinkedIn
        handled, msg = local_intelligence.evaluate_and_execute("post to linkedin Exciting milestone today")
        self.assertTrue(handled)
        self.assertIn("Linkedin composer", msg)


if __name__ == "__main__":
    unittest.main()
