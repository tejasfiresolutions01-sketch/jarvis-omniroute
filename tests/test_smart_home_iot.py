import unittest
import json
import urllib.request
import socket
import time
from pathlib import Path
from tools.smart_home_controller import smart_home, DEFAULT_DEVICES
from tools.network_scanner import network_scanner
from core.local_intelligence import LocalIntelligence
from ui.web_portal import WebPortalServer

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port

class TestSmartHomeIoT(unittest.TestCase):
    def setUp(self):
        self.loc_intel = LocalIntelligence()

    def test_default_device_registry(self):
        devices = smart_home.get_devices()
        self.assertIn("lab_lights", devices)
        self.assertIn("workshop_lights", devices)
        self.assertIn("ambient_reactor", devices)
        self.assertIn("main_thermostat", devices)
        self.assertIn("front_door_lock", devices)

    def test_power_control_and_state(self):
        ok, msg = smart_home.set_device_power("workshop_lights", "on")
        self.assertTrue(ok)
        self.assertEqual(smart_home.get_device("workshop_lights")["state"], "on")
        self.assertIn("energized", msg)

        ok, msg = smart_home.set_device_power("workshop_lights", "off")
        self.assertTrue(ok)
        self.assertEqual(smart_home.get_device("workshop_lights")["state"], "off")
        self.assertIn("powered down", msg)

    def test_brightness_control(self):
        ok, msg = smart_home.set_brightness("lab_lights", 65)
        self.assertTrue(ok)
        dev = smart_home.get_device("lab_lights")
        self.assertEqual(dev["brightness"], 65)
        self.assertEqual(dev["state"], "on")
        self.assertIn("65 percent", msg)

    def test_climate_control(self):
        ok, msg = smart_home.set_climate_temperature("main_thermostat", 21.5)
        self.assertTrue(ok)
        dev = smart_home.get_device("main_thermostat")
        self.assertEqual(dev["target_temp"], 21.5)
        self.assertIn("21.5 degrees", msg)

    def test_lock_control(self):
        ok, msg = smart_home.set_lock_state("front_door_lock", locked=False)
        self.assertTrue(ok)
        self.assertEqual(smart_home.get_device("front_door_lock")["state"], "unlocked")
        self.assertIn("unlocked", msg)

        ok, msg = smart_home.set_lock_state("front_door_lock", locked=True)
        self.assertTrue(ok)
        self.assertEqual(smart_home.get_device("front_door_lock")["state"], "locked")
        self.assertIn("secured", msg)

    def test_natural_language_parsing(self):
        # Lights on
        handled, resp = smart_home.parse_and_execute("turn on the workshop lights")
        self.assertTrue(handled)
        self.assertIn("energized", resp)

        # Brightness
        handled, resp = smart_home.parse_and_execute("set lab lights brightness to 50 percent")
        self.assertTrue(handled)
        self.assertEqual(smart_home.get_device("lab_lights")["brightness"], 50)

        # Climate
        handled, resp = smart_home.parse_and_execute("set temperature to 23 degrees")
        self.assertTrue(handled)
        self.assertEqual(smart_home.get_device("main_thermostat")["target_temp"], 23.0)

        # Lock
        handled, resp = smart_home.parse_and_execute("lock front door")
        self.assertTrue(handled)
        self.assertEqual(smart_home.get_device("front_door_lock")["state"], "locked")

        # Status
        handled, resp = smart_home.parse_and_execute("smart home status")
        self.assertTrue(handled)
        self.assertIn("Smart Home & Automation Matrix Telemetry", resp)

    def test_local_intelligence_routing(self):
        handled, resp = self.loc_intel.evaluate_and_execute("turn on lab lights")
        self.assertTrue(handled)
        self.assertIn("energized", resp)

        handled, resp = self.loc_intel.evaluate_and_execute("adjust climate to 22 degrees")
        self.assertTrue(handled)
        self.assertIn("22.0 degrees", resp)

    def test_network_scanner_iot_discovery_hook(self):
        res = network_scanner.scan_iot_devices()
        self.assertIsInstance(res, list)

    def test_web_portal_iot_endpoints(self):
        h_port = find_free_port()
        w_port = find_free_port()
        while w_port == h_port:
            w_port = find_free_port()

        server = WebPortalServer(port=h_port, ws_port=w_port)
        server.start()
        time.sleep(0.3)
        try:
            # Test GET /api/iot
            with urllib.request.urlopen(f"http://127.0.0.1:{h_port}/api/iot", timeout=3) as res:
                self.assertEqual(res.status, 200)
                data = json.loads(res.read().decode("utf-8"))
                self.assertIn("lab_lights", data)

            # Test POST /api/iot/command
            req = urllib.request.Request(
                f"http://127.0.0.1:{h_port}/api/iot/command",
                data=json.dumps({"directive": "turn on ambient reactor"}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=3) as res:
                self.assertEqual(res.status, 200)
                post_data = json.loads(res.read().decode("utf-8"))
                self.assertTrue(post_data.get("handled"))
        finally:
            server.stop()

if __name__ == "__main__":
    unittest.main()
