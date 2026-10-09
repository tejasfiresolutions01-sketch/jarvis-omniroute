"""
Unit tests for J.A.R.V.I.S. Unified System Orchestration & Executive Dashboard Matrix.
Validates:
1. Executive Telemetry Aggregation across all 11 Upgrades.
2. High-Fidelity British Butler Spoken Briefing Synthesis.
3. Cybernetic Executive Dashboard HTML Rendering.
4. Web Portal /dashboard and /api/orchestration/dashboard HTTP Endpoints.
5. Local Intelligence Voice Intent Routing.
"""

import json
import urllib.request
import unittest
from unittest.mock import patch, MagicMock

from core.system_orchestration import SystemOrchestrationEngine, system_orchestrator
from core.local_intelligence import local_intelligence
from ui.web_portal import WebPortalServer


def find_free_port():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class TestSystemOrchestration(unittest.TestCase):

    def setUp(self):
        self.orchestrator = SystemOrchestrationEngine()

    def test_executive_telemetry_aggregation(self):
        """Verifies consolidated telemetry spans all 11 upgrades."""
        tel = self.orchestrator.get_executive_telemetry()
        self.assertIsInstance(tel, dict)
        self.assertIn("timestamp", tel)
        self.assertIn("uptime_seconds", tel)
        self.assertIn("composite_score", tel)
        self.assertIn("readiness_level", tel)
        self.assertIn("subsystems", tel)

        subs = tel["subsystems"]
        expected_modules = [
            "neural_vad",
            "local_slm",
            "windows_uia",
            "mesh_3d_engine",
            "gesture_controller",
            "web_portal",
            "quotation_engine",
            "smart_home",
            "vision_perception",
            "self_healing"
        ]
        for mod in expected_modules:
            self.assertIn(mod, subs, f"Subsystem '{mod}' missing from telemetry aggregation")
            self.assertIn("status", subs[mod])

    def test_generate_executive_briefing(self):
        """Verifies spoken executive briefing includes all key status indicators."""
        briefing = self.orchestrator.generate_executive_briefing()
        self.assertIsInstance(briefing, str)
        self.assertIn("sir", briefing.lower())
        self.assertIn("orchestration matrix", briefing.lower())
        self.assertIn("resilience index", briefing.lower())
        self.assertIn("eleven", briefing.lower())

    def test_get_executive_dashboard_html(self):
        """Verifies futuristic cybernetic dashboard HTML renders cleanly."""
        html = self.orchestrator.get_executive_dashboard_html()
        self.assertIsInstance(html, str)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("EXECUTIVE ORCHESTRATION MATRIX", html)
        self.assertIn("COMPOSITE RESILIENCE SCORE", html)
        self.assertIn("NEURAL REASONING & SLM", html)
        self.assertIn("SMART HOME PERIMETER", html)

    def test_local_intelligence_orchestration_directives(self):
        """Verifies voice directive intent resolution in local intelligence."""
        # 1. Orchestration briefing
        handled, resp = local_intelligence.evaluate_and_execute("orchestration briefing")
        self.assertTrue(handled)
        self.assertIn("sir", resp.lower())
        self.assertIn("orchestration matrix", resp.lower())

        # 2. Master system status
        handled, resp = local_intelligence.evaluate_and_execute("master system status")
        self.assertTrue(handled)
        self.assertIn("resilience index", resp.lower())

    def test_web_portal_dashboard_endpoints(self):
        """Verifies /dashboard and /api/orchestration/dashboard endpoints."""
        http_p = find_free_port()
        ws_p = find_free_port()
        while ws_p == http_p:
            ws_p = find_free_port()

        portal = WebPortalServer(port=http_p, ws_port=ws_p)
        portal.start()
        import time
        time.sleep(0.2)

        try:
            # 1. Test HTML Dashboard
            url_html = f"http://127.0.0.1:{http_p}/dashboard"
            req = urllib.request.Request(url_html)
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                self.assertEqual(resp.status, 200)
                html_body = resp.read().decode("utf-8")
                self.assertIn("EXECUTIVE ORCHESTRATION MATRIX", html_body)

            # 2. Test JSON Telemetry API
            url_api = f"http://127.0.0.1:{http_p}/api/orchestration/dashboard"
            req2 = urllib.request.Request(url_api)
            with urllib.request.urlopen(req2, timeout=3.0) as resp2:
                self.assertEqual(resp2.status, 200)
                json_data = json.loads(resp2.read().decode("utf-8"))
                self.assertIn("composite_score", json_data)
                self.assertIn("subsystems", json_data)
        finally:
            portal.stop()



if __name__ == "__main__":
    unittest.main()
