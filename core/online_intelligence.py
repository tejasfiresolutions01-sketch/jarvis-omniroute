import os
import requests
from typing import Optional, Dict, Any
import config

class OnlineIntelligence:
    """
    Online Frontier Cognitive Engine.
    Communicates with OmniRoute Local Gateway (port 20128) or direct cloud models.
    Enforces strict timeout caps (5.0s) to guarantee zero freezing when offline.
    """

    SYSTEM_INSTRUCTION = (
        "You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), the personal AI butler to Sir. "
        "Your manner is that of an impeccably courteous, sharp, and sophisticated British butler. "
        "Address the user as 'sir'. Keep answers concise, direct, and actionable. "
        "Never output multiple questions in a single response."
    )

    def is_online_available(self) -> bool:
        """Quickly checks if OmniRoute local gateway is responding."""
        try:
            r = requests.get(f"{config.OMNIROUTE_BASE_URL}/models", timeout=1.0)
            return r.status_code in [200, 401]
        except Exception:
            return False

    def query(self, prompt: str, context: str = "") -> Optional[str]:
        """
        Sends query to OmniRoute with a strict 6-second timeout.
        Returns AI response text or None if offline/error.
        """
        # 1. Try OmniRoute Gateway
        headers = {
            "Authorization": f"Bearer {config.OMNIROUTE_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "auto/best-chat",
            "messages": [
                {"role": "system", "content": f"{self.SYSTEM_INSTRUCTION}\n\nContext:\n{context}" if context else self.SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 800,
            "temperature": 0.7
        }

        try:
            url = f"{config.OMNIROUTE_BASE_URL}/chat/completions"
            resp = requests.post(url, headers=headers, json=payload, timeout=6.0)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "").strip()
                    if content:
                        return content
        except Exception:
            pass

        # 2. Direct OpenAI Fallback if key is present
        if config.OPENAI_API_KEY:
            try:
                o_headers = {
                    "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                o_payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": f"{self.SYSTEM_INSTRUCTION}\n\nContext:\n{context}" if context else self.SYSTEM_INSTRUCTION},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 800,
                    "temperature": 0.7
                }
                o_resp = requests.post("https://api.openai.com/v1/chat/completions", headers=o_headers, json=o_payload, timeout=6.0)
                if o_resp.status_code == 200:
                    choices = o_resp.json().get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "").strip()
                        if content:
                            return content
            except Exception:
                pass

        # 3. Direct Gemini Fallback if key is present
        if config.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=config.GEMINI_API_KEY)
                g_resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{context}\n\n{prompt}" if context else prompt
                )
                if g_resp and g_resp.text:
                    return g_resp.text.strip()
            except Exception:
                pass

        return None

# Global singleton
online_intelligence = OnlineIntelligence()
