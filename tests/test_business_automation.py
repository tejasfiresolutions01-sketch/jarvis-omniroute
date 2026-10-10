"""
Unit tests for J.A.R.V.I.S. Enterprise Business Automation & Commercial Operations Engine.
Validates CRM pipeline, automated invoicing, P&L financial statements,
contract & SLA management, trigger-action workflow engine, and voice directive routing.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from core.local_intelligence import local_intelligence
from tools.business_automation_suite import BusinessAutomationSuite, business_automation_suite


class TestBusinessAutomationSuite(unittest.TestCase):

    def setUp(self):
        self.suite = business_automation_suite

    # ─────────────────────────────────────────────────────────────────────────
    # 1. CRM & Client Lifecycle Matrix
    # ─────────────────────────────────────────────────────────────────────────
    def test_client_creation_and_update(self):
        """Verifies onboarding new accounts and updating existing client profiles."""
        client_name = "Apex Aerospace Engineering"
        res = self.suite.create_or_update_client(
            name=client_name,
            company="Apex Aerospace Ltd",
            email="contracts@apex-aero.com",
            phone="+91-44-2828-1122",
            stage="Lead",
            deal_value=75000.0,
            industry="Aerospace & Defense",
        )
        self.assertTrue(res["success"])
        self.assertIn("client", res)
        client = res["client"]
        self.assertEqual(client["name"], client_name)
        self.assertEqual(client["deal_value"], 75000.0)

        # Retrieve client
        fetched = self.suite.get_client(client_name)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["email"], "contracts@apex-aero.com")

        # Update client
        res_update = self.suite.create_or_update_client(
            name=client_name,
            deal_value=90000.0,
        )
        self.assertTrue(res_update["success"])
        self.assertFalse(res_update["is_new"])
        updated = self.suite.get_client(client_name)
        self.assertEqual(updated["deal_value"], 90000.0)

    def test_advance_client_stage(self):
        """Verifies moving an account through the pipeline stages."""
        c_name = "Titanium Foundry Works"
        self.suite.create_or_update_client(name=c_name, stage="Lead", deal_value=45000.0)

        res = self.suite.advance_client_stage(c_name, "Qualified")
        self.assertTrue(res["success"])
        self.assertEqual(res["new_stage"], "Qualified")

        # Test invalid stage rejection
        res_invalid = self.suite.advance_client_stage(c_name, "NonExistentStage")
        self.assertFalse(res_invalid["success"])
        self.assertIn("Invalid stage", res_invalid["error"])

    def test_list_clients_filtered(self):
        """Verifies querying clients with stage and deal value thresholds."""
        self.suite.create_or_update_client(name="Filter Client A", stage="Discovery", deal_value=20000.0)
        self.suite.create_or_update_client(name="Filter Client B", stage="Negotiation", deal_value=120000.0)

        high_value = self.suite.list_clients(min_value=50000.0)
        names = [c["name"] for c in high_value]
        self.assertIn("Filter Client B", names)
        self.assertNotIn("Filter Client A", names)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Invoicing, Billing & Accounting Engine
    # ─────────────────────────────────────────────────────────────────────────
    def test_create_invoice_tax_and_totals(self):
        """Verifies itemized invoice creation and tax computation."""
        items = [
            {"description": "Industrial Fire Extinguisher Refilling 6kg", "quantity": 10, "unit_rate": 850.0},
            {"description": "Hydrostatic Pressure Testing Certification", "quantity": 5, "unit_rate": 200.0},
        ]
        # Subtotal: (10 * 850) + (5 * 200) = 8500 + 1000 = 9500.0
        # Tax 18%: 9500 * 0.18 = 1710.0
        # Total: 9500 + 1710 = 11210.0
        res = self.suite.create_invoice(
            client_name="OmniCorp Logistics",
            line_items=items,
            tax_rate_pct=18.0,
            discount_amount=210.0,
        )
        self.assertTrue(res["success"])
        inv = res["invoice"]
        self.assertEqual(inv["subtotal"], 9500.0)
        self.assertEqual(inv["tax_amount"], 1710.0)
        self.assertEqual(inv["total_amount"], 11000.0)  # 11210 - 210 = 11000
        self.assertEqual(inv["status"], "Sent")

    def test_record_payment_and_reconciliation(self):
        """Verifies partial and complete payment logging."""
        inv_res = self.suite.create_invoice(
            client_name="Stark Port Facility",
            line_items=[{"description": "Consulting & Safety Audit", "quantity": 1, "unit_rate": 10000.0}],
            tax_rate_pct=0.0,
        )
        inv = inv_res["invoice"]
        inv_num = inv["invoice_number"]

        # Partial Payment
        pay1 = self.suite.record_payment(inv_num, 4000.0)
        self.assertTrue(pay1["success"])
        self.assertEqual(pay1["status"], "Partial")
        self.assertEqual(pay1["outstanding_balance"], 6000.0)

        # Full Payment Settlement
        pay2 = self.suite.record_payment(inv_num, 6000.0)
        self.assertTrue(pay2["success"])
        self.assertEqual(pay2["status"], "Paid")
        self.assertEqual(pay2["outstanding_balance"], 0.0)

    def test_expenses_and_pnl_statement(self):
        """Verifies expense tracking and Profit & Loss report generation."""
        self.suite.log_expense(category="Operations", description="Workshop consumables", amount=2500.0)
        self.suite.log_expense(category="Software", description="Local cloud backup server", amount=1500.0)

        pnl = self.suite.get_financial_pnl()
        self.assertIn("realized_revenue", pnl)
        self.assertIn("total_expenses", pnl)
        self.assertIn("net_operating_profit", pnl)
        self.assertGreaterEqual(pnl["total_expenses"], 4000.0)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Contract & SLA Monitoring (AMCs, Retainers)
    # ─────────────────────────────────────────────────────────────────────────
    def test_contract_creation_and_expirations(self):
        """Verifies contract lifecycle and expiry window detection."""
        c_res = self.suite.create_contract(
            client_name="Global Steel Works",
            title="Annual Maintenance Contract (Plant Alpha)",
            value=120000.0,
            duration_days=15,  # Expiring soon
            service_type="AMC",
            sla_hours=12,
        )
        self.assertTrue(c_res["success"])
        cnt_id = c_res["contract_number"]

        # Detect expiring within 30 days
        expiring = self.suite.check_expiring_contracts(days_ahead=30)
        self.assertGreater(len(expiring), 0)
        exp_numbers = [c["contract_number"] for c in expiring]
        self.assertIn(cnt_id, exp_numbers)

        # Renew contract
        renew_res = self.suite.renew_contract(cnt_id, extension_days=365, new_value=135000.0)
        self.assertTrue(renew_res["success"])
        self.assertEqual(renew_res["value"], 135000.0)

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Trigger-Condition-Action Workflow Automation Engine
    # ─────────────────────────────────────────────────────────────────────────
    def test_workflow_execution_and_audit_logging(self):
        """Verifies event trigger execution and audit trail recording."""
        custom_event = "on_test_dispatch"
        self.suite.register_workflow(
            name="Test Auto Notification Workflow",
            trigger_event=custom_event,
            conditions={},
            actions=[{"type": "notify", "message": "Automated test notification triggered successfully."}],
        )

        results = self.suite.trigger_event(custom_event, {"source": "unit_test", "deal_value": 10000.0})
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["workflow_name"], "Test Auto Notification Workflow")
        self.assertEqual(results[0]["actions_executed"], 1)

        # Verify audit history
        history = self.suite.get_workflow_history(limit=5)
        self.assertGreater(len(history), 0)
        self.assertEqual(history[0]["trigger_event"], custom_event)

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Multi-Channel B2B Outreach Cadence
    # ─────────────────────────────────────────────────────────────────────────
    def test_outreach_cadence_generation(self):
        """Verifies structured 4-touchpoint communication synthesis."""
        res = self.suite.generate_outreach_cadence(
            client_name="Vikram Mehta",
            company="Mehta Heavy Forgings",
            industry="Automotive Stamping",
            deal_value=85000.0,
        )
        self.assertTrue(res["success"])
        cadence = res["cadence"]
        self.assertEqual(cadence["client_name"], "Vikram Mehta")
        self.assertEqual(len(cadence["touchpoints"]), 4)
        days = [t["day"] for t in cadence["touchpoints"]]
        self.assertEqual(days, [1, 3, 7, 14])

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Executive Business Intelligence Briefing
    # ─────────────────────────────────────────────────────────────────────────
    def test_business_intelligence_dashboard(self):
        """Verifies aggregated commercial KPIs and vocal executive summary."""
        bi = self.suite.get_business_intelligence()
        self.assertIn("crm_pipeline", bi)
        self.assertIn("invoicing", bi)
        self.assertIn("contracts", bi)
        self.assertIn("financial_pnl", bi)

        briefing = self.suite.format_executive_briefing()
        self.assertIn("Executive Commercial Briefing", briefing)
        self.assertIn("pipeline", briefing.lower())

    # ─────────────────────────────────────────────────────────────────────────
    # 7. Local Intelligence Routing & Skill 15 Integration
    # ─────────────────────────────────────────────────────────────────────────
    def test_local_intelligence_skill_15_directives(self):
        """Verifies voice and text command handling in local intelligence."""
        # 1. Status
        h1, res1 = local_intelligence.evaluate_and_execute("business automation status")
        self.assertTrue(h1)
        self.assertIn("Business Automation Suite online", res1)

        # 2. Executive Briefing
        h2, res2 = local_intelligence.evaluate_and_execute("business intelligence")
        self.assertTrue(h2)
        self.assertIn("Executive Commercial Briefing", res2)

        # 3. Financial P&L
        h3, res3 = local_intelligence.evaluate_and_execute("financial pnl")
        self.assertTrue(h3)
        self.assertIn("P&L Financial Report", res3)

        # 4. Onboard Client
        h4, res4 = local_intelligence.evaluate_and_execute("onboard client Dynamic Robotics company DynamicRobo email contact@dynamicrobo.com value 80000")
        self.assertTrue(h4)
        self.assertIn("client profile 'Dynamic Robotics'", res4)

        # 5. Advance Stage
        h5, res5 = local_intelligence.evaluate_and_execute("advance client Dynamic Robotics to Qualified")
        self.assertTrue(h5)
        self.assertIn("advanced from", res5)

        # 6. Invoicing
        h6, res6 = local_intelligence.evaluate_and_execute("create invoice Dynamic Robotics amount 50000 for Automation Engineering")
        self.assertTrue(h6)
        self.assertIn("Commercial invoice", res6)
        self.assertIn("Subtotal ₹50,000.00", res6)

        # 7. Contract Creation
        h7, res7 = local_intelligence.evaluate_and_execute("create contract Dynamic Robotics value 120000 title Annual Robotics AMC")
        self.assertTrue(h7)
        self.assertIn("active for Dynamic Robotics", res7)

        # 8. Expiring Contracts
        h8, res8 = local_intelligence.evaluate_and_execute("check expiring contracts")
        self.assertTrue(h8)

        # 9. Outreach Cadence
        h9, res9 = local_intelligence.evaluate_and_execute("generate outreach cadence for Dynamic Robotics")
        self.assertTrue(h9)
        self.assertIn("B2B Outreach Cadence generated", res9)

        # 10. List Workflows
        h10, res10 = local_intelligence.evaluate_and_execute("list business workflows")
        self.assertTrue(h10)
        self.assertIn("Tracking", res10)


if __name__ == "__main__":
    unittest.main()
