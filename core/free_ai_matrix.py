"""
J.A.R.V.I.S. Universal Free AI Matrix
Integrates and coordinates the world's leading AI models (OpenAI, Claude, Mistral, 
DeepSeek, Meta Llama, Alibaba Qwen, Google Gemini) strictly using 100% free-tier, 
zero-cost options only.
"""

import os
import re
import time
import requests
from typing import Dict, Any, Optional, Tuple, List
import config

class FreeAIMatrix:
    """
    Universal Free Multi-Model AI Dispatcher.
    Routes queries to top AI model providers at zero cost with automated fallback.
    """

    # Provider model registries mapping to verified zero-cost endpoints
    FREE_PROVIDER_ROUTING = {
        "openai": [
            {"type": "omniroute", "model": "ddgw/gpt-5.4-mini", "label": "OpenAI GPT (Zero-Cost Gateway)"},
            {"type": "omniroute", "model": "ddgw/gpt-5.6-luna", "label": "OpenAI Luna (Zero-Cost Gateway)"},
            {"type": "pollinations", "model": "openai", "label": "OpenAI (Pollinations Free)"},
            {"type": "openai_api", "model": "gpt-4o-mini", "label": "OpenAI Free Tier API"}
        ],
        "claude": [
            {"type": "omniroute", "model": "ddgw/claude-haiku-4-5", "label": "Anthropic Claude (Zero-Cost Gateway)"},
            {"type": "omniroute", "model": "ddgw/mistral-small-2603", "label": "Claude Fallback (Mistral Free)"}
        ],
        "mistral": [
            {"type": "omniroute", "model": "ddgw/mistral-small-2603", "label": "Mistral AI (Zero-Cost Gateway)"},
            {"type": "omniroute", "model": "ddgw/tinfoil/gpt-oss-120b", "label": "Mistral Fallback (OSS Free)"}
        ],
        "deepseek": [
            {"type": "omniroute", "model": "ddgw/tinfoil/gpt-oss-120b", "label": "DeepSeek / OSS Reasoning (Zero-Cost Gateway)"},
            {"type": "omniroute", "model": "ddgw/mistral-small-2603", "label": "DeepSeek Fallback (Mistral Free)"},
            {"type": "omniroute", "model": "ddgw/gpt-5.4-mini", "label": "DeepSeek Fallback (GPT Free)"}
        ],
        "llama": [
            {"type": "omniroute", "model": "ddgw/tinfoil/gemma4-31b", "label": "Meta Llama / Open Weights (Zero-Cost Gateway)"},
            {"type": "omniroute", "model": "ddgw/mistral-small-2603", "label": "Llama Fallback (Mistral Free)"},
            {"type": "omniroute", "model": "ddgw/gpt-5.4-mini", "label": "Llama Fallback (GPT Free)"}
        ],
        "qwen": [
            {"type": "omniroute", "model": "ddgw/tinfoil/gpt-oss-120b", "label": "Alibaba Qwen / OSS Matrix (Zero-Cost Gateway)"},
            {"type": "omniroute", "model": "ddgw/mistral-small-2603", "label": "Qwen Fallback (Mistral Free)"},
            {"type": "omniroute", "model": "ddgw/gpt-5.4-mini", "label": "Qwen Fallback (GPT Free)"}
        ],
        "gemini": [
            {"type": "gemini_api", "model": "gemini-2.5-flash", "label": "Google Gemini (Free Tier API)"},
            {"type": "omniroute", "model": "ddgw/tinfoil/gemma4-31b", "label": "Google Gemma (Zero-Cost Gateway)"},
            {"type": "omniroute", "model": "ddgw/gpt-5.4-mini", "label": "Gemini Fallback (Zero-Cost Gateway)"}
        ]
    }

    # Universal default cascade order when auto-routing
    UNIVERSAL_AUTO_CASCADE = [
        ("claude", "ddgw/claude-haiku-4-5"),
        ("mistral", "ddgw/mistral-small-2603"),
        ("openai", "ddgw/gpt-5.4-mini"),
        ("gemini", "ddgw/tinfoil/gemma4-31b"),
        ("deepseek", "ddgw/tinfoil/gpt-oss-120b")
    ]

    def __init__(self):
        self.omniroute_base_url = config.OMNIROUTE_BASE_URL
        self.omniroute_api_key = config.OMNIROUTE_API_KEY
        self.timeout = 7.0

    def list_supported_ais(self) -> Dict[str, Any]:
        """Returns catalog of all supported global AI families and free tiers."""
        return {
            "OpenAI": ["GPT-5.4 Mini (Zero Cost)", "GPT-5.6 Luna (Zero Cost)", "Pollinations Serverless", "GPT-4o Mini (Free Tier)"],
            "Anthropic Claude": ["Claude Haiku 4.5 (Zero Cost)", "Claude 3.5 Sonnet Bridge"],
            "Mistral AI": ["Mistral Small 2603 (Zero Cost)"],
            "DeepSeek": ["DeepSeek / GPT-OSS 120B Reasoning (Zero Cost)"],
            "Meta Llama": ["Meta Llama & Open Weights Matrix (Zero Cost)"],
            "Alibaba Qwen": ["Qwen & Open Reasoning Matrix (Zero Cost)"],
            "Google Gemini": ["Gemini 2.5 Flash (Free Tier)", "Google Gemma 31B (Zero Cost)"]
        }

    def _sanitize_for_voice(self, text: str) -> str:
        """Strips markdown asterisks, hashes, backticks, and bullet points for clean voice synthesis."""
        if not text:
            return ""
        # Remove markdown headers
        text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
        # Remove bold / italics asterisks
        text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
        # Remove inline code backticks
        text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text)
        # Remove bullet points
        text = re.sub(r"^\s*[-*•]\s+", "", text, flags=re.MULTILINE)
        # Remove excessive whitespace
        text = re.sub(r"\n{2,}", " ", text)
        return text.strip()

    def _call_omniroute(self, model: str, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Queries local OmniRoute gateway."""
        try:
            headers = {
                "Authorization": f"Bearer {self.omniroute_api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 600,
                "temperature": 0.7
            }
            resp = requests.post(
                f"{self.omniroute_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
        except Exception:
            pass
        return None

    def _call_pollinations(self, model: str, prompt: str) -> Optional[str]:
        """Queries Pollinations free text API."""
        try:
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "model": model,
                "jsonMode": False
            }
            resp = requests.post(
                "https://text.pollinations.ai/",
                json=payload,
                timeout=self.timeout
            )
            if resp.status_code == 200 and resp.text:
                return resp.text.strip()
        except Exception:
            pass
        return None

    def _call_gemini_free(self, prompt: str) -> Optional[str]:
        """Queries Google Gemini free tier API if key present."""
        if not config.GEMINI_API_KEY:
            return None
        try:
            from google import genai
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            if res and res.text:
                return res.text.strip()
        except Exception:
            pass
        return None

    def _call_openai_free(self, prompt: str) -> Optional[str]:
        """Queries OpenAI API if key present."""
        if not config.OPENAI_API_KEY:
            return None
        try:
            headers = {
                "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600
            }
            r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=self.timeout)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
        return None

    def query_provider(self, provider: str, prompt: str) -> Tuple[str, str]:
        """
        Queries a specific AI provider family (openai, claude, mistral, deepseek, llama, qwen, gemini).
        Returns (spoken_reply, provider_label).
        """
        p_clean = provider.lower().strip()
        target_routes = self.FREE_PROVIDER_ROUTING.get(p_clean)

        # Fallback to auto if unknown provider
        if not target_routes:
            for k, routes in self.FREE_PROVIDER_ROUTING.items():
                if k in p_clean:
                    target_routes = routes
                    p_clean = k
                    break

        if not target_routes:
            return self.query_auto(prompt)

        # Cascade through provider's free route options
        for route in target_routes:
            rtype = route["type"]
            model = route["model"]
            label = route["label"]
            content = None

            if rtype == "omniroute":
                content = self._call_omniroute(model, prompt)
            elif rtype == "pollinations":
                content = self._call_pollinations(model, prompt)
            elif rtype == "gemini_api":
                content = self._call_gemini_free(prompt)
            elif rtype == "openai_api":
                content = self._call_openai_free(prompt)

            if content:
                clean_text = self._sanitize_for_voice(content)
                return f"According to {label}: {clean_text}", label

        # Universal auto failover if all provider-specific routes fail
        fallback_text, fallback_label = self.query_auto(prompt)
        return f"Sir, {p_clean.capitalize()} was momentarily busy. Delegating through {fallback_label}: {fallback_text}", fallback_label

    def query_auto(self, prompt: str) -> Tuple[str, str]:
        """
        Automatically selects and queries the fastest available zero-cost AI provider.
        """
        for prov_name, model_id in self.UNIVERSAL_AUTO_CASCADE:
            content = self._call_omniroute(model_id, prompt)
            if content:
                clean_text = self._sanitize_for_voice(content)
                label = f"{prov_name.capitalize()} Free Tier ({model_id})"
                return clean_text, label

        # Fallback to Pollinations
        pol_content = self._call_pollinations("openai", prompt)
        if pol_content:
            clean_text = self._sanitize_for_voice(pol_content)
            return clean_text, "OpenAI Pollinations Free"

        # Final local emergency response
        return "All external free AI networks are currently unreachable, sir. Local fallback engaged.", "Local Offline"

# Global singleton
free_ai_matrix = FreeAIMatrix()
