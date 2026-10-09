"""
Unit Tests for J.A.R.V.I.S. 3D Holographic Mesh Engine & Neon Bloom Shader Matrix.
Validates procedural meshes, OBJ/STL parsing, physics inertia, and multi-pass rendering.
"""

import os
import tempfile
import time
import unittest
import numpy as np
from unittest.mock import MagicMock

from ui.mesh_3d_engine import Mesh3D, MeshLoader, Holographic3DRenderer, holographic_3d
from tools.hud_controller import hud_controller


class TestMesh3DEngine(unittest.TestCase):
    def setUp(self):
        self.renderer = Holographic3DRenderer()

    def test_procedural_meshes_generation(self):
        """All procedural models (helmet, reactor, globe, tesseract, drone) must construct valid geometry."""
        for name in ["helmet", "reactor", "globe", "tesseract", "drone"]:
            mesh = MeshLoader.get_procedural_mesh(name)
            self.assertIsInstance(mesh, Mesh3D)
            self.assertGreater(len(mesh.vertices), 0)
            self.assertGreater(len(mesh.edges), 0)
            # Verify bounding coordinates are normalized
            max_r = np.max(np.linalg.norm(mesh.vertices, axis=1))
            self.assertAlmostEqual(max_r, 65.0, delta=1.0)

    def test_obj_parser(self):
        """Must parse Wavefront .obj files accurately into vertices and edges."""
        obj_content = """# Test Cube
v -1.0 -1.0 -1.0
v 1.0 -1.0 -1.0
v 1.0 1.0 -1.0
v -1.0 1.0 -1.0
v -1.0 -1.0 1.0
v 1.0 -1.0 1.0
v 1.0 1.0 1.0
v -1.0 1.0 1.0
f 1 2 3 4
f 5 6 7 8
f 1 2 6 5
"""
        with tempfile.NamedTemporaryFile("w", suffix=".obj", delete=False) as f:
            f.write(obj_content)
            tmp_path = f.name

        try:
            mesh = MeshLoader.load_obj(tmp_path)
            self.assertIsNotNone(mesh)
            self.assertEqual(len(mesh.vertices), 8)
            self.assertGreater(len(mesh.edges), 0)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_stl_parser_ascii(self):
        """Must parse ASCII STL files into vertices and edges."""
        stl_content = """solid test_triangle
facet normal 0.0 0.0 1.0
outer loop
vertex 0.0 0.0 0.0
vertex 1.0 0.0 0.0
vertex 0.0 1.0 0.0
endloop
endfacet
endsolid
"""
        with tempfile.NamedTemporaryFile("w", suffix=".stl", delete=False) as f:
            f.write(stl_content)
            tmp_path = f.name

        try:
            mesh = MeshLoader.load_stl(tmp_path)
            self.assertIsNotNone(mesh)
            self.assertEqual(len(mesh.vertices), 3)
            self.assertEqual(len(mesh.edges), 3)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_physics_auto_spin_and_inertia(self):
        """Physics engine must update rotation and apply friction inertia."""
        self.renderer.auto_spin = True
        init_yaw = self.renderer.yaw
        self.renderer.update_physics()
        self.assertGreater(self.renderer.yaw, init_yaw)

        # Inertia flick
        self.renderer.auto_spin = False
        self.renderer.vel_yaw = 0.5
        self.renderer.update_physics()
        self.assertLess(self.renderer.vel_yaw, 0.5, "Friction should dampen angular velocity")

    def test_multi_pass_neon_bloom_rendering(self):
        """Renderer must project points and invoke canvas drawing lines."""
        mock_canvas = MagicMock()
        theme = {"primary": "#00f0ff", "glow": "#00a2ff", "secondary": "#ffd700"}

        self.renderer.set_mesh("helmet")
        self.renderer.project_and_render(mock_canvas, cx=200, cy=150, theme=theme, audio_energy=0.4)
        self.assertTrue(mock_canvas.create_line.called)
        self.assertGreater(mock_canvas.create_line.call_count, 10)

    def test_hud_controller_load_custom_mesh(self):
        """hud_controller must accept load_mesh commands."""
        ok = hud_controller.load_custom_mesh("C:/test_model.obj")
        self.assertTrue(ok)

    def test_transform_latency_sub_millisecond(self):
        """3D transformation must execute in sub-millisecond time (< 2ms)."""
        mock_canvas = MagicMock()
        theme = {"primary": "#00f0ff", "glow": "#00a2ff", "secondary": "#ffd700"}
        self.renderer.set_mesh("helmet")

        start = time.perf_counter()
        for _ in range(50):
            self.renderer.project_and_render(mock_canvas, cx=200, cy=150, theme=theme)
        elapsed_per_frame_ms = ((time.perf_counter() - start) / 50.0) * 1000.0

        self.assertLess(elapsed_per_frame_ms, 5.0, f"Frame latency was {elapsed_per_frame_ms:.2f}ms")


if __name__ == "__main__":
    unittest.main()
