"""
J.A.R.V.I.S. Social Media Dispatcher & Direct Multi-Platform Publisher.
Features:
1. Hybrid Architecture (100% Free Plan Default + Optional Direct API Mode):
   - Zero-Credential 1-Click Web Intent Dispatch: Immediately prepares and launches pre-filled
     native composer URLs for LinkedIn, X (Twitter), Facebook, WhatsApp, and Reddit.
   - Direct Background API Publishing: Automatically dispatches directly via official APIs if
     developer tokens are configured in .env (Meta Graph API, X API v2, LinkedIn REST API).
2. Social Content Formatter:
   - Formats character-limited, hashtag-optimized posts for Twitter (280 chars), LinkedIn (B2B longform),
     Facebook, and WhatsApp message broadcasts.
3. Scheduled Outbox Queue:
   - Maintains persistent outbox in data/social_media_queue.json for draft review and delivery logs.
"""

import json
import logging
import os
import re
import sys
import time
import urllib.parse
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

logger = logging.getLogger("SocialMediaAgent")

SOCIAL_QUEUE_FILE = config.DATA_DIR / "social_media_queue.json"


class SocialMediaAgent:
    """Manages publishing, formatting, and queueing across social media networks."""

    SUPPORTED_PLATFORMS = ["twitter", "x", "linkedin", "facebook", "meta", "whatsapp", "reddit"]

    def __init__(self):
        self._ensure_storage()

    def _ensure_storage(self):
        try:
            config.DATA_DIR.mkdir(parents=True, exist_ok=True)
            if not SOCIAL_QUEUE_FILE.exists():
                init_data = {"queue": [], "history": []}
                SOCIAL_QUEUE_FILE.write_text(json.dumps(init_data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_data(self) -> Dict[str, Any]:
        try:
            if SOCIAL_QUEUE_FILE.exists():
                return json.loads(SOCIAL_QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"queue": [], "history": []}

    def _save_data(self, data: Dict[str, Any]):
        try:
            SOCIAL_QUEUE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Error saving social queue: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Platform Specific Intent Generators (100% Free, Zero Auth Required)
    # ─────────────────────────────────────────────────────────────────────────
    def generate_intent_url(self, platform: str, text: str, url: Optional[str] = None, recipient: Optional[str] = None) -> str:
        """Generates frictionless, pre-filled web composer URL for one-click publishing."""
        p = platform.lower().strip()
        encoded_text = urllib.parse.quote(text.strip())
        encoded_url = urllib.parse.quote(url.strip(), safe="") if url else ""

        if p in ["twitter", "x"]:
            # Twitter / X Web Intent
            base = f"https://twitter.com/intent/tweet?text={encoded_text}"
            if encoded_url:
                base += f"&url={encoded_url}"
            return base

        elif p == "linkedin":
            # LinkedIn Web Share Intent
            if encoded_url:
                return f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}"
            else:
                # Direct feed feed launch with text query
                return f"https://www.linkedin.com/feed/?shareActive=true&text={encoded_text}"

        elif p in ["facebook", "meta"]:
            # Facebook Web Sharer
            base = "https://www.facebook.com/sharer/sharer.php?"
            if encoded_url:
                base += f"u={encoded_url}&quote={encoded_text}"
            else:
                base += f"u=https%3A%2F%2Fwww.facebook.com&quote={encoded_text}"
            return base

        elif p == "whatsapp":
            # WhatsApp Web / Desktop Direct Send (Digits only international format)
            phone_clean = re.sub(r"[^0-9]", "", recipient) if recipient else ""
            if phone_clean:
                return f"https://api.whatsapp.com/send?phone={phone_clean}&text={encoded_text}"
            return f"https://api.whatsapp.com/send?text={encoded_text}"

        elif p == "reddit":
            # Reddit Submit Intent
            title = text[:80]
            encoded_title = urllib.parse.quote(title)
            return f"https://www.reddit.com/submit?title={encoded_title}&text={encoded_text}"

        return f"https://www.google.com/search?q={encoded_text}"

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Direct API Dispatch (If Credentials Configured in .env)
    # ─────────────────────────────────────────────────────────────────────────
    def publish_direct_api(self, platform: str, text: str) -> Tuple[bool, str]:
        """Attempts background publishing if user has registered API tokens in .env."""
        p = platform.lower().strip()

        if p in ["twitter", "x"]:
            bearer = os.getenv("TWITTER_BEARER_TOKEN", "")
            if not bearer:
                return False, "No TWITTER_BEARER_TOKEN configured in .env."
            try:
                endpoint = "https://api.twitter.com/2/tweets"
                resp = requests.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {bearer}", "Content-Type": "application/json"},
                    json={"text": text[:280]},
                    timeout=8.0,
                )
                if resp.status_code in [200, 201]:
                    return True, "Tweet published directly via X API v2."
                return False, f"X API returned status {resp.status_code}: {resp.text}"
            except Exception as e:
                return False, f"X API error: {str(e)}"

        elif p in ["facebook", "meta"]:
            page_token = os.getenv("META_PAGE_ACCESS_TOKEN", "")
            page_id = os.getenv("META_PAGE_ID", "")
            if not page_token or not page_id:
                return False, "No META_PAGE_ACCESS_TOKEN or META_PAGE_ID in .env."
            try:
                endpoint = f"https://graph.facebook.com/v19.0/{page_id}/feed"
                resp = requests.post(endpoint, data={"message": text, "access_token": page_token}, timeout=8.0)
                if resp.status_code == 200:
                    return True, "Post published directly to Meta Facebook Page."
                return False, f"Meta Graph API status {resp.status_code}: {resp.text}"
            except Exception as e:
                return False, f"Meta API error: {str(e)}"

        elif p == "linkedin":
            li_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
            li_author = os.getenv("LINKEDIN_PERSON_URN", "")
            if not li_token or not li_author:
                return False, "No LINKEDIN_ACCESS_TOKEN or LINKEDIN_PERSON_URN in .env."
            try:
                endpoint = "https://api.linkedin.com/v2/ugcPosts"
                headers = {"Authorization": f"Bearer {li_token}", "X-Restli-Protocol-Version": "2.0.0"}
                body = {
                    "author": li_author,
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {"text": text},
                            "shareMediaCategory": "NONE",
                        }
                    },
                    "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
                }
                resp = requests.post(endpoint, headers=headers, json=body, timeout=8.0)
                if resp.status_code in [200, 201]:
                    return True, "Post published directly to LinkedIn feed."
                return False, f"LinkedIn API status {resp.status_code}: {resp.text}"
            except Exception as e:
                return False, f"LinkedIn API error: {str(e)}"

        return False, f"Direct background API not implemented for platform '{platform}'."

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Unified Publisher & Orchestrator
    # ─────────────────────────────────────────────────────────────────────────
    def publish(
        self,
        platform: str,
        text: str,
        url: Optional[str] = None,
        recipient: Optional[str] = None,
        auto_open: bool = True,
    ) -> Dict[str, Any]:
        """
        Publishes content to the designated social network.
        Prefers direct API if configured; otherwise opens 1-click native web composer.
        """
        p = platform.lower().strip()
        clean_text = text.strip()

        # Try direct API first
        api_ok, api_msg = self.publish_direct_api(p, clean_text)
        if api_ok:
            self._log_history(p, clean_text, "DIRECT_API", api_msg)
            return {
                "success": True,
                "mode": "DIRECT_API",
                "platform": p,
                "message": api_msg,
            }

        # Fallback to zero-credential 1-click web intent
        intent_url = self.generate_intent_url(p, clean_text, url=url, recipient=recipient)
        if auto_open:
            webbrowser.open(intent_url)

        msg = f"Opened pre-filled 1-click {p.capitalize()} composer in your browser, sir. Ready for instant dispatch."
        self._log_history(p, clean_text, "WEB_INTENT", msg)

        return {
            "success": True,
            "mode": "WEB_INTENT",
            "platform": p,
            "intent_url": intent_url,
            "message": msg,
        }

    def _log_history(self, platform: str, text: str, mode: str, details: str):
        data = self._load_data()
        data["history"].append({
            "platform": platform,
            "text": text[:180] + ("..." if len(text) > 180 else ""),
            "mode": mode,
            "details": details,
            "timestamp": time.time(),
            "time_str": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        # Keep last 50 entries
        data["history"] = data["history"][-50:]
        self._save_data(data)

    def format_post(self, platform: str, topic: str, hashtags: Optional[List[str]] = None) -> str:
        """Formats optimized copy tailored to specific platform constraints."""
        p = platform.lower().strip()
        tags = " ".join([f"#{h.strip('#')}" for h in (hashtags or ["Tech", "Innovation"])])

        if p in ["twitter", "x"]:
            tag_suffix = f"\n\n{tags}" if tags else ""
            avail = 280 - len(tag_suffix)
            trimmed_topic = topic[:max(avail, 0)].rstrip()
            return f"{trimmed_topic}{tag_suffix}"
        elif p == "linkedin":
            return (
                f"Excited to share insights on {topic}.\n\n"
                f"Continuous system optimization and architectural modularity remain essential for reliable software operations.\n\n"
                f"{tags}\n#Engineering #Technology"
            )
        elif p in ["facebook", "meta"]:
            return f"{topic}\n\nCheck out the latest developments!\n{tags}"
        elif p == "whatsapp":
            return f"*Update:* {topic}\n\n_Generated via J.A.R.V.I.S._"
        return f"{topic} {tags}"

    def get_status(self) -> Dict[str, Any]:
        data = self._load_data()
        return {
            "supported_platforms": self.SUPPORTED_PLATFORMS,
            "history_count": len(data.get("history", [])),
            "recent_posts": data.get("history", [])[-5:],
            "api_keys_configured": {
                "twitter": bool(os.getenv("TWITTER_BEARER_TOKEN")),
                "meta": bool(os.getenv("META_PAGE_ACCESS_TOKEN")),
                "linkedin": bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
            },
        }


# Global Singleton Instance
social_media_agent = SocialMediaAgent()
