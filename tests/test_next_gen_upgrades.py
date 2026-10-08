"""
Unit test suite verifying the 5 Next-Generation Upgrades:
1. Full-Duplex Continuous Conversation & Ambient Biometric Diarization
2. Autonomous Live B2B Lead Harvester & DNS MX Verification Engine
3. Proactive Multimodal Vision & Active IDE Co-Pilot
4. Zero-Cost Embedded Local SLM & Offline Neural Reasoning Runtime
5. Canary Sandboxing & Latency Immune System for Self-Evolution
"""

import os
import sys
import unittest
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.listener import listener
from core.voice_biometrics import voice_biometrics
from tools.lead_harvester import lead_harvester
from core.vision_copilot import vision_copilot
from core.local_neural_slm import local_neural_slm
from core.canary_sandbox import canary_sandbox
from core.local_intelligence import local_intelligence
from core.brain import brain

class TestNextGenUpgrades(unittest.TestCase):
    """Verifies all 5 Next-Generation Upgrades under unit test conditions."""

    # ─────────────────────────────────────────────────────────────────────
    # Upgrade 1: Full-Duplex Voice & Ambient Biometric Diarization
    # ─────────────────────────────────────────────────────────────────────
    def test_full_duplex_conversation_lease(self):
        """Verifies conversational lease management and state transitions."""
        listener.close_conversation_lease()
        self.assertFalse(listener.has_active_conversation_lease())

        listener.renew_conversation_lease(duration=5.0)
        self.assertTrue(listener.has_active_conversation_lease())

        listener.close_conversation_lease()
        self.assertFalse(listener.has_active_conversation_lease())

    def test_biometric_owner_speaking_check(self):
        """Verifies rapid biometric speaker diarization filter."""
        # Generate dummy 16kHz audio array
        sample_rate = 16000
        t = np.linspace(0, 1.0, sample_rate, False)
        # 120Hz fundamental pitch (male chest resonance)
        tone = (np.sin(2 * np.pi * 120 * t) * 8000).astype(np.int16)
        pcm_bytes = tone.tobytes()

        # Should execute without throwing and return a bool
        result = voice_biometrics.is_owner_speaking(pcm_bytes, sample_rate)
        self.assertIsInstance(result, bool)

    # ─────────────────────────────────────────────────────────────────────
    # Upgrade 2: Autonomous Live B2B Lead Harvester & Verification Engine
    # ─────────────────────────────────────────────────────────────────────
    def test_lead_harvester_corridor_scan(self):
        """Verifies B2B lead harvesting and IS 2190 qualification scoring."""
        leads = lead_harvester.harvest_leads_for_corridor("ambattur")
        self.assertGreater(len(leads), 0)
        top_lead = leads[0]
        self.assertIn("company_name", top_lead)
        self.assertIn("lead_score", top_lead)
        self.assertGreaterEqual(top_lead["lead_score"], 30)
        self.assertIn("extinguisher_needs", top_lead)

    def test_lead_harvester_mx_verification(self):
        """Verifies DNS MX record deliverability check."""
        # Known domain test
        has_mx, hosts, msg = lead_harvester.verify_dns_mx_record("google.com")
        self.assertTrue(has_mx)
        self.assertGreater(len(hosts), 0)

        # Invalid domain test
        bad_mx, bad_hosts, bad_msg = lead_harvester.verify_dns_mx_record("invalid-domain-xyz-404.nonexistent")
        self.assertFalse(bad_mx)

    def test_lead_harvester_voice_intents(self):
        """Verifies local intelligence voice routing for lead harvesting."""
        handled, resp = local_intelligence.evaluate_and_execute("harvest b2b leads in ambattur")
        self.assertTrue(handled)
        self.assertIn("lead harvesting completed", resp.lower())

        handled_mx, resp_mx = local_intelligence.evaluate_and_execute("verify lead domain google.com")
        self.assertTrue(handled_mx)
        self.assertIn("email delivery", resp_mx.lower())

    # ─────────────────────────────────────────────────────────────────────
    # Upgrade 3: Proactive Multimodal Vision & Active IDE Co-Pilot
    # ─────────────────────────────────────────────────────────────────────
    def test_ide_context_inspection(self):
        """Verifies IDE context retrieval from active window."""
        ctx = vision_copilot.get_ide_context()
        self.assertIn("window_title", ctx)
        self.assertIn("is_developer_environment", ctx)

    def test_traceback_parser(self):
        """Verifies detection and parsing of Python traceback errors."""
        mock_traceback = (
            "Traceback (most recent call last):\n"
            '  File "c:/jarvis ai/core/sample.py", line 42, in run_task\n'
            "    undefined_var.execute()\n"
            "AttributeError: 'NoneType' object has no attribute 'execute'"
        )
        parsed = vision_copilot.parse_traceback_text(mock_traceback)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["error_type"], "AttributeError")
        self.assertEqual(parsed["file"], "sample.py")
        self.assertEqual(parsed["line"], "42")

    def test_ide_copilot_voice_intent(self):
        """Verifies voice directive for IDE co-pilot screen diagnosis."""
        handled, resp = local_intelligence.evaluate_and_execute("check my code")
        self.assertTrue(handled)
        self.assertIsInstance(resp, str)
        self.assertGreater(len(resp), 10)

    # ─────────────────────────────────────────────────────────────────────
    # Upgrade 4: Zero-Cost Embedded Local SLM & Offline Reasoning
    # ─────────────────────────────────────────────────────────────────────
    def test_local_slm_math_expressions(self):
        """Verifies zero-cost offline mathematical deduction."""
        ans_mult = local_neural_slm.solve_math_expression("what is 25 times 4")
        self.assertIsNotNone(ans_mult)
        self.assertIn("100", ans_mult)

        ans_sqrt = local_neural_slm.solve_math_expression("square root of 144")
        self.assertIsNotNone(ans_sqrt)
        self.assertIn("12", ans_sqrt)

    def test_local_slm_semantic_knowledge(self):
        """Verifies deep offline semantic knowledge retrieval."""
        ans_photo = local_neural_slm.query_semantic_knowledge("explain photosynthesis")
        self.assertIsNotNone(ans_photo)
        self.assertIn("chlorophyll", ans_photo.lower())

        ans_rec = local_neural_slm.reason("how does recursion work")
        self.assertIsNotNone(ans_rec)
        self.assertIn("function calls itself", ans_rec.lower())

    def test_brain_offline_slm_fallback(self):
        """Verifies brain falls back to Local Neural SLM when offline."""
        resp = brain.think("what is 60 times 5")
        self.assertIn("300", resp)

    # ─────────────────────────────────────────────────────────────────────
    # Upgrade 5: Canary Sandboxing & Latency Immune System
    # ─────────────────────────────────────────────────────────────────────
    def test_canary_sandbox_benchmark(self):
        """Verifies canary audit execution and latency thresholds."""
        audit = canary_sandbox.execute_canary_audit()
        self.assertIn("status", audit)
        self.assertIn("avg_latency_ms", audit)
        self.assertIn("memory_delta_mb", audit)
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["status"], "APPROVED")

    def test_latency_immune_voice_intent(self):
        """Verifies voice directive for latency immune telemetry."""
        handled, resp = local_intelligence.evaluate_and_execute("latency immune system status")
        self.assertTrue(handled)
        self.assertIn("latency immune system is active", resp.lower())

if __name__ == "__main__":
    unittest.main()
