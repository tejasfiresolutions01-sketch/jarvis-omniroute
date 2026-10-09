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
        self.assertIn("ONLINE", status["status"])
        self.assertIn("python", status["supported_languages"])
        self.assertEqual(status["ast_validation"], "Active")
        self.assertEqual(status["auto_diagnostician"], "Active")

    def test_diagnose_and_patch_error(self):
        """Verifies traceback parsing and root-cause diagnosis."""
        traceback_sample = """Traceback (most recent call last):
  File "tools/test_demo.py", line 42, in execute_action
    val = self.missing_variable
AttributeError: 'TestDemo' object has no attribute 'missing_variable'"""
        res = self.agent.diagnose_and_patch_error(traceback_sample)
        self.assertTrue(res["success"])
        self.assertEqual(res["error_type"], "AttributeError")
        self.assertEqual(res["line_number"], 42)
        self.assertIn("missing_variable", res["error_message"])
        self.assertIn("Attribute mismatch detected", res["recommended_patch"])

    def test_analyze_complexity(self):
        """Verifies cyclomatic complexity calculation across functions."""
        sample_code = """
def simple_fn():
    return 1

def complex_fn(a, b, c):
    if a > 0:
        for x in range(b):
            if x % 2 == 0:
                print(x)
            elif x == 3:
                break
    elif c:
        while True:
            pass
    return True
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(sample_code)
            tmp_path = f.name

        try:
            res = self.agent.analyze_complexity(tmp_path)
            self.assertTrue(res["success"])
            self.assertEqual(res["total_functions_analyzed"], 2)
            fn_map = {f["name"]: f["complexity"] for f in res["functions"]}
            self.assertEqual(fn_map["simple_fn"], 1)
            self.assertGreater(fn_map["complex_fn"], 4)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_execute_code_snippet(self):
        """Verifies sandboxed snippet execution and timing capture."""
        code = "print('Hello from sandboxed J.A.R.V.I.S.')"
        res = self.agent.execute_code_snippet(code, timeout=4.0)
        self.assertTrue(res["success"])
        self.assertTrue(res["passed"])
        self.assertEqual(res["return_code"], 0)
        self.assertIn("Hello from sandboxed J.A.R.V.I.S.", res["stdout"])
        self.assertGreater(res["duration_ms"], 0)

    def test_scan_dead_code(self):
        """Verifies detection of unused imports."""
        sample_code = """
import os
import sys
import math

print(os.getcwd())
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(sample_code)
            tmp_path = f.name

        try:
            res = self.agent.scan_dead_code(tmp_path)
            self.assertTrue(res["success"])
            self.assertEqual(res["total_imports"], 3)
            unused_symbols = [u["symbol"] for u in res["unused_imports"]]
            self.assertIn("sys", unused_symbols)
            self.assertIn("math", unused_symbols)
            self.assertNotIn("os", unused_symbols)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

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

        # 6. Complexity Analysis
        handled, msg = local_intelligence.evaluate_and_execute("analyze complexity tools/coding_agent.py")
        self.assertTrue(handled)
        self.assertIn("Complexity analysis for coding_agent.py", msg)

        # 7. Dead Code Scan
        handled, msg = local_intelligence.evaluate_and_execute("scan dead code tools/coding_agent.py")
        self.assertTrue(handled)
        self.assertIn("Dead code audit for coding_agent.py", msg)

        # 8. Diagnose Error
        handled, msg = local_intelligence.evaluate_and_execute('diagnose error File "app.py", line 10, in run\n    raise ValueError("Invalid parameter")\nValueError: Invalid parameter')
        self.assertTrue(handled)
        self.assertIn("Diagnosed ValueError", msg)

        # 9. Execute Snippet
        handled, msg = local_intelligence.evaluate_and_execute("run snippet print(40 + 2)")
        self.assertTrue(handled)
        self.assertIn("Snippet execution Passed", msg)
        self.assertIn("42", msg)


if __name__ == "__main__":
    unittest.main()

