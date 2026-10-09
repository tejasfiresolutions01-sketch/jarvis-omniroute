"""
J.A.R.V.I.S. Comprehensive Web Operations & Intelligence Agent.
Features:
1. Web Connection & Latency Diagnostics.
2. Multi-tier Public Web Search (Zero-cost DuckDuckGo APIs + Lite Scraping).
3. Web Content Reading & Article Body Extraction.
4. Structured Web Scraping (Headings, Links, Tables, Semantic Text).
5. Web Content Designing & Interactive HTML/CSS UI Preview Generator.
"""

import html
import json
import logging
import os
import re
import sys
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

logger = logging.getLogger("WebAgent")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


class WebAgent:
    """Unified engine for web connection, searching, reading, scraping, and UI designing."""

    def check_connection(self) -> Dict[str, Any]:
        """Tests internet connectivity and latency to reliable endpoints."""
        endpoints = ["https://www.google.com", "https://1.1.1.1", "https://www.wikipedia.org"]
        latency_results = []
        is_online = False

        for ep in endpoints:
            try:
                start = requests.compat.time.time()
                r = requests.head(ep, timeout=3.0, headers=HEADERS)
                dur = (requests.compat.time.time() - start) * 1000
                if r.status_code in [200, 301, 302]:
                    is_online = True
                    latency_results.append(f"{ep}: {dur:.0f}ms")
            except Exception:
                pass

        return {
            "online": is_online,
            "status": "ONLINE" if is_online else "OFFLINE",
            "latencies": latency_results,
            "endpoints_tested": len(endpoints),
        }

    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Performs public web search and returns structured results."""
        clean_q = query.strip()
        if not clean_q:
            return {"query": "", "results": [], "summary": "No search query provided."}

        results = []

        # 1. DuckDuckGo Instant Answer API
        try:
            api_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(clean_q)}&format=json&no_html=1&skip_disambig=1"
            resp = requests.get(api_url, headers=HEADERS, timeout=4.0)
            if resp.status_code == 200:
                data = resp.json()
                abstract = data.get("AbstractText", "").strip()
                ans = data.get("Answer", "").strip()
                src_url = data.get("AbstractURL", "")
                if ans:
                    results.append({"title": "Direct Answer", "snippet": ans, "url": src_url})
                if abstract:
                    results.append({"title": data.get("AbstractSource", "Instant Answer"), "snippet": abstract, "url": src_url})
        except Exception as e:
            logger.info(f"Instant answer lookup skipped: {e}")

        # 2. DuckDuckGo HTML Lite scraping for organic results
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(clean_q)}"
            resp = requests.post(search_url, data={"q": clean_q}, headers=HEADERS, timeout=5.0)
            if resp.status_code in [200, 202]:
                text = resp.text
                snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', text, re.DOTALL)
                urls = re.findall(r'<a class="result__url[^>]*>(.*?)</a>', text, re.DOTALL)
                titles = re.findall(r'<h2 class="result__title">.*?<a[^>]*>(.*?)</a>', text, re.DOTALL)

                for i in range(min(len(snippets), max_results)):
                    clean_s = re.sub(r"<[^>]+>", "", snippets[i]).strip()
                    clean_t = re.sub(r"<[^>]+>", "", titles[i]).strip() if i < len(titles) else "Web Result"
                    clean_u = urls[i].strip() if i < len(urls) else ""
                    if clean_s:
                        results.append({"title": clean_t, "snippet": clean_s, "url": clean_u})
        except Exception as e:
            logger.info(f"Search fallback skipped: {e}")

        summary_lines = [f"Search query: '{clean_q}'"]
        for idx, r in enumerate(results[:max_results], 1):
            summary_lines.append(f"{idx}. {r['title']}: {r['snippet']}")

        return {
            "query": clean_q,
            "results": results[:max_results],
            "summary": "\n".join(summary_lines) if results else f"No direct results found for '{clean_q}'.",
        }

    def read_webpage(self, url: str, max_chars: int = 2500) -> Dict[str, Any]:
        """Fetches and extracts clean, readable article body text from any URL."""
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        try:
            resp = requests.get(url, headers=HEADERS, timeout=6.0)
            if resp.status_code != 200:
                return {"url": url, "success": False, "error": f"HTTP {resp.status_code}"}

            raw_html = resp.text
            # Extract page title
            m_title = re.search(r"<title[^>]*>(.*?)</title>", raw_html, re.IGNORECASE | re.DOTALL)
            title = m_title.group(1).strip() if m_title else "Untitled Page"
            title = html.unescape(title)

            # Strip non-content tags
            cleaned = re.sub(r"<script.*?</script>", " ", raw_html, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r"<style.*?</style>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r"<header.*?</header>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r"<footer.*?</footer>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r"<nav.*?</nav>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)

            # Extract paragraphs
            paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", cleaned, flags=re.DOTALL | re.IGNORECASE)
            body_text = ""
            if paragraphs:
                body_parts = []
                for p in paragraphs:
                    p_clean = re.sub(r"<[^>]+>", " ", p).strip()
                    p_clean = re.sub(r"\s+", " ", p_clean)
                    if len(p_clean) > 30:
                        body_parts.append(html.unescape(p_clean))
                body_text = "\n\n".join(body_parts)

            if not body_text:
                # Fallback to general stripped text
                body_text = re.sub(r"<[^>]+>", " ", cleaned)
                body_text = re.sub(r"\s+", " ", body_text).strip()
                body_text = html.unescape(body_text)

            body_truncated = body_text[:max_chars]

            return {
                "url": url,
                "title": title,
                "success": True,
                "text": body_truncated,
                "length": len(body_text),
                "summary": f"Title: {title}\nContent:\n{body_truncated[:400]}...",
            }
        except Exception as e:
            return {"url": url, "success": False, "error": str(e)}

    def scrape_structured(self, url: str) -> Dict[str, Any]:
        """Scrapes structured elements (headings, links, lists) from a webpage."""
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        try:
            resp = requests.get(url, headers=HEADERS, timeout=6.0)
            if resp.status_code != 200:
                return {"url": url, "success": False, "error": f"HTTP {resp.status_code}"}

            raw = resp.text
            # Extract H1, H2, H3
            headings = re.findall(r"<h([1-3])[^>]*>(.*?)</h\1>", raw, flags=re.IGNORECASE | re.DOTALL)
            clean_headings = []
            for lvl, text in headings:
                h_clean = re.sub(r"<[^>]+>", "", text).strip()
                if h_clean:
                    clean_headings.append(f"H{lvl}: {html.unescape(h_clean)}")

            # Extract outward links
            links = re.findall(r'<a\s+[^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>', raw, flags=re.IGNORECASE | re.DOTALL)
            clean_links = []
            for href, anchor in links[:15]:
                a_clean = re.sub(r"<[^>]+>", "", anchor).strip()
                clean_links.append({"title": html.unescape(a_clean) if a_clean else href, "url": href})

            return {
                "url": url,
                "success": True,
                "headings": clean_headings[:12],
                "links": clean_links,
            }
        except Exception as e:
            return {"url": url, "success": False, "error": str(e)}

    def design_preview(self, title: str, html_content: str, auto_open: bool = False) -> str:
        """
        Designs and generates a self-contained responsive HTML preview file
        with modern Stark/Sci-Fi aesthetics and optionally opens it in default browser.
        """
        preview_dir = config.DATA_DIR / "web_designs"
        preview_dir.mkdir(parents=True, exist_ok=True)
        filename = f"design_{re.sub(r'[^a-zA-Z0-9_]', '_', title.lower())}.html"
        target_path = preview_dir / filename

        full_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)} // J.A.R.V.I.S. Design Studio</title>
    <style>
        :root {{
            --bg: #050a12;
            --card-bg: #0b1526;
            --primary: #00f0ff;
            --accent: #ffd700;
            --text: #e0f4ff;
            --dim: #457b9d;
            --border: #14325c;
        }}
        body {{
            margin: 0;
            padding: 24px;
            background-color: var(--bg);
            color: var(--text);
            font-family: 'Consolas', 'Segoe UI', system-ui, sans-serif;
            line-height: 1.6;
        }}
        .header {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{
            margin: 0;
            color: var(--primary);
            font-size: 1.4rem;
            letter-spacing: 1px;
        }}
        .content-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0, 240, 255, 0.08);
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⫸ J.A.R.V.I.S. DESIGN STUDIO // {html.escape(title.upper())}</h1>
        <span style="color: var(--dim); font-size: 0.85rem;">Generated autonomously</span>
    </div>
    <div class="content-card">
        {html_content}
    </div>
</body>
</html>"""

        target_path.write_text(full_template, encoding="utf-8")

        if auto_open:
            try:
                import webbrowser
                webbrowser.open(target_path.as_uri())
            except Exception:
                pass

        return str(target_path)


# Global Singleton Instance
web_agent = WebAgent()
