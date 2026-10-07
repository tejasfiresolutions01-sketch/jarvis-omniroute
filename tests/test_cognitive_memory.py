"""
Unit tests for J.A.R.V.I.S. Multi-Store Cognitive Memory Architecture.
Tests working memory, semantic facts, episodic traces, subconscious auto-learning,
and cognitive context synthesis.
"""

import time
import unittest
import tempfile
from pathlib import Path
from core.cognitive_memory import CognitiveMemory

class TestCognitiveMemory(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_cognitive.db"
        self.cog_mem = CognitiveMemory(db_path=self.db_path)

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_working_memory_focus(self):
        self.assertEqual(self.cog_mem.get_focus(), "General Assistance")
        ack = self.cog_mem.set_focus("Quantum Flight Stabilizer")
        self.assertIn("Quantum Flight Stabilizer", ack)
        self.assertEqual(self.cog_mem.get_focus(), "Quantum Flight Stabilizer")

    def test_working_memory_goals(self):
        gid1 = self.cog_mem.add_goal("Calibrate arc reactor output", importance=9)
        gid2 = self.cog_mem.add_goal("Review subsystem telemetry", importance=5)
        
        goals = self.cog_mem.get_active_goals()
        self.assertEqual(len(goals), 2)
        self.assertEqual(goals[0]["id"], gid1) # Importance 9 sorted before 5
        
        # Complete goal by keyword
        ok = self.cog_mem.complete_goal("telemetry")
        self.assertTrue(ok)
        
        remaining = self.cog_mem.get_active_goals()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["id"], gid1)

    def test_semantic_facts_and_profile(self):
        self.cog_mem.store_fact("User", "Name", "Tony Stark", category="user_profile")
        self.cog_mem.store_fact("User", "Prefers", "Espresso", category="preference")
        self.cog_mem.store_fact("User", "Current Project", "Mark VII Armor", category="project")

        summary = self.cog_mem.get_user_profile_summary()
        self.assertIn("Tony Stark", summary)
        self.assertIn("Espresso", summary)
        self.assertIn("Mark VII Armor", summary)

        # Update fact
        self.cog_mem.store_fact("User", "Prefers", "Double Espresso", category="preference")
        prefs = self.cog_mem.recall_facts(category="preference")
        self.assertEqual(len(prefs), 1)
        self.assertEqual(prefs[0]["object_value"], "Double Espresso")

    def test_delete_fact(self):
        self.cog_mem.store_fact("User", "Prefers", "Tea", category="preference")
        count = self.cog_mem.delete_fact("tea")
        self.assertEqual(count, 1)
        self.assertEqual(len(self.cog_mem.recall_facts(category="preference")), 0)

    def test_episodic_memory_and_decay(self):
        ep1 = self.cog_mem.record_episode("Tested repulsor flight thrusters in workshop", episode_type="action", importance=8)
        self.assertGreater(ep1, 0)
        
        episodes = self.cog_mem.recall_episodes(query="repulsor thrusters", top_k=2)
        self.assertGreater(len(episodes), 0)
        self.assertIn("repulsor", episodes[0]["summary"].lower())

    def test_auto_extract_and_learn(self):
        learned = self.cog_mem.auto_extract_and_learn("My name is Venkat and I prefer dark mode in all apps")
        self.assertTrue(any("Venkat" in l for l in learned))
        self.assertTrue(any("dark mode" in l for l in learned))

        # Check stored facts
        facts = self.cog_mem.recall_facts(category="user_profile")
        self.assertEqual(facts[0]["object_value"], "Venkat")

        # Project extraction
        proj_learned = self.cog_mem.auto_extract_and_learn("I am working on the Iron Man HUD interface")
        self.assertTrue(any("HUD interface" in l for l in proj_learned))
        self.assertEqual(self.cog_mem.get_focus(), "the Iron Man HUD interface")

    def test_synthesize_context(self):
        self.cog_mem.set_focus("Autonomous Guidance")
        self.cog_mem.store_fact("User", "Role", "Chief Architect", category="user_profile")
        self.cog_mem.record_episode("Calibrated flight vectors", episode_type="milestone", importance=6)

        context = self.cog_mem.synthesize_context("guidance vectors")
        self.assertIn("Autonomous Guidance", context)
        self.assertIn("Cognitive State", context)

    def test_handle_cognitive_directive(self):
        # 1. Profile query
        self.cog_mem.store_fact("User", "Name", "Tony", category="user_profile")
        handled, resp = self.cog_mem.handle_cognitive_directive("What do you know about me?")
        self.assertTrue(handled)
        self.assertIn("Tony", resp)

        # 2. Set focus directive
        handled, resp = self.cog_mem.handle_cognitive_directive("Set focus to Neural Net Optimization")
        self.assertTrue(handled)
        self.assertEqual(self.cog_mem.get_focus(), "Neural Net Optimization")

        # 3. Add goal directive
        handled, resp = self.cog_mem.handle_cognitive_directive("Add goal: Refactor speech synthesis")
        self.assertTrue(handled)
        self.assertIn("Refactor speech synthesis", resp)

        # 4. Working memory query
        handled, resp = self.cog_mem.handle_cognitive_directive("What are our goals?")
        self.assertTrue(handled)
        self.assertIn("Refactor speech synthesis", resp)

if __name__ == "__main__":
    unittest.main()
