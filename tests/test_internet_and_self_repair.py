"""
Unit tests for J.A.R.V.I.S. Opportunistic Internet Sentinel and Autonomous Self-Repair Engine.
Validates:
1. Internet Sentinel: Rapid reachability detection, reconnection routines, and state caching.
2. Self-Repair Engine: Subsystem healing (network, audio, databases, display, daemons, resources).
3. Full self-repair sweep and plain English British Butler verbal reporting.
4. Local Intelligence: Voice intent recognition for self-repair and internet connection directives.
5. Brain: Opportunistic connectivity and automated retry after self-healing.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import time
import os

from core.internet_sentinel import InternetSentinel, internet_sentinel
from core.self_repair import SelfRepairEngine, self_repair_engine
from core.local_intelligence import local_intelligence
from core.brain import brain


class TestInternetSentinel(unittest.TestCase):

    def setUp(self):
        self.sentinel = InternetSentinel()

    @patch("socket.socket")
    def test_connectivity_success_via_socket(self, mock_socket_cls):
        """Verifies rapid Tier-1 socket reachability."""
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock
        connected = self.sentinel.check_connectivity(timeout=0.5)
        self.assertTrue(connected)
        self.assertTrue(self.sentinel.is_connected())

    @patch("socket.socket")
    @patch("urllib.request.urlopen")
    def test_connectivity_fallback_to_http(self, mock_urlopen, mock_socket_cls):
        """Verifies HTTP fallback when raw sockets are blocked."""
        mock_socket_cls.side_effect = Exception("Socket blocked")
        mock_urlopen.return_value.__enter__.return_value = MagicMock()
        connected = self.sentinel.check_connectivity(timeout=0.5)
        self.assertTrue(connected)

    @patch("socket.socket")
    @patch("urllib.request.urlopen")
    def test_connectivity_failure_handled(self, mock_urlopen, mock_socket_cls):
        """Verifies clean offline detection without crashes."""
        mock_socket_cls.side_effect = Exception("No network")
        mock_urlopen.side_effect = Exception("No route to host")
        connected = self.sentinel.check_connectivity(timeout=0.5)
        self.assertFalse(connected)

    @patch.object(InternetSentinel, "check_connectivity", return_value=True)
    @patch("subprocess.run")
    def test_reconnect_success(self, mock_run, mock_check):
        """Verifies reconnect flushes DNS and reports verified status."""
        success, msg = self.sentinel.reconnect()
        self.assertTrue(success)
        self.assertIn("operational", msg.lower())


class TestSelfRepairEngine(unittest.TestCase):

    def setUp(self):
        self.engine = SelfRepairEngine()

    @patch("core.internet_sentinel.internet_sentinel.reconnect", return_value=(True, "Internet verified."))
    def test_repair_network(self, mock_reconnect):
        """Verifies network and gateway repair delegation."""
        success, msg = self.engine.repair_network()
        self.assertTrue(success)
        self.assertTrue(mock_reconnect.called)

    def test_repair_audio_subsystem(self):
        """Verifies speech lock cleaning and audio pipeline reset."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_lock = Path(tmp_dir) / "jarvis_speech.lock"
            test_lock.write_text("lock_test")
            past_time = time.time() - 25.0
            os.utime(test_lock, (past_time, past_time))

            with patch("config.BASE_DIR", tmp_dir):
                # Ensure logs subdir exists in mocked BASE_DIR
                (Path(tmp_dir) / "logs").mkdir(exist_ok=True)
                mock_target = Path(tmp_dir) / "logs" / "jarvis_speech.lock"
                mock_target.write_text("lock_test")
                os.utime(mock_target, (past_time, past_time))

                success, msg = self.engine.repair_audio_subsystem()
                self.assertTrue(success)
                self.assertFalse(mock_target.exists())

    def test_repair_databases(self):
        """Verifies database integrity check and WAL checkpoint."""
        success, msg = self.engine.repair_databases()
        self.assertTrue(success)
        self.assertIn("database", msg.lower())

    @patch("core.hologram_sentinel.hologram_sentinel.display_hologram")
    def test_repair_hologram_display(self, mock_disp):
        """Verifies HUD display verification."""
        success, msg = self.engine.repair_hologram_display()
        self.assertTrue(success)
        self.assertTrue(mock_disp.called)

    def test_run_full_repair_manual(self):
        """Verifies full system repair returns polite spoken summary."""
        with patch.object(self.engine, "repair_network", return_value=(True, "OK")), \
             patch.object(self.engine, "repair_audio_subsystem", return_value=(True, "OK")), \
             patch.object(self.engine, "repair_databases", return_value=(True, "OK")), \
             patch.object(self.engine, "repair_hologram_display", return_value=(True, "OK")), \
             patch.object(self.engine, "repair_sentinels_and_daemons", return_value=(True, "OK")), \
             patch.object(self.engine, "repair_system_resources", return_value=(True, "OK")):

            res = self.engine.run_full_repair(manual=True)
            self.assertTrue(res["all_rectified"])
            self.assertIn("spoken_response", res)
            spoken = res["spoken_response"]
            self.assertIn("subsystems", spoken.lower())
            self.assertIn("sir", spoken.lower())


class TestLocalIntelligenceSelfRepairDirectives(unittest.TestCase):

    def test_repair_yourself_directive(self):
        """Verifies 'repair yourself' triggers full self-repair."""
        handled, resp = local_intelligence.evaluate_and_execute("repair yourself")
        self.assertTrue(handled)
        self.assertTrue(any(w in resp.lower() for w in ["repair", "subroutines", "operational", "subsystems"]))

    def test_fix_yourself_directive(self):
        """Verifies 'fix yourself' triggers full self-repair."""
        handled, resp = local_intelligence.evaluate_and_execute("fix yourself")
        self.assertTrue(handled)
        self.assertTrue(any(w in resp.lower() for w in ["repair", "subroutines", "operational", "subsystems"]))

    def test_self_repair_directive(self):
        """Verifies 'self repair' directive."""
        handled, resp = local_intelligence.evaluate_and_execute("self repair")
        self.assertTrue(handled)
        self.assertTrue(any(w in resp.lower() for w in ["repair", "subroutines", "operational", "subsystems"]))

    def test_connect_to_internet_directive(self):
        """Verifies 'connect to internet' directive."""
        handled, resp = local_intelligence.evaluate_and_execute("connect to internet")
        self.assertTrue(handled)
        self.assertTrue(any(w in resp.lower() for w in ["internet", "network", "connectivity", "connection"]))

    def test_internet_status_directive(self):
        """Verifies 'internet status' directive."""
        handled, resp = local_intelligence.evaluate_and_execute("internet status")
        self.assertTrue(handled)
        self.assertTrue(any(w in resp.lower() for w in ["internet", "network", "operational", "connection"]))


class TestBrainOpportunisticAndHealedExecution(unittest.TestCase):

    @patch("core.internet_sentinel.internet_sentinel.is_connected", return_value=True)
    @patch("core.online_intelligence.online_intelligence.query", return_value="The speed of light in vacuum is approximately 299,792 kilometers per second, sir.")
    def test_brain_uses_online_when_connected(self, mock_query, mock_conn):
        """Verifies brain utilizes online cognitive matrix when internet is active."""
        resp = brain.think("what is the speed of light in vacuum")
        self.assertIn("299,792", resp)

    @patch("core.online_intelligence.online_intelligence.query", side_effect=[None, "Successfully resolved online after gateway healing, sir."])
    @patch("core.problem_healer.problem_healer.handle_problem", return_value=(True, "Restored"))
    def test_brain_retries_after_successful_healing(self, mock_handle, mock_query):
        """Verifies query automatically retries and succeeds if healing restored the network."""
        resp = brain.think("Calculate orbital velocity for low earth orbit trajectory")
        self.assertIn("successfully resolved", resp.lower())


if __name__ == "__main__":
    unittest.main()
