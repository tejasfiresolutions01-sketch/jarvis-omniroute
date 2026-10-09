import unittest
import urllib.request
import json
import time
import socket
from ui.web_portal import WebPortalServer, get_pwa_icon, get_telemetry_snapshot
import config

try:
    from websockets.sync.client import connect as ws_connect
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False


def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class TestWebPortalSocketsAndPWA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http_port = find_free_port()
        cls.ws_port = find_free_port()
        while cls.ws_port == cls.http_port:
            cls.ws_port = find_free_port()

        cls.portal = WebPortalServer(port=cls.http_port, ws_port=cls.ws_port)
        cls.portal.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.portal.stop()

    def test_pwa_manifest_endpoint(self):
        url = f"http://127.0.0.1:{self.http_port}/manifest.json"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as res:
            self.assertEqual(res.status, 200)
            self.assertIn("application/manifest+json", res.headers.get("Content-Type", ""))
            data = json.loads(res.read().decode("utf-8"))
            self.assertEqual(data.get("short_name"), "J.A.R.V.I.S.")
            self.assertEqual(data.get("display"), "standalone")
            self.assertEqual(data.get("theme_color"), "#00f0ff")
            self.assertGreaterEqual(len(data.get("icons", [])), 2)

    def test_pwa_service_worker_endpoint(self):
        url = f"http://127.0.0.1:{self.http_port}/sw.js"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as res:
            self.assertEqual(res.status, 200)
            self.assertIn("application/javascript", res.headers.get("Content-Type", ""))
            content = res.read().decode("utf-8")
            self.assertIn("CACHE_NAME", content)
            self.assertIn("addEventListener('push'", content)
            self.assertIn("addEventListener('notificationclick'", content)

    def test_pwa_icon_assets(self):
        for size in [192, 512]:
            url = f"http://127.0.0.1:{self.http_port}/assets/icon-{size}.png"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3) as res:
                self.assertEqual(res.status, 200)
                self.assertEqual(res.headers.get("Content-Type"), "image/png")
                raw = res.read()
                self.assertTrue(raw.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_html_portal_shell(self):
        url = f"http://127.0.0.1:{self.http_port}/"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as res:
            self.assertEqual(res.status, 200)
            html = res.read().decode("utf-8")
            self.assertIn('<link rel="manifest" href="/manifest.json">', html)
            self.assertIn('WebSocket', html)
            self.assertIn('Holographic Arc Reactor', html)

    def test_api_status_endpoint(self):
        url = f"http://127.0.0.1:{self.http_port}/api/status"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
            self.assertEqual(data.get("status"), "ONLINE")
            self.assertEqual(data.get("assistant"), config.ASSISTANT_NAME)
            self.assertTrue(data.get("pwa"))

    def test_api_telemetry_endpoint(self):
        url = f"http://127.0.0.1:{self.http_port}/api/telemetry"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
            self.assertIn("cpu_percent", data)
            self.assertIn("ram_percent", data)
            self.assertIn("battery", data)
            self.assertEqual(data.get("status"), "OPTIMAL")

    def test_api_command_backward_compatibility(self):
        url = f"http://127.0.0.1:{self.http_port}/api/command"
        body = json.dumps({"prompt": "system vitals"}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
            self.assertIn("response", data)
            self.assertTrue(len(data["response"]) > 0)

    @unittest.skipUnless(HAS_WEBSOCKETS, "websockets package required for full-duplex tests")
    def test_websocket_handshake_and_ping(self):
        ws_url = f"ws://127.0.0.1:{self.ws_port}"
        with ws_connect(ws_url, close_timeout=2) as ws:
            handshake = json.loads(ws.recv(timeout=3))
            self.assertEqual(handshake.get("type"), "connected")

            ws.send(json.dumps({"action": "ping"}))
            pong = json.loads(ws.recv(timeout=3))
            self.assertEqual(pong.get("type"), "pong")
            self.assertIn("timestamp", pong)

    @unittest.skipUnless(HAS_WEBSOCKETS, "websockets package required for full-duplex tests")
    def test_websocket_command_execution(self):
        ws_url = f"ws://127.0.0.1:{self.ws_port}"
        with ws_connect(ws_url, close_timeout=2) as ws:
            # Drain handshake
            ws.recv(timeout=3)

            cmd_payload = {
                "action": "command",
                "prompt": "system vitals",
                "speak": False,
                "id": "req-999"
            }
            ws.send(json.dumps(cmd_payload))
            resp = json.loads(ws.recv(timeout=5))
            self.assertEqual(resp.get("type"), "response")
            self.assertEqual(resp.get("id"), "req-999")
            self.assertTrue(len(resp.get("response", "")) > 0)

    @unittest.skipUnless(HAS_WEBSOCKETS, "websockets package required for full-duplex tests")
    def test_websocket_broadcast_notification(self):
        ws_url = f"ws://127.0.0.1:{self.ws_port}"
        with ws_connect(ws_url, close_timeout=2) as ws:
            ws.recv(timeout=3) # Handshake

            # Trigger broadcast
            self.portal.broadcast_notification("Security Alert", "Perimeter sensors active.")

            msg = json.loads(ws.recv(timeout=3))
            self.assertEqual(msg.get("type"), "notification")
            self.assertEqual(msg.get("title"), "Security Alert")
            self.assertEqual(msg.get("message"), "Perimeter sensors active.")


if __name__ == "__main__":
    unittest.main()
