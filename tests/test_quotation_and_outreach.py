import unittest
import os
import json
from pathlib import Path
from tools.quotation_engine import quotation_engine, STANDARD_CATALOG
from tools.digital_marketing_suite import marketing_suite
from core.local_intelligence import LocalIntelligence

class TestQuotationAndOutreach(unittest.TestCase):
    def setUp(self):
        self.loc_intel = LocalIntelligence()

    def test_quotation_creation_default_package(self):
        quote = quotation_engine.create_quotation(
            client_name="Tata Communications",
            facility_location="Ambattur Industrial Estate, Chennai",
            corridor="Ambattur",
            generate_pdf=True
        )

        self.assertIn("quote_id", quote)
        self.assertTrue(quote["quote_id"].startswith("TFS-QT-"))
        self.assertEqual(quote["client_name"], "Tata Communications")
        self.assertGreater(quote["subtotal"], 0)
        self.assertEqual(quote["gst_pct"], 18.0)
        self.assertEqual(quote["grand_total"], round(quote["taxable_amount"] + quote["gst_amount"], 2))
        
        # Verify JSON persistence
        json_path = Path(quote["json_path"])
        self.assertTrue(json_path.exists())
        with open(json_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data["quote_id"], quote["quote_id"])

        # Verify PDF creation
        self.assertIn("pdf_path", quote)
        pdf_path = Path(quote["pdf_path"])
        self.assertTrue(pdf_path.exists())
        self.assertTrue(pdf_path.name.endswith(".pdf"))
        with open(pdf_path, "rb") as f:
            header = f.read(5)
            self.assertEqual(header, b"%PDF-")

    def test_quotation_custom_items_and_discount(self):
        custom_items = [
            {"desc": "Clean Agent FK-5-1-12 Refilling 45kg", "qty": 2, "rate": 4500.0},
            {"desc": "CO2 Gas Cylinder Refilling 4.5kg", "qty": 10, "rate": 1200.0}
        ]
        quote = quotation_engine.create_quotation(
            client_name="Foxconn India",
            facility_location="Sriperumbudur Hi-Tech SEZ",
            items=custom_items,
            discount_pct=10.0,
            corridor="Sriperumbudur",
            generate_pdf=True
        )

        # 2*4500 = 9000; 10*1200 = 12000; Subtotal = 21000
        self.assertEqual(quote["subtotal"], 21000.0)
        self.assertEqual(quote["discount_amt"], 2100.0)
        self.assertEqual(quote["taxable_amount"], 18900.0)
        self.assertEqual(quote["gst_amount"], round(18900.0 * 0.18, 2))
        self.assertEqual(quote["grand_total"], round(18900.0 + (18900.0 * 0.18), 2))

    def test_multi_channel_outreach_generation(self):
        quote = quotation_engine.create_quotation(
            client_name="Saint-Gobain Glass",
            facility_location="Sriperumbudur",
            discount_pct=5.0
        )
        outreach = quotation_engine.generate_multi_channel_outreach(
            quote_data=quote,
            client_email="safety.head@saint-gobain.com",
            client_phone="+919840998877"
        )

        # Email
        self.assertIn("email", outreach)
        self.assertTrue(outreach["email"]["mailto_url"].startswith("mailto:safety.head@saint-gobain.com"))
        self.assertIn(quote["quote_id"], outreach["email"]["subject"])

        # WhatsApp
        self.assertIn("whatsapp", outreach)
        self.assertTrue(outreach["whatsapp"]["click_to_chat_url"].startswith("https://wa.me/919840998877"))
        self.assertIn(quote["quote_id"], outreach["whatsapp"]["message_text"])

        # SMS
        self.assertIn("sms", outreach)
        self.assertLessEqual(outreach["sms"]["length"], 160)
        self.assertIn(quote["quote_id"], outreach["sms"]["text"])

        # Cadence
        self.assertIn("cadence", outreach)
        self.assertEqual(len(outreach["cadence"]), 3)
        self.assertEqual(outreach["cadence"][0]["day"], 1)
        self.assertEqual(outreach["cadence"][1]["day"], 3)
        self.assertEqual(outreach["cadence"][2]["day"], 7)

    def test_voice_summary_articulation(self):
        quote = quotation_engine.create_quotation(
            client_name="Lucas TVS",
            facility_location="Padi, Chennai"
        )
        summary = quotation_engine.format_voice_summary(quote)
        self.assertIn("Commercial quotation", summary)
        self.assertIn(quote["quote_id"], summary)
        self.assertIn("Lucas TVS", summary)
        self.assertIn("18% GST", summary)

    def test_digital_marketing_commercial_stack(self):
        res = marketing_suite.execute_commercial_outreach_stack(
            client_name="Hyundai Mobis",
            corridor="Sriperumbudur",
            client_email="vendor.mgmt@hyundai.com",
            client_phone="+919840112233"
        )
        self.assertEqual(res["client_name"], "Hyundai Mobis")
        self.assertIn("marketing_stack", res)
        self.assertIn("1_seo", res["marketing_stack"])
        self.assertIn("2_ads", res["marketing_stack"])
        self.assertIn("3_cro", res["marketing_stack"])
        self.assertIn("4_inbound", res["marketing_stack"])
        self.assertIn("5_nurture", res["marketing_stack"])
        self.assertIn("quotation", res)
        self.assertIn("outreach", res)
        self.assertIn("voice_summary", res)

    def test_local_intelligence_quotation_directive(self):
        handled, resp = self.loc_intel.evaluate_and_execute("generate commercial quotation for Ashok Leyland in Ennore")
        self.assertTrue(handled)
        self.assertIn("Commercial quotation TFS-QT-", resp)
        self.assertIn("Ashok Leyland", resp)

    def test_local_intelligence_outreach_directive(self):
        handled, resp = self.loc_intel.evaluate_and_execute("generate commercial outreach for Royal Enfield in Oragadam")
        self.assertTrue(handled)
        self.assertIn("Commercial quotation TFS-QT-", resp)
        self.assertIn("Royal Enfield", resp)


if __name__ == "__main__":
    unittest.main()
