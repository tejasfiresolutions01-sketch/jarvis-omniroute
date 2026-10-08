"""
J.A.R.V.I.S. Fire Safety B2B Campaign Generator.
Tailored for Chennai, Tiruvallur, and Kancheepuram districts (Tamil Nadu).
Generates:
1. High-converting B2B Cold Email Sequence (3 Touches: Audit Offer, Price Advantage, Compliance Reminder).
2. WhatsApp Rapid Follow-up scripts for Facility Managers.
3. Pre-targeted Industrial & Commercial Hub Prospect Directory (Ambattur, Guindy, Sriperumbudur, Oragadam, Gummidipoondi, Maraimalai Nagar).
4. Direct Mailto: 1-click sending links.
"""

import os
import sys
import csv
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config

TARGET_CORRIDORS = [
    {"name": "Ambattur Industrial Estate", "district": "Chennai / Tiruvallur", "type": "Light Engineering, SME, Auto Components"},
    {"name": "Guindy Industrial Estate", "district": "Chennai", "type": "Garments, Electronics, Plastics, Engineering"},
    {"name": "Sriperumbudur Industrial Hub", "district": "Kancheepuram", "type": "Automotive Tier 1/2, Electronics, Warehouses"},
    {"name": "Oragadam Industrial Corridor", "district": "Kancheepuram", "type": "Automobile, Heavy Engineering, Logistics"},
    {"name": "Gummidipoondi SIPCOT", "district": "Tiruvallur", "type": "Steel, Chemical, Packaging, Fabrication"},
    {"name": "Thirumazhisai Industrial Area", "district": "Tiruvallur", "type": "Warehouses, Food Processing, Engineering"},
    {"name": "Maraimalai Nagar & Mahindra World City", "district": "Kancheepuram", "type": "Automotive, IT, Logistics Parks"},
    {"name": "OMR & Guindy Tech Parks", "district": "Chennai", "type": "IT/ITES, Corporate Offices, Commercial Facilities"},
    {"name": "Koyambedu & Madhavaram Logistics Parks", "district": "Chennai / Tiruvallur", "type": "Cold Storage, Transport Warehousing"}
]

COLD_EMAIL_TEMPLATES = [
    {
        "touch": "Touch 1: The Fire NOC & Safety Audit Angle (Highest Response Rate)",
        "subject": "Quick question regarding [Company Name]'s fire extinguisher inspection & refilling",
        "body": (
            "Dear Facility / Safety Team at [Company Name],\n\n"
            "Under Tamil Nadu Fire & Rescue Services (TNFRS) and IS 2190:2010 norms, commercial premises "
            "require mandatory annual servicing and pressure testing of all portable fire extinguishers.\n\n"
            "We are conducting scheduled servicing routes across [District / Industrial Area] this week, and we can offer your facility:\n"
            "1. Complimentary On-site Inspection & Weight Check of all existing extinguishers.\n"
            "2. Genuine ISI-grade Refilling (ABC MAP Powder, CO2, Mechanical Foam, Clean Agent) at direct bulk rates.\n"
            "3. Temporary Standby Cylinders provided free during servicing so your premises remain 100% protected.\n"
            "4. Official Refilling Certificate & Hydro-Test Report for audit and insurance compliance.\n\n"
            "Would you be open to a complimentary 10-minute cylinder inspection tomorrow morning, or should I forward our refilling rate card for your review?\n\n"
            "Best regards,\n"
            "Tejas Fire Solutions\n"
            "Safety Division - Chennai | Tiruvallur | Kancheepuram\n"
            "Phone / WhatsApp: [Phone Number]\n"
            "Service Hub: Tamil Nadu"
        )
    },
    {
        "touch": "Touch 2: Direct Price & Same-Day Turnaround (Urgency)",
        "subject": "Fire extinguisher refilling with same-day pickup & standby cylinders in [Industrial Area]",
        "body": (
            "Hi [Facility Manager / Admin Lead],\n\n"
            "Following up on our earlier note. If you have fire extinguishers due for refilling or hydro-testing, "
            "we are currently offering same-day pickup and delivery across [District / Area].\n\n"
            "Our Rates Include:\n"
            "- ABC Dry Powder (1kg to 9kg) - Starting at ₹450 / cylinder\n"
            "- CO2 Cylinders (2kg, 4.5kg) - High-pressure certified\n"
            "- Foam / Clean Agent (HFC 236fa) - Industrial grade\n"
            "- New Discharge Horns, Seals & Pressure Gauges included where needed\n"
            "- Free pickup, doorstep delivery, and 1-year refilling warranty\n\n"
            "Can we dispatch a technician to service your units today or tomorrow morning?\n\n"
            "Best regards,\n"
            "Tejas Fire Solutions\n"
            "Contact: [Phone Number]"
        )
    },
    {
        "touch": "Touch 3: WhatsApp Instant Booking Script",
        "subject": "WhatsApp Direct Pitch",
        "body": (
            "Hello Sir / Ma'am, this is from Tejas Fire Solutions.\n"
            "We are currently servicing commercial & industrial units in your area ([Industrial Area]).\n"
            "Are any of your fire extinguishers (ABC / CO2 / Foam) due for refilling or annual expiry check?\n"
            "- Free Onsite Inspection\n"
            "- Standby cylinders provided\n"
            "- TNFRS Audit Compliant Certificate\n"
            "Reply with your cylinder count and location for an instant WhatsApp quotation!"
        )
    }
]

SAMPLE_PROSPECT_LEADS = [
    {"company": "Apex Auto Components Pvt Ltd", "contact": "Admin / Safety Officer", "area": "Ambattur Industrial Estate", "district": "Chennai", "email": "admin@apexauto.example.com", "target_extinguishers": "ABC 6kg, CO2 4.5kg"},
    {"company": "Sri Krishna Logistics & Warehousing", "contact": "Warehouse Operations Manager", "area": "Madhavaram", "district": "Tiruvallur", "email": "ops@krishnalogistics.example.com", "target_extinguishers": "ABC 9kg, Water Foam 9L"},
    {"company": "Oragadam Precision Engineering", "contact": "Plant Head / Maintenance", "area": "Oragadam Industrial Corridor", "district": "Kancheepuram", "email": "maintenance@oragadamprecision.example.com", "target_extinguishers": "CO2 4.5kg, ABC 6kg"},
    {"company": "Sriperumbudur Electronics Sub-Assembly", "contact": "EHS / Facilities Lead", "area": "Sriperumbudur SIPCOT", "district": "Kancheepuram", "email": "ehs@sriperumbudur-elec.example.com", "target_extinguishers": "Clean Agent 4kg, CO2 2kg"},
    {"company": "Gummidipoondi Steel & Fabrication", "contact": "Safety Incharge", "area": "Gummidipoondi SIPCOT", "district": "Tiruvallur", "email": "safety@gummidipoondisteel.example.com", "target_extinguishers": "ABC 9kg, Dry Powder 50kg Trolley"},
    {"company": "Vel Tech Fabrication & Spares", "contact": "Admin Officer", "area": "Thirumazhisai", "district": "Tiruvallur", "email": "admin@veltechfab.example.com", "target_extinguishers": "ABC 4kg, CO2 2kg"},
    {"company": "Grand Palace Hotel & Banquets", "contact": "General Manager", "area": "Guindy", "district": "Chennai", "email": "manager@grandpalacehotel.example.com", "target_extinguishers": "K-Class Wet Chemical, ABC 4kg"},
    {"company": "Maraimalai Nagar Tooling Corp", "contact": "Factory Manager", "area": "Maraimalai Nagar", "district": "Kancheepuram", "email": "factory@mmnagartooling.example.com", "target_extinguishers": "CO2 4.5kg, ABC 6kg"}
]

def verify_campaign_english_only(content: str) -> bool:
    """Verifies that no non-English regional greetings or foreign words appear in campaign copy."""
    forbidden_tokens = ["vanakkam", "namaste", "namaskaram", "kaalai vanakkam", "nandri", "dhanyavad"]
    content_lower = content.lower()
    for token in forbidden_tokens:
        if token in content_lower:
            return False
    return True

def generate_campaign_package(phone_number: str = "[Your Phone Number]", base_rate: str = "₹450") -> str:
    """Compiles the complete B2B campaign report and saves the prospect database."""
    out_dir = config.COMPLETED_TASKS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save prospect CSV
    csv_path = out_dir / "fire_extinguisher_leads_tn.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["company", "contact", "area", "district", "email", "target_extinguishers"])
        writer.writeheader()
        writer.writerows(SAMPLE_PROSPECT_LEADS)

    # 2. Save comprehensive Dossier
    dossier_path = out_dir / "fire_extinguisher_campaign_chennai_tiruvallur_kanchipuram.md"
    content = (
        f"# TEJAS FIRE SOLUTIONS // HIGH-CONVERSION B2B COLD CAMPAIGN\n\n"
        f"**Target Territories:** Chennai District, Tiruvallur District, Kancheepuram District (Tamil Nadu)\n"
        f"**Campaign Language:** English (Strictly Enforced)\n"
        f"**Goal:** Secure Fire Extinguisher Refilling Order before 11:30 AM\n"
        f"**Starting Rate:** {base_rate} / cylinder\n"
        f"**Contact Hotline / WhatsApp:** {phone_number}\n\n"
        f"---\n\n"
        f"## 1. High-Converting Email Sequences\n\n"
    )

    for tmpl in COLD_EMAIL_TEMPLATES:
        body_filled = tmpl["body"].replace("[Phone Number]", phone_number)
        content += (
            f"### {tmpl['touch']}\n"
            f"**Subject:** `{tmpl['subject']}`\n\n"
            f"```text\n{body_filled}\n```\n\n"
            f"---\n\n"
        )

    content += (
        f"## 2. Priority Industrial & Commercial Targets\n\n"
        f"| Corridor / Industrial Area | District | Target Industry Profile |\n"
        f"|---|---|---|\n"
    )
    for c in TARGET_CORRIDORS:
        content += f"| {c['name']} | {c['district']} | {c['type']} |\n"

    content += (
        f"\n---\n\n"
        f"## 3. Fast Action Playbook (To Close Before 11:30 AM)\n\n"
        f"1. **08:30 AM - 09:30 AM:** Dispatch Touch 1 email to Factory & Warehouse leads in Ambattur, Sriperumbudur, and Guindy.\n"
        f"2. **09:30 AM - 10:30 AM:** Send Touch 3 WhatsApp message to Facility Managers offering a *complimentary 10-minute onsite cylinder inspection* today.\n"
        f"3. **10:30 AM - 11:30 AM:** Follow up via phone call on incoming replies with the promise: *'We provide standby backup cylinders while yours are refilled, so your plant is never out of compliance.'*\n"
    )

    if getattr(config, "CAMPAIGN_ENGLISH_ONLY", True):
        if not verify_campaign_english_only(content):
            raise ValueError("Campaign content violates strict English-only policy.")

    with open(dossier_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(dossier_path)

if __name__ == "__main__":
    generate_campaign_package()
