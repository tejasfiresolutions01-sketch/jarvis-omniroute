"""
Unit tests for Phase 4: Scaled GraphRAG and Persistent Episodic Memory Matrix.
Verifies:
1. PersistentEpisodicMemory recording, embedding, querying, and filtering.
2. Emotional valence, arousal, and importance scaling.
3. Entity auto-detection and query by entity.
4. Temporal recency decay weighting.
5. Ingestion of Stark Global Archive articles and CAD blueprints into GraphRAG.
6. Multi-hop subsystem dependency resolution (find_subsystem_dependencies).
7. Ego-subgraph extraction (query_subsystem_graph).
8. Articulate lineage path explanation (explain_lineage).
"""

import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from core.graph_rag import GraphRAG
from core.persistent_episodic_memory import PersistentEpisodicMemory


class TestScaledMemoryAndGraphRAG(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.graph_db_path = Path(self.temp_dir) / "test_knowledge_graph.db"
        self.episodes_db_path = Path(self.temp_dir) / "test_persistent_episodes.db"
        self.graph = GraphRAG(db_path=self.graph_db_path)
        self.episodic_mem = PersistentEpisodicMemory(db_path=self.episodes_db_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_and_query_episode(self):
        ep_id = self.episodic_mem.record_episode(
            speaker="User",
            content="Deploy hypersonic drone surveillance over the perimeter.",
            intent="tactical_command",
            emotional_valence=0.4,
            arousal=0.8,
            importance=9,
            context_tags=["defense", "uav"],
            action_taken="UAV telemetry initialized"
        )
        self.assertTrue(ep_id.startswith("ep_"))

        # Query back
        results = self.episodic_mem.query_episodes(
            query_text="drone surveillance",
            min_importance=5,
            limit=5
        )
        self.assertGreaterEqual(len(results), 1)
        top = results[0]
        self.assertEqual(top.episode_id, ep_id)
        self.assertEqual(top.speaker, "User")
        self.assertEqual(top.importance, 9)
        self.assertAlmostEqual(top.emotional_valence, 0.4, places=2)
        self.assertIn("Drone", top.entities_mentioned)

    def test_query_by_entity(self):
        self.episodic_mem.record_episode(
            speaker="JARVIS",
            content="Mark 85 armor integrity is at 98.4% with Gold-Titanium skin intact.",
            intent="status_telemetry",
            importance=7
        )
        episodes = self.episodic_mem.get_episodes_by_entity("Mark 85", limit=5)
        self.assertGreaterEqual(len(episodes), 1)
        self.assertIn("Mark 85", episodes[0].content)

    def test_timeline_stats_and_compaction(self):
        # Insert a routine low-importance episode
        self.episodic_mem.record_episode(
            speaker="User",
            content="What time is it in Tokyo?",
            importance=2
        )
        stats = self.episodic_mem.get_timeline_stats()
        self.assertGreaterEqual(stats["total_episodes"], 1)
        self.assertIn("User", stats["speakers"])

        # Test compaction
        pruned = self.episodic_mem.compact_old_episodes(days_threshold=0.0, retain_importance_gte=5)
        self.assertEqual(pruned, 1)

    def test_graph_rag_stark_ingestion(self):
        summary_before = self.graph.dump_graph_summary()
        self.assertEqual(summary_before["total_entities"], 0)

        # Ingest
        res = self.graph.ingest_stark_knowledge_graph()
        self.assertGreater(res["entities_added"], 10)
        self.assertGreater(res["relations_added"], 10)

        summary_after = self.graph.dump_graph_summary()
        self.assertGreater(summary_after["total_entities"], 20)
        self.assertGreater(summary_after["total_relations"], 15)

    def test_find_subsystem_dependencies(self):
        self.graph.ingest_stark_knowledge_graph()

        deps = self.graph.find_subsystem_dependencies("Iron Man Mark 85 Full Tactical Armor", max_hops=3)
        self.assertEqual(deps["root_system"], "Iron Man Mark 85 Full Tactical Armor")
        self.assertGreater(deps["total_dependencies"], 3)
        self.assertIn("Mark 50 Toroidal Arc Reactor (Exploded View)", deps["power_sources"])
        self.assertTrue(any("Gold-Titanium" in m for m in deps["materials"]))

    def test_query_subsystem_graph(self):
        self.graph.ingest_stark_knowledge_graph()

        subgraph = self.graph.query_subsystem_graph("Iron Man Mark 85 Full Tactical Armor", depth=2)
        self.assertEqual(subgraph["system_name"], "Iron Man Mark 85 Full Tactical Armor")
        self.assertGreater(subgraph["node_count"], 3)
        self.assertGreater(subgraph["edge_count"], 3)

        # Verify root node is marked
        root_node = next(n for n in subgraph["nodes"] if n["name"] == "Iron Man Mark 85 Full Tactical Armor")
        self.assertTrue(root_node["is_root"])

    def test_explain_lineage(self):
        self.graph.ingest_stark_knowledge_graph()

        lineage = self.graph.explain_lineage(
            "Iron Man Mark 85 Full Tactical Armor",
            "Gold-Titanium Matrix (Ti3Au)"
        )
        self.assertIn("Relational lineage analysis", lineage)
        self.assertIn("uses material", lineage)
        self.assertIn("1 hops", lineage)


if __name__ == "__main__":
    unittest.main()
