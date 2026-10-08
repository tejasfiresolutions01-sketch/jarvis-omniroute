"""
J.A.R.V.I.S. Google Services Suite:
1. Google Maps: Place search, turn-by-turn route directions, industrial corridor mapping.
2. Gmail: Frictionless Web Compose link generation, Inbox access, and optional direct SMTP dispatch.
3. Google Search Engine: Real-time organic web search parsing and browser launch.
100% Free Plan.
"""

import os
import smtplib
import urllib.parse
import webbrowser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

import config

class GoogleServices:
    """Unified Google Ecosystem Integrations for J.A.R.V.I.S."""

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Google Search Engine Integration
    # ─────────────────────────────────────────────────────────────────────────
    def search_google(self, query: str, num_results: int = 5, open_browser: bool = False) -> List[Dict[str, str]]:
        """
        Executes a search on Google Search Engine.
        Returns extracted organic results and optionally displays in browser.
        """
        clean_q = query.strip()
        if not clean_q:
            return []

        if open_browser:
            url = f"https://www.google.com/search?q={urllib.parse.quote(clean_q)}"
            webbrowser.open(url)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        results = []
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(clean_q)}&num={num_results}&hl=en"
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Parse Google Search organic result blocks
                for g in soup.find_all("div", class_="tF2Cxc"):
                    title_elem = g.find("h3")
                    link_elem = g.find("a")
                    snippet_elem = g.find("div", class_="VwiC3b") or g.find("div", class_="yXK7lf")

                    if title_elem and link_elem:
                        title = title_elem.get_text()
                        link = link_elem.get("href", "")
                        snippet = snippet_elem.get_text() if snippet_elem else ""
                        results.append({
                            "title": title,
                            "link": link,
                            "snippet": snippet
                        })
                    if len(results) >= num_results:
                        break
        except Exception:
            pass

        # Fallback to DuckDuckGo HTML / Web Tools if Google rate limits
        if not results:
            try:
                from tools.web_tools import search_web
                raw = search_web(clean_q)
                results.append({
                    "title": f"Web Intelligence: {clean_q}",
                    "link": f"https://www.google.com/search?q={urllib.parse.quote(clean_q)}",
                    "snippet": str(raw)[:300]
                })
            except Exception:
                pass

        return results

    def format_search_summary(self, query: str) -> str:
        """Returns an articulate spoken butler summary of Google search results."""
        results = self.search_google(query, num_results=3)
        if not results:
            return f"No definitive search results were located for '{query}', sir."

        snippets = []
        for r in results:
            snippets.append(f"{r['title']}: {r['snippet'][:120]}")
        joined = "; ".join(snippets)
        return f"According to Google Search for '{query}': {joined}."

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Google Maps Platform Integration
    # ─────────────────────────────────────────────────────────────────────────
    def search_maps(self, location_or_query: str, open_browser: bool = True) -> str:
        """Searches Google Maps for a location, business, or industrial corridor."""
        clean = location_or_query.strip()
        url = f"https://www.google.com/maps/search/{urllib.parse.quote(clean)}"
        if open_browser:
            webbrowser.open(url)
        return f"Opening Google Maps search for '{clean}', sir."

    def get_directions(
        self,
        origin: str,
        destination: str,
        travel_mode: str = "driving",
        open_browser: bool = True
    ) -> str:
        """Generates Google Maps turn-by-turn navigation between origin and destination."""
        orig_clean = origin.strip()
        dest_clean = destination.strip()
        url = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={urllib.parse.quote(orig_clean)}"
            f"&destination={urllib.parse.quote(dest_clean)}"
            f"&travelmode={travel_mode}"
        )
        if open_browser:
            webbrowser.open(url)
        return f"Calculating Google Maps navigation route from '{orig_clean}' to '{dest_clean}' via {travel_mode}, sir."

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Gmail Integration
    # ─────────────────────────────────────────────────────────────────────────
    def open_gmail(self) -> str:
        """Opens Gmail Inbox in default browser."""
        url = "https://mail.google.com/mail/u/0/#inbox"
        webbrowser.open(url)
        return "Opening your Gmail Inbox, sir."

    def compose_email(
        self,
        to: str = "",
        subject: str = "",
        body: str = "",
        open_browser: bool = True
    ) -> str:
        """
        Creates a new pre-populated Gmail compose window in the user's browser.
        Zero authentication required — operates seamlessly through active session.
        """
        params = {"view": "cm", "fs": "1"}
        if to:
            params["to"] = to.strip()
        if subject:
            params["su"] = subject.strip()
        if body:
            params["body"] = body.strip()

        url = f"https://mail.google.com/mail/?{urllib.parse.urlencode(params)}"
        if open_browser:
            webbrowser.open(url)
        return f"Opening Gmail compose draft addressed to '{to or 'recipient'}', sir."

    def send_email_direct(
        self,
        to_address: str,
        subject: str,
        body: str,
        attachment_path: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Dispatches email directly via Gmail SMTP server if credentials are configured in .env.
        Requires GMAIL_ADDRESS and GMAIL_APP_PASSWORD.
        """
        gmail_user = os.getenv("GMAIL_ADDRESS", "")
        gmail_pass = os.getenv("GMAIL_APP_PASSWORD", "")

        if not gmail_user or not gmail_pass:
            # Fallback to zero-friction Web Compose link
            self.compose_email(to=to_address, subject=subject, body=body, open_browser=True)
            return (
                True,
                "Direct SMTP credentials not found in .env; opened pre-filled Gmail compose window for instant one-click dispatch, sir."
            )

        try:
            msg = MIMEMultipart()
            msg["From"] = gmail_user
            msg["To"] = to_address
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            if attachment_path and Path(attachment_path).exists():
                p = Path(attachment_path)
                with open(p, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename= {p.name}")
                msg.attach(part)

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, to_address, msg.as_string())
            server.quit()
            return True, f"Email dispatched successfully to {to_address} via Gmail SMTP, sir."
        except Exception as e:
            return False, f"Failed to dispatch email via Gmail SMTP ({e}), sir."

# Global singleton
google_services = GoogleServices()
