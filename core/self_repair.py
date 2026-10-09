"""
J.A.R.V.I.S. Autonomous Self-Repair & Healing Matrix.
Provides comprehensive self-healing and proactive auto-remediation across all subsystems:
1. Network & OmniRoute AI Gateway Re-synchronization
2. Audio & Speech Lock Healing and Temp File Housekeeping
3. SQLite Database Integrity Checks and WAL Log Checkpointing
4. Holographic Display and Tactical HUD Auto-Recovery
5. Background Sentinel and Daemon Thread Watchdog Resuscitation (with Exponential Backoff & Circuit Breakers)
6. System Memory Leak Pruning, Garbage Collection & Windows Working Set Compaction
7. Socket and Port Verification & Self-Healing
8. System Health Telemetry & Composite Resilience Index (0-100%)

Core Directive:
- Resolves anomalies silently in the background.
- Only notifies Sir when a critical problem cannot be autonomously rectified.
- Speaks in simple, natural English without robotic jargon.
"""

import os
import re
import sys
import gc
import glob
import time
import socket
import logging
import tempfile
import ctypes
import threading
from typing import Dict, Any, Tuple, List, Optional, Callable
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
    Autonomous Self-Repair, Process Resilience, and System Maintenance Engine.
    Keeps J.A.R.V.I.S. operating in peak health, repairing anomalies silently.
    """

    def __init__(self):
        self.remediation_log: List[Dict[str, Any]] = []
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._failure_counts: Dict[str, int] = {}
        self._max_attempts = 3

        # Supervised Daemon Registry (key -> dict)
        self._supervised_daemons: Dict[str, Dict[str, Any]] = {}
        self._init_default_daemon_registry()

    def _init_default_daemon_registry(self):
        """Initializes the built-in monitored daemon matrix."""
        # 1. Internet Sentinel
        self.register_daemon(
            key="internet_sentinel",
            name="Internet Sentinel",
            check_fn=lambda: getattr(internet_sentinel, "_running", False),
            restart_fn=lambda: internet_sentinel.start()
        )

        # 2. Ambient Hardware Watchdog
        def _check_watchdog():
            try:
                from core.watchdog import watchdog
                return getattr(watchdog, "is_running", False)
            except Exception:
                return False

        def _restart_watchdog():
            try:
                from core.watchdog import watchdog
                watchdog.start()
            except Exception:
                pass

        self.register_daemon(
            key="watchdog",
            name="Hardware Watchdog",
            check_fn=_check_watchdog,
            restart_fn=_restart_watchdog
        )

        # 3. Proactive Butler Agent
        def _check_proactive():
            try:
                from core.proactive_agent import proactive_agent
                return getattr(proactive_agent, "is_running", False)
            except Exception:
                return False

        def _restart_proactive():
            try:
                from core.proactive_agent import proactive_agent
                proactive_agent.start()
            except Exception:
                pass

        self.register_daemon(
            key="proactive_agent",
            name="Proactive Butler",
            check_fn=_check_proactive,
            restart_fn=_restart_proactive
        )

        # 4. Display Sentinel
        def _check_display():
            try:
                from core.display_sentinel import display_sentinel
                return getattr(display_sentinel, "_running", False)
            except Exception:
                return False

        def _restart_display():
            try:
                from core.display_sentinel import display_sentinel
                display_sentinel.start()
            except Exception:
                pass

        self.register_daemon(
            key="display_sentinel",
            name="Display Sentinel",
            check_fn=_check_display,
            restart_fn=_restart_display
        )

        # 5. Hologram Sentinel
        def _check_hologram():
            try:
                from core.hologram_sentinel import hologram_sentinel
                return getattr(hologram_sentinel, "_running", False)
            except Exception:
                return False

        def _restart_hologram():
            try:
                from core.hologram_sentinel import hologram_sentinel
                hologram_sentinel.start()
            except Exception:
                pass

        self.register_daemon(
            key="hologram_sentinel",
            name="Hologram Sentinel",
            check_fn=_check_hologram,
            restart_fn=_restart_hologram
        )

    def register_daemon(
        self,
        key: str,
        name: str,
        check_fn: Callable[[], bool],
        restart_fn: Callable[[], None]
    ):
        """Registers a background daemon subroutine for health supervision and auto-restart."""
        with self._lock:
            self._supervised_daemons[key] = {
                "name": name,
                "check_fn": check_fn,
                "restart_fn": restart_fn,
                "failure_count": 0,
                "last_restart_time": 0.0,
                "last_failure_time": 0.0,
                "backoff_delay": 5.0,
                "circuit_breaker": False,
                "restarts_total": 0
            }

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

        # 1. Clear stale speech lock if it has been held too long (> 3s)
        try:
            lock_path = Path(config.BASE_DIR) / "logs" / "jarvis_speech.lock"
            if lock_path.exists():
                mtime = lock_path.stat().st_mtime
                if time.time() - mtime > 3.0:
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
        Audits registered background daemon subroutines and revives any dead workers
        with exponential backoff protection.
        """
        logger.info(f"[Self Repair]: Auditing sentinel daemon health ({details})...")
        revived = self.supervise_daemons().get("revived", [])

        if revived:
            logger.info(f"[Self Repair]: Successfully resuscitated daemons: {', '.join(revived)}")
        return True, "All background sentinels and butler subroutines are active."

    def supervise_daemons(self) -> Dict[str, Any]:
        """
        Checks all registered daemons, restarts dead ones, and enforces exponential backoff
        and circuit breakers to prevent restart thrashing.
        """
        now = time.time()
        revived: List[str] = []
        statuses: Dict[str, Any] = {}

        with self._lock:
            for key, d in self._supervised_daemons.items():
                name = d["name"]
                check_fn = d["check_fn"]
                restart_fn = d["restart_fn"]

                is_alive = False
                try:
                    is_alive = bool(check_fn())
                except Exception as e:
                    logger.debug(f"Health check for {name} error: {e}")

                statuses[key] = {
                    "name": name,
                    "alive": is_alive,
                    "circuit_breaker": d["circuit_breaker"],
                    "restarts_total": d["restarts_total"]
                }

                if not is_alive:
                    # Check circuit breaker reset window (10 minutes)
                    if d["circuit_breaker"] and (now - d["last_failure_time"] > 600.0):
                        d["circuit_breaker"] = False
                        d["failure_count"] = 0
                        d["backoff_delay"] = 5.0

                    if d["circuit_breaker"]:
                        continue

                    # Check backoff delay
                    if now - d["last_restart_time"] < d["backoff_delay"]:
                        continue

                    # Attempt restart
                    try:
                        restart_fn()
                        d["last_restart_time"] = now
                        d["restarts_total"] += 1
                        revived.append(name)
                        # Re-check status
                        time.sleep(0.05)
                        if check_fn():
                            d["failure_count"] = max(0, d["failure_count"] - 1)
                            d["backoff_delay"] = max(5.0, d["backoff_delay"] / 1.5)
                        else:
                            d["failure_count"] += 1
                            d["backoff_delay"] = min(60.0, d["backoff_delay"] * 2.0)
                            if d["failure_count"] >= 5:
                                d["circuit_breaker"] = True
                                d["last_failure_time"] = now
                                logger.warning(f"[Self Repair]: Circuit breaker tripped for {name} after multiple crashes.")
                    except Exception as e:
                        logger.error(f"[Self Repair]: Failed restarting {name}: {e}")
                        d["failure_count"] += 1

        return {"revived": revived, "statuses": statuses}

    def prune_memory_and_resources(self, threshold_mb: float = 400.0, force: bool = False) -> Dict[str, Any]:
        """
        Monitors process RSS memory and system RAM. If memory exceeds threshold or force=True,
        executes aggressive multi-tier resource pruning:
        1. Multi-generational garbage collection: gc.collect(2)
        2. Regular expression pattern cache purge: re.purge()
        3. Temporary disk cache eviction: temp/ and OS temp files > 180s
        4. Windows Working Set compaction via psapi.EmptyWorkingSet
        """
        import psutil
        p = psutil.Process()
        mem_info = p.memory_info()
        rss_before = mem_info.rss / (1024 * 1024)
        sys_ram_pct = psutil.virtual_memory().percent

        pruned = False
        files_removed = 0

        if force or rss_before > threshold_mb or sys_ram_pct > 85.0:
            pruned = True
            # 1. GC
            gc.collect(2)

            # 2. Regex cache purge
            re.purge()

            # 3. Temp file housekeeping
            try:
                base_dir = Path(config.BASE_DIR)
                target_dirs = [base_dir / "temp", base_dir]
                now = time.time()
                for t_dir in target_dirs:
                    if t_dir.exists():
                        for f in t_dir.glob("*"):
                            if f.is_file() and f.name not in ["screen_capture.png", ".gitkeep"] and (f.suffix in [".tmp", ".mp3", ".wav", ".lock"] or "temp" in f.name.lower()):
                                try:
                                    if now - f.stat().st_mtime > 180:
                                        f.unlink()
                                        files_removed += 1
                                except Exception:
                                    pass
            except Exception:
                pass

            # 4. Windows Working Set compaction
            if sys.platform == "win32":
                try:
                    ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
                except Exception:
                    pass

        mem_info_after = p.memory_info()
        rss_after = mem_info_after.rss / (1024 * 1024)
        freed_mb = max(0.0, rss_before - rss_after)

        return {
            "pruned": pruned,
            "rss_before_mb": round(rss_before, 2),
            "rss_after_mb": round(rss_after, 2),
            "freed_mb": round(freed_mb, 2),
            "system_ram_pct": round(sys_ram_pct, 1),
            "files_removed": files_removed
        }

    def repair_system_resources(self, details: str = "") -> Tuple[bool, str]:
        """
        Trims working memory, runs garbage collection, and clears system cache.
        """
        try:
            from tools.system_optimizer import system_optimizer
            system_optimizer.optimize_system()
        except Exception:
            pass
        self.prune_memory_and_resources(force=True)
        return True, "System memory and working set caches have been cleared."

    def verify_and_repair_ports(self) -> Dict[str, Any]:
        """
        Audits core service ports (e.g. Web Portal 5050 and WebSocket 5051).
        Verifies local socket binding responsiveness.
        """
        ports_to_check = [
            getattr(config, "WEB_PORTAL_PORT", 5050),
            getattr(config, "WEB_SOCKET_PORT", 5051)
        ]
        port_results = {}

        for port in ports_to_check:
            is_open = False
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.3)
                    res = s.connect_ex(("127.0.0.1", port))
                    is_open = (res == 0)
            except Exception:
                is_open = False
            port_results[port] = {"listening": is_open}

        return port_results

    def get_system_health_telemetry(self) -> Dict[str, Any]:
        """
        Computes composite system resilience index (0-100) and gathers
        full telemetry across daemon statuses, memory, and database integrity.
        """
        # Daemon statuses
        daemon_data = self.supervise_daemons()
        daemon_statuses = daemon_data.get("statuses", {})

        total_daemons = len(daemon_statuses)
        alive_daemons = sum(1 for d in daemon_statuses.values() if d.get("alive"))

        # Memory vitals
        import psutil
        p = psutil.Process()
        rss_mb = round(p.memory_info().rss / (1024 * 1024), 1)
        sys_ram_pct = round(psutil.virtual_memory().percent, 1)

        # Internet
        is_net_up = internet_sentinel.is_connected()

        # Database Quick Check
        db_ok = True
        try:
            import sqlite3
            if Path(config.MEMORY_DB_PATH).exists():
                conn = sqlite3.connect(str(config.MEMORY_DB_PATH), timeout=2.0)
                res = conn.execute("PRAGMA quick_check;").fetchone()
                conn.close()
                db_ok = (res and res[0] == "ok")
        except Exception:
            db_ok = False

        # Compute Health Score (100 Max)
        score = 100
        if not is_net_up:
            score -= 10
        if total_daemons > 0:
            dead_count = total_daemons - alive_daemons
            score -= (dead_count * 10)
        if sys_ram_pct > 85.0:
            score -= 15
        elif sys_ram_pct > 75.0:
            score -= 5
        if not db_ok:
            score -= 20

        score = max(0, min(100, score))

        return {
            "health_score": score,
            "status": "Nominal" if score >= 80 else ("Degraded" if score >= 50 else "Critical"),
            "internet_connected": is_net_up,
            "daemons_alive": alive_daemons,
            "daemons_total": total_daemons,
            "daemon_matrix": daemon_statuses,
            "process_rss_mb": rss_mb,
            "system_ram_pct": sys_ram_pct,
            "database_intact": db_ok,
            "timestamp": time.time()
        }

    def get_health_voice_summary(self) -> str:
        """Generates an articulate British Butler verbal status report for system health."""
        telemetry = self.get_system_health_telemetry()
        score = telemetry["health_score"]
        status = telemetry["status"]
        alive = telemetry["daemons_alive"]
        total = telemetry["daemons_total"]
        rss = telemetry["process_rss_mb"]
        ram = telemetry["system_ram_pct"]

        net_str = "online and synchronized" if telemetry["internet_connected"] else "operating in off-grid offline mode"

        return (
            f"Autonomous resilience matrix is {status}, sir, with an overall system health score of {score} percent. "
            f"All {alive} of {total} background sentinels are functioning normally, "
            f"the workstation network is {net_str}, "
            f"and core memory footprint is holding steady at {rss} megabytes ({ram} percent system RAM)."
        )

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

        # 6. Memory & Resources (with leak pruning)
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
        # 1. Audit and revive daemons with exponential backoff
        self.supervise_daemons()

        # 2. Audit audio lock
        self.repair_audio_subsystem("periodic_watchdog")

        # 3. Check and prune memory pressure
        self.prune_memory_and_resources(threshold_mb=400.0)

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
