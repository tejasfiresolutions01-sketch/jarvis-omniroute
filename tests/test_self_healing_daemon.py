"""
Unit tests for J.A.R.V.I.S. Autonomous Self-Healing Daemon & Process Resilience Matrix.
"""

import os
import time
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.self_repair import SelfRepairEngine, self_repair_engine
from core.local_intelligence import local_intelligence


class TestSelfHealingDaemon(unittest.TestCase):
    """Validates daemon supervision, memory pruning, port audits, and health score telemetry."""

    def setUp(self):
        self.engine = SelfRepairEngine()

    def test_daemon_registration_and_supervision(self):
        """Verifies custom daemon registration, dead thread detection, and resuscitation."""
        is_alive = False
        restarts = 0

        def check_status():
            return is_alive

        def restart_worker():
            nonlocal is_alive, restarts
            is_alive = True
            restarts += 1

        self.engine.register_daemon("mock_worker", "Mock Worker Daemon", check_status, restart_worker)
        self.assertIn("mock_worker", self.engine._supervised_daemons)

        # Supervise while dead -> Should resuscitate
        res = self.engine.supervise_daemons()
        self.assertIn("Mock Worker Daemon", res["revived"])
        self.assertTrue(is_alive)
        self.assertEqual(restarts, 1)

    def test_circuit_breaker_and_backoff(self):
        """Verifies exponential backoff and circuit breaker activation after 5 crashes."""
        fail_count = 0

        def dead_check():
            return False

        def failing_restart():
            nonlocal fail_count
            fail_count += 1

        self.engine.register_daemon("crash_worker", "Crash Worker", dead_check, failing_restart)
        d_meta = self.engine._supervised_daemons["crash_worker"]

        # Simulate 5 crashes
        for i in range(5):
            d_meta["last_restart_time"] = 0.0 # Force bypass of backoff delay
            self.engine.supervise_daemons()

        self.assertTrue(d_meta["circuit_breaker"])
        self.assertGreaterEqual(d_meta["failure_count"], 5)
        self.assertEqual(d_meta["backoff_delay"], 60.0)

        # Subsequent supervise calls should skip restart due to circuit breaker
        initial_restarts = d_meta["restarts_total"]
        self.engine.supervise_daemons()
        self.assertEqual(d_meta["restarts_total"], initial_restarts)

    def test_memory_leak_pruning(self):
        """Verifies multi-generational garbage collection and working set trimming."""
        res = self.engine.prune_memory_and_resources(force=True)
        self.assertTrue(res["pruned"])
        self.assertIn("rss_before_mb", res)
        self.assertIn("rss_after_mb", res)
        self.assertIn("system_ram_pct", res)
        self.assertGreaterEqual(res["rss_before_mb"], 0.0)

    def test_temp_file_housekeeping(self):
        """Verifies stale temporary files (>180s old) are cleaned from temp directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            stale_file = temp_path / "stale_temp_artifact.tmp"
            stale_file.write_text("temporary data")
            
            # Set mtime to 300 seconds ago
            past_time = time.time() - 300.0
            os.utime(stale_file, (past_time, past_time))

            with patch("config.BASE_DIR", temp_path):
                # Run memory pruning with force=True
                res = self.engine.prune_memory_and_resources(force=True)
                self.assertFalse(stale_file.exists())
                self.assertGreaterEqual(res["files_removed"], 1)

    def test_verify_and_repair_ports(self):
        """Verifies non-intrusive socket audit across web portal and websocket ports."""
        port_audit = self.engine.verify_and_repair_ports()
        self.assertIsInstance(port_audit, dict)
        # Should contain port entries
        self.assertTrue(len(port_audit) >= 1)
        for port, info in port_audit.items():
            self.assertIn("listening", info)

    def test_get_system_health_telemetry(self):
        """Verifies 0-100 composite health index and telemetry aggregation."""
        telemetry = self.engine.get_system_health_telemetry()
        self.assertIsInstance(telemetry, dict)
        self.assertIn("health_score", telemetry)
        self.assertIn("status", telemetry)
        self.assertIn("daemons_alive", telemetry)
        self.assertIn("daemons_total", telemetry)
        self.assertIn("daemon_matrix", telemetry)
        self.assertIn("process_rss_mb", telemetry)
        self.assertIn("system_ram_pct", telemetry)

        self.assertGreaterEqual(telemetry["health_score"], 0)
        self.assertLessEqual(telemetry["health_score"], 100)
        self.assertIn(telemetry["status"], ["Nominal", "Degraded", "Critical"])

    def test_get_health_voice_summary(self):
        """Verifies articulate British Butler phrasing for system health inquiries."""
        summary = self.engine.get_health_voice_summary()
        self.assertIsInstance(summary, str)
        self.assertIn("sir", summary.lower())
        self.assertIn("health score", summary.lower())
        self.assertIn("megabytes", summary.lower())

    def test_local_intelligence_health_and_healing_directives(self):
        """Verifies voice directive dispatch via local_intelligence."""
        # 1. System Health
        handled, resp = local_intelligence.evaluate_and_execute("system health")
        self.assertTrue(handled)
        self.assertIn("health score", resp.lower())
        self.assertIn("sir", resp.lower())

        # 2. Run Self Healing
        handled, resp = local_intelligence.evaluate_and_execute("run self healing")
        self.assertTrue(handled)
        self.assertIn("subsystems", resp.lower())
        self.assertIn("sir", resp.lower())


if __name__ == "__main__":
    unittest.main()
