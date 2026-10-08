"""
Unit tests for J.A.R.V.I.S. Supreme Command Execution & Task Cancellation Core.
Validates:
1. Head Commander: Bulk cancellation of pending and in-progress tasks.
2. Schedule Manager: Bulk cancellation of uncompleted calendar events.
3. Supreme Command Executor: Windows process priority elevation and Tier 5 Omega upgrade.
4. Local Intelligence: Voice intent recognition for task cancellation and command execution elevation.
5. Combined directive execution: 'cancel all the pending tasks and upgrade the command execution to the highest level'.
"""

import unittest
from unittest.mock import patch, MagicMock

from core.head_commander import head_commander
from core.schedule_manager import schedule_manager
from core.supreme_command_executor import supreme_executor, SupremeCommandExecutor
from core.local_intelligence import local_intelligence


class TestSupremeCommandExecutor(unittest.TestCase):

    def setUp(self):
        self.executor = SupremeCommandExecutor()

    def test_process_elevation_and_upgrade(self):
        """Verifies process priority elevation and Tier 5 Omega upgrade."""
        status = self.executor.upgrade_execution_to_highest_level()
        self.assertIn("OMEGA", status["tier"])
        self.assertEqual(status["concurrency_limit"], 12)
        self.assertTrue(status["speculative_racing"])
        self.assertTrue(status["auto_remediation"])
        self.assertIn("highest level", status["message"].lower())

    def test_cancel_all_pending_tasks_in_head_commander(self):
        """Verifies cancelling all pending tasks in head commander."""
        # Create a test pending task
        head_commander.add_task(
            title="test pending directive cancellation",
            category="test",
            priority="normal"
        )
        cancelled_count = head_commander.cancel_all_pending_tasks()
        self.assertGreaterEqual(cancelled_count, 1)

        # Verify no pending tasks remain
        pending = head_commander.list_tasks(status="pending")
        self.assertEqual(len(pending), 0)

    def test_cancel_all_pending_events_in_schedule_manager(self):
        """Verifies cancelling all uncompleted events in schedule manager."""
        schedule_manager.add_event(
            title="Test Appointment",
            event_date="2026-10-09",
            event_time="10:00"
        )
        cancelled = schedule_manager.cancel_all_pending_events()
        self.assertGreaterEqual(cancelled, 1)

    def test_cancel_and_upgrade_simultaneous(self):
        """Verifies simultaneous task cancellation and execution elevation."""
        success, spoken = self.executor.cancel_and_upgrade()
        self.assertTrue(success)
        self.assertIn("cancelled", spoken.lower())
        self.assertIn("highest level", spoken.lower())
        self.assertIn("priority", spoken.lower())


class TestLocalIntelligenceSupremeIntents(unittest.TestCase):

    def test_combined_cancel_and_upgrade_directive(self):
        """Verifies the exact user directive 'cancel all the pending tasks and upgrade the command execution to the highest level'."""
        handled, resp = local_intelligence.evaluate_and_execute(
            "cancel all the pending tasks and upgrade the command execution to the highest level"
        )
        self.assertTrue(handled)
        self.assertIn("cancelled", resp.lower())
        self.assertIn("highest level", resp.lower())

    def test_cancel_pending_tasks_directive(self):
        """Verifies 'cancel all pending tasks' directive."""
        handled, resp = local_intelligence.evaluate_and_execute("cancel all pending tasks")
        self.assertTrue(handled)
        self.assertIn("cancelled", resp.lower())

    def test_upgrade_command_execution_directive(self):
        """Verifies 'upgrade the command execution to the highest level' directive."""
        handled, resp = local_intelligence.evaluate_and_execute(
            "upgrade the command execution to the highest level"
        )
        self.assertTrue(handled)
        self.assertIn("omega", resp.lower())
        self.assertIn("high priority", resp.lower())


if __name__ == "__main__":
    unittest.main()
