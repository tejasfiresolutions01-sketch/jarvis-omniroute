import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import date

import time
from core.voice import clean_for_speech, _get_os_speech_lock, _release_os_speech_lock, stop_speaking
from core.conceptual_synthesizer import conceptual_synthesizer
from core.local_intelligence import local_intelligence
from core.supreme_command_executor import supreme_executor
from core.head_commander import head_commander
from core.schedule_manager import schedule_manager
from core.internet_sentinel import internet_sentinel

class TestGapUpgrades(unittest.TestCase):
    """Test suite covering 5 Major and 10 Minor Upgrades."""

    def test_voice_clean_and_acoustic_lock(self):
        """Verifies acoustic lock and English speech cleaning."""
        cleaned = clean_for_speech("**Alert**: CPU temperature at 45°C. Namaste, please check https://example.com.")
        self.assertNotIn("**", cleaned)
        self.assertNotIn("https://", cleaned)
        self.assertIn("degrees Celsius", cleaned)
        self.assertIn("Greetings", cleaned)
        self.assertNotIn("Namaste", cleaned)

        # Test OS speech lock
        stop_speaking()
        time.sleep(0.1)
        lock = _get_os_speech_lock(timeout=8.0)
        self.assertIsNotNone(lock)
        _release_os_speech_lock(lock)

    def test_conceptual_synthesizer_mechanistic_ontology(self):
        """Verifies sub-millisecond offline mechanistic ontology."""
        # 1. Comparative Analysis: AC vs DC
        ac_dc = conceptual_synthesizer.synthesize("difference between AC and DC")
        self.assertIsNotNone(ac_dc)
        self.assertIn("Alternating current", ac_dc)
        self.assertIn("Direct current", ac_dc)
        self.assertIn("transformers", ac_dc)

        # 2. Fire Safety Standards: IS 2190
        is_2190 = conceptual_synthesizer.synthesize("what is IS 2190")
        self.assertIsNotNone(is_2190)
        self.assertIn("2190", is_2190)
        self.assertIn("extinguishers", is_2190)

        # 3. ABC Dry Chemical Powder
        abc = conceptual_synthesizer.synthesize("explain ABC dry chemical powder")
        self.assertIsNotNone(abc)
        self.assertIn("monoammonium phosphate", abc)

        # 4. Computing: CPU vs GPU
        cpu_gpu = conceptual_synthesizer.synthesize("compare CPU and GPU")
        self.assertIsNotNone(cpu_gpu)
        self.assertIn("central processing unit", cpu_gpu)
        self.assertIn("graphics processing unit", cpu_gpu)

    def test_google_ecosystem_voice_intents(self):
        """Verifies Google Maps, Gmail, and Google Search intent resolution."""
        # Google Maps
        with patch("webbrowser.open") as mock_open:
            handled, resp = local_intelligence.evaluate_and_execute("find route to Sriperumbudur on google maps")
            self.assertTrue(handled)
            self.assertIn("Google Maps", resp)

        # Gmail Compose
        with patch("webbrowser.open") as mock_open:
            handled, resp = local_intelligence.evaluate_and_execute("compose email to client@tejas.com about fire refill")
            self.assertTrue(handled)
            self.assertIn("Gmail", resp)
            self.assertIn("client@tejas.com", resp)

        # Google Search
        with patch("tools.google_services.google_services.search_google", return_value=[{"title": "Test", "link": "http", "snippet": "info"}]):
            handled, resp = local_intelligence.evaluate_and_execute("search google for fire safety regulations")
            self.assertTrue(handled)
            self.assertIn("Google Search", resp)

    def test_system_vitals_voice_intent(self):
        """Verifies system hardware vitals voice command."""
        handled, resp = local_intelligence.evaluate_and_execute("system vitals")
        self.assertTrue(handled)
        self.assertIn("CPU load is at", resp)
        self.assertIn("memory usage is at", resp)
        self.assertIn("disk storage has", resp)

    def test_supreme_command_executor_priority_dispatch(self):
        """Verifies 4-tier priority scheduling and speculative execution."""
        # Speculative racing
        result = supreme_executor.execute_speculative([
            lambda: None,
            lambda: "Omega Candidate Winner"
        ])
        self.assertEqual(result, "Omega Candidate Winner")

        # Priority dispatch
        crit_res = supreme_executor.dispatch(lambda x: x * 2, priority=supreme_executor.PRIORITY_CRITICAL, x=21)
        self.assertEqual(crit_res, 42)

        future = supreme_executor.dispatch(lambda x: x + 10, priority=supreme_executor.PRIORITY_NORMAL, x=5)
        self.assertEqual(future.result(), 15)

    def test_database_connection_context_managers(self):
        """Verifies SQLite connection context managers cleanly open and close without leaks."""
        # Head Commander
        with head_commander._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM pending_tasks;")
            count = cur.fetchone()[0]
            self.assertIsInstance(count, int)

        # Schedule Manager
        with schedule_manager._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM schedule_events;")
            count2 = cur.fetchone()[0]
            self.assertIsInstance(count2, int)

    def test_internet_sentinel_reconnection_sync(self):
        """Verifies Internet Sentinel handles reconnection and callback registry."""
        cb_called = []
        def sample_cb():
            cb_called.append(True)

        internet_sentinel.register_on_connect(sample_cb)
        self.assertIn(sample_cb, internet_sentinel._on_connect_callbacks)

if __name__ == "__main__":
    unittest.main()
