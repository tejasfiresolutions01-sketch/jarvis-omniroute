"""
Unit tests for Google Services (Maps, Gmail, Search Engine),
Executive PDF Document Generation, System Notifications, and Hologram Always-On.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from tools.google_services import google_services
from tools.pdf_generator import pdf_generator
from tools.notification_sentinel import notification_sentinel
from core.hologram_sentinel import hologram_sentinel
from core.local_intelligence import local_intelligence

class TestGoogleServices(unittest.TestCase):

    @patch("webbrowser.open")
    def test_search_maps(self, mock_browser):
        res = google_services.search_maps("Ambattur Industrial Estate", open_browser=True)
        self.assertIn("Ambattur Industrial Estate", res)
        mock_browser.assert_called_once()
        call_url = mock_browser.call_args[0][0]
        self.assertIn("google.com/maps/search", call_url)
        self.assertIn("Ambattur", call_url)

    @patch("webbrowser.open")
    def test_get_directions(self, mock_browser):
        res = google_services.get_directions("Chennai", "Sriperumbudur", travel_mode="driving", open_browser=True)
        self.assertIn("Chennai", res)
        self.assertIn("Sriperumbudur", res)
        mock_browser.assert_called_once()
        call_url = mock_browser.call_args[0][0]
        self.assertIn("google.com/maps/dir", call_url)
        self.assertIn("Sriperumbudur", call_url)

    @patch("webbrowser.open")
    def test_open_gmail(self, mock_browser):
        res = google_services.open_gmail()
        self.assertIn("Gmail Inbox", res)
        mock_browser.assert_called_once()
        self.assertIn("mail.google.com", mock_browser.call_args[0][0])

    @patch("webbrowser.open")
    def test_compose_email(self, mock_browser):
        res = google_services.compose_email(to="client@example.com", subject="Fire Extinguisher Refilling", body="Rate card attached", open_browser=True)
        self.assertIn("client@example.com", res)
        mock_browser.assert_called_once()
        call_url = mock_browser.call_args[0][0]
        self.assertIn("mail.google.com/mail/?", call_url)
        self.assertIn("client%40example.com", call_url)

    @patch("webbrowser.open")
    def test_search_google_browser(self, mock_browser):
        res = google_services.search_google("Tamil Nadu Fire NOC compliance", open_browser=True)
        mock_browser.assert_called_once()
        self.assertIn("google.com/search", mock_browser.call_args[0][0])
        self.assertIsInstance(res, list)

class TestPDFGenerator(unittest.TestCase):

    def test_generate_pdf_from_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            gen = pdf_generator.__class__(output_dir=tmp_path)
            content = (
                "# Test Autonomous Dossier\n\n"
                "**Executive Summary:** Testing ReportLab rendering.\n\n"
                "- Item 1: ABC Refilling\n"
                "- Item 2: Hydrostatic pressure test\n\n"
                "```text\nSample code or rate block\n```\n"
            )
            pdf = gen.generate_pdf(title="Executive Report", content=content, filename="test_output.pdf")
            self.assertTrue(pdf.exists())
            self.assertTrue(pdf.stat().st_size > 1000)

    def test_convert_markdown_file_to_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            md_file = tmp_path / "sample_campaign.md"
            md_file.write_text("# Fire Safety Campaign\n\nDetails here.", encoding="utf-8")

            gen = pdf_generator.__class__(output_dir=tmp_path)
            pdf = gen.convert_markdown_file_to_pdf(md_file)
            self.assertTrue(pdf.exists())
            self.assertEqual(pdf.suffix, ".pdf")

class TestNotificationSentinel(unittest.TestCase):

    @patch("subprocess.Popen")
    def test_notify(self, mock_popen):
        res = notification_sentinel.notify("J.A.R.V.I.S. Alert", "Task completed.")
        self.assertTrue(res)
        mock_popen.assert_called_once()

    @patch("subprocess.Popen")
    def test_notify_task_completed(self, mock_popen):
        res = notification_sentinel.notify_task_completed(42, "Refilling Outreach Campaign")
        self.assertTrue(res)
        mock_popen.assert_called_once()

class TestHologramAlwaysOn(unittest.TestCase):

    def test_always_on_toggle(self):
        hologram_sentinel.set_always_on(True)
        self.assertTrue(hologram_sentinel.always_on)

        # In always-on mode, regular hide_hologram should be rejected
        hidden = hologram_sentinel.hide_hologram(force=False)
        self.assertFalse(hidden)

        # Force hide should still work
        with patch.object(hologram_sentinel, "get_hud_hwnd", return_value=12345), \
             patch.object(hologram_sentinel.user32, "ShowWindow", return_value=1):
            force_hidden = hologram_sentinel.hide_hologram(force=True)
            self.assertTrue(force_hidden)

        hologram_sentinel.set_always_on(False)
        self.assertFalse(hologram_sentinel.always_on)

class TestLocalIntelligenceGoogleAndHologramIntents(unittest.TestCase):

    @patch("tools.google_services.google_services.open_gmail")
    def test_gmail_intent(self, mock_gmail):
        mock_gmail.return_value = "Opening your Gmail Inbox, sir."
        handled, resp = local_intelligence.evaluate_and_execute("open gmail")
        self.assertTrue(handled)
        self.assertIn("Gmail", resp)

    @patch("tools.google_services.google_services.compose_email")
    def test_gmail_compose_intent(self, mock_compose):
        mock_compose.return_value = "Opening Gmail compose draft, sir."
        handled, resp = local_intelligence.evaluate_and_execute("compose email to manager@factory.com about refilling quote")
        self.assertTrue(handled)
        mock_compose.assert_called_once()

    @patch("tools.google_services.google_services.search_maps")
    def test_google_maps_search_intent(self, mock_maps):
        mock_maps.return_value = "Opening Google Maps search for Ambattur, sir."
        handled, resp = local_intelligence.evaluate_and_execute("search maps for Ambattur")
        self.assertTrue(handled)
        self.assertIn("Ambattur", resp)

    @patch("tools.google_services.google_services.get_directions")
    def test_google_maps_directions_intent(self, mock_dir):
        mock_dir.return_value = "Calculating Google Maps navigation route, sir."
        handled, resp = local_intelligence.evaluate_and_execute("get directions from Chennai to Sriperumbudur")
        self.assertTrue(handled)
        self.assertIn("navigation", resp.lower())

    def test_hologram_always_on_intent(self):
        handled, resp = local_intelligence.evaluate_and_execute("run holographic interface all time")
        self.assertTrue(handled)
        self.assertIn("continuously at all times", resp)
        self.assertTrue(hologram_sentinel.always_on)

    def test_campaign_english_only_intent(self):
        handled, resp = local_intelligence.evaluate_and_execute("run campaigns only in english and not in any other language")
        self.assertTrue(handled)
        self.assertIn("English", resp)

    def test_campaign_generator_english_validation(self):
        from tools.campaign_generator import verify_campaign_english_only, generate_campaign_package
        self.assertTrue(verify_campaign_english_only("Hello Sir / Ma'am, this is from Tejas Fire Solutions."))
        self.assertFalse(verify_campaign_english_only("Vanakkam sir, this is from Tejas Fire Solutions."))
        md_path = generate_campaign_package()
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue(verify_campaign_english_only(content))
        self.assertNotIn("Vanakkam", content)

if __name__ == "__main__":
    unittest.main()

