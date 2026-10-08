"""
Unit tests for the J.A.R.V.I.S. Digital Marketing Suite:
1. Module 1: SEO & Local Search Engine (seo_engine)
2. Module 2: Paid Ads PPC & Social (ads_engine)
3. Module 3: Conversion Rate Optimization & Funnels (cro_engine)
4. Module 4: Inbound Marketing & Video Scripts (inbound_engine)
5. Module 5: Customer Nurture & Retention Drips (nurture_engine)
6. Master Orchestrator (marketing_suite)
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.digital_marketing_seo import seo_engine
from tools.digital_marketing_ads import ads_engine
from tools.digital_marketing_cro import cro_engine
from tools.digital_marketing_inbound import inbound_engine
from tools.digital_marketing_nurture import nurture_engine
from tools.digital_marketing_suite import marketing_suite
from core.local_intelligence import local_intelligence

class TestDigitalMarketingSuite(unittest.TestCase):
    """Verifies all 5 specialized digital marketing engines and master suite."""

    # ─────────────────────────────────────────────────────────────────────
    # Module 1: SEO & Local SEO
    # ─────────────────────────────────────────────────────────────────────
    def test_seo_keywords_and_onpage(self):
        """Verifies SEO keyword research and strict character lengths."""
        kw_data = seo_engine.generate_keyword_research()
        self.assertGreater(kw_data["total_keywords"], 0)

        onpage = seo_engine.generate_on_page_seo("Fire Extinguisher Refilling", "Ambattur")
        self.assertLessEqual(onpage["title_length"], 60)
        self.assertLessEqual(onpage["description_length"], 160)
        self.assertIn("Ambattur", onpage["h1"])

    def test_seo_schema_and_gbp(self):
        """Verifies LocalBusiness JSON-LD schema and GBP posts."""
        schema_str = seo_engine.generate_local_business_schema()
        self.assertIn("FireProtectionService", schema_str)
        self.assertIn("Tejas Fire Solutions", schema_str)

        gbp = seo_engine.generate_google_business_profile_post("Safety Check", "Sriperumbudur")
        self.assertIn("Sriperumbudur", gbp["post_content"])
        self.assertIn("Call Now", gbp["call_to_action"])

    # ─────────────────────────────────────────────────────────────────────
    # Module 2: Paid Ads (Google RSA, Meta, LinkedIn)
    # ─────────────────────────────────────────────────────────────────────
    def test_google_rsa_ad_limits(self):
        """Verifies Google Search RSA rules (15 headlines <= 30 chars, 4 descriptions <= 90 chars)."""
        ad = ads_engine.generate_google_search_ad("Guindy")
        self.assertEqual(ad["headlines_count"], 15)
        for h in ad["headlines"]:
            self.assertLessEqual(len(h), 30)

        self.assertEqual(ad["descriptions_count"], 4)
        for d in ad["descriptions"]:
            self.assertLessEqual(len(d), 90)

        self.assertGreater(ad["negative_keywords_count"], 5)

    def test_meta_and_linkedin_ads(self):
        """Verifies Meta direct-response lead ads and LinkedIn B2B authority copy."""
        meta_ad = ads_engine.generate_meta_ad_campaign("Oragadam")
        self.assertIn("Oragadam", meta_ad["primary_text"])
        self.assertEqual(len(meta_ad["carousel_cards"]), 4)

        li_ad = ads_engine.generate_linkedin_b2b_ad()
        self.assertIn("IS 2190:2010", li_ad["introductory_text"])

    # ─────────────────────────────────────────────────────────────────────
    # Module 3: Conversion Rate Optimization (CRO & Funnels)
    # ─────────────────────────────────────────────────────────────────────
    def test_cro_wireframe_and_ab_tests(self):
        """Verifies high-converting landing page elements and A/B split test designs."""
        cro = cro_engine.generate_landing_page_wireframe("Chennai")
        self.assertIn("hero_section", cro)
        self.assertTrue(any("IS 2190" in b for b in cro["hero_section"]["trust_badges"]))
        self.assertEqual(len(cro["objection_busters"]), 3)

        tests = cro_engine.generate_ab_split_tests()
        self.assertEqual(len(tests), 3)
        self.assertIn("EXP-01-HEADLINE", tests[0]["test_id"])

    # ─────────────────────────────────────────────────────────────────────
    # Module 4: Inbound Content & Video Scripts
    # ─────────────────────────────────────────────────────────────────────
    def test_inbound_lead_magnet_and_video(self):
        """Verifies downloadable compliance checklist and short-form video scripts."""
        lead_magnet = inbound_engine.generate_lead_magnet_checklist()
        self.assertEqual(len(lead_magnet["checklist_points"]), 10)
        self.assertIn("Tamil Nadu Industrial Fire Safety", lead_magnet["lead_magnet_title"])

        videos = inbound_engine.generate_video_scripts()
        self.assertIn("Comment 'AUDIT'", videos["short_script_30s"])
        self.assertIn("CO2 cylinders don't have pressure gauges", videos["full_script_60s"])

    # ─────────────────────────────────────────────────────────────────────
    # Module 5: Customer Nurture & Retention
    # ─────────────────────────────────────────────────────────────────────
    def test_nurture_drip_sequence_and_review(self):
        """Verifies 4-stage post-service drip sequence and review scripts."""
        drips = nurture_engine.generate_drip_sequence("Apex Auto", "2026-10-08")
        self.assertEqual(len(drips), 4)
        self.assertIn("Touch 1", drips[0]["stage"])
        self.assertIn("Annual Renewal", drips[3]["stage"])

        rev = nurture_engine.generate_review_request_whatsapp("Apex Auto")
        self.assertTrue("g.page" in rev.lower() or "google" in rev.lower())

    # ─────────────────────────────────────────────────────────────────────
    # Master Suite & Voice Directives
    # ─────────────────────────────────────────────────────────────────────
    def test_master_marketing_suite_execution(self):
        """Verifies full-stack marketing package aggregation."""
        pkg = marketing_suite.execute_full_marketing_stack("Gummidipoondi")
        self.assertIn("1_seo", pkg)
        self.assertIn("2_ads", pkg)
        self.assertIn("3_cro", pkg)
        self.assertIn("4_inbound", pkg)
        self.assertIn("5_nurture", pkg)

    def test_marketing_voice_intents(self):
        """Verifies voice directives for digital marketing campaigns."""
        handled, resp = local_intelligence.evaluate_and_execute("run digital marketing campaign for Ambattur")
        self.assertTrue(handled)
        self.assertIn("digital marketing campaign", resp.lower())

        handled_s, resp_s = local_intelligence.evaluate_and_execute("seo recommendations")
        self.assertTrue(handled_s)
        self.assertIn("seo", resp_s.lower())

if __name__ == "__main__":
    unittest.main()
