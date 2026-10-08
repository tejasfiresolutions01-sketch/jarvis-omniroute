"""
Unit tests for the 5 Comprehensive Expansion Areas:
1. Autonomous Web & Market Intelligence Agent
2. Business Workflow, Quotations, and WhatsApp Engine
3. Real-World Optical Vision & Camera Inspection Engine
4. Advanced Multi-Agent Workflow Mesh
5. Holographic HUD Telemetry & Auditory Experience Matrix
"""

import os
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.browser_agent import browser_agent
from tools.business_workflow_engine import business_workflow
from tools.optical_inspection_engine import optical_inspection
from core.multi_agent_mesh import multi_agent_mesh
from ui.hud_telemetry_matrix import hud_telemetry
from core.local_intelligence import local_intelligence

class TestComprehensiveExpansion(unittest.TestCase):
    """Verifies all 5 comprehensive development areas."""

    # ─────────────────────────────────────────────────────────────────────
    # Area 1: Autonomous Web & Market Intelligence
    # ─────────────────────────────────────────────────────────────────────
    def test_browser_agent_material_prices(self):
        """Verifies market raw material tracking and pricing data."""
        p_data = browser_agent.track_supplier_material_prices()
        self.assertGreater(p_data["materials_count"], 0)
        self.assertIn("map_abc_powder", p_data["pricing"])

    def test_browser_agent_tenders(self):
        """Verifies Tamil Nadu fire safety tender scanning."""
        tenders = browser_agent.scan_government_tenders()
        self.assertGreater(len(tenders), 0)
        self.assertIn("tender_id", tenders[0])

    def test_browser_agent_voice_intents(self):
        """Verifies voice intents for material prices and tenders."""
        handled_p, resp_p = local_intelligence.evaluate_and_execute("track supplier prices")
        self.assertTrue(handled_p)
        self.assertIn("material tracking", resp_p.lower())

        handled_t, resp_t = local_intelligence.evaluate_and_execute("check government tenders")
        self.assertTrue(handled_t)
        self.assertIn("tender", resp_t.lower())

    # ─────────────────────────────────────────────────────────────────────
    # Area 2: Business Workflow, Quotations & CRM
    # ─────────────────────────────────────────────────────────────────────
    def test_business_workflow_crm(self):
        """Verifies CRM lead addition and pipeline statistics."""
        lead_id = business_workflow.add_or_update_lead("Sriperumbudur Auto Spares", hub="Sriperumbudur", quote_amount=15000.0)
        self.assertIsInstance(lead_id, int)
        summary = business_workflow.get_pipeline_summary()
        self.assertGreaterEqual(summary["total_leads"], 1)

    def test_business_workflow_quotation(self):
        """Verifies commercial quotation generation and GST ledgering."""
        items = [{"item_code": "abc_6kg", "quantity": 5}, {"item_code": "hydro_test", "quantity": 5}]
        quote = business_workflow.generate_quotation("Ambattur Tooling Corp", items)
        self.assertIn("quotation_number", quote)
        self.assertGreater(quote["subtotal_inr"], 0)
        self.assertAlmostEqual(quote["cgst_9pct"], quote["sgst_9pct"])
        self.assertAlmostEqual(quote["total_inr"], quote["subtotal_inr"] + quote["cgst_9pct"] + quote["sgst_9pct"])

    def test_business_workflow_whatsapp(self):
        """Verifies WhatsApp Web dispatch link construction."""
        link = business_workflow.build_whatsapp_message_link("9840012345", "Quotation is ready, sir.")
        self.assertTrue(link.startswith("https://web.whatsapp.com/send?phone=919840012345"))
        self.assertIn("Quotation%20is%20ready", link)

    def test_business_workflow_voice_intents(self):
        """Verifies voice intents for quotes and pipeline status."""
        handled_q, resp_q = local_intelligence.evaluate_and_execute("generate quotation for Tata Motors Hub")
        self.assertTrue(handled_q)
        self.assertIn("quotation", resp_q.lower())

        handled_c, resp_c = local_intelligence.evaluate_and_execute("crm pipeline status")
        self.assertTrue(handled_c)
        self.assertIn("pipeline", resp_c.lower())

    # ─────────────────────────────────────────────────────────────────────
    # Area 3: Real-World Optical Vision & Camera Inspection
    # ─────────────────────────────────────────────────────────────────────
    def test_optical_extinguisher_classification(self):
        """Verifies extinguisher type classification from optical input."""
        res = optical_inspection.classify_fire_extinguisher()
        self.assertTrue(res["detected"])
        self.assertIn("type", res)

    def test_optical_pressure_gauge(self):
        """Verifies analog manometer pressure inspection."""
        gauge = optical_inspection.inspect_pressure_gauge()
        self.assertTrue(gauge["gauge_visible"])
        self.assertIn("status", gauge)

    def test_optical_user_presence(self):
        """Verifies user facial presence detection."""
        presence = optical_inspection.detect_user_presence()
        self.assertIn("user_present", presence)

    def test_optical_voice_intents(self):
        """Verifies voice intents for camera inspection."""
        handled_i, resp_i = local_intelligence.evaluate_and_execute("inspect extinguisher camera")
        self.assertTrue(handled_i)
        self.assertIn("optical camera inspection", resp_i.lower())

        handled_g, resp_g = local_intelligence.evaluate_and_execute("check pressure gauge")
        self.assertTrue(handled_g)
        self.assertIn("manometer", resp_g.lower())

    # ─────────────────────────────────────────────────────────────────────
    # Area 4: Advanced Multi-Agent Workflow Mesh
    # ─────────────────────────────────────────────────────────────────────
    def test_multi_agent_mesh_execution(self):
        """Verifies cooperative multi-agent execution and consensus synthesis."""
        mission = "Prepare full safety compliance package for Ambattur automotive facility"
        m_res = multi_agent_mesh.execute_mesh_mission(mission)
        self.assertIn("reports", m_res)
        self.assertIn("LeadProspector", m_res["reports"])
        self.assertIn("EngineeringCompliance", m_res["reports"])
        self.assertIn("FinancialEstimator", m_res["reports"])
        self.assertIn("CodeSentinel", m_res["reports"])
        self.assertIn("synthesis", m_res)

    def test_multi_agent_voice_intent(self):
        """Verifies voice intent for multi-agent mesh execution."""
        handled, resp = local_intelligence.evaluate_and_execute("run agent mesh for Oragadam plant")
        self.assertTrue(handled)
        self.assertIn("multi-agent mission complete", resp.lower())

    # ─────────────────────────────────────────────────────────────────────
    # Area 5: Holographic HUD Telemetry & Auditory Experience
    # ─────────────────────────────────────────────────────────────────────
    def test_hud_telemetry_gathering(self):
        """Verifies HUD telemetry matrix aggregation."""
        t = hud_telemetry.get_live_hud_telemetry()
        self.assertIn("hardware", t)
        self.assertIn("cognitive", t)
        self.assertIn("commercial", t)
        self.assertIn("security", t)

    def test_hud_telemetry_voice_intent(self):
        """Verifies voice intent for HUD telemetry inquiry."""
        handled, resp = local_intelligence.evaluate_and_execute("hud telemetry status")
        self.assertTrue(handled)
        self.assertIn("holographic hud telemetry", resp.lower())

if __name__ == "__main__":
    unittest.main()
