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
<title>J.A.R.V.I.S. // MOBILE COMMAND PORTAL</title>
<style>
  :root {
    --bg: #030811;
    --card: #08152b;
    --cyan: #00e5ff;
    --gold: #d4af37;
    --red: #ff3344;
    --text: #e0f4ff;
    --dim: #4a6fa5;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
  body { background: var(--bg); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; padding: 16px; }
  header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 16px; border-bottom: 1px solid rgba(0,229,255,0.2); margin-bottom: 16px; }
  .title { color: var(--cyan); font-size: 1.2rem; font-weight: bold; letter-spacing: 2px; }
  .badge { background: rgba(0,229,255,0.1); border: 1px solid var(--cyan); color: var(--cyan); padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; }
  .console { flex: 1; background: #02050a; border: 1px solid rgba(0,229,255,0.2); border-radius: 8px; padding: 14px; height: 350px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; font-size: 0.9rem; margin-bottom: 16px; }
  .msg-user { color: #fff; align-self: flex-end; background: rgba(0,229,255,0.15); padding: 8px 12px; border-radius: 8px; max-width: 80%; }
  .msg-jarvis { color: var(--cyan); align-self: flex-start; background: rgba(8,21,43,0.8); border-left: 3px solid var(--cyan); padding: 8px 12px; border-radius: 8px; max-width: 85%; }
  .input-bar { display: flex; gap: 8px; margin-bottom: 12px; }
  input[type="text"] { flex: 1; background: #091933; border: 1px solid var(--dim); color: #fff; padding: 12px 14px; border-radius: 6px; font-size: 1rem; outline: none; }
  input[type="text"]:focus { border-color: var(--cyan); box-shadow: 0 0 10px rgba(0,229,255,0.3); }
  button { background: #0c2347; color: var(--cyan); border: 1px solid var(--cyan); padding: 12px 18px; border-radius: 6px; font-weight: bold; cursor: pointer; transition: all 0.2s; }
  button:hover { background: var(--cyan); color: #000; }
  .quick-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
  .q-btn { font-size: 0.8rem; padding: 10px 4px; text-align: center; }
</style>
</head>
<body>
<header>
  <div class="title">◆ J.A.R.V.I.S. BUTLER ◆</div>
  <div class="badge" id="mode-badge">OFFLINE / ONLINE READY</div>
</header>
<div class="console" id="console">
  <div class="msg-jarvis">J.A.R.V.I.S. Mark-III online, sir. Standing ready for your directive or schedule inquiry.</div>
</div>
<div class="input-bar">
  <input type="text" id="cmd-input" placeholder="Directive, sir (or 'what is my schedule?')..." autofocus />
  <button id="send-btn" onclick="sendCommand()">TRANSMIT</button>
  <button onclick="toggleVoice()" id="mic-btn" style="border-color: #d4af37; color: #d4af37;">🎤</button>
</div>
<div class="quick-grid">
  <button class="q-btn" onclick="quickSend('daily briefing')">📋 Briefing</button>
  <button class="q-btn" onclick="quickSend('what is on my schedule today')">📅 Schedule</button>
  <button class="q-btn" onclick="quickSend('system vitals')">⚡ Vitals</button>
  <button class="q-btn" onclick="quickSend('open notepad')">📝 Notepad</button>
</div>
<script>
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
