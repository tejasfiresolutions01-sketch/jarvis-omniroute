"""
Unit and integration tests for RPA Orchestrator and Anti-Bot Scraping Engine.
Strictly in English.
"""

import os
import sys
import json
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.rpa_orchestrator import RPAOrchestrator, rpa_orchestrator, RPAFlowReport
from tools.antibot_scraper import AntiBotScraperEngine, antibot_scraper, ScrapedArticle


class TestRPAAndScraping(unittest.TestCase):

    def setUp(self):
        self.rpa = RPAOrchestrator()
        self.scraper = AntiBotScraperEngine()

    def test_rpa_initialization_and_flow_registration(self):
        """Verifies flow registration and default flows."""
        flows = self.rpa.list_flows()
        self.assertIn("gather_system_telemetry", flows)
        self.assertIn("clipboard_data_pipeline", flows)

        # Register custom test flow
        self.rpa.register_flow("custom_math_flow", [
            {
                "name": "multiply_numbers",
                "action": "execute_python",
                "code": "a = context.get('num1', 5); b = context.get('num2', 10); return {'product': a * b}"
            }
        ])
        self.assertIn("custom_math_flow", self.rpa.list_flows())

    def test_rpa_flow_execution_success(self):
        """Tests successful flow execution and context propagation."""
        self.rpa.register_flow("pipeline_test", [
            {
                "name": "generate_data",
                "action": "execute_python",
                "code": "return {'source_val': 42, 'greeting': 'Hello'}"
            },
            {
                "name": "transform_data",
                "action": "execute_python",
                "code": "val = context['source_val'] * 2; return {'doubled_val': val}"
            }
        ])

        report = self.rpa.execute_flow("pipeline_test", context={"num": 10})
        self.assertIsInstance(report, RPAFlowReport)
        self.assertEqual(report.total_steps, 2)
        self.assertEqual(report.successful_steps, 2)
        self.assertEqual(report.failed_steps, 0)
        self.assertEqual(report.artifacts.get("source_val"), 42)
        self.assertEqual(report.artifacts.get("doubled_val"), 84)

    def test_rpa_flow_error_handling(self):
        """Tests error recovery and abort behavior."""
        self.rpa.register_flow("failing_flow", [
            {
                "name": "will_fail",
                "action": "execute_python",
                "code": "raise ValueError('Simulated step breakdown')",
                "on_error": "abort"
            },
            {
                "name": "should_not_run",
                "action": "execute_python",
                "code": "return {'ran': True}"
            }
        ])

        report = self.rpa.execute_flow("failing_flow")
        self.assertEqual(report.successful_steps, 0)
        self.assertEqual(report.failed_steps, 1)
        self.assertEqual(len(report.step_results), 1)
        self.assertEqual(report.step_results[0].status, "FAILED")
        self.assertIn("Simulated step breakdown", report.step_results[0].error or "")

    def test_antibot_scraper_stealth_headers(self):
        """Verifies stealth headers construction."""
        headers = self.scraper._get_stealth_headers("https://example.com/products")
        self.assertIn("User-Agent", headers)
        self.assertIn("Accept", headers)
        self.assertIn("Referer", headers)
        self.assertEqual(headers["Referer"], "https://example.com/")

    def test_scraper_extract_tables(self):
        """Verifies HTML table parsing into structured row dictionaries."""
        mock_html = """
        <html>
            <body>
                <table id="price_table">
                    <thead>
                        <tr><th>Material</th><th>Unit Price</th><th>Stock</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>ABC Powder 6kg</td><td>INR 450</td><td>120</td></tr>
                        <tr><td>CO2 Gas 4.5kg</td><td>INR 550</td><td>85</td></tr>
                    </tbody>
                </table>
            </body>
        </html>
        """
        tables = self.scraper.extract_tables(mock_html)
        self.assertEqual(len(tables), 1)
        rows = tables[0]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Material"], "ABC Powder 6kg")
        self.assertEqual(rows[0]["Unit Price"], "INR 450")
        self.assertEqual(rows[1]["Stock"], "85")

    def test_scraper_extract_article_and_metadata(self):
        """Verifies clean text, headings, and JSON-LD metadata extraction."""
        mock_html = """
        <html>
            <head>
                <title>Fire Safety Technical Bulletin</title>
                <meta property="og:title" content="Fire Safety Standards 2026" />
                <script type="application/ld+json">
                    {"@type": "NewsArticle", "headline": "New IS 2190 Compliance Mandates"}
                </script>
            </head>
            <body>
                <header><nav><a href="/home">Home</a></nav></header>
                <h1>Critical Safety Regulation</h1>
                <p>All commercial premises must hydro-test extinguishers every 3 years.</p>
                <script>console.log("tracker");</script>
                <footer>Confidential</footer>
            </body>
        </html>
        """
        article = self.scraper.extract_article(mock_html)
        self.assertIsInstance(article, ScrapedArticle)
        self.assertEqual(article.title, "Fire Safety Technical Bulletin")
        self.assertIn("Critical Safety Regulation", article.headings)
        self.assertIn("All commercial premises must hydro-test", article.clean_text)
        self.assertNotIn("console.log", article.clean_text)
        self.assertNotIn("Confidential", article.clean_text)
        self.assertIn("og:title", article.metadata)
        self.assertIn("json_ld", article.metadata)
        self.assertEqual(article.metadata["json_ld"]["@type"], "NewsArticle")

    def test_scraper_extract_links(self):
        """Verifies normalized URL extraction with domain filtering."""
        mock_html = """
        <html>
            <body>
                <a href="/safety/protocols">Internal Safety Link</a>
                <a href="https://tenders.gov.in/notice_401">External Gov Tender</a>
                <a href="https://external-ads.com/promo">Unwanted Ads</a>
            </body>
        </html>
        """
        links = self.scraper.extract_links(mock_html, domain_filter="gov.in")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0], "https://tenders.gov.in/notice_401")


if __name__ == "__main__":
    unittest.main()
