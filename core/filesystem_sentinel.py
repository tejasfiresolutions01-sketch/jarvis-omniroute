"""
J.A.R.V.I.S. Event-Driven Filesystem Sentinel & Document Ingestion Core.
Features:
1. Continuous non-blocking directory watcher for inbound technical and commercial files.
2. File category classifier (CAD schematics, commercial invoices, CSV datasets, source code).
3. SHA-256 fingerprint deduplication preventing redundant processing.
4. Event callback dispatch pipeline wiring directly into RPA workflows and GraphRAG.
5. 100% Free, local standard library implementation with zero cloud overhead.
Strictly in English.
"""

import os
import sys
import time
import hashlib
import logging
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Set

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config

logger = logging.getLogger("FilesystemSentinel")

FILE_CATEGORY_MAP = {
    "pdf": "DOCUMENT_PDF",
    "csv": "DATA_TABULAR",
    "xlsx": "DATA_SPREADSHEET",
    "xls": "DATA_SPREADSHEET",
    "json": "DATA_STRUCTURED",
    "dxf": "CAD_BLUEPRINT",
    "dwg": "CAD_BLUEPRINT",
    "stl": "CAD_3D_MESH",
    "obj": "CAD_3D_MESH",
    "step": "CAD_SOLID_MODEL",
    "py": "SOURCE_CODE",
    "rs": "SOURCE_CODE",
    "cpp": "SOURCE_CODE",
    "sql": "DATABASE_SCRIPT",
    "png": "IMAGE_VISUAL",
    "jpg": "IMAGE_VISUAL",
    "jpeg": "IMAGE_VISUAL"
}


class FilesystemSentinel:
    """
    Background file observer tracking file events and triggering downstream automation.
    """

    def __init__(self, watch_dirs: Optional[List[Path]] = None, poll_interval_sec: float = 2.0):
        self.poll_interval = poll_interval_sec
        self.watch_dirs: List[Path] = []
        default_dir = config.BASE_DIR / "data" / "inbox"
        default_dir.mkdir(parents=True, exist_ok=True)
        self.add_watch_dir(default_dir)

        if watch_dirs:
            for d in watch_dirs:
                self.add_watch_dir(d)

        self._known_file_hashes: Dict[str, str] = {}
        self._handlers: List[Callable[[Dict[str, Any]], None]] = []
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def add_watch_dir(self, directory: Path):
        """Adds a directory to the observation list."""
        directory.mkdir(parents=True, exist_ok=True)
        if directory not in self.watch_dirs:
            self.watch_dirs.append(directory)
            logger.info(f"Filesystem Sentinel watching: {directory}")

    def register_handler(self, callback: Callable[[Dict[str, Any]], None]):
        """Registers a callback to receive file ingestion events."""
        with self._lock:
            if callback not in self._handlers:
                self._handlers.append(callback)

    def classify_file(self, file_path: Path) -> str:
        """Determines the semantic category of a file by extension."""
        ext = file_path.suffix.lower().lstrip(".")
        return FILE_CATEGORY_MAP.get(ext, "UNKNOWN_BINARY")

    def compute_sha256(self, file_path: Path) -> str:
        """Calculates file checksum for deduplication."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    def scan_once(self) -> List[Dict[str, Any]]:
        """Performs a synchronous scan across all watched folders."""
        new_events: List[Dict[str, Any]] = []

        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                continue

            for root, _, files in os.walk(watch_dir):
                for filename in files:
                    file_path = Path(root) / filename
                    file_str = str(file_path)
                    try:
                        file_hash = self.compute_sha256(file_path)
                        if not file_hash:
                            continue

                        with self._lock:
                            prev_hash = self._known_file_hashes.get(file_str)
                            if prev_hash is None:
                                # New File Detected
                                self._known_file_hashes[file_str] = file_hash
                                category = self.classify_file(file_path)
                                event = {
                                    "event_type": "FILE_CREATED",
                                    "path": file_str,
                                    "filename": filename,
                                    "category": category,
                                    "hash": file_hash,
                                    "size_bytes": file_path.stat().st_size,
                                    "timestamp": time.time()
                                }
                                new_events.append(event)
                            elif prev_hash != file_hash:
                                # File Modified
                                self._known_file_hashes[file_str] = file_hash
                                category = self.classify_file(file_path)
                                event = {
                                    "event_type": "FILE_MODIFIED",
                                    "path": file_str,
                                    "filename": filename,
                                    "category": category,
                                    "hash": file_hash,
                                    "size_bytes": file_path.stat().st_size,
                                    "timestamp": time.time()
                                }
                                new_events.append(event)
                    except Exception as e:
                        logger.debug(f"Error inspecting {file_path}: {e}")

        # Dispatch events to registered handlers
        if new_events:
            with self._lock:
                for event in new_events:
                    for handler in self._handlers:
                        try:
                            handler(event)
                        except Exception as e:
                            logger.error(f"Handler failed on event {event.get('filename')}: {e}")

        return new_events

    def start_sentinel(self):
        """Starts background monitoring thread."""
        if self._is_running:
            return
        self._is_running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="FilesystemSentinelWorker")
        self._thread.start()
        logger.info("Filesystem Sentinel monitoring loop started.")

    def stop_sentinel(self):
        """Halts background monitoring."""
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        logger.info("Filesystem Sentinel monitoring loop stopped.")

    def _monitor_loop(self):
        while self._is_running:
            try:
                self.scan_once()
            except Exception as e:
                logger.error(f"Error in Filesystem Sentinel scan loop: {e}")
            time.sleep(self.poll_interval)


# Global Singleton
filesystem_sentinel = FilesystemSentinel()
