"""
Unit tests for Final Batch Upgrades:
- SpreadsheetInjector
- B2BOutreachEngine
- AcousticShield
- OSEventSentinel
Strictly in English.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.spreadsheet_injector import SpreadsheetInjector
from tools.b2b_outreach_engine import B2BOutreachEngine
from core.acoustic_shield import AcousticShield
from core.os_event_sentinel import OSEventSentinel


class TestFinalUpgrades(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.injector = SpreadsheetInjector(output_dir=self.temp_dir)
        self.outreach = B2BOutreachEngine()
        self.outreach.EML_OUTPUT_DIR = self.temp_dir
        self.shield = AcousticShield()
        self.os_sentinel = OSEventSentinel()

    def test_spreadsheet_injector_csv_and_xml(self):
        """Verifies CSV and Excel XML spreadsheet generation with formula injection."""
        # 1. CSV test
        headers = ["Item", "Qty", "Price", "Total"]
        rows = [["ABC Powder 6kg", 2, 450, "=B2*C2"], ["CO2 Gas 4.5kg", 1, 550, "=B3*C3"]]
        csv_path = self.injector.generate_csv_with_formulas("test_sheet.csv", headers, rows, ["Summary", "", "", "=SUM(D2:D3)"])
        self.assertTrue(csv_path.exists())
        csv_content = csv_path.read_text(encoding="utf-8")
        self.assertIn("=SUM(D2:D3)", csv_content)

        # 2. Excel XML test
        xml_path = self.injector.generate_excel_xml(
            "test_sheet.xml",
            "Pricing",
            ["Item", "Rate"],
            [["Extinguisher", 650], ["Valve", 150]],
            total_columns_with_sum=[1]
        )
        self.assertTrue(xml_path.exists())
        xml_content = xml_path.read_text(encoding="utf-8")
        self.assertIn("urn:schemas-microsoft-com:office:spreadsheet", xml_content)
        self.assertIn("=SUM(", xml_content)

        # 3. Quotation builder
        quote_path = self.injector.build_b2b_quotation_sheet("Acme Corp", [{"name": "Refill", "hsn": "8424", "qty": 4, "rate": 450.0}])
        self.assertTrue(quote_path.exists())

    def test_b2b_outreach_engine(self):
        """Verifies EML synthesis, WhatsApp link generation, and ledger tracking."""
        eml_path = self.outreach.build_eml_message(
            to_email="procurement@acmefabricators.in",
            company_name="Acme Fabricators",
            contact_person="Operations Director"
        )
        self.assertTrue(eml_path.exists())
        eml_bytes = eml_path.read_bytes()
        self.assertIn(b"Subject: Commercial Fire Safety", eml_bytes)
        self.assertIn(b"IS 2190", eml_bytes)

        # WhatsApp link
        wa_link = self.outreach.generate_whatsapp_link("+919876543210", "Acme Fabricators")
        self.assertIn("https://wa.me/+919876543210", wa_link)
        self.assertIn("IS%202190", wa_link)

        # Campaign history
        history = self.outreach.get_campaign_history(limit=5)
        self.assertGreater(len(history), 0)
        self.assertEqual(history[0]["company_name"], "Acme Fabricators")

    def test_acoustic_shield_and_chime(self):
        """Verifies procedural earcon chime generation and phonetic normalizer."""
        # Chime WAV generation
        wav_path = self.shield.generate_procedural_chime_wav(duration_sec=0.1)
        self.assertTrue(wav_path.exists())
        self.assertGreater(wav_path.stat().st_size, 500)

        # Phonetic expansion
        expanded = self.shield.expand_phonetics("Launch RPA task and inspect UIA tree.")
        self.assertIn("R P A", expanded)
        self.assertIn("U I A", expanded)

    def test_os_event_sentinel(self):
        """Verifies port auditing, peripheral tracking, and uptime inspection."""
        ports = self.os_sentinel.audit_listening_ports()
        self.assertIn("total_listening", ports)
        self.assertIn("status", ports)

        drives = self.os_sentinel.check_peripheral_storage_changes()
        self.assertIn("active_drives", drives)

        uptime = self.os_sentinel.get_system_uptime()
        self.assertIn("uptime_hours", uptime)
        self.assertGreater(uptime["uptime_hours"], 0)


if __name__ == "__main__":
    unittest.main()
