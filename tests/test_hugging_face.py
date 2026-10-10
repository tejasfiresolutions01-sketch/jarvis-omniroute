"""
Unit tests for J.A.R.V.I.S. Hugging Face Integration & Cognitive Hub Client.
Validates model discovery, model card metadata inspection, serverless inference,
text summarization, embedding extraction, and local intelligence routing.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from core.local_intelligence import local_intelligence
from tools.huggingface_client import HuggingFaceIntegration, huggingface_client


class TestHuggingFaceIntegration(unittest.TestCase):

    def setUp(self):
        self.client = huggingface_client

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Status & Configuration
    # ─────────────────────────────────────────────────────────────────────────
    def test_status_and_summary(self):
        """Verifies status dictionary and formatted summary string."""
        st = self.client.get_status()
        self.assertEqual(st["status"], "ONLINE (HUGGING FACE INTEGRATION TIER 5)")
        self.assertIn("library_version", st)
        self.assertIn("default_models", st)
        self.assertIn("capabilities", st)

        summary = self.client.format_status_summary()
        self.assertIn("Hugging Face integration online", summary)
        self.assertIn("default generation model", summary.lower())

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Model Discovery & Metadata
    # ─────────────────────────────────────────────────────────────────────────
    def test_search_models_mocked_and_structure(self):
        """Verifies model search structure and error resilience."""
        mock_model = MagicMock()
        mock_model.id = "meta-llama/Llama-3.2-1B"
        mock_model.author = "meta-llama"
        mock_model.downloads = 1500000
        mock_model.likes = 4200
        mock_model.pipeline_tag = "text-generation"

        with patch.object(self.client._api, "list_models", return_value=[mock_model]):
            res = self.client.search_models("llama", limit=2)
            self.assertTrue(res["success"])
            self.assertEqual(res["count"], 1)
            self.assertEqual(res["models"][0]["id"], "meta-llama/Llama-3.2-1B")
            self.assertEqual(res["models"][0]["pipeline_tag"], "text-generation")

    def test_get_model_info_mocked(self):
        """Verifies model card metadata extraction."""
        mock_info = MagicMock()
        mock_info.id = "Qwen/Qwen2.5-7B"
        mock_info.pipeline_tag = "text-generation"
        mock_info.downloads = 890000
        mock_info.likes = 2100
        mock_info.tags = ["safetensors", "qwen2", "conversational"]
        mock_info.safetensors = True
        mock_info.last_modified = "2024-10-01"

        with patch.object(self.client._api, "model_info", return_value=mock_info):
            res = self.client.get_model_info("Qwen/Qwen2.5-7B")
            self.assertTrue(res["success"])
            self.assertEqual(res["id"], "Qwen/Qwen2.5-7B")
            self.assertEqual(res["security"], "SafeTensors Verified")
            self.assertIn("safetensors", res["tags"])

    def test_search_datasets_and_spaces(self):
        """Verifies dataset and spaces search methods."""
        mock_d = MagicMock()
        mock_d.id = "squad"
        mock_d.author = "rajpurkar"
        mock_d.downloads = 50000
        mock_d.likes = 800

        with patch.object(self.client._api, "list_datasets", return_value=[mock_d]):
            res_d = self.client.search_datasets("squad", limit=1)
            self.assertTrue(res_d["success"])
            self.assertEqual(res_d["count"], 1)
            self.assertEqual(res_d["datasets"][0]["id"], "squad")

        mock_s = MagicMock()
        mock_s.id = "gradio/chat"
        mock_s.author = "gradio"
        mock_s.likes = 120

        with patch.object(self.client._api, "list_spaces", return_value=[mock_s]):
            res_s = self.client.search_spaces("chat", limit=1)
            self.assertTrue(res_s["success"])
            self.assertEqual(res_s["count"], 1)
            self.assertEqual(res_s["spaces"][0]["id"], "gradio/chat")

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Serverless Inference & Fallback
    # ─────────────────────────────────────────────────────────────────────────
    def test_generate_text_resilient_fallback(self):
        """Verifies text generation fallback when unauthenticated."""
        res = self.client.generate_text("Explain arc reactor containment.")
        self.assertTrue(res["success"])
        self.assertIn("generated_text", res)
        self.assertGreater(len(res["generated_text"]), 10)

    def test_generate_text_authenticated_mock(self):
        """Verifies text generation when serverless client succeeds."""
        mock_choice = MagicMock()
        mock_choice.message.content = "Containment achieved through magnetic stabilization fields."
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]

        with patch.object(self.client, "token", "hf_validmocktoken123"), \
             patch.object(self.client._inference_client, "chat_completion", return_value=mock_resp):
            res = self.client.generate_text("Containment query")
            self.assertTrue(res["success"])
            self.assertIn("magnetic stabilization", res["generated_text"])

    def test_summarize_text(self):
        """Verifies text summarization routine."""
        sample_doc = (
            "The Mark-85 armor features nanotech surface deployment. "
            "Energy is routed through a vibranium composite arc reactor. "
            "Sub-orbital flight testing demonstrated 98 percent aerodynamic efficiency. "
            "Defensive shields activate within 4 milliseconds."
        )
        res = self.client.summarize_text(sample_doc)
        self.assertTrue(res["success"])
        self.assertIn("summary", res)
        self.assertGreater(len(res["summary"]), 15)

    def test_generate_embeddings(self):
        """Verifies vector embedding dimensionality and normalized values."""
        res = self.client.generate_embeddings("Telemetry packet vector representation")
        self.assertTrue(res["success"])
        self.assertEqual(res["dimensions"], 384)
        self.assertEqual(len(res["vector_sample"]), 5)
        for val in res["vector_sample"]:
            self.assertIsInstance(val, float)
            self.assertGreaterEqual(val, -1.0)
            self.assertLessEqual(val, 1.0)

    def test_list_cached_models(self):
        """Verifies cached repository listing."""
        res = self.client.list_cached_models()
        self.assertTrue(res["success"])
        self.assertIn("cached_repos_count", res)

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Local Intelligence Directives Integration (Skill 16)
    # ─────────────────────────────────────────────────────────────────────────
    def test_local_intelligence_skill_16_directives(self):
        """Verifies voice/text directives in local intelligence."""
        # 1. Status
        h1, res1 = local_intelligence.evaluate_and_execute("hugging face status")
        self.assertTrue(h1)
        self.assertIn("Hugging Face integration online", res1)

        # 2. Search models
        mock_m = MagicMock()
        mock_m.id = "Qwen/Qwen2.5-7B-Instruct"
        mock_m.author = "Qwen"
        mock_m.downloads = 500000
        mock_m.likes = 1200
        mock_m.pipeline_tag = "text-generation"

        with patch.object(self.client._api, "list_models", return_value=[mock_m]):
            h2, res2 = local_intelligence.evaluate_and_execute("search hf models qwen")
            self.assertTrue(h2)
            self.assertIn("Hugging Face Hub search for 'qwen'", res2)
            self.assertIn("Qwen/Qwen2.5-7B-Instruct", res2)

        # 3. Model info
        mock_info = MagicMock()
        mock_info.id = "microsoft/Phi-3.5-mini-instruct"
        mock_info.pipeline_tag = "text-generation"
        mock_info.downloads = 320000
        mock_info.likes = 950
        mock_info.tags = ["safetensors", "phi"]
        mock_info.safetensors = True
        mock_info.last_modified = "2024-09-15"

        with patch.object(self.client._api, "model_info", return_value=mock_info):
            h3, res3 = local_intelligence.evaluate_and_execute("inspect hf model microsoft/Phi-3.5-mini-instruct")
            self.assertTrue(h3)
            self.assertIn("Hugging Face Model 'microsoft/Phi-3.5-mini-instruct'", res3)
            self.assertIn("text-generation", res3)

        # 4. Ask / Generate
        h4, res4 = local_intelligence.evaluate_and_execute("ask hugging face Explain repulsor mechanics")
        self.assertTrue(h4)
        self.assertGreater(len(res4), 20)

        # 5. Summarize
        h5, res5 = local_intelligence.evaluate_and_execute("hf summarize Flight stabilizers are operating normally. Internal core temperatures are within standard ranges.")
        self.assertTrue(h5)
        self.assertIn("Hugging Face Summary", res5)

        # 6. Embed
        h6, res6 = local_intelligence.evaluate_and_execute("hf embed neural matrix state")
        self.assertTrue(h6)
        self.assertIn("Extracted 384-dimensional vector embedding", res6)


if __name__ == "__main__":
    unittest.main()
