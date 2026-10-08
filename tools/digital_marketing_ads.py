"""
J.A.R.V.I.S. Digital Marketing Suite - Module 2: Paid Advertising (PPC & Social Ads).
Features:
1. Google Search Ads (Responsive Search Ads): 15 headlines (<=30 chars), 4 descriptions (<=90 chars),
   callout extensions, and a high-converting negative keyword exclusion list.
2. Meta Ads (Facebook & Instagram): High-converting direct response hooks, carousel copy,
   and instant lead form fields.
3. LinkedIn Sponsored Content: Authoritative B2B ad copy targeting Plant Managers, EHS Directors,
   and Procurement Officers in industrial corridors.
Strictly in English.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config

logger = logging.getLogger("DigitalMarketingAds")

class DigitalMarketingAds:
    """
    Paid Search (PPC) and Social Advertising Campaign Engine.
    """

    NEGATIVE_KEYWORDS = [
        "free", "diy", "how to refill at home", "training jobs", "vacancy", "career",
        "internship", "wikipedia", "youtube", "ppt", "pdf download", "used second hand",
        "antique", "toy extinguisher"
    ]

    def generate_google_search_ad(self, corridor: str = "Chennai") -> Dict[str, Any]:
        """
        Generates compliant Google Responsive Search Ad (RSA) package.
        Headlines must be <= 30 chars, Descriptions must be <= 90 chars.
        """
        raw_headlines = [
            f"Fire Extinguisher Refilling",
            f"IS 2190 Refilling in {corridor}",
            f"Free Standby Cylinders",
            f"Same-Day Industrial Pickup",
            f"Certified Hydro-Testing",
            f"ABC & CO2 Cylinder Refill",
            f"TNFRS Audit Compliant",
            f"Factory Fire Safety AMC",
            f"Doorstep Cylinder Service",
            f"Tejas Fire Solutions",
            f"Save Up To 25% on Bulk Refill",
            f"Genuine ISI Certified MAP",
            f"100% Audit Ready Testing",
            f"Fast 24-Hour Turnaround",
            f"Get Free Onsite Inspection"
        ]

        # Enforce strict 30-char limit
        headlines = [h[:30] for h in raw_headlines]

        raw_descriptions = [
            f"Certified fire extinguisher refilling in {corridor}. Free pickup & standby cylinders.",
            "IS 2190 compliant hydro-testing & cylinder refilling. Protect your facility today.",
            "Genuine ISI certified ABC powder and high-purity CO2. Trusted by top factories.",
            "Ensure 100% TNFRS compliance. Call Tejas Fire Solutions now for a rapid quotation."
        ]

        # Enforce strict 90-char limit
        descriptions = [d[:90] for d in raw_descriptions]

        callouts = [
            "Free Standby Cylinders",
            "IS 2190 Certified",
            "Same-Day Pickup",
            "TNFRS Audit Ready",
            "Genuine ISI Powder",
            "1-Year Refilling Warranty"
        ]

        return {
            "campaign_type": "Google Search - Responsive Search Ad",
            "target_location": corridor,
            "headlines_count": len(headlines),
            "headlines": headlines,
            "descriptions_count": len(descriptions),
            "descriptions": descriptions,
            "callout_extensions": callouts,
            "negative_keywords_count": len(self.NEGATIVE_KEYWORDS),
            "negative_keywords": self.NEGATIVE_KEYWORDS
        }

    def generate_meta_ad_campaign(self, corridor: str = "Ambattur / Sriperumbudur") -> Dict[str, Any]:
        """
        Generates direct-response Facebook/Instagram ad copy and instant lead form config.
        """
        primary_text = (
            f"Attention Factory & Warehouse Managers in {corridor}: "
            f"Are your fire extinguishers due for mandatory annual refilling or hydro-testing?\n\n"
            f"Operating with expired or depressurized cylinders risks failed insurance audits "
            f"and severe TNFRS compliance fines. Tejas Fire Solutions keeps your premises 100% protected:\n\n"
            f"✅ Free Onsite Cylinder Weight & Pressure Inspection\n"
            f"✅ Temporary Standby Cylinders Provided At No Charge\n"
            f"✅ Genuine IS 2190 Certified Refilling & Hydro-Testing\n"
            f"✅ Same-Day Doorstep Pickup & Delivery\n\n"
            f"Click below to get an instant quote or book your complimentary inspection today!"
        )

        carousel_cards = [
            {"title": "ABC Powder Refilling", "description": "ISI MAP 50% powder starting at ₹450 / cylinder"},
            {"title": "High-Pressure CO2 Gas", "description": "Pure carbon dioxide refilling & 250 kg/cm2 testing"},
            {"title": "Annual Maintenance AMC", "description": "Quarterly weight checks & standby replacements"},
            {"title": "TNFRS Audit Certification", "description": "Official hydro-test test reports issued within 24 hours"}
        ]

        lead_form_fields = [
            "Full Name",
            "Company / Facility Name",
            "Industrial Location (e.g., Ambattur, Sriperumbudur)",
            "Estimated Extinguisher Count",
            "Phone Number / WhatsApp"
        ]

        return {
            "platform": "Meta Ads (Facebook & Instagram Feed + Stories)",
            "target_location": corridor,
            "headline": "Certified Fire Extinguisher Refilling | Free Standby Cylinders",
            "primary_text": primary_text,
            "cta_button": "Get Quote",
            "carousel_cards": carousel_cards,
            "lead_form_questions": lead_form_fields
        }

    def generate_linkedin_b2b_ad(self) -> Dict[str, Any]:
        """
        Generates authority-driven B2B LinkedIn sponsored content.
        """
        copy = (
            "Safety Directors & Plant Operations Heads across Tamil Nadu: "
            "How audit-ready is your plant's fire suppression infrastructure?\n\n"
            "Under IS 2190:2010 regulations, failure to maintain annual weight audits and "
            "5-year hydrostatic pressure logs can invalidate commercial insurance claims during a hazard.\n\n"
            "Tejas Fire Solutions provides industrial facilities with turnkey fire protection management:\n"
            "• End-to-end cylinder collection with zero operational downtime (free standby cylinders).\n"
            "• High-pressure certified hydrostatic testing and valve overhaul.\n"
            "• Standardized documentation compliant with Tamil Nadu Fire & Rescue Services (TNFRS).\n\n"
            "Download our Industrial Compliance Checklist or request an engineering consultation for your plant."
        )

        return {
            "platform": "LinkedIn Sponsored Content",
            "target_audience": "EHS Managers, Plant Heads, Facilities Directors, Safety Officers",
            "headline": "Turnkey IS 2190 Fire Safety Management for Manufacturing Plants",
            "introductory_text": copy,
            "cta": "Learn More / Request Audit"
        }

    def format_voice_summary(self) -> str:
        """Articulate spoken summary of advertising campaigns."""
        return (
            "Paid advertising engines are configured, sir. "
            "Google Responsive Search Ads with 15 headlines and negative keyword exclusions, "
            "Meta direct-response lead forms, and LinkedIn B2B authority copy are ready for deployment."
        )

# Global singleton
ads_engine = DigitalMarketingAds()
