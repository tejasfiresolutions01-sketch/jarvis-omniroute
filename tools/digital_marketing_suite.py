"""
J.A.R.V.I.S. Master Digital Marketing Suite.
Unifies all 5 specialized marketing engines:
1. SEO & Local Search (seo_engine)
2. Paid Advertising PPC & Social (ads_engine)
3. Conversion Rate Optimization & Funnels (cro_engine)
4. Inbound Marketing & Video Scripts (inbound_engine)
5. Customer Nurture & Retention Drips (nurture_engine)
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
from tools.digital_marketing_seo import seo_engine
from tools.digital_marketing_ads import ads_engine
from tools.digital_marketing_cro import cro_engine
from tools.digital_marketing_inbound import inbound_engine
from tools.digital_marketing_nurture import nurture_engine

logger = logging.getLogger("DigitalMarketingSuite")

class DigitalMarketingSuite:
    """
    Central Controller for J.A.R.V.I.S. Digital Marketing Operations.
    """

    def __init__(self):
        self.seo = seo_engine
        self.ads = ads_engine
        self.cro = cro_engine
        self.inbound = inbound_engine
        self.nurture = nurture_engine

    def execute_full_marketing_stack(self, corridor: str = "Ambattur") -> Dict[str, Any]:
        """
        Executes a 360-degree digital marketing campaign package across all 5 engines.
        """
        logger.info(f"[Marketing Suite]: Generating 360-degree marketing package for {corridor}...")
        
        seo_res = self.seo.generate_on_page_seo("Fire Extinguisher Refilling", corridor)
        ads_res = self.ads.generate_google_search_ad(corridor)
        cro_res = self.cro.generate_landing_page_wireframe(corridor)
        inbound_res = self.inbound.generate_lead_magnet_checklist()
        nurture_res = self.nurture.generate_drip_sequence(f"{corridor} Manufacturing Facility")

        package = {
            "target_corridor": corridor,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "1_seo": seo_res,
            "2_ads": ads_res,
            "3_cro": cro_res,
            "4_inbound": inbound_res,
            "5_nurture": nurture_res
        }

        return package

    def format_suite_voice_summary(self, corridor: str = "Ambattur") -> str:
        """Articulate spoken summary of full marketing package."""
        return (
            f"Full-stack digital marketing campaign compiled for {corridor}, sir. "
            f"All 5 engines—SEO metadata, Google Search Ads, high-converting landing page wireframe, "
            f"IS 2190 compliance checklist lead magnet, and 4-stage retention drip sequence—are fully generated and ready."
        )

# Global singleton
marketing_suite = DigitalMarketingSuite()
