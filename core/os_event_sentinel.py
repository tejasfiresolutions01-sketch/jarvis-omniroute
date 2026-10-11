"""
J.A.R.V.I.S. OS Peripheral, Open Port Auditor & Process Affinity Sentinel.
Features:
1. Local Port Listener & Network Security Auditor:
   - Scans active listening TCP/UDP sockets, identifying listening PID, process name, and port.
   - Alerts on suspicious or non-whitelisted listening ports.
2. Removable USB & Drive Insertion Sentinel:
   - Tracks dynamic mounting and unmounting of external removable USB and network drives.
3. Process Priority & Core Affinity Optimizer:
   - Adjusts process priority to High / Above Normal for sub-10ms acoustic latency.
4. Windows System Uptime & Session Inspector.
5. 100% Free, zero cloud dependency, native psutil execution.
Strictly in English.
"""

import os
import sys
import time
import psutil
import logging
import threading
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config

logger = logging.getLogger("OSEventSentinel")

# Standard Whitelisted Local Listening Ports for J.A.R.V.I.S.
STANDARD_AUTHORIZED_PORTS = {
    5050,  # Web Portal
    5051,  # Web Portal WebSocket
    20128, # OmniRoute Local Bridge
    8000,  # Local Development
    8080,  # Local Development
}


class OSEventSentinel:
    """
    Operating system security auditor and hardware peripheral observer.
    """

    def __init__(self):
        self._known_drives: Set[str] = set()
        self._init_drive_baseline()

    def _init_drive_baseline(self):
        """Records initially present drive mount points."""
        try:
            self._known_drives = set(p.mountpoint for p in psutil.disk_partitions(all=False))
        except Exception:
            self._known_drives = set()

    def audit_listening_ports(self) -> Dict[str, Any]:
        """
        Scans all active listening sockets on the local machine.
        Identifies port, PID, process name, and flags unexpected listeners.
        """
        listening_sockets = []
        unauthorized_count = 0

        try:
            # kind='inet' returns IPv4 and IPv6
            conns = psutil.net_connections(kind="inet")
            for c in conns:
                if c.status == psutil.CONN_LISTEN:
                    port = c.laddr.port
                    ip = c.laddr.ip
                    pid = c.pid
                    proc_name = "System"
                    if pid:
                        try:
                            proc_name = psutil.Process(pid).name()
                        except Exception:
                            proc_name = "Unknown"

                    is_whitelisted = port in STANDARD_AUTHORIZED_PORTS or port > 49152  # Ephemeral range
                    if not is_whitelisted and port < 10000:
                        unauthorized_count += 1

                    listening_sockets.append({
                        "ip": ip,
                        "port": port,
                        "pid": pid,
                        "process_name": proc_name,
                        "authorized": is_whitelisted
                    })
        except Exception as e:
            logger.debug(f"Socket inspection error: {e}")

        return {
            "total_listening": len(listening_sockets),
            "unauthorized_alerts": unauthorized_count,
            "status": "SECURE" if unauthorized_count == 0 else "REVIEW_RECOMMENDED",
            "sockets": listening_sockets[:15]
        }

    def check_peripheral_storage_changes(self) -> Dict[str, Any]:
        """
        Detects newly inserted USB flash drives, external SSDs, or unmounted drives.
        """
        current_drives: Set[str] = set()
        newly_attached: List[str] = []
        detached: List[str] = []

        try:
            partitions = psutil.disk_partitions(all=False)
            current_drives = set(p.mountpoint for p in partitions)
            newly_attached = list(current_drives - self._known_drives)
            detached = list(self._known_drives - current_drives)
            self._known_drives = current_drives
        except Exception as e:
            logger.debug(f"Partition inspection error: {e}")

        return {
            "active_drives": list(current_drives),
            "newly_attached": newly_attached,
            "detached": detached,
            "has_changes": len(newly_attached) > 0 or len(detached) > 0
        }

    def optimize_process_priority(self) -> bool:
        """
        Sets J.A.R.V.I.S. process priority to ABOVE_NORMAL on Windows
        to avoid acoustic thread starvation under heavy workload.
        """
        if sys.platform != "win32":
            return False
        try:
            current_proc = psutil.Process()
            current_proc.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
            logger.info("Process execution priority set to ABOVE_NORMAL.")
            return True
        except Exception as e:
            logger.debug(f"Unable to set process priority: {e}")
            return False

    def get_system_uptime(self) -> Dict[str, Any]:
        """Calculates system boot time and uptime in hours."""
        boot_ts = psutil.boot_time()
        uptime_sec = time.time() - boot_ts
        hours = round(uptime_sec / 3600.0, 2)
        return {
            "boot_timestamp": boot_ts,
            "uptime_seconds": round(uptime_sec, 1),
            "uptime_hours": hours,
            "boot_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(boot_ts))
        }


# Global Singleton
os_event_sentinel = OSEventSentinel()
