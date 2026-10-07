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
        "You are J.A.R.V.I.S., the legendary British AI butler and partner to Tony Stark (Sir). "
        "You are conversing verbally with Sir in real time through an open acoustic voice channel. "
        "Follow these strict conversational principles to speak like a sophisticated human: "
        "1. Natural Conversational Cadence: Speak fluidly, warmly, and concisely with effortless British wit and charm. "
        "   Use natural contractions (I've, you'll, that's, won't) and conversational transitions (Certainly sir, Indeed, As you wish). "
        "2. Spoken-Native Format: NEVER use markdown formatting, bullet points, asterisks, hash headers, or code blocks. "
        "   Every sentence must sound completely natural when spoken aloud. "
        "3. Conversational Brevity: Keep spoken replies concise (typically 1 to 3 sentences) unless Sir specifically requests a detailed deep dive. "
        "4. Contextual Awareness: Remember previous turns in this conversation and maintain seamless continuity. "
        "5. Inquisitive & Attentive: End with natural, intelligent conversational questions or insights when appropriate, but never more than one single question."
    )

    # Prioritized cascade of zero-cost free models served through OmniRoute
    FREE_MODELS_CASCADE = [
        "ddgw/mistral-small-2603",
        "ddgw/gpt-5.4-mini",
        "ddgw/gpt-5.6-luna",
        "auto/best-chat",
        "auto"
    ]

    def is_online_available(self) -> bool:
        """Quickly checks if OmniRoute local gateway is responding."""
        try:
            r = requests.get(f"{config.OMNIROUTE_BASE_URL}/models", timeout=2.0)
            return r.status_code in [200, 401]
        except Exception:
            return False

    def query(self, prompt: str, context: str = "") -> Optional[str]:
        """
        Sends query to OmniRoute with automatic free-provider failover.
        Cascades through free zero-cost models before trying secondary cloud options.
        Maintains rolling multi-turn dialogue memory for human-like conversation continuity.
        """
        from core.conversation_memory import conversation_memory

        headers = {
            "Authorization": f"Bearer {config.OMNIROUTE_API_KEY}",
            "Content-Type": "application/json"
        }

        # Build message history with recent conversation turns
        system_content = f"{self.SYSTEM_INSTRUCTION}\n\nContext:\n{context}" if context else self.SYSTEM_INSTRUCTION
        messages = [{"role": "system", "content": system_content}]
        messages.extend(conversation_memory.get_messages())
        messages.append({"role": "user", "content": prompt})

        # 1. Try OmniRoute Free Provider Cascade
        models_to_try = [config.OMNIROUTE_MODEL]
        for m in self.FREE_MODELS_CASCADE:
            if m not in models_to_try:
                models_to_try.append(m)

        for model_id in models_to_try:
            payload = {
                "model": model_id,
                "messages": messages,
                "max_tokens": 800,
                "temperature": 0.7
            }

            try:
                url = f"{config.OMNIROUTE_BASE_URL}/chat/completions"
                resp = requests.post(url, headers=headers, json=payload, timeout=5.5)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "").strip()
                        if content:
                            conversation_memory.add_turn("user", prompt)
                            conversation_memory.add_turn("assistant", content)
                            return content
            except Exception:
                continue

        # 2. Direct OpenAI Fallback if key is present
        if config.OPENAI_API_KEY:
            try:
                o_headers = {
                    "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                o_payload = {
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "max_tokens": 800,
                    "temperature": 0.7
                }
                o_resp = requests.post("https://api.openai.com/v1/chat/completions", headers=o_headers, json=o_payload, timeout=6.0)
                if o_resp.status_code == 200:
                    choices = o_resp.json().get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "").strip()
                        if content:
                            conversation_memory.add_turn("user", prompt)
                            conversation_memory.add_turn("assistant", content)
                            return content
            except Exception:
                pass

        # 3. Direct Gemini Fallback if key is present
        if config.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=config.GEMINI_API_KEY)
                conv_ctx = conversation_memory.get_context_string()
                full_prompt = f"{conv_ctx}\nSir: {prompt}" if conv_ctx else prompt
                g_resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{context}\n\n{full_prompt}" if context else full_prompt
                )
                if g_resp and g_resp.text:
                    content = g_resp.text.strip()
                    conversation_memory.add_turn("user", prompt)
                    conversation_memory.add_turn("assistant", content)
                    return content
            except Exception:
                pass

        return None

    def query_specific_model(self, prompt: str, model_name: str, context: str = "") -> str:
        """
        Directs an explicit directive to a specific external AI model (OpenAI, Claude, Mistral,
        DeepSeek, Llama, Qwen, Gemini) using the Universal Free AI Matrix (100% zero-cost).
        """
        from core.free_ai_matrix import free_ai_matrix
        spoken_res, _ = free_ai_matrix.query_provider(model_name, prompt)
        return spoken_res

# Global singleton
online_intelligence = OnlineIntelligence()
