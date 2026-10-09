"""
Comprehensive Unit Test Suite for J.A.R.V.I.S. Three Frontier Pillars:
1. Global 24/7 Telemetry Sentinel & Anomaly Detection
2. Frontier Swarm Intelligence & RAG-Grounded Reasoning Core
3. Industrial Fault-Tolerant "Zero-Defect" Execution Sentinel
"""

import os
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.fault_tolerant_executor import FaultTolerantExecutor, fault_tolerant_executor
from core.frontier_intelligence_core import FrontierIntelligenceCore, frontier_intelligence_core
from core.local_intelligence import local_intelligence
from tools.global_telemetry_sentinel import GlobalTelemetrySentinel, global_telemetry_sentinel


class TestGlobalTelemetrySentinel(unittest.TestCase):

    def setUp(self):
        self.sentinel = global_telemetry_sentinel

    def test_calculate_urgency_scoring(self):
        """Verifies urgency scoring detects critical keywords and scales appropriately."""
        # High urgency alert
        score_high, triggers = self.sentinel.calculate_urgency(
            "Breaking: Critical Zero-Day Vulnerability Discovered in Cloud Core",
            "Emergency patching required after massive cyber attack."
        )
        self.assertGreaterEqual(score_high, 70)
        self.assertIn("breaking", triggers)
        self.assertIn("critical", triggers)
        self.assertIn("zero-day", triggers)

        # Nominal routine news
        score_low, _ = self.sentinel.calculate_urgency(
            "Community Garden Opens New Greenhouse",
            "Local residents gather to plant tomatoes and lettuce."
        )
        self.assertLess(score_low, 30)

    def test_parse_rss_xml(self):
        """Verifies structured parsing of standard RSS 2.0 channel XML."""
        sample_rss = """<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <title>Tech Dispatch</title>
            <item>
              <title>Quantum Processor Reaches 1000 Qubits</title>
              <link>https://example.com/quantum</link>
              <description>&lt;p&gt;Historic breakthrough in quantum coherence.&lt;/p&gt;</description>
            </item>
          </channel>
        </rss>"""
        items = self.sentinel.parse_feed_xml(sample_rss, "Tech Dispatch", "frontier_ai")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Quantum Processor Reaches 1000 Qubits")
        self.assertEqual(items[0]["category"], "frontier_ai")
        self.assertIn("breakthrough", items[0]["triggers"])

    def test_parse_atom_xml(self):
        """Verifies structured parsing of Atom feed XML."""
        sample_atom = """<?xml version="1.0" encoding="utf-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <title>Security Feed</title>
          <entry>
            <title>Critical Outage Reported</title>
            <link href="https://example.com/outage"/>
            <summary>Emergency engineers responding to power grid failure.</summary>
          </entry>
        </feed>"""
        items = self.sentinel.parse_feed_xml(sample_atom, "Security Feed", "cybersecurity")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Critical Outage Reported")
        self.assertEqual(items[0]["link"], "https://example.com/outage")

    def test_get_status_and_situation_report(self):
        """Verifies sentinel status and executive situation report generation."""
        status = self.sentinel.get_status()
        self.assertIn("stream_categories", status)
        self.assertIn("total_streams", status)
        self.assertGreater(status["total_streams"], 0)

        report = self.sentinel.format_situation_report()
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 10)


class TestFrontierIntelligenceCore(unittest.TestCase):

    def setUp(self):
        self.core = frontier_intelligence_core

    def test_get_status(self):
        """Verifies frontier intelligence status reporting."""
        status = self.core.get_status()
        self.assertEqual(status["swarm_status"], "ACTIVE")
        self.assertIn("deep_reasoning", status["available_domains"])
        self.assertTrue(status["local_slm_ready"])

    def test_synthesize_frontier_reasoning_fallback(self):
        """Verifies end-to-end multi-model reasoning with offline fallback resilience."""
        query = "Explain modular microservices resilience in high-throughput architectures"
        res = self.core.synthesize_frontier_reasoning(query, domain="deep_reasoning", include_rag=False)
        self.assertTrue(res["success"])
        self.assertEqual(res["query"], query)
        self.assertIn("response", res)
        self.assertGreater(len(res["response"]), 10)
        self.assertIn("latency_ms", res)
        self.assertIn(res["synthesis_mode"], ["SPECULATIVE_SWARM", "DIRECT_GROUNDED"])


class TestFaultTolerantExecutor(unittest.TestCase):

    def setUp(self):
        self.executor = FaultTolerantExecutor(failure_threshold=3, recovery_timeout=0.2)

    def test_preflight_syntax_check(self):
        """Verifies AST inspection catches syntax errors before runtime dispatch."""
        valid_code = "def compute():\n    return 42 * 2\n"
        ok, err = self.executor.preflight_syntax_check(valid_code)
        self.assertTrue(ok)
        self.assertIsNone(err)

        invalid_code = "def broken(:\n    return 42"
        ok_bad, err_bad = self.executor.preflight_syntax_check(invalid_code)
        self.assertFalse(ok_bad)
        self.assertIn("Syntax error", err_bad)

    def test_execute_with_retry_success(self):
        """Verifies immediate execution success resets circuit counters."""
        mock_func = MagicMock(return_value="Mission accomplished")
        ok, res = self.executor.execute_with_retry(mock_func, category="test_ops")
        self.assertTrue(ok)
        self.assertEqual(res, "Mission accomplished")
        mock_func.assert_called_once()

    def test_execute_with_retry_transient_recovery(self):
        """Verifies transient failures trigger retries and recover on subsequent attempt."""
        attempts = [0]

        def flaky_func():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ValueError("Transient network blip")
            return "Recovered"

        ok, res = self.executor.execute_with_retry(flaky_func, category="network_fetch", max_retries=3, initial_backoff=0.01)
        self.assertTrue(ok)
        self.assertEqual(res, "Recovered")
        self.assertEqual(attempts[0], 2)

    def test_circuit_breaker_tripping_and_rollback(self):
        """Verifies circuit breaker trips after reaching failure threshold and triggers rollback."""
        rollback_called = [False]

        def rollback():
            rollback_called[0] = True

        def always_fails():
            raise RuntimeError("Hardware disconnect")

        # 1. Failures reach threshold
        for _ in range(3):
            ok, _ = self.executor.execute_with_retry(
                always_fails,
                category="sensor_comm",
                max_retries=1,
                rollback_handler=rollback,
            )
            self.assertFalse(ok)

        self.assertTrue(rollback_called[0])

        # 2. Circuit is now OPEN; subsequent call is immediately blocked without executing
        dummy_func = MagicMock()
        ok_blocked, msg = self.executor.execute_with_retry(dummy_func, category="sensor_comm")
        self.assertFalse(ok_blocked)
        self.assertIn("Circuit breaker for 'sensor_comm' is OPEN", msg)
        dummy_func.assert_not_called()

        # 3. After recovery timeout, circuit enters HALF_OPEN and resets on success
        time.sleep(0.25)
        dummy_success = MagicMock(return_value="Restored")
        ok_recovered, res_recovered = self.executor.execute_with_retry(dummy_success, category="sensor_comm")
        self.assertTrue(ok_recovered)
        self.assertEqual(res_recovered, "Restored")


class TestLocalIntelligencePillarsIntegration(unittest.TestCase):

    def test_local_intelligence_global_telemetry_commands(self):
        """Verifies voice/text directives for Global Telemetry Sentinel."""
        handled, msg = local_intelligence.evaluate_and_execute("global telemetry status")
        self.assertTrue(handled)
        self.assertIn("Global telemetry sentinel active", msg)

        handled, msg = local_intelligence.evaluate_and_execute("world situation report")
        self.assertTrue(handled)
        self.assertIn("telemetry", msg.lower())

    def test_local_intelligence_frontier_swarm_commands(self):
        """Verifies voice/text directives for Frontier Swarm Core."""
        handled, msg = local_intelligence.evaluate_and_execute("frontier intelligence status")
        self.assertTrue(handled)
        self.assertIn("Frontier swarm core online", msg)

        handled, msg = local_intelligence.evaluate_and_execute("frontier reasoning How to optimize neural caching?")
        self.assertTrue(handled)
        self.assertIsInstance(msg, str)
        self.assertGreater(len(msg), 10)

    def test_local_intelligence_fault_tolerant_commands(self):
        """Verifies voice/text directives for Fault-Tolerant Executor."""
        handled, msg = local_intelligence.evaluate_and_execute("fault tolerant status")
        self.assertTrue(handled)
        self.assertIn("Fault-tolerant execution sentinel online", msg)


if __name__ == "__main__":
    unittest.main()
