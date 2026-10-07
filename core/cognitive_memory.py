"""
J.A.R.V.I.S. Cognitive Memory Architecture (Multi-Store Cognitive Memory Core).
Provides human-like cognitive awareness, episodic narrative traces, semantic facts
(user profile and preferences), active working-state memory (current focus and pending goals),
and automatic subconscious fact-extraction from natural conversation.
"""

import re
import json
import time
import sqlite3
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager
import numpy as np

import config
from core.vector_memory import FastEmbeddingEngine

class CognitiveMemory:
    """
    Multi-Store Human Cognitive Memory Matrix.
    Stores:
      1. Working Memory: Active mental model, active focus, current goals, and scratchpad.
      2. Semantic Facts: User profile, habits, preferences, and entity knowledge graph.
      3. Episodic Memory: Narrative interaction history with cognitive salience and temporal decay.
      4. Auto-Extraction: Learns preferences, facts, and goals automatically from natural conversation.
    """

    def __init__(self, db_path: Path = config.MEMORY_DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.embedding_engine = FastEmbeddingEngine(seed=42)
        
        # Working Memory (In-Memory Fast Scratchpad + SQLite mirror)
        self.working_memory: Dict[str, Any] = {
            "current_focus": "General Assistance",
            "active_tasks": [],
            "last_interaction": time.time(),
            "user_mood": "Neutral"
        }
        
        self._init_db()
        self._load_working_state()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._lock:
            with self._get_connection() as conn:
                # 1. Semantic Facts (Declarative Knowledge & User Profile)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cognitive_facts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        subject TEXT NOT NULL,
                        predicate TEXT NOT NULL,
                        object_value TEXT NOT NULL,
                        category TEXT DEFAULT 'general',
                        confidence REAL DEFAULT 1.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cf_category ON cognitive_facts(category)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cf_subject ON cognitive_facts(subject)")

                # 2. Episodic Memory (Narrative Episodes with Importance & Vector)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cognitive_episodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        summary TEXT NOT NULL,
                        episode_type TEXT DEFAULT 'dialogue',
                        importance INTEGER DEFAULT 5,
                        details TEXT,
                        timestamp REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_ce_timestamp ON cognitive_episodes(timestamp)")

                # 3. Working Memory State
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cognitive_working_state (
                        state_key TEXT PRIMARY KEY,
                        state_value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 4. Active Goals & Intentions
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cognitive_goals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        goal TEXT NOT NULL,
                        status TEXT DEFAULT 'ACTIVE',
                        importance INTEGER DEFAULT 5,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP
                    )
                """)
                conn.commit()

    def _load_working_state(self):
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT state_key, state_value FROM cognitive_working_state")
                    rows = cur.fetchall()
                    for r in rows:
                        k = r["state_key"]
                        try:
                            self.working_memory[k] = json.loads(r["state_value"])
                        except Exception:
                            self.working_memory[k] = r["state_value"]
            except Exception:
                pass

    def _save_working_state_key(self, key: str, value: Any):
        with self._lock:
            self.working_memory[key] = value
            try:
                with self._get_connection() as conn:
                    conn.execute("""
                        INSERT INTO cognitive_working_state (state_key, state_value, updated_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(state_key) DO UPDATE SET
                            state_value = excluded.state_value,
                            updated_at = CURRENT_TIMESTAMP
                    """, (key, json.dumps(value) if not isinstance(value, str) else value))
                    conn.commit()
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Working Memory (Active Goals, Cognitive Focus & Scratchpad)
    # ─────────────────────────────────────────────────────────────────────────

    def set_focus(self, focus_topic: str) -> str:
        """Sets current active cognitive focus or project."""
        clean = focus_topic.strip()
        self._save_working_state_key("current_focus", clean)
        return f"Cognitive focus aligned to '{clean}', sir."

    def get_focus(self) -> str:
        return self.working_memory.get("current_focus", "General Assistance")

    def add_goal(self, goal_desc: str, importance: int = 5) -> int:
        """Commits an active objective or task to working memory."""
        clean = goal_desc.strip()
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO cognitive_goals (goal, status, importance) VALUES (?, 'ACTIVE', ?)",
                    (clean, max(1, min(10, importance)))
                )
                conn.commit()
                goal_id = cur.lastrowid
        return goal_id

    def complete_goal(self, identifier: str) -> bool:
        """Marks an active goal as completed by ID or keyword."""
        clean = identifier.strip().lower()
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                if clean.isdigit():
                    cur.execute(
                        "UPDATE cognitive_goals SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'ACTIVE'",
                        (int(clean),)
                    )
                else:
                    cur.execute(
                        "UPDATE cognitive_goals SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP WHERE LOWER(goal) LIKE ? AND status = 'ACTIVE'",
                        (f"%{clean}%",)
                    )
                conn.commit()
                return cur.rowcount > 0

    def get_active_goals(self, limit: int = 5) -> List[Dict[str, Any]]:
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, goal, importance, created_at FROM cognitive_goals WHERE status = 'ACTIVE' ORDER BY importance DESC, id DESC LIMIT ?",
                    (limit,)
                )
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def get_working_memory_summary(self) -> str:
        focus = self.get_focus()
        goals = self.get_active_goals()
        lines = [f"• Active Focus: {focus}"]
        if goals:
            lines.append("• Active Objectives:")
            for g in goals:
                lines.append(f"  - [P{g['importance']} | #{g['id']}] {g['goal']}")
        else:
            lines.append("• Active Objectives: None currently pending.")
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Semantic Facts (Declarative Knowledge, User Profile & Preferences)
    # ─────────────────────────────────────────────────────────────────────────

    def store_fact(
        self,
        subject: str,
        predicate: str,
        object_value: str,
        category: str = "general",
        confidence: float = 1.0
    ) -> int:
        """
        Stores or updates a semantic fact tuple (Subject, Predicate, Object).
        If the same subject + predicate exists in category, it updates the value.
        """
        sub = subject.strip()
        pred = predicate.strip()
        obj = object_value.strip()
        cat = category.strip().lower()

        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                # Check for existing fact with matching subject & predicate
                cur.execute(
                    "SELECT id FROM cognitive_facts WHERE LOWER(subject) = ? AND LOWER(predicate) = ? AND category = ?",
                    (sub.lower(), pred.lower(), cat)
                )
                row = cur.fetchone()
                if row:
                    fact_id = row["id"]
                    cur.execute(
                        "UPDATE cognitive_facts SET object_value = ?, confidence = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (obj, confidence, fact_id)
                    )
                else:
                    cur.execute(
                        "INSERT INTO cognitive_facts (subject, predicate, object_value, category, confidence) VALUES (?, ?, ?, ?, ?)",
                        (sub, pred, obj, cat, confidence)
                    )
                    fact_id = cur.lastrowid
                conn.commit()
                return fact_id

    def recall_facts(
        self,
        query: str = "",
        category: Optional[str] = None,
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        """Recalls semantic facts matching category or lexical query tokens."""
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                if category:
                    cur.execute(
                        "SELECT id, subject, predicate, object_value, category, confidence, updated_at FROM cognitive_facts WHERE category = ? ORDER BY id DESC LIMIT ?",
                        (category.lower(), limit)
                    )
                elif query:
                    tokens = [f"%{t.lower()}%" for t in re.findall(r'[a-zA-Z0-9]+', query) if len(t) > 2]
                    if not tokens:
                        cur.execute("SELECT id, subject, predicate, object_value, category, confidence, updated_at FROM cognitive_facts ORDER BY id DESC LIMIT ?", (limit,))
                    else:
                        # Construct token search clause
                        clause = " OR ".join(["(LOWER(subject) LIKE ? OR LOWER(predicate) LIKE ? OR LOWER(object_value) LIKE ?)" for _ in tokens])
                        params = []
                        for tok in tokens:
                            params.extend([tok, tok, tok])
                        params.append(limit)
                        cur.execute(f"SELECT id, subject, predicate, object_value, category, confidence, updated_at FROM cognitive_facts WHERE {clause} ORDER BY id DESC LIMIT ?", params)
                else:
                    cur.execute("SELECT id, subject, predicate, object_value, category, confidence, updated_at FROM cognitive_facts ORDER BY id DESC LIMIT ?", (limit,))
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def delete_fact(self, keyword_or_id: str) -> int:
        """Deletes a fact by ID or matching keyword in subject/object."""
        clean = keyword_or_id.strip()
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                if clean.isdigit():
                    cur.execute("DELETE FROM cognitive_facts WHERE id = ?", (int(clean),))
                else:
                    cur.execute(
                        "DELETE FROM cognitive_facts WHERE LOWER(subject) LIKE ? OR LOWER(predicate) LIKE ? OR LOWER(object_value) LIKE ?",
                        (f"%{clean.lower()}%", f"%{clean.lower()}%", f"%{clean.lower()}%")
                    )
                conn.commit()
                return cur.rowcount

    def get_user_profile_summary(self) -> str:
        """Returns consolidated summary of known user facts and preferences."""
        facts = self.recall_facts(category="user_profile", limit=10)
        prefs = self.recall_facts(category="preference", limit=10)
        projects = self.recall_facts(category="project", limit=5)

        if not facts and not prefs and not projects:
            return "My cognitive profile contains no explicit personal parameters yet, sir. You may share your preferences freely."

        sections = []
        if facts:
            sections.append("• Identity & Profile:")
            for f in facts:
                sections.append(f"  - {f['subject']} {f['predicate']}: {f['object_value']}")
        if prefs:
            sections.append("• Preferences & Habits:")
            for p in prefs:
                sections.append(f"  - {p['predicate']}: {p['object_value']}")
        if projects:
            sections.append("• Known Projects:")
            for pr in projects:
                sections.append(f"  - {pr['predicate']}: {pr['object_value']}")

        return "\n".join(sections)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Episodic Memory (Narrative Traces with Salience & Recency Decay)
    # ─────────────────────────────────────────────────────────────────────────

    def record_episode(
        self,
        summary: str,
        episode_type: str = "dialogue",
        importance: int = 5,
        details: Optional[Dict[str, Any]] = None
    ) -> int:
        """Records an episodic narrative interaction trace with cognitive importance."""
        clean_sum = summary.strip()
        if not clean_sum:
            return -1

        meta_str = json.dumps(details or {})
        now_ts = time.time()
        imp_clamped = max(1, min(10, importance))

        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO cognitive_episodes (summary, episode_type, importance, details, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (clean_sum, episode_type, imp_clamped, meta_str, now_ts)
                )
                conn.commit()
                return cur.lastrowid

    def recall_episodes(self, query: str = "", top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Recalls episodes using cognitive spreading activation:
        combines lexical relevance, temporal recency decay, and importance score.
        """
        now = time.time()
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, summary, episode_type, importance, details, timestamp, created_at FROM cognitive_episodes ORDER BY id DESC LIMIT 50"
                )
                rows = cur.fetchall()

        if not rows:
            return []

        scored = []
        query_words = set(re.findall(r'[a-zA-Z0-9]+', query.lower())) if query else set()

        for r in rows:
            doc = dict(r)
            doc_words = set(re.findall(r'[a-zA-Z0-9]+', doc["summary"].lower()))
            # 1. Lexical overlap score
            if query_words and doc_words:
                overlap = len(query_words.intersection(doc_words)) / max(1, len(query_words))
            else:
                overlap = 0.5 if not query_words else 0.0

            # 2. Recency decay (half-life of 24 hours = 86400s)
            delta_hours = max(0.0, (now - doc["timestamp"]) / 3600.0)
            recency_score = float(np.exp(-0.02 * delta_hours))

            # 3. Importance score (0.1 to 1.0)
            importance_score = doc["importance"] / 10.0

            # Total associative salience
            total_salience = (0.5 * overlap) + (0.3 * recency_score) + (0.2 * importance_score)
            doc["salience"] = round(total_salience, 3)
            scored.append((total_salience, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    def get_recent_episodes_summary(self, limit: int = 4) -> str:
        episodes = self.recall_episodes(top_k=limit)
        if not episodes:
            return "No previous episodic memories recorded yet, sir."
        lines = ["Recent cognitive episodic traces:"]
        for ep in episodes:
            lines.append(f"  • [{ep['episode_type'].upper()}] {ep['summary']}")
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Automatic Subconscious Cognitive Extraction & Fact Learning
    # ─────────────────────────────────────────────────────────────────────────

    def auto_extract_and_learn(self, user_input: str) -> List[str]:
        """
        Subconsciously parses natural language utterances to extract user profile facts,
        preferences, active projects, and goals without requiring explicit 'remember' commands.
        Returns a list of learned facts/actions.
        """
        learned: List[str] = []
        text = user_input.strip()
        lower = text.lower()

        # 1. User Name / Identity
        # e.g., "my name is Tony Stark", "call me Venkat", "my name is Venkat and I prefer dark mode"
        name_match = re.search(r"\b(?:my name is|call me)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)(?:\s+(?:and|who|from)\b|[,\.\!]|\s*$)", text, re.IGNORECASE)
        if name_match:
            candidate = name_match.group(1).strip()
            # Exclude common predicates like "busy", "fine", "ready"
            if candidate.lower() not in ["busy", "fine", "ready", "here", "happy", "tired", "working", "going", "jarvis"]:
                self.store_fact("User", "Name", candidate, category="user_profile")
                learned.append(f"User Name: {candidate}")

        # 2. Preferences
        # e.g., "I prefer dark mode", "I love black coffee", "I like python over c++"
        pref_match = re.search(r"\bi\s+(?:prefer|like|love|enjoy|always use)\s+([^,.\n]+)", text, re.IGNORECASE)
        if pref_match:
            pref_val = pref_match.group(1).strip()
            if len(pref_val) > 2 and len(pref_val.split()) <= 8:
                self.store_fact("User", "Prefers", pref_val, category="preference")
                learned.append(f"Preference: {pref_val}")

        # Dislikes / Constraints
        dislike_match = re.search(r"\bi\s+(?:don't like|hate|dislike|never use)\s+([^,.\n]+)", text, re.IGNORECASE)
        if dislike_match:
            dislike_val = dislike_match.group(1).strip()
            if len(dislike_val) > 2 and len(dislike_val.split()) <= 8:
                self.store_fact("User", "Dislikes", dislike_val, category="preference")
                learned.append(f"Dislike: {dislike_val}")

        # 3. Active Projects & Work Focus
        # e.g., "I am working on the Iron Man helmet", "My current project is Jarvis"
        proj_match = re.search(r"\b(?:working on|project is|building|developing)\s+([^,.\n]+)", text, re.IGNORECASE)
        if proj_match:
            proj_val = proj_match.group(1).strip()
            if len(proj_val) > 3 and len(proj_val.split()) <= 7:
                self.store_fact("User", "Current Project", proj_val, category="project")
                self.set_focus(proj_val)
                learned.append(f"Project Focus: {proj_val}")

        # 4. Explicit Memory Declarations
        # e.g., "remember that my car is a Tesla", "keep in mind that the server port is 8080"
        rem_match = re.search(r"\b(?:remember that|keep in mind that|don't forget that|take note that)\s+(.+)", text, re.IGNORECASE)
        if rem_match:
            note_val = rem_match.group(1).strip()
            self.store_fact("User Note", "States", note_val, category="general")
            learned.append(f"Explicit Note: {note_val}")

        # 5. Goal Declarations
        # e.g., "my goal is to finish the thesis", "we need to fix the audio latency"
        goal_match = re.search(r"\b(?:my goal is to|we need to|i have to|task is to)\s+([^,.\n]+)", text, re.IGNORECASE)
        if goal_match:
            goal_val = goal_match.group(1).strip()
            if len(goal_val) > 4 and len(goal_val.split()) <= 10:
                self.add_goal(goal_val, importance=7)
                learned.append(f"Active Goal: {goal_val}")

        return learned

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Cognitive Synthesis (Prompt Context Enrichment)
    # ─────────────────────────────────────────────────────────────────────────

    def synthesize_context(self, current_prompt: str) -> str:
        """
        Synthesizes active working memory, relevant declarative facts,
        and associative episodic traces into a rich cognitive prompt context.
        """
        parts = []

        # 1. Working Memory
        focus = self.get_focus()
        goals = self.get_active_goals(limit=3)
        wm_desc = f"Active Focus: {focus}"
        if goals:
            wm_desc += " | Pending Objectives: " + "; ".join([g['goal'] for g in goals])
        parts.append(f"[Cognitive State]: {wm_desc}")

        # 2. Relevant Facts & User Profile
        facts = self.recall_facts(query=current_prompt, limit=4)
        if facts:
            fact_lines = [f"{f['subject']} {f['predicate']}: {f['object_value']}" for f in facts]
            parts.append(f"[Known Personal Facts & Preferences]: {'; '.join(fact_lines)}")

        # 3. Associative Episodic Traces
        episodes = self.recall_episodes(query=current_prompt, top_k=2)
        if episodes:
            ep_lines = [f"{ep['summary']}" for ep in episodes]
            parts.append(f"[Relevant Past Interactions]: {'; '.join(ep_lines)}")

        return "\n".join(parts)

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Cognitive Directives & Conversational Handler
    # ─────────────────────────────────────────────────────────────────────────

    def handle_cognitive_directive(self, prompt: str) -> Tuple[bool, str]:
        """
        Evaluates and responds to user queries about cognitive state,
        user profile, active goals, and memory management.
        """
        clean = prompt.strip()
        lower = clean.lower()

        # 1. User Profile & Preferences
        if any(p in lower for p in [
            "what do you know about me", "who am i", "what are my preferences",
            "show my profile", "tell me about myself", "what have you learned about me",
            "cognitive profile", "show user profile"
        ]):
            summary = self.get_user_profile_summary()
            return True, f"Here is the consolidated summary of your cognitive profile, sir:\n{summary}"

        # 2. Working Memory & Current Focus
        if any(p in lower for p in [
            "what is our focus", "what are we working on", "current focus",
            "what's our focus", "working memory", "current objective", "what are my goals",
            "what are our goals", "our goals", "show active goals", "show goals", "list goals",
            "current goals", "active objectives", "what are we doing"
        ]):
            summary = self.get_working_memory_summary()
            return True, f"Here is our active cognitive working state, sir:\n{summary}"

        # 3. Set Working Focus
        focus_match = re.search(r"\b(?:set focus to|change focus to|focus on|our focus is now)\s+(.+)", clean, re.IGNORECASE)
        if focus_match:
            new_focus = focus_match.group(1).strip()
            ack = self.set_focus(new_focus)
            return True, ack

        # 4. Add Goal
        goal_match = re.search(r"\b(?:add goal|new goal|set goal|record goal)\s*[:\-]?\s*(.+)", clean, re.IGNORECASE)
        if goal_match:
            goal_txt = goal_match.group(1).strip()
            gid = self.add_goal(goal_txt, importance=7)
            return True, f"Objective #{gid} committed to active working memory, sir: \"{goal_txt}\""

        # 5. Complete Goal
        comp_match = re.search(r"\b(?:complete goal|finish goal|mark goal done|goal completed)\s*[:\-]?\s*(.+)", clean, re.IGNORECASE)
        if comp_match:
            target = comp_match.group(1).strip()
            ok = self.complete_goal(target)
            if ok:
                return True, f"Objective '{target}' marked as completed in cognitive working memory, sir."
            return True, f"Could not find an active objective matching '{target}', sir."

        # 6. Episodic Recall
        if any(p in lower for p in [
            "what happened earlier", "what did we do today", "recent episodes",
            "past interactions", "what did we do recently"
        ]):
            summary = self.get_recent_episodes_summary(limit=4)
            return True, f"{summary}, sir."

        # 7. Forget or Delete Facts
        forget_match = re.search(r"\b(?:forget that|delete fact|remove fact|forget preference|forget note)\s+(.+)", clean, re.IGNORECASE)
        if forget_match:
            target = forget_match.group(1).strip()
            count = self.delete_fact(target)
            if count > 0:
                return True, f"Excised {count} matching declarative record(s) from cognitive memory, sir."
            return True, f"No cognitive records matching '{target}' were found to remove, sir."

        # 8. Memory Reflection & Consolidation
        if any(p in lower for p in [
            "consolidate memory", "consolidate memories", "cognitive reflection",
            "reflect on memories", "synthesize memory"
        ]):
            facts_count = len(self.recall_facts(limit=100))
            ep_count = len(self.recall_episodes(top_k=100))
            goals_count = len(self.get_active_goals())
            return True, (
                f"Cognitive consolidation complete, sir. Currently indexing {facts_count} declarative profile facts, "
                f"{ep_count} episodic traces, and {goals_count} active working objectives across the neural matrix."
            )

        return False, ""

# Global singleton
cognitive_memory = CognitiveMemory()
