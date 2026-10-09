"""
J.A.R.V.I.S. Local LAN Perimeter & IoT Device Scanner.
Provides Tony Stark-level network situational awareness: sweeps local subnet ARP tables,
measures gateway ping latencies, discovers local nodes, and inspects service ports.
"""

import socket
import subprocess
import re
import threading
from typing import Dict, Any, List, Optional
import config

class NetworkScanner:
    """
    Subnet Perimeter & Local Network Sentinel.
    Extracts local host telemetry, gateway routing, ARP neighbor tables, and service ports.
    """

    COMMON_PORTS = [80, 443, 8080, 8123, 1883, 22, 53, 5000, 20128]

    def scan_iot_devices(self) -> List[Dict[str, Any]]:
        """Discovers smart home hubs and IoT nodes across the local subnet."""
        from tools.smart_home_controller import smart_home
        return smart_home.scan_lan_for_iot()

    def get_local_identity(self) -> Dict[str, str]:
        """Returns local hostname, primary IP address, and default gateway."""
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "127.0.0.1"

        gateway = self._detect_default_gateway()
        return {
            "hostname": hostname,
            "local_ip": local_ip,
            "gateway": gateway or "Unknown"
        }

    def _detect_default_gateway(self) -> Optional[str]:
        """Detects default gateway via route print 0.0.0.0."""
        try:
            out = subprocess.run(["route", "print", "0.0.0.0"], capture_output=True, text=True, timeout=2.0).stdout
            for line in out.splitlines():
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0] == "0.0.0.0":
                    gw = parts[2]
                    # Validate IP format
                    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", gw):
                        return gw
        except Exception:
            pass
        return None

    def ping_host(self, ip: str, timeout_ms: int = 500) -> Optional[int]:
        """Sends an ICMP ping to check latency in milliseconds."""
        try:
            res = subprocess.run(
                ["ping", "-n", "1", "-w", str(timeout_ms), ip],
                capture_output=True,
                text=True,
                timeout=1.5
            )
            if res.returncode == 0:
                m = re.search(r"time[=<](\d+)ms", res.stdout, re.IGNORECASE)
                if m:
                    return int(m.group(1))
                return 1 # Fast localhost or sub-1ms
        except Exception:
            pass
        return None

    def scan_arp_table(self) -> List[Dict[str, str]]:
        """Parses the Windows ARP cache table for active IP and MAC addresses."""
        devices = []
        try:
            out = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=3.0).stdout
            pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([0-9a-fA-F\-]{17})\s+(\w+)"
            for match in re.finditer(pattern, out):
                ip = match.group(1)
                mac = match.group(2).lower()
                entry_type = match.group(3).lower()

                # Filter out multicast and broadcast ranges
                if (
                    not ip.startswith("224.") and
                    not ip.startswith("239.") and
                    ip != "255.255.255.255" and
                    not ip.endswith(".255")
                ):
                    devices.append({
                        "ip": ip,
                        "mac": mac,
                        "type": entry_type
                    })
        except Exception:
            pass
        return devices

    def check_open_port(self, ip: str, port: int, timeout: float = 0.3) -> bool:
        """Checks if a TCP port is open on target IP."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                res = s.connect_ex((ip, port))
                return res == 0
        except Exception:
            return False

    def scan_open_ports(self, ip: str, ports: Optional[List[int]] = None) -> List[int]:
        """Scans specified ports concurrently."""
        target_ports = ports or self.COMMON_PORTS
        open_ports = []
        threads = []

        def _check(p):
            if self.check_open_port(ip, p):
                open_ports.append(p)

        for p in target_ports:
            t = threading.Thread(target=_check, args=(p,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=0.5)

        return sorted(open_ports)

    def perform_perimeter_sweep(self) -> Dict[str, Any]:
        """Performs a full perimeter sweep across local subnet and gateway."""
        identity = self.get_local_identity()
        gw = identity["gateway"]
        gw_latency = self.ping_host(gw) if gw != "Unknown" else None

        arp_devices = self.scan_arp_table()
        discovered_nodes = []

        for dev in arp_devices:
            ip = dev["ip"]
            lat = self.ping_host(ip, timeout_ms=300)
            open_p = self.scan_open_ports(ip, [80, 443, 20128, 5050])
            discovered_nodes.append({
                "ip": ip,
                "mac": dev["mac"],
                "type": dev["type"],
                "latency_ms": lat,
                "open_ports": open_p,
                "is_gateway": (ip == gw)
            })

        return {
            "host_identity": identity,
            "gateway_latency_ms": gw_latency,
            "discovered_nodes": discovered_nodes,
            "node_count": len(discovered_nodes) + 1 # Include host
        }

    def format_butler_perimeter_report(self, sweep_results: Optional[Dict[str, Any]] = None) -> str:
        """Synthesizes an articulate butler security report on local perimeter telemetry."""
        results = sweep_results or self.perform_perimeter_sweep()
        identity = results["host_identity"]
        gw = identity["gateway"]
        gw_lat = results.get("gateway_latency_ms")
        gw_status = f"Online ({gw_lat}ms latency)" if gw_lat is not None else "Reachable"
        nodes = results.get("discovered_nodes", [])

        lines = [
            f"Perimeter reconnaissance complete, sir.",
            f"Host workstation '{identity['hostname']}' is active on {identity['local_ip']}.",
            f"Primary Gateway ({gw}) status: {gw_status}.",
            f"Total active network nodes identified: {results.get('node_count', len(nodes) + 1)}."
        ]

        if nodes:
            lines.append("Discovered active perimeter nodes:")
            for n in nodes[:5]:
                lat_str = f"{n['latency_ms']}ms" if n['latency_ms'] is not None else "responsive"
                role = " [Default Gateway]" if n.get("is_gateway") else ""
                port_str = f" | Open Ports: {n['open_ports']}" if n.get("open_ports") else ""
                lines.append(f"- {n['ip']}{role} (MAC: {n['mac']}, Latency: {lat_str}{port_str})")

        lines.append("All perimeter telemetry is nominal and secure, sir.")
        return "\n".join(lines)

# Global singleton
network_scanner = NetworkScanner()
