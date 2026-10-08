"""
J.A.R.V.I.S. Digital Marketing Suite - Module 5: Customer Nurture & Retention Engine.
Features:
1. Automated Lifecycle Drip Sequence:
   - Touch 1: Welcome & Compliance Certificate Delivery.
   - Touch 2: Post-Service Review Request (Google 5-Star reputation engine).
   - Touch 3: 6-Month Complimentary Pressure & Gauge Health Check.
   - Touch 4: 11-Month Annual Refilling & Hydro-Test Renewal Alert.
2. Review Generation Gateway: Builds high-converting WhatsApp review request templates.
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

logger = logging.getLogger("DigitalMarketingNurture")

class DigitalMarketingNurture:
    """
    Automated Lifecycle Drip Sequences & Reputation Management.
    """

    def generate_drip_sequence(self, client_name: str = "Client Facility", service_date: str = "today") -> List[Dict[str, Any]]:
        """
        Generates 4-touch post-service retention and annual renewal email sequence.
        """
        return [
            {
                "stage": "Touch 1: Immediate Post-Service Delivery",
                "timing": "Immediately upon cylinder delivery",
                "subject": f"Your IS 2190 Fire Safety Refilling Certificate - {client_name}",
                "body": (
                    f"Dear {client_name} Team,\n\n"
                    f"Thank you for choosing Tejas Fire Solutions for your fire protection servicing. "
                    f"All extinguishers collected have been successfully refilled, tested, and reinstalled at your premises.\n\n"
                    f"Attached is your official Hydrostatic Pressure Test Report and IS 2190 Refilling Compliance Certificate. "
                    f"Please keep this document accessible for your next TNFRS safety audit or insurance inspection.\n\n"
                    f"Warm regards,\n"
                    f"Tejas Fire Solutions Customer Success Team"
                )
            },
            {
                "stage": "Touch 2: Review & Reputation Request",
                "timing": "3 days post-delivery",
                "subject": f"Quick question about your service experience at {client_name}",
                "body": (
                    f"Hi {client_name} Team,\n\n"
                    f"We hope your facility operations are running smoothly with our serviced cylinders in place. "
                    f"Our goal is to provide the fastest, safest fire protection service in Tamil Nadu.\n\n"
                    f"If our technicians were prompt and professional, would you mind taking 30 seconds to leave us a brief review on Google? "
                    f"It helps other local industrial facilities find certified fire safety partners.\n\n"
                    f"👉 [Click here to leave a Google Review: https://g.page/r/tejasfiresolutions/review]\n\n"
                    f"Thank you for your partnership!\n"
                    f"Tejas Fire Solutions"
                )
            },
            {
                "stage": "Touch 3: 6-Month Complimentary Checkpoint",
                "timing": "6 months post-service",
                "subject": f"Complimentary 6-month fire extinguisher pressure check for {client_name}",
                "body": (
                    f"Dear Facilities Team,\n\n"
                    f"It has been 6 months since your last extinguisher refilling cycle. "
                    f"Under IS 2190 guidelines, industrial plants should perform a mid-year check on gauge pressures and nozzle seals.\n\n"
                    f"We have technicians scheduled on routes through your industrial corridor next week. "
                    f"We would be delighted to perform a complimentary 10-minute visual walk-through of your units at zero cost.\n\n"
                    f"Reply to this email or send us a WhatsApp message to lock in your free route visit.\n\n"
                    f"Best regards,\n"
                    f"Tejas Fire Solutions"
                )
            },
            {
                "stage": "Touch 4: 11-Month Annual Renewal Alert",
                "timing": "11 months post-service (1 month before expiry)",
                "subject": f"URGENT: Annual Fire Extinguisher Refilling Due Next Month - {client_name}",
                "body": (
                    f"Dear {client_name} Safety Lead,\n\n"
                    f"Your facility's annual fire extinguisher servicing certification is due for renewal next month. "
                    f"To ensure your premises remain continuously compliant with TNFRS standards without insurance lapse:\n\n"
                    f"1. We have pre-reserved your equivalent standby cylinders to guarantee zero factory downtime.\n"
                    f"2. Your existing preferred pricing tier has been locked in.\n\n"
                    f"Please confirm your preferred pickup date for this month so we can allocate your technician.\n\n"
                    f"Warm regards,\n"
                    f"Tejas Fire Solutions Service Division"
                )
            }
        ]

    def generate_review_request_whatsapp(self, client_name: str) -> str:
        """
        Generates direct WhatsApp review request script with review link.
        """
        return (
            f"Hello {client_name} Team! This is from Tejas Fire Solutions.\n"
            f"We hope your serviced fire extinguishers were delivered to your satisfaction.\n"
            f"Could you please share your quick feedback on Google? It takes just 20 seconds and means the world to our team:\n"
            f"👉 https://g.page/r/tejasfiresolutions/review\n"
            f"Thank you for trusting us with your plant's fire safety!"
        )

    def format_voice_summary(self) -> str:
        """Articulate spoken summary of customer nurture sequences."""
        return (
            "Customer nurture and retention matrix is operational, sir. "
            "A 4-stage post-service drip sequence covering certificate delivery, "
            "Google review generation, 6-month checkups, and 11-month annual renewals is ready."
        )

# Global singleton
nurture_engine = DigitalMarketingNurture()
