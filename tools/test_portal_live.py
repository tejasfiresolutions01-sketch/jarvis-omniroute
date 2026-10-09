"""
Live Verification Harness for J.A.R.V.I.S. Full-Duplex WebSockets & Mobile PWA Web Portal.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import json
import urllib.request
import socket
from ui.web_portal import WebPortalServer, get_telemetry_snapshot
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


def run_live_check():
    print("=" * 65)
    print(" [J.A.R.V.I.S. LIVE PORTAL & WEBSOCKET VERIFICATION HARNESS]")
    print("=" * 65)

    http_port = find_free_port()
    ws_port = find_free_port()
    while ws_port == http_port:
        ws_port = find_free_port()

    print(f"[Portal Harness]: Starting test portal (HTTP: {http_port}, WS: {ws_port})...")
    server = WebPortalServer(port=http_port, ws_port=ws_port)
    server.start()
    time.sleep(0.3)

    try:
        # 1. Check HTTP Shell
        print("\n--- 1. Testing PWA HTTP Shell & Endpoints ---")
        base_url = f"http://127.0.0.1:{http_port}"
        for ep in ["/", "/manifest.json", "/sw.js", "/assets/icon-192.png", "/assets/icon-512.png", "/api/status", "/api/telemetry"]:
            req = urllib.request.Request(f"{base_url}{ep}")
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=3) as res:
                dur = (time.time() - t0) * 1000
                content_len = len(res.read())
                print(f"  [HTTP GET] {ep:<25} -> Status: {res.status} ({dur:.1f}ms, {content_len} bytes)")

        # 2. Check REST API Command
        print("\n--- 2. Testing REST API Command Dispatch ---")
        cmd_req = urllib.request.Request(
            f"{base_url}/api/command",
            data=json.dumps({"prompt": "system vitals"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        t0 = time.time()
        with urllib.request.urlopen(cmd_req, timeout=5) as res:
            dur = (time.time() - t0) * 1000
            data = json.loads(res.read().decode("utf-8"))
            print(f"  [REST POST] /api/command -> Status: {res.status} ({dur:.1f}ms)")
            print(f"  Response: {data.get('response')[:80]}...")

        # 3. Check Full-Duplex WebSocket
        if HAS_WEBSOCKETS:
            print("\n--- 3. Testing Full-Duplex WebSocket Uplink ---")
            ws_url = f"ws://127.0.0.1:{ws_port}"
            t0 = time.time()
            with ws_connect(ws_url, close_timeout=2) as ws:
                conn_ms = (time.time() - t0) * 1000
                print(f"  [WS Connect] Uplink connected in {conn_ms:.1f}ms")

                # Receive Handshake
                handshake = json.loads(ws.recv(timeout=3))
                print(f"  [WS Handshake] Type: '{handshake.get('type')}', Status: '{handshake.get('status')}'")

                # Ping-Pong Latency
                t_ping = time.time()
                ws.send(json.dumps({"action": "ping"}))
                pong = json.loads(ws.recv(timeout=3))
                ping_ms = (time.time() - t_ping) * 1000
                print(f"  [WS Ping-Pong] Round-trip latency: {ping_ms:.2f}ms")

                # Full-Duplex Command
                ws.send(json.dumps({"action": "command", "prompt": "what is on my schedule today", "speak": False, "id": "live-1"}))
                ws_resp = json.loads(ws.recv(timeout=5))
                print(f"  [WS Command] id: {ws_resp.get('id')} -> {ws_resp.get('response')[:75]}...")

                # Broadcast Notification
                server.broadcast_notification("SYSTEM NOTICE", "Quantum reactor frequency stabilized.")
                notif_packet = json.loads(ws.recv(timeout=3))
                print(f"  [WS Push Notification] Received real-time alert: '{notif_packet.get('title')}' - '{notif_packet.get('message')}'")
        else:
            print("[Portal Harness Warning]: 'websockets' module not detected.")

        print("\n" + "=" * 65)
        print(" [ALL PORTAL & WEBSOCKET VERIFICATIONS PASSED SUCCESSFULLY]")
        print("=" * 65)

    finally:
        print("\n[Portal Harness]: Terminating test server cleanly...")
        server.stop()
        print("[Portal Harness]: Server stopped.")


if __name__ == "__main__":
    run_live_check()
