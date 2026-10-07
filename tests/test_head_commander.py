"""
Unit tests for J.A.R.V.I.S. Supreme Head Commander, Multi-Agent Syndicate,
and Off-Grid Hardware Standby Autonomy Sentinel.
"""

import os
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.head_commander import JarvisHeadCommander
from core.offgrid_sentinel import OffgridSentinel
from core.local_intelligence import local_intelligence

class TestHeadCommander(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_tasks.db"
        self.json_sync_path = Path(self.temp_dir) / "test_pending_tasks.json"
        self.commander = JarvisHeadCommander(db_path=self.db_path, json_sync_path=self.json_sync_path)

    def tearDown(self):
        self.commander.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_and_get_task(self):
        task = self.commander.add_task(
            title="Analyze enterprise marketing funnel",
            description="Audit CAC and LTV metrics for Q4",
            category="business",
            priority="high"
        )
        self.assertIsNotNone(task)
        self.assertEqual(task["title"], "Analyze enterprise marketing funnel")
        self.assertEqual(task["status"], "pending")
        self.assertEqual(task["priority"], "high")

        fetched = self.commander.get_task(task["id"])
        self.assertEqual(fetched["title"], "Analyze enterprise marketing funnel")

    def test_list_tasks_by_status(self):
        self.commander.add_task("Task 1")
        t2 = self.commander.add_task("Task 2")
        self.commander.update_task_progress(t2["id"], "completed", 100, "Done")

        pending = self.commander.list_tasks(status="pending")
        completed = self.commander.list_tasks(status="completed")

        self.assertEqual(len(pending), 1)
        self.assertEqual(len(completed), 1)

    def test_analyze_task_and_assign_agents_marketing(self):
        task = {
            "title": "Design global brand marketing campaign and ad copy",
            "description": "Target enterprise clients on LinkedIn and Google Search"
        }
        agents, tools, subtasks = self.commander.analyze_task_and_assign_agents(task)
        self.assertIn("marketing", agents)
        self.assertIn("search_web", tools)
        self.assertIn("write_file", tools)
        self.assertGreater(len(subtasks), 1)

    def test_analyze_task_and_assign_agents_accounts(self):
        task = {
            "title": "Audit corporate balance sheet and reconcile bookkeeping ledgers",
            "description": "Assess cash flow trajectories and invoices"
        }
        agents, tools, subtasks = self.commander.analyze_task_and_assign_agents(task)
        self.assertIn("accounts_and_bookkeeping", agents)
        self.assertIn("write_file", tools)

    def test_analyze_task_and_assign_agents_lead_gen(self):
        task = {
            "title": "Outbound lead generation campaign for SaaS founders",
            "description": "Prospect 500 decision makers and qualify via BANT"
        }
        agents, tools, subtasks = self.commander.analyze_task_and_assign_agents(task)
        self.assertTrue("lead_generation" in agents or "lead_verification" in agents)

    @patch("core.free_ai_matrix.free_ai_matrix.query_business_operation")
    @patch("tools.file_tools.write_file")
    def test_execute_task_full_lifecycle(self, mock_write, mock_query_biz):
        mock_query_biz.return_value = ("Comprehensive Marketing Strategy Plan Ready", "ddgw/claude-haiku-4-5")
        mock_write.return_value = "File created"

        task = self.commander.add_task("Develop growth marketing funnel")
        summary = self.commander.execute_task(task["id"])

        self.assertIn("completed with full precision", summary.lower())
        updated = self.commander.get_task(task["id"])
        self.assertEqual(updated["status"], "completed")
        self.assertEqual(updated["progress_percent"], 100)
        self.assertTrue(len(updated["result_summary"]) > 0)

    def test_sync_to_and_from_json(self):
        task = self.commander.add_task("Offline Sync Directive")
        self.commander.sync_to_json()
        self.assertTrue(self.json_sync_path.exists())

        with open(self.json_sync_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data["tasks"]), 1)
        self.assertEqual(data["tasks"][0]["title"], "Offline Sync Directive")

        # Simulate remote cloud execution updating JSON
        data["tasks"][0]["status"] = "completed"
        data["tasks"][0]["result_summary"] = "Completed by Cloud Drone"
        data["tasks"][0]["completed_at"] = "2026-10-08 12:00:00"
        with open(self.json_sync_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        self.commander.sync_from_json()
        updated = self.commander.get_task(task["id"])
        self.assertEqual(updated["status"], "completed")
        self.assertEqual(updated["result_summary"], "Completed by Cloud Drone")

    def test_generate_offline_debrief(self):
        t = self.commander.add_task("Quarterly Revenue Audit")
        self.commander.update_task_progress(t["id"], "completed", 100, "Ledgers reconciled")
        debrief = self.commander.generate_offline_debrief()
        self.assertIsNotNone(debrief)
        self.assertIn("Welcome back, sir", debrief)
        self.assertIn("Quarterly Revenue Audit", debrief)

        # Subsequent check should return None since briefing was read
        second_debrief = self.commander.generate_offline_debrief()
        self.assertIsNone(second_debrief)

class TestOffgridSentinel(unittest.TestCase):

    def setUp(self):
        self.sentinel = OffgridSentinel()

    @patch("ctypes.windll.kernel32.SetThreadExecutionState")
    def test_away_mode_toggle(self, mock_set_state):
        mock_set_state.return_value = 1
        res = self.sentinel.enable_away_mode()
        self.assertTrue(res)
        self.assertTrue(self.sentinel.away_mode_active)

        self.sentinel.disable_away_mode()
        self.assertFalse(self.sentinel.away_mode_active)

    def test_cloud_drone_workflow_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with patch("config.BASE_DIR", tmp_path):
                self.sentinel.ensure_cloud_drone_workflow()
                wf_path = tmp_path / ".github" / "workflows" / "jarvis_offgrid_worker.yml"
                self.assertTrue(wf_path.exists())
                content = wf_path.read_text(encoding="utf-8")
                self.assertIn("J.A.R.V.I.S. Off-Grid Autonomous Cloud Worker", content)
                self.assertIn("offgrid_cloud_worker.py", content)

class TestTaskDirectivesViaLocalIntelligence(unittest.TestCase):

    def test_add_pending_task_directive(self):
        prompt = "Jarvis, add pending task: analyze competitor pricing models"
        handled, response = local_intelligence.evaluate_and_execute(prompt)
        self.assertTrue(handled)
        self.assertIn("Directive queued in persistent task ledger", response)
        self.assertIn("analyze competitor pricing models", response)
        self.assertIn("specialist agents", response)

    def test_show_pending_tasks_directive(self):
        prompt = "what are my pending tasks"
        handled, response = local_intelligence.evaluate_and_execute(prompt)
        self.assertTrue(handled)
        self.assertTrue(len(response) > 0)

    def test_offgrid_status_directive(self):
        prompt = "offgrid status"
        handled, response = local_intelligence.evaluate_and_execute(prompt)
        self.assertTrue(handled)
        self.assertIn("Off-Grid and Standby Autonomy is operational", response)

class TestOffgridCloudWorker(unittest.TestCase):

    def test_process_pending_tasks_in_cloud(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tasks_file = tmp_path / "pending_tasks.json"
            completed_dir = tmp_path / "completed_tasks"
            completed_dir.mkdir(parents=True, exist_ok=True)

            sample_data = {
                "synced_at": "2026-10-08 00:00:00",
                "tasks": [
                    {
                        "id": 101,
                        "title": "Cloud Off-Grid Market Analysis",
                        "description": "Analyze market opportunities in renewable energy",
                        "category": "marketing",
                        "status": "pending"
                    }
                ]
            }
            tasks_file.write_text(json.dumps(sample_data), encoding="utf-8")

            from tools import offgrid_cloud_worker
            with patch.object(offgrid_cloud_worker, "TASKS_JSON_PATH", tasks_file), \
                 patch.object(offgrid_cloud_worker, "COMPLETED_DIR", completed_dir), \
                 patch.object(offgrid_cloud_worker, "query_duckduckgo_free_ai", return_value="Market analysis synthesized."):
                offgrid_cloud_worker.process_pending_tasks()

            updated_data = json.loads(tasks_file.read_text(encoding="utf-8"))
            self.assertEqual(updated_data["tasks"][0]["status"], "completed")
            self.assertEqual(updated_data["tasks"][0]["execution_environment"], "offgrid_cloud")
            self.assertEqual(updated_data["tasks"][0]["progress_percent"], 100)
            self.assertTrue(any(completed_dir.glob("task_101_*.md")))

if __name__ == "__main__":
    unittest.main()
