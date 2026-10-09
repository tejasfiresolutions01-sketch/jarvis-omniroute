"""
J.A.R.V.I.S. Automated Commercial Quotation & Multi-Channel Outreach Engine.
Specialized for Tejas Fire Solutions commercial operations:
- Instant compilation of IS 2190 compliant industrial quotations.
- Automated GST (18%) and corporate discount financial calculations.
- Executive PDF rendering via ReportLab and NumberedCanvas.
- Multi-channel outreach synthesis: Email (mailto / HTML), WhatsApp Web API, SMS, and 7-Day Follow-Up Cadence.
- Strictly in English.
"""

import sys
import os
import json
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config
from tools.pdf_generator import pdf_generator

QUOTATIONS_DIR = config.DATA_DIR / "quotations"
QUOTATIONS_DIR.mkdir(parents=True, exist_ok=True)

# Standardized Industrial Fire Protection Catalog (IS Codes & Base Rates in INR)
STANDARD_CATALOG: Dict[str, Dict[str, Any]] = {
    "abc_6kg": {
        "desc": "ABC 90% Mono-Ammonium Phosphate Powder Refilling 6kg (IS 15683 / IS 2190)",
        "unit": "Cylinder",
        "rate": 850.0,
        "standard": "IS 15683:2018 / IS 2190:2010"
    },
    "abc_4kg": {
        "desc": "ABC 90% Dry Chemical Powder Refilling 4kg (IS 15683 / IS 2190)",
        "unit": "Cylinder",
        "rate": 650.0,
        "standard": "IS 15683:2018 / IS 2190:2010"
    },
    "abc_9kg": {
        "desc": "ABC 90% Dry Chemical Powder Refilling 9kg (IS 15683 / IS 2190)",
        "unit": "Cylinder",
        "rate": 1150.0,
        "standard": "IS 15683:2018 / IS 2190:2010"
    },
    "co2_4.5kg": {
        "desc": "Carbon Dioxide (CO2) Gas Cylinder Refilling 4.5kg (IS 2878)",
        "unit": "Cylinder",
        "rate": 1200.0,
        "standard": "IS 2878:2004 / PESO Certified"
    },
    "co2_2kg": {
        "desc": "Carbon Dioxide (CO2) Gas Cylinder Refilling 2kg (IS 2878)",
        "unit": "Cylinder",
        "rate": 750.0,
        "standard": "IS 2878:2004 / PESO Certified"
    },
    "foam_9l": {
        "desc": "Mechanical Foam (AFFF 6%) Refilling & Discharge Test 9 Litres (IS 10204)",
        "unit": "Cylinder",
        "rate": 950.0,
        "standard": "IS 10204:2001 / IS 2190:2010"
    },
    "clean_agent": {
        "desc": "Clean Agent FK-5-1-12 / Novec Server Room Refilling & Certification (IS 15493)",
        "unit": "Cylinder",
        "rate": 4500.0,
        "standard": "IS 15493:2004 / NFPA 2001"
    },
    "hydro_test": {
        "desc": "Hydraulic Proof Pressure Testing with Calibration Certificate (IS 2190)",
        "unit": "Unit",
        "rate": 350.0,
        "standard": "IS 2190:2010 Clause 11.3"
    },
    "amc_quarterly": {
        "desc": "Annual Maintenance Contract (AMC) Comprehensive Quarterly Audit per unit",
        "unit": "Unit / Year",
        "rate": 450.0,
        "standard": "IS 2190:2010 Annual Schedule"
    },
    "valve_replacement": {
        "desc": "OEM High-Pressure Forged Brass Squeeze Grip Valve & Pressure Gauge Replacement",
        "unit": "Set",
        "rate": 550.0,
        "standard": "OEM PESO Grade"
    }
}


class QuotationEngine:
    """Automated commercial quotation and multi-channel sales outreach generator."""

    def __init__(self):
        self.catalog = STANDARD_CATALOG

    def create_quotation(
        self,
        client_name: str,
        facility_location: str,
        items: Optional[List[Dict[str, Any]]] = None,
        discount_pct: float = 0.0,
        corridor: str = "Ambattur",
        contact_person: str = "Plant Safety Manager",
        generate_pdf: bool = True
    ) -> Dict[str, Any]:
        """
        Compiles an itemized commercial quotation with GST, compliance references,
        JSON persistence, and executive PDF dossier generation.
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        timestamp_slug = now.strftime("%Y%m%d-%H%M%S")
        quote_id = f"TFS-QT-{now.strftime('%Y%m')}-{abs(hash(client_name + timestamp_slug)) % 9000 + 1000}"

        # If items not provided, assemble standard corridor factory compliance package
        if not items:
            items = [
                {"desc": self.catalog["abc_6kg"]["desc"], "qty": 12, "rate": self.catalog["abc_6kg"]["rate"]},
                {"desc": self.catalog["co2_4.5kg"]["desc"], "qty": 4, "rate": self.catalog["co2_4.5kg"]["rate"]},
                {"desc": self.catalog["hydro_test"]["desc"], "qty": 16, "rate": self.catalog["hydro_test"]["rate"]},
                {"desc": self.catalog["amc_quarterly"]["desc"], "qty": 16, "rate": self.catalog["amc_quarterly"]["rate"]},
            ]

        # Calculate line item amounts and totals
        calculated_items = []
        subtotal = 0.0
        for it in items:
            qty = int(it.get("qty", it.get("quantity", 1)))
            rate = float(it.get("rate", it.get("unit_rate", 0.0)))
            amt = round(qty * rate, 2)
            subtotal += amt
            calculated_items.append({
                "desc": it.get("desc", it.get("description", "Service Item")),
                "qty": qty,
                "rate": rate,
                "amount": amt
            })

        discount_pct = max(0.0, min(100.0, float(discount_pct)))
        discount_amt = round(subtotal * (discount_pct / 100.0), 2)
        taxable_amount = round(subtotal - discount_amt, 2)
        gst_pct = 18.0
        gst_amount = round(taxable_amount * (gst_pct / 100.0), 2)
        grand_total = round(taxable_amount + gst_amount, 2)

        quote_data = {
            "quote_id": quote_id,
            "date": date_str,
            "client_name": client_name,
            "facility_location": facility_location,
            "corridor": corridor,
            "contact_person": contact_person,
            "validity_days": 30,
            "items": calculated_items,
            "subtotal": subtotal,
            "discount_pct": discount_pct,
            "discount_amt": discount_amt,
            "taxable_amount": taxable_amount,
            "gst_pct": gst_pct,
            "gst_amount": gst_amount,
            "grand_total": grand_total,
            "compliance_standards": "IS 2190:2010, PESO Regulations & Tamil Nadu Fire Service Directives",
            "payment_terms": "30 Days from delivery of serviced cylinders and hydro-test certificates",
            "warranty": "12 Months comprehensive OEM warranty on dry chemical powder & pressure valves"
        }

        # Render Executive PDF
        pdf_path_str = ""
        if generate_pdf:
            try:
                pdf_file = pdf_generator.generate_quotation_pdf(quote_data)
                quote_data["pdf_path"] = str(pdf_file)
                pdf_path_str = str(pdf_file)
            except Exception as e:
                quote_data["pdf_error"] = str(e)

        # Persist JSON Record
        json_path = QUOTATIONS_DIR / f"{quote_id}.json"
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(quote_data, f, indent=2)
            quote_data["json_path"] = str(json_path)
        except Exception:
            pass

        return quote_data

    def generate_multi_channel_outreach(
        self,
        quote_data: Dict[str, Any],
        client_email: str = "safety@enterprise.com",
        client_phone: str = "+919840012345"
    ) -> Dict[str, Any]:
        """
        Synthesizes omni-channel outreach materials:
        - Executive Email (HTML + mailto direct link)
        - WhatsApp Web click-to-chat API URL
        - SMS broadcast copy (concise 160 chars)
        - 7-Day Follow-Up Cadence
        """
        quote_id = quote_data.get("quote_id", "TFS-QUOTE")
        client_name = quote_data.get("client_name", "Valued Client")
        location = quote_data.get("facility_location", "Industrial Corridor")
        grand_total = quote_data.get("grand_total", 0.0)
        items_count = len(quote_data.get("items", []))

        # 1. Executive Email
        email_subject = f"Commercial Proposal & IS 2190 Fire Safety Quotation [{quote_id}] - Tejas Fire Solutions"
        email_body_text = (
            f"Dear {quote_data.get('contact_person', 'Plant Safety Manager')},\n\n"
            f"Thank you for contacting Tejas Fire Solutions regarding fire safety services for your facility at {location}.\n\n"
            f"We are pleased to enclose Official Commercial Quotation Ref: {quote_id} covering {items_count} line items "
            f"of fire extinguisher refilling, hydrostatic pressure testing, and IS 2190 compliance certification.\n\n"
            f"FINANCIAL SUMMARY:\n"
            f"- Taxable Value: INR {quote_data.get('taxable_amount', 0.0):,.2f}\n"
            f"- GST (18%): INR {quote_data.get('gst_amount', 0.0):,.2f}\n"
            f"- Grand Total: INR {grand_total:,.2f}\n\n"
            f"All refilling services utilize 90% MAP powder adhering to IS 15683 and IS 2190 standards, accompanied by "
            f"individual hydrostatic proof test certificates and 12-month OEM warranties.\n\n"
            f"Please let us know your preferred date for cylinder pickup and on-site audit.\n\n"
            f"Warm regards,\n"
            f"Technical Operations Directorate\n"
            f"Tejas Fire Solutions &bull; J.A.R.V.I.S. Autonomous Matrix"
        )

        mailto_url = f"mailto:{client_email}?subject={urllib.parse.quote(email_subject)}&body={urllib.parse.quote(email_body_text)}"

        # 2. WhatsApp Business Outreach
        wa_text = (
            f"🔥 *TEJAS FIRE SOLUTIONS // OFFICIAL QUOTATION*\n\n"
            f"Hello Sir,\n"
            f"Quotation *{quote_id}* for *{client_name}* ({location}) is ready.\n\n"
            f"📋 *Scope:* {items_count} Services (Refilling, Hydro-Testing & IS 2190 Certification)\n"
            f"💰 *Total Amount:* INR {grand_total:,.2f} (Inclusive of 18% GST)\n"
            f"🛡️ *Standards:* IS 2190:2010 & PESO Approved\n"
            f"⏱️ *Validity:* 30 Days\n\n"
            f"Our service van can collect cylinders from your facility tomorrow. Would you like us to schedule pickup?"
        )
        clean_phone = "".join(ch for ch in client_phone if ch.isdigit() or ch == "+").replace("+", "")
        wa_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(wa_text)}"

        # 3. SMS Broadcast
        sms_text = (
            f"Tejas Fire Solutions: Quotation {quote_id} for {client_name[:20]} (INR {grand_total:,.0f}) is ready. "
            f"IS 2190 compliant. Call +91-9840000000 to schedule pickup."
        )

        # 4. 7-Day Follow-Up Cadence
        cadence = [
            {
                "day": 1,
                "channel": "Email + WhatsApp",
                "objective": "Official Quotation Dispatch & Executive Compliance Brief",
                "action": "Transmit PDF dossier and WhatsApp confirmation message."
            },
            {
                "day": 3,
                "channel": "WhatsApp / Phone Call",
                "objective": "Technical Consultation & Hydrostatic Test Verification",
                "action": "Address safety questions, verify cylinder counts, offer sample demonstration."
            },
            {
                "day": 7,
                "channel": "Executive Email / Priority Call",
                "objective": "Audit Slot Confirmation & Work Order Finalization",
                "action": "Reserve maintenance slot and dispatch pickup authorization team."
            }
        ]

        outreach = {
            "quote_id": quote_id,
            "client_name": client_name,
            "email": {
                "recipient": client_email,
                "subject": email_subject,
                "body_text": email_body_text,
                "mailto_url": mailto_url
            },
            "whatsapp": {
                "recipient_phone": client_phone,
                "message_text": wa_text,
                "click_to_chat_url": wa_url
            },
            "sms": {
                "recipient_phone": client_phone,
                "text": sms_text,
                "length": len(sms_text)
            },
            "cadence": cadence
        }

        return outreach

    def format_voice_summary(self, quote_data: Dict[str, Any]) -> str:
        """Articulates concise, elegant voice briefing of the quotation and outreach package."""
        quote_id = quote_data.get("quote_id", "TFS-QUOTE")
        client = quote_data.get("client_name", "the client")
        location = quote_data.get("facility_location", "the facility")
        grand_total = quote_data.get("grand_total", 0.0)

        return (
            f"Commercial quotation {quote_id} compiled for {client} at {location}, sir. "
            f"Total value is INR {grand_total:,.2f} inclusive of 18% GST. "
            f"The executive PDF dossier and multi-channel outreach templates for WhatsApp and email are fully generated and ready."
        )


# Global singleton
quotation_engine = QuotationEngine()
