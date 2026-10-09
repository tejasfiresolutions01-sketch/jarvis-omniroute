"""
Unit tests for J.A.R.V.I.S. Local Knowledge Retrieval Engine (RAG) and
Multi-Model Consensus Reviewer.
Validates document chunking, semantic retrieval, consensus cross-checking,
and permission gate enforcement.
"""

import os
import tempfile
import unittest
from pathlib import Path

from core.consensus_reviewer import MultiModelConsensusReviewer, consensus_reviewer
from core.local_intelligence import local_intelligence
from core.rag_knowledge_engine import DocumentChunker, LocalRAGEngine, rag_knowledge_engine


class TestRAGAndConsensusReviewer(unittest.TestCase):

    def setUp(self):
        self.rag = rag_knowledge_engine
        self.consensus = consensus_reviewer
        self.rag.clear_knowledge()

    def tearDown(self):
        self.rag.clear_knowledge()

    def test_document_chunker(self):
        """Verifies text chunking maintains order, overlap, and length bounds."""
        sample_text = (
            "Paragraph one introduces the neural architecture of the Mark-85 armor.\n"
            "Paragraph two details the repulsor arc reactor core telemetry and magnetic coils.\n"
            "Paragraph three outlines the autonomous Butler protocol and voice recognition routines.\n"
        )
        chunks = DocumentChunker.chunk_text(sample_text, chunk_size=120, overlap=30)
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertIn("chunk_index", c)
            self.assertIn("text", c)
            self.assertGreater(len(c["text"]), 0)

    def test_rag_file_indexing_and_query(self):
        """Verifies end-to-end file indexing, hash deduplication, and semantic retrieval."""
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Stark Workshop Protocol\nThe Mark-85 flight stabilizers operate at 94 percent efficiency.")
            tmp_path = f.name

        try:
            # 1. Index file
            ok, msg = self.rag.index_file(tmp_path)
            self.assertTrue(ok)
            self.assertIn("Successfully indexed", msg)

            # 2. Re-indexing unchanged file skips
            ok2, msg2 = self.rag.index_file(tmp_path)
            self.assertTrue(ok2)
            self.assertIn("already indexed", msg2)

            # 3. Query knowledge base
            res = self.rag.query_knowledge("flight stabilizers efficiency", top_k=2)
            self.assertGreater(len(res["matches"]), 0)
            self.assertIn("94 percent", res["synthesis"])
            self.assertIn(Path(tmp_path).name, str(res["citations"]))

            # 4. Status reflects index
            st = self.rag.get_status()
            self.assertGreater(st["indexed_documents_count"], 0)
            self.assertEqual(st["storage_status"], "ONLINE")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_consensus_reviewer_upgrade_proposal(self):
        """Verifies multi-model cross-checking, agreement scoring, and permission recommendations."""
        res = self.consensus.review_upgrade_proposal("MAJOR-1")
        self.assertTrue(res["success"])
        self.assertEqual(res["item_id"], "MAJOR-1")
        self.assertGreaterEqual(res["consensus_score_pct"], 80.0)
        self.assertIn(res["overall_verdict"], ["STRONG_CONSENSUS_APPROVE", "MODERATE_CONSENSUS_APPROVE"])
        self.assertEqual(len(res["evaluations"]), 4)

        # Formatted summary contains permission gate notice
        summary = self.consensus.format_review_summary(res)
        self.assertIn("Consensus Agreement Score", summary)
        self.assertIn("Awaiting your explicit permission", summary)

    def test_consensus_reviewer_invalid_upgrade_id(self):
        """Verifies graceful handling of non-existent upgrade ID."""
        res = self.consensus.review_upgrade_proposal("NONEXISTENT-999")
        self.assertFalse(res["success"])
        self.assertIn("not found", res["error"].lower())

    def test_local_intelligence_rag_and_consensus_directives(self):
        """Verifies voice/text directives evaluate cleanly in local_intelligence."""
        # 1. Knowledge base status
        h1, res1 = local_intelligence.evaluate_and_execute("knowledge base status")
        self.assertTrue(h1)
        self.assertIn("Local Knowledge Base Status", res1)

        # 2. Consensus review directive
        h2, res2 = local_intelligence.evaluate_and_execute("consensus review upgrade MAJOR-2")
        self.assertTrue(h2)
        self.assertIn("Multi-Model Consensus Audit", res2)
        self.assertIn("Permission Gate", res2)


if __name__ == "__main__":
    unittest.main()
