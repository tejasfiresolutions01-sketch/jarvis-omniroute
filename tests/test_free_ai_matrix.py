import unittest
from unittest.mock import patch, MagicMock
from core.free_ai_matrix import FreeAIMatrix, free_ai_matrix
from core.local_intelligence import LocalIntelligence
from core.task_orchestrator import TaskOrchestrator

class TestFreeAIMatrix(unittest.TestCase):
    """
    Unit test suite for the Universal Free AI Matrix.
    Validates zero-cost multi-model routing, failover cascades, voice sanitization,
    and voice intent mapping across all global frontier AI providers.
    """

    def setUp(self):
        self.matrix = FreeAIMatrix()

    def test_catalog_listing(self):
        """Verifies that all major AI families are cataloged."""
        catalog = self.matrix.list_supported_ais()
        expected = ["OpenAI", "Anthropic Claude", "Mistral AI", "DeepSeek", "Meta Llama", "Alibaba Qwen", "Google Gemini"]
        for prov in expected:
            self.assertIn(prov, catalog)
            self.assertTrue(len(catalog[prov]) > 0)

    def test_voice_sanitization(self):
        """Verifies markdown asterisks, backticks, and bullet points are stripped for voice."""
        raw = "### Title\n* Bullet 1\n**Bold text** with `inline code` and normal text."
        clean = self.matrix._sanitize_for_voice(raw)
        self.assertNotIn("###", clean)
        self.assertNotIn("*", clean)
        self.assertNotIn("`", clean)
        self.assertIn("Bold text with inline code", clean)

    @patch("core.free_ai_matrix.requests.post")
    def test_query_provider_success(self, mock_post):
        """Tests successful provider routing via OmniRoute gateway."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "I am Claude, at your service."}}]
        }
        mock_post.return_value = mock_resp

        reply, label = self.matrix.query_provider("claude", "Introduce yourself")
        self.assertIn("According to", reply)
        self.assertIn("Claude", reply)
        self.assertIn("I am Claude, at your service.", reply)

    @patch("core.free_ai_matrix.requests.post")
    def test_query_provider_cascade_failover(self, mock_post):
        """Tests that if primary route fails, failover cascades to secondary zero-cost route."""
        # First call fails (500), second call succeeds (200)
        fail_resp = MagicMock()
        fail_resp.status_code = 500

        succ_resp = MagicMock()
        succ_resp.status_code = 200
        succ_resp.json.return_value = {
            "choices": [{"message": {"content": "Fallback response engaged."}}]
        }

        mock_post.side_effect = [fail_resp, succ_resp]

        reply, label = self.matrix.query_provider("claude", "Test prompt")
        self.assertIn("Fallback response engaged", reply)

    def test_local_intelligence_catalog_intent(self):
        """Tests that 'what ais do you support' returns catalog summary."""
        local_intel = LocalIntelligence()
        handled, response = local_intel.evaluate_and_execute("what ais do you support")
        self.assertTrue(handled)
        self.assertIn("OpenAI", response)
        self.assertIn("Claude", response)
        self.assertIn("DeepSeek", response)

    @patch.object(FreeAIMatrix, "query_provider")
    def test_local_intelligence_model_commands(self, mock_query):
        """Tests that voice directives to specific models are properly extracted."""
        local_intel = LocalIntelligence()

        test_phrases = [
            ("ask deepseek to solve this proof", "deepseek"),
            ("ask claude about quantum computing", "claude"),
            ("command openai to write a poem", "openai"),
            ("ask llama to summarize this", "llama"),
            ("ask qwen to analyze code", "qwen"),
            ("ask gemini for suggestions", "gemini")
        ]

        for phrase, prov in test_phrases:
            mock_query.return_value = (f"According to {prov}: OK", prov)
            handled, resp = local_intel.evaluate_and_execute(phrase)
            self.assertTrue(handled, f"Failed on phrase: {phrase}")
            self.assertIn(f"According to {prov}: OK", resp)

    def test_omniroute_free_providers_catalog(self):
        """Verifies all 11 OmniRoute free providers are indexed."""
        providers = self.matrix.list_omniroute_free_providers()
        expected = [
            "duckduckgo-web", "aihorde", "cloudflare-playground", "freetheai",
            "freebuff", "opencode", "freemodel-dev", "uncloseai",
            "free-ai", "freeinference", "openai"
        ]
        for ep in expected:
            self.assertIn(ep, providers)
            self.assertTrue(len(providers[ep]["models"]) > 0)

    def test_omniroute_free_providers_summary(self):
        """Verifies summary string formatting for OmniRoute free providers."""
        summary = self.matrix.get_omniroute_free_summary()
        self.assertIn("DuckDuckGo Web", summary)
        self.assertIn("AI Horde", summary)
        self.assertIn("Cloudflare AI Playground", summary)

    @patch("core.free_ai_matrix.requests.post")
    def test_query_omniroute_provider_direct(self, mock_post):
        """Tests directly targeting an OmniRoute free provider by alias."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "DuckDuckGo response received."}}]
        }
        mock_post.return_value = mock_resp

        reply, label = self.matrix.query_omniroute_provider("ddgw", "Test query")
        self.assertIn("DuckDuckGo response received.", reply)
        self.assertIn("DuckDuckGo Web", label)

    def test_local_intelligence_omniroute_free_intent(self):
        """Tests voice recognition of 'list omniroute free providers'."""
        local_intel = LocalIntelligence()
        handled, response = local_intel.evaluate_and_execute("list omniroute free providers")
        self.assertTrue(handled)
        self.assertIn("OmniRoute active free providers", response)
        self.assertIn("DuckDuckGo Web", response)

    @patch.object(FreeAIMatrix, "query_provider")
    def test_task_orchestrator_tool_dispatch(self, mock_query):
        """Tests orchestrator tool dispatch for command_other_ai."""
        mock_query.return_value = ("According to OpenAI: Result", "OpenAI")
        orchestrator = TaskOrchestrator()
        calls = [("command_other_ai", {"prompt": "Calculate 2+2", "model_name": "openai"})]
        results = orchestrator.execute_tools(calls)
        self.assertEqual(len(results), 1)
        self.assertIn("According to OpenAI: Result", results[0]["output"])

if __name__ == "__main__":
    unittest.main()
