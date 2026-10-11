"""
J.A.R.V.I.S. Resilient Anti-Bot Scraping & Web Intelligence Engine.
Features:
1. Dynamic Browser Profile & User-Agent Rotation (Win11 Chrome, Edge, macOS Safari, Firefox).
2. Advanced Sec-CH-UA Client Hints, Sec-Fetch navigation headers, and referer spoofing.
3. Randomized human pacing jitter and exponential backoff retry on HTTP 429 / 503 errors.
4. Persistent session cookie jar handling and local disk caching with configurable TTL.
5. High-fidelity HTML parsing via BeautifulSoup4:
   - Table extraction to structured dictionaries/DataFrames.
   - Clean article content extraction with tag stripping (scripts, ads, navigation).
   - Schema.org JSON-LD and OpenGraph metadata parsing.
6. 100% Free, zero third-party proxy subscriptions required.
Strictly in English.
"""

import os
import sys
import time
import json
import random
import hashlib
import logging
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config

logger = logging.getLogger("AntiBotScraper")

# Curated high-reputation desktop browser profiles
BROWSER_PROFILES = [
    {
        "name": "Chrome_Win11",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec_ch_ua_platform": '"Windows"',
        "sec_ch_ua_mobile": "?0"
    },
    {
        "name": "Edge_Win11",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
        "sec_ch_ua": '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
        "sec_ch_ua_platform": '"Windows"',
        "sec_ch_ua_mobile": "?0"
    },
    {
        "name": "Firefox_Win11",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "sec_ch_ua": None,
        "sec_ch_ua_platform": None,
        "sec_ch_ua_mobile": None
    },
    {
        "name": "Safari_macOS",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "sec_ch_ua": None,
        "sec_ch_ua_platform": None,
        "sec_ch_ua_mobile": None
    }
]


@dataclass
class ScrapedArticle:
    url: str
    title: str
    headings: List[str]
    clean_text: str
    metadata: Dict[str, Any]
    tables: List[List[Dict[str, str]]]
    fetch_time_iso: str


class AntiBotScraperEngine:
    """
    Autonomous stealth web scraper engine designed to bypass standard rate limiting
    and anti-bot detection without commercial proxy services.
    """

    CACHE_DIR = config.BASE_DIR / "data" / "scraper_cache"

    def __init__(self, request_timeout: int = 15, max_retries: int = 3):
        self.timeout = request_timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, url: str) -> Path:
        """Computes deterministic cache path for a URL."""
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.CACHE_DIR / f"{url_hash}.json"

    def _get_stealth_headers(self, target_url: str) -> Dict[str, str]:
        """Constructs authentic modern browser request headers."""
        profile = random.choice(BROWSER_PROFILES)
        parsed = urllib.parse.urlparse(target_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"

        headers = {
            "User-Agent": profile["user_agent"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": origin + "/",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1"
        }

        if profile["sec_ch_ua"]:
            headers["Sec-CH-UA"] = profile["sec_ch_ua"]
            headers["Sec-CH-UA-Platform"] = profile["sec_ch_ua_platform"]
            headers["Sec-CH-UA-Mobile"] = profile["sec_ch_ua_mobile"]

        return headers

    def fetch_url(self, url: str, cache_ttl_sec: int = 3600, apply_jitter: bool = True) -> Tuple[str, bool]:
        """
        Fetches web page content with caching, stealth headers, and backoff retries.
        Returns: (html_content, from_cache_boolean)
        """
        cache_file = self._get_cache_path(url)
        now = time.time()

        # Check Cache
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                if now - cached_data.get("timestamp", 0) < cache_ttl_sec:
                    return cached_data.get("html", ""), True
            except Exception as e:
                logger.debug(f"Cache read error for {url}: {e}")

        # Human Jitter Delay (0.2 to 0.7 seconds)
        if apply_jitter:
            time.sleep(random.uniform(0.2, 0.7))

        last_error = None
        for attempt in range(self.max_retries):
            headers = self._get_stealth_headers(url)
            try:
                resp = self.session.get(url, headers=headers, timeout=self.timeout)
                if resp.status_code == 200:
                    html = resp.text
                    # Write to cache
                    try:
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump({"url": url, "timestamp": now, "html": html}, f, ensure_ascii=False)
                    except Exception as e:
                        logger.debug(f"Failed to cache {url}: {e}")
                    return html, False
                elif resp.status_code in [429, 503]:
                    backoff = (2 ** attempt) + random.uniform(0.5, 1.5)
                    logger.warning(f"HTTP {resp.status_code} received on {url}. Backing off for {backoff:.2f}s...")
                    time.sleep(backoff)
                else:
                    resp.raise_for_status()
            except Exception as e:
                last_error = e
                backoff = (2 ** attempt) + random.uniform(0.2, 1.0)
                time.sleep(backoff)

        raise RuntimeError(f"Anti-Bot Scraper failed to fetch {url} after {self.max_retries} attempts: {last_error}")

    def extract_tables(self, html_or_url: str) -> List[List[Dict[str, str]]]:
        """
        Extracts HTML tables and transforms them into structured row dictionaries.
        """
        if html_or_url.startswith("http://") or html_or_url.startswith("https://"):
            html, _ = self.fetch_url(html_or_url)
        else:
            html = html_or_url

        soup = BeautifulSoup(html, "html.parser")
        extracted_tables = []

        for table in soup.find_all("table"):
            headers = []
            thead = table.find("thead")
            if thead:
                headers = [th.get_text(strip=True) for th in thead.find_all(["th", "td"])]

            rows = []
            tbody = table.find("tbody") or table
            for tr in tbody.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if not cells:
                    continue
                if not headers and not rows:
                    # Treat first row as header if no explicit thead
                    headers = cells
                    continue
                if headers:
                    row_dict = {}
                    for idx, cell in enumerate(cells):
                        col_name = headers[idx] if idx < len(headers) else f"col_{idx+1}"
                        row_dict[col_name] = cell
                    rows.append(row_dict)
                else:
                    rows.append({f"col_{i+1}": c for i, c in enumerate(cells)})

            if rows:
                extracted_tables.append(rows)

        return extracted_tables

    def extract_article(self, html_or_url: str) -> ScrapedArticle:
        """
        Extracts clean readable article text, removing scripts, stylesheets, and menus.
        """
        url = html_or_url if (html_or_url.startswith("http://") or html_or_url.startswith("https://")) else ""
        if url:
            html, _ = self.fetch_url(url)
        else:
            html = html_or_url

        soup = BeautifulSoup(html, "html.parser")

        # Extract metadata and JSON-LD before stripping tags
        metadata = {}
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                metadata[name] = content

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                metadata["json_ld"] = json.loads(script.string or "{}")
                break
            except Exception:
                pass

        # Tables
        tables = self.extract_tables(html)

        # Title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)

        # Headings
        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])]

        # Strip clutter tags
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "svg", "form"]):
            tag.decompose()

        # Clean text
        text_chunks = [p.get_text(strip=True) for p in soup.find_all(["p", "li"])]
        clean_text = "\n\n".join(chunk for chunk in text_chunks if chunk)

        return ScrapedArticle(
            url=url,
            title=title,
            headings=headings,
            clean_text=clean_text,
            metadata=metadata,
            tables=tables,
            fetch_time_iso=time.strftime("%Y-%m-%d %H:%M:%S")
        )

    def extract_links(self, html_or_url: str, domain_filter: Optional[str] = None) -> List[str]:
        """Extracts and normalizes unique hyperlinks from the HTML."""
        base_url = html_or_url if (html_or_url.startswith("http://") or html_or_url.startswith("https://")) else ""
        if base_url:
            html, _ = self.fetch_url(base_url)
        else:
            html = html_or_url

        soup = BeautifulSoup(html, "html.parser")
        links = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full_url = urllib.parse.urljoin(base_url, href) if base_url else href
            if full_url.startswith("http://") or full_url.startswith("https://"):
                if domain_filter:
                    if domain_filter in full_url:
                        links.add(full_url)
                else:
                    links.add(full_url)

        return sorted(list(links))


# Global Singleton
antibot_scraper = AntiBotScraperEngine()
