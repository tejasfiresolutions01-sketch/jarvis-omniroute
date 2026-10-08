"""
J.A.R.V.I.S. Opportunistic Internet & Online Connectivity Sentinel.
Continuously senses network state and seamlessly connects to the internet
whenever connectivity becomes available, restoring online neural pathways,
OmniRoute gateway models, and edge-tts synthesis.
"""

import socket
import urllib.request
import threading
import time
import logging
from typing import Tuple, Optional

import config

logger = logging.getLogger("InternetSentinel")

class InternetSentinel:
    """
    Opportunistic Internet Connectivity Sentinel.
    - Proactively senses and connects to the internet whenever available.
    - Manages dynamic transition between local offline Butler and online frontier matrices.
    - Automatically re-initializes OmniRoute Gateway upon network detection.
    """

    PROBE_TARGETS = [
        ("1.1.1.1", 53),
        ("8.8.8.8", 53),
        ("9.9.9.9", 53)
    ]
    PROBE_URLS = [
        "https://www.google.com",
        "https://1.1.1.1",
        "https://www.cloudflare.com"
    ]
    CACHE_TTL_SECONDS = 3.0

    def __init__(self):
        self._is_connected: bool = False
        self._last_checked: float = 0.0
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._running: bool = False
        self._on_connect_callbacks: list = []

    def check_connectivity(self, timeout: float = 1.2) -> bool:
        """
        Rapid multi-tier reachability check with sub-second latency.
        Tier 1: Ultra-fast raw socket handshake to global DNS endpoints.
        Tier 2: HTTP GET probe fallback.
        """
        now = time.time()
        with self._lock:
            if now - self._last_checked < self.CACHE_TTL_SECONDS:
                return self._is_connected

        connected = False

        # Tier 1: Fast socket connect (typically 15-40ms)
        for host, port in self.PROBE_TARGETS:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                sock.connect((host, port))
                sock.close()
                connected = True
                break
            except Exception:
                pass

        # Tier 2: HTTP probe fallback if sockets are restricted
        if not connected:
            for url in self.PROBE_URLS:
                try:
                    req = urllib.request.Request(
                        url,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                    )
                    with urllib.request.urlopen(req, timeout=timeout):
                        connected = True
                        break
                except Exception:
                    pass

        with self._lock:
            prev = self._is_connected
            self._is_connected = connected
            self._last_checked = now

        # Detect transition from offline to online
        if connected and not prev:
            logger.info("[Internet Sentinel]: Internet connection established. Synchronizing online matrices.")
            self._on_online_transition()
        elif not connected and prev:
            logger.info("[Internet Sentinel]: Internet connection dropped. Switching smoothly to local offline Butler mode.")

        return connected

    def is_connected(self) -> bool:
        """Thread-safe fast check of current internet connection state."""
        return self.check_connectivity()

    def _on_online_transition(self):
        """Executed automatically when internet connectivity is gained."""
        def _sync_subroutines():
            try:
                # 1. Verify and start OmniRoute gateway if needed
                from tools.omniroute_controller import omniroute_controller
                st = omniroute_controller.get_status()
                if not st.get("online"):
                    logger.info("[Internet Sentinel]: Starting OmniRoute gateway detached...")
                    omniroute_controller.start_service_detached()
            except Exception as e:
                logger.error(f"[Internet Sentinel]: Error launching gateway on reconnect: {e}")

            # Fire any registered callbacks
            for cb in list(self._on_connect_callbacks):
                try:
                    cb()
                except Exception:
                    pass

        threading.Thread(target=_sync_subroutines, daemon=True).start()

    def register_on_connect(self, callback):
        """Register a callback function to be called when internet connects."""
        if callback not in self._on_connect_callbacks:
            self._on_connect_callbacks.append(callback)

    def reconnect(self) -> Tuple[bool, str]:
        """
        Actively attempts to repair and reconnect internet connectivity:
        - Flushes Windows DNS cache.
        - Restarts OmniRoute gateway.
        - Re-checks connection status.
        """
        import subprocess
        # 1. Flush DNS cache
        try:
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=3.0)
        except Exception:
            pass

        # 2. Re-initialize OmniRoute gateway
        try:
            from tools.omniroute_controller import omniroute_controller
            omniroute_controller.start_service_detached()
        except Exception:
            pass

        # 3. Invalidate cache and re-probe
        with self._lock:
            self._last_checked = 0.0

        is_up = self.check_connectivity(timeout=2.0)
        if is_up:
            return True, "Internet connectivity is operational and verified, sir. All online neural channels are active."
        return False, "I cannot reach external networks right now, sir. Please check your Wi-Fi or router connection."

    def start(self):
        """Launches the background opportunistic connection monitor."""
        if self._running:
            return
        self._running = True

        def _monitor_loop():
            # Initial probe
            self.check_connectivity()
            while self._running:
                try:
                    self.check_connectivity()
                except Exception:
                    pass
                time.sleep(10.0)

        self._monitor_thread = threading.Thread(target=_monitor_loop, daemon=True, name="InternetSentinelThread")
        self._monitor_thread.start()
        logger.info("[Internet Sentinel]: Opportunistic internet monitoring active.")

    def stop(self):
        """Halts the monitor thread."""
        self._running = False

# Global singleton
internet_sentinel = InternetSentinel()
