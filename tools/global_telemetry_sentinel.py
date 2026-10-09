"""
J.A.R.V.I.S. Global 24/7 Telemetry Sentinel & World Event Monitor.
Features:
1. Multi-Stream Ingestion:
   - Continuously monitors high-signal streams across Geopolitics, Cybersecurity, Frontier AI, and Markets.
2. Anomaly & Urgency Detection:
   - Scans stream items for breaking anomalies, security advisories, and critical market events.
   - Computes urgency confidence scores (0-100%).
3. Non-Blocking 24/7 Background Daemon:
   - Operates in a lightweight daemon thread with local caching and SHA-256 deduplication.
4. Voice Briefing & Audit Log:
   - Formats concise executive situation reports ready for acoustic vocalization.
100% Free Plan, zero cloud subscriptions, zero external API keys required.
"""

import hashlib
import json
import logging
import os
import re
import sys
import threading
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

logger = logging.getLogger("GlobalTelemetrySentinel")

TELEMETRY_CACHE_FILE = config.DATA_DIR / "global_telemetry_cache.json"
TELEMETRY_ALERTS_FILE = config.DATA_DIR / "global_telemetry_alerts.json"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# Urgency keywords and weights for world-event anomaly detection
URGENCY_KEYWORDS = {
    "breaking": 25,
    "critical": 25,
    "emergency": 30,
    "outage": 20,
    "zero-day": 35,
    "vulnerability": 20,
    "attack": 20,
    "surge": 15,
    "plunge": 15,
    "breakthrough": 20,
    "historic": 15,
    "escalation": 25,
    "sanctions": 15,
    "blackout": 25,
    "unprecedented": 20,
}


class GlobalTelemetrySentinel:
    """Autonomous 24/7 world telemetry monitoring sentinel with anomaly scoring."""

    GLOBAL_STREAMS = {
        "geopolitics": [
            {"name": "BBC World News", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
            {"name": "NPR World", "url": "https://feeds.npr.org/1004/rss.xml"},
        ],
        "cybersecurity": [
            {"name": "Hacker News Top", "url": "https://news.ycombinator.com/rss"},
            {"name": "SecurityWeek", "url": "https://feeds.feedburner.com/securityweek"},
        ],
        "frontier_ai": [
            {"name": "ArXiv AI", "url": "https://export.arxiv.org/rss/cs.AI"},
            {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/"},
        ],
        "markets": [
            {"name": "BBC Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml"},
            {"name": "CNBC Market", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
        ],
    }

    def __init__(self):
        self._ensure_storage()
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._poll_interval = 300  # 5 minutes default

    def _ensure_storage(self):
        try:
            config.DATA_DIR.mkdir(parents=True, exist_ok=True)
            if not TELEMETRY_CACHE_FILE.exists():
                TELEMETRY_CACHE_FILE.write_text(json.dumps({"seen_hashes": [], "last_scan": 0}, indent=2), encoding="utf-8")
            if not TELEMETRY_ALERTS_FILE.exists():
                TELEMETRY_ALERTS_FILE.write_text(json.dumps({"alerts": []}, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_cache(self) -> Dict[str, Any]:
        try:
            if TELEMETRY_CACHE_FILE.exists():
                return json.loads(TELEMETRY_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"seen_hashes": [], "last_scan": 0}

    def _save_cache(self, data: Dict[str, Any]):
        try:
            TELEMETRY_CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_alerts(self) -> List[Dict[str, Any]]:
        try:
            if TELEMETRY_ALERTS_FILE.exists():
                data = json.loads(TELEMETRY_ALERTS_FILE.read_text(encoding="utf-8"))
                return data.get("alerts", [])
        except Exception:
            pass
        return []

    def _save_alerts(self, alerts: List[Dict[str, Any]]):
        try:
            TELEMETRY_ALERTS_FILE.write_text(json.dumps({"alerts": alerts[-100:]}, indent=2), encoding="utf-8")
        except Exception:
            pass

    def calculate_urgency(self, title: str, summary: str) -> Tuple[int, List[str]]:
        """Calculates urgency confidence score (0-100) and triggered keywords."""
        content = f"{title} {summary}".lower()
        score = 10  # Baseline observation score
        matched = []
        for kw, weight in URGENCY_KEYWORDS.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", content):
                score += weight
                matched.append(kw)
        score = min(score, 100)
        return score, matched

    def parse_feed_xml(self, xml_content: str, source_name: str, category: str) -> List[Dict[str, Any]]:
        """Parses RSS or Atom XML content safely into structured telemetry items."""
        items = []
        try:
            root = ET.fromstring(xml_content)
            # Standard RSS channel/item
            channel = root.find("channel")
            if channel is not None:
                for elem in channel.findall("item"):
                    title = (elem.findtext("title") or "").strip()
                    link = (elem.findtext("link") or "").strip()
                    desc = (elem.findtext("description") or "").strip()
                    # Strip basic HTML from desc
                    clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()
                    if title:
                        urgency, triggers = self.calculate_urgency(title, clean_desc)
                        item_id = hashlib.sha256(f"{title}_{link}".encode("utf-8")).hexdigest()[:16]
                        items.append({
                            "id": item_id,
                            "source": source_name,
                            "category": category,
                            "title": title,
                            "link": link,
                            "summary": clean_desc[:240],
                            "urgency": urgency,
                            "triggers": triggers,
                            "timestamp": time.time(),
                        })
            else:
                # Atom namespace handling
                atom_entries = root.findall("{http://www.w3.org/2005/Atom}entry")
                if not atom_entries:
                    atom_entries = root.findall("entry")
                for entry in atom_entries:
                    title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
                    if title_elem is None:
                        title_elem = entry.find("title")
                    title = (title_elem.text or "").strip() if title_elem is not None else ""

                    link_elem = entry.find("{http://www.w3.org/2005/Atom}link")
                    if link_elem is None:
                        link_elem = entry.find("link")
                    link = link_elem.attrib.get("href", "") if link_elem is not None else ""

                    summary_elem = entry.find("{http://www.w3.org/2005/Atom}summary")
                    if summary_elem is None:
                        summary_elem = entry.find("summary")
                    summary = (summary_elem.text or "").strip() if summary_elem is not None else ""
                    clean_summary = re.sub(r"<[^>]+>", " ", summary).strip()
                    if title:
                        urgency, triggers = self.calculate_urgency(title, clean_summary)
                        item_id = hashlib.sha256(f"{title}_{link}".encode("utf-8")).hexdigest()[:16]
                        items.append({
                            "id": item_id,
                            "source": source_name,
                            "category": category,
                            "title": title,
                            "link": link,
                            "summary": clean_summary[:240],
                            "urgency": urgency,
                            "triggers": triggers,
                            "timestamp": time.time(),
                        })
        except Exception as e:
            logger.debug(f"XML parse error for {source_name}: {e}")
        return items

    def fetch_stream(self, url: str, source_name: str, category: str, timeout: float = 6.0) -> List[Dict[str, Any]]:
        """Fetches and parses a single external feed stream with graceful timeout."""
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
            if resp.status_code == 200:
                return self.parse_feed_xml(resp.text, source_name, category)
        except Exception:
            pass
        return []

    def scan_all_streams(self, max_per_source: int = 5) -> Dict[str, Any]:
        """
        Executes a full cycle scan across all registered global streams.
        Deduplicates previously observed items and surfaces high-urgency alerts.
        """
        cache = self._load_cache()
        seen_hashes = set(cache.get("seen_hashes", []))
        existing_alerts = self._load_alerts()

        new_items: List[Dict[str, Any]] = []
        high_urgency_alerts: List[Dict[str, Any]] = []

        for category, sources in self.GLOBAL_STREAMS.items():
            for src in sources:
                fetched = self.fetch_stream(src["url"], src["name"], category)
                for item in fetched[:max_per_source]:
                    item_id = item["id"]
                    if item_id not in seen_hashes:
                        seen_hashes.add(item_id)
                        new_items.append(item)
                        if item["urgency"] >= 50:
                            high_urgency_alerts.append(item)

        # Update cache
        cache["seen_hashes"] = list(seen_hashes)[-500:]  # Keep last 500
        cache["last_scan"] = time.time()
        self._save_cache(cache)

        # Save alerts
        if high_urgency_alerts:
            existing_alerts.extend(high_urgency_alerts)
            self._save_alerts(existing_alerts)

        return {
            "scanned_at": time.time(),
            "new_items_count": len(new_items),
            "high_urgency_alerts_count": len(high_urgency_alerts),
            "latest_alerts": high_urgency_alerts[:5],
        }

    def start_background_monitoring(self, poll_interval: int = 300):
        """Starts continuous non-blocking 24/7 background telemetry daemon."""
        with self._lock:
            if self._is_running:
                return
            self._is_running = True
            self._poll_interval = poll_interval
            self._thread = threading.Thread(target=self._run_daemon_loop, daemon=True, name="JarvisGlobalTelemetrySentinel")
            self._thread.start()
            logger.info("[Global Telemetry Sentinel]: 24/7 background stream monitoring engaged.")

    def stop_background_monitoring(self):
        """Halts background telemetry daemon."""
        with self._lock:
            self._is_running = False

    def _run_daemon_loop(self):
        while self._is_running:
            try:
                self.scan_all_streams()
            except Exception as e:
                logger.debug(f"Telemetry loop error: {e}")
            for _ in range(self._poll_interval):
                if not self._is_running:
                    break
                time.sleep(1)

    def get_status(self) -> Dict[str, Any]:
        """Returns live monitoring status and telemetry counts."""
        cache = self._load_cache()
        alerts = self._load_alerts()
        return {
            "active": self._is_running,
            "stream_categories": list(self.GLOBAL_STREAMS.keys()),
            "total_streams": sum(len(v) for v in self.GLOBAL_STREAMS.values()),
            "cached_signatures": len(cache.get("seen_hashes", [])),
            "unresolved_alerts": len([a for a in alerts if a.get("urgency", 0) >= 60]),
            "last_scan_time": cache.get("last_scan", 0),
        }

    def format_situation_report(self) -> str:
        """Generates concise executive briefing formatted for voice and display."""
        alerts = self._load_alerts()
        recent = sorted(alerts, key=lambda x: x.get("urgency", 0), reverse=True)[:3]
        if not recent:
            return "World telemetry stable, sir. All monitored global streams (geopolitics, cybersecurity, AI, markets) indicate nominal activity."

        headlines = []
        for r in recent:
            headlines.append(f"{r['source']} reports: {r['title']} (Urgency: {r['urgency']}%)")
        return f"Global telemetry briefing, sir: {'; '.join(headlines)}."


# Global Singleton Instance
global_telemetry_sentinel = GlobalTelemetrySentinel()
