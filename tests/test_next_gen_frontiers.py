"""
Unit Tests for J.A.R.V.I.S. Next-Gen Upgrade Frontiers:
1. Frontier 1: Autonomous Agent Swarm & Hierarchical HiveMind Engine (core/hivemind_swarm.py)
2. Frontier 2: Polyglot Sandboxed Code Execution & Benchmark Matrix (tools/polyglot_runtime.py)
3. Frontier 3: Hybrid GraphRAG Local Knowledge Engine (core/graph_rag.py)
4. Frontier 4: OmniVision 2.0 Visual Grounding & Diffing (tools/omnivision.py)
5. Frontier 5: Stark Acoustic Core 2.0 Audio Ducking & Vocal Modulation (core/audio_ducking.py)
6. Frontier 6: Holographic Display 3.0 Acoustic Ribbon Mesh & Ray-Casting (ui/mesh_3d_engine.py, tools/gesture_controller.py)
"""

import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np

from core.hivemind_swarm import (
    HiveMindSwarm,
    PersonaRole,
    SwarmAgent,
    SwarmBlackboard,
    SwarmTask,
    TaskStatus,
)
from tools.polyglot_runtime import PolyglotRuntime, ExecutionResult
from core.graph_rag import GraphRAG, EntityNode, RelationEdge
from tools.omnivision import OmniVision, UIElement, ScreenDiffResult
from core.audio_ducking import AudioDuckingEngine, AffectiveTone, AffectiveVocalModulator
from ui.mesh_3d_engine import MeshLoader, Mesh3D
from tools.gesture_controller import SpatialGestureEngine


class TestHiveMindSwarm(unittest.TestCase):
    """Verifies Frontier 1 Swarm Orchestration and DAG planning."""

    def setUp(self):
        self.swarm = HiveMindSwarm()

    def test_spawn_default_agents(self):
        agents = self.swarm.blackboard.get_all_agents()
        self.assertEqual(len(agents), 5)
        roles = {a.role for a in agents}
        self.assertIn(PersonaRole.ARCHITECT, roles)
        self.assertIn(PersonaRole.ENGINEER, roles)
        self.assertIn(PersonaRole.QA, roles)
        self.assertIn(PersonaRole.SECURITY, roles)
        self.assertIn(PersonaRole.DEVOPS, roles)

    def test_blackboard_post_and_retrieve_artifact(self):
        art = self.swarm.blackboard.post_artifact(
            artifact_type="code",
            title="Algorithm Core",
            content="def run(): pass",
            author_role=PersonaRole.ENGINEER
        )
        retrieved = self.swarm.blackboard.get_artifact(art.artifact_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Algorithm Core")
        self.assertEqual(len(self.swarm.blackboard.get_artifacts_by_type("code")), 1)

    def test_peer_review_consensus(self):
        art = self.swarm.blackboard.post_artifact(
            artifact_type="plan",
            title="Deployment Spec",
            content="deploy to cluster",
            author_role=PersonaRole.ARCHITECT
        )
        approved = self.swarm.conduct_peer_review(art.artifact_id, required_approvals=2)
        self.assertTrue(approved)
        reviews = self.swarm.blackboard.get_reviews_for_artifact(art.artifact_id)
        self.assertGreaterEqual(len(reviews), 2)

    def test_execute_mission(self):
        res = self.swarm.execute_mission(
            mission_title="Build Real-Time Pipeline",
            mission_objective="Construct resilient streaming ingest"
        )
        self.assertTrue(res["success"])
        self.assertGreaterEqual(len(res["artifacts_produced"]), 3)
        self.assertEqual(res["tasks_executed"], 5)


class TestPolyglotRuntime(unittest.TestCase):
    """Verifies Frontier 2 Polyglot Sandboxed Code Execution."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_polyglot_"))
        self.runtime = PolyglotRuntime(scratch_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_python_execution_success(self):
        code = "val = 40 + 2\nprint(f'Computed: {val}')"
        res = self.runtime.execute(code, language="python")
        self.assertEqual(res.exit_code, 0)
        self.assertIn("Computed: 42", res.stdout)
        self.assertTrue(res.syntax_valid)
        self.assertFalse(res.timed_out)

    def test_python_syntax_error_prevalidation(self):
        bad_code = "def broken(\n  print('missing close')"
        res = self.runtime.execute(bad_code, language="python")
        self.assertNotEqual(res.exit_code, 0)
        self.assertFalse(res.syntax_valid)
        self.assertTrue("syntaxerror" in (res.error_message or "").lower())

    def test_benchmark_snippet(self):
        code = "s = sum(range(5000))\nprint(s)"
        bench = self.runtime.benchmark_snippet(code, language="python", iterations=3)
        self.assertEqual(bench["iterations"], 3)
        self.assertGreater(bench["mean_ms"], 0.0)
        self.assertIn("min_ms", bench)


class TestGraphRAG(unittest.TestCase):
    """Verifies Frontier 3 Hybrid GraphRAG Knowledge Engine."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_graph_rag_"))
        self.db_path = self.temp_dir / "test_graph.db"
        self.rag = GraphRAG(db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_upsert_and_retrieve_entity(self):
        self.rag.upsert_entity(
            name="QuantumCore",
            entity_type="subsystem",
            description="High-frequency coherence processing unit",
            properties={"version": "3.1"}
        )
        ent = self.rag.get_entity("QuantumCore")
        self.assertIsNotNone(ent)
        self.assertEqual(ent.name, "QuantumCore")
        self.assertEqual(ent.entity_type, "subsystem")
        self.assertEqual(ent.properties.get("version"), "3.1")

    def test_relational_edges_and_pathfinding(self):
        self.rag.upsert_entity("Alpha", "node", "Entry node")
        self.rag.upsert_entity("Beta", "node", "Middle bridge node")
        self.rag.upsert_entity("Gamma", "node", "Destination node")

        self.rag.add_relation("Alpha", "Beta", "routes_to")
        self.rag.add_relation("Beta", "Gamma", "connects_with")

        neighbors = self.rag.get_neighbors("Beta", direction="both")
        self.assertEqual(len(neighbors), 2)

        path = self.rag.find_path("Alpha", "Gamma", max_hops=3)
        self.assertIsNotNone(path)
        self.assertEqual(len(path), 2)
        self.assertEqual(path[0], ("Alpha", "routes_to", "Beta"))
        self.assertEqual(path[1], ("Beta", "connects_with", "Gamma"))

    def test_hybrid_search(self):
        self.rag.upsert_entity("AcousticRadar", "sensor", "3D acoustic FFT wave monitor")
        self.rag.upsert_entity("VisionCopilot", "sensor", "Screen visual perception unit")
        results = self.rag.hybrid_search("acoustic FFT", top_k=2)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].entity.name, "AcousticRadar")
        self.assertGreater(results[0].score, 0.0)


class TestOmniVision(unittest.TestCase):
    """Verifies Frontier 4 OmniVision 2.0 Visual Grounding & Diffing."""

    def setUp(self):
        self.omnivision = OmniVision()

    def test_screen_diff_computation(self):
        img_a = np.zeros((300, 400, 3), dtype=np.uint8)
        img_b = img_a.copy()
        # Draw modified rectangle
        img_b[50:120, 50:180] = (255, 255, 255)

        diff = self.omnivision.compute_screen_diff(img_a, img_b)
        self.assertTrue(diff.changed)
        self.assertGreater(diff.diff_percentage, 1.0)
        self.assertIsNotNone(diff.changed_bbox)
        bx, by, bw, bh = diff.changed_bbox
        self.assertEqual(bx, 50)
        self.assertEqual(by, 50)

    def test_detect_ui_elements(self):
        canvas = np.zeros((400, 600, 3), dtype=np.uint8)
        # Draw a simulated button (aspect ratio ~ 3.0)
        canvas[100:140, 150:270] = (200, 200, 200)
        elements = self.omnivision.detect_ui_elements(canvas)
        self.assertGreaterEqual(len(elements), 1)
        btn = next((e for e in elements if e.element_type == "button"), None)
        self.assertIsNotNone(btn)


class TestStarkAcousticCore(unittest.TestCase):
    """Verifies Frontier 5 Stark Acoustic Core 2.0."""

    def test_affective_vocal_modulator_presets(self):
        rate_alert, pitch_alert = AffectiveVocalModulator.get_voice_params(AffectiveTone.ALERT)
        self.assertEqual(rate_alert, "+16%")
        self.assertEqual(pitch_alert, "+6Hz")

        rate_calm, pitch_calm = AffectiveVocalModulator.get_voice_params(AffectiveTone.CALM)
        self.assertEqual(rate_calm, "-8%")
        self.assertEqual(pitch_calm, "-3Hz")

    def test_audio_ducking_engine_context(self):
        duck = AudioDuckingEngine(duck_factor=0.30)
        self.assertEqual(duck._duck_count, 0)
        with duck.ducked():
            self.assertEqual(duck._duck_count, 1)
            with duck.ducked():
                self.assertEqual(duck._duck_count, 2)
            self.assertEqual(duck._duck_count, 1)
        self.assertEqual(duck._duck_count, 0)


class TestHolographic3DUpgrades(unittest.TestCase):
    """Verifies Frontier 6 3D Acoustic Ribbon Mesh & Gesture Ray-Casting."""

    def test_acoustic_ribbon_mesh_generation(self):
        mesh = MeshLoader.get_procedural_mesh("acoustic_ribbon")
        self.assertEqual(mesh.name, "Acoustic FFT Ribbon Terrain")
        self.assertEqual(len(mesh.vertices), 192)  # 16 x 12
        self.assertGreater(len(mesh.edges), 300)
        self.assertGreater(len(mesh.highlight_nodes), 0)

    def test_gesture_ray_casting_and_grabbing(self):
        engine = SpatialGestureEngine()
        verts = np.array([
            [0.0, 0.0, 0.0],
            [25.0, 25.0, 0.0],
            [-25.0, -25.0, 0.0]
        ], dtype=np.float32)

        # Center pointing at (320, 240) in 640x480 frame -> ndc (0, 0)
        hit = engine.ray_cast_mesh(320, 240, 640, 480, verts)
        self.assertIsNotNone(hit)
        idx, dist = hit
        self.assertEqual(idx, 0)

        # Test node grab & release
        self.assertTrue(engine.grab_node(idx))
        self.assertEqual(engine.get_grabbed_node(), idx)
        released = engine.release_node()
        self.assertEqual(released, idx)
        self.assertIsNone(engine.get_grabbed_node())


if __name__ == "__main__":
    unittest.main()
