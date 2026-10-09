"""
J.A.R.V.I.S. Curated Information Stream & Web Feed Monitor.
Provides targeted, high-signal information streams across technology,
world news, science, and custom topics with local caching and offline fallback.
100% Free Plan, zero paid API keys, zero cloud dependencies.
"""

import hashlib
import json
import logging
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

logger = logging.getLogger("WebStreamMonitor")

STREAM_CACHE_FILE = config.DATA_DIR / "web_stream_cache.json"
CUSTOM_FEEDS_FILE = config.DATA_DIR / "custom_web_feeds.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


class WebStreamMonitor:
    """Monitors curated targeted RSS/Atom information streams."""

    DEFAULT_FEEDS = {
        "tech": [
            {"name": "BBC Technology", "url": "https://feeds.bbci.co.uk/news/technology/rss.xml"},
            {"name": "NYT Tech", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"},
            {"name": "ArXiv AI", "url": "https://export.arxiv.org/rss/cs.AI"},
        ],
        "world": [
            {"name": "BBC World News", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
            {"name": "NPR News", "url": "https://feeds.npr.org/1001/rss.xml"},
        ],
        "science": [
            {"name": "Science Daily", "url": "https://www.sciencedaily.com/rss/all.xml"},
            {"name": "NASA Breaking", "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss"},
        ],
        "business": [
            {"name": "BBC Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml"},
            {"name": "NPR Business", "url": "https://feeds.npr.org/1006/rss.xml"},
        ],
    }

    def __init__(self):
        self._ensure_storage()

    def _ensure_storage(self):
        try:
            config.DATA_DIR.mkdir(parents=True, exist_ok=True)
            if not STREAM_CACHE_FILE.exists():
                STREAM_CACHE_FILE.write_text("{}", encoding="utf-8")
            if not CUSTOM_FEEDS_FILE.exists():
                CUSTOM_FEEDS_FILE.write_text("{}", encoding="utf-8")
        except Exception:
            pass

    def get_all_feeds(self) -> Dict[str, List[Dict[str, str]]]:
        """Combines default curated feeds with custom user-registered feeds."""
        feeds = dict(self.DEFAULT_FEEDS)
        try:
            if CUSTOM_FEEDS_FILE.exists():
                custom = json.loads(CUSTOM_FEEDS_FILE.read_text(encoding="utf-8"))
                for cat, f_list in custom.items():
                    if cat not in feeds:
                        feeds[cat] = []
                    feeds[cat].extend(f_list)
        except Exception:
            pass
        return feeds

    def add_custom_feed(self, category: str, name: str, url: str) -> bool:
        """Adds a custom RSS/Atom URL to the targeted streams monitor."""
        cat = category.lower().strip()
        try:
            custom = {}
            if CUSTOM_FEEDS_FILE.exists():
                try:
                    custom = json.loads(CUSTOM_FEEDS_FILE.read_text(encoding="utf-8"))
                except Exception:
                    custom = {}
            if cat not in custom:
                custom[cat] = []
            custom[cat].append({"name": name, "url": url})
            CUSTOM_FEEDS_FILE.write_text(json.dumps(custom, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            logger.warning(f"Error saving custom feed: {e}")
            return False

    def fetch_stream_items(self, category: str = "tech", max_items_per_feed: int = 3) -> List[Dict[str, Any]]:
        """
        Fetches and parses articles from curated feeds in the specified category.
        Falls back to local cache gracefully if network is unavailable.
        """
        cat = category.lower().strip()
        all_feeds = self.get_all_feeds()
        feed_targets = all_feeds.get(cat, all_feeds.get("tech", []))

        results = []
        cache = self._load_cache()

        for feed in feed_targets:
            f_name = feed["name"]
            f_url = feed["url"]
            try:
                resp = requests.get(f_url, headers=HEADERS, timeout=5.0)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    items = root.findall(".//item")
                    if not items:
                        # Try Atom entry tags
                        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

                    for it in items[:max_items_per_feed]:
                        title = self._get_node_text(it, ["title", "{http://www.w3.org/2005/Atom}title"])
                        link = self._get_node_text(it, ["link", "{http://www.w3.org/2005/Atom}link"])
                        desc = self._get_node_text(it, ["description", "summary", "{http://www.w3.org/2005/Atom}summary"])

                        # Clean description text
                        clean_desc = re.sub(r"<[^>]+>", "", desc).strip()
                        clean_desc = re.sub(r"\s+", " ", clean_desc)

                        item_data = {
                            "source": f_name,
                            "category": cat,
                            "title": title.strip() if title else "Untitled Alert",
                            "link": link.strip() if link else f_url,
                            "summary": clean_desc[:240] + ("..." if len(clean_desc) > 240 else ""),
                            "timestamp": time.time(),
                        }
                        results.append(item_data)
                        # Update cache
                        item_id = hashlib.md5(f"{f_name}:{title}".encode("utf-8")).hexdigest()
                        cache[item_id] = item_data
            except Exception as e:
                logger.info(f"Feed '{f_name}' offline or timed out: {e}")

        # Update cache file if items retrieved
        if results:
            self._save_cache(cache)
        else:
            # Fallback to cached items for this category
            results = [item for item in cache.values() if item.get("category") == cat][-6:]

        return results

    def _get_node_text(self, parent: ET.Element, tag_names: List[str]) -> str:
        for tag in tag_names:
            node = parent.find(tag)
            if node is not None and node.text:
                return node.text
            elif node is not None and "href" in node.attrib:
                return node.attrib["href"]
        return ""

    def _load_cache(self) -> Dict[str, Any]:
        try:
            if STREAM_CACHE_FILE.exists():
                return json.loads(STREAM_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_cache(self, cache: Dict[str, Any]):
        try:
            # Keep cache bounded to 100 recent entries
            keys = list(cache.keys())[-100:]
            bounded = {k: cache[k] for k in keys}
            STREAM_CACHE_FILE.write_text(json.dumps(bounded, indent=2), encoding="utf-8")
        except Exception:
            pass

    def format_briefing(self, category: str = "tech") -> str:
        """Formats stream items into a concise voice/display briefing."""
        cat = category.lower().strip()
        items = self.fetch_stream_items(cat, max_items_per_feed=2)

        if not items:
            return f"No live information stream updates available for {cat.upper()} at this moment, sir."

        lines = [f"Curated {cat.upper()} Stream Intelligence:"]
        for idx, it in enumerate(items[:4], 1):
            lines.append(f"{idx}. [{it['source']}] {it['title']}")
            if it.get("summary"):
                lines.append(f"   {it['summary']}")

        return "\n".join(lines)


# Global Singleton Instance
web_stream_monitor = WebStreamMonitor()
