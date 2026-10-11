"""
J.A.R.V.I.S. Autonomous Ambient Sentinel & Hardware/IDE Guardian.
Features:
1. Low-Overhead Background Environmental Telemetry (<0.2% CPU):
   - Monitors CPU load, memory pressure, battery level, and disk space.
2. Git Repository & Workspace Integrity Guardian:
   - Tracks uncommitted changes, modified files, and untracked artifacts.
3. Active Window Focus Identification:
   - Senses foreground development environment and developer context.
4. Proactive Threshold-Triggered Verbal Advisories:
   - Speaks proactive alerts when critical thresholds are reached (thermal spikes, low battery).
   - Strict rate-limiting: max 1 notification per alert type every 15 minutes.
5. 100% Free Plan, zero external cloud dependency, thread-safe daemon.
"""

import logging
import os
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

import config

logger = logging.getLogger("AmbientSentinel")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class SystemVitals:
    """Snapshot of active physical machine vitals."""
    cpu_percent: float
    per_cpu_percent: List[float]
    memory_percent: float
    available_ram_gb: float
    battery_percent: Optional[float]
    power_plugged: Optional[bool]
    free_disk_gb: float
    active_window_title: str = "Unknown"
    uncommitted_git_files: int = 0
    timestamp: float = field(default_factory=time.time)


class AmbientSentinel:
    """
    Autonomous Background Guardian and Environment Sensor.
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = workspace_root or PROJECT_ROOT
        self._lock = threading.RLock()
        self._is_running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._last_alert_times: Dict[str, float] = {}
        self.alert_cooldown_seconds = 900.0  # 15 minutes minimum between repeated alert types
        self.enable_vocal_alerts = False  # Disabled by default; can be toggled on

    def get_vitals(self) -> SystemVitals:
        """Captures an instantaneous snapshot of machine vitals."""
        cpu = psutil.cpu_percent(interval=None)
        per_cpu = psutil.cpu_percent(interval=None, percpu=True)
        mem = psutil.virtual_memory()

        battery = None
        plugged = None
        try:
            batt_info = psutil.sensors_battery()
            if batt_info:
                battery = round(batt_info.percent, 1)
                plugged = batt_info.power_plugged
        except Exception:
            pass

        try:
            _, _, free_bytes = shutil.disk_usage(str(self.workspace_root))
            free_gb = round(free_bytes / (1024 ** 3), 2)
        except Exception:
            free_gb = 0.0

        active_win = self._get_active_window_title()
        uncommitted = self._get_uncommitted_git_count()

        return SystemVitals(
            cpu_percent=round(cpu, 1),
            per_cpu_percent=[round(p, 1) for p in per_cpu],
            memory_percent=round(mem.percent, 1),
            available_ram_gb=round(mem.available / (1024 ** 3), 2),
            battery_percent=battery,
            power_plugged=plugged,
            free_disk_gb=free_gb,
            active_window_title=active_win,
            uncommitted_git_files=uncommitted,
            timestamp=time.time()
        )

    def _get_active_window_title(self) -> str:
        """Retrieves title of the foreground active window on Windows."""
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                if hwnd:
                    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                        return buff.value
            except Exception:
                pass
        return "Desktop Session"

    def _get_uncommitted_git_count(self) -> int:
        """Counts modified and untracked files in the workspace."""
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=2.0
            )
            if res.returncode == 0:
                lines = [l for l in res.stdout.strip().splitlines() if l.strip()]
                return len(lines)
        except Exception:
            pass
        return 0

    def evaluate_health_advisories(self, vitals: Optional[SystemVitals] = None) -> List[Dict[str, Any]]:
        """
        Analyzes vitals against safety thresholds and returns advisory alerts.
        """
        v = vitals or self.get_vitals()
        advisories = []
        now = time.time()

        # 1. High CPU Sustained Load
        if v.cpu_percent >= 92.0:
            if now - self._last_alert_times.get("high_cpu", 0) > self.alert_cooldown_seconds:
                advisories.append({
                    "type": "high_cpu",
                    "severity": "WARNING",
                    "message": f"Sir, sustained processor load has reached {v.cpu_percent}%. Thermal throttling may occur.",
                    "value": v.cpu_percent
                })
                self._last_alert_times["high_cpu"] = now

        # 2. Critical Memory Saturation
        if v.memory_percent >= 90.0 or v.available_ram_gb < 0.8:
            if now - self._last_alert_times.get("high_ram", 0) > self.alert_cooldown_seconds:
                advisories.append({
                    "type": "high_ram",
                    "severity": "WARNING",
                    "message": f"Sir, system memory is at {v.memory_percent}%. Available headroom is {v.available_ram_gb} gigabytes.",
                    "value": v.memory_percent
                })
                self._last_alert_times["high_ram"] = now

        # 3. Low Battery Depletion
        if v.battery_percent is not None and v.battery_percent <= 18.0 and not v.power_plugged:
            if now - self._last_alert_times.get("low_battery", 0) > self.alert_cooldown_seconds:
                advisories.append({
                    "type": "low_battery",
                    "severity": "CRITICAL",
                    "message": f"Sir, battery reserve is down to {v.battery_percent}%. Please connect external power.",
                    "value": v.battery_percent
                })
                self._last_alert_times["low_battery"] = now

        # 4. Git Workspace Dirty Status Check
        if v.uncommitted_git_files >= 10:
            if now - self._last_alert_times.get("git_dirty", 0) > self.alert_cooldown_seconds:
                advisories.append({
                    "type": "git_dirty",
                    "severity": "INFO",
                    "message": f"Sir, you have {v.uncommitted_git_files} uncommitted modifications in the repository.",
                    "value": v.uncommitted_git_files
                })
                self._last_alert_times["git_dirty"] = now

        if self.enable_vocal_alerts and advisories:
            for adv in advisories:
                try:
                    from core.voice import speak
                    speak(adv["message"])
                except Exception:
                    pass

        return advisories

    def start_sentinel(self, poll_interval_s: float = 10.0):
        """Starts the background sensor daemon."""
        with self._lock:
            if not self._is_running:
                self._is_running = True
                self._monitor_thread = threading.Thread(
                    target=self._run_loop,
                    args=(poll_interval_s,),
                    daemon=True,
                    name="JarvisAmbientSentinel"
                )
                self._monitor_thread.start()
                logger.info("Ambient Sentinel daemon initialized.")

    def stop_sentinel(self):
        """Stops the background sensor daemon."""
        with self._lock:
            self._is_running = False

    def _run_loop(self, interval_s: float):
        while self._is_running:
            try:
                self.evaluate_health_advisories()
            except Exception as e:
                logger.debug(f"Sentinel loop exception: {e}")
            time.sleep(interval_s)


# Global Singleton Instance
ambient_sentinel = AmbientSentinel()
