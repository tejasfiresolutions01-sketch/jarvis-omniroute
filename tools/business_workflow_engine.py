"""
J.A.R.V.I.S. Business Workflow, Commercial Invoicing & WhatsApp Engine.
Features:
1. GST Quotation & Refilling Invoice Generator: Prepares IS 2190 compliant commercial quotations
   with cylinder quantities, hydro-testing, replacement valves, and standard 18% GST calculation.
2. Local CRM Pipeline Tracker: Manages customer acquisition lifecycle
   (Prospect -> Quoted -> AMC Active -> Annual Hydro-Test Due).
3. WhatsApp Web Link Generator: Builds pre-filled, compliant WhatsApp Web dispatch links for seamless client communication.
Strictly in English.
"""

import os
import re
import sys
import json
import sqlite3
import logging
import urllib.parse
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config

logger = logging.getLogger("BusinessWorkflow")

# Standard Rate Card for Tejas Fire Solutions B2B Services (IS 2190 Compliant)
STANDARD_REFILLING_RATES = {
    "abc_4kg": {"name": "ABC Powder Refilling 4kg (IS 15683)", "base_rate": 350.00, "hsn": "8424"},
    "abc_6kg": {"name": "ABC Powder Refilling 6kg (IS 15683)", "base_rate": 450.00, "hsn": "8424"},
    "abc_9kg": {"name": "ABC Powder Refilling 9kg (IS 15683)", "base_rate": 650.00, "hsn": "8424"},
    "co2_2kg": {"name": "CO2 Gas Refilling 2kg (IS 15683)", "base_rate": 380.00, "hsn": "8424"},
    "co2_4.5kg": {"name": "CO2 Gas Refilling 4.5kg (IS 15683)", "base_rate": 550.00, "hsn": "8424"},
    "foam_9l": {"name": "Mechanical Foam Refilling 9 Liters (IS 15683)", "base_rate": 500.00, "hsn": "8424"},
    "hydro_test": {"name": "Hydraulic Pressure Testing & Certificate (IS 2190)", "base_rate": 200.00, "hsn": "9987"}
}

class BusinessWorkflowEngine:
    """
    Automated B2B Commercial Sales, Quotation, and Customer Relations Matrix.
    """

    DB_PATH = config.BASE_DIR / "data" / "crm_pipeline.db"

    def __init__(self):
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.DB_PATH), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS crm_leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name TEXT NOT NULL,
                    hub TEXT,
                    phone TEXT,
                    email TEXT,
                    status TEXT DEFAULT 'Prospect',
                    quote_amount REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_followup TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def add_or_update_lead(self, client_name: str, hub: str = "", phone: str = "", status: str = "Prospect", quote_amount: float = 0.0) -> int:
        """Adds or updates a B2B prospect in the CRM database."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM crm_leads WHERE LOWER(client_name) = LOWER(?)", (client_name.strip(),))
            row = cur.fetchone()
            if row:
                lead_id = row["id"]
                conn.execute(
                    "UPDATE crm_leads SET hub = ?, phone = ?, status = ?, quote_amount = ?, last_followup = CURRENT_TIMESTAMP WHERE id = ?",
                    (hub, phone, status, quote_amount, lead_id)
                )
            else:
                cur.execute(
                    "INSERT INTO crm_leads (client_name, hub, phone, status, quote_amount) VALUES (?, ?, ?, ?, ?)",
                    (client_name.strip(), hub, phone, status, quote_amount)
                )
                lead_id = cur.lastrowid
            conn.commit()
            return lead_id

    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Returns structured statistics across the active sales funnel."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT status, count(*) as count, sum(quote_amount) as total_value FROM crm_leads GROUP BY status")
            rows = cur.fetchall()
            stages = {r["status"]: {"count": r["count"], "value": r["total_value"] or 0.0} for r in rows}
            
            cur.execute("SELECT count(*) as total, sum(quote_amount) as pipeline_value FROM crm_leads")
            total_row = cur.fetchone()
            
            return {
                "total_leads": total_row["total"] if total_row else 0,
                "total_pipeline_value_inr": total_row["pipeline_value"] or 0.0 if total_row else 0.0,
                "stages": stages
            }

    def generate_quotation(self, client_name: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates an IS 2190 GST-compliant commercial quotation.
        Calculates subtotal, 18% GST (9% CGST + 9% SGST), and total payable.
        """
        line_items = []
        subtotal = 0.0

        for it in items:
            code = it.get("item_code", "abc_6kg")
            qty = int(it.get("quantity", 1))
            rate_info = STANDARD_REFILLING_RATES.get(code, STANDARD_REFILLING_RATES["abc_6kg"])
            unit_rate = float(it.get("custom_rate", rate_info["base_rate"]))
            amount = unit_rate * qty
            subtotal += amount

            line_items.append({
                "item_name": rate_info["name"],
                "hsn": rate_info["hsn"],
                "quantity": qty,
                "rate": unit_rate,
                "amount": amount
            })

        cgst = subtotal * 0.09
        sgst = subtotal * 0.09
        total_amount = subtotal + cgst + sgst

        quotation_number = f"TFS-EST-{datetime.now().strftime('%Y%m')}-{len(line_items):02d}"

        quote_data = {
            "quotation_number": quotation_number,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "client_name": client_name,
            "supplier": "Tejas Fire Solutions (Certified IS 2190 Station)",
            "line_items": line_items,
            "subtotal_inr": round(subtotal, 2),
            "cgst_9pct": round(cgst, 2),
            "sgst_9pct": round(sgst, 2),
            "total_inr": round(total_amount, 2),
            "payment_terms": "30 Days Net on delivery with Hydro-Test Compliance Certificates"
        }

        # Auto-update CRM pipeline
        self.add_or_update_lead(client_name, status="Quote Sent", quote_amount=quote_data["total_inr"])

        return quote_data

    def build_whatsapp_message_link(self, phone: str, message_text: str) -> str:
        """
        Generates a direct WhatsApp Web URL with URL-encoded message text.
        """
        clean_phone = re.sub(r"[^\d]", "", phone)
        if len(clean_phone) == 10:
            clean_phone = "91" + clean_phone # Add India country code if 10-digit

        encoded_msg = urllib.parse.quote(message_text.strip())
        return f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"

    def format_crm_voice_summary(self) -> str:
        """Formats an articulate spoken summary of the sales pipeline."""
        pipe = self.get_pipeline_summary()
        total = pipe.get("total_leads", 0)
        val = pipe.get("total_pipeline_value_inr", 0.0)
        return (
            f"CRM sales pipeline active, sir. Currently tracking {total} commercial accounts "
            f"with an active pipeline value of ₹{val:,.2f}. All records are synchronized locally."
        )

# Global singleton
business_workflow = BusinessWorkflowEngine()
