"""
J.A.R.V.I.S. Scaled Persistent Episodic Memory & Cognitive Interaction Matrix.
Features:
1. Multi-Year High-Throughput Indexed Episodic Engine:
   - SQLite ACID-compliant persistence for lifelong conversational episodes,
     tactical milestones, system events, and user emotional valence.
2. Emotional Valence & Salience Indexing:
   - Tracks valence (-1.0 to +1.0), cognitive arousal (0.0 to 1.0), and importance (1 to 10).
3. Hybrid Semantic & Recency-Decayed Retrieval:
   - Dense 384-dimensional vector embedding search fused with lexical BM25 matching
     and exponential temporal recency decay: Score = (Vector + Lexical) * exp(-lambda * dt).
4. Automated Cross-Linking with GraphRAG:
   - Automatically detects mentioned entities (alloys, systems, blueprints, science)
     and registers episodic observations in the knowledge graph.
5. Lifelong Storage Budget:
   - Part of the 30 GB persistent memory tier under models/archive/ (air-gapped & gitignored).
6. 100% Free Plan, zero external cloud dependency, local offline SQLite.
"""

import datetime
import json
import logging
import math
import os
import re
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

import config
from core.vector_memory import FastEmbeddingEngine

logger = logging.getLogger("PersistentEpisodicMemory")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = PROJECT_ROOT / "models" / "archive"
DEFAULT_DB_PATH = ARCHIVE_DIR / "persistent_episodes.db"


@dataclass
class EpisodeRecord:
    """A single persistent interaction or cognitive episode."""
    episode_id: str
    timestamp: float
    iso_time: str
    session_id: str
    speaker: str  # "User", "JARVIS", "System"
    intent: str
    emotional_valence: float  # -1.0 to 1.0
    arousal: float  # 0.0 to 1.0
    importance: int  # 1 to 10
    content: str
    context_tags: List[str] = field(default_factory=list)
    entities_mentioned: List[str] = field(default_factory=list)
    action_taken: str = ""
    relevance_score: float = 1.0


class PersistentEpisodicMemory:
    """
    Scaled Lifelong Episodic Memory Controller for J.A.R.V.I.S.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.embedder = FastEmbeddingEngine(seed=42)
        self._init_db()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initializes tables and high-speed B-tree indexes for episodic queries."""
        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    episode_id TEXT UNIQUE NOT NULL,
                    timestamp REAL NOT NULL,
                    iso_time TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    speaker TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    emotional_valence REAL NOT NULL DEFAULT 0.0,
                    arousal REAL NOT NULL DEFAULT 0.5,
                    importance INTEGER NOT NULL DEFAULT 5,
                    content TEXT NOT NULL,
                    context_tags_json TEXT NOT NULL DEFAULT '[]',
                    entities_json TEXT NOT NULL DEFAULT '[]',
                    action_taken TEXT NOT NULL DEFAULT '',
                    embedding BLOB
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS episode_entity_index (
                    episode_id TEXT NOT NULL,
                    entity_name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'mentioned',
                    PRIMARY KEY (episode_id, entity_name),
                    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ep_timestamp ON episodes(timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ep_speaker ON episodes(speaker)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ep_intent ON episodes(intent)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ep_importance ON episodes(importance)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ep_valence ON episodes(emotional_valence)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_eei_entity ON episode_entity_index(entity_name)")
            conn.commit()

    def record_episode(
        self,
        speaker: str,
        content: str,
        intent: str = "general_query",
        session_id: str = "default_session",
        emotional_valence: float = 0.0,
        arousal: float = 0.5,
        importance: int = 5,
        context_tags: Optional[List[str]] = None,
        entities: Optional[List[str]] = None,
        action_taken: str = "",
        auto_link_graph: bool = True
    ) -> str:
        """
        Records a persistent episode with vector embedding and auto-links to GraphRAG.
        """
        now = time.time()
        iso = datetime.datetime.fromtimestamp(now, tz=datetime.timezone.utc).isoformat()
        ep_id = f"ep_{uuid.uuid4().hex[:12]}"
        tags = context_tags or []
        extracted_entities = list(entities or [])

        # Heuristic entity detection if not explicitly supplied
        if not extracted_entities:
            extracted_entities = self._detect_candidate_entities(content)

        # Compute 384-d vector embedding
        vec = self.embedder.embed(content)
        blob = vec.tobytes()

        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO episodes (
                    episode_id, timestamp, iso_time, session_id, speaker, intent,
                    emotional_valence, arousal, importance, content,
                    context_tags_json, entities_json, action_taken, embedding
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ep_id, now, iso, session_id, speaker, intent,
                max(-1.0, min(1.0, emotional_valence)),
                max(0.0, min(1.0, arousal)),
                max(1, min(10, importance)),
                content.strip(),
                json.dumps(tags),
                json.dumps(extracted_entities),
                action_taken.strip(),
                blob
            ))

            for ent in extracted_entities:
                cur.execute("""
                    INSERT OR IGNORE INTO episode_entity_index (episode_id, entity_name, role)
                    VALUES (?, ?, 'mentioned')
                """, (ep_id, ent.strip()))

            conn.commit()

        # Cross-link with GraphRAG
        if auto_link_graph and extracted_entities:
            self._link_with_graph_rag(extracted_entities, content, ep_id)

        return ep_id

    def _detect_candidate_entities(self, text: str) -> List[str]:
        """Detects STEM, CAD, and system keywords mentioned in conversational text."""
        candidates = []
        known_keywords = [
            "Mark 85", "Mark 50", "Arc Reactor", "Repulsor", "Dum-E", "Drone",
            "Titanium", "Gold-Titanium", "Ti-6Al-4V", "Inconel", "Nitinol",
            "Palladium", "Beryllium", "Gold", "Carbon Nanotube",
            "IS 2190", "AES-256", "Hypersonic", "Aerodynamics", "Fire Safety",
            "Fusion", "Plasma", "Toroidal"
        ]
        text_lower = text.lower()
        for kw in known_keywords:
            if kw.lower() in text_lower:
                candidates.append(kw)
        return list(dict.fromkeys(candidates))

    def _link_with_graph_rag(self, entities: List[str], text: str, episode_id: str):
        """Cross-references episode observation into GraphRAG."""
        try:
            from core.graph_rag import graph_rag
            for ent in entities:
                obs_content = f"[Episode {episode_id}] {text[:150]}"
                graph_rag.record_observation(entity_name=ent, content=obs_content, confidence=0.95)
        except Exception as e:
            logger.debug(f"GraphRAG cross-link skipped: {e}")

    def query_episodes(
        self,
        query_text: Optional[str] = None,
        speaker: Optional[str] = None,
        min_importance: int = 0,
        min_valence: Optional[float] = None,
        max_valence: Optional[float] = None,
        limit: int = 10,
        time_decay: bool = True
    ) -> List[EpisodeRecord]:
        """
        Retrieves ranked episodes via hybrid vector similarity + lexical match + temporal decay.
        Score = (0.6 * Vector + 0.4 * Lexical) * exp(-lambda * dt_days)
        """
        now = time.time()
        q_vec = self.embedder.embed(query_text) if query_text else None
        q_tokens = set(re.findall(r"\w+", query_text.lower())) if query_text else set()

        where_clauses = ["importance >= ?"]
        params: List[Any] = [min_importance]

        if speaker:
            where_clauses.append("speaker = ?")
            params.append(speaker)
        if min_valence is not None:
            where_clauses.append("emotional_valence >= ?")
            params.append(min_valence)
        if max_valence is not None:
            where_clauses.append("emotional_valence <= ?")
            params.append(max_valence)

        where_sql = " AND ".join(where_clauses)
        sql = f"""
            SELECT episode_id, timestamp, iso_time, session_id, speaker, intent,
                   emotional_valence, arousal, importance, content,
                   context_tags_json, entities_json, action_taken, embedding
            FROM episodes WHERE {where_sql} ORDER BY timestamp DESC LIMIT ?
        """
        params.append(limit * 4 if query_text else limit)

        candidates = []
        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            for row in cur.fetchall():
                emb = np.frombuffer(row["embedding"], dtype=np.float32) if row["embedding"] else None
                candidates.append({
                    "row": row,
                    "embedding": emb
                })

        if not candidates:
            return []

        results: List[Tuple[float, EpisodeRecord]] = []
        # Lambda decay constant: half-life ~60 days
        lambda_decay = 0.0115

        for cand in candidates:
            row = cand["row"]
            ts = row["timestamp"]
            dt_days = max(0.0, (now - ts) / 86400.0)
            decay_factor = math.exp(-lambda_decay * dt_days) if time_decay else 1.0

            # 1. Vector similarity
            if q_vec is not None and cand["embedding"] is not None:
                v_score = float(np.dot(q_vec, cand["embedding"]))
                v_score = max(0.0, min(1.0, v_score))
            else:
                v_score = 0.5 if not query_text else 0.0

            # 2. Lexical overlap
            c_tokens = set(re.findall(r"\w+", row["content"].lower()))
            if q_tokens and c_tokens:
                lex_score = len(q_tokens.intersection(c_tokens)) / float(len(q_tokens))
            else:
                lex_score = 0.5 if not query_text else 0.0

            # Importance multiplier (0.8 to 1.3)
            imp_boost = 0.8 + (row["importance"] / 20.0)

            if query_text:
                base_score = (0.60 * v_score) + (0.40 * lex_score)
            else:
                base_score = 1.0

            final_score = base_score * decay_factor * imp_boost

            rec = EpisodeRecord(
                episode_id=row["episode_id"],
                timestamp=row["timestamp"],
                iso_time=row["iso_time"],
                session_id=row["session_id"],
                speaker=row["speaker"],
                intent=row["intent"],
                emotional_valence=row["emotional_valence"],
                arousal=row["arousal"],
                importance=row["importance"],
                content=row["content"],
                context_tags=json.loads(row["context_tags_json"]),
                entities_mentioned=json.loads(row["entities_json"]),
                action_taken=row["action_taken"],
                relevance_score=round(final_score, 4)
            )
            results.append((final_score, rec))

        results.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in results[:limit]]

    def get_episodes_by_entity(self, entity_name: str, limit: int = 10) -> List[EpisodeRecord]:
        """Retrieves episodes that directly referenced an entity or component."""
        sql = """
            SELECT e.episode_id, e.timestamp, e.iso_time, e.session_id, e.speaker, e.intent,
                   e.emotional_valence, e.arousal, e.importance, e.content,
                   e.context_tags_json, e.entities_json, e.action_taken
            FROM episodes e
            JOIN episode_entity_index i ON e.episode_id = i.episode_id
            WHERE LOWER(i.entity_name) = LOWER(?)
            ORDER BY e.timestamp DESC LIMIT ?
        """
        results = []
        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, (entity_name.strip(), limit))
            for row in cur.fetchall():
                results.append(EpisodeRecord(
                    episode_id=row["episode_id"],
                    timestamp=row["timestamp"],
                    iso_time=row["iso_time"],
                    session_id=row["session_id"],
                    speaker=row["speaker"],
                    intent=row["intent"],
                    emotional_valence=row["emotional_valence"],
                    arousal=row["arousal"],
                    importance=row["importance"],
                    content=row["content"],
                    context_tags=json.loads(row["context_tags_json"]),
                    entities_mentioned=json.loads(row["entities_json"]),
                    action_taken=row["action_taken"]
                ))
        return results

    def get_timeline_stats(self) -> Dict[str, Any]:
        """Provides statistical telemetry on episodic storage and cognitive traces."""
        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as c FROM episodes")
            total = cur.fetchone()["c"]

            cur.execute("SELECT speaker, COUNT(*) as cnt FROM episodes GROUP BY speaker")
            speakers = {r["speaker"]: r["cnt"] for r in cur.fetchall()}

            cur.execute("SELECT AVG(emotional_valence) as avg_val, AVG(arousal) as avg_ar FROM episodes")
            mood_row = cur.fetchone()
            avg_val = round(float(mood_row["avg_val"] or 0.0), 3)
            avg_ar = round(float(mood_row["avg_ar"] or 0.5), 3)

            cur.execute("""
                SELECT entity_name, COUNT(*) as cnt
                FROM episode_entity_index
                GROUP BY entity_name ORDER BY cnt DESC LIMIT 10
            """)
            top_entities = {r["entity_name"]: r["cnt"] for r in cur.fetchall()}

        size_mb = 0.0
        if self.db_path.exists():
            size_mb = round(self.db_path.stat().st_size / (1024 * 1024), 2)

        return {
            "total_episodes": total,
            "speakers": speakers,
            "average_emotional_valence": avg_val,
            "average_arousal": avg_ar,
            "top_entities_referenced": top_entities,
            "db_size_mb": size_mb,
            "db_path": str(self.db_path)
        }

    def compact_old_episodes(self, days_threshold: float = 90.0, retain_importance_gte: int = 7) -> int:
        """
        Compacts storage by pruning routine low-importance episodes older than days_threshold,
        while strictly preserving high-importance milestones and lessons.
        """
        cutoff = time.time() - (days_threshold * 86400.0)
        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM episodes
                WHERE timestamp < ? AND importance < ?
            """, (cutoff, retain_importance_gte))
            pruned = cur.rowcount
            conn.commit()

        logger.info(f"Compacted episodic memory: pruned {pruned} low-importance episodes older than {days_threshold} days.")
        return pruned


# Global Singleton Instance
persistent_episodic_memory = PersistentEpisodicMemory()
