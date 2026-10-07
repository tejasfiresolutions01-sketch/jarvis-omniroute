"""
Unit tests for J.A.R.V.I.S. Task Orchestrator & Free Model Tool Execution.
"""

import unittest
from unittest.mock import patch, MagicMock
from core.task_orchestrator import TaskOrchestrator

class TestTaskOrchestrator(unittest.TestCase):

    def setUp(self):
        self.orchestrator = TaskOrchestrator()

    def test_is_complex_directive(self):
        self.assertTrue(self.orchestrator.is_complex_directive("search the web for SpaceX and save to notes.txt"))
        self.assertTrue(self.orchestrator.is_complex_directive("look at my screen and check vitals"))
        self.assertTrue(self.orchestrator.is_complex_directive("check CPU usage and write summary to file"))
        # Simple greetings should not be flagged as complex
        self.assertFalse(self.orchestrator.is_complex_directive("hello jarvis"))
        self.assertFalse(self.orchestrator.is_complex_directive("who are you"))

    def test_parse_tool_calls(self):
        plan = (
            "CALL: system_vitals()\n"
            "CALL: search_web(query='latest python release')\n"
            "CALL: write_file(filepath='test.txt', content='Sample content')\n"
        )
        calls = self.orchestrator.parse_tool_calls(plan)
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0][0], "system_vitals")
        self.assertEqual(calls[0][1], {})

        self.assertEqual(calls[1][0], "search_web")
        self.assertEqual(calls[1][1], {"query": "latest python release"})

        self.assertEqual(calls[2][0], "write_file")
        self.assertEqual(calls[2][1], {"filepath": "test.txt", "content": "Sample content"})

    def test_execute_tools_and_format_summary(self):
        calls = [
            ("system_vitals", {}),
            ("search_web", {"query": "test query"})
        ]
        with patch("tools.system_controller.system_controller.get_vitals", return_value={"cpu_usage": "10%", "ram_usage": "50%", "disk_free": "500 GB"}), \
             patch("core.task_orchestrator.search_web", return_value="Test Web Info"):
            obs = self.orchestrator.execute_tools(calls)
            self.assertEqual(len(obs), 2)
            self.assertTrue(obs[0]["success"])
            self.assertTrue(obs[1]["success"])

            summary = self.orchestrator.format_butler_summary(obs, "Check vitals and search")
            self.assertIn("CPU load is at 10%", summary)
            self.assertIn("Test Web Info", summary)
            self.assertIn("sir", summary.lower())

if __name__ == "__main__":
    unittest.main()
