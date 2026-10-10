"""
Unit tests for J.A.R.V.I.S. Coding AI Consensus, Full-Stack & DevOps Suite,
Media Studio, and Autonomous Device Controller.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from core.consensus_reviewer import MultiModelConsensusReviewer, consensus_reviewer
from core.local_intelligence import local_intelligence
from tools.autonomous_device_controller import AutonomousDeviceController, autonomous_device_controller
from tools.fullstack_devops_agent import FullstackDevOpsAgent, fullstack_devops_agent
from tools.media_studio_agent import MediaStudioAgent, media_studio_agent


class TestFullstackMediaDevice(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        try:
            shutil.rmtree(self.tmp_dir)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Multi-Model Consensus Reviewer (with Coding AI 5th Perspective)
    # ─────────────────────────────────────────────────────────────────────────
    def test_consensus_reviewer_five_perspectives(self):
        """Verifies consensus reviewer incorporates all 5 perspectives including Coding AI."""
        res = consensus_reviewer.review_upgrade_proposal("MAJOR-1")
        self.assertTrue(res["success"])
        evals = res["evaluations"]
        self.assertEqual(len(evals), 5)
        perspectives = [e["perspective"] for e in evals]
        self.assertIn("Architectural Sentinel", perspectives)
        self.assertIn("Security & Safety Sentinel", perspectives)
        self.assertIn("Performance & Speed Optimizer", perspectives)
        self.assertIn("Code Quality & Regression Inspector", perspectives)
        self.assertIn("Coding AI & Autonomous Software Architect", perspectives)
        self.assertGreaterEqual(res["consensus_score_pct"], 80.0)

    def test_consensus_reviewer_code_artifact(self):
        """Verifies multi-model code AST analysis and cyclomatic review."""
        sample_code = '''
def calculate_telemetry(pitch: float, roll: float) -> float:
    """Calculates composite vector orientation."""
    if pitch > 90.0:
        pitch = 90.0
    return pitch * 0.5 + roll * 0.5
'''
        res = consensus_reviewer.review_code_artifact(sample_code, context="stabilizer")
        self.assertTrue(res["success"])
        self.assertTrue(res["syntax_valid"])
        self.assertEqual(len(res["evaluations"]), 5)
        coding_eval = next(e for e in res["evaluations"] if e["perspective"] == "Coding AI & Autonomous Software Architect")
        self.assertEqual(coding_eval["verdict"], "APPROVE")
        self.assertIn("AST verified", coding_eval["analysis"])

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Full-Stack & DevOps Engineering Suite
    # ─────────────────────────────────────────────────────────────────────────
    def test_frontend_component_generation(self):
        """Tests Vanilla and React UI component synthesis."""
        res_v = fullstack_devops_agent.generate_frontend_component("FlightTelemetry", framework="vanilla")
        self.assertTrue(res_v["success"])
        self.assertEqual(res_v["framework"], "vanilla")
        self.assertTrue(Path(res_v["saved_path"]).exists())
        self.assertIn("export class FlightTelemetry", res_v["code"])

        res_r = fullstack_devops_agent.generate_frontend_component("ReactorCore", framework="react")
        self.assertTrue(res_r["success"])
        self.assertEqual(res_r["framework"], "react")
        self.assertTrue(Path(res_r["saved_path"]).exists())
        self.assertIn("export const ReactorCore", res_r["code"])

    def test_backend_service_generation(self):
        """Tests FastAPI and Flask microservice scaffolding."""
        res_fa = fullstack_devops_agent.generate_backend_service("ArmorTelemetry", framework="fastapi")
        self.assertTrue(res_fa["success"])
        self.assertEqual(res_fa["framework"], "fastapi")
        self.assertTrue(Path(res_fa["saved_path"]).exists())
        self.assertIn("FastAPI", res_fa["code"])

        res_fl = fullstack_devops_agent.generate_backend_service("DiagnosticsApi", framework="flask")
        self.assertTrue(res_fl["success"])
        self.assertEqual(res_fl["framework"], "flask")
        self.assertTrue(Path(res_fl["saved_path"]).exists())
        self.assertIn("Flask", res_fl["code"])

    def test_database_schema_generation(self):
        """Tests SQL DDL relational schema generation."""
        res = fullstack_devops_agent.generate_database_schema("SensorMetrics")
        self.assertTrue(res["success"])
        self.assertTrue(Path(res["saved_path"]).exists())
        self.assertIn("create table if not exists sensormetrics", res["sql_ddl"].lower())

    def test_devops_automation(self):
        """Tests Dockerfile, compose, CI, and Nginx generation."""
        # Dockerfile
        res_doc = fullstack_devops_agent.generate_dockerfile("test_microservice", app_type="python")
        self.assertTrue(res_doc["success"])
        self.assertTrue(Path(res_doc["saved_path"]).exists())
        self.assertIn("FROM python:", res_doc["dockerfile_content"])

        # Docker Compose
        res_cmp = fullstack_devops_agent.generate_docker_compose("stark_fleet")
        self.assertTrue(res_cmp["success"])
        self.assertTrue(Path(res_cmp["saved_path"]).exists())
        self.assertIn("services:", res_cmp["compose_yaml"])

        # GitHub Actions CI
        res_ci = fullstack_devops_agent.generate_github_actions_ci("autonomous_ci")
        self.assertTrue(res_ci["success"])
        self.assertTrue(Path(res_ci["saved_path"]).exists())
        self.assertIn("name: Autonomous CI Pipeline", res_ci["workflow_yaml"])

        # Nginx Config
        res_ng = fullstack_devops_agent.generate_nginx_config("jarvis.stark.local")
        self.assertTrue(res_ng["success"])
        self.assertTrue(Path(res_ng["saved_path"]).exists())
        self.assertIn("server_name jarvis.stark.local;", res_ng["nginx_conf"])

    def test_ai_powered_website_generation(self):
        """Tests end-to-end responsive website synthesis with embedded AI chat."""
        site_name = "nebula_portal"
        res = fullstack_devops_agent.generate_ai_powered_website(
            site_name=site_name,
            site_topic="Deep Space Exploration Dashboard",
            ai_persona="J.A.R.V.I.S. Navigator",
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["site_name"], site_name)
        site_dir = Path(res["directory"])
        self.assertTrue((site_dir / "index.html").exists())
        self.assertTrue((site_dir / "style.css").exists())
        self.assertTrue((site_dir / "app.js").exists())

        html_content = (site_dir / "index.html").read_text(encoding="utf-8")
        self.assertIn("ai-chat-window", html_content)
        self.assertIn("J.A.R.V.I.S. Navigator", html_content)

        js_content = (site_dir / "app.js").read_text(encoding="utf-8")
        self.assertIn("generateLocalAIReply", js_content)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Media Studio Agent (Photo & Video Processing)
    # ─────────────────────────────────────────────────────────────────────────
    def test_media_studio_blank_and_photo_actions(self):
        """Tests blank image creation, resizing, and optical filters."""
        # 1. Create blank canvas
        img_out = os.path.join(self.tmp_dir, "test_base.png")
        res_b = media_studio_agent.edit_photo("", action="blank", params={"width": 400, "height": 300}, output_path=img_out)
        self.assertTrue(res_b["success"])
        self.assertTrue(os.path.exists(img_out))

        # 2. Resize
        resized_out = os.path.join(self.tmp_dir, "test_resized.png")
        res_r = media_studio_agent.edit_photo(img_out, action="resize", params={"width": 200, "height": 150}, output_path=resized_out)
        self.assertTrue(res_r["success"])
        self.assertTrue(os.path.exists(resized_out))
        with Image.open(resized_out) as im:
            self.assertEqual(im.size, (200, 150))

        # 3. Filter (Grayscale)
        gray_out = os.path.join(self.tmp_dir, "test_gray.png")
        res_g = media_studio_agent.edit_photo(img_out, action="filter", params={"filter": "grayscale"}, output_path=gray_out)
        self.assertTrue(res_g["success"])
        self.assertTrue(os.path.exists(gray_out))

        # 4. Watermark
        wm_out = os.path.join(self.tmp_dir, "test_wm.png")
        res_w = media_studio_agent.edit_photo(img_out, action="watermark", params={"text": "J.A.R.V.I.S."}, output_path=wm_out)
        self.assertTrue(res_w["success"])
        self.assertTrue(os.path.exists(wm_out))

    def test_media_studio_ffmpeg_command_generation(self):
        """Tests deterministic ffmpeg pipeline command generation."""
        cmd_c = media_studio_agent.generate_ffmpeg_command("reactor_test.mp4", action="compress")
        self.assertIn("ffmpeg", cmd_c)
        self.assertIn("-crf 26", cmd_c)

        cmd_a = media_studio_agent.generate_ffmpeg_command("reactor_test.mp4", action="extract_audio")
        self.assertIn("-acodec mp3", cmd_a)

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Autonomous Device Controller
    # ─────────────────────────────────────────────────────────────────────────
    def test_device_controller_screen_state_and_vitals(self):
        """Tests resolution, vitals, and coordinate boundary clamping."""
        res_w, res_h = autonomous_device_controller.get_screen_resolution()
        self.assertGreater(res_w, 0)
        self.assertGreater(res_h, 0)

        # Coordinate clamping prevents off-screen PyAutoGUI errors
        cx, cy = autonomous_device_controller._clamp_coordinates(99999, -500)
        self.assertEqual(cx, res_w - 1)
        self.assertEqual(cy, 0)

        vitals = autonomous_device_controller.get_system_vitals()
        self.assertIn("cpu_percent", vitals)
        self.assertIn("ram_percent", vitals)
        self.assertIn("top_processes", vitals)

    def test_device_controller_screenshot(self):
        """Tests screenshot capture."""
        ss_path = os.path.join(self.tmp_dir, "unit_capture.png")
        res = autonomous_device_controller.capture_screen(output_path=ss_path)
        self.assertTrue(res["success"])
        self.assertTrue(os.path.exists(ss_path))
        with Image.open(ss_path) as im:
            self.assertGreater(im.width, 0)
            self.assertGreater(im.height, 0)

    def test_device_controller_typing_and_clipboard(self):
        """Tests type_text logic."""
        with patch("pyautogui.write") as mock_write, patch("pyautogui.hotkey") as mock_hotkey, \
             patch("pyperclip.copy") as mock_copy, patch("pyperclip.paste", return_value=""):
            # Short text: normal write
            res_short = autonomous_device_controller.type_text("hello", delay=0.01)
            self.assertTrue(res_short["success"])
            mock_write.assert_called_once_with("hello", interval=0.01)

            # Long text (> 50 chars): clipboard paste
            long_payload = "A" * 60
            res_long = autonomous_device_controller.type_text(long_payload)
            self.assertTrue(res_long["success"])
            mock_hotkey.assert_called_with("ctrl", "v")

    def test_autonomous_workflow_execution(self):
        """Tests sequential multi-action autonomous execution loop."""
        steps = [
            {"action": "wait", "seconds": 0.05},
            {"action": "wait", "seconds": 0.05},
        ]
        res = autonomous_device_controller.execute_autonomous_workflow(steps)
        self.assertTrue(res["success"])
        self.assertEqual(res["total_steps"], 2)
        self.assertEqual(res["completed_steps"], 2)

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Local Intelligence Directives Integration
    # ─────────────────────────────────────────────────────────────────────────
    def test_local_intelligence_fullstack_directives(self):
        """Tests local intelligence routing for fullstack commands."""
        # Status
        h1, res1 = local_intelligence.evaluate_and_execute("fullstack devops status")
        self.assertTrue(h1)
        self.assertIn("Fullstack & DevOps Suite online", res1)

        # Frontend component
        h2, res2 = local_intelligence.evaluate_and_execute("generate frontend component NavHeader as react")
        self.assertTrue(h2)
        self.assertIn("Frontend component 'NavHeader' (REACT) generated", res2)

        # AI website
        h3, res3 = local_intelligence.evaluate_and_execute("build ai website TitanStation about Solar Array with assistant Sol")
        self.assertTrue(h3)
        self.assertIn("AI-Powered Responsive Website 'titanstation' generated", res3)
        self.assertIn("Sol", res3)

    def test_local_intelligence_media_and_device_directives(self):
        """Tests local intelligence routing for media and device control."""
        # Media studio status
        h1, res1 = local_intelligence.evaluate_and_execute("media studio status")
        self.assertTrue(h1)
        self.assertIn("Media Studio online", res1)

        # Autonomous device status
        h2, res2 = local_intelligence.evaluate_and_execute("autonomous device status")
        self.assertTrue(h2)
        self.assertIn("Autonomous Device Controller online", res2)

        # Device vitals
        h3, res3 = local_intelligence.evaluate_and_execute("device vitals")
        self.assertTrue(h3)
        self.assertIn("Device Vitals:", res3)
        self.assertIn("CPU", res3)

        # Code consensus review
        h4, res4 = local_intelligence.evaluate_and_execute("consensus review code def test_fn(): pass")
        self.assertTrue(h4)
        self.assertIn("Multi-Model Consensus Audit", res4)
        self.assertIn("Coding AI & Autonomous Software Architect", res4)


if __name__ == "__main__":
    unittest.main()
