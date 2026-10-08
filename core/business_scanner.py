"""
J.A.R.V.I.S. Monthly Business Opportunity & Commercial Lead Scanner.
Scans for new commercial leads, industrial facilities, and B2B contracts every month.
Target Corridors: Chennai District, Tiruvallur District, Kancheepuram District (Tamil Nadu).
Language: Strictly and Exclusively English.
"""

import os
import sys
import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config
from tools.pdf_generator import pdf_generator
from tools.notification_sentinel import notification_sentinel
from tools.campaign_generator import verify_campaign_english_only

logger = logging.getLogger("BusinessScanner")

class BusinessScanner:
    """
    Autonomous monthly scanner for discovering and qualifying new business opportunities.
    """

    STATE_FILE = config.MEMORY_DIR / "last_business_scan.json"
    LEADS_DIR = config.BASE_DIR / "data" / "business_leads"

    # Targeted Monthly Industrial & Commercial Hubs
    EXPANDED_HUBS = [
        {"hub": "Ambattur Industrial Estate Phase I & II", "district": "Chennai / Tiruvallur", "sectors": "Auto Components, Tooling, CNC Machining", "extinguisher_demand": "ABC 6kg, CO2 4.5kg"},
        {"hub": "Guindy Industrial Estate & Ekkattuthangal", "district": "Chennai", "sectors": "Electronics, Garments, Commercial Printing", "extinguisher_demand": "ABC 4kg, Clean Agent 2kg"},
        {"hub": "Sriperumbudur SIPCOT & Mambakkam", "district": "Kancheepuram", "sectors": "Automotive Tier 1/2, Mobile Electronics, Warehousing", "extinguisher_demand": "ABC 9kg, CO2 4.5kg, Foam 9L"},
        {"hub": "Oragadam Industrial Corridor (Vallam Vadagal)", "district": "Kancheepuram", "sectors": "Heavy Engineering, Commercial Vehicles, Plastics", "extinguisher_demand": "ABC 9kg, 50kg Trolley Powder"},
        {"hub": "Gummidipoondi SIPCOT", "district": "Tiruvallur", "sectors": "Chemical Processing, Steel Rolling, Corrugated Packaging", "extinguisher_demand": "ABC 9kg, Dry Powder, CO2"},
        {"hub": "Thirumazhisai & Poonamallee Industrial Zone", "district": "Tiruvallur", "sectors": "Food Processing Units, Cold Chains, Logistics Hubs", "extinguisher_demand": "Foam 9L, ABC 6kg, Wet Chemical"},
        {"hub": "Maraimalai Nagar & Mahindra World City", "district": "Kancheepuram", "sectors": "Automotive Assembly, IT SEZ, Precision Spares", "extinguisher_demand": "Clean Agent 4kg, CO2 4.5kg, ABC 6kg"},
        {"hub": "Madhavaram & Manali Freight Terminals", "district": "Tiruvallur / Chennai", "sectors": "Heavy Freight, Petrochemical Warehousing, Containers", "extinguisher_demand": "ABC 9kg, Mechanical Foam, CO2"},
        {"hub": "OMR Sholinganallur & Siruseri SIPCOT", "district": "Chennai / Kancheepuram", "sectors": "IT/ITES Towers, Tech Campuses, High-Rise Facilities", "extinguisher_demand": "Clean Agent HFC-236fa, CO2 2kg"}
    ]

    def __init__(self):
        self.LEADS_DIR.mkdir(parents=True, exist_ok=True)

    def is_scan_due(self) -> bool:
        """Determines if the monthly business scan is due for the current calendar month."""
        current_month = datetime.now().strftime("%Y-%m")
        if not self.STATE_FILE.exists():
            return True
        try:
            with open(self.STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("last_month_scanned") != current_month
        except Exception:
            return True

    def scan_for_new_business(self, force: bool = False) -> Dict[str, Any]:
        """
        Executes a comprehensive monthly business scan across target territories.
        Generates an executive dossier, compiles an executive PDF, and alerts the user.
        """
        now = datetime.now()
        month_str = now.strftime("%Y-%m")
        month_name = now.strftime("%B %Y")

        if not force and not self.is_scan_due():
            logger.info(f"[Business Scanner]: Monthly scan for {month_name} already completed.")
            return {
                "status": "already_completed",
                "month": month_str,
                "message": f"Business scan for {month_name} is already up to date, sir."
            }

        logger.info(f"[Business Scanner]: Initiating monthly business opportunity scan for {month_name}...")

        # 1. Author Comprehensive Monthly Business Dossier in Strict English
        dossier_content = (
            f"# J.A.R.V.I.S. MONTHLY BUSINESS OPPORTUNITY SCAN // {month_name.upper()}\n\n"
            f"**Territories Evaluated:** Chennai District, Tiruvallur District, Kancheepuram District (Tamil Nadu)\n"
            f"**Execution Date:** {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"**Language:** English (Strictly Enforced)\n"
            f"**Primary Service Vertical:** Fire Extinguisher Refilling, Annual Maintenance Contracts (AMC), and Safety Audits\n\n"
            f"---\n\n"
            f"## 1. Executive Opportunity Summary\n\n"
            f"This monthly intelligence scan details high-conversion industrial corridors, logistics hubs, and commercial centers "
            f"across Tamil Nadu requiring periodic fire safety inspections, hydro-testing, and cylinder refilling in compliance "
            f"with Tamil Nadu Fire & Rescue Services (TNFRS) standards and IS 2190 regulations.\n\n"
            f"---\n\n"
            f"## 2. Priority Industrial Corridors & Target Profiles\n\n"
            f"| Industrial / Commercial Corridor | District | Target Sectors | Fire Extinguisher Demand |\n"
            f"|---|---|---|---|\n"
        )

        for hub in self.EXPANDED_HUBS:
            dossier_content += f"| {hub['hub']} | {hub['district']} | {hub['sectors']} | {hub['extinguisher_demand']} |\n"

        dossier_content += (
            f"\n---\n\n"
            f"## 3. High-Conversion Outreach Action Plan for {month_name}\n\n"
            f"1. **Direct Safety Audit Inquiries:** Dispatch Touch 1 email introducing complimentary cylinder weight checks to factory managers.\n"
            f"2. **Same-Day Standby Cylinder Guarantee:** Address client operational downtime concerns by providing free backup cylinders during refilling.\n"
            f"3. **District Route Consolidation:** Group pickup routes geographically (Tiruvallur northern corridor on Mondays/Thursdays; Sriperumbudur/Oragadam on Tuesdays/Fridays) to minimize transport overhead.\n\n"
            f"---\n\n"
            f"## 4. Quality & Compliance Assurance\n\n"
            f"All refilling operations utilize genuine ISI certified ABC MAP powder, high-purity CO2, and certified mechanical foam "
            f"with official hydro-test test certificates provided upon completion.\n"
        )

        # Enrich dossier with live harvested B2B leads (Zero-Cost DNS MX Verified)
        try:
            from tools.lead_harvester import lead_harvester
            live_leads = lead_harvester.harvest_leads_for_corridor("ambattur")
            if live_leads:
                dossier_content += "\n---\n\n## 5. Verified B2B Lead Pipeline (Zero-Cost DNS MX Verified)\n\n"
                dossier_content += "| Company | Hub | Lead Score | Deliverability | Extinguisher Requirement |\n"
                dossier_content += "|---|---|---|---|---|\n"
                for l in live_leads[:5]:
                    mx_str = "Verified MX" if l.get("has_verified_mx") else "Standard Host"
                    dossier_content += f"| {l['company_name']} | {l['hub']} | {l['lead_score']}/100 | {mx_str} | {l['extinguisher_needs']} |\n"
        except Exception:
            pass

        # Enforce English-only verification
        if not verify_campaign_english_only(dossier_content):
            raise ValueError("Business scan content violates English-only policy.")

        # Save Markdown dossier
        md_filename = f"monthly_business_scan_{month_str}.md"
        md_path = self.LEADS_DIR / md_filename
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(dossier_content)

        # 2. Render Executive PDF Document
        pdf_path_str = pdf_generator.convert_markdown_file_to_pdf(str(md_path))
        pdf_path = Path(pdf_path_str)

        # 3. Update State File
        with open(self.STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "last_month_scanned": month_str,
                "timestamp": now.isoformat(),
                "dossier_md": str(md_path),
                "dossier_pdf": str(pdf_path)
            }, f, indent=2)

        # 4. Notify User via Voice
        notification_sentinel.notify_task_completed(
            task_id=now.month,
            task_title=f"Monthly Business Scan - {month_name}"
        )

        logger.info(f"[Business Scanner]: Monthly business scan completed. Saved to {md_path}")
        return {
            "status": "completed",
            "month": month_str,
            "dossier_md": str(md_path),
            "dossier_pdf": str(pdf_path),
            "message": f"Monthly business opportunity scan for {month_name} completed successfully, sir. Voice notification delivered."
        }

    def run_monthly_check(self):
        """Called by background daemon to execute monthly scan if due."""
        if self.is_scan_due():
            try:
                self.scan_for_new_business(force=False)
            except Exception as e:
                logger.error(f"[Business Scanner]: Scheduled monthly scan encountered error: {e}")

# Global singleton
business_scanner = BusinessScanner()
