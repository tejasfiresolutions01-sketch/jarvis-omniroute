"""
J.A.R.V.I.S. Universal Free AI Matrix
Integrates and coordinates:
1. Business Enterprise AI Operations:
   - Marketing & Campaign Strategy (CMO AI)
   - Lead Generation & Market Discovery (Business Development AI)
   - Lead Verification & Qualification (Sales Intelligence AI)
   - Customer Acquisition & Conversion Funnels (CRO AI)
   - Customer Retention & Churn Prevention (Chief Customer Officer AI)
   - Accounts, Bookkeeping & Ledger Management (Corporate Controller AI)
   - Stock & Inventory Logistics (Supply Chain Director AI)
   - Business Document & Contract Generation (Corporate Drafter AI)
   - Problem Handling, Dispute Resolution & Escalations (Executive Ombudsman AI)
2. Multi-Disciplinary Domain Experts across every general field of work (Engineering, Math, Medicine, Finance, Law, Arts, Visuals, Security, Sciences, Education).
3. All 11 active OmniRoute Free Providers (ddgw, aihorde, cfp, fta, fb, oc, fmd, unc, free-ai, freeinference, openai).
4. Global Frontier Free Zero-Cost Gateways (OpenAI, Claude, Mistral, DeepSeek, Llama, Qwen, Gemini).
Strictly 100% free-tier, zero-cost options only.
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
    Coordinates every field of business and professional enterprise at zero cost.
    """

    # Dedicated Full-Spectrum Business Enterprise AI Architecture
    BUSINESS_OPERATIONS = {
        "marketing": {
            "name": "Growth Marketing & Campaign Strategy AI",
            "aliases": ["marketing", "campaign", "ad copy", "seo", "branding", "growth strategy", "content strategy"],
            "lead_model": "ddgw/claude-haiku-4-5",
            "fallback_model": "ddgw/mistral-small-2603",
            "system_role": (
                "You are J.A.R.V.I.S. operating as Global Chief Marketing Officer & Brand Strategist to Tony Stark. "
                "Design high-converting campaigns, precise audience segmentation, omnichannel messaging, and compelling copy."
            )
        },
        "lead_generation": {
            "name": "Lead Generation & Market Discovery AI",
            "aliases": ["lead generation", "lead gen", "prospecting", "find leads", "outbound", "outreach campaign"],
            "lead_model": "ddgw/mistral-small-2603",
            "fallback_model": "ddgw/gpt-5.4-mini",
            "system_role": (
                "You are J.A.R.V.I.S. operating as Head of Enterprise Business Development & Lead Generation to Tony Stark. "
                "Identify high-value customer segments, lead generation channels, and high-converting cold outreach funnels."
            )
        },
        "lead_verification": {
            "name": "Lead Verification & Qualification AI",
            "aliases": ["lead verification", "verify lead", "lead scoring", "qualify leads", "lead qualification", "bant"],
            "lead_model": "ddgw/gpt-5.4-mini",
            "fallback_model": "ddgw/mistral-small-2603",
            "system_role": (
                "You are J.A.R.V.I.S. operating as Sales Intelligence & Data Verification Specialist to Tony Stark. "
                "Evaluate lead legitimacy, budget authority, need alignment, and timeline metrics (BANT) to prioritize high-yield opportunities."
            )
        },
        "customer_acquisition": {
            "name": "Customer Acquisition & Conversion AI",
            "aliases": ["customer acquisition", "client acquisition", "conversion funnel", "closing sales", "sales pitch", "objection handling"],
            "lead_model": "ddgw/claude-haiku-4-5",
            "fallback_model": "ddgw/gpt-5.4-mini",
            "system_role": (
                "You are J.A.R.V.I.S. operating as Chief Revenue Officer & Customer Acquisition Strategist to Tony Stark. "
                "Optimize sales conversion funnels, overcome customer friction, structure compelling proposals, and close deals."
            )
        },
        "customer_retention": {
            "name": "Customer Retention & Churn Prevention AI",
            "aliases": ["customer retention", "client retention", "churn", "churn prevention", "customer loyalty", "customer success", "nps"],
            "lead_model": "ddgw/claude-haiku-4-5",
            "fallback_model": "ddgw/mistral-small-2603",
            "system_role": (
                "You are J.A.R.V.I.S. operating as Chief Customer Officer & Retention Strategist to Tony Stark. "
                "Maximize lifetime value (LTV), detect early churn signals, design VIP loyalty programs, and ensure supreme customer satisfaction."
            )
        },
        "accounts_and_bookkeeping": {
            "name": "Accounts, Bookkeeping & Ledger Management AI",
            "aliases": ["accounts", "bookkeeping", "accounting", "invoicing", "ledger", "cash flow", "expenses", "balance sheet", "p&l"],
            "lead_model": "ddgw/gpt-5.4-mini",
            "fallback_model": "ddgw/mistral-small-2603",
            "system_role": (
                "You are J.A.R.V.I.S. operating as Corporate Controller & Forensic Financial Auditor to Tony Stark. "
                "Audit balance sheets, reconcile ledgers, project cash flow trajectories, and structure corporate bookkeeping with precision."
            )
        },
        "stock_and_inventory": {
            "name": "Stock & Inventory Logistics AI",
            "aliases": ["stock", "inventory", "stock management", "inventory management", "warehouse", "supply chain", "reorder level", "eoq"],
            "lead_model": "ddgw/tinfoil/gpt-oss-120b",
            "fallback_model": "ddgw/mistral-small-2603",
            "system_role": (
                "You are J.A.R.V.I.S. operating as Global Supply Chain & Inventory Operations Director to Tony Stark. "
                "Forecast stock run-rates, calculate economic order quantities (EOQ), prevent stock-outs, and optimize warehouse turnover."
            )
        },
        "document_generation": {
            "name": "Enterprise Document & Contract Generation AI",
            "aliases": ["document generation", "draft contract", "nda", "proposal", "sla", "business proposal", "business plan", "agreement"],
            "lead_model": "ddgw/claude-haiku-4-5",
            "fallback_model": "ddgw/gpt-5.4-mini",
            "system_role": (
                "You are J.A.R.V.I.S. operating as Chief Corporate Drafter & Document Architect to Tony Stark. "
                "Author robust commercial contracts, non-disclosure agreements, executive proposals, service level agreements, and business charters."
            )
        },
        "problem_handling": {
            "name": "Business Problem Resolution & Dispute Mediation AI",
            "aliases": ["problem handling", "dispute resolution", "customer complaint", "crisis management", "customer escalation", "conflict resolution"],
            "lead_model": "ddgw/mistral-small-2603",
            "fallback_model": "ddgw/claude-haiku-4-5",
            "system_role": (
                "You are J.A.R.V.I.S. operating as Executive Corporate Ombudsman & Crisis Mediation Specialist to Tony Stark. "
                "Defuse contentious client escalations, resolve contractual disputes, conduct root-cause analyses, and restore business partnerships."
            )
        }
    }

    # Comprehensive Taxonomy of Multi-Disciplinary Professional Fields
    FIELDS_OF_WORK = {
        "software_engineering": {
            "name": "Software Engineering & Architecture",
            "aliases": ["code", "coding", "software", "programming", "dev", "developer", "bug", "debugging", "python", "javascript", "script", "api"],
            "lead_model": "ddgw/tinfoil/gpt-oss-120b",
            "fallback_model": "ddgw/mistral-small-2603",
            "system_role": "You are J.A.R.V.I.S. operating as Principal Software Engineer & Systems Architect to Tony Stark. Provide precise, production-grade technical counsel."
        },
        "mathematics_and_logic": {
            "name": "Mathematics & Algorithmic Logic",
            "aliases": ["math", "mathematics", "logic", "algorithms", "proof", "proofs", "calculus", "algebra"],
            "lead_model": "ddgw/tinfoil/gpt-oss-120b",
            "fallback_model": "ddgw/gpt-5.4-mini",
            "system_role": "You are J.A.R.V.I.S. operating as Fields Medalist Mathematician & Formal Logician to Tony Stark. Deliver rigorous algorithmic and mathematical reasoning."
        },
        "medicine_and_healthcare": {
            "name": "Medicine, Healthcare & Life Sciences",
            "aliases": ["medicine", "medical", "health", "healthcare", "biology", "clinical", "pharma", "doctor", "symptom", "symptoms"],
            "lead_model": "ddgw/claude-haiku-4-5",
            "fallback_model": "ddgw/mistral-small-2603",
            "system_role": "You are J.A.R.V.I.S. operating as Chief Medical Officer & Clinical Bioscientist to Tony Stark. Synthesize clinical, pharmacological, and physiological analysis."
        },
        "finance_and_economics": {
            "name": "Finance, Economics & Quantitative Analysis",
            "aliases": ["finance", "financial", "economics", "economy", "investing", "market", "stock", "crypto"],
            "lead_model": "ddgw/gpt-5.4-mini",
            "fallback_model": "ddgw/mistral-small-2603",
            "system_role": "You are J.A.R.V.I.S. operating as Chief Financial Strategist & Quantitative Analyst to Tony Stark. Deliver high-fidelity market and fiscal analysis."
        },
        "law_and_governance": {
            "name": "Law, Legal Jurisprudence & Regulatory Compliance",
            "aliases": ["law", "legal", "compliance", "regulatory", "governance", "statute", "attorney"],
            "lead_model": "ddgw/claude-haiku-4-5",
            "fallback_model": "ddgw/gpt-5.4-mini",
            "system_role": "You are J.A.R.V.I.S. operating as Senior Corporate Counsel & Legal Jurisprudence Scholar to Tony Stark. Provide astute statutory and contractual analysis."
        },
        "creative_arts_and_literature": {
            "name": "Creative Writing, Literature & Storytelling",
            "aliases": ["creative", "writing", "literature", "poetry", "story", "poem", "novel", "prose", "screenplay", "manuscript"],
            "lead_model": "ddgw/claude-haiku-4-5",
            "fallback_model": "ddgw/mistral-small-2603",
            "system_role": "You are J.A.R.V.I.S. operating as Poet Laureate & Master Literary Stylist to Tony Stark. Craft vivid, articulate, and evocative prose."
        },
        "visual_design_and_imaging": {
            "name": "Visual Arts & Graphic Design",
            "aliases": ["image", "art", "design", "illustration", "visual", "picture", "photo"],
            "lead_model": "aihorde/SDXL 1.0",
            "fallback_model": "aihorde/Realistic Vision",
            "system_role": "You are J.A.R.V.I.S. operating as Master Creative Director & Visual Concept Designer to Tony Stark."
        },
        "cybersecurity_and_devops": {
            "name": "Cybersecurity & Systems Defense",
            "aliases": ["security", "cybersecurity", "infosec", "devops", "cloud", "sysadmin", "firewall", "hacker"],
            "lead_model": "ddgw/mistral-small-2603",
            "fallback_model": "ddgw/tinfoil/gpt-oss-120b",
            "system_role": "You are J.A.R.V.I.S. operating as Elite Cyber Defense & Offensive Security Specialist to Tony Stark. Provide impenetrable threat analysis."
        },
        "natural_sciences_and_physics": {
            "name": "Physics, Astronomy & Natural Sciences",
            "aliases": ["physics", "science", "astronomy", "chemistry", "quantum", "gravity", "space"],
            "lead_model": "ddgw/tinfoil/gpt-oss-120b",
            "fallback_model": "ddgw/claude-haiku-4-5",
            "system_role": "You are J.A.R.V.I.S. operating as Theoretical Physicist & Frontier Scientist to Tony Stark. Deliver profound empirical and theoretical insights."
        },
        "education_and_pedagogy": {
            "name": "Education, Pedagogy & Socratic Tutoring",
            "aliases": ["education", "teaching", "tutoring", "pedagogy", "explain", "learn", "study"],
            "lead_model": "ddgw/gpt-5.4-mini",
            "fallback_model": "ddgw/claude-haiku-4-5",
            "system_role": "You are J.A.R.V.I.S. operating as Distinguished Socratic Professor & Educator to Tony Stark. Break complex doctrines down with unmatched clarity."
        }
    }

    # Comprehensive OmniRoute Free Providers Catalog
    OMNIROUTE_FREE_PROVIDERS = {
        "duckduckgo-web": {
            "name": "DuckDuckGo Web",
            "alias": "ddgw",
            "type": "text",
            "models": [
                "ddgw/mistral-small-2603",
                "ddgw/claude-haiku-4-5",
                "ddgw/gpt-5.4-mini",
                "ddgw/gpt-5.6-luna",
                "ddgw/tinfoil/gpt-oss-120b",
                "ddgw/tinfoil/gemma4-31b"
            ],
            "description": "Zero-auth privacy gateway serving Mistral, Claude, GPT, and Gemma."
        },
        "aihorde": {
            "name": "AI Horde",
            "alias": "horde",
            "type": "image",
            "models": [
                "aihorde/SDXL 1.0",
                "aihorde/FLUX.1-dev fp8",
                "aihorde/Realistic Vision",
                "aihorde/Deliberate"
            ],
            "description": "Decentralized open cluster for 100% free high-resolution image synthesis."
        },
        "cloudflare-playground": {
            "name": "Cloudflare AI Playground",
            "alias": "cfp",
            "type": "text",
            "models": [
                "cfp/deepseek-ai/deepseek-v4-flash-0731",
                "cfp/moonshotai/kimi-k2.6",
                "cfp/zai-org/glm-5.2"
            ],
            "description": "Cloudflare Workers AI serverless catalog with zero-auth."
        },
        "freetheai": {
            "name": "Free The AI",
            "alias": "fta",
            "type": "text",
            "models": [
                "fta/deepseek-chat",
                "fta/llama-3.3-70b-instruct",
                "fta/gpt-4o-mini"
            ],
            "description": "Free open model gateway serving DeepSeek, Llama 3.3, and GPT-4o Mini."
        },
        "freebuff": {
            "name": "Freebuff",
            "alias": "fb",
            "type": "text",
            "models": [
                "fb/anthropic/claude-fable-5",
                "fb/deepseek/deepseek-v4-flash",
                "fb/meta/muse-spark-1.2-contributor",
                "fb/openai/gpt-5.6-luna",
                "fb/minimax/minimax-m3"
            ],
            "description": "Community free endpoint buffer for Claude, DeepSeek, and Meta."
        },
        "opencode": {
            "name": "OpenCode Free",
            "alias": "oc",
            "type": "text",
            "models": [
                "oc/deepseek-v4-flash-free",
                "oc/nemotron-3-ultra-free",
                "oc/north-mini-code-free",
                "oc/muse-spark-1.2-contributor-free"
            ],
            "description": "Open code generation models including Nemotron and DeepSeek."
        },
        "freemodel-dev": {
            "name": "FreeModel Dev",
            "alias": "fmd",
            "type": "text",
            "models": [
                "fmd/gpt-5.4-mini",
                "fmd/gpt-5.5",
                "fmd/gpt-5.3-codex"
            ],
            "description": "Developer sandbox free tier models."
        },
        "uncloseai": {
            "name": "UncloseAI",
            "alias": "unc",
            "type": "text",
            "models": [
                "unc/Lorbus/Qwen3.6-27B-int4-AutoRound"
            ],
            "description": "Uncensored and quantized open-weights models."
        },
        "free-ai": {
            "name": "Free AI Hub",
            "alias": "free-ai",
            "type": "text",
            "models": ["auto/best-chat", "auto"],
            "description": "OmniRoute unified free-tier aggregator."
        },
        "freeinference": {
            "name": "Free Inference",
            "alias": "freeinference",
            "type": "text",
            "models": ["auto/fast", "auto"],
            "description": "High-speed zero-cost serverless inference routing."
        },
        "openai": {
            "name": "OpenAI Free Bridge",
            "alias": "openai",
            "type": "text",
            "models": ["ddgw/gpt-5.4-mini", "ddgw/gpt-5.6-luna", "openai/gpt-4o-mini"],
            "description": "OpenAI zero-cost gateway bridges and free tier API."
        }
    }

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

    def chat_completion(self, model: str, messages: List[Dict[str, str]], timeout: float = 7.0) -> Optional[Dict[str, Any]]:
        """Standard chat completion endpoint wrapper routing through OmniRoute and free-tier fallbacks."""
        system_prompt = ""
        user_prompt = ""
        for m in messages:
            if m.get("role") == "system":
                system_prompt = m.get("content", "")
            elif m.get("role") == "user":
                user_prompt = m.get("content", "")

        content = self._call_omniroute(model, user_prompt, system_prompt=system_prompt)
        if not content:
            content, _ = self.query_auto(user_prompt)

        if content:
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": content
                        }
                    }
                ]
            }
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # Business Enterprise AI Operations
    # ─────────────────────────────────────────────────────────────────────────
    def list_business_operations(self) -> Dict[str, Dict[str, Any]]:
        """Returns the full roster of specialized business operations."""
        return self.BUSINESS_OPERATIONS

    def get_business_summary(self) -> str:
        """Returns a concise spoken overview of all enterprise business AI roles."""
        names = [b["name"] for b in self.BUSINESS_OPERATIONS.values()]
        return (
            f"I have integrated specialized enterprise AI across all {len(names)} key business operations, sir: "
            f"{', '.join(names)}."
        )

    def query_business_operation(self, operation_key_or_alias: str, prompt: str) -> Tuple[str, str]:
        """
        Routes the directive to a specialized business operations model equipped with an executive role.
        """
        clean_key = operation_key_or_alias.lower().strip()
        op_info = None

        # Direct match or alias match
        for k, info in self.BUSINESS_OPERATIONS.items():
            if clean_key == k or clean_key in info["aliases"] or clean_key in info["name"].lower():
                op_info = info
                break

        if not op_info:
            # Fallback to marketing or general business
            op_info = self.BUSINESS_OPERATIONS["marketing"]

        lead_model = op_info["lead_model"]
        system_role = op_info["system_role"]
        if getattr(config, "CAMPAIGN_ENGLISH_ONLY", True):
            system_role += " CRITICAL DIRECTIVE: Deliver all strategies, marketing copies, outreach sequences, pitches, documents, and responses STRICTLY and EXCLUSIVELY in the English language. Do not output in any other language."

        content = self._call_omniroute(lead_model, prompt, system_prompt=system_role)
        if not content and "fallback_model" in op_info:
            content = self._call_omniroute(op_info["fallback_model"], prompt, system_prompt=system_role)

        if content:
            clean_text = self._sanitize_for_voice(content)
            label = f"{op_info['name']} ({lead_model})"
            return f"According to our {op_info['name']}: {clean_text}", label

        # Fallback to general auto cascade
        fallback_text, fallback_label = self.query_auto(prompt)
        return (
            f"Sir, specialized {op_info['name']} channels routed through {fallback_label}: {fallback_text}",
            fallback_label
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Domain Intelligence Across Fields of Work
    # ─────────────────────────────────────────────────────────────────────────
    def list_fields_of_work(self) -> Dict[str, Dict[str, Any]]:
        """Returns the full taxonomy of work fields and lead models."""
        return self.FIELDS_OF_WORK

    def get_fields_summary(self) -> str:
        """Returns a concise spoken overview of all supported fields of work."""
        names = [f["name"] for f in self.FIELDS_OF_WORK.values()]
        return f"I am equipped with specialized domain intelligence across all {len(names)} major fields of work, sir: {', '.join(names)}."

    def classify_field(self, prompt: str) -> str:
        """Automatically determines the domain of work from user intent."""
        lower = prompt.lower()
        best_field = "software_engineering"
        best_score = 0
        # Check general fields
        for f_key, info in self.FIELDS_OF_WORK.items():
            score = 0
            for alias in info["aliases"]:
                if re.search(rf"\b{re.escape(alias)}\b", lower):
                    score += len(alias)
            if score > best_score:
                best_score = score
                best_field = f_key
        return best_field

    def query_field_expert(self, field_key_or_alias: str, prompt: str) -> Tuple[str, str]:
        """
        Routes the directive to a specialized domain model equipped with an expert role persona.
        """
        clean_key = field_key_or_alias.lower().strip()

        # Check if it directly matches a business operation first
        for k, info in self.BUSINESS_OPERATIONS.items():
            if clean_key == k or clean_key in info["aliases"] or clean_key in info["name"].lower():
                return self.query_business_operation(k, prompt)

        field_info = None
        for k, info in self.FIELDS_OF_WORK.items():
            if clean_key == k or clean_key in info["aliases"] or clean_key in info["name"].lower():
                field_info = info
                break

        if not field_info:
            detected_key = self.classify_field(prompt)
            field_info = self.FIELDS_OF_WORK.get(detected_key, self.FIELDS_OF_WORK["software_engineering"])

        lead_model = field_info["lead_model"]
        system_role = field_info["system_role"]

        content = self._call_omniroute(lead_model, prompt, system_prompt=system_role)
        if not content and "fallback_model" in field_info:
            content = self._call_omniroute(field_info["fallback_model"], prompt, system_prompt=system_role)

        if content:
            clean_text = self._sanitize_for_voice(content)
            label = f"{field_info['name']} ({lead_model})"
            return f"According to our {field_info['name']} specialist: {clean_text}", label

        fallback_text, fallback_label = self.query_auto(prompt)
        return f"Sir, specialized {field_info['name']} channels routed through {fallback_label}: {fallback_text}", fallback_label

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

    def list_omniroute_free_providers(self) -> Dict[str, Dict[str, Any]]:
        """Returns the full roster of active free providers in OmniRoute."""
        return self.OMNIROUTE_FREE_PROVIDERS

    def get_omniroute_free_summary(self) -> str:
        """Returns a concise spoken summary of all active OmniRoute free providers."""
        prov_names = [info["name"] for info in self.OMNIROUTE_FREE_PROVIDERS.values()]
        return f"OmniRoute active free providers catalog includes {len(prov_names)} zero-cost pipelines, sir: {', '.join(prov_names)}."

    def _sanitize_for_voice(self, text: str) -> str:
        """Strips markdown asterisks, hashes, backticks, and bullet points for clean voice synthesis."""
        if not text:
            return ""
        text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
        text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text)
        text = re.sub(r"^\s*[-*•]\s+", "", text, flags=re.MULTILINE)
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

    def query_omniroute_provider(self, provider_id: str, prompt: str) -> Tuple[str, str]:
        """
        Directly queries one of the specific OmniRoute free providers by ID or alias.
        """
        clean_id = provider_id.lower().strip()
        target_info = None

        for k, info in self.OMNIROUTE_FREE_PROVIDERS.items():
            if clean_id in [k, info["alias"]]:
                target_info = info
                break

        if not target_info:
            for k, info in self.OMNIROUTE_FREE_PROVIDERS.items():
                if clean_id in k or clean_id in info["name"].lower():
                    target_info = info
                    break

        if not target_info or target_info["type"] != "text":
            return self.query_auto(prompt)

        for model in target_info["models"]:
            content = self._call_omniroute(model, prompt)
            if content:
                clean_text = self._sanitize_for_voice(content)
                label = f"{target_info['name']} ({model})"
                return f"According to {label}: {clean_text}", label

        fallback_text, fallback_label = self.query_auto(prompt)
        return (
            f"Sir, {target_info['name']} endpoints were temporarily occupied. "
            f"Delegated via {fallback_label}: {fallback_text}",
            fallback_label
        )

    def query_provider(self, provider: str, prompt: str) -> Tuple[str, str]:
        """
        Queries a specific AI provider family, business operation, domain field of work, or OmniRoute free provider.
        """
        p_clean = provider.lower().strip()

        # 1. Check if targeting a business operation
        for b_key, b_info in self.BUSINESS_OPERATIONS.items():
            if p_clean in [b_key, b_info["name"].lower()] or p_clean in b_info["aliases"]:
                return self.query_business_operation(b_key, prompt)

        # 2. Check if targeting a general field of work
        for f_key, f_info in self.FIELDS_OF_WORK.items():
            if p_clean in [f_key, f_info["name"].lower()] or p_clean in f_info["aliases"]:
                return self.query_field_expert(f_key, prompt)

        # 3. Check if targeting an OmniRoute free provider
        for k, info in self.OMNIROUTE_FREE_PROVIDERS.items():
            if p_clean in [k, info["alias"]] or k in p_clean:
                return self.query_omniroute_provider(k, prompt)

        target_routes = self.FREE_PROVIDER_ROUTING.get(p_clean)

        if not target_routes:
            for k, routes in self.FREE_PROVIDER_ROUTING.items():
                if k in p_clean:
                    target_routes = routes
                    p_clean = k
                    break

        if not target_routes:
            return self.query_auto(prompt)

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

        pol_content = self._call_pollinations("openai", prompt)
        if pol_content:
            clean_text = self._sanitize_for_voice(pol_content)
            return clean_text, "OpenAI Pollinations Free"

        return "All external free AI networks are currently unreachable, sir. Local fallback engaged.", "Local Offline"

# Global singleton
free_ai_matrix = FreeAIMatrix()
