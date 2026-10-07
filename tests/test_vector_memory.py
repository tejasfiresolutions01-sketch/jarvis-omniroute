"""
Unit tests for J.A.R.V.I.S. Semantic Vector Memory & Long-Term Neural Recall (RAG).
"""

import unittest
import tempfile
import json
from pathlib import Path
import numpy as np
from core.vector_memory import FastEmbeddingEngine, VectorMemoryStore
from core.local_intelligence import local_intelligence
from core.task_orchestrator import task_orchestrator

class TestFastEmbeddingEngine(unittest.TestCase):

    def setUp(self):
        self.engine = FastEmbeddingEngine(seed=42)

    def test_embed_shape_and_norm(self):
        vec = self.engine.embed("Tony Stark prefers Earl Grey tea in the afternoon.")
        self.assertEqual(vec.shape, (384,))
        self.assertEqual(vec.dtype, np.float32)
        norm = np.linalg.norm(vec)
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_embed_empty(self):
        vec_empty = self.engine.embed("")
        self.assertEqual(vec_empty.shape, (384,))
        self.assertEqual(float(np.linalg.norm(vec_empty)), 0.0)

        vec_spaces = self.engine.embed("   ")
        self.assertEqual(float(np.linalg.norm(vec_spaces)), 0.0)

    def test_semantic_similarity(self):
        v1 = self.engine.embed("Tony drinks hot Earl Grey tea with two sugars.")
        v2 = self.engine.embed("What hot tea beverage does Tony enjoy?")
        v_unrelated = self.engine.embed("Mark 85 armor flight stabilization quantum thruster.")

        sim_related = float(np.dot(v1, v2))
        sim_unrelated = float(np.dot(v1, v_unrelated))

        self.assertGreater(sim_related, sim_unrelated)
        self.assertGreater(sim_related, 0.12)


class TestVectorMemoryStore(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db_path = Path(self.temp_file.name)
        self.store = VectorMemoryStore(db_path=self.db_path)

    def tearDown(self):
        try:
            if self.db_path.exists():
                self.db_path.unlink()
        except Exception:
            pass

    def test_store_and_count(self):
        id1 = self.store.store_memory("Tony prefers Earl Grey tea with two sugars.", category="preference")
        id2 = self.store.store_memory("OmniRoute gateway is running on port 20128.", category="project")
        id3 = self.store.store_memory("Mark 85 thrusters calibration required.", category="note")

        self.assertGreater(id1, 0)
        self.assertGreater(id2, 0)
        self.assertGreater(id3, 0)
        self.assertEqual(self.store.count(), 3)
        self.assertEqual(self.store.count("preference"), 1)
        self.assertEqual(self.store.count("project"), 1)
        self.assertEqual(self.store.count("note"), 1)

    def test_semantic_search_and_ranking(self):
        self.store.store_memory("Tony prefers hot Earl Grey tea with two sugars.", category="preference")
        self.store.store_memory("OmniRoute server operates locally on port 20128.", category="project")
        self.store.store_memory("Mark 85 armor thrusters flight diagnostic scheduled.", category="note")

        results = self.store.semantic_search("what beverage does Tony drink?")
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertEqual(top["category"], "preference")
        self.assertIn("tea", top["content"].lower())

    def test_category_filtering(self):
        self.store.store_memory("Stark prefers coffee.", category="preference")
        self.store.store_memory("Coffee machine model espresso 500.", category="note")

        pref_results = self.store.semantic_search("coffee", category="preference")
        for r in pref_results:
            self.assertEqual(r["category"], "preference")

    def test_recall_context_formatting(self):
        self.store.store_memory("OmniRoute port is 20128.", category="project")
        ctx = self.store.recall_context("what is the port for OmniRoute?")
        self.assertIn("Relevant Long-Term Neural Memories", ctx)
        self.assertIn("20128", ctx)
        self.assertIn("PROJECT", ctx)

    def test_delete_memory(self):
        mem_id = self.store.store_memory("Temporary test memory item.", category="general")
        self.assertEqual(self.store.count(), 1)

        deleted = self.store.delete_memory(mem_id)
        self.assertTrue(deleted)
        self.assertEqual(self.store.count(), 0)

    def test_clear_memories(self):
        self.store.store_memory("Item 1", category="note")
        self.store.store_memory("Item 2", category="preference")
        self.assertEqual(self.store.count(), 2)

        cleared = self.store.clear_memories()
        self.assertEqual(cleared, 2)
        self.assertEqual(self.store.count(), 0)


class TestMemoryDirectivesAndIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db_path = Path(self.temp_file.name)
        self.store = VectorMemoryStore(db_path=self.db_path)

    def tearDown(self):
        try:
            if self.db_path.exists():
                self.db_path.unlink()
        except Exception:
            pass

    def test_parse_store_directives(self):
        act, cat, content = self.store.parse_memory_directive("remember that I prefer black coffee without sugar")
        self.assertEqual(act, "store")
        self.assertEqual(cat, "preference")
        self.assertIn("prefer black coffee", content)

        act, cat, content = self.store.parse_memory_directive("save note: verify Mark 85 thrusters before flight")
        self.assertEqual(act, "store")
        self.assertEqual(cat, "note")
        self.assertIn("verify Mark 85", content)

    def test_parse_recall_directives(self):
        act, query, _ = self.store.parse_memory_directive("what do you remember about my coffee preference")
        self.assertEqual(act, "recall")
        self.assertIn("coffee preference", query)

        act, query, _ = self.store.parse_memory_directive("recall my notes on Mark 85")
        self.assertEqual(act, "recall")
        self.assertIn("mark 85", query.lower())

    def test_local_intelligence_store_and_recall_flow(self):
        # 1. Clear any existing memories for clean test
        local_intelligence.evaluate_and_execute("clear memories")

        # 2. Store memory directive
        handled, resp = local_intelligence.evaluate_and_execute("remember that my flight suit access code is 4209")
        self.assertTrue(handled)
        self.assertIn("Memory committed to long-term neural recall", resp)

        # 3. Recall memory directive
        handled_recall, resp_recall = local_intelligence.evaluate_and_execute("what do you remember about flight suit access code")
        self.assertTrue(handled_recall)
        self.assertIn("4209", resp_recall)

        # 4. Clean up
        local_intelligence.evaluate_and_execute("clear memories")

    def test_task_orchestrator_memory_tools(self):
        tools = task_orchestrator.TOOLS
        self.assertIn("store_memory", tools)
        self.assertIn("recall_memory", tools)
        self.assertIn("search_memory", tools)

        # Execute store_memory tool
        res_store = tools["store_memory"](content="Mark 85 armor flight telemetry nominal", category="project")
        self.assertIn("Stored memory", res_store)

        # Execute recall_memory tool
        res_recall = tools["recall_memory"](query="Mark 85 armor flight telemetry")
        self.assertIn("Mark 85", res_recall)


if __name__ == "__main__":
    unittest.main()
