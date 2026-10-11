"""
Unit Tests for J.A.R.V.I.S. Stark Global Archive & Offline STEM Encyclopedic Engine.
Verifies:
1. SQLite FTS5 table initialization and full-text search indexing.
2. BM25 ranked lexical retrieval across metallurgy, aerospace, and physics.
3. Category-filtered search and exact title lookup.
4. JSONL streaming ingestion pipeline.
5. Two-tier neural SLM integration with Stark Global Archive.
"""

import json
import tempfile
import unittest
from pathlib import Path

from core.stark_archive import StarkArchiveEngine, ArchiveArticle, ArchiveSearchResult
from core.local_neural_slm import local_neural_slm


class TestStarkArchive(unittest.TestCase):
    """Verifies Phase 2 of the 300 GB Stark Advancement Matrix."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_stark_archive_"))
        self.db_path = self.temp_dir / "test_archive.db"
        self.engine = StarkArchiveEngine(db_path=self.db_path)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_database_initialization_and_seeding(self):
        """Engine must automatically create FTS5 tables and seed foundational articles."""
        stats = self.engine.get_stats()
        self.assertGreaterEqual(stats["total_articles"], 10)
        self.assertIn("materials_metallurgy", stats["categories"])
        self.assertIn("physics_aerospace", stats["categories"])
        self.assertIn("chemistry_elements", stats["categories"])
        self.assertGreater(stats["db_size_mb"], 0.0)

    def test_add_and_get_article(self):
        """Adds custom engineering article and retrieves by exact title."""
        art = self.engine.add_article(
            category="quantum_computing",
            title="Superconducting Qubit Matrix",
            summary="Transmon qubit architecture with microwave flux bias control.",
            content="Josephson junction circuits coupled to planar transmission line resonators with coherence time T2 > 100 microseconds.",
            formulas=["Hamiltonian: H = 4*Ec*(n - ng)^2 - Ej*cos(phi)"],
            specifications={"coherence_us": 100, "temp_mk": 15}
        )
        self.assertEqual(art.title, "Superconducting Qubit Matrix")
        retrieved = self.engine.get_article_by_title("Superconducting Qubit Matrix")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.category, "quantum_computing")
        self.assertIn("Josephson junction", retrieved.content)

    def test_fts5_bm25_search(self):
        """FTS5 search must rank relevant matches with negative BM25 score."""
        results = self.engine.search("titanium grade 5", top_k=3)
        self.assertGreater(len(results), 0)
        top = results[0]
        self.assertIsInstance(top, ArchiveSearchResult)
        self.assertIn("Titanium", top.article.title)
        self.assertLess(top.bm25_score, 0.0)
        self.assertGreater(len(top.snippet), 0)

    def test_category_filtered_search(self):
        """Search query restricted to a specific category."""
        results = self.engine.search("reactor", category="physics_aerospace", top_k=2)
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertEqual(r.article.category, "physics_aerospace")

    def test_ingest_jsonl(self):
        """Verifies bulk streaming ingestion from a JSONL file."""
        sample_file = self.temp_dir / "sample_records.jsonl"
        records = [
            {"title": "Aerogel Thermal Barrier", "summary": "Ultralight synthetic porous material", "content": "Silica aerogel with 99.8% air porosity providing thermal conductivity k = 0.013 W/m*K.", "category": "materials_metallurgy"},
            {"title": "Beryllium Armor Plate", "summary": "Lightweight structural metal", "content": "Beryllium provides high specific stiffness for aerospace satellite optical mirrors.", "category": "materials_metallurgy"}
        ]
        with open(sample_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        count = self.engine.ingest_jsonl(str(sample_file))
        self.assertEqual(count, 2)
        found = self.engine.get_article_by_title("Aerogel Thermal Barrier")
        self.assertIsNotNone(found)

    def test_local_slm_archive_integration(self):
        """Verifies local_neural_slm routes engineering questions to Stark Archive."""
        ans = local_neural_slm.reason("Titanium Alloy Grade 5 tensile strength")
        self.assertIsNotNone(ans)
        self.assertTrue("titanium" in ans.lower() or "ti-6al-4v" in ans.lower())


if __name__ == "__main__":
    unittest.main()
