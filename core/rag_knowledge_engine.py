"""
J.A.R.V.I.S. Local Knowledge Retrieval Engine & Document RAG Core.
Features:
1. 100% Offline, Zero-Cost Semantic Document Ingestion:
   - Ingests .txt, .md, .py, .json, .csv, and text logs.
   - Intelligent sliding-window paragraph chunking with contextual overlap.
2. Hash-based Incremental Indexing:
   - Tracks file SHA-256 signatures to avoid redundant re-embedding of unmodified documents.
3. Hybrid Semantic Dense + Sparse Lexical Retrieval:
   - Powered by 384-dimensional vector embeddings in SQLite vector_memory_store.
4. Grounded Synthesis & Citation:
   - Synthesizes prompt-ready answers and provides exact file names, chunk indices, and confidence metrics.
"""

import hashlib
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from core.vector_memory import vector_memory

logger = logging.getLogger("RAGKnowledgeEngine")

KNOWLEDGE_INDEX_FILE = config.DATA_DIR / "knowledge_index.json"
SUPPORTED_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv", ".log", ".yaml", ".yml"}


class DocumentChunker:
    """Splits documents into coherent overlapping chunks for semantic retrieval."""

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> List[Dict[str, Any]]:
        """Splits text into chunks respecting sentence and line boundaries."""
        if not text or not text.strip():
            return []

        # Split into paragraphs/lines first
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        chunks = []
        current_chunk = []
        current_len = 0

        for line in lines:
            line_len = len(line)
            if current_len + line_len > chunk_size and current_chunk:
                chunk_str = " ".join(current_chunk)
                chunks.append(chunk_str)
                # Keep last part for overlap
                overlap_tokens = chunk_str[-overlap:] if len(chunk_str) > overlap else chunk_str
                current_chunk = [overlap_tokens, line]
                current_len = len(overlap_tokens) + line_len
            else:
                current_chunk.append(line)
                current_len += line_len

        if current_chunk:
            chunk_str = " ".join(current_chunk)
            if chunk_str:
                chunks.append(chunk_str)

        # Structure each chunk
        results = []
        for idx, c in enumerate(chunks):
            results.append({
                "chunk_index": idx,
                "text": c.strip(),
                "char_length": len(c.strip()),
            })
        return results


class LocalRAGEngine:
    """Manages document ingestion, indexing, and grounded semantic retrieval."""

    def __init__(self):
        self.store = vector_memory
        self._ensure_storage()

    def _ensure_storage(self):
        try:
            config.DATA_DIR.mkdir(parents=True, exist_ok=True)
            if not KNOWLEDGE_INDEX_FILE.exists():
                KNOWLEDGE_INDEX_FILE.write_text("{}", encoding="utf-8")
        except Exception:
            pass

    def _load_index_metadata(self) -> Dict[str, Any]:
        try:
            if KNOWLEDGE_INDEX_FILE.exists():
                return json.loads(KNOWLEDGE_INDEX_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_index_metadata(self, meta: Dict[str, Any]):
        try:
            KNOWLEDGE_INDEX_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Error saving knowledge index metadata: {e}")

    def index_file(self, file_path: str, force: bool = False) -> Tuple[bool, str]:
        """
        Ingests and indexes a single document into the vector knowledge base.
        Skips indexing if file hash is unchanged.
        """
        p = Path(file_path).resolve()
        if not p.is_file():
            return False, f"File not found: '{file_path}'"

        if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file format '{p.suffix}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"

        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return False, f"Failed to read file: {e}"

        if not content.strip():
            return False, f"File '{p.name}' is empty."

        file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        meta = self._load_index_metadata()
        file_key = str(p)

        if not force and file_key in meta and meta[file_key].get("hash") == file_hash:
            return True, f"Document '{p.name}' is already indexed and up to date."

        # Chunk content
        chunks = DocumentChunker.chunk_text(content)
        if not chunks:
            return False, f"No extractable text chunks from '{p.name}'."

        # Store chunks in vector memory
        chunk_ids = []
        for c in chunks:
            c_meta = {
                "source_file": p.name,
                "file_path": str(p),
                "chunk_index": c["chunk_index"],
                "total_chunks": len(chunks),
                "indexed_at": time.time(),
            }
            c_content = f"Source [{p.name}]: {c['text']}"
            mem_id = self.store.store_memory(
                content=c_content,
                category="knowledge_doc",
                metadata=c_meta
            )
            chunk_ids.append(mem_id)

        meta[file_key] = {
            "name": p.name,
            "hash": file_hash,
            "chunks_count": len(chunks),
            "chunk_ids": chunk_ids,
            "size_bytes": len(content),
            "indexed_at": time.time(),
        }
        self._save_index_metadata(meta)

        return True, f"Successfully indexed '{p.name}': {len(chunks)} semantic chunks stored in neural memory."

    def index_directory(self, dir_path: str, recursive: bool = True) -> Dict[str, Any]:
        """Scans and indexes all supported files in a directory."""
        p = Path(dir_path).resolve()
        if not p.is_dir():
            return {"success": False, "error": f"Directory not found: '{dir_path}'"}

        pattern = "**/*" if recursive else "*"
        files = [f for f in p.glob(pattern) if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]

        indexed_count = 0
        skipped_count = 0
        total_chunks = 0

        for f in files:
            # Skip virtual environments and git directories
            if any(part in f.parts for part in [".git", "venv", ".venv", "__pycache__", "node_modules"]):
                continue
            ok, msg = self.index_file(str(f))
            if ok:
                if "already indexed" in msg:
                    skipped_count += 1
                else:
                    indexed_count += 1
            else:
                skipped_count += 1

        meta = self._load_index_metadata()
        for v in meta.values():
            total_chunks += v.get("chunks_count", 0)

        return {
            "success": True,
            "directory": str(p),
            "files_scanned": len(files),
            "newly_indexed": indexed_count,
            "unchanged_skipped": skipped_count,
            "total_knowledge_chunks": total_chunks,
        }

    def query_knowledge(self, query: str, top_k: int = 4, min_score: float = 0.16) -> Dict[str, Any]:
        """
        Executes dense semantic retrieval over indexed documents and synthesizes a grounded answer.
        """
        clean_q = query.strip()
        if not clean_q:
            return {"query": "", "matches": [], "synthesis": "No search query provided."}

        matches = self.store.semantic_search(
            query=clean_q,
            category="knowledge_doc",
            top_k=top_k,
            min_score=min_score
        )

        if not matches:
            return {
                "query": clean_q,
                "matches": [],
                "synthesis": f"No relevant documentation found in local knowledge base for '{clean_q}', sir.",
            }

        citations = []
        snippets = []
        for m in matches:
            meta = m.get("metadata", {})
            src = meta.get("source_file", "Document")
            score_pct = int(min(1.0, max(0.0, m["score"])) * 100)
            clean_snippet = m["content"].replace(f"Source [{src}]: ", "").strip()
            citations.append(f"{src} ({score_pct}% match)")
            snippets.append(f"• [{src}]: {clean_snippet}")

        citation_str = ", ".join(citations)
        synthesis = (
            f"Knowledge Base Retrieval for '{clean_q}':\n"
            f"Sources: {citation_str}\n\n"
            + "\n\n".join(snippets)
        )

        return {
            "query": clean_q,
            "matches": matches,
            "citations": citations,
            "synthesis": synthesis,
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns diagnostic statistics of the local RAG knowledge base."""
        meta = self._load_index_metadata()
        total_chunks = sum(v.get("chunks_count", 0) for v in meta.values())
        total_bytes = sum(v.get("size_bytes", 0) for v in meta.values())

        return {
            "indexed_documents_count": len(meta),
            "total_semantic_chunks": total_chunks,
            "total_text_volume_kb": round(total_bytes / 1024, 1),
            "documents": [v.get("name") for v in meta.values()][:10],
            "storage_status": "ONLINE",
        }

    def clear_knowledge(self) -> int:
        """Clears all indexed knowledge documents from vector store and index metadata."""
        count = self.store.clear_memories(category="knowledge_doc")
        self._save_index_metadata({})
        return count


# Global Singleton Instance
rag_knowledge_engine = LocalRAGEngine()
