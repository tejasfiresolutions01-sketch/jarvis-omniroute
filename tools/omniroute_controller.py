"""
J.A.R.V.I.S. OmniRoute Controller & Telemetry Sentinel
Monitors, manages, and interacts with the OmniRoute Multi-Provider AI Gateway
Upstream: https://github.com/diegosouzapw/OmniRoute
"""

import os
import time
import requests
import subprocess
from typing import Dict, Any, Optional
import config

class OmniRouteController:
    """
    Manages the OmniRoute Local AI Gateway lifecycle and telemetry.
    """

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or config.OMNIROUTE_BASE_URL
        self.api_key = api_key or config.OMNIROUTE_API_KEY
        self.port = config.OMNIROUTE_PORT
        self.upstream_repo = "https://github.com/diegosouzapw/OmniRoute"

    def get_status(self) -> Dict[str, Any]:
        """
        Polls the local OmniRoute instance and returns operational metrics.
        """
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        start_time = time.time()
        try:
            resp = requests.get(f"{self.base_url}/models", headers=headers, timeout=3.0)
            latency_ms = round((time.time() - start_time) * 1000, 1)

            if resp.status_code == 200:
                data = resp.json()
                models = data.get("data", [])
                return {
                    "online": True,
                    "status_code": 200,
                    "latency_ms": latency_ms,
                    "model_count": len(models),
                    "base_url": self.base_url,
                    "upstream": self.upstream_repo,
                    "message": f"OmniRoute Gateway active ({len(models)} models available, {latency_ms}ms)"
                }
            elif resp.status_code in [401, 403]:
                return {
                    "online": True,
                    "status_code": resp.status_code,
                    "latency_ms": latency_ms,
                    "model_count": 0,
                    "base_url": self.base_url,
                    "upstream": self.upstream_repo,
                    "message": "OmniRoute Gateway active (authentication required)"
                }
            else:
                return {
                    "online": False,
                    "status_code": resp.status_code,
                    "latency_ms": latency_ms,
                    "model_count": 0,
                    "base_url": self.base_url,
                    "upstream": self.upstream_repo,
                    "message": f"OmniRoute Gateway returned HTTP {resp.status_code}"
                }
        except requests.exceptions.RequestException as err:
            return {
                "online": False,
                "status_code": 0,
                "latency_ms": 0,
                "model_count": 0,
                "base_url": self.base_url,
                "upstream": self.upstream_repo,
                "message": f"OmniRoute Gateway unreachable: {err}"
            }

    def get_butler_summary(self) -> str:
        """
        Returns a refined spoken summary suitable for J.A.R.V.I.S. voice response.
        """
        status = self.get_status()
        if status["online"]:
            if status["model_count"] > 0:
                return f"OmniRoute multi-provider gateway is operational at port {self.port}, sir, with {status['model_count']} models indexed."
            return f"OmniRoute gateway is online at port {self.port}, sir."
        return f"OmniRoute gateway is currently offline at port {self.port}, sir. Local deterministic matrix is active."

    def start_service_detached(self) -> bool:
        """
        Attempts to launch the omniroute service in the background if not running.
        """
        if self.get_status()["online"]:
            return True

        try:
            # Launch via cmd start in background
            subprocess.Popen(
                ["cmd.exe", "/c", "start", "/b", "omniroute", "serve"],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS if os.name == "nt" else 0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(2)
            return self.get_status()["online"]
        except Exception:
            return False

# Global instance
omniroute_controller = OmniRouteController()
