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

    def test_fields_of_work_catalog(self):
        """Verifies all 10 major fields of work are indexed with personas."""
        fields = self.matrix.list_fields_of_work()
        expected = [
            "software_engineering", "mathematics_and_logic", "medicine_and_healthcare",
            "finance_and_economics", "law_and_governance", "creative_arts_and_literature",
            "visual_design_and_imaging", "cybersecurity_and_devops",
            "natural_sciences_and_physics", "education_and_pedagogy"
        ]
        for f in expected:
            self.assertIn(f, fields)
            self.assertTrue(len(fields[f]["aliases"]) > 0)
            self.assertIn("system_role", fields[f])

    def test_fields_of_work_summary(self):
        """Verifies summary string formatting for fields of work."""
        summary = self.matrix.get_fields_summary()
        self.assertIn("Software Engineering", summary)
        self.assertIn("Medicine", summary)
        self.assertIn("Law", summary)

    def test_classify_field(self):
        """Tests automatic domain classifier for varied user prompts."""
        self.assertEqual(self.matrix.classify_field("Write a python script for sorting"), "software_engineering")
        self.assertEqual(self.matrix.classify_field("Calculate calculus integral proof"), "mathematics_and_logic")
        self.assertEqual(self.matrix.classify_field("Analyze clinical symptoms for disease"), "medicine_and_healthcare")
        self.assertEqual(self.matrix.classify_field("Evaluate investing in stock market"), "finance_and_economics")
        self.assertEqual(self.matrix.classify_field("Review this contracts statute"), "law_and_governance")

    @patch("core.free_ai_matrix.requests.post")
    def test_query_field_expert(self, mock_post):
        """Tests querying a specialized field expert with expert persona."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Clinical diagnosis completed, sir."}}]
        }
        mock_post.return_value = mock_resp

        reply, label = self.matrix.query_field_expert("medicine", "Examine cardiac biomarkers")
        self.assertIn("Clinical diagnosis completed, sir.", reply)
        self.assertIn("Medicine, Healthcare", label)

    def test_local_intelligence_fields_intent(self):
        """Tests voice recognition of 'list fields of work' and domain expert queries."""
        local_intel = LocalIntelligence()
        handled, response = local_intel.evaluate_and_execute("list fields of work")
        self.assertTrue(handled)
        self.assertIn("specialized domain intelligence", response)
        self.assertIn("Software Engineering", response)

    def test_business_operations_catalog(self):
        """Verifies all 9 requested business operations are cataloged with roles and models."""
        ops = self.matrix.list_business_operations()
        expected = [
            "marketing", "lead_generation", "lead_verification",
            "customer_acquisition", "customer_retention", "accounts_and_bookkeeping",
            "stock_and_inventory", "document_generation", "problem_handling"
        ]
        for op in expected:
            self.assertIn(op, ops)
            self.assertTrue(len(ops[op]["aliases"]) > 0)
            self.assertIn("system_role", ops[op])
            self.assertIn("lead_model", ops[op])

    def test_business_operations_summary(self):
        """Verifies spoken overview of all 9 enterprise business operations."""
        summary = self.matrix.get_business_summary()
        self.assertIn("all 9 key business operations", summary)
        self.assertIn("Growth Marketing", summary)
        self.assertIn("Lead Generation", summary)
        self.assertIn("Accounts, Bookkeeping", summary)
        self.assertIn("Stock & Inventory", summary)
        self.assertIn("Enterprise Document & Contract", summary)
        self.assertIn("Business Problem Resolution", summary)

    @patch("core.free_ai_matrix.requests.post")
    def test_query_business_operation(self, mock_post):
        """Tests executing a business operation directive with specialized executive role."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Executive marketing campaign strategy formulated."}}]
        }
        mock_post.return_value = mock_resp

        reply, label = self.matrix.query_business_operation("marketing", "Formulate Q4 SaaS campaign")
        self.assertIn("Executive marketing campaign strategy formulated.", reply)
        self.assertIn("Growth Marketing & Campaign Strategy AI", label)

    def test_local_intelligence_business_listing_intent(self):
        """Tests voice recognition of 'list business ais'."""
        local_intel = LocalIntelligence()
        handled, response = local_intel.evaluate_and_execute("list business ais")
        self.assertTrue(handled)
        self.assertIn("key business operations", response)
        self.assertIn("Growth Marketing", response)

    @patch.object(FreeAIMatrix, "query_business_operation")
    def test_local_intelligence_business_operation_commands(self, mock_biz_query):
        """Tests voice directive extraction for business AI operations."""
        local_intel = LocalIntelligence()

        test_commands = [
            ("consult marketing ai on holiday campaigns", "marketing"),
            ("ask lead generation ai to prospect B2B leads", "lead generation"),
            ("use lead verification ai to score prospects", "lead verification"),
            ("consult customer acquisition ai on sales funnels", "customer acquisition"),
            ("ask customer retention ai to prevent churn", "customer retention"),
            ("consult accounts ai on balance sheet", "accounts"),
            ("ask stock management ai to check warehouse inventory", "stock management"),
            ("run document generation ai to draft NDA contract", "document generation"),
            ("consult problem handling ai on dispute resolution", "problem handling")
        ]

        for phrase, op in test_commands:
            mock_biz_query.return_value = (f"Executive brief on {op}: Complete", op)
            handled, resp = local_intel.evaluate_and_execute(phrase)
            self.assertTrue(handled, f"Failed on business phrase: {phrase}")
            self.assertIn(f"Executive brief on {op}: Complete", resp)

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

