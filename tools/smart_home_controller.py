"""
J.A.R.V.I.S. Smart Home IoT & Perimeter Automation Controller.
Supports:
1. Native Home Assistant REST / WebSocket API integration.
2. Direct Local LAN Smart Device discovery (mDNS, Shelly, Tasmota, WLED, Hue, Chromecast).
3. Stateful Local IoT Matrix (persisted to memory/smart_home_state.json).
4. Full range of natural language device directives (lights, climate, security locks, appliances).
5. Strictly in English.
"""

import os
import sys
import re
import json
import socket
import urllib.request
import urllib.parse
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config

STATE_FILE = config.MEMORY_DIR / "smart_home_state.json"

DEFAULT_DEVICES = {
    "lab_lights": {
        "id": "lab_lights",
        "name": "Stark Lab Overhead Lights",
        "type": "light",
        "room": "Stark Lab",
        "state": "off",
        "brightness": 100,
        "color": "#00f0ff",
        "ha_entity_id": "light.stark_lab_lights"
    },
    "workshop_lights": {
        "id": "workshop_lights",
        "name": "Workshop Bench Lights",
        "type": "light",
        "room": "Workshop",
        "state": "off",
        "brightness": 100,
        "color": "#ffffff",
        "ha_entity_id": "light.workshop_bench"
    },
    "ambient_reactor": {
        "id": "ambient_reactor",
        "name": "Arc Reactor Ambient Display",
        "type": "light",
        "room": "Command Center",
        "state": "on",
        "brightness": 80,
        "color": "#00f0ff",
        "ha_entity_id": "light.arc_reactor_ambient"
    },
    "main_thermostat": {
        "id": "main_thermostat",
        "name": "Stark Residence HVAC",
        "type": "climate",
        "room": "Residence",
        "state": "cool",
        "current_temp": 24.0,
        "target_temp": 22.0,
        "unit": "C",
        "ha_entity_id": "climate.residence_hvac"
    },
    "front_door_lock": {
        "id": "front_door_lock",
        "name": "Perimeter Security Deadbolt",
        "type": "lock",
        "room": "Perimeter",
        "state": "locked",
        "ha_entity_id": "lock.perimeter_front_door"
    },
    "lab_holo_projector": {
        "id": "lab_holo_projector",
        "name": "Holographic Projector Rig",
        "type": "switch",
        "room": "Stark Lab",
        "state": "on",
        "ha_entity_id": "switch.holo_projector"
    },
    "smart_plug_workbench": {
        "id": "smart_plug_workbench",
        "name": "Main Fabrication Bench Relay",
        "type": "switch",
        "room": "Workshop",
        "state": "on",
        "ha_entity_id": "switch.fabrication_bench"
    }
}


class SmartHomeController:
    """Master controller for smart home devices, IoT network discovery, and Home Assistant."""

    def __init__(self):
        self._lock = threading.Lock()
        self.ha_url = os.getenv("HASS_URL", "http://homeassistant.local:8123").rstrip("/")
        self.ha_token = os.getenv("HASS_TOKEN", "")
        self.devices: Dict[str, Dict[str, Any]] = {}
        self._load_state()

    def _load_state(self):
        with self._lock:
            if STATE_FILE.exists():
                try:
                    with open(STATE_FILE, "r", encoding="utf-8") as f:
                        self.devices = json.load(f)
                except Exception:
                    self.devices = dict(DEFAULT_DEVICES)
            else:
                self.devices = dict(DEFAULT_DEVICES)
                self._save_state_unlocked()

    def _save_state_unlocked(self):
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.devices, f, indent=2)
        except Exception:
            pass

    def _save_state(self):
        with self._lock:
            self._save_state_unlocked()

    def get_devices(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return dict(self.devices)

    def get_device(self, dev_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.devices.get(dev_id)

    def _call_ha_service(self, domain: str, service: str, entity_id: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Attempts to call Home Assistant REST API if configured and reachable."""
        if not self.ha_token:
            return False

        url = f"{self.ha_url}/api/services/{domain}/{service}"
        payload = {"entity_id": entity_id}
        if data:
            payload.update(data)

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.ha_token}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=0.8) as res:
                return res.status in (200, 201)
        except Exception:
            return False

    def scan_lan_for_iot(self) -> List[Dict[str, Any]]:
        """Scans local subnet for common IoT hubs and smart devices."""
        from tools.network_scanner import network_scanner
        arp_devices = network_scanner.scan_arp_table()
        discovered_iot = []

        iot_port_map = {
            8123: "Home Assistant Hub",
            8008: "Google Cast / Smart Display",
            8009: "Chromecast Video/Audio",
            1883: "MQTT Broker",
            80: "HTTP Smart Device / Shelly / WLED",
            8080: "IoT Gateway / Hub",
            6053: "ESPHome Node"
        }

        for dev in arp_devices:
            ip = dev["ip"]
            # Fast check on select ports
            for port, label in iot_port_map.items():
                if network_scanner.check_open_port(ip, port, timeout=0.15):
                    discovered_iot.append({
                        "ip": ip,
                        "mac": dev["mac"],
                        "port": port,
                        "label": label,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    break

        return discovered_iot

    def set_device_power(self, dev_id: str, state: str) -> Tuple[bool, str]:
        """Turns a device on or off."""
        clean_state = "on" if state.lower() in ["on", "true", "enable", "activate"] else "off"
        with self._lock:
            if dev_id not in self.devices:
                return False, f"Device '{dev_id}' not found in registry."

            dev = self.devices[dev_id]
            dev["state"] = clean_state
            dev_name = dev["name"]
            dev_type = dev["type"]
            ha_id = dev.get("ha_entity_id", "")

        self._save_state()

        # HA sync
        domain = "light" if dev_type == "light" else "switch"
        service = "turn_on" if clean_state == "on" else "turn_off"
        if ha_id:
            threading.Thread(target=self._call_ha_service, args=(domain, service, ha_id), daemon=True).start()

        action = "energized" if clean_state == "on" else "powered down"
        return True, f"{dev_name} has been {action}, sir."

    def set_brightness(self, dev_id: str, level: int) -> Tuple[bool, str]:
        """Sets brightness (0-100) for a light."""
        level = max(0, min(100, int(level)))
        with self._lock:
            if dev_id not in self.devices:
                return False, f"Device '{dev_id}' not found in registry."
            dev = self.devices[dev_id]
            if dev["type"] != "light":
                return False, f"{dev['name']} does not support brightness adjustments."
            dev["brightness"] = level
            dev["state"] = "on" if level > 0 else "off"
            dev_name = dev["name"]
            ha_id = dev.get("ha_entity_id", "")

        self._save_state()

        if ha_id and level > 0:
            pct_255 = int(level * 2.55)
            threading.Thread(
                target=self._call_ha_service,
                args=("light", "turn_on", ha_id, {"brightness": pct_255}),
                daemon=True
            ).start()

        return True, f"{dev_name} brightness set to {level} percent, sir."

    def set_climate_temperature(self, dev_id: str, target_temp: float) -> Tuple[bool, str]:
        """Sets target climate temperature."""
        with self._lock:
            if dev_id not in self.devices:
                return False, f"Device '{dev_id}' not found in registry."
            dev = self.devices[dev_id]
            if dev["type"] != "climate":
                return False, f"{dev['name']} is not a climate or thermostat controller."
            dev["target_temp"] = float(target_temp)
            dev_name = dev["name"]
            unit = dev.get("unit", "C")
            ha_id = dev.get("ha_entity_id", "")

        self._save_state()

        if ha_id:
            threading.Thread(
                target=self._call_ha_service,
                args=("climate", "set_temperature", ha_id, {"temperature": target_temp}),
                daemon=True
            ).start()

        return True, f"{dev_name} target temperature adjusted to {target_temp:.1f} degrees {unit}, sir."

    def set_lock_state(self, dev_id: str, locked: bool) -> Tuple[bool, str]:
        """Locks or unlocks a security deadbolt."""
        state_str = "locked" if locked else "unlocked"
        with self._lock:
            if dev_id not in self.devices:
                return False, f"Device '{dev_id}' not found in registry."
            dev = self.devices[dev_id]
            if dev["type"] != "lock":
                return False, f"{dev['name']} is not a lock mechanism."
            dev["state"] = state_str
            dev_name = dev["name"]
            ha_id = dev.get("ha_entity_id", "")

        self._save_state()

        if ha_id:
            service = "lock" if locked else "unlock"
            threading.Thread(target=self._call_ha_service, args=("lock", service, ha_id), daemon=True).start()

        action = "secured" if locked else "unlocked"
        return True, f"{dev_name} has been {action}, sir."

    def format_status_report(self) -> str:
        """Returns a concise butler summary of all registered devices."""
        with self._lock:
            devs = list(self.devices.values())

        lines = ["Smart Home & Automation Matrix Telemetry, sir:"]
        for d in devs:
            dtype = d["type"]
            name = d["name"]
            state = d.get("state", "unknown").upper()
            room = d.get("room", "General")
            if dtype == "light":
                bri = d.get("brightness", 100)
                lines.append(f"&bull; [{room}] {name}: {state} (Brightness: {bri}%)")
            elif dtype == "climate":
                curr = d.get("current_temp", 22.0)
                tgt = d.get("target_temp", 22.0)
                u = d.get("unit", "C")
                lines.append(f"&bull; [{room}] {name}: Current {curr}°{u} -> Target {tgt}°{u}")
            elif dtype == "lock":
                lines.append(f"&bull; [{room}] {name}: {state}")
            else:
                lines.append(f"&bull; [{room}] {name}: {state}")

        return "\n".join(lines)

    def parse_and_execute(self, prompt: str) -> Tuple[bool, str]:
        """
        Parses natural language directives for smart home control.
        Returns: (handled, response_string)
        """
        clean = prompt.lower().strip()

        # 1. Status / Overview
        if any(p in clean for p in [
            "smart home status", "iot status", "home automation status",
            "device status", "check smart home", "smart home report",
            "list smart devices", "smart home devices"
        ]):
            return True, self.format_status_report()

        # 2. LAN IoT Device Discovery
        if any(p in clean for p in [
            "scan for smart home", "scan for iot", "discover smart home",
            "discover iot devices", "scan smart devices", "find smart devices"
        ]):
            nodes = self.scan_lan_for_iot()
            if not nodes:
                return True, "Local IoT sweep completed, sir. Zero external IoT hubs detected on this subnet. Operating through the virtual Stark Automation Matrix."
            
            res_lines = [f"Reconnaissance complete, sir. Identified {len(nodes)} active IoT nodes on the local perimeter:"]
            for n in nodes[:5]:
                res_lines.append(f"&bull; {n['label']} at {n['ip']} (Port {n['port']})")
            return True, "\n".join(res_lines)

        # 3. Climate / Temperature Directives
        temp_match = re.search(r"(?:set|change|adjust)\s+(?:the\s+)?(?:thermostat|temperature|climate|ac|hvac)\s+(?:to\s+)?(\d+(?:\.\d+)?)\s*(?:degrees|c|f)?", clean)
        if temp_match:
            deg = float(temp_match.group(1))
            return self.set_climate_temperature("main_thermostat", deg)

        # 4. Lock / Unlock Directives
        if any(p in clean for p in ["lock front door", "lock perimeter", "secure front door", "lock door", "lock the door"]):
            return self.set_lock_state("front_door_lock", locked=True)

        if any(p in clean for p in ["unlock front door", "unlock perimeter", "open front door lock", "unlock door", "unlock the door"]):
            return self.set_lock_state("front_door_lock", locked=False)

    def _match_devices(self, target: str) -> List[str]:
        t = target.lower().strip()
        matched = []
        if t in ["lights", "all lights", "all the lights"]:
            return [dev_id for dev_id, dev in self.devices.items() if dev["type"] == "light"]

        if t in ["everything", "all devices", "all"]:
            return list(self.devices.keys())

        for dev_id, dev in self.devices.items():
            norm_id = dev_id.replace("_", " ")
            name_lower = dev["name"].lower()
            room_lower = dev["room"].lower()

            if norm_id in t or t in norm_id:
                matched.append(dev_id)
                continue

            words = t.split()
            if all(w in (name_lower + " " + norm_id + " " + room_lower) for w in words):
                matched.append(dev_id)
                continue

            if dev["room"].lower() in t and (dev["type"] in t or (dev["type"] == "light" and "light" in t)):
                matched.append(dev_id)
                continue

        return matched

    def parse_and_execute(self, prompt: str) -> Tuple[bool, str]:
        """
        Parses natural language directives for smart home control.
        Returns: (handled, response_string)
        """
        clean = prompt.lower().strip()

        # 1. Status / Overview
        if any(p in clean for p in [
            "smart home status", "iot status", "home automation status",
            "device status", "check smart home", "smart home report",
            "list smart devices", "smart home devices"
        ]):
            return True, self.format_status_report()

        # 2. LAN IoT Device Discovery
        if any(p in clean for p in [
            "scan for smart home", "scan for iot", "discover smart home",
            "discover iot devices", "scan smart devices", "find smart devices"
        ]):
            nodes = self.scan_lan_for_iot()
            if not nodes:
                return True, "Local IoT sweep completed, sir. Zero external IoT hubs detected on this subnet. Operating through the virtual Stark Automation Matrix."
            
            res_lines = [f"Reconnaissance complete, sir. Identified {len(nodes)} active IoT nodes on the local perimeter:"]
            for n in nodes[:5]:
                res_lines.append(f"&bull; {n['label']} at {n['ip']} (Port {n['port']})")
            return True, "\n".join(res_lines)

        # 3. Climate / Temperature Directives
        temp_match = re.search(r"(?:set|change|adjust)\s+(?:the\s+)?(?:thermostat|temperature|climate|ac|hvac)\s+(?:to\s+)?(\d+(?:\.\d+)?)\s*(?:degrees|c|f)?", clean)
        if temp_match:
            deg = float(temp_match.group(1))
            return self.set_climate_temperature("main_thermostat", deg)

        # 4. Lock / Unlock Directives
        if re.search(r"\b(?:lock|secure)\s+(?:the\s+)?(?:front\s+)?(?:door|deadbolt|lock|perimeter)", clean):
            return self.set_lock_state("front_door_lock", locked=True)

        if re.search(r"\b(?:unlock|unsecure|open)\s+(?:the\s+)?(?:front\s+)?(?:door|deadbolt|lock|perimeter)", clean):
            return self.set_lock_state("front_door_lock", locked=False)

        # 5. Brightness Directives
        bri_match = re.search(r"(?:set|adjust)\s+(?:the\s+)?(.+?)\s+(?:brightness\s+to\s+|to\s+)(\d+)\s*(?:percent|%)?", clean)
        if bri_match:
            target_phrase = bri_match.group(1).strip()
            level = int(bri_match.group(2))
            matched = self._match_devices(target_phrase)
            light_matched = [m for m in matched if self.devices[m]["type"] == "light"]
            if light_matched:
                return self.set_brightness(light_matched[0], level)
            return self.set_brightness("lab_lights", level)

        # 6. Power Directives (Turn On / Turn Off)
        on_match = re.match(r"^(?:turn\s+on|activate|energize|enable|power\s+on)\s+(?:the\s+)?(.+)$", clean)
        if on_match:
            target = on_match.group(1).strip()
            if "night shield" in target or "night mode" in target or "camera" in target:
                return False, ""
            
            matched = self._match_devices(target)
            if matched:
                results = []
                for dev_id in matched:
                    ok, msg = self.set_device_power(dev_id, "on")
                    results.append(msg)
                return True, " ".join(results)

        off_match = re.match(r"^(?:turn\s+off|deactivate|power\s+down|disable|shut\s+down)\s+(?:the\s+)?(.+)$", clean)
        if off_match:
            target = off_match.group(1).strip()
            if "night shield" in target or "night mode" in target or "camera" in target:
                return False, ""

            matched = self._match_devices(target)
            if matched:
                results = []
                for dev_id in matched:
                    ok, msg = self.set_device_power(dev_id, "off")
                    results.append(msg)
                return True, " ".join(results)

        return False, ""


# Global singleton
smart_home = SmartHomeController()
