"""
Unit Tests for J.A.R.V.I.S. MateoTechLab Holographic Display & Projector HUD.
Tests:
- 3D Wireframe Perspective Engine & Model Math (Helmet, Arc Reactor, Globe, Tesseract)
- Interactive Mouse Drag Rotation, Pitch, Yaw & Zoom
- Borderless Fullscreen Projector Mode (F11 toggle)
- HUD Controller IPC command queue, state broadcasting & synchronization
- Local Intelligence voice and directive intents for HUD control
"""

import unittest
import math
import time
import json
from unittest.mock import MagicMock, patch
from pathlib import Path
import config
from tools.hud_controller import hud_controller, HUDController
from core.local_intelligence import local_intelligence


class TestHolographicDisplayMathAndModels(unittest.TestCase):
    """Tests 3D wireframe perspective projection and vector geometric models."""

    def setUp(self):
        # Create a lightweight stub for TacticalHUD projection
        from ui.hud import TacticalHUD
        # We can test the math methods without launching Tk mainloop
        self.hud_class = TacticalHUD

    def test_project_3d_center(self):
        """Verifies 3D point (0, 0, 0) projects directly to canvas center (cx, cy)."""
        # Create a mock TacticalHUD with default angles
        hud = MagicMock()
        hud.model_scale = 1.0
        hud.model_yaw = 0.0
        hud.model_pitch = 0.0
        
        # Call the actual _project_3d function
        px, py, depth = self.hud_class._project_3d(hud, 0, 0, 0, cx=280, cy=140, fov=240, dist=260)
        self.assertEqual(px, 280)
        self.assertEqual(py, 140)
        self.assertAlmostEqual(depth, 260, delta=1.0)

    def test_project_3d_perspective_scaling(self):
        """Verifies points closer on Z axis (larger scale) project further from center."""
        hud = MagicMock()
        hud.model_scale = 1.0
        hud.model_yaw = 0.0
        hud.model_pitch = 0.0

        # Point with z=-50 (depth = 260 - 50 = 210, closer to camera) vs z=50 (depth = 260 + 50 = 310, further)
        px_close, py_close, d_close = self.hud_class._project_3d(hud, 50, 0, -50, cx=280, cy=140, fov=240, dist=260)
        px_far, py_far, d_far = self.hud_class._project_3d(hud, 50, 0, 50, cx=280, cy=140, fov=240, dist=260)

        self.assertLess(d_close, d_far)
        # Closer point has larger displacement from center px=280
        self.assertGreater(px_close - 280, px_far - 280)

    def test_project_3d_yaw_rotation(self):
        """Verifies 90-degree yaw (pi/2) rotates X axis onto Z axis."""
        hud = MagicMock()
        hud.model_scale = 1.0
        hud.model_yaw = math.pi / 2  # 90 degrees yaw
        hud.model_pitch = 0.0

        # Point on positive X axis (100, 0, 0) rotated by 90 deg yaw should have x1=0, z1=-100
        px, py, depth = self.hud_class._project_3d(hud, 100, 0, 0, cx=280, cy=140, fov=240, dist=260)
        self.assertAlmostEqual(px, 280, delta=1.0)
        self.assertAlmostEqual(depth, 260 - 100, delta=1.0)

    def test_wireframe_models_generation(self):
        """Verifies all 4 holographic models (helmet, reactor, globe, tesseract) generate valid nodes and edges."""
        canvas_mock = MagicMock()
        theme_stub = {"primary": "#00f0ff", "secondary": "#ffd700"}

        hud = MagicMock()
        hud.model_scale = 1.0
        hud.model_yaw = 0.2
        hud.model_pitch = 0.1
        hud._project_3d = lambda x, y, z, cx, cy: self.hud_class._project_3d(hud, x, y, z, cx, cy)

        for model_name in ["helmet", "reactor", "globe", "tesseract", "drone", "neural_mesh", "planetary_radar", "quantum_dna"]:
            hud.active_3d_model = model_name
            canvas_mock.reset_mock()
            self.hud_class._draw_3d_wireframe(hud, canvas_mock, cx=280, cy=140, t_style=theme_stub)
            # Must draw lines and oval nodes
            self.assertGreater(canvas_mock.create_line.call_count, 10, f"Model {model_name} drew too few edges")
            self.assertGreater(canvas_mock.create_oval.call_count, 4, f"Model {model_name} drew too few nodes")


class TestHolographicInteractiveControls(unittest.TestCase):
    """Tests mouse drag rotation, zoom, and fullscreen projector mode."""

    def setUp(self):
        from ui.hud import TacticalHUD
        self.hud_class = TacticalHUD

    def test_mouse_drag_rotation_updates_angles(self):
        """Simulates mouse drag and verifies model_yaw and model_pitch are updated and auto_spin paused."""
        hud = MagicMock()
        hud.model_yaw = 0.0
        hud.model_pitch = 0.2
        hud.auto_spin = True
        hud._drag_start_x = 0
        hud._drag_start_y = 0

        # Mouse press at (100, 100)
        press_event = MagicMock()
        press_event.x = 100
        press_event.y = 100
        self.hud_class._on_3d_drag_start(hud, press_event)

        self.assertEqual(hud._drag_start_x, 100)
        self.assertEqual(hud._drag_start_y, 100)
        self.assertFalse(hud.auto_spin, "Auto-spin should be paused on user interaction")

        # Mouse drag to (150, 120)
        motion_event = MagicMock()
        motion_event.x = 150
        motion_event.y = 120
        self.hud_class._on_3d_drag_motion(hud, motion_event)

        # dx = 50, dy = 20 -> yaw += 50 * 0.015 = 0.75, pitch += 20 * 0.015 = 0.3
        self.assertAlmostEqual(hud.model_yaw, 0.75, places=3)
        self.assertAlmostEqual(hud.model_pitch, 0.50, places=3)
        self.assertEqual(hud._drag_start_x, 150)
        self.assertEqual(hud._drag_start_y, 120)

    def test_mouse_scroll_zoom(self):
        """Verifies mouse wheel zoom in and zoom out adjusts scale within bounds."""
        hud = MagicMock()
        hud.model_scale = 1.0

        # Zoom in
        zoom_in_event = MagicMock()
        zoom_in_event.delta = 120
        self.hud_class._on_3d_zoom(hud, zoom_in_event)
        self.assertAlmostEqual(hud.model_scale, 1.1, places=3)

        # Zoom out
        zoom_out_event = MagicMock()
        zoom_out_event.delta = -120
        self.hud_class._on_3d_zoom(hud, zoom_out_event)
        self.assertAlmostEqual(hud.model_scale, 1.1 * 0.9, places=3)

    def test_fullscreen_projector_toggle(self):
        """Verifies toggle_fullscreen_mode switches between windowed and borderless fullscreen."""
        hud = MagicMock()
        hud.is_fullscreen = False
        hud.root = MagicMock()
        hud.btn_fullscreen = MagicMock()
        hud.append_log = MagicMock()
        hud._play_fx = MagicMock()

        # 1. Toggle ON
        self.hud_class.toggle_fullscreen_mode(hud)
        self.assertTrue(hud.is_fullscreen)
        hud.root.attributes.assert_called_with("-fullscreen", True)
        hud.btn_fullscreen.config.assert_called_with(text="⛶ EXIT FULLSCREEN")

        # 2. Toggle OFF
        self.hud_class.toggle_fullscreen_mode(hud)
        self.assertFalse(hud.is_fullscreen)
        hud.root.attributes.assert_called_with("-fullscreen", False)
        hud.btn_fullscreen.config.assert_called_with(text="⛶ PROJECTOR MODE")


class TestHUDControllerIPC(unittest.TestCase):
    """Tests the IPC command bridge and status queries."""

    def setUp(self):
        import tempfile
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_ipc = Path(self.tmp_dir.name) / "test_ipc.json"
        self.tmp_ipc.write_text("[]", encoding="utf-8")
        self.patcher = patch("tools.hud_controller.IPC_FILE", self.tmp_ipc)
        self.patcher.start()
        self.controller = HUDController()

    def tearDown(self):
        self.patcher.stop()
        self.tmp_dir.cleanup()

    def test_send_and_poll_commands(self):
        """Verifies commands queued via send_command are retrieved and cleared by poll_pending_commands."""
        self.controller.send_command("set_model", model="reactor")
        self.controller.send_command("toggle_fullscreen", state=True)

        cmds = self.controller.poll_pending_commands()
        self.assertGreaterEqual(len(cmds), 2)
        actions = [c.get("action") for c in cmds]
        self.assertIn("set_model", actions)
        self.assertIn("toggle_fullscreen", actions)

        # Second poll should be empty
        subsequent = self.controller.poll_pending_commands()
        self.assertEqual(len(subsequent), 0)

    def test_direct_in_memory_execution(self):
        """Verifies commands execute immediately on registered HUD instance."""
        mock_hud = MagicMock()
        mock_hud.is_fullscreen = False
        mock_hud.active_3d_model = "helmet"
        mock_hud.model_yaw = 0.0
        mock_hud.model_pitch = 0.2
        mock_hud.auto_spin = True

        self.controller.register_hud_instance(mock_hud)

        # Test set model
        self.controller._execute_direct_command({"action": "set_model", "model": "globe"})
        mock_hud.set_3d_model.assert_called_with("globe")

        # Test toggle fullscreen
        self.controller._execute_direct_command({"action": "toggle_fullscreen"})
        mock_hud.toggle_fullscreen_mode.assert_called_once()

        # Test rotate
        self.controller._execute_direct_command({"action": "rotate", "delta_yaw": 0.5, "delta_pitch": 0.1})
        self.assertAlmostEqual(mock_hud.model_yaw, 0.5)
        self.assertAlmostEqual(mock_hud.model_pitch, 0.3)
        self.assertFalse(mock_hud.auto_spin)

        # Test reset view
        self.controller._execute_direct_command({"action": "reset_view"})
        self.assertEqual(mock_hud.model_yaw, 0.0)
        self.assertEqual(mock_hud.model_pitch, 0.2)
        self.assertTrue(mock_hud.auto_spin)

        self.controller.unregister_hud_instance()


class TestLocalIntelligenceHologramIntents(unittest.TestCase):
    """Tests voice and text directive recognition in local_intelligence for HUD controls."""

    def test_projector_mode_intent(self):
        """Verifies 'projector mode' and 'fullscreen projector' directives."""
        handled, resp = local_intelligence.evaluate_and_execute("projector mode")
        self.assertTrue(handled)
        self.assertIn("projector", resp.lower())

        handled, resp = local_intelligence.evaluate_and_execute("exit projector mode")
        self.assertTrue(handled)
        self.assertIn("windowed mode", resp.lower())

    def test_switch_3d_model_intents(self):
        """Verifies model switching directives (helmet, reactor, globe, tesseract)."""
        handled, resp = local_intelligence.evaluate_and_execute("show 3d helmet")
        self.assertTrue(handled)
        self.assertIn("Helmet", resp)

        handled, resp = local_intelligence.evaluate_and_execute("switch to arc reactor")
        self.assertTrue(handled)
        self.assertIn("Arc Reactor", resp)

        handled, resp = local_intelligence.evaluate_and_execute("show 3d globe")
        self.assertTrue(handled)
        self.assertIn("Globe", resp)

        handled, resp = local_intelligence.evaluate_and_execute("show tesseract")
        self.assertTrue(handled)
        self.assertIn("Tesseract", resp)

    def test_rotate_and_view_manipulation_intents(self):
        """Verifies rotate, stop spinning, and reset 3D view directives."""
        handled, resp = local_intelligence.evaluate_and_execute("rotate helmet")
        self.assertTrue(handled)
        self.assertIn("rotated", resp.lower())

        handled, resp = local_intelligence.evaluate_and_execute("stop spinning")
        self.assertTrue(handled)
        self.assertIn("frozen", resp.lower())

        handled, resp = local_intelligence.evaluate_and_execute("reset 3d view")
        self.assertTrue(handled)
        self.assertIn("reset", resp.lower())

    def test_cycle_hud_theme_intent(self):
        """Verifies 'cycle hud theme' directive."""
        handled, resp = local_intelligence.evaluate_and_execute("cycle hud theme")
        self.assertTrue(handled)
        self.assertIn("palette", resp.lower())


if __name__ == "__main__":
    unittest.main()
