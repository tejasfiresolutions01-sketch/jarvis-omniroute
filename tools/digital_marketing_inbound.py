"""
J.A.R.V.I.S. Digital Marketing Suite - Module 4: Inbound Marketing & Lead Magnets.
Features:
1. High-Value B2B Lead Magnet: Generates the 'Tamil Nadu Industrial Fire Safety & IS 2190 Compliance Checklist'
   which visitors download in exchange for contact details.
2. Short-Form Video Scripts: 30s and 60s viral educational scripts for LinkedIn, Instagram Reels, and YouTube Shorts.
3. Educational SEO Pillar Article: In-depth technical guides establishing market authority.
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

logger = logging.getLogger("DigitalMarketingInbound")

class DigitalMarketingInbound:
    """
    Inbound Content Marketing, Lead Magnets, and Video Scriptwriting Engine.
    """

    def generate_lead_magnet_checklist(self) -> Dict[str, Any]:
        """
        Generates comprehensive downloadable compliance checklist for factory EHS heads.
        """
        title = "Tamil Nadu Industrial Fire Safety & IS 2190 Audit Checklist (2026 Edition)"
        points = [
            "1. Cylinder Accessibility: Extinguishers mounted at 1.5m height with unobstructed 1-meter perimeter.",
            "2. Pressure Verification: Manometer needle verified dead-center within green operational quadrant (12-15 bar).",
            "3. Safety Tamper Seal: Wire seal and pull pin intact; no evidence of prior unauthorized discharge.",
            "4. Shell Corrosion & Dents: Zero mechanical deformations or corrosion pitting on bottom rim.",
            "5. Discharge Horn Inspection: Horn completely clear of spider webs, dust accumulation, or cracked rubber.",
            "6. Weight Audit (CO2 Cylinders): Gross weight logged; if loss exceeds 10% of tare weight, cylinder must be recharged.",
            "7. Hydrostatic Pressure Testing Stamp: Stamped test date verified within 3 years (ABC/Foam) or 5 years (CO2).",
            "8. Operating Instruction Legibility: Front decal and pictogram clear and readable from 2 meters.",
            "9. Maintenance Tag Sign-Off: Quarterly inspection punch tag signed by certified competent engineer.",
            "10. Standby Spare Ratio: Minimum 10% standby spare cylinders available on premises during off-site servicing."
        ]

        document = (
            f"# {title.upper()}\n\n"
            f"**Publisher:** Tejas Fire Solutions (Certified IS 2190 Service Station)\n"
            f"**Standard Reference:** IS 2190:2010 Code of Practice & TNFRS Guidelines\n\n"
            f"---\n\n"
            f"## Mandatory 10-Point Monthly Facility Inspection Protocol\n\n"
        )
        for p in points:
            document += f"- [ ] **{p}**\n\n"

        document += (
            f"---\n\n"
            f"### Need An Official Audit or Hydro-Testing For Your Facility?\n"
            f"Contact Tejas Fire Solutions for complimentary onsite inspections and certified refilling across Chennai, "
            f"Sriperumbudur, Oragadam, and Ambattur. Phone: +91-98400-00000 | Web: tejasfiresolutions.com\n"
        )

        return {
            "lead_magnet_title": title,
            "checklist_points": points,
            "document_markdown": document,
            "call_to_action": "Download Free PDF Checklist"
        }

    def generate_video_scripts(self) -> Dict[str, Any]:
        """
        Generates short-form video scripts for LinkedIn, Reels, and YouTube Shorts.
        """
        script_30s = (
            "Hook (0-5s): [Show close-up of fire extinguisher gauge in red] "
            "If your factory's fire extinguisher needle is here, you are one spark away from an audit failure or disaster.\n\n"
            "Body (5-20s): Stored-pressure extinguishers lose nitrogen pressure over time through micro-vibrations in industrial plants. "
            "Under IS 2190, if this needle drops out of the green zone, the powder won't discharge when you squeeze the trigger.\n\n"
            "Call-To-Action (20-30s): Don't wait for an inspection fine. Tejas Fire Solutions gives you free standby cylinders while we service yours. "
            "Comment 'AUDIT' below for a free facility inspection."
        )

        script_60s = (
            "Hook (0-8s): 3 things every plant manager in Chennai forgets before a fire safety audit.\n\n"
            "Point 1 (8-22s): First, CO2 cylinders don't have pressure gauges! The only way to know if your CO2 extinguisher is full is by weighing it. "
            "If it lost more than 10% of gas, it will fail inspection.\n\n"
            "Point 2 (22-38s): Second, hydrostatic pressure testing. Under IS 2190, cylinders must be pressure-tested with water every 3 to 5 years. "
            "Without an official hydro-test stamp, your insurance claim can be rejected.\n\n"
            "Point 3 (38-50s): Third, operational downtime. When you send extinguishers out for refilling, your factory floor is legally unprotected unless you have standby units.\n\n"
            "Outro (50-60s): That's why Tejas Fire Solutions places free backup cylinders at your plant before taking yours for service. "
            "Visit tejasfiresolutions.com to book your servicing route today."
        )

        return {
            "short_script_30s": script_30s,
            "full_script_60s": script_60s,
            "recommended_platforms": ["LinkedIn Video", "Instagram Reels", "YouTube Shorts"]
        }

    def format_voice_summary(self) -> str:
        """Articulate spoken summary of inbound marketing content."""
        return (
            "Inbound marketing materials are prepared, sir. "
            "A downloadable 10-point IS 2190 factory compliance checklist lead magnet "
            "and two viral short-form video scripts for LinkedIn and Reels are ready to deploy."
        )

# Global singleton
inbound_engine = DigitalMarketingInbound()
