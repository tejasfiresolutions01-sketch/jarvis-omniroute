import unittest
from core.single_question import enforce_single_question

class TestSingleQuestion(unittest.TestCase):
    def test_single_question_unchanged(self):
        text = "Would you like me to schedule that meeting, sir?"
        self.assertEqual(enforce_single_question(text), text)

    def test_no_question_unchanged(self):
        text = "Your schedule is clear for today, sir."
        self.assertEqual(enforce_single_question(text), text)

    def test_multiple_questions_reduced_to_one(self):
        text = "Would you like me to book this? Or should I postpone it? Do you agree?"
        res = enforce_single_question(text)
        self.assertLessEqual(res.count("?"), 1)
        self.assertIn("Would you like me to book this?", res)

if __name__ == "__main__":
    unittest.main()
