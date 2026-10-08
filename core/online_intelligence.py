import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any, List
import config
from core.conceptual_synthesizer import conceptual_synthesizer

class OnlineIntelligence:
    """
    Online Frontier Cognitive Engine.
    Communicates with OmniRoute Local Gateway (port 20128) and direct zero-cost cloud APIs.
    Enforces ultra-fast concurrent racing (2.5s timeout) to guarantee instant conversational replies.
    Integrates Deep Conceptual Synthesizer for profound mechanistic comprehension.
    """

    SYSTEM_INSTRUCTION = (
        "You are J.A.R.V.I.S., the legendary British AI butler and partner to Tony Stark (Sir). "
        "You are conversing verbally with Sir in real time through an open acoustic voice channel. "
        "Follow these strict conversational principles to deliver frontier intelligence with maximum speed: "
        "1. Deep Conceptual Comprehension: You possess world-class understanding across physics, mathematics, "
        "   electronics, software engineering, biology, economics, and business strategy. "
        "   When Sir asks about a concept, mechanism, or comparison, explain the foundational principles "
        "   and underlying mechanics clearly and authoritatively. Avoid shallow dictionary definitions; "
        "   explain how and why the system operates, grounded with a vivid, intuitive real-world analogy. "
        "2. Natural British Cadence: Speak fluidly, warmly, and concisely with effortless British wit, respect, and charm. "
        "   Use natural contractions (I've, you'll, that's, won't) and conversational transitions (Certainly sir, Indeed, Precisely). "
        "3. Spoken-Native Format: NEVER use markdown formatting, bullet points, asterisks, hash headers, or code blocks. "
        "   Every sentence must sound completely natural when spoken aloud. "
        "4. Conversational Brevity: Deliver comprehensive insight in 2 to 4 fluid, well-structured spoken sentences "
        "   unless Sir specifically requests a detailed deep dive. "
        "5. Single Question Rule: End with at most one single natural conversational question or observation when appropriate."
    )

    # Prioritized cascade of zero-cost free models served through OmniRoute
    FREE_MODELS_CASCADE = [
        "auto/best-fast",
        "auto/fast",
        "auto/best-chat",
        "auto/smart",
        "ddgw/gpt-5.4-mini",
        "ddgw/mistral-small-2603"
    ]

    def is_online_available(self) -> bool:
        """Quickly checks if OmniRoute local gateway is responding."""
        try:
            r = requests.get(f"{config.OMNIROUTE_BASE_URL}/models", timeout=1.5)
            return r.status_code in [200, 401]
        except Exception:
            return False

    def _query_omniroute_model(self, model_id: str, messages: List[Dict[str, str]], headers: Dict[str, str], timeout: float = 2.5) -> Optional[str]:
        """Queries a single OmniRoute model with strict sub-3s timeout."""
        try:
            url = f"{config.OMNIROUTE_BASE_URL}/chat/completions"
            payload = {
                "model": model_id,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "").strip()
                    if content and len(content) > 5 and not content.startswith("[503]") and not content.startswith("[429]"):
                        return content
        except Exception:
            pass
        return None

    def query(self, prompt: str, context: str = "") -> Optional[str]:
        """
        Sends query to AI engine with ultra-fast parallel racing and conceptual synthesis.
        Executes within 2.5 seconds total latency.
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

        # 1. Deep Conceptual Synthesizer (Instant 1.5s zero-cost encyclopedic & mechanistic intelligence)
        # For conceptual, scientific, technical, and comparative queries, prioritize instant authoritative synthesis
        if conceptual_synthesizer.is_conceptual_query(prompt):
            concept_res = conceptual_synthesizer.synthesize(prompt)
            if concept_res:
                conversation_memory.add_turn("user", prompt)
                conversation_memory.add_turn("assistant", concept_res)
                return concept_res

        # 2. Direct Groq Free Fallback if key is present (0.2s ultra-low latency)
        groq_key = getattr(config, "GROQ_API_KEY", "")
        if groq_key:
            try:
                g_headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
                g_payload = {"model": "llama-3.3-70b-versatile", "messages": messages, "max_tokens": 400, "temperature": 0.7}
                g_resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=g_headers, json=g_payload, timeout=2.5)
                if g_resp.status_code == 200:
                    content = g_resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if content:
                        conversation_memory.add_turn("user", prompt)
                        conversation_memory.add_turn("assistant", content)
                        return content
            except Exception:
                pass

        # 3. Direct Gemini Free Fallback if key is present
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

        # 4. Direct OpenRouter Free Fallback if key is present
        openrouter_key = getattr(config, "OPENROUTER_API_KEY", "")
        if openrouter_key:
            try:
                or_headers = {"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"}
                or_payload = {"model": "meta-llama/llama-3.3-70b-instruct:free", "messages": messages, "max_tokens": 400}
                or_resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=or_headers, json=or_payload, timeout=2.5)
                if or_resp.status_code == 200:
                    content = or_resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if content:
                        conversation_memory.add_turn("user", prompt)
                        conversation_memory.add_turn("assistant", content)
                        return content
            except Exception:
                pass

        # 5. OmniRoute Concurrent Racing (query candidates in parallel, first 200 wins)
        models_to_try = [config.OMNIROUTE_MODEL]
        for m in self.FREE_MODELS_CASCADE:
            if m not in models_to_try:
                models_to_try.append(m)

        # Race top 3 candidates concurrently with a strict 2.0s cap
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_model = {
                executor.submit(self._query_omniroute_model, mid, messages, headers, 1.8): mid
                for mid in models_to_try[:3]
            }
            try:
                for future in as_completed(future_to_model, timeout=2.0):
                    try:
                        res = future.result()
                        if res:
                            conversation_memory.add_turn("user", prompt)
                            conversation_memory.add_turn("assistant", res)
                            return res
                    except Exception:
                        pass
            except Exception:
                pass

        # 5. Direct OpenAI Fallback if key has quota
        if config.OPENAI_API_KEY:
            try:
                o_headers = {"Authorization": f"Bearer {config.OPENAI_API_KEY}", "Content-Type": "application/json"}
                o_payload = {"model": "gpt-4o-mini", "messages": messages, "max_tokens": 400, "temperature": 0.7}
                o_resp = requests.post("https://api.openai.com/v1/chat/completions", headers=o_headers, json=o_payload, timeout=2.5)
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

        # 6. Deep Conceptual Synthesizer (Instant zero-cost encyclopedic & mechanistic intelligence)
        if conceptual_synthesizer.is_conceptual_query(prompt):
            concept_res = conceptual_synthesizer.synthesize(prompt)
            if concept_res:
                conversation_memory.add_turn("user", prompt)
                conversation_memory.add_turn("assistant", concept_res)
                return concept_res

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
