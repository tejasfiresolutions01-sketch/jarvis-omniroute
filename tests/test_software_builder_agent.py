"""
Unit tests for J.A.R.V.I.S. Autonomous Software Builder & Application Architect.
Validates multi-archetype scaffolding, agentic autonomous task loops,
surgical AST patching, project health audits, and local intelligence directives.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from core.local_intelligence import local_intelligence
from tools.software_builder_agent import SoftwareBuilderAgent, software_builder_agent


class TestSoftwareBuilderAgent(unittest.TestCase):

    def setUp(self):
        self.agent = software_builder_agent
        self.temp_dir = tempfile.mkdtemp(prefix="jarvis_builder_test_")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scaffold_python_cli(self):
        """Verifies end-to-end scaffolding of a Python CLI application."""
        app_dir = Path(self.temp_dir) / "test_cli"
        res = self.agent.scaffold_application("test_cli", app_type="python_cli", spec="Test CLI Spec", target_dir=str(app_dir))

        self.assertTrue(res["success"])
        self.assertEqual(res["app_name"], "test_cli")
        self.assertIn("main.py", res["files_created"])
        self.assertIn("app_core.py", res["files_created"])
        self.assertIn("test_app.py", res["files_created"])
        self.assertTrue((app_dir / "main.py").exists())
        self.assertTrue((app_dir / "app_core.py").exists())
        self.assertTrue((app_dir / "test_app.py").exists())

        # Verify project health
        v = res["verification"]
        self.assertTrue(v["tests_passed"])
        self.assertEqual(v["syntax_errors_count"], 0)
        self.assertGreaterEqual(v["health_score"], 80)

    def test_scaffold_python_api(self):
        """Verifies scaffolding of a Python REST API service."""
        app_dir = Path(self.temp_dir) / "test_api"
        res = self.agent.scaffold_application("test_api", app_type="python_api", spec="REST Endpoint Service", target_dir=str(app_dir))

        self.assertTrue(res["success"])
        self.assertIn("app.py", res["files_created"])
        self.assertIn("test_api.py", res["files_created"])
        self.assertTrue((app_dir / "app.py").exists())

    def test_scaffold_web_app(self):
        """Verifies scaffolding of a modern HTML/CSS/JS frontend application."""
        app_dir = Path(self.temp_dir) / "test_web"
        res = self.agent.scaffold_application("test_web", app_type="web_app", spec="Interactive web dashboard", target_dir=str(app_dir))

        self.assertTrue(res["success"])
        self.assertIn("index.html", res["files_created"])
        self.assertIn("style.css", res["files_created"])
        self.assertIn("app.js", res["files_created"])
        self.assertTrue((app_dir / "index.html").exists())
        self.assertTrue((app_dir / "style.css").exists())
        self.assertTrue((app_dir / "app.js").exists())

    def test_scaffold_python_gui(self):
        """Verifies scaffolding of a Desktop GUI application."""
        app_dir = Path(self.temp_dir) / "test_gui"
        res = self.agent.scaffold_application("test_gui", app_type="python_gui", spec="Desktop Utility", target_dir=str(app_dir))

        self.assertTrue(res["success"])
        self.assertIn("gui.py", res["files_created"])
        self.assertTrue((app_dir / "gui.py").exists())

    def test_autonomous_task_loop(self):
        """Verifies Claude Code/Codex-style autonomous agentic execution loop."""
        proj_dir = Path(self.temp_dir) / "task_tracker"
        res = self.agent.autonomous_task_loop(goal="Task tracker CLI utility", project_dir=str(proj_dir))

        self.assertTrue(res["success"])
        self.assertEqual(len(res["execution_plan"]), 4)
        self.assertTrue(res["tests_passed"])
        self.assertGreater(res["duration_seconds"], 0)
        self.assertIn("python", res["run_command"])

    def test_apply_patch_surgical(self):
        """Verifies surgical search and replace patching with AST validation."""
        test_file = Path(self.temp_dir) / "patch_demo.py"
        test_file.write_text("def compute():\n    return 10\n", encoding="utf-8")

        # 1. Valid patch
        res = self.agent.apply_patch(str(test_file), "return 10", "return 10 * 5")
        self.assertTrue(res["success"])
        self.assertIn("return 10 * 5", test_file.read_text(encoding="utf-8"))

        # 2. Syntax error patch rejected
        res_bad = self.agent.apply_patch(str(test_file), "return 10 * 5", "return (10 *")
        self.assertFalse(res_bad["success"])
        self.assertIn("syntax error", res_bad["error"].lower())

    def test_verify_project(self):
        """Verifies architectural audit and test status scoring."""
        app_dir = Path(self.temp_dir) / "audit_app"
        self.agent.scaffold_application("audit_app", app_type="python_cli", target_dir=str(app_dir))

        audit = self.agent.verify_project(str(app_dir))
        self.assertTrue(audit["success"])
        self.assertTrue(audit["tests_passed"])
        self.assertEqual(audit["syntax_errors_count"], 0)
        self.assertTrue(audit["ready_for_production"])

    def test_get_status(self):
        """Verifies builder agent status structure."""
        status = self.agent.get_status()
        self.assertIn("ONLINE", status["status"])
        self.assertIn("python_cli", status["supported_archetypes"])
        self.assertIn("web_app", status["supported_archetypes"])
        self.assertTrue(status["agentic_loop_active"])

    def test_local_intelligence_builder_directives(self):
        """Verifies voice/text directives in LocalIntelligence."""
        # 1. Status
        handled, msg = local_intelligence.evaluate_and_execute("software builder status")
        self.assertTrue(handled)
        self.assertIn("Software Builder online", msg)

        # 2. Scaffold application directive
        handled, msg = local_intelligence.evaluate_and_execute("create application note_tool type python_cli spec Quick note manager")
        self.assertTrue(handled)
        self.assertIn("Application 'note_tool' created", msg)

        # 3. Autonomous dev loop directive
        handled, msg = local_intelligence.evaluate_and_execute("autonomous build System diagnostic monitor")
        self.assertTrue(handled)
        self.assertIn("Autonomous task loop complete", msg)


if __name__ == "__main__":
    unittest.main()
