"""
J.A.R.V.I.S. Web Intelligence & Search Tools.
Provides zero-cost web search and content retrieval using DuckDuckGo APIs and web scraping.
"""

import re
import urllib.parse
import requests
from typing import Dict, Any, List

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def search_web(query: str, max_results: int = 5) -> str:
    """
    Searches the web via DuckDuckGo and returns a synthesized summary with citations.
    """
    clean_query = query.strip()
    if not clean_query:
        return "No search query provided."

    results = []

    # 1. Try DuckDuckGo Instant Answer API
    try:
        api_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(clean_query)}&format=json&no_html=1&skip_disambig=1"
        resp = requests.get(api_url, headers=HEADERS, timeout=4.0)
        if resp.status_code == 200:
            data = resp.json()
            abstract = data.get("AbstractText", "").strip()
            answer = data.get("Answer", "").strip()
            source = data.get("AbstractSource", "")
            url = data.get("AbstractURL", "")

            if answer:
                results.append(f"Direct Answer: {answer}")
            if abstract:
                results.append(f"Summary ({source}): {abstract} [Source: {url}]")

            # Check related topics
            related = data.get("RelatedTopics", [])
            for item in related[:3]:
                if isinstance(item, dict) and "Text" in item:
                    results.append(f"- {item['Text']}")
    except Exception:
        pass

    # 2. Try DuckDuckGo Lite / HTML if instant answer was sparse
    if len(results) < 2:
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(clean_query)}"
            resp = requests.post(search_url, data={"q": clean_query}, headers=HEADERS, timeout=5.0)
            if resp.status_code in [200, 202]:
                text = resp.text
                # Extract snippets and titles
                snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', text, re.DOTALL)
                titles = re.findall(r'<a class="result__url[^>]*>(.*?)</a>', text, re.DOTALL)
                for i in range(min(len(snippets), max_results)):
                    clean_s = re.sub(r'<[^>]+>', '', snippets[i]).strip()
                    if clean_s and clean_s not in results:
                        results.append(f"- {clean_s}")
        except Exception:
            pass

    if not results:
        return f"Sir, I queried the web for '{clean_query}', but no public results were returned within the response window."

    return f"Web search results for '{clean_query}':\n" + "\n".join(results[:max_results])

def fetch_webpage_content(url: str, max_chars: int = 1500) -> str:
    """
    Fetches and extracts clean readable text from a URL.
    """
    try:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        resp = requests.get(url, headers=HEADERS, timeout=6.0)
        if resp.status_code != 200:
            return f"Failed to retrieve URL ({resp.status_code})"

        # Strip scripts and styles
        html = re.sub(r'<script.*?</script>', ' ', resp.text, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style.*?</style>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
        # Strip all HTML tags
        clean_text = re.sub(r'<[^>]+>', ' ', html)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        return clean_text[:max_chars]
    except requests.exceptions.Timeout:
        return "Error fetching webpage: Request timed out after 6.0s."
    except requests.exceptions.HTTPError as e:
        return f"Error fetching webpage: HTTP protocol error ({str(e)})"
    except requests.exceptions.ConnectionError:
        return "Error fetching webpage: Host unreachable or connection failed."
    except requests.exceptions.RequestException as e:
        return f"Error fetching webpage: Network exception ({str(e)})"
    except Exception as e:
        return f"Error fetching webpage: {str(e)}"
