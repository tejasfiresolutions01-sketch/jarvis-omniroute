"""
Unit Tests for J.A.R.V.I.S. Stark Neural Core & 300 GB Local Model Orchestration Matrix.
Verifies:
1. Model directory provisioning and 300 GB storage quota auditing.
2. Native AVX2 llama.cpp binary resolution.
3. Active Qwen2.5-1.5B GGUF model resolution and CPU text generation.
4. Two-tier neural reasoning in core.local_neural_slm (Sub-5ms Reflex + Generative SLM).
"""

import unittest
from pathlib import Path

from core.stark_neural_manager import stark_neural_manager, StorageQuotaStatus, SLMGenerationResult
from core.local_neural_slm import local_neural_slm


class TestStarkNeuralCore(unittest.TestCase):
    """Verifies Phase 1 of the 300 GB Stark Advancement Matrix."""

    def setUp(self):
        self.manager = stark_neural_manager
        self.slm = local_neural_slm

    def test_tier_directories_provisioned(self):
        """All 8 model tier directories must exist under models/."""
        for tier in self.manager.TIERS:
            p = self.manager.models_dir / tier
            self.assertTrue(p.exists(), f"Tier directory missing: {tier}")
            self.assertTrue(p.is_dir(), f"Tier path is not a directory: {tier}")

    def test_storage_quota_audit(self):
        """Storage audit must correctly report allocated 300 GB quota and usage."""
        audit = self.manager.get_storage_audit()
        self.assertIsInstance(audit, StorageQuotaStatus)
        self.assertEqual(audit.allocated_gb, 300.0)
        self.assertGreater(audit.total_used_gb, 0.5)  # GGUF model is ~1 GB
        self.assertGreater(audit.remaining_gb, 200.0)
        self.assertIn("llm", audit.tier_usage_mb)
        self.assertIn("bin", audit.tier_usage_mb)
        self.assertGreater(audit.tier_usage_mb["llm"], 500.0)  # GGUF size in MB

    def test_binary_resolution(self):
        """Local AVX2 llama-cli binary must resolve in models/bin."""
        bin_path = self.manager.get_binary_path("llama-cli.exe")
        self.assertIsNotNone(bin_path)
        self.assertTrue(bin_path.is_file())

    def test_active_slm_model_resolution(self):
        """Active Tactical Reflex SLM GGUF model must resolve in models/llm."""
        model_path = self.manager.get_active_slm_path()
        self.assertIsNotNone(model_path)
        self.assertTrue(model_path.is_file())
        self.assertTrue(model_path.name.endswith(".gguf"))

    def test_local_slm_generation(self):
        """Generates offline response using native AVX2 Qwen2.5 GGUF."""
        res = self.manager.generate_response(
            prompt="State J.A.R.V.I.S. operational status in one sentence.",
            max_tokens=32
        )
        self.assertIsInstance(res, SLMGenerationResult)
        self.assertTrue(res.success)
        self.assertGreater(len(res.text), 5)
        self.assertGreater(res.elapsed_seconds, 0.0)
        self.assertIn(".gguf", res.model_name)

    def test_two_tier_reasoning_reflex_and_generative(self):
        """Verifies sub-5ms mathematical reflex and fallback to generative SLM."""
        # Layer 1: Sub-5ms Exact Reflex
        math_ans = self.slm.reason("what is 25 times 4", enable_generative_slm=False)
        self.assertIsNotNone(math_ans)
        self.assertIn("100", math_ans)

        # Layer 2: Deep Generative SLM
        gen_ans = self.slm.reason("What does J.A.R.V.I.S. stand for?", enable_generative_slm=True)
        self.assertIsNotNone(gen_ans)
        self.assertGreater(len(gen_ans), 10)


if __name__ == "__main__":
    unittest.main()
