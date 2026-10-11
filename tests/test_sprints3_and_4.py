"""
Unit tests for Sprints 3 & 4:
- VisualSemanticScraper
- PromptCompressor
- SynonymQueryExpander
- ContextStateCheckpointer
- PersonaDriftSentinel
Strictly in English.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.visual_semantic_scraper import VisualSemanticScraper
from core.prompt_memory_optimizer import (
    PromptCompressor,
    SynonymQueryExpander,
    ContextStateCheckpointer,
    PersonaDriftSentinel
)


class TestSprints3And4(unittest.TestCase):

    def setUp(self):
        self.vscraper = VisualSemanticScraper()

    def test_visual_semantic_sitemap_and_markdown(self):
        """Verifies sitemap XML parsing and HTML to markdown conversion."""
        mock_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/pricing</loc>
                <lastmod>2026-10-10</lastmod>
            </url>
        </urlset>
        """
        urls = self.vscraper.parse_sitemap(mock_sitemap)
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0]["loc"], "https://example.com/pricing")
        self.assertEqual(urls[0]["lastmod"], "2026-10-10")

        # HTML to Markdown
        html = """
        <html>
            <body>
                <h1>Header Title</h1>
                <p>First Paragraph.</p>
                <ul><li>Bullet One</li><li>Bullet Two</li></ul>
                <pre><code>print('ok')</code></pre>
            </body>
        </html>
        """
        md = self.vscraper.html_to_markdown(html)
        self.assertIn("# Header Title", md)
        self.assertIn("First Paragraph.", md)
        self.assertIn("- Bullet One", md)
        self.assertIn("```\nprint('ok')\n```", md)

    def test_content_delta_detection(self):
        """Verifies change detection between snapshots."""
        old_text = "Line 1: Status OK\nLine 2: Temperature Normal"
        new_text = "Line 1: Status OK\nLine 2: Temperature Warning\nLine 3: Pressure High"

        delta = self.vscraper.detect_content_delta(old_text, new_text)
        self.assertTrue(delta["has_changed"])
        self.assertGreater(delta["added_count"], 0)
        self.assertGreater(delta["removed_count"], 0)

    def test_prompt_compressor(self):
        """Verifies removal of filler phrases and token savings."""
        prompt = "Could you please tell me as an AI language model if the system is ready?"
        compressed, pct = PromptCompressor.compress_prompt(prompt)
        self.assertNotIn("could you please", compressed.lower())
        self.assertNotIn("as an ai language model", compressed.lower())
        self.assertIn("system is ready?", compressed)
        self.assertGreater(pct, 20.0)

    def test_synonym_query_expander(self):
        """Verifies domain engineering query expansion."""
        expanded = SynonymQueryExpander.expand_query("Inspect the extinguisher valve")
        self.assertGreater(len(expanded), 1)
        self.assertTrue(any("discharge valve" in q or "IS 15683" in q for q in expanded))

    def test_context_state_checkpointer(self):
        """Verifies conversation checkpoint save and restore."""
        checkpointer = ContextStateCheckpointer()
        sample_history = [{"role": "user", "content": "Run diagnostics."}]
        checkpointer.save_checkpoint(1, sample_history, {"active_tool": "rpa"})

        loaded = checkpointer.load_checkpoint()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["turn_index"], 1)
        self.assertEqual(len(loaded["history"]), 1)
        self.assertEqual(loaded["history"][0]["content"], "Run diagnostics.")

    def test_persona_drift_sentinel(self):
        """Verifies score boost for Butler demeanor and penalties for robotic disclaimers."""
        butler_response = "Certainly sir, telemetry indicates all systems online and operational."
        eval_butler = PersonaDriftSentinel.evaluate_response(butler_response)
        self.assertTrue(eval_butler["aligned"])
        self.assertGreaterEqual(eval_butler["persona_score"], 85)

        robotic_response = "As an AI, I cannot perform physical actions or feel emotions."
        eval_robotic = PersonaDriftSentinel.evaluate_response(robotic_response)
        self.assertFalse(eval_robotic["aligned"])
        self.assertLess(eval_robotic["persona_score"], 70)


if __name__ == "__main__":
    unittest.main()
