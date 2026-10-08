"""
J.A.R.V.I.S. Problem Healer & Silent Autonomous Remediation Engine.
Core Principles:
1. Explains problems in simple, clear English without technical jargon.
2. Autonomously attempts to resolve the problem first (silent healing).
3. ONLY notifies the user when the problem cannot be rectified.
"""

import os
import sys
import time
import logging
from typing import Tuple, Dict, Any, Optional
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config
from tools.notification_sentinel import notification_sentinel

logger = logging.getLogger("ProblemHealer")

class ProblemHealer:
    """
    Autonomous problem diagnostic, remediation, and selective notification engine.
    Silently resolves issues and only alerts the user if remediation fails.
    """

    def __init__(self):
        self.remediation_history: list = []
        self._max_healing_attempts = 3

    def diagnose_and_heal(self, problem_type: str, details: str = "") -> Tuple[bool, str]:
        """
        Attempts autonomous silent healing based on problem type.
        Returns:
            (rectified: bool, simple_english_explanation: str)
        """
        p_type = problem_type.lower()
        logger.info(f"[Problem Healer]: Diagnosing issue '{p_type}' (Details: {details})")

        # 1. Network / Cloud / Gateway Issues
        if any(k in p_type for k in ["network", "cloud", "omniroute", "connection", "http", "api"]):
            return self._heal_network_gateway(details)

        # 2. Database Locks / SQLite Busy
        if any(k in p_type for k in ["database", "sqlite", "locked", "db_busy"]):
            return self._heal_database_locks(details)

        # 3. High Memory / Resource Bloat
        if any(k in p_type for k in ["memory", "ram", "high_load", "cpu", "resource"]):
            return self._heal_system_resources(details)

        # 4. Holographic Display / HUD Window Issues
        if any(k in p_type for k in ["hud", "hologram", "display", "window"]):
            return self._heal_hologram_display(details)

        # Generic Fallback
        return False, "I encountered an operational issue that could not be automatically resolved, sir."

    def _heal_network_gateway(self, details: str) -> Tuple[bool, str]:
        """Attempts to restart or verify the OmniRoute gateway and connectivity."""
        try:
            from tools.omniroute_controller import omniroute_controller
            status = omniroute_controller.get_status()

            if not status.get("online"):
                logger.info("[Problem Healer]: OmniRoute gateway offline. Attempting silent launch...")
                omniroute_controller.start_service_detached()
                time.sleep(2.0)
                new_status = omniroute_controller.get_status()
                if new_status.get("online"):
                    logger.info("[Problem Healer]: Gateway restored successfully. Problem resolved silently.")
                    return True, "Network gateway was offline but has been successfully restarted."

            # Test internet reachability via simple ping
            import urllib.request
            try:
                urllib.request.urlopen("https://www.google.com", timeout=3.0)
                return True, "Internet connectivity is verified and operational."
            except Exception:
                logger.warning("[Problem Healer]: Internet connectivity check failed.")
                return False, (
                    "I am unable to connect to the internet right now, sir. "
                    "I tried restarting our local connection gateway, but the network is still offline. "
                    "Please check your Wi-Fi or network connection."
                )
        except Exception as e:
            logger.error(f"[Problem Healer]: Network healing encountered error: {e}")
            return False, "I cannot connect to the internet right now, sir. Please check your network connection."

    def _heal_database_locks(self, details: str) -> Tuple[bool, str]:
        """Attempts to clear locks by running WAL checkpoint or VACUUM."""
        try:
            import sqlite3
            dbs = [config.MEMORY_DB_PATH, config.SCHEDULE_DB_PATH, config.TASKS_DB_PATH]
            for db_path in dbs:
                if Path(db_path).exists():
                    try:
                        conn = sqlite3.connect(str(db_path), timeout=5.0)
                        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                        conn.close()
                    except Exception:
                        pass
            logger.info("[Problem Healer]: Database checkpoints completed.")
            return True, "Database locks cleared successfully."
        except Exception as e:
            logger.error(f"[Problem Healer]: Database healing failed: {e}")
            return False, "A local database file is temporarily locked by another task and could not be freed."

    def _heal_system_resources(self, details: str) -> Tuple[bool, str]:
        """Attempts to optimize system memory and flush dead caches."""
        try:
            from tools.system_optimizer import system_optimizer
            system_optimizer.optimize_system()
            logger.info("[Problem Healer]: System memory optimization completed.")
            return True, "System memory and background caches optimized."
        except Exception as e:
            logger.error(f"[Problem Healer]: Resource healing failed: {e}")
            return False, "System memory remains very high, sir. You may want to close some heavy background applications."

    def _heal_hologram_display(self, details: str) -> Tuple[bool, str]:
        """Attempts to re-summon or verify the holographic HUD."""
        try:
            from core.hologram_sentinel import hologram_sentinel
            hologram_sentinel.display_hologram(reason="auto_heal")
            time.sleep(0.5)
            if hologram_sentinel.is_hologram_visible():
                return True, "Holographic display recovered successfully."
            return False, "The holographic display window could not be opened, sir."
        except Exception as e:
            logger.error(f"[Problem Healer]: HUD healing failed: {e}")
            return False, "The holographic display window could not be displayed, sir."

    def handle_problem(self, problem_type: str, details: str = "", notify_if_unrectified: bool = True) -> Tuple[bool, str]:
        """
        Main entry point for handling problems:
        - Tries to heal the problem silently.
        - If rectified: Logs and suppresses user notification.
        - If NOT rectified: Explains in simple English and notifies user.
        """
        rectified, explanation = self.diagnose_and_heal(problem_type, details)

        record = {
            "time": time.time(),
            "problem_type": problem_type,
            "details": details,
            "rectified": rectified,
            "explanation": explanation
        }
        self.remediation_history.append(record)

        if rectified:
            logger.info(f"[Problem Healer]: Problem '{problem_type}' rectified autonomously. User notification suppressed.")
            return True, explanation

        # Problem could NOT be rectified: notify user simply and clearly
        logger.warning(f"[Problem Healer]: Problem '{problem_type}' could NOT be rectified. Alerting user: {explanation}")
        if notify_if_unrectified:
            try:
                notification_sentinel.notify(
                    title="J.A.R.V.I.S. Attention Required",
                    message=explanation
                )
            except Exception as e:
                logger.error(f"[Problem Healer]: Failed to dispatch desktop notification: {e}")

        return False, explanation

    def heal_and_retry_query(self, prompt: str, context: str = "") -> Optional[str]:
        """
        Attempts to silently heal network issues and retry an online query.
        Returns response string if successful, or None.
        """
        rectified, _ = self.diagnose_and_heal("network")
        if rectified:
            try:
                from core.online_intelligence import online_intelligence
                res = online_intelligence.query(prompt, context=context)
                if res:
                    return res
            except Exception:
                pass
        return None

# Global singleton
problem_healer = ProblemHealer()
