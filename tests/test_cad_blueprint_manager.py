"""
Unit Tests for J.A.R.V.I.S. Holographic 3D CAD Blueprint & Engineering Asset Matrix.
Verifies:
1. Procedural 3D OBJ file synthesis and cad_catalog.json caching.
2. Metadata inspection: mass, alloys, power requirements, and vertex/face counts.
3. Live conversion of CAD OBJ models into normalized Mesh3D wireframe objects.
4. Engineering bill of materials (BOM) and structural dossier generation.
5. Integration with ProjectorMeshLibrary and ProjectorSystem.
"""

import unittest
from pathlib import Path

from core.cad_blueprint_manager import cad_blueprint_manager, CADBlueprint
from ui.mesh_3d_engine import Mesh3D, MeshLoader
from ui.projector_3d import ProjectorMeshLibrary
from core.projector_system import projector_system


class TestCADBlueprintManager(unittest.TestCase):
    """Verifies Phase 3 of the 300 GB Stark Advancement Matrix."""

    def setUp(self):
        self.manager = cad_blueprint_manager

    def test_catalog_blueprints_populated(self):
        """Must catalog all 5 foundational Stark engineering assets."""
        bps = self.manager.list_blueprints()
        self.assertGreaterEqual(len(bps), 5)
        ids = {b.blueprint_id for b in bps}
        self.assertIn("mark85_armor_full", ids)
        self.assertIn("arc_reactor_exploded", ids)
        self.assertIn("stark_hypersonic_drone", ids)
        self.assertIn("repulsor_gauntlet_hd", ids)
        self.assertIn("dume_robotic_arm", ids)

    def test_blueprint_metadata_and_specifications(self):
        """Validates technical specifications for Mark 85 armor."""
        bp = self.manager.get_blueprint("mark85_armor_full")
        self.assertIsNotNone(bp)
        self.assertEqual(bp.category, "armor_suit")
        self.assertGreater(bp.vertex_count, 30)
        self.assertGreater(bp.face_count, 10)
        self.assertGreater(bp.mass_kg, 50.0)
        self.assertGreater(len(bp.materials), 0)

    def test_mesh3d_wireframe_conversion(self):
        """Converts OBJ blueprint to normalized Mesh3D wireframe."""
        mesh = self.manager.load_wireframe_mesh("mark85_armor_full")
        self.assertIsInstance(mesh, Mesh3D)
        self.assertGreater(len(mesh.vertices), 30)
        self.assertGreater(len(mesh.edges), 40)
        # Verify normalized radius is ~65.0
        import numpy as np
        max_rad = float(np.max(np.linalg.norm(mesh.vertices, axis=1)))
        self.assertAlmostEqual(max_rad, 65.0, delta=1.5)

    def test_engineering_dossier_generation(self):
        """Generates comprehensive structural dossier and bill of materials."""
        dossier = self.manager.generate_engineering_dossier("arc_reactor_exploded")
        self.assertIn("designation", dossier)
        self.assertIn("structural_specifications", dossier)
        self.assertIn("energetics_and_power", dossier)
        specs = dossier["structural_specifications"]
        self.assertIn("dry_mass_kg", specs)
        self.assertIn("primary_alloys", specs)

    def test_projector_mesh_library_integration(self):
        """ProjectorMeshLibrary must dynamically load CAD blueprints."""
        mesh = ProjectorMeshLibrary.get_mesh("mark85_armor_full")
        self.assertIsNotNone(mesh)
        self.assertEqual(mesh.name, "Iron Man Mark 85 Full Tactical Armor")
        self.assertIn("mark85_armor_full", projector_system.SUPPORTED_MODELS)


if __name__ == "__main__":
    unittest.main()
