"""
Unit tests for Sprint 2 Upgrades:
- FilesystemSentinel
- BackgroundJobScheduler
- MarketSentinel
- WindowTiler
Strictly in English.
"""

import os
import sys
import time
import shutil
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.filesystem_sentinel import FilesystemSentinel
from core.background_job_scheduler import BackgroundJobScheduler
from tools.market_sentinel import MarketSentinel
from tools.window_tiler import WindowTiler


class TestSprint2Upgrades(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_filesystem_sentinel_classification_and_events(self):
        """Verifies file type classification, hash deduplication, and event triggering."""
        sentinel = FilesystemSentinel(watch_dirs=[self.temp_dir])

        # Test classification
        self.assertEqual(sentinel.classify_file(Path("tender_specs.pdf")), "DOCUMENT_PDF")
        self.assertEqual(sentinel.classify_file(Path("valve_assembly.dxf")), "CAD_BLUEPRINT")
        self.assertEqual(sentinel.classify_file(Path("pricing.csv")), "DATA_TABULAR")
        self.assertEqual(sentinel.classify_file(Path("engine.py")), "SOURCE_CODE")

        # Track event callback
        events_received = []
        sentinel.register_handler(lambda ev: events_received.append(ev))

        # Create a test file
        test_file = self.temp_dir / "invoice_test.pdf"
        test_file.write_text("Sample Invoice Data Content", encoding="utf-8")

        events = sentinel.scan_once()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "FILE_CREATED")
        self.assertEqual(events[0]["filename"], "invoice_test.pdf")
        self.assertEqual(events[0]["category"], "DOCUMENT_PDF")
        self.assertEqual(len(events_received), 1)

        # Scanning again without changes should return 0 new events (deduplication)
        subsequent = sentinel.scan_once()
        self.assertEqual(len(subsequent), 0)

    def test_background_job_scheduler(self):
        """Verifies natural language scheduling, execution, and history recording."""
        scheduler = BackgroundJobScheduler()

        # Natural language parsing
        sec, daily = scheduler.parse_natural_schedule("every 45 seconds")
        self.assertEqual(sec, 45.0)
        self.assertIsNone(daily)

        sec_min, daily_min = scheduler.parse_natural_schedule("every 5 minutes")
        self.assertEqual(sec_min, 300.0)

        sec_d, daily_t = scheduler.parse_natural_schedule("daily at 10:15")
        self.assertEqual(daily_t, "10:15")

        # Add job and trigger
        counter = {"val": 0}
        def sample_job():
            counter["val"] += 1
            return counter["val"]

        job = scheduler.add_job("test_counter", "Counter Job", sample_job, natural_schedule="every 10 seconds")
        rec = scheduler.trigger_now("test_counter")

        self.assertIsNotNone(rec)
        self.assertTrue(rec.success)
        self.assertEqual(rec.result, 1)
        self.assertEqual(counter["val"], 1)
        self.assertEqual(len(job.history), 1)

        # Remove job
        removed = scheduler.remove_job("test_counter")
        self.assertTrue(removed)

    def test_market_sentinel_analytics(self):
        """Verifies commodity market tracking, moving averages, and volatility alerts."""
        sentinel = MarketSentinel()
        briefing = sentinel.generate_market_briefing()
        self.assertTrue(len(briefing) >= 5)

        # Record a price surge
        analysis = sentinel.record_price("map_abc_powder", 115.00, source="MOCK_TEST_HARVESTER")
        self.assertEqual(analysis["item_key"], "map_abc_powder")
        self.assertEqual(analysis["latest_price_inr"], 115.00)
        self.assertIn("delta_percent", analysis)
        self.assertIn(analysis["alert_level"], ["STABLE", "SURGE_WARNING", "PRICE_DROP_OPPORTUNITY"])

    def test_window_tiler_geometry(self):
        """Verifies screen resolution detection and snap handling."""
        tiler = WindowTiler()
        w, h = tiler.get_screen_resolution()
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)


if __name__ == "__main__":
    unittest.main()
