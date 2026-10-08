import http.server
import socketserver
import threading
import json
import socket
from typing import Optional
from core.brain import brain
from core.voice import speak
import config

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

HTML_PORTAL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>J.A.R.V.I.S. // STARK QUANTUM HOLOGRAPHIC PORTAL</title>
<style>
  :root {
    --bg: #010612;
    --card: #041126;
    --card-border: #0b2f5c;
    --cyan: #00f0ff;
    --gold: #ffd700;
    --red: #ff2a55;
    --text: #e0f6ff;
    --dim: #3a6899;
    --glow: rgba(0, 240, 255, 0.35);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Consolas', 'Segoe UI', monospace; }
  body {
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    padding: 14px;
    background-image: 
      radial-gradient(circle at 50% 20%, rgba(0, 240, 255, 0.08) 0%, transparent 60%),
      linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
    background-size: 100% 100%, 32px 32px, 32px 32px;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(0,240,255,0.3);
    margin-bottom: 12px;
  }
  .title {
    color: var(--cyan);
    font-size: 1.15rem;
    font-weight: bold;
    letter-spacing: 2px;
    text-shadow: 0 0 10px var(--glow);
  }
  .badge {
    background: rgba(0,240,255,0.1);
    border: 1px solid var(--cyan);
    color: var(--cyan);
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: bold;
    letter-spacing: 1px;
    box-shadow: 0 0 8px var(--glow);
  }
  .hologram-viewport {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 12px;
    position: relative;
  }
  #hologram-canvas {
    background: transparent;
    border-radius: 50%;
    filter: drop-shadow(0 0 12px rgba(0,240,255,0.4));
  }
  .telemetry-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: var(--dim);
    margin-bottom: 8px;
    padding: 0 4px;
  }
  .telemetry-val { color: var(--gold); font-weight: bold; }
  .console {
    flex: 1;
    background: #020b18;
    border: 1px solid var(--card-border);
    border-radius: 6px;
    padding: 12px;
    height: 300px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-size: 0.85rem;
    margin-bottom: 12px;
    box-shadow: inset 0 0 15px rgba(0,0,0,0.8);
  }
  .msg-user {
    color: #fff;
    align-self: flex-end;
    background: rgba(0,240,255,0.15);
    border: 1px solid rgba(0,240,255,0.3);
    padding: 8px 12px;
    border-radius: 6px;
    max-width: 82%;
  }
  .msg-jarvis {
    color: var(--cyan);
    align-self: flex-start;
    background: rgba(4,17,38,0.85);
    border-left: 3px solid var(--cyan);
    border-top: 1px solid var(--card-border);
    border-right: 1px solid var(--card-border);
    border-bottom: 1px solid var(--card-border);
    padding: 8px 12px;
    border-radius: 6px;
    max-width: 88%;
    box-shadow: 0 0 10px rgba(0,240,255,0.1);
  }
  .input-bar { display: flex; gap: 8px; margin-bottom: 10px; }
  input[type="text"] {
    flex: 1;
    background: #04142d;
    border: 1px solid var(--card-border);
    color: #fff;
    padding: 12px 14px;
    border-radius: 4px;
    font-size: 0.95rem;
    outline: none;
    transition: all 0.2s;
  }
  input[type="text"]:focus {
    border-color: var(--cyan);
    box-shadow: 0 0 12px var(--glow);
  }
  button {
    background: #051a3b;
    color: var(--cyan);
    border: 1px solid var(--cyan);
    padding: 12px 18px;
    border-radius: 4px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s;
    letter-spacing: 1px;
  }
  button:hover {
    background: var(--cyan);
    color: #000;
    box-shadow: 0 0 12px var(--glow);
  }
  .quick-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
  .q-btn {
    font-size: 0.75rem;
    padding: 10px 4px;
    text-align: center;
    background: #041126;
    border: 1px solid var(--card-border);
    color: var(--text);
  }
  .q-btn:hover { border-color: var(--gold); color: var(--gold); }
</style>
</head>
<body>
<header>
  <div class="title">⫸ J.A.R.V.I.S. // QUANTUM HUD</div>
  <div class="badge" id="mode-badge">MK-LXXXV ARMED</div>
</header>

<div class="hologram-viewport">
  <canvas id="hologram-canvas" width="220" height="220"></canvas>
</div>

<div class="telemetry-row">
  <div>STATUS: <span class="telemetry-val" id="tel-status">OPTIMAL</span></div>
  <div>DEFENSE: <span class="telemetry-val">ASIMOV ENFORCED</span></div>
  <div>UPLINK: <span class="telemetry-val">0.8ms</span></div>
</div>

<div class="console" id="console">
  <div class="msg-jarvis">[J.A.R.V.I.S. Mark-LXXXV]: Quantum holographic core synchronized. Standing ready for your directive, sir.</div>
</div>

<div class="input-bar">
  <input type="text" id="cmd-input" placeholder="Directive, sir (or 'what is my schedule?')..." autofocus />
  <button id="send-btn" onclick="sendCommand()">⚡ TRANSMIT</button>
  <button onclick="toggleVoice()" id="mic-btn" style="border-color: var(--gold); color: var(--gold);">🎤</button>
</div>

<div class="quick-grid">
  <button class="q-btn" onclick="quickSend('daily briefing')">📋 Briefing</button>
  <button class="q-btn" onclick="quickSend('what is on my schedule today')">📅 Schedule</button>
  <button class="q-btn" onclick="quickSend('system vitals')">⚡ Vitals</button>
  <button class="q-btn" onclick="quickSend('lock my device')">🔒 Lock</button>
</div>

<script>
  // ── Holographic Arc Reactor Canvas Animation ──
  const canvas = document.getElementById('hologram-canvas');
  const ctx = canvas.getContext('2d');
  let angle = 0;

  function renderHologram() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    angle += 0.025;

    // Outer Segmented Ring
    ctx.strokeStyle = '#00f0ff';
    ctx.lineWidth = 2;
    for (let i = 0; i < 6; i++) {
      ctx.beginPath();
      const start = angle * 0.8 + (i * Math.PI / 3);
      ctx.arc(cx, cy, 85, start, start + 0.35);
      ctx.stroke();
    }

    // Concentric Gyroscopic Ellipse
    ctx.strokeStyle = '#ffd700';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.ellipse(cx, cy, 96, 35 + Math.sin(angle * 1.2) * 10, angle * 0.5, 0, Math.PI * 2);
    ctx.stroke();

    // Inner Counter-Rotating Ring
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.6)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx, cy, 60, 0, Math.PI * 2);
    ctx.stroke();

    // Spokes
    ctx.strokeStyle = '#00f0ff';
    ctx.lineWidth = 1.5;
    for (let i = 0; i < 8; i++) {
      const a = -angle * 1.5 + (i * Math.PI / 4);
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(a) * 20, cy + Math.sin(a) * 20);
      ctx.lineTo(cx + Math.cos(a) * 58, cy + Math.sin(a) * 58);
      ctx.stroke();
    }

    // Singularity Core
    const pulse = Math.sin(angle * 3) * 3;
    const grad = ctx.createRadialGradient(cx, cy, 2, cx, cy, 18 + pulse);
    grad.addColorStop(0, '#ffffff');
    grad.addColorStop(0.4, '#00f0ff');
    grad.addColorStop(1, 'transparent');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(cx, cy, 18 + pulse, 0, Math.PI * 2);
    ctx.fill();

    requestAnimationFrame(renderHologram);
  }
  renderHologram();

  // ── Console & Communication ──
  const consoleBox = document.getElementById('console');
  const input = document.getElementById('cmd-input');
  input.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendCommand(); });

  function appendMsg(text, type) {
    const el = document.createElement('div');
    el.className = type === 'user' ? 'msg-user' : 'msg-jarvis';
    el.innerText = text;
    consoleBox.appendChild(el);
    consoleBox.scrollTop = consoleBox.scrollHeight;
  }

  async function sendCommand() {
    const val = input.value.trim();
    if (!val) return;
    appendMsg(val, 'user');
    input.value = '';
    try {
      const res = await fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: val })
      });
      const data = await res.json();
      appendMsg(data.response || 'Directive acknowledged, sir.', 'jarvis');
    } catch (e) {
      appendMsg('Connection anomaly, sir. Ensure J.A.R.V.I.S. host is reachable.', 'jarvis');
    }
  }

  function quickSend(cmd) {
    input.value = cmd;
    sendCommand();
  }

  function toggleVoice() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in this browser.');
      return;
    }
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SpeechRec();
    rec.onresult = (e) => {
      input.value = e.results[0][0].transcript;
      sendCommand();
    };
    rec.start();
  }
</script>
</body>
</html>
"""

class PortalHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PORTAL.encode("utf-8"))
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ONLINE", "assistant": config.ASSISTANT_NAME}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/command":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode("utf-8"))
                # Robust key extraction: prompt, command, text, query
                prompt = data.get("prompt") or data.get("command") or data.get("text") or data.get("query") or ""
                response_text = brain.think(prompt)
                threading.Thread(target=speak, args=(response_text,), daemon=True).start()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"response": response_text}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

class WebPortalServer:
    def __init__(self, port: int = config.WEB_PORTAL_PORT):
        self.port = port
        self.ip = get_local_ip()
        self.server: Optional[socketserver.TCPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        socketserver.TCPServer.allow_reuse_address = True
        try:
            self.server = socketserver.TCPServer(("0.0.0.0", self.port), PortalHandler)
            self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self._thread.start()
            print(f"[Web Portal]: Online at http://localhost:{self.port} (Network: http://{self.ip}:{self.port})")
        except Exception as e:
            print(f"[Web Portal Warning]: Unable to bind port {self.port}: {e}")

    def stop(self):
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass

web_portal = WebPortalServer()
