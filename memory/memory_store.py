import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import config

class MemoryStore:
    """
    Episodic Memory Core.
    Maintains persistent record of user interactions, butler actions, and tool invocations.
    """

    def __init__(self, db_path: Path = config.MEMORY_DB_PATH):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS function_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    arguments TEXT,
                    status TEXT DEFAULT 'SUCCESS',
                    result_summary TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def log_interaction(self, sender: str, message: str):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO interactions (sender, message) VALUES (?, ?)",
                (sender, message)
            )
            conn.commit()

    def log_function_call(self, tool_name: str, arguments: str = "", status: str = "SUCCESS", result_summary: str = ""):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO function_calls (tool_name, arguments, status, result_summary) VALUES (?, ?, ?, ?)",
                (tool_name, arguments, status, result_summary)
            )
            conn.commit()

    def get_recent_interactions(self, limit: int = 5) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT sender, message, timestamp FROM interactions ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            rows = cur.fetchall()
            return [dict(r) for r in reversed(rows)]

    def recall_last_function(self) -> str:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM function_calls ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            if not row:
                return "No previous actions have been logged in this session, sir."
            return f"The last action executed was `{row['tool_name']}` with parameters: {row['arguments']} (Status: {row['status']}), sir."

# Global singleton
memory = MemoryStore()
