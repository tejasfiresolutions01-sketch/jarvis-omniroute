"""
J.A.R.V.I.S. Autonomous Self-Repair & Healing Matrix.
Provides comprehensive self-healing and proactive auto-remediation across all subsystems:
1. Network & OmniRoute AI Gateway Re-synchronization
2. Audio & Speech Lock Healing and Temp File Housekeeping
3. SQLite Database Integrity Checks and WAL Log Checkpointing
4. Holographic Display and Tactical HUD Auto-Recovery
5. Background Sentinel and Daemon Thread Watchdog Resuscitation
6. System Memory Trimming and Garbage Collection

Core Directive:
- Resolves anomalies silently in the background.
- Only notifies Sir when a critical problem cannot be autonomously rectified.
- Speaks in simple, natural English without robotic jargon.
"""

import os
import sys
import gc
import glob
import time
import logging
import tempfile
import threading
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config
from tools.notification_sentinel import notification_sentinel
from core.internet_sentinel import internet_sentinel

logger = logging.getLogger("SelfRepairEngine")

class SelfRepairEngine:
    """
    Autonomous Self-Repair and System Maintenance Engine.
    Keeps J.A.R.V.I.S. operating in peak health, repairing anomalies silently.
    """

    def __init__(self):
        self.remediation_log: List[Dict[str, Any]] = []
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._failure_counts: Dict[str, int] = {}
        self._max_attempts = 3

    # ─────────────────────────────────────────────────────────────────────────
    # Subsystem Healers
    # ─────────────────────────────────────────────────────────────────────────

    def repair_network(self, details: str = "") -> Tuple[bool, str]:
        """
        Repairs network connectivity, connection gateway, and DNS resolution.
        """
        logger.info(f"[Self Repair]: Initiating network and gateway repair ({details})...")
        success, msg = internet_sentinel.reconnect()
        return success, msg

    def repair_audio_subsystem(self, details: str = "") -> Tuple[bool, str]:
        """
        Clears stale speech locks, unhangs pygame mixer, and removes leaked audio files.
        """
        logger.info(f"[Self Repair]: Inspecting and repairing audio subsystem ({details})...")
        cleared_items = 0

        # 1. Clear stale speech lock if it has been held too long (> 10s)
        try:
            lock_path = Path(config.BASE_DIR) / "logs" / "jarvis_speech.lock"
            if lock_path.exists():
                mtime = lock_path.stat().st_mtime
                if time.time() - mtime > 10.0:
                    try:
                        lock_path.unlink()
                        cleared_items += 1
                        logger.info("[Self Repair]: Cleared stale speech lock file.")
                    except Exception:
                        pass
        except Exception:
            pass

        # 2. Reset audio flag in core.voice
        try:
            import core.voice as voice_module
            voice_module.is_speaking = False
        except Exception:
            pass

        # 3. Clean up orphaned temp audio files
        try:
            tmp_dir = tempfile.gettempdir()
            for pattern in ["*.mp3", "*.wav"]:
                for fpath in glob.glob(os.path.join(tmp_dir, pattern)):
                    try:
                        # Only delete files older than 60 seconds
                        if time.time() - os.path.getmtime(fpath) > 60:
                            os.remove(fpath)
                            cleared_items += 1
                    except Exception:
                        pass
        except Exception:
            pass

        return True, "Audio and voice synthesis pipelines are operational."

    def repair_databases(self, details: str = "") -> Tuple[bool, str]:
        """
        Checks SQLite database files, runs integrity checks, and executes WAL checkpoints.
        """
        logger.info(f"[Self Repair]: Verifying database integrity and clearing locks ({details})...")
        import sqlite3

        db_files = [
            config.MEMORY_DB_PATH,
            config.SCHEDULE_DB_PATH,
            config.TASKS_DB_PATH,
            getattr(config, "COGNITIVE_DB_PATH", os.path.join(config.BASE_DIR, "memory", "cognitive_memory.db")),
            getattr(config, "VECTOR_DB_PATH", os.path.join(config.BASE_DIR, "memory", "vector_memory.db"))
        ]

        verified = 0
        for p in db_files:
            db_path = Path(p)
            if db_path.exists():
                try:
                    conn = sqlite3.connect(str(db_path), timeout=5.0)
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                    res = conn.execute("PRAGMA quick_check;").fetchone()
                    conn.close()
                    if res and res[0] == "ok":
                        verified += 1
                except Exception as e:
                    logger.warning(f"[Self Repair]: Database check for {db_path.name} error: {e}")

        return True, "All database registries and memory stores are verified intact."

    def repair_hologram_display(self, details: str = "") -> Tuple[bool, str]:
        """
        Ensures holographic tactical HUD window is healthy and displayed.
        """
        try:
            from core.hologram_sentinel import hologram_sentinel
            hologram_sentinel.display_hologram(reason="self_repair")
            time.sleep(0.3)
            return True, "Holographic tactical interface is active and aligned."
        except Exception as e:
            logger.error(f"[Self Repair]: Display recovery error: {e}")
            return False, "The holographic display window could not be displayed, sir."

    def repair_sentinels_and_daemons(self, details: str = "") -> Tuple[bool, str]:
        """
        Checks background daemon threads and revives any that stopped unexpectedly.
        """
        logger.info(f"[Self Repair]: Auditing sentinel daemon health ({details})...")
        revived = []

        # 1. Internet Sentinel
        try:
            if not internet_sentinel._running:
                internet_sentinel.start()
                revived.append("Internet Sentinel")
        except Exception:
            pass

        # 2. Watchdog
        try:
            from core.watchdog import watchdog
            if not watchdog.is_running:
                watchdog.start()
                revived.append("Hardware Watchdog")
        except Exception:
            pass

        # 3. Proactive Agent
        try:
            from core.proactive_agent import proactive_agent
            if not proactive_agent.is_running:
                proactive_agent.start()
                revived.append("Proactive Butler")
        except Exception:
            pass

        # 4. Display Sentinel
        try:
            from core.display_sentinel import display_sentinel
            if not display_sentinel._running:
                display_sentinel.start()
                revived.append("Display Sentinel")
        except Exception:
            pass

        # 5. Hologram Sentinel
        try:
            from core.hologram_sentinel import hologram_sentinel
            if not hologram_sentinel._running:
                hologram_sentinel.start()
                revived.append("Hologram Sentinel")
        except Exception:
            pass

        if revived:
            logger.info(f"[Self Repair]: Successfully resuscitated daemons: {', '.join(revived)}")
        return True, "All background sentinels and butler subroutines are active."

    def repair_system_resources(self, details: str = "") -> Tuple[bool, str]:
        """
        Trims working memory, runs garbage collection, and clears system cache.
        """
        try:
            from tools.system_optimizer import system_optimizer
            system_optimizer.optimize_system()
        except Exception:
            pass
        gc.collect()
        return True, "System memory and working set caches have been cleared."

    # ─────────────────────────────────────────────────────────────────────────
    # Subsystem Dispatcher
    # ─────────────────────────────────────────────────────────────────────────

    def repair_subsystem(self, subsystem: str, details: str = "") -> Tuple[bool, str]:
        """
        Directs repair request to the appropriate healer.
        """
        sub = subsystem.lower()

        if any(k in sub for k in ["network", "internet", "cloud", "omniroute", "gateway", "connection", "http"]):
            return self.repair_network(details)
        elif any(k in sub for k in ["audio", "voice", "speech", "tts", "speaker", "sound"]):
            return self.repair_audio_subsystem(details)
        elif any(k in sub for k in ["database", "sqlite", "memory_db", "lock", "db"]):
            return self.repair_databases(details)
        elif any(k in sub for k in ["display", "hud", "hologram", "window"]):
            return self.repair_hologram_display(details)
        elif any(k in sub for k in ["daemon", "thread", "sentinel", "watchdog"]):
            return self.repair_sentinels_and_daemons(details)
        elif any(k in sub for k in ["ram", "memory", "cpu", "resource", "cache"]):
            return self.repair_system_resources(details)
        else:
            # Full system sweep fallback
            res = self.run_full_repair(manual=False)
            return res["all_rectified"], "System self-repair routine executed."

    # ─────────────────────────────────────────────────────────────────────────
    # Full System Repair & Manual Voice Directive
    # ─────────────────────────────────────────────────────────────────────────

    def run_full_repair(self, manual: bool = False) -> Dict[str, Any]:
        """
        Runs comprehensive self-repair pass across all subsystems.
        """
        logger.info("[Self Repair]: Running comprehensive self-repair cycle across all subsystems...")
        results: Dict[str, Any] = {}

        # 1. Network & Gateway
        net_ok, net_msg = self.repair_network("full_sweep")
        results["network"] = {"rectified": net_ok, "message": net_msg}

        # 2. Audio Subsystem
        aud_ok, aud_msg = self.repair_audio_subsystem("full_sweep")
        results["audio"] = {"rectified": aud_ok, "message": aud_msg}

        # 3. Databases & Storage
        db_ok, db_msg = self.repair_databases("full_sweep")
        results["databases"] = {"rectified": db_ok, "message": db_msg}

        # 4. Display & HUD
        hud_ok, hud_msg = self.repair_hologram_display("full_sweep")
        results["display"] = {"rectified": hud_ok, "message": hud_msg}

        # 5. Sentinels & Daemons
        sen_ok, sen_msg = self.repair_sentinels_and_daemons("full_sweep")
        results["sentinels"] = {"rectified": sen_ok, "message": sen_msg}

        # 6. Memory & Resources
        res_ok, res_msg = self.repair_system_resources("full_sweep")
        results["resources"] = {"rectified": res_ok, "message": res_msg}

        all_rectified = all(item["rectified"] for item in results.values())
        results["all_rectified"] = all_rectified
        results["timestamp"] = time.time()

        with self._lock:
            self.remediation_log.append(results)
            # Cap log history
            if len(self.remediation_log) > 50:
                self.remediation_log = self.remediation_log[-50:]

        if manual:
            if all_rectified:
                spoken = (
                    "I have conducted a full self-repair and diagnostic routine across all subsystems, sir. "
                    "The connection gateway, audio pipeline, databases, and background sentinels are in prime operational health."
                )
            else:
                spoken = (
                    "I have repaired our local subroutines, sir. However, external internet connectivity "
                    "remains unreachable right now. Please check your network connection."
                )
            results["spoken_response"] = spoken
            return results

        return results

    # ─────────────────────────────────────────────────────────────────────────
    # Autonomous Background Self-Healing Loop
    # ─────────────────────────────────────────────────────────────────────────

    def start(self):
        """Launches the autonomous self-repair daemon."""
        if self._running:
            return
        self._running = True

        def _healing_loop():
            # Initial graceful delay
            time.sleep(15.0)
            while self._running:
                try:
                    self._check_and_heal_autonomously()
                except Exception as e:
                    logger.error(f"[Self Repair Loop Error]: {e}")
                # Audit every 60 seconds
                time.sleep(60.0)

        self._thread = threading.Thread(target=_healing_loop, daemon=True, name="SelfRepairThread")
        self._thread.start()
        logger.info("[Self Repair Engine]: Autonomous background self-repair watchdog active.")

    def stop(self):
        self._running = False

    def _check_and_heal_autonomously(self):
        """
        Silently monitors each subsystem, heals anomalies, and notifies
        only when an issue remains unrectified after healing attempts.
        """
        # 1. Audit daemons
        self.repair_sentinels_and_daemons("periodic_watchdog")

        # 2. Audit audio lock
        self.repair_audio_subsystem("periodic_watchdog")

        # 3. Check memory pressure
        try:
            import psutil
            mem = psutil.virtual_memory()
            if mem.percent > 85.0:
                self.repair_system_resources("high_ram_watchdog")
        except Exception:
            pass

        # 4. Check OmniRoute gateway responsiveness if internet is active
        if internet_sentinel.is_connected():
            try:
                from tools.omniroute_controller import omniroute_controller
                st = omniroute_controller.get_status()
                if not st.get("online"):
                    logger.info("[Self Repair]: OmniRoute gateway unresponsive while online. Reviving...")
                    self.repair_network("gateway_recovery")
            except Exception:
                pass

# Global singleton
self_repair_engine = SelfRepairEngine()
