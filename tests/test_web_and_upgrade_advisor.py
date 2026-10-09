"""
Unit tests for J.A.R.V.I.S. Web Stream Monitor, Web Agent, and Daily Upgrade Advisor.
Validates targeted information streams, search, scraping, UI designing,
and permission-gated upgrade execution.
"""

import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.local_intelligence import local_intelligence
from core.upgrade_advisor import UpgradeAdvisor, upgrade_advisor
from tools.web_agent import WebAgent, web_agent
from tools.web_stream_monitor import WebStreamMonitor, web_stream_monitor


class TestWebAndUpgradeAdvisor(unittest.TestCase):

    def setUp(self):
        self.stream_mon = web_stream_monitor
        self.agent = web_agent
        self.advisor = upgrade_advisor

    def test_web_stream_feed_structure(self):
        """Verifies default curated feeds are properly categorized."""
        feeds = self.stream_mon.get_all_feeds()
        self.assertIn("tech", feeds)
        self.assertIn("world", feeds)
        self.assertIn("science", feeds)
        self.assertIn("business", feeds)
        self.assertGreater(len(feeds["tech"]), 0)

    def test_web_stream_add_custom_feed(self):
        """Verifies dynamic registration of custom RSS feeds."""
        success = self.stream_mon.add_custom_feed("tech", "Custom Tech Test", "https://example.com/rss.xml")
        self.assertTrue(success)

    def test_web_agent_check_connection(self):
        """Verifies web connection diagnostics returns structured response."""
        res = self.agent.check_connection()
        self.assertIn("online", res)
        self.assertIn("status", res)
        self.assertIn("endpoints_tested", res)

    def test_web_agent_design_preview(self):
        """Verifies web designing generates a valid responsive HTML file."""
        path = self.agent.design_preview("Test Project Preview", "<h1>Cyber Matrix</h1>", auto_open=False)
        self.assertTrue(Path(path).exists())
        content = Path(path).read_text(encoding="utf-8")
        self.assertIn("Cyber Matrix", content)
        self.assertIn("J.A.R.V.I.S. DESIGN STUDIO", content)

    def test_upgrade_advisor_generates_5_major_10_minor(self):
        """Verifies exactly 5 major and 10 minor upgrades are generated."""
        data = self.advisor.generate_daily_proposals(force=True)
        self.assertEqual(len(data["major"]), 5, "Must generate exactly 5 Major Upgrades")
        self.assertEqual(len(data["minor"]), 10, "Must generate exactly 10 Minor Upgrades")

        major_ids = [u["id"] for u in data["major"]]
        self.assertEqual(major_ids, ["MAJOR-1", "MAJOR-2", "MAJOR-3", "MAJOR-4", "MAJOR-5"])

        minor_ids = [u["id"] for u in data["minor"]]
        expected_minor = [f"MINOR-{i}" for i in range(1, 11)]
        self.assertEqual(minor_ids, expected_minor)

    def test_upgrade_advisor_permission_gate(self):
        """Verifies upgrades cannot execute without valid approval and record deployment."""
        # Invalid ID rejected
        ok, msg = self.advisor.execute_approved_upgrade("INVALID-99")
        self.assertFalse(ok)
        self.assertIn("not found", msg.lower())

        # Valid approved upgrade execution
        ok2, msg2 = self.advisor.execute_approved_upgrade("MINOR-2")
        self.assertTrue(ok2)
        self.assertIn("deployed successfully", msg2.lower())
        self.assertIn("Work Efficiency Recommendation", msg2)

        # Re-executing already deployed item recognizes state
        ok3, msg3 = self.advisor.execute_approved_upgrade("MINOR-2")
        self.assertTrue(ok3)
        self.assertIn("already deployed", msg3.lower())

    def test_local_intelligence_web_and_upgrade_intents(self):
        """Verifies voice directives for web connection, streams, and upgrades."""
        queries = [
            ("web connection status", "Web connection is"),
            ("suggest daily upgrades", "Daily Upgrade Advisory"),
            ("show major upgrades", "5 MAJOR ARCHITECTURAL UPGRADES"),
            ("show minor upgrades", "10 MINOR CODE & SYSTEM REFINEMENTS"),
            ("approve upgrade MINOR-10", "deployed successfully"),
        ]

        for q, expected in queries:
            handled, res = local_intelligence.evaluate_and_execute(q)
            self.assertTrue(handled, f"Query '{q}' failed to evaluate")
            self.assertIn(expected.lower(), res.lower(), f"Response for '{q}' did not contain '{expected}': {res}")


if __name__ == "__main__":
    unittest.main()
