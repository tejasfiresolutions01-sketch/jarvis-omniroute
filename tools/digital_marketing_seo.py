"""
J.A.R.V.I.S. Digital Marketing Suite - Module 1: Search Engine Optimization & Local SEO.
Features:
1. High-Intent Commercial Keyword Research: Targets fire extinguisher refilling, hydro-testing,
   and AMC contracts across Tamil Nadu industrial districts.
2. Complete On-Page SEO Generator: Title tags (<60 chars), meta descriptions (<160 chars),
   structured H1/H2 headers, canonical tags, and OpenGraph metadata.
3. Schema Markup Generator: Rich JSON-LD LocalBusiness & FireProtectionService structured data.
4. Google Business Profile (GBP) Post Generator: Weekly local update posts with direct calls-to-action.
5. Local Corridor Landing Page Architecture: Geotargeted page content for industrial corridors.
Strictly in English.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config

logger = logging.getLogger("DigitalMarketingSEO")

# High-Intent Keyword Repository for Tamil Nadu Industrial Markets
CORE_B2B_KEYWORDS = {
    "refilling": [
        {"keyword": "fire extinguisher refilling near me", "intent": "Transactional / Local", "volume": "High"},
        {"keyword": "fire extinguisher refilling in chennai", "intent": "Transactional / Commercial", "volume": "High"},
        {"keyword": "IS 2190 fire extinguisher refilling", "intent": "Commercial B2B", "volume": "Medium"},
        {"keyword": "co2 fire extinguisher refilling sriperumbudur", "intent": "Local B2B", "volume": "Medium"},
        {"keyword": "abc dry powder refilling ambattur", "intent": "Local B2B", "volume": "Medium"},
        {"keyword": "fire extinguisher refilling cost per kg", "intent": "Commercial Research", "volume": "Medium"}
    ],
    "hydro_test": [
        {"keyword": "fire extinguisher hydro test certificate", "intent": "Commercial Compliance", "volume": "High"},
        {"keyword": "cylinder hydrostatic pressure testing chennai", "intent": "Commercial B2B", "volume": "Medium"},
        {"keyword": "IS 2190 hydrostatic test frequency", "intent": "Informational Compliance", "volume": "Medium"}
    ],
    "amc_audit": [
        {"keyword": "fire safety AMC contract chennai", "intent": "Commercial B2B", "volume": "High"},
        {"keyword": "factory fire audit for TNFRS NOC", "intent": "Commercial B2B", "volume": "High"},
        {"keyword": "industrial fire protection services oragadam", "intent": "Local B2B", "volume": "Medium"}
    ]
}

class DigitalMarketingSEO:
    """
    Search Engine Optimization & Local Search Engine.
    """

    def generate_keyword_research(self, category: str = "all") -> Dict[str, Any]:
        """Returns structured keyword target list categorized by search intent."""
        cat = category.lower().strip()
        if cat in CORE_B2B_KEYWORDS:
            keywords = CORE_B2B_KEYWORDS[cat]
        else:
            keywords = [kw for group in CORE_B2B_KEYWORDS.values() for kw in group]

        return {
            "category": category,
            "total_keywords": len(keywords),
            "keywords": keywords,
            "recommended_primary": keywords[0]["keyword"] if keywords else "fire extinguisher refilling in chennai"
        }

    def generate_on_page_seo(self, service: str = "Fire Extinguisher Refilling", location: str = "Chennai") -> Dict[str, Any]:
        """
        Generates strict character-optimized on-page metadata.
        Title tag <= 60 characters, Meta Description <= 160 characters.
        """
        title = f"{service} in {location} | IS 2190 Certified | TFS"
        if len(title) > 60:
            title = f"{service} {location} | Certified | TFS"[:60]

        description = (
            f"Certified {service.lower()} in {location}. Compliant with IS 2190 & TNFRS regulations. "
            f"Same-day pickup, free standby cylinders, and official hydro-test reports."
        )
        if len(description) > 160:
            description = description[:157] + "..."

        h1 = f"Certified {service} Across {location} & Industrial Parks"
        h2_tags = [
            f"Why Choose Tejas Fire Solutions for {service}?",
            "IS 2190 Compliant Refilling & Hydro-Testing Standards",
            "Free Standby Cylinders & Same-Day Industrial Pickup",
            f"Service Corridors: Ambattur, Sriperumbudur, Oragadam & Guindy"
        ]

        return {
            "title_tag": title,
            "title_length": len(title),
            "meta_description": description,
            "description_length": len(description),
            "h1": h1,
            "h2_subheadings": h2_tags,
            "canonical_url": f"https://tejasfiresolutions.com/{service.lower().replace(' ', '-')}-{location.lower().replace(' ', '-')}"
        }

    def generate_local_business_schema(
        self,
        business_name: str = "Tejas Fire Solutions",
        phone: str = "+91-98400-00000",
        address: str = "Ambattur Industrial Estate, Chennai 600058",
        city: str = "Chennai"
    ) -> str:
        """
        Generates production-ready JSON-LD schema markup for LocalBusiness.
        """
        schema_dict = {
            "@context": "https://schema.org",
            "@type": "FireProtectionService",
            "name": business_name,
            "image": "https://tejasfiresolutions.com/assets/logo.png",
            "telephone": phone,
            "url": "https://tejasfiresolutions.com",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": address,
                "addressLocality": city,
                "addressRegion": "Tamil Nadu",
                "postalCode": "600058",
                "addressCountry": "IN"
            },
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": 13.0827,
                "longitude": 80.1550
            },
            "openingHoursSpecification": [
                {
                    "@type": "OpeningHoursSpecification",
                    "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                    "opens": "08:30",
                    "closes": "20:00"
                }
            ],
            "priceRange": "₹₹",
            "hasOfferCatalog": {
                "@type": "OfferCatalog",
                "name": "Fire Safety Services",
                "itemListElement": [
                    {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "ABC Dry Powder Refilling (IS 15683)"}},
                    {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "CO2 Cylinder Refilling & Hydro-Testing"}},
                    {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Annual Maintenance Contracts (IS 2190)"}}
                ]
            }
        }
        return json.dumps(schema_dict, indent=2)

    def generate_google_business_profile_post(self, topic: str = "Monsoon Fire Safety Check", corridor: str = "Ambattur") -> Dict[str, Any]:
        """
        Generates a Google Business Profile (GBP) update post with call to action.
        """
        content = (
            f"Are your industrial fire extinguishers certified for the current quarter? "
            f"Under IS 2190 standards, all manufacturing and warehouse units in {corridor} "
            f"must complete quarterly pressure checks and annual hydraulic testing.\n\n"
            f"Tejas Fire Solutions provides:\n"
            f"✔ Complimentary Onsite Weight & Pressure Inspection\n"
            f"✔ Genuine ISI Certified ABC & CO2 Refilling\n"
            f"✔ Standby Cylinders Provided Free During Servicing\n\n"
            f"Keep your facility 100% compliant and protected. Contact our {corridor} service team today."
        )
        return {
            "topic": topic,
            "corridor": corridor,
            "post_content": content,
            "call_to_action": "Call Now / Book Online",
            "character_count": len(content)
        }

    def format_voice_summary(self) -> str:
        """Articulate spoken summary of SEO optimizations."""
        return (
            "SEO and Local Search optimization matrix is primed, sir. "
            "High-intent commercial keywords, JSON-LD LocalBusiness schema, "
            "and geotargeted on-page metadata for Chennai industrial corridors are generated."
        )

# Global singleton
seo_engine = DigitalMarketingSEO()
