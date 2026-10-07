"""
Unit tests for J.A.R.V.I.S. Proactive Butler Agent & Protocol Sunrise.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from core.proactive_agent import ProactiveButlerAgent

class TestProactiveAgent(unittest.TestCase):

    def setUp(self):
        self.agent = ProactiveButlerAgent()

    def test_set_sunrise_time(self):
        msg = self.agent.set_sunrise_time("07:30")
        self.assertEqual(self.agent.sunrise_time, "07:30")
        self.assertIn("07:30 AM", msg)

        msg2 = self.agent.set_sunrise_time("8:15 AM")
        self.assertEqual(self.agent.sunrise_time, "08:15")
        self.assertIn("08:15 AM", msg2)

    def test_check_schedule_reminders_pre_and_ontime(self):
        now = datetime.now()
        # Event in exactly 9.5 minutes
        ev_time = now + timedelta(minutes=9.5)
        ev_str = ev_time.strftime("%H:%M")

        fake_schedule = [
            {"id": 101, "title": "Stark Board Meeting", "event_time": ev_str}
        ]

        with patch("core.schedule_manager.schedule_manager.get_events_for_date", return_value=fake_schedule), \
             patch.object(self.agent, "_deliver_proactive_alert") as mock_alert:

            self.agent.check_schedule_reminders()
            # Should deliver pre-alert
            self.assertTrue(mock_alert.called)
            self.assertIn("101:10min", self.agent._notified_events)

            # Calling again within same interval should not double-notify
            mock_alert.reset_mock()
            self.agent.check_schedule_reminders()
            self.assertFalse(mock_alert.called)

    def test_hardware_health_cooldown(self):
        with patch("tools.system_controller.system_controller.get_vitals", return_value={"cpu_usage": "98%", "ram_usage": "97%"}), \
             patch.object(self.agent, "_deliver_proactive_alert") as mock_alert:

            # Consecutive high loads required
            self.agent.check_hardware_health()
            self.agent.check_hardware_health()
            self.agent.check_hardware_health()

            self.assertTrue(mock_alert.called)

if __name__ == "__main__":
    unittest.main()
