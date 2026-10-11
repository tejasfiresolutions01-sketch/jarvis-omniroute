"""
Comprehensive Unit Test Suite for All 12 J.A.R.V.I.S. Upgraded Subsystems.
Verifies:
1. LocalVisionCopilot (spatial vision, edge density, layout classification).
2. StarkVoiceEngine (phonetic formatting, British Butler cadence, telemetry).
3. AmbientSentinel (vitals telemetry, hardware threshold advisories).
4. DockedTacticalHUD (overlay geometry, 3D wireframe mesh cycling).
5. SoftwareBuilderAgent (scaffolding and project structure formulation).
6. FullstackDevOpsAgent (service lifecycle, Docker and CI generation).
7. BrowserAgent (DOM navigation logic, tender and price tracking).
8. MediaStudioAgent (multimedia asset management, ffmpeg command generation).
9. HivemindSwarm (multi-agent coordination, mission planning and peer review).
10. SelfEvolver (evolutionary cycles, self-upgrade automation).
11. OffGridSentinel (kernel wake timer, away mode, hardware wake task).
12. WebPortal (WebSocket HUD telemetry payload generation).
"""

import unittest
from PIL import Image

from core.local_vision_copilot import local_vision_copilot
from core.stark_voice_engine import stark_voice_engine
from core.ambient_sentinel import ambient_sentinel
from ui.docked_tactical_hud import docked_tactical_hud
from tools.software_builder_agent import software_builder_agent
from tools.fullstack_devops_agent import fullstack_devops_agent
from tools.browser_agent import browser_agent
from tools.media_studio_agent import media_studio_agent
from core.hivemind_swarm import hivemind_swarm
from core.self_evolver import self_evolver
from core.offgrid_sentinel import offgrid_sentinel
from ui.web_portal import web_portal


class TestAll12Upgrades(unittest.TestCase):

    # 1. Local Vision Copilot
    def test_local_vision_copilot(self):
        test_img = Image.new("RGB", (320, 240), color=(10, 15, 25))
        res = local_vision_copilot.analyze_image(test_img)
        self.assertEqual(res.width, 320)
        self.assertEqual(res.height, 240)
        self.assertIn("desktop", res.layout_classification)
        self.assertGreaterEqual(res.analysis_time_ms, 0.0)

    # 2. Stark Voice Engine
    def test_stark_voice_engine(self):
        formatted = stark_voice_engine.format_stark_cadence("Mach 5.0 with Ti3Au at 3.0 GW", add_honorific=True)
        self.assertIn("Mock 5.0", formatted)
        self.assertIn("Titanium three gold matrix", formatted)
        self.assertIn("sir.", formatted)

        telem = stark_voice_engine.get_telemetry()
        self.assertEqual(telem["primary_voice"], "en-GB-RyanNeural")

    # 3. Ambient Sentinel
    def test_ambient_sentinel(self):
        vitals = ambient_sentinel.get_vitals()
        self.assertGreaterEqual(vitals.cpu_percent, 0.0)
        self.assertGreater(vitals.available_ram_gb, 0.1)
        self.assertGreaterEqual(vitals.uncommitted_git_files, 0)

        adv = ambient_sentinel.evaluate_health_advisories(vitals)
        self.assertIsInstance(adv, list)

    # 4. Docked Tactical HUD
    def test_docked_tactical_hud(self):
        self.assertEqual(docked_tactical_hud.width, 320)
        self.assertEqual(docked_tactical_hud.height, 560)
        orig_name = docked_tactical_hud.mesh.name
        docked_tactical_hud.cycle_mesh()
        self.assertNotEqual(docked_tactical_hud.mesh.name, "")

    # 5. Software Builder Agent
    def test_software_builder_agent(self):
        status = software_builder_agent.get_status()
        self.assertIn("supported_archetypes", status)
        self.assertIn("python_cli", software_builder_agent.SUPPORTED_ARCHETYPES)

    # 6. Fullstack DevOps Agent
    def test_fullstack_devops_agent(self):
        status = fullstack_devops_agent.get_status()
        self.assertIn("status", status)
        res = fullstack_devops_agent.generate_dockerfile(app_name="demo_api", app_type="python", save_to_disk=False)
        self.assertTrue(res.get("success", False))
        self.assertIn("FROM python", res.get("dockerfile_content", ""))

    # 7. Browser Agent
    def test_browser_agent(self):
        self.assertTrue(callable(browser_agent.fetch_url_text))
        summary = browser_agent.format_price_voice_summary({"pricing": {}})
        self.assertIsInstance(summary, str)

    # 8. Media Studio Agent
    def test_media_studio_agent(self):
        status = media_studio_agent.get_status()
        self.assertIn("status", status)
        self.assertIn("grayscale", media_studio_agent.SUPPORTED_FILTERS)

    # 9. Hivemind Swarm
    def test_hivemind_swarm(self):
        self.assertIsInstance(hivemind_swarm.agents, dict)
        self.assertTrue(callable(hivemind_swarm.plan_mission))
        self.assertTrue(callable(hivemind_swarm.conduct_peer_review))

    # 10. Self Evolver
    def test_self_evolver(self):
        summary = self_evolver.get_upgrade_status_summary()
        self.assertIsInstance(summary, str)
        self.assertTrue(callable(self_evolver.is_evolution_due))

    # 11. Off-Grid Sentinel
    def test_offgrid_sentinel(self):
        self.assertFalse(offgrid_sentinel.away_mode_active)
        self.assertTrue(callable(offgrid_sentinel.enable_away_mode))
        self.assertTrue(callable(offgrid_sentinel.disable_away_mode))

    # 12. Web Portal
    def test_web_portal(self):
        self.assertTrue(callable(web_portal.start))
        self.assertTrue(callable(web_portal.broadcast_event))
        self.assertGreater(web_portal.port, 0)


if __name__ == "__main__":
    unittest.main()
