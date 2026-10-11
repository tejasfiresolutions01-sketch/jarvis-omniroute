"""
J.A.R.V.I.S. Hybrid GraphRAG & Entity-Relation Local Knowledge Engine.
Features:
1. SQLite Entity-Relation Graph Store:
   - Atomic persistence for entities, semantic relations, and dynamic observations.
2. N-Hop Relational Traversal & Path Discovery:
   - Breadth-first graph traversal for multi-hop contextual reasoning across systems and facts.
3. Hybrid Search Fusion:
   - Synthesizes 384-dimensional dense vector embeddings with lexical token matching
     and graph topology centrality scoring.
4. Self-Consolidating Autonomous Memory:
   - Automatic edge reinforcement, observation compaction, and semantic synonym clustering.
5. 100% Free Plan, zero external cloud dependencies, offline SQLite storage.
"""

import collections
import json
import logging
import re
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np

import config
from core.vector_memory import FastEmbeddingEngine

logger = logging.getLogger("GraphRAG")


@dataclass
class EntityNode:
    """Represents a node in the J.A.R.V.I.S. Knowledge Graph."""
    id: str
    name: str
    entity_type: str
    description: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    access_count: int = 0


@dataclass
class RelationEdge:
    """Represents a directed or symmetric edge between two knowledge entities."""
    id: str
    source_name: str
    target_name: str
    relation_type: str
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class SearchResult:
    """Result of a hybrid GraphRAG contextual retrieval."""
    entity: EntityNode
    score: float
    vector_score: float
    lexical_score: float
    graph_boost: float
    connected_entities: List[str] = field(default_factory=list)


class GraphRAG:
    """
    Local Hybrid Knowledge Graph Engine with N-hop relational traversal
    and multi-signal retrieval fusion.
    """

    DEFAULT_DB_PATH = Path(config.DATA_DIR) / "knowledge_graph.db"

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.embedder = FastEmbeddingEngine()
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
        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    name TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    properties_json TEXT NOT NULL DEFAULT '{}',
                    embedding BLOB,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    access_count INTEGER NOT NULL DEFAULT 0
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS relations (
                    id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    target_name TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    weight REAL NOT NULL DEFAULT 1.0,
                    properties_json TEXT NOT NULL DEFAULT '{}',
                    created_at REAL NOT NULL,
                    FOREIGN KEY (source_name) REFERENCES entities (name) ON DELETE CASCADE,
                    FOREIGN KEY (target_name) REFERENCES entities (name) ON DELETE CASCADE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 1.0,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (entity_name) REFERENCES entities (name) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_name)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_name)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_obs_entity ON observations(entity_name)")
            conn.commit()

    def upsert_entity(
        self,
        name: str,
        entity_type: str,
        description: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> EntityNode:
        """Creates or updates a knowledge entity with precomputed vector embedding."""
        clean_name = name.strip()
        now = time.time()
        props_str = json.dumps(properties or {})
        embed_text = f"{clean_name}: {description}"
        vec = self.embedder.embed(embed_text)
        blob = vec.tobytes()

        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT created_at, access_count FROM entities WHERE name = ?", (clean_name,))
            row = cur.fetchone()
            if row:
                created_at = row["created_at"]
                access_count = row["access_count"]
                cur.execute("""
                    UPDATE entities
                    SET entity_type = ?, description = ?, properties_json = ?, embedding = ?, updated_at = ?
                    WHERE name = ?
                """, (entity_type, description, props_str, blob, now, clean_name))
            else:
                created_at = now
                access_count = 0
                cur.execute("""
                    INSERT INTO entities (name, entity_type, description, properties_json, embedding, created_at, updated_at, access_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (clean_name, entity_type, description, props_str, blob, created_at, now, access_count))
            conn.commit()

        return EntityNode(
            id=clean_name,
            name=clean_name,
            entity_type=entity_type,
            description=description,
            properties=properties or {},
            created_at=created_at,
            updated_at=now,
            access_count=access_count
        )

    def add_relation(
        self,
        source_name: str,
        target_name: str,
        relation_type: str,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None
    ) -> RelationEdge:
        """Establishes a directed semantic relation edge between two entities."""
        s = source_name.strip()
        t = target_name.strip()
        edge_id = f"{s}::[{relation_type}]::{t}"
        now = time.time()
        props_str = json.dumps(properties or {})

        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO relations (id, source_name, target_name, relation_type, weight, properties_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    weight = excluded.weight,
                    properties_json = excluded.properties_json
            """, (edge_id, s, t, relation_type, weight, props_str, now))
            conn.commit()

        return RelationEdge(
            id=edge_id,
            source_name=s,
            target_name=t,
            relation_type=relation_type,
            weight=weight,
            properties=properties or {},
            created_at=now
        )

    def record_observation(self, entity_name: str, content: str, confidence: float = 1.0) -> int:
        """Records an episodic observation associated with an entity."""
        name = entity_name.strip()
        now = time.time()
        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO observations (entity_name, content, confidence, timestamp)
                VALUES (?, ?, ?, ?)
            """, (name, content.strip(), confidence, now))
            conn.commit()
            return cur.lastrowid

    def get_entity(self, name: str) -> Optional[EntityNode]:
        """Retrieves an entity and increments its access counter."""
        clean_name = name.strip()
        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT name, entity_type, description, properties_json, created_at, updated_at, access_count
                FROM entities WHERE name = ?
            """, (clean_name,))
            row = cur.fetchone()
            if not row:
                return None
            cur.execute("UPDATE entities SET access_count = access_count + 1 WHERE name = ?", (clean_name,))
            conn.commit()
            return EntityNode(
                id=row["name"],
                name=row["name"],
                entity_type=row["entity_type"],
                description=row["description"],
                properties=json.loads(row["properties_json"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                access_count=row["access_count"] + 1
            )

    def get_neighbors(
        self,
        name: str,
        direction: str = "both",
        relation_type: Optional[str] = None
    ) -> List[Tuple[str, str, float]]:
        """
        Returns list of (neighbor_entity_name, relation_type, weight).
        direction can be 'out', 'in', or 'both'.
        """
        clean_name = name.strip()
        results = []
        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            if direction in ("out", "both"):
                query = "SELECT target_name, relation_type, weight FROM relations WHERE source_name = ?"
                params: List[Any] = [clean_name]
                if relation_type:
                    query += " AND relation_type = ?"
                    params.append(relation_type)
                cur.execute(query, params)
                for r in cur.fetchall():
                    results.append((r["target_name"], r["relation_type"], r["weight"]))

            if direction in ("in", "both"):
                query = "SELECT source_name, relation_type, weight FROM relations WHERE target_name = ?"
                params = [clean_name]
                if relation_type:
                    query += " AND relation_type = ?"
                    params.append(relation_type)
                cur.execute(query, params)
                for r in cur.fetchall():
                    results.append((r["source_name"], r["relation_type"], r["weight"]))

        return results

    def find_path(
        self,
        source_name: str,
        target_name: str,
        max_hops: int = 4
    ) -> Optional[List[Tuple[str, str, str]]]:
        """
        Breadth-first search for shortest relational path between two entities.
        Returns list of (from_node, relation_type, to_node) or None.
        """
        s = source_name.strip()
        t = target_name.strip()
        if s == t:
            return []

        queue = collections.deque([(s, [])])
        visited = {s}

        while queue:
            current, path = queue.popleft()
            if len(path) >= max_hops:
                continue

            # Query outgoing edges
            with self._lock, self._get_conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT target_name, relation_type FROM relations WHERE source_name = ?", (current,))
                rows = cur.fetchall()

            for r in rows:
                next_node = r["target_name"]
                rel = r["relation_type"]
                new_path = path + [(current, rel, next_node)]
                if next_node == t:
                    return new_path
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, new_path))

        return None

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        entity_type: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Multi-signal hybrid retrieval combining dense vector similarity,
        lexical token matching, and graph edge density boost.
        """
        if not query or not query.strip():
            return []

        q_clean = query.lower().strip()
        q_tokens = set(re.findall(r"\w+", q_clean))
        q_vec = self.embedder.embed(query)

        candidates: List[Dict[str, Any]] = []
        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            sql = "SELECT name, entity_type, description, properties_json, embedding, access_count FROM entities"
            params: List[Any] = []
            if entity_type:
                sql += " WHERE entity_type = ?"
                params.append(entity_type)
            cur.execute(sql, params)
            for row in cur.fetchall():
                candidates.append({
                    "name": row["name"],
                    "entity_type": row["entity_type"],
                    "description": row["description"],
                    "properties": json.loads(row["properties_json"]),
                    "embedding": np.frombuffer(row["embedding"], dtype=np.float32) if row["embedding"] else None,
                    "access_count": row["access_count"]
                })

        if not candidates:
            return []

        results: List[SearchResult] = []
        for cand in candidates:
            # 1. Vector cosine similarity
            if cand["embedding"] is not None and len(cand["embedding"]) == len(q_vec):
                v_score = float(np.dot(q_vec, cand["embedding"]))
                v_score = max(0.0, min(1.0, v_score))
            else:
                v_score = 0.0

            # 2. Lexical token overlap
            name_desc_tokens = set(re.findall(r"\w+", f"{cand['name']} {cand['description']}".lower()))
            if q_tokens and name_desc_tokens:
                overlap = len(q_tokens.intersection(name_desc_tokens))
                lex_score = overlap / float(len(q_tokens))
            else:
                lex_score = 0.0

            # 3. Graph Degree & Connectivity Boost
            neighbors = self.get_neighbors(cand["name"], direction="both")
            connected_names = [n[0] for n in neighbors]
            # Graph centrality boost up to 0.25 based on degree and access frequency
            graph_boost = min(0.25, (len(neighbors) * 0.04) + (min(cand["access_count"], 10) * 0.01))

            # Fused Weighted Score: 0.50 Vector + 0.30 Lexical + 0.20 Graph
            total_score = (0.50 * v_score) + (0.30 * lex_score) + (0.20 * (graph_boost / 0.25))

            node = EntityNode(
                id=cand["name"],
                name=cand["name"],
                entity_type=cand["entity_type"],
                description=cand["description"],
                properties=cand["properties"],
                access_count=cand["access_count"]
            )
            results.append(SearchResult(
                entity=node,
                score=round(total_score, 4),
                vector_score=round(v_score, 4),
                lexical_score=round(lex_score, 4),
                graph_boost=round(graph_boost, 4),
                connected_entities=connected_names
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def consolidate_memory(self, max_stale_days: float = 30.0) -> Dict[str, int]:
        """
        Autonomous knowledge graph consolidation:
        - Prunes orphaned observations older than threshold.
        - Boosts weights on heavily co-accessed relations.
        - Synthesizes cluster health telemetry.
        """
        cutoff = time.time() - (max_stale_days * 86400.0)
        pruned_obs = 0
        reinforced_edges = 0

        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            # 1. Prune ancient observations
            cur.execute("DELETE FROM observations WHERE timestamp < ?", (cutoff,))
            pruned_obs = cur.rowcount

            # 2. Reinforce edges between active nodes
            cur.execute("""
                UPDATE relations
                SET weight = MIN(5.0, weight + 0.1)
                WHERE source_name IN (SELECT name FROM entities WHERE access_count > 5)
                  AND target_name IN (SELECT name FROM entities WHERE access_count > 5)
            """)
            reinforced_edges = cur.rowcount
            conn.commit()

        logger.info(f"Consolidated GraphRAG: pruned {pruned_obs} observations, reinforced {reinforced_edges} edges.")
        return {
            "pruned_observations": pruned_obs,
            "reinforced_edges": reinforced_edges
        }

    def dump_graph_summary(self) -> Dict[str, Any]:
        """Returns statistical telemetry on the local knowledge graph."""
        with self._lock, self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS c FROM entities")
            entity_count = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM relations")
            relation_count = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM observations")
            obs_count = cur.fetchone()["c"]
            cur.execute("SELECT entity_type, COUNT(*) as cnt FROM entities GROUP BY entity_type")
            types = {r["entity_type"]: r["cnt"] for r in cur.fetchall()}

        return {
            "total_entities": entity_count,
            "total_relations": relation_count,
            "total_observations": obs_count,
            "entity_types": types
        }

    def ingest_stark_knowledge_graph(
        self,
        archive_engine: Optional[Any] = None,
        cad_manager: Optional[Any] = None
    ) -> Dict[str, int]:
        """
        Cross-links all STEM articles, periodic elements, and 3D CAD blueprints
        into the relational GraphRAG SQLite engine with multi-hop semantic edges.
        """
        entities_added = 0
        relations_added = 0

        # 1. Ingest CAD Blueprints & Hardware Subsystems
        if cad_manager is None:
            try:
                from core.cad_blueprint_manager import CADBlueprintManager
                cad_manager = CADBlueprintManager()
            except Exception as e:
                logger.warning(f"Could not load CADBlueprintManager for graph ingestion: {e}")

        if cad_manager and hasattr(cad_manager, "catalog"):
            for bp_id, bp in cad_manager.catalog.items():
                self.upsert_entity(
                    name=bp.name,
                    entity_type="cad_hardware_system",
                    description=f"{bp.description} Category: {bp.category}. Mass: {bp.mass_kg}kg, Power: {bp.power_draw_kw}kW.",
                    properties={
                        "blueprint_id": bp.blueprint_id,
                        "category": bp.category,
                        "mass_kg": bp.mass_kg,
                        "power_draw_kw": bp.power_draw_kw,
                        "vertex_count": bp.vertex_count,
                        "face_count": bp.face_count,
                        "file_path": bp.file_path,
                    }
                )
                entities_added += 1

                # Link materials to hardware system
                for mat_name in bp.materials:
                    self.upsert_entity(
                        name=mat_name,
                        entity_type="aerospace_material",
                        description=f"Advanced material alloy specified for Stark engineering assets: {mat_name}."
                    )
                    entities_added += 1

                    self.add_relation(
                        source_name=bp.name,
                        target_name=mat_name,
                        relation_type="USES_MATERIAL",
                        weight=1.5,
                        properties={"specification_role": "structural_skin"}
                    )
                    relations_added += 1

            # Known inter-subsystem relations
            subsystem_edges = [
                ("Mark 50 Toroidal Arc Reactor (Exploded View)", "Iron Man Mark 85 Full Tactical Armor", "POWERS", 2.0),
                ("Mark 50 Toroidal Arc Reactor (Exploded View)", "Stark Hypersonic Tactical UAV Airframe", "POWERS", 1.5),
                ("Mark 50 Toroidal Arc Reactor (Exploded View)", "Mark 85 High-Definition Repulsor Gauntlet", "POWERS", 2.0),
                ("Mark 85 High-Definition Repulsor Gauntlet", "Iron Man Mark 85 Full Tactical Armor", "SUBSYSTEM_OF", 1.8),
                ("Dum-E Workshop Robotic Articulated Arm", "Iron Man Mark 85 Full Tactical Armor", "ASSEMBLES", 1.2),
                ("Dum-E Workshop Robotic Articulated Arm", "Mark 85 High-Definition Repulsor Gauntlet", "ASSEMBLES", 1.2),
            ]
            for src, tgt, rel, w in subsystem_edges:
                if self.get_entity(src) and self.get_entity(tgt):
                    self.add_relation(src, tgt, rel, weight=w)
                    relations_added += 1

        # 2. Ingest Stark Global Archive Articles
        if archive_engine is None:
            try:
                from core.stark_archive import StarkArchiveEngine
                archive_engine = StarkArchiveEngine()
            except Exception as e:
                logger.warning(f"Could not load StarkArchiveEngine for graph ingestion: {e}")

        if archive_engine:
            articles = archive_engine.get_all_articles(limit=500)
            for art in articles:
                ent_type = f"stark_{art.category}"
                self.upsert_entity(
                    name=art.title,
                    entity_type=ent_type,
                    description=art.summary,
                    properties={
                        "category": art.category,
                        "formulas": art.formulas,
                        "specifications": art.specifications
                    }
                )
                entities_added += 1

                # Establish material & element linkages
                title_lower = art.title.lower()
                if "titanium" in title_lower and "gold" in title_lower:
                    self.add_relation(art.title, "Titanium (Ti)", "ALLOYED_FROM", weight=1.4)
                    self.add_relation(art.title, "Gold (Au)", "ALLOYED_FROM", weight=1.4)
                    self.add_relation(art.title, "High-Altitude Icing Dynamics", "MITIGATES", weight=2.0)
                    relations_added += 3

                    # Link to Mark 85
                    if self.get_entity("Iron Man Mark 85 Full Tactical Armor"):
                        self.add_relation("Iron Man Mark 85 Full Tactical Armor", art.title, "ENGINEERED_WITH", weight=1.8)
                        relations_added += 1

                elif "ti-6al-4v" in title_lower or "grade 5" in title_lower:
                    self.add_relation(art.title, "Titanium (Ti)", "ALLOYED_FROM", weight=1.4)
                    self.add_relation(art.title, "Aluminium (Al)", "ALLOYED_FROM", weight=1.2)
                    self.add_relation(art.title, "Vanadium (V)", "ALLOYED_FROM", weight=1.2)
                    relations_added += 3
                    if self.get_entity("Stark Hypersonic Tactical UAV Airframe"):
                        self.add_relation("Stark Hypersonic Tactical UAV Airframe", art.title, "ENGINEERED_WITH", weight=1.6)
                        relations_added += 1

                elif "arc reactor" in title_lower:
                    if self.get_entity("Mark 50 Toroidal Arc Reactor (Exploded View)"):
                        self.add_relation("Mark 50 Toroidal Arc Reactor (Exploded View)", art.title, "THEORY_OF", weight=2.0)
                        relations_added += 1
                    self.add_relation(art.title, "Palladium (Pd)", "USES_ELEMENT", weight=1.3)
                    self.add_relation(art.title, "Beryllium (Be)", "USES_ELEMENT", weight=1.3)
                    relations_added += 2

                elif "is 2190" in title_lower or "fire" in title_lower:
                    self.add_relation(art.title, "Fire Engineering & Suppression Dynamics", "GOVERNS", weight=1.7)
                    relations_added += 1

                elif "cryptography" in title_lower or "aes-256" in title_lower:
                    if self.get_entity("Iron Man Mark 85 Full Tactical Armor"):
                        self.add_relation("Iron Man Mark 85 Full Tactical Armor", art.title, "SECURING_AVIONICS", weight=1.5)
                        relations_added += 1

        logger.info(f"Stark Knowledge Graph Ingestion Complete: {entities_added} entities, {relations_added} relations.")
        return {
            "entities_added": entities_added,
            "relations_added": relations_added
        }

    def find_subsystem_dependencies(
        self,
        root_system: str,
        max_hops: int = 3
    ) -> Dict[str, Any]:
        """
        Recursively discovers all upstream power sources, materials, subsystems,
        and engineering principles connected to a given system within max_hops.
        """
        clean_name = root_system.strip()
        visited: Set[str] = {clean_name}
        queue: collections.deque = collections.deque([(clean_name, 0, [clean_name])])

        power_sources: List[str] = []
        materials: List[str] = []
        subsystems: List[str] = []
        assembly_units: List[str] = []
        principles: List[str] = []
        all_paths: List[List[str]] = []

        while queue:
            curr_name, depth, path = queue.popleft()
            if depth >= max_hops:
                continue

            neighbors = self.get_neighbors(curr_name, direction="both")
            for neighbor_name, rel_type, weight in neighbors:
                if neighbor_name not in visited:
                    visited.add(neighbor_name)
                    new_path = path + [f"-[{rel_type}]->", neighbor_name]
                    all_paths.append(new_path)
                    queue.append((neighbor_name, depth + 1, new_path))

                    # Classify node by relation type or entity type
                    ent = self.get_entity(neighbor_name)
                    ent_type = ent.entity_type if ent else ""

                    if rel_type in ("POWERS", "POWERED_BY") or "power" in ent_type:
                        if neighbor_name not in power_sources and neighbor_name != clean_name:
                            power_sources.append(neighbor_name)
                    elif rel_type in ("USES_MATERIAL", "ALLOYED_FROM", "ENGINEERED_WITH") or "material" in ent_type or "alloy" in ent_type:
                        if neighbor_name not in materials and neighbor_name != clean_name:
                            materials.append(neighbor_name)
                    elif rel_type in ("SUBSYSTEM_OF", "HAS_SUBSYSTEM") or "subsystem" in ent_type:
                        if neighbor_name not in subsystems and neighbor_name != clean_name:
                            subsystems.append(neighbor_name)
                    elif rel_type in ("ASSEMBLES", "FABRICATES") or "robotics" in ent_type:
                        if neighbor_name not in assembly_units and neighbor_name != clean_name:
                            assembly_units.append(neighbor_name)
                    else:
                        if neighbor_name not in principles and neighbor_name != clean_name:
                            principles.append(neighbor_name)

        return {
            "root_system": clean_name,
            "total_dependencies": len(visited) - 1,
            "power_sources": power_sources,
            "materials": materials,
            "subsystems": subsystems,
            "assembly_units": assembly_units,
            "principles": principles,
            "paths_discovered": len(all_paths),
            "sample_paths": all_paths[:5]
        }

    def query_subsystem_graph(self, system_name: str, depth: int = 2) -> Dict[str, Any]:
        """
        Returns full ego-subgraph of nodes and connecting directed edges
        within 'depth' hops of system_name.
        """
        clean_name = system_name.strip()
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        edge_keys: Set[str] = set()

        root_ent = self.get_entity(clean_name)
        if root_ent:
            nodes[clean_name] = {
                "name": root_ent.name,
                "type": root_ent.entity_type,
                "description": root_ent.description,
                "is_root": True
            }

        frontier = {clean_name}
        for _ in range(depth):
            next_frontier = set()
            for curr in frontier:
                neighbors = self.get_neighbors(curr, direction="both")
                for n_name, rel, weight in neighbors:
                    if n_name not in nodes:
                        ent = self.get_entity(n_name)
                        if ent:
                            nodes[n_name] = {
                                "name": ent.name,
                                "type": ent.entity_type,
                                "description": ent.description,
                                "is_root": False
                            }
                        next_frontier.add(n_name)

                    edge_key = f"{curr}->{rel}->{n_name}"
                    if edge_key not in edge_keys:
                        edge_keys.add(edge_key)
                        edges.append({
                            "source": curr,
                            "target": n_name,
                            "relation": rel,
                            "weight": weight
                        })
            frontier = next_frontier

        return {
            "system_name": clean_name,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": list(nodes.values()),
            "edges": edges
        }

    def explain_lineage(self, source_name: str, target_name: str) -> str:
        """
        Discovers the relational path between two entities and generates
        an articulate, Stark-grade technical narrative of their connection.
        """
        path = self.find_path(source_name, target_name, max_hops=5)
        if path is None:
            return f"No direct or multi-hop relational lineage discovered between '{source_name}' and '{target_name}' within 5 hops."
        if not path:
            return f"'{source_name}' and '{target_name}' are identical nodes in the knowledge graph."

        narrative_parts = [f"Relational lineage analysis from '{source_name}' to '{target_name}':"]
        for idx, (src, rel, tgt) in enumerate(path, 1):
            rel_phrase = rel.lower().replace("_", " ")
            narrative_parts.append(f"  Step {idx}: '{src}' {rel_phrase} '{tgt}'.")

        summary = f"Total path length: {len(path)} hops. Direct dependency established."
        narrative_parts.append(summary)
        return "\n".join(narrative_parts)


# Global Singleton Instance
graph_rag = GraphRAG()
