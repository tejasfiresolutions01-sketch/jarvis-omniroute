"""
Unit Tests for J.A.R.V.I.S. Embedded Local Neural SLM & Offline Reasoning Matrix.
Validates zero-cost offline deduction, mathematical calculations, unit conversions,
semantic knowledge retrieval, and contextual memory fact reasoning.
"""

import time
import unittest
from core.local_neural_slm import LocalNeuralSLM, local_neural_slm
from core.brain import brain


class TestLocalNeuralSLM(unittest.TestCase):
    def setUp(self):
        self.slm = LocalNeuralSLM()

    def test_mathematical_percentage_calculation(self):
        """Must calculate percentages accurately in English."""
        res = self.slm.solve_math_expression("what is 15 percent of 200")
        self.assertIsNotNone(res)
        self.assertIn("30", res)

    def test_mathematical_square_and_cube_roots(self):
        """Must calculate roots accurately."""
        sqrt_res = self.slm.solve_math_expression("square root of 144")
        self.assertIsNotNone(sqrt_res)
        self.assertIn("12", sqrt_res)

        cbrt_res = self.slm.solve_math_expression("cube root of 27")
        self.assertIsNotNone(cbrt_res)
        self.assertIn("3", cbrt_res)

    def test_mathematical_powers_and_trigonometry(self):
        """Must calculate powers and trigonometry accurately."""
        pow_res = self.slm.solve_math_expression("2 to the power of 8")
        self.assertIsNotNone(pow_res)
        self.assertIn("256", pow_res)

        sin_res = self.slm.solve_math_expression("sin 90 degrees")
        self.assertIsNotNone(sin_res)
        self.assertIn("1", sin_res)

    def test_unit_conversions(self):
        """Must accurately convert between metric and imperial units."""
        temp_res = self.slm.solve_unit_conversion("100 fahrenheit to celsius")
        self.assertIsNotNone(temp_res)
        self.assertIn("37.78", temp_res)

        dist_res = self.slm.solve_unit_conversion("10 km to miles")
        self.assertIsNotNone(dist_res)
        self.assertIn("6.21", dist_res)

        data_res = self.slm.solve_unit_conversion("4 gb to mb")
        self.assertIsNotNone(data_res)
        self.assertIn("4096", data_res)

    def test_semantic_knowledge_lookup(self):
        """Must retrieve accurate encyclopedic knowledge offline."""
        api_res = self.slm.query_semantic_knowledge("explain what is an api")
        self.assertIsNotNone(api_res)
        self.assertIn("Application Programming Interface", api_res)

        hydro_res = self.slm.query_semantic_knowledge("what is the hydro test pressure for co2 under is 2190")
        self.assertIsNotNone(hydro_res)
        self.assertIn("250 kg/cm2", hydro_res)

        fire_res = self.slm.query_semantic_knowledge("tell me about the classes of fire")
        self.assertIsNotNone(fire_res)
        self.assertIn("Class A", fire_res)

    def test_contextual_fact_deduction(self):
        """Must extract facts directly from context when provided."""
        context = "User Project: Project Omniroute.\nLead Architect: Tony Stark.\nDeployment Node: Windows Server 2026."
        res = self.slm.reason("who is the lead architect", context=context)
        self.assertIsNotNone(res)
        self.assertIn("Tony Stark", res)

    def test_latency_performance_sub_10ms(self):
        """Deduction must execute in sub-10ms time offline."""
        start = time.perf_counter()
        for _ in range(50):
            self.slm.reason("explain what is an operating system")
        elapsed_per_query_ms = ((time.perf_counter() - start) / 50.0) * 1000.0
        self.assertLess(elapsed_per_query_ms, 10.0, f"Query latency was {elapsed_per_query_ms:.2f}ms")

    def test_brain_offline_deduction_integration(self):
        """Brain must deduce queries using Local SLM without internet."""
        ans = brain.think("calculate 12 times 12")
        self.assertIn("144", ans)


if __name__ == "__main__":
    unittest.main()
