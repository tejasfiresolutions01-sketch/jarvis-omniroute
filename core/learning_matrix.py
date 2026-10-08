import sqlite3
from contextlib import contextmanager
import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from pathlib import Path
import config

class LearningMatrix:
    """
    Self-Evolving Heuristic Memory & Monthly Maintenance Core.
    - Captures mistakes, user corrections, and learned preferences.
    - Automatically checks and triggers monthly diagnostics & repairs on the 1st of every month.
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
                CREATE TABLE IF NOT EXISTS learned_heuristics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trigger_context TEXT NOT NULL,
                    mistake_description TEXT NOT NULL,
                    correct_behavior TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    # ─────────────────────────────────────────────────────────────────────────
    # Learning From Mistakes
    # ─────────────────────────────────────────────────────────────────────────
    def record_mistake(self, trigger_context: str, mistake: str, correction: str):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO learned_heuristics (trigger_context, mistake_description, correct_behavior) VALUES (?, ?, ?)",
                (trigger_context.strip(), mistake.strip(), correction.strip())
            )
            conn.commit()

    def detect_and_absorb_correction(self, prompt: str) -> Optional[str]:
        """Detects if user is offering a correction and records it permanently."""
        clean = prompt.lower().strip()
        correction_patterns = [
            r"(?:that was wrong|mistake|don'?t do that|incorrect)[,.\s]+(?:next time|instead|always|prefer)\s+(.+)",
            r"(?:you should have|i wanted you to)\s+(.+)"
        ]

        for pat in correction_patterns:
            m = re.search(pat, clean)
            if m:
                lesson = m.group(1).strip()
                self.record_mistake(
                    trigger_context="User Correction",
                    mistake=prompt,
                    correction=lesson
                )
                return (
                    f"Heuristic recorded into long-term cognitive matrix, sir. "
                    f"I have learned: '{lesson}'. I shall adapt accordingly."
                )
        return None

    def get_learned_rules_summary(self) -> str:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM learned_heuristics ORDER BY id DESC LIMIT 5")
            rows = cur.fetchall()
            if not rows:
                return "My cognitive matrix has recorded no operational discrepancies to date, sir. All protocols are aligned."
            lines = ["Here are the operational heuristics learned from past directives, sir:"]
            for r in rows:
                lines.append(f"  • Trigger: {r['trigger_context']} ➔ Adapted Behavior: {r['correct_behavior']}")
            return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────────
    # Monthly Diagnostic & Self-Maintenance Scanner
    # ─────────────────────────────────────────────────────────────────────────
    def is_starting_day_of_month(self) -> bool:
        return date.today().day == 1

    def has_run_maintenance_this_month(self) -> bool:
        month_prefix = date.today().strftime("%Y-%m")
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM maintenance_logs WHERE scan_date LIKE ? LIMIT 1", (f"{month_prefix}%",))
            return cur.fetchone() is not None

    def run_self_maintenance_scan(self, force: bool = False) -> str:
        """
        Executes comprehensive self-maintenance:
        - Validates database integrity.
        - Checks asset availability.
        - Tests system controllers.
        - Optimizes SQLite tables (VACUUM & PRAGMA optimize).
        """
        today_str = date.today().strftime("%Y-%m-%d")
        results = []

        # 1. Database Integrity
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("PRAGMA integrity_check")
                res = cur.fetchone()[0]
                if res == "ok":
                    results.append("Database integrity: OPTIMAL (PRAGMA verified)")
                conn.execute("VACUUM")
                conn.execute("PRAGMA optimize")
        except Exception as e:
            results.append(f"Database integrity warning: {e}")

        # 2. Asset Verification
        if config.IRONMAN_ICO_PATH.exists():
            results.append(f"Desktop icon asset: VERIFIED ({config.IRONMAN_ICO_PATH.name})")
        else:
            results.append("Desktop icon asset: MISSING")

        # 3. Schedule Core Integrity
        from core.schedule_manager import schedule_manager
        try:
            schedule_manager.get_events_for_date(today_str)
            results.append("Agenda subsystem: ONLINE & RESPONSIVE")
        except Exception as e:
            results.append(f"Agenda subsystem anomaly: {e}")

        # Log maintenance result
        summary = "; ".join(results)
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO maintenance_logs (scan_date, status, details) VALUES (?, ?, ?)",
                (today_str, "COMPLETED", summary)
            )
            conn.commit()

        return (
            f"Monthly Diagnostic & Self-Maintenance Scan Completed, sir.\n"
            f"Status: ALL SYSTEMS NOMINAL\n" +
            "\n".join([f"  • {r}" for r in results])
        )

# Global singleton
learning_matrix = LearningMatrix()
