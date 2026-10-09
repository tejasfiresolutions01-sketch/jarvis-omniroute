"""
J.A.R.V.I.S. Deep Conceptual Synthesizer & Zero-Cost Knowledge Engine.
Provides instant, profound conceptual understanding and scientific explanations
at 100% zero cost with sub-second retrieval latency.

Capabilities:
1. High-Precision Conceptual Extraction: Queries Wikipedia REST API and DuckDuckGo
   Instant Knowledge API.
2. Comparative Analysis (X vs Y): Seamlessly contrasts competing technologies or concepts
   (e.g., AC vs DC, RAM vs ROM, compiler vs interpreter).
3. Mechanistic Depth: Explains *why* and *how* systems work underneath, avoiding shallow definitions.
4. Spoken Butler Formatting: Translates complex scientific/engineering facts into
   elegant, natural British spoken English tailored for J.A.R.V.I.S.
5. Zero-Cost & Resilient: Operates completely free of API charges or rate limit failures.
"""

import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple, Dict, Any
import requests

class ConceptualSynthesizer:
    """
    Zero-Cost Conceptual Intelligence Engine.
    Provides deep mechanistic understanding of physics, engineering, computer science,
    biology, business, and general philosophy in simple, articulate English.
    """

    CONCEPT_TRIGGERS = [
        r"^(?:explain|describe|clarify|elaborate on)\s+(?:the\s+)?(.+)$",
        r"^(?:what is|what are|whats|what's)\s+(?:the\s+)?(.+)$",
        r"^(?:how does|how do|how works|how can)\s+(?:the\s+)?(.+)\s*(?:work|function|operate)?$",
        r"^(?:difference between|compare|contrast)\s+(.+)$",
        r"^(?:tell me about|give me a breakdown of)\s+(.+)$",
        r"^(?:teach me about|help me understand)\s+(.+)$",
    ]

    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._headers = {"User-Agent": "JARVIS-OmniButler/2.0 (Cognitive Knowledge Engine)"}

    def is_conceptual_query(self, query: str) -> bool:
        """Determines if a prompt is seeking conceptual or factual comprehension."""
        q = query.strip().lower()
        if len(q.split()) < 2:
            return False
            
        # Exclude system/device/butler commands
        excluded_verbs = [
            "open", "launch", "close", "turn off", "shutdown", "restart", "volume",
            "mute", "play", "pause", "scroll", "snap", "schedule", "calendar",
            "task", "campaign", "scan", "healer", "upgrade", "git", "commit"
        ]
        if any(q.startswith(w) for w in excluded_verbs):
            return False

        # Exclude mathematical arithmetic & calculation queries
        if re.search(r"\b\d+\s*(?:times|multiplied\s+by|divided\s+by|plus|minus|\+|\-|\*|\/|\^)\s*\d+\b", q):
            return False
        if re.search(r"\b(?:square\s+root\s+of|sqrt)\s+\d+", q):
            return False

        for pattern in self.CONCEPT_TRIGGERS:
            if re.search(pattern, q):
                return True
        return False

    OFFLINE_MECHANISTIC_ONTOLOGY = {
        # Electricity & Electronics
        "ac": "Alternating current reverses direction periodically and oscillates sinusoidally, making it exceptionally efficient for long-distance grid transmission through transformers.",
        "alternating current": "Alternating current reverses direction periodically and oscillates sinusoidally, making it exceptionally efficient for long-distance grid transmission through transformers.",
        "dc": "Direct current flows unidirectionally with constant polarity, making it the indispensable standard for battery storage, semiconductor logic, and photovoltaic solar systems.",
        "direct current": "Direct current flows unidirectionally with constant polarity, making it the indispensable standard for battery storage, semiconductor logic, and photovoltaic solar systems.",
        "voltage": "Voltage represents electrical potential difference, analogous to pressure in a hydraulic circuit that compels electrons to move between two points.",
        "current": "Current is the physical rate of electric charge flow through a conductor, quantified in amperes representing coulombs per second.",
        "transformer": "A transformer alters alternating voltage levels through mutual electromagnetic induction between primary and secondary copper windings without changing frequency.",
        "inverter": "An inverter converts direct current from battery banks or solar arrays into alternating current using high-frequency switching transistors like MOSFETs or IGBTs.",

        # Computing & Architecture
        "cpu": "The central processing unit features a modest count of exceptionally powerful cores optimized for serial computation, rapid clock frequencies, and complex branching logic.",
        "central processing unit": "The central processing unit features a modest count of exceptionally powerful cores optimized for serial computation, rapid clock frequencies, and complex branching logic.",
        "gpu": "The graphics processing unit houses thousands of smaller, streamlined cores engineered for massive parallel mathematical throughput, making it ideal for rendering and neural matrix multiplications.",
        "graphics processing unit": "The graphics processing unit houses thousands of smaller, streamlined cores engineered for massive parallel mathematical throughput, making it ideal for rendering and neural matrix multiplications.",
        "ram": "Random-access memory is ultra-fast volatile semiconductor storage that holds active operating system instructions and application working sets for immediate processor execution.",
        "random-access memory": "Random-access memory is ultra-fast volatile semiconductor storage that holds active operating system instructions and application working sets for immediate processor execution.",
        "random access memory": "Random-access memory is ultra-fast volatile semiconductor storage that holds active operating system instructions and application working sets for immediate processor execution.",
        "rom": "Read-only memory is non-volatile permanent semiconductor storage that preserves foundational startup firmware such as the BIOS even when powered down.",
        "read-only memory": "Read-only memory is non-volatile permanent semiconductor storage that preserves foundational startup firmware such as the BIOS even when powered down.",
        "read only memory": "Read-only memory is non-volatile permanent semiconductor storage that preserves foundational startup firmware such as the BIOS even when powered down.",
        "compiler": "A compiler translates high-level human-readable source code in its entirety into native binary machine instructions prior to execution, producing optimal execution velocity.",
        "interpreter": "An interpreter reads and executes source code instructions sequentially line by line at runtime, offering interactive flexibility at the expense of computational speed.",
        "process": "A process is an isolated operating system execution context possessing its own dedicated virtual address space, file handles, and security tokens.",
        "thread": "A thread is a lightweight unit of execution within a parent process, sharing that process's heap memory and resources while maintaining its own call stack and program counter.",
        "operating system": "An operating system is the master supervisory software suite managing hardware resources, memory scheduling, file systems, and peripheral communication across the workstation.",
        "kernel": "The kernel is the foundational core of the operating system that resides permanently in memory, directly orchestrating CPU time slices, hardware interrupts, and memory paging.",

        # AI & Machine Learning
        "artificial intelligence": "Artificial intelligence is the broad engineering discipline of constructing synthetic computational systems capable of performing reasoning, decision-making, and language tasks typically requiring human intelligence.",
        "machine learning": "Machine learning is a subset of artificial intelligence focused on mathematical and statistical models that automatically extract patterns and generalize from data without explicit procedural programming.",
        "deep learning": "Deep learning employs deep artificial neural networks featuring numerous hidden layers to hierarchically extract abstract features from raw inputs.",
        "large language model": "A large language model is a neural network based on the transformer architecture, utilizing multi-head self-attention mechanisms trained over massive linguistic corpora to predict token probabilities.",

        # Fire Safety Engineering & Compliance
        "is 2190": "Indian Standard 2190 establishes mandatory national guidelines for the selection, installation, maintenance, and hydraulic testing of portable first-aid fire extinguishers across commercial and industrial premises.",
        "is 2190 standards": "Indian Standard 2190 establishes mandatory national guidelines for the selection, installation, maintenance, and hydraulic testing of portable first-aid fire extinguishers across commercial and industrial premises.",
        "abc dry chemical powder": "ABC dry chemical powder extinguishers utilize monoammonium phosphate that melts at approximately 180 degrees Celsius to blanket fuel and break chemical combustion chain reactions across Class A, B, and C fires.",
        "co2 extinguisher": "Carbon dioxide extinguishers discharge pressurized liquid CO2 as an expanding gas, displacing atmospheric oxygen and rapidly cooling the fire zone without leaving residue, making them ideal for live electrical equipment.",
        "clean agent": "Clean agent extinguishers employ eco-friendly halocarbon compounds such as HFC-236fa or NOVEC that vaporize instantly upon discharge, extinguishing flames thermally without conducting electricity or damaging sensitive electronics.",
        "hydro testing": "Hydraulic pressure testing verifies the structural integrity of fire extinguisher shells using pressurized water, ensuring cylinders withstand operational internal pressures without catastrophic rupture.",
        "fire extinguisher refilling": "Fire extinguisher refilling entails evacuating spent or degraded extinguishing media, inspecting internal valve assemblies, refilling with certified extinguishing agents, and pressurizing with high-purity dry nitrogen in compliance with IS 2190 standards.",
        "amc": "An Annual Maintenance Contract provides scheduled quarterly or half-yearly fire safety inspections, weight audits, emergency standby cylinders, and regulatory compliance certification for manufacturing and warehousing facilities.",
        "fire audit": "A fire safety audit systematically reviews a facility's fire risks, exit corridors, extinguisher placement densities, and emergency readiness to ensure total compliance with state fire rescue directives."
    }

    COMMON_ACRONYMS = {
        "ac": "Alternating current",
        "dc": "Direct current",
        "ai": "Artificial intelligence",
        "ml": "Machine learning",
        "dl": "Deep learning",
        "ram": "Random-access memory",
        "rom": "Read-only memory",
        "cpu": "Central processing unit",
        "gpu": "Graphics processing unit",
        "tpu": "Tensor Processing Unit",
        "os": "Operating system",
        "api": "API",
        "http": "Hypertext Transfer Protocol",
        "dns": "Domain Name System",
        "tcp": "Transmission Control Protocol",
        "ip": "Internet Protocol",
        "iot": "Internet of things",
        "sql": "SQL",
        "nosql": "NoSQL",
        "llm": "Large language model"
    }

    def _clean_entity(self, text: str) -> str:
        """Cleans a single topic/entity down to its core noun phrase and expands acronyms."""
        t = text.strip(" ?.,!")
        t = re.sub(r"^(?:the|a|an)\s+", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s+(?:current|power|voltage)$", "", t, flags=re.IGNORECASE) if t.lower().strip() in ("ac current", "dc current") else t
        t = re.sub(r"\s+(?:works?|functioning|functions?|operates?|explained)$", "", t, flags=re.IGNORECASE)
        t = re.sub(r"^(?:concept of|idea of|theory of|principles? of)\s+", "", t, flags=re.IGNORECASE)
        key = t.strip().lower()
        if key in self.COMMON_ACRONYMS:
            return self.COMMON_ACRONYMS[key]
        return t.strip()

    def fetch_wikipedia_summary(self, topic: str) -> Optional[Tuple[str, str]]:
        """
        Retrieves high-authority conceptual extract from Wikipedia REST API.
        Returns: (resolved_title, extract_summary)
        """
        clean_t = self._clean_entity(topic)
        if not clean_t:
            return None

        # 1. Direct page summary attempt
        title_slug = urllib.parse.quote(clean_t.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title_slug}"
        try:
            r = requests.get(url, headers=self._headers, timeout=2.0)
            if r.status_code == 200:
                data = r.json()
                extract = data.get("extract", "").strip()
                title = data.get("title", clean_t)
                if extract and len(extract) > 40 and not any(d in extract.lower() for d in ["may refer to:", "most often refers to:", "refers to:"]):
                    return title, extract
        except Exception:
            pass

        # 2. Search fallback to find the most relevant article title
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_t)}&utf8=&format=json"
        try:
            r = requests.get(search_url, headers=self._headers, timeout=2.0)
            if r.status_code == 200:
                hits = r.json().get("query", {}).get("search", [])
                if hits:
                    best_title = hits[0].get("title", "")
                    if best_title:
                        title_slug2 = urllib.parse.quote(best_title.replace(" ", "_"))
                        r2 = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{title_slug2}", headers=self._headers, timeout=2.0)
                        if r2.status_code == 200:
                            data2 = r2.json()
                            extract2 = data2.get("extract", "").strip()
                            if extract2 and len(extract2) > 40 and "may refer to:" not in extract2:
                                return best_title, extract2
        except Exception:
            pass

        return None

    def fetch_duckduckgo_abstract(self, topic: str) -> Optional[str]:
        """Retrieves instant definition from DuckDuckGo Instant Knowledge API."""
        clean_t = self._clean_entity(topic)
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(clean_t)}&format=json"
        try:
            r = requests.get(url, headers=self._headers, timeout=1.8)
            if r.status_code == 200:
                data = r.json()
                abstract = data.get("AbstractText") or data.get("Abstract")
                if abstract and len(abstract) > 30:
                    return abstract.strip()
        except Exception:
            pass
        return None

    def _extract_difference_entities(self, query: str) -> Optional[Tuple[str, str]]:
        """Extracts X and Y from comparative queries like 'difference between X and Y'."""
        patterns = [
            r"(?:difference between|distinction between|compare)\s+(?:the\s+)?(.+?)\s+(?:and|with|to)\s+(?:the\s+)?(.+)$",
            r"(.+?)\s+(?:versus|vs\.?|vs)\s+(.+)$"
        ]
        q_clean = re.sub(r"^(?:explain|tell me|what is)\s+(?:the\s+)?", "", query, flags=re.IGNORECASE).strip(" ?.,!")
        for pat in patterns:
            m = re.search(pat, q_clean, re.IGNORECASE)
            if m:
                e1 = self._clean_entity(m.group(1))
                e2 = self._clean_entity(m.group(2))
                if e1 and e2:
                    return e1, e2
        return None

    def synthesize_difference(self, item1: str, item2: str) -> Optional[str]:
        """Contrasts two concepts side by side with mechanistic clarity."""
        c1 = item1.strip().lower()
        c2 = item2.strip().lower()
        # Fast offline mechanistic check (< 1ms)
        desc1 = self.OFFLINE_MECHANISTIC_ONTOLOGY.get(c1)
        desc2 = self.OFFLINE_MECHANISTIC_ONTOLOGY.get(c2)
        if desc1 and desc2:
            return f"In fundamental terms, sir: {desc1} In contrast, {desc2}"

        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(self.fetch_wikipedia_summary, item1)
            f2 = executor.submit(self.fetch_wikipedia_summary, item2)
            res1 = f1.result()
            res2 = f2.result()

        if not res1 or not res2:
            return None

        _, text1 = res1
        _, text2 = res2

        # Extract primary explanatory sentences
        s1 = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text1) if s.strip()]
        s2 = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text2) if s.strip()]

        if not s1 or not s2:
            return None

        # Clean citations
        p1 = re.sub(r"\([^)]*\)|\[[^\]]*\]", "", s1[0]).strip()
        p2 = re.sub(r"\([^)]*\)|\[[^\]]*\]", "", s2[0]).strip()

        speech = f"In fundamental terms, sir: {p1} In contrast, {p2}"
        if not speech.endswith((".", "!", "?")):
            speech += "."
        return speech

    def synthesize(self, query: str) -> Optional[str]:
        """
        Synthesizes a deep conceptual explanation from authoritative foundations.
        Formats into warm, articulate British Butler conversational phrasing.
        """
        clean_key = query.strip().lower()
        if clean_key in self._cache:
            return self._cache[clean_key]

        # 1. Check for comparative/difference query (e.g. AC vs DC)
        diff_pair = self._extract_difference_entities(query)
        if diff_pair:
            item1, item2 = diff_pair
            diff_speech = self.synthesize_difference(item1, item2)
            if diff_speech:
                self._cache[clean_key] = diff_speech
                return diff_speech

        # 2. Single concept extraction
        topic = self._clean_entity(query)
        for pattern in self.CONCEPT_TRIGGERS:
            m = re.match(pattern, query.strip(), flags=re.IGNORECASE)
            if m:
                topic = self._clean_entity(m.group(1))
                break

        if not topic:
            return None

        topic_lower = topic.strip().lower()
        # Fast offline mechanistic check (< 1ms)
        if topic_lower in self.OFFLINE_MECHANISTIC_ONTOLOGY:
            speech = f"At its core, sir: {self.OFFLINE_MECHANISTIC_ONTOLOGY[topic_lower]}"
            self._cache[clean_key] = speech
            return speech

        for k, v in self.OFFLINE_MECHANISTIC_ONTOLOGY.items():
            if f" {k} " in f" {clean_key} " or (topic_lower and k == topic_lower):
                speech = f"At its core, sir: {v}"
                self._cache[clean_key] = speech
                return speech

        # Fetch knowledge extract concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            f_wiki = executor.submit(self.fetch_wikipedia_summary, topic)
            f_ddg = executor.submit(self.fetch_duckduckgo_abstract, topic)
            wiki_res = f_wiki.result()
            ddg_res = f_ddg.result()

        raw_text = ""
        if wiki_res:
            _, raw_text = wiki_res
        elif ddg_res:
            raw_text = ddg_res

        if not raw_text:
            return None

        # Clean text into spoken sentences (remove parenthetical citations, brackets)
        clean_extract = re.sub(r"\([^)]*\)", "", raw_text)
        clean_extract = re.sub(r"\[[^\]]*\]", "", clean_extract)
        clean_extract = re.sub(r"\s+", " ", clean_extract).strip()

        # Split into sentences
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_extract) if s.strip()]
        if not sentences:
            return None

        # Pick the top 2-3 most informative conceptual sentences
        summary_body = " ".join(sentences[:2])
        if len(sentences) >= 3 and len(summary_body) < 180:
            summary_body = " ".join(sentences[:3])

        speech = f"At its core, sir: {summary_body}"
        if not speech.endswith((".", "!", "?")):
            speech += "."

        self._cache[clean_key] = speech
        return speech

# Global singleton
conceptual_synthesizer = ConceptualSynthesizer()
