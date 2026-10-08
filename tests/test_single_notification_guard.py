"""
Unit Tests for J.A.R.V.I.S. Single Notification Guard & Unprompted Speech Sentinel.
Tests:
- Single notification enforcement (strictly once per notification ID)
- Suppression of duplicate/repeated notifications unless explicitly asked again
- Suppression of unprompted speech on display wake or boot
- Explicit user repeat and query directives ('what was that notification?', 'repeat notification', 'read notifications')
- Task completion single-notification enforcement via NotificationSentinel
"""

import unittest
from unittest.mock import patch, MagicMock
from core.notification_guard import NotificationGuard, notification_guard
from core.local_intelligence import local_intelligence
from tools.notification_sentinel import NotificationSentinel
from core.display_sentinel import DisplaySentinel


class TestSingleNotificationGuard(unittest.TestCase):

    def setUp(self):
        self.guard = NotificationGuard()
        self.guard.clear_registry()

    def test_notify_strictly_once(self):
        """Verifies a notification is delivered strictly once, and duplicate attempts are suppressed."""
        with patch.object(self.guard, "_vocalize") as mock_vocalize:
            # First attempt: should succeed and vocalize
            res1 = self.guard.notify_once(
                notification_id="task:101",
                message="Task 101 completed successfully, sir.",
                category="task",
                is_user_command=True
            )
            self.assertTrue(res1)
            mock_vocalize.assert_called_once_with("Task 101 completed successfully, sir.")

            # Second attempt with same ID: must be SUPPRESSED
            mock_vocalize.reset_mock()
            res2 = self.guard.notify_once(
                notification_id="task:101",
                message="Task 101 completed successfully, sir.",
                category="task",
                is_user_command=True
            )
            self.assertFalse(res2, "Duplicate notification must be suppressed")
            mock_vocalize.assert_not_called()

    def test_repeat_only_when_asked_again(self):
        """Verifies a notification can be repeated IF AND ONLY IF the user explicitly asks for it."""
        with patch.object(self.guard, "_vocalize") as mock_vocalize:
            self.guard.notify_once(
                notification_id="meeting:board",
                message="Meeting scheduled at 3 PM, sir.",
                is_user_command=True
            )

            # User asks to repeat
            last = self.guard.request_repeat("meeting:board")
            self.assertEqual(last, "Meeting scheduled at 3 PM, sir.")

            # Now a repeat is permitted exactly once
            res_repeat = self.guard.notify_once(
                notification_id="meeting:board",
                message="Meeting scheduled at 3 PM, sir.",
                is_user_command=True
            )
            self.assertTrue(res_repeat)
            mock_vocalize.assert_called_with("Meeting scheduled at 3 PM, sir.")

            # Subsequent unasked attempt is suppressed again
            mock_vocalize.reset_mock()
            res_subsequent = self.guard.notify_once(
                notification_id="meeting:board",
                message="Meeting scheduled at 3 PM, sir.",
                is_user_command=True
            )
            self.assertFalse(res_subsequent)
            mock_vocalize.assert_not_called()

    def test_unprompted_speech_suppressed(self):
        """Verifies unprompted notifications are logged silently without vocalizing unless commanded."""
        with patch.object(self.guard, "_vocalize") as mock_vocalize, \
             patch("config.UNPROMPTED_NOTIFICATIONS_ENABLED", False):

            # Unprompted alert without user command
            res = self.guard.notify_once(
                notification_id="background_strain",
                message="CPU load elevated",
                category="vitals",
                is_user_command=False,
                allow_unprompted=False
            )
            self.assertFalse(res)
            mock_vocalize.assert_not_called()

            # Message is still recorded in history so user can ask what happened
            self.assertEqual(self.guard.get_last_notification(), "CPU load elevated")


class TestLocalIntelligenceNotificationDirectives(unittest.TestCase):

    def setUp(self):
        notification_guard.clear_registry()

    def test_what_was_that_notification_directive(self):
        """Verifies 'what was that notification' and 'repeat notification' vocalize the last notification."""
        # Prime a notification
        notification_guard.notify_once(
            notification_id="fire_alarm_test",
            message="Industrial safety sensors are fully synchronized, sir.",
            is_user_command=True
        )

        handled, resp = local_intelligence.evaluate_and_execute("what was that notification")
        self.assertTrue(handled)
        self.assertIn("Repeating your notification", resp)
        self.assertIn("safety sensors", resp)

        handled2, resp2 = local_intelligence.evaluate_and_execute("repeat notification")
        self.assertTrue(handled2)
        self.assertIn("safety sensors", resp2)

    def test_read_notifications_directive(self):
        """Verifies 'read notifications' returns list of recent alerts."""
        notification_guard.notify_once(
            notification_id="note_1",
            message="Meeting at 4 PM",
            is_user_command=True
        )

        handled, resp = local_intelligence.evaluate_and_execute("read notifications")
        self.assertTrue(handled)
        self.assertIn("Meeting at 4 PM", resp)

    def test_no_notifications_on_record(self):
        """Verifies clean response when there are zero prior notifications."""
        handled, resp = local_intelligence.evaluate_and_execute("what was that notification")
        self.assertTrue(handled)
        self.assertIn("no prior notifications", resp.lower())


class TestSentinelSingleNotificationIntegrations(unittest.TestCase):

    def setUp(self):
        notification_guard.clear_registry()

    def test_notification_sentinel_notifies_task_once(self):
        """Verifies task completion is notified strictly once per task ID."""
        sentinel = NotificationSentinel()
        with patch("core.voice.speak") as mock_speak, \
             patch.object(sentinel, "notify", return_value=True):

            # First notification succeeds
            sentinel.notify_task_completed(task_id=42, task_title="Deep Space Telemetry")
            self.assertEqual(mock_speak.call_count, 1)

            # Second notification for same task ID is suppressed
            sentinel.notify_task_completed(task_id=42, task_title="Deep Space Telemetry")
            self.assertEqual(mock_speak.call_count, 1, "Must not repeat task notification without being asked")

    def test_display_sentinel_suppresses_unprompted_greeting(self):
        """Verifies DisplaySentinel does not vocalize on display wake when DISPLAY_GREETINGS_VOCAL is False."""
        disp = DisplaySentinel()
        with patch("core.voice.speak") as mock_speak, \
             patch("config.DISPLAY_GREETINGS_VOCAL", False), \
             patch("core.hologram_sentinel.hologram_sentinel.display_hologram"):

            disp.trigger_greeting(reason="user_returned_to_display")
            mock_speak.assert_not_called()


if __name__ == "__main__":
    unittest.main()
