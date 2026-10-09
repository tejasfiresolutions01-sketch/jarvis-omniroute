"""
Unit tests for J.A.R.V.I.S. Autonomous Coding AI and Engineering Skills Engine.
Validates code generation, AST parsing, security anti-pattern scanning,
test suite generation, codebase metrics, and voice directive dispatch.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.local_intelligence import local_intelligence
from tools.coding_agent import CodingAgent, coding_agent


class TestCodingAgent(unittest.TestCase):

    def setUp(self):
        self.agent = coding_agent

    def test_generate_code_offline_fallback(self):
        """Verifies code generation creates valid, parseable Python code."""
        with patch("core.free_ai_matrix.free_ai_matrix.chat_completion", return_value=None):
            res = self.agent.generate_code("calculate factorial iteratively", language="python")
            self.assertTrue(res["success"])
            self.assertEqual(res["language"], "python")
            self.assertTrue(res["syntax_valid"])
            self.assertIn("def calculate_factorial", res["extracted_code"])

    def test_review_code_clean_file(self):
        """Verifies static code review on a clean Python file."""
        code = '''"""Sample Module."""

class VectorCalculator:
    """Calculates vector magnitudes."""
    def magnitude(self, x: float, y: float) -> float:
        """Returns Euclidean magnitude."""
        return (x**2 + y**2)**0.5
'''
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name

        try:
            res = self.agent.review_code(tmp_path)
            self.assertTrue(res["success"])
            self.assertTrue(res["ast_valid"])
            self.assertIn("VectorCalculator", res["classes"])
            self.assertIn("magnitude", res["functions"])
            self.assertEqual(res["findings_count"], 0)
            self.assertEqual(res["quality_score"], 100)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_review_code_security_flaws(self):
        """Verifies static analyzer detects security anti-patterns."""
        flawed_code = '''
def dangerous_routine(payload):
    api_key = "abcdef12345678"
    eval("2 + 2")
    os.system("echo hacked")
    try:
        pass
    except:
        pass
'''
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(flawed_code)
            tmp_path = f.name

        try:
            res = self.agent.review_code(tmp_path)
            self.assertTrue(res["success"])
            self.assertGreater(res["findings_count"], 0)
            self.assertLess(res["quality_score"], 80)
            messages = [f["message"] for f in res["findings"]]
            self.assertTrue(any("credential" in m.lower() for m in messages))
            self.assertTrue(any("eval" in m.lower() for m in messages))
            self.assertTrue(any("os.system" in m.lower() for m in messages))
            self.assertTrue(any("except" in m.lower() for m in messages))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_generate_tests_for_file(self):
        """Verifies automated test generation authoring unittest.TestCase."""
        sample_code = '''
def add_numbers(a, b):
    return a + b

class MatrixSolver:
    def solve(self):
        return True
'''
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(sample_code)
            tmp_path = f.name

        try:
            res = self.agent.generate_tests_for_file(tmp_path)
            self.assertTrue(res["success"])
            self.assertIn("add_numbers", res["detected_functions"])
            self.assertIn("MatrixSolver", res["detected_classes"])
            self.assertIn("unittest.TestCase", res["test_code"])
            self.assertIn("test_add_numbers_callable", res["test_code"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_get_codebase_metrics(self):
        """Verifies codebase metrics analysis."""
        metrics = self.agent.get_codebase_metrics()
        self.assertIn("metrics", metrics)
        m = metrics["metrics"]
        self.assertGreater(m["python_files"], 10)
        self.assertGreater(m["test_files"], 5)
        self.assertGreater(m["total_lines"], 1000)

    def test_get_status(self):
        """Verifies coding agent status reporting."""
        status = self.agent.get_status()
        self.assertEqual(status["status"], "ONLINE")
        self.assertIn("python", status["supported_languages"])
        self.assertEqual(status["ast_validation"], "Active")

    def test_local_intelligence_coding_directives(self):
        """Verifies voice/text directives in LocalIntelligence."""
        # 1. Status
        handled, msg = local_intelligence.evaluate_and_execute("coding ai status")
        self.assertTrue(handled)
        self.assertIn("Coding AI online", msg)

        # 2. Metrics
        handled, msg = local_intelligence.evaluate_and_execute("codebase metrics")
        self.assertTrue(handled)
        self.assertIn("Codebase metrics", msg)

        # 3. Generate Code
        handled, msg = local_intelligence.evaluate_and_execute("write code for binary search algorithm")
        self.assertTrue(handled)
        self.assertIn("Code generated successfully", msg)
        self.assertIn("```python", msg)

        # 4. Review Code
        handled, msg = local_intelligence.evaluate_and_execute("review code tools/coding_agent.py")
        self.assertTrue(handled)
        self.assertIn("Code review for coding_agent.py complete", msg)

        # 5. Generate Tests
        handled, msg = local_intelligence.evaluate_and_execute("generate tests for tools/coding_agent.py")
        self.assertTrue(handled)
        self.assertIn("Generated automated unit test suite", msg)


if __name__ == "__main__":
    unittest.main()
