"""
Unit tests for J.A.R.V.I.S. 3-Dimensional Holographic Projector System.
Tests procedural optical models, perspective transformations, stereoscopic parallax,
monitor enumeration, IPC communication, and voice directives.
"""

import math
import os
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

from core.local_intelligence import local_intelligence
from core.projector_system import ProjectorSystem, projector_system
from tools.projector_controller import ProjectorController, projector_controller
from ui.projector_3d import Projector3DEngine, ProjectorMeshLibrary, projector_3d_engine


class TestProjectorSystem(unittest.TestCase):

    def setUp(self):
        self.system = projector_system
        self.engine = projector_3d_engine
        self.controller = projector_controller

    def test_mesh_library_models(self):
        """Validates all procedural 3D models have valid geometry and connectivity."""
        models = [
            "helmet", "reactor", "globe", "tesseract", "drone", "gauntlet", "emitter",
            "neural_mesh", "planetary_radar", "quantum_dna"
        ]
        for m in models:
            mesh = ProjectorMeshLibrary.get_mesh(m)
            self.assertIsNotNone(mesh, f"Failed to retrieve mesh for {m}")
            self.assertGreater(len(mesh.vertices), 0, f"No vertices for {m}")
            self.assertGreater(len(mesh.edges), 0, f"No edges for {m}")
            self.assertIsInstance(mesh.highlight_nodes, set)

    def test_keystone_bilinear_warp_correction(self):
        """Validates 4-corner bilinear keystone adjustment and interpolation math."""
        engine = Projector3DEngine()
        self.assertEqual(engine.keystone_corners["TL"], (0.0, 0.0))
        self.assertEqual(engine.keystone_corners["BR"], (1.0, 1.0))

        # Adjust TL corner inwards
        engine.set_keystone_corner("TL", 0.1, 0.1)
        self.assertEqual(engine.keystone_corners["TL"], (0.1, 0.1))

        # Cycle corner
        next_c = engine.cycle_keystone_corner()
        self.assertEqual(next_c, "TR")

        # Nudge corner
        engine.adjust_keystone_corner("TR", -0.05, 0.05)
        self.assertEqual(engine.keystone_corners["TR"], (0.95, 0.05))

        # Bilinear warp mapping
        x_pts = np.array([0.0, 500.0, 1000.0])
        y_pts = np.array([0.0, 400.0, 800.0])
        wx, wy = engine.apply_keystone(x_pts, y_pts, w=1000, h=800)
        self.assertEqual(len(wx), 3)
        self.assertEqual(len(wy), 3)
        # Check warped top-left
        self.assertAlmostEqual(wx[0], 100.0, delta=1.0)
        self.assertAlmostEqual(wy[0], 80.0, delta=1.0)

        # Reset keystone
        engine.reset_keystone()
        self.assertEqual(engine.keystone_corners["TL"], (0.0, 0.0))

    def test_spatial_continuous_orientation(self):
        """Validates 6-DoF continuous spatial orientation updates."""
        ok = self.system.update_spatial_orientation(delta_yaw=0.15, delta_pitch=-0.10)
        self.assertTrue(ok)
        st = self.system.get_state()
        self.assertFalse(st["auto_spin"])

    def test_state_management(self):
        """Verifies state retrieval and atomic updates."""
        state = self.system.get_state()
        self.assertIn("mode", state)
        self.assertIn("model", state)
        self.assertIn("timestamp", state)

        updated = self.system.update_state({"mode": "pyramid", "beam_lux": 95})
        self.assertEqual(updated["mode"], "pyramid")
        self.assertEqual(updated["beam_lux"], 95)

    def test_projection_modes(self):
        """Verifies switching between supported projection modes and rejection of invalid ones."""
        valid_modes = ["standard", "pyramid", "anaglyph", "floating"]
        for mode in valid_modes:
            res = self.system.set_projection_mode(mode)
            self.assertTrue(res)
            self.assertEqual(self.system.get_state()["mode"], mode)

        # Invalid mode rejected
        self.assertFalse(self.system.set_projection_mode("invalid_mode_xyz"))

    def test_model_selection(self):
        """Verifies selecting valid 3D models and rejection of invalid ones."""
        for m in ["helmet", "reactor", "gauntlet", "emitter", "tesseract"]:
            res = self.system.set_3d_model(m)
            self.assertTrue(res)
            self.assertEqual(self.system.get_state()["model"], m)

        self.assertFalse(self.system.set_3d_model("nonexistent_mesh"))

    def test_monitor_enumeration(self):
        """Verifies video display enumeration and structure."""
        monitors = self.system.enumerate_monitors()
        self.assertIsInstance(monitors, list)
        self.assertGreater(len(monitors), 0)
        first = monitors[0]
        self.assertIn("index", first)
        self.assertIn("width", first)
        self.assertIn("height", first)
        self.assertIn("is_primary", first)
        self.assertGreater(first["width"], 0)
        self.assertGreater(first["height"], 0)

    def test_parallax_depth_adjustment(self):
        """Verifies stereoscopic anaglyph parallax modification within safe bounds."""
        self.system.update_state({"parallax": 6.0})
        p1 = self.system.adjust_parallax(4.0)
        self.assertEqual(p1, 10.0)

        # Lower bound clamping
        p2 = self.system.adjust_parallax(-50.0)
        self.assertEqual(p2, 0.0)

        # Upper bound clamping
        p3 = self.system.adjust_parallax(100.0)
        self.assertEqual(p3, 25.0)

    def test_rotation_and_spin(self):
        """Verifies 3D model orientation manipulation and auto-spin controls."""
        self.system.rotate_model(delta_yaw=0.5, delta_pitch=0.2)
        st = self.system.get_state()
        self.assertFalse(st["auto_spin"])

        self.system.toggle_auto_spin(True)
        self.assertTrue(self.system.get_state()["auto_spin"])

        self.system.toggle_auto_spin(False)
        self.assertFalse(self.system.get_state()["auto_spin"])

    def test_vectorized_transforms(self):
        """Verifies 3D perspective projection mathematics on mesh vertices."""
        self.engine.set_mesh("gauntlet")
        px, py, depth = self.engine._transform_vertices(yaw=0.3, pitch=0.1, scale=1.0)
        self.assertEqual(len(px), len(self.engine.active_mesh.vertices))
        self.assertEqual(len(py), len(self.engine.active_mesh.vertices))
        self.assertTrue((depth > 0).all())

    def test_projector_controller_cli(self):
        """Verifies high-level controller methods and formatted responses."""
        res_mode = self.controller.set_mode("anaglyph")
        self.assertIn("ANAGLYPH", res_mode)

        res_model = self.controller.set_model("gauntlet")
        self.assertIn("GAUNTLET", res_model)

        status = self.controller.get_status()
        self.assertIn("mode", status)
        self.assertIn("model", status)
        self.assertIn("target_display", status)

    def test_local_intelligence_projector_directives(self):
        """Verifies natural language voice directives for 3D Projector System."""
        queries = [
            ("activate 3 dimensional projector", "3-Dimensional Holographic Projector System activated"),
            ("projector mode pyramid", "Projector switched to 4-Way Holographic Pyramid Mode"),
            ("projector mode anaglyph", "Projector switched to Stereoscopic Anaglyph 3D Mode"),
            ("projector mode floating", "Projector switched to Floating Desktop Hologram Mode"),
            ("project gauntlet", "Projecting 3D Mark-85 Repulsor Gauntlet"),
            ("project emitter", "Projecting 3D Conical Holo-Lens Emitter"),
            ("project drone", "Projecting 3D Stark Industries Hypersonic Drone"),
            ("increase projector depth", "Stereoscopic 3D parallax depth increased"),
            ("projector status", "Projector System Status"),
            ("deactivate 3d projector", "3-Dimensional Holographic Projector System deactivated"),
        ]

        for q, expected in queries:
            handled, res = local_intelligence.evaluate_and_execute(q)
            self.assertTrue(handled, f"Directive '{q}' failed to evaluate")
            self.assertIn(expected.lower(), res.lower(), f"Unexpected response for '{q}': {res}")


if __name__ == "__main__":
    unittest.main()
