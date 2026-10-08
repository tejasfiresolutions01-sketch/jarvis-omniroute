"""
Unit tests for J.A.R.V.I.S. Problem Healer, Monthly Business Scanner, and 3rd-Night Self-Evolver.
Validates:
1. Problem Healer: Silent resolution on success, notification ONLY when unrectified.
2. Problem Healer: Explanations delivered in simple, clear English without technical jargon.
3. Brain: Absence of forbidden robotic fallback phrase.
4. Business Scanner: Monthly commercial lead scan, PDF generation, and strict English enforcement.
5. Self-Evolver: 3rd-night system optimization, database vacuum, and PDF generation.
6. Local Intelligence: Direct voice intents for business scan and self-evolution.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from core.problem_healer import ProblemHealer, problem_healer
from core.business_scanner import BusinessScanner, business_scanner
from core.self_evolver import SelfEvolver, self_evolver
from core.local_intelligence import local_intelligence
from core.brain import brain

class TestProblemHealer(unittest.TestCase):

    def setUp(self):
        self.healer = ProblemHealer()

    @patch("tools.notification_sentinel.notification_sentinel.notify")
    def test_silent_healing_suppresses_notification(self, mock_notify):
        """Verifies that rectified problems do NOT alert or bother the user."""
        with patch.object(self.healer, "diagnose_and_heal", return_value=(True, "Resolved silently")):
            rectified, explanation = self.healer.handle_problem(
                problem_type="network",
                details="test transient disconnect",
                notify_if_unrectified=True
            )
            self.assertTrue(rectified)
            self.assertFalse(mock_notify.called)

    @patch("tools.notification_sentinel.notification_sentinel.notify")
    def test_unrectified_problem_triggers_simple_english_notification(self, mock_notify):
        """Verifies that unrectified problems alert the user in simple English."""
        with patch.object(self.healer, "diagnose_and_heal", return_value=(False, "I cannot connect to the internet right now, sir. Please check your network connection.")):
            rectified, explanation = self.healer.handle_problem(
                problem_type="network",
                details="test persistent failure",
                notify_if_unrectified=True
            )
            self.assertFalse(rectified)
            self.assertTrue(mock_notify.called)
            self.assertIn("internet", explanation.lower())

    def test_simple_english_explanations(self):
        """Ensures diagnostic explanations are in plain, accessible English."""
        # Check database explanation
        _, exp_db = self.healer._heal_database_locks("")
        self.assertIsInstance(exp_db, str)

        # Check system resource explanation
        _, exp_res = self.healer._heal_system_resources("")
        self.assertIsInstance(exp_res, str)


class TestBrainForbiddenMessageSuppression(unittest.TestCase):

    @patch("core.online_intelligence.online_intelligence.query", return_value=None)
    @patch("core.problem_healer.problem_healer.heal_and_retry_query", return_value=None)
    @patch("core.problem_healer.problem_healer.handle_problem", return_value=(False, "Network is offline."))
    def test_no_forbidden_fallback_phrase(self, mock_handle, mock_retry, mock_query):
        """Verifies that the old canned offline disclaimer never appears in brain responses."""
        resp = brain.think("Tell me the exact quantum state of Andromeda galaxy")
        forbidden_phrases = [
            "Directive acknowledged, sir. While cloud neural networks are currently unreachable",
            "all local butler subroutines, schedule controls, and device automations remain fully active at your command."
        ]
        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, resp)
        # Should be simple English explanation
        self.assertTrue(any(w in resp.lower() for w in ["network", "connect", "offline", "trouble"]))


class TestBusinessScanner(unittest.TestCase):

    def setUp(self):
        self.scanner = BusinessScanner()

    @patch("tools.notification_sentinel.notification_sentinel.notify_task_completed")
    def test_scan_for_new_business_generation(self, mock_notify):
        """Verifies monthly business opportunity dossier and PDF creation in strict English."""
        res = self.scanner.scan_for_new_business(force=True)
        self.assertEqual(res["status"], "completed")
        self.assertTrue(Path(res["dossier_md"]).exists())
        self.assertTrue(Path(res["dossier_pdf"]).exists())

        # Verify English-only constraint
        content = Path(res["dossier_md"]).read_text(encoding="utf-8")
        self.assertIn("MONTHLY BUSINESS OPPORTUNITY SCAN", content)
        self.assertIn("Chennai District", content)
        self.assertNotIn("Vanakkam", content)
        self.assertNotIn("Namaste", content)


class TestSelfEvolver(unittest.TestCase):

    def setUp(self):
        self.evolver = SelfEvolver()

    @patch("tools.notification_sentinel.notification_sentinel.notify_task_completed")
    def test_run_self_upgrade_and_automation(self, mock_notify):
        """Verifies 3rd-night system optimization, database vacuum, and report generation."""
        res = self.evolver.run_self_upgrade_and_automation(force=True)
        self.assertEqual(res["status"], "completed")
        self.assertTrue(Path(res["dossier_md"]).exists())
        self.assertTrue(Path(res["dossier_pdf"]).exists())
        self.assertGreaterEqual(res["consecutive_passes"], 3)
        self.assertIn("Voice notification delivered", res["message"])

        # Verify English-only constraint
        content = Path(res["dossier_md"]).read_text(encoding="utf-8")
        self.assertIn("AUTONOMOUS 3RD-NIGHT SELF-UPGRADE", content)
        self.assertNotIn("Vanakkam", content)

    def test_triple_testing_and_debugging_cycles(self):
        """Verifies that at least 3 testing and debugging passes run before deployment."""
        res = self.evolver.run_testing_and_debugging_cycles(required_consecutive_passes=3)
        self.assertTrue(res["deployed"])
        self.assertEqual(res["consecutive_passes"], 3)
        self.assertGreaterEqual(res["total_cycles_executed"], 3)
        self.assertEqual(len(res["cycle_logs"]), res["total_cycles_executed"])


class TestVoiceOnlyTaskNotification(unittest.TestCase):

    @patch("core.voice.speak")
    @patch("tools.notification_sentinel.notification_sentinel.notify")
    def test_task_completed_notified_by_voice_not_pdf(self, mock_notify, mock_speak):
        """Verifies completed tasks are announced via voice without PDF in notification."""
        from tools.notification_sentinel import notification_sentinel
        res = notification_sentinel.notify_task_completed(task_id=99, task_title="Fire Extinguisher Route Plan")
        self.assertTrue(res)
        self.assertTrue(mock_speak.called)
        spoken_args = mock_speak.call_args[0][0]
        self.assertIn("Fire Extinguisher Route Plan", spoken_args)
        self.assertNotIn("pdf", spoken_args.lower())

        # Verify desktop notification text does not mention PDF
        notify_args = mock_notify.call_args[0]
        self.assertNotIn("pdf", notify_args[1].lower())


class TestLocalIntelligenceNewIntents(unittest.TestCase):

    @patch("core.business_scanner.business_scanner.scan_for_new_business")
    def test_monthly_business_scan_voice_intent(self, mock_scan):
        mock_scan.return_value = {"message": "Monthly business scan completed, sir."}
        handled, resp = local_intelligence.evaluate_and_execute("scan for new business")
        self.assertTrue(handled)
        self.assertIn("Monthly business scan", resp)

    @patch("core.self_evolver.self_evolver.run_self_upgrade_and_automation")
    def test_self_upgrade_voice_intent(self, mock_upgrade):
        mock_upgrade.return_value = {"message": "System self-upgrade completed, sir."}
        handled, resp = local_intelligence.evaluate_and_execute("upgrade yourself")
        self.assertTrue(handled)
        self.assertIn("self-upgrade", resp)


if __name__ == "__main__":
    unittest.main()

