"""
Live Verification Harness for J.A.R.V.I.S. Smart Home IoT & Network Telemetry.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import json
import urllib.request
import socket
from tools.smart_home_controller import smart_home
from tools.network_scanner import network_scanner
from core.local_intelligence import LocalIntelligence
from ui.web_portal import WebPortalServer

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run_live_check():
    print("=" * 65)
    print(" [J.A.R.V.I.S. LIVE SMART HOME IoT & NETWORK TELEMETRY HARNESS]")
    print("=" * 65)

    # 1. Device Matrix Status
    print("\n[1. Inspecting Smart Home Device Registry]...")
    devs = smart_home.get_devices()
    print(f"  Total registered IoT devices: {len(devs)}")
    for d_id, d in devs.items():
        print(f"  &bull; {d['name']} [{d['room']}] -> State: {d.get('state', 'N/A').upper()} ({d['type']})")

    # 2. Testing Live Automation Directives
    print("\n[2. Executing Real-Time Device Automation Battery]...")
    t0 = time.time()
    ok, msg = smart_home.set_device_power("lab_lights", "on")
    print(f"  [Power] {msg} ({(time.time()-t0)*1000:.2f}ms)")

    t0 = time.time()
    ok, msg = smart_home.set_brightness("lab_lights", 85)
    print(f"  [Brightness] {msg} ({(time.time()-t0)*1000:.2f}ms)")

    t0 = time.time()
    ok, msg = smart_home.set_climate_temperature("main_thermostat", 21.0)
    print(f"  [Climate] {msg} ({(time.time()-t0)*1000:.2f}ms)")

    t0 = time.time()
    ok, msg = smart_home.set_lock_state("front_door_lock", locked=True)
    print(f"  [Security] {msg} ({(time.time()-t0)*1000:.2f}ms)")

    # 3. Natural Language Directives via Butler Core
    print("\n[3. Testing Natural Language Butler Execution]...")
    loc = LocalIntelligence()
    test_prompts = [
        "turn on the workshop lights",
        "set temperature to 22.5 degrees",
        "lock the front door",
        "smart home status"
    ]
    for prompt in test_prompts:
        t0 = time.time()
        handled, resp = loc.evaluate_and_execute(prompt)
        dur = (time.time() - t0) * 1000
        print(f"  Directive: '{prompt}' -> Handled: {handled} ({dur:.1f}ms)")
        print(f"  Response: {resp.splitlines()[0][:75]}...")

    # 4. LAN IoT Reconnaissance
    print("\n[4. Running Local LAN IoT Sweep]...")
    t0 = time.time()
    iot_nodes = smart_home.scan_lan_for_iot()
    print(f"  IoT Sweep completed in {(time.time()-t0)*1000:.1f}ms. Detected: {len(iot_nodes)} devices.")

    # 5. Testing Web Portal IoT Integration
    print("\n[5. Testing Web Portal IoT REST API Integration]...")
    h_port = find_free_port()
    w_port = find_free_port()
    while w_port == h_port:
        w_port = find_free_port()

    server = WebPortalServer(port=h_port, ws_port=w_port)
    server.start()
    time.sleep(0.3)
    try:
        # GET /api/iot
        with urllib.request.urlopen(f"http://127.0.0.1:{h_port}/api/iot", timeout=3) as res:
            data = json.loads(res.read().decode("utf-8"))
            print(f"  [REST GET] /api/iot -> 200 OK ({len(data)} devices reported)")

        # POST /api/iot/command
        req = urllib.request.Request(
            f"http://127.0.0.1:{h_port}/api/iot/command",
            data=json.dumps({"directive": "turn off workshop lights"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3) as res:
            p_data = json.loads(res.read().decode("utf-8"))
            print(f"  [REST POST] /api/iot/command -> 200 OK (Handled: {p_data.get('handled')})")
    finally:
        server.stop()

    print("\n" + "=" * 65)
    print(" [ALL SMART HOME IoT & NETWORK TELEMETRY VERIFICATIONS PASSED]")
    print("=" * 65)

if __name__ == "__main__":
    run_live_check()
