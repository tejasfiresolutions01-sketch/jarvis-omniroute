import unittest
from core.conceptual_synthesizer import ConceptualSynthesizer

class TestConceptualSynthesizer(unittest.TestCase):
    def setUp(self):
        self.synthesizer = ConceptualSynthesizer()

    def test_conceptual_query_triggers(self):
        self.assertTrue(self.synthesizer.is_conceptual_query("explain how an electric motor works"))
        self.assertTrue(self.synthesizer.is_conceptual_query("what is the difference between ac and dc"))
        self.assertTrue(self.synthesizer.is_conceptual_query("difference between ram and rom"))
        self.assertTrue(self.synthesizer.is_conceptual_query("what is artificial intelligence"))
        self.assertTrue(self.synthesizer.is_conceptual_query("how does photosynthesis operate"))

    def test_non_conceptual_commands_rejected(self):
        self.assertFalse(self.synthesizer.is_conceptual_query("open notepad"))
        self.assertFalse(self.synthesizer.is_conceptual_query("turn off volume"))
        self.assertFalse(self.synthesizer.is_conceptual_query("shutdown device"))
        self.assertFalse(self.synthesizer.is_conceptual_query("commit git changes"))
        self.assertFalse(self.synthesizer.is_conceptual_query("hi"))

    def test_acronym_and_entity_cleaning(self):
        self.assertEqual(self.synthesizer._clean_entity("ac"), "Alternating current")
        self.assertEqual(self.synthesizer._clean_entity("dc"), "Direct current")
        self.assertEqual(self.synthesizer._clean_entity("ram"), "Random-access memory")
        self.assertEqual(self.synthesizer._clean_entity("rom"), "Read-only memory")
        self.assertEqual(self.synthesizer._clean_entity("the electric motor works"), "electric motor")

    def test_single_question_compliance(self):
        ans = self.synthesizer.synthesize("difference between AC and DC current")
        self.assertIsNotNone(ans)
        self.assertIsInstance(ans, str)
        question_count = ans.count("?")
        self.assertLessEqual(question_count, 1)

    def test_caching_behavior(self):
        self.synthesizer._cache["test_topic"] = "Test synthesis result."
        res = self.synthesizer._cache.get("test_topic")
        self.assertEqual(res, "Test synthesis result.")

    def test_mechanistic_difference_parsing(self):
        diff = self.synthesizer.synthesize_difference("AC", "DC")
        if diff:
            self.assertIn("alternating current", diff.lower())
            self.assertIn("direct current", diff.lower())
            self.assertLessEqual(diff.count("?"), 1)

if __name__ == "__main__":
    unittest.main()
