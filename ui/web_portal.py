import http.server
import socketserver
import threading
import json
import socket
import io
import time
import datetime
from typing import Optional, Set
from core.brain import brain
from core.voice import speak
import config

try:
    import psutil
except ImportError:
    psutil = None

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image, ImageDraw = None, None

try:
    from websockets.sync.server import serve as ws_serve, ServerConnection
    from websockets.exceptions import ConnectionClosed
except ImportError:
    ws_serve = None
    ServerConnection = None
    ConnectionClosed = Exception

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

_ICON_CACHE = {}

def get_pwa_icon(size: int = 192) -> bytes:
    """Generates and caches high-definition Stark Arc Reactor PNG icon for PWA."""
    if size in _ICON_CACHE:
        return _ICON_CACHE[size]
    
    if Image and ImageDraw:
        img = Image.new("RGBA", (size, size), (1, 6, 18, 255))
        draw = ImageDraw.Draw(img)
        cx, cy = size // 2, size // 2
        r_outer = int(size * 0.42)
        r_mid = int(size * 0.30)
        r_inner = int(size * 0.16)

        # Outer cyan glow ring
        draw.ellipse((cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer),
                     outline=(0, 240, 255, 255), width=max(2, size // 35))
        # Mid gold ring
        draw.ellipse((cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid),
                     outline=(255, 215, 0, 230), width=max(1, size // 55))
        # Inner reactor core
        draw.ellipse((cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner),
                     fill=(0, 240, 255, 255))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        icon_bytes = buf.getvalue()
    else:
        # Minimal 1x1 transparent fallback PNG
        icon_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\r\xefU\xb5\x00\x00\x00\x00IEND\xaeB`\x82'
    
    _ICON_CACHE[size] = icon_bytes
    return icon_bytes

def get_telemetry_snapshot() -> dict:
    """Fetches real-time system vitals and J.A.R.V.I.S. operating telemetry."""
    cpu = 0.0
    mem = 0.0
    batt = "AC POWER (OPTIMAL)"
    if psutil:
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            b = psutil.sensors_battery()
            if b:
                charging = " [Charging]" if b.power_plugged else ""
                batt = f"{b.percent:.0f}%{charging}"
        except Exception:
            pass
    return {
        "status": "OPTIMAL",
        "assistant": config.ASSISTANT_NAME,
        "cpu_percent": cpu,
        "ram_percent": mem,
        "battery": batt,
        "protocol": "ASIMOV ENFORCED",
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "uplink_latency_ms": 0.4
    }

MANIFEST_JSON = json.dumps({
    "name": "J.A.R.V.I.S. // STARK QUANTUM PORTAL",
    "short_name": "J.A.R.V.I.S.",
    "start_url": "/",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#010612",
    "theme_color": "#00f0ff",
    "description": "Tactical Quantum Holographic Mobile Controller for J.A.R.V.I.S. Mark-LXXXV",
    "icons": [
        {
            "src": "/assets/icon-192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any maskable"
        },
        {
            "src": "/assets/icon-512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any maskable"
        }
    ]
}, indent=2)

SERVICE_WORKER_JS = """// J.A.R.V.I.S. Tactical Service Worker (PWA Offline Shell & Push Notifications)
const CACHE_NAME = 'jarvis-pwa-v2';
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/assets/icon-192.png',
  '/assets/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_ASSETS).catch(() => {}))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
    self.registration.showNotification(event.data.title || 'J.A.R.V.I.S. Priority Alert', {
      body: event.data.body || 'Alert directive received.',
      icon: '/assets/icon-192.png',
      badge: '/assets/icon-192.png',
      vibrate: [200, 100, 200],
      tag: 'jarvis-pwa-alert',
      renotify: true
    });
  }
});

self.addEventListener('push', (event) => {
  let payload = { title: 'J.A.R.V.I.S. Alert', body: 'New directive from host system.' };
  if (event.data) {
    try { payload = event.data.json(); } catch(err) { payload.body = event.data.text(); }
  }
  event.waitUntil(
    self.registration.showNotification(payload.title, {
      body: payload.body || payload.message,
      icon: '/assets/icon-192.png',
      badge: '/assets/icon-192.png',
      vibrate: [250, 120, 250]
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ('focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow('/');
    })
  );
});
"""

HTML_PORTAL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#00f0ff">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="J.A.R.V.I.S.">
<link rel="manifest" href="/manifest.json">
<link rel="apple-touch-icon" href="/assets/icon-192.png">
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
    padding: 12px;
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
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(0,240,255,0.3);
    margin-bottom: 10px;
  }
  .title {
    color: var(--cyan);
    font-size: 1.05rem;
    font-weight: bold;
    letter-spacing: 2px;
    text-shadow: 0 0 10px var(--glow);
  }
  .header-actions { display: flex; align-items: center; gap: 8px; }
  .badge {
    background: rgba(0,240,255,0.1);
    border: 1px solid var(--cyan);
    color: var(--cyan);
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: bold;
    letter-spacing: 1px;
    box-shadow: 0 0 8px var(--glow);
    transition: all 0.3s ease;
  }
  .icon-btn {
    background: transparent;
    border: 1px solid var(--dim);
    color: var(--text);
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  .icon-btn:hover { border-color: var(--cyan); color: var(--cyan); }
  .hologram-viewport {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 8px;
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
    font-size: 0.72rem;
    color: var(--dim);
    margin-bottom: 8px;
    padding: 0 4px;
    flex-wrap: wrap;
    gap: 4px;
  }
  .telemetry-val { color: var(--gold); font-weight: bold; }
  .pwa-banner {
    display: none;
    background: rgba(0, 240, 255, 0.12);
    border: 1px solid var(--cyan);
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 8px;
    justify-content: space-between;
    align-items: center;
    font-size: 0.8rem;
    color: var(--cyan);
  }
  .pwa-banner button {
    padding: 4px 10px;
    font-size: 0.75rem;
  }
  .console {
    flex: 1;
    background: #020b18;
    border: 1px solid var(--card-border);
    border-radius: 6px;
    padding: 10px;
    height: 280px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-size: 0.85rem;
    margin-bottom: 10px;
    box-shadow: inset 0 0 15px rgba(0,0,0,0.8);
  }
  .msg-user {
    color: #fff;
    align-self: flex-end;
    background: rgba(0,240,255,0.15);
    border: 1px solid rgba(0,240,255,0.3);
    padding: 8px 12px;
    border-radius: 6px;
    max-width: 85%;
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
  .msg-alert {
    color: var(--gold);
    align-self: stretch;
    background: rgba(255, 215, 0, 0.08);
    border-left: 3px solid var(--gold);
    border: 1px solid rgba(255, 215, 0, 0.3);
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.82rem;
    box-shadow: 0 0 10px rgba(255, 215, 0, 0.15);
  }
  .input-bar { display: flex; gap: 8px; margin-bottom: 8px; }
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
  .quick-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
  .q-btn {
    font-size: 0.72rem;
    padding: 9px 3px;
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
  <div class="header-actions">
    <button class="icon-btn" id="notif-btn" onclick="requestPushPermission()" title="Enable Mobile PWA Push">🔔</button>
    <div class="badge" id="mode-badge">MK-LXXXV ARMED</div>
  </div>
</header>

<div class="pwa-banner" id="pwa-banner">
  <span>📲 Install J.A.R.V.I.S. as Standalone Mobile App</span>
  <button onclick="installPWA()">INSTALL</button>
</div>

<div class="hologram-viewport">
  <canvas id="hologram-canvas" width="220" height="220"></canvas>
</div>

<div class="telemetry-row">
  <div>STATUS: <span class="telemetry-val" id="tel-status">OPTIMAL</span></div>
  <div>CPU: <span class="telemetry-val" id="tel-cpu">--%</span></div>
  <div>RAM: <span class="telemetry-val" id="tel-ram">--%</span></div>
  <div>UPLINK: <span class="telemetry-val" id="tel-uplink">WS CONNECTING</span></div>
</div>

<div class="console" id="console">
  <div class="msg-jarvis">[J.A.R.V.I.S. Mark-LXXXV]: Quantum holographic core synchronized. Full-Duplex neural uplink active. Standing ready, sir.</div>
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
  // ── PWA & Service Worker Registration ──
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').then((reg) => {
      console.log('[PWA]: ServiceWorker registered with scope:', reg.scope);
    }).catch((err) => {
      console.warn('[PWA]: ServiceWorker registration error:', err);
    });
  }

  let deferredInstallPrompt = null;
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    const banner = document.getElementById('pwa-banner');
    if (banner) banner.style.display = 'flex';
  });

  function installPWA() {
    if (deferredInstallPrompt) {
      deferredInstallPrompt.prompt();
      deferredInstallPrompt.userChoice.then(() => {
        deferredInstallPrompt = null;
        const banner = document.getElementById('pwa-banner');
        if (banner) banner.style.display = 'none';
      });
    }
  }

  function requestPushPermission() {
    if (!('Notification' in window)) {
      alert('System notifications are not supported on this browser.');
      return;
    }
    Notification.requestPermission().then((permission) => {
      if (permission === 'granted') {
        appendAlert('Mobile PWA and desktop notifications authorized, sir.');
        playStarkChime();
      }
    });
  }

  // ── Sci-Fi Audio Synthesizer (Zero External Assets) ──
  function playStarkChime() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();

      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(880, ctx.currentTime);
      osc1.frequency.exponentialRampToValueAtTime(1760, ctx.currentTime + 0.15);

      osc2.type = 'triangle';
      osc2.frequency.setValueAtTime(1320, ctx.currentTime);
      osc2.frequency.exponentialRampToValueAtTime(2640, ctx.currentTime + 0.15);

      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ctx.destination);

      osc1.start();
      osc2.start();
      osc1.stop(ctx.currentTime + 0.25);
      osc2.stop(ctx.currentTime + 0.25);
    } catch(e) {}
  }

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

  function appendAlert(text) {
    const el = document.createElement('div');
    el.className = 'msg-alert';
    el.innerText = '⫸ [STARK NOTIFICATION]: ' + text;
    consoleBox.appendChild(el);
    consoleBox.scrollTop = consoleBox.scrollHeight;
  }

  // ── Full-Duplex WebSocket Engine ──
  let ws = null;
  let wsConnected = false;
  const wsPort = 5051;

  function initWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${location.hostname}:${wsPort}`;

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        wsConnected = true;
        const badge = document.getElementById('mode-badge');
        badge.innerText = 'MK-LXXXV // WS FULL-DUPLEX';
        badge.style.borderColor = 'var(--cyan)';
        badge.style.color = 'var(--cyan)';
        document.getElementById('tel-uplink').innerText = '0.4ms (WS)';
        // Subscribe to live telemetry
        ws.send(JSON.stringify({ action: 'subscribe_telemetry' }));
      };

      ws.onmessage = (event) => {
        try {
          const packet = JSON.parse(event.data);
          handleWebSocketMessage(packet);
        } catch(e) {}
      };

      ws.onclose = () => {
        wsConnected = false;
        const badge = document.getElementById('mode-badge');
        badge.innerText = 'MK-LXXXV // HTTP FALLBACK';
        badge.style.borderColor = 'var(--gold)';
        badge.style.color = 'var(--gold)';
        document.getElementById('tel-uplink').innerText = 'REST (POLL)';
        setTimeout(initWebSocket, 4000);
      };

      ws.onerror = () => {
        if (ws) ws.close();
      };
    } catch(err) {
      wsConnected = false;
    }
  }

  function handleWebSocketMessage(packet) {
    if (packet.type === 'response') {
      appendMsg(packet.response || 'Directive executed, sir.', 'jarvis');
      playStarkChime();
    } else if (packet.type === 'notification' || packet.type === 'alert') {
      const msg = packet.message || packet.data || 'Notification received.';
      appendAlert(msg);
      playStarkChime();
      if (Notification && Notification.permission === 'granted') {
        if (navigator.serviceWorker && navigator.serviceWorker.controller) {
          navigator.serviceWorker.controller.postMessage({
            type: 'SHOW_NOTIFICATION',
            title: packet.title || 'J.A.R.V.I.S. Alert',
            body: msg
          });
        } else {
          new Notification(packet.title || 'J.A.R.V.I.S. Alert', { body: msg, icon: '/assets/icon-192.png' });
        }
      }
    } else if (packet.type === 'telemetry') {
      const d = packet.data || {};
      if (d.cpu_percent !== undefined) document.getElementById('tel-cpu').innerText = `${d.cpu_percent}%`;
      if (d.ram_percent !== undefined) document.getElementById('tel-ram').innerText = `${d.ram_percent}%`;
      if (d.status) document.getElementById('tel-status').innerText = d.status;
    }
  }

  initWebSocket();

  // ── Directive Transmission (WebSocket with Seamless REST Fallback) ──
  async function sendCommand() {
    const val = input.value.trim();
    if (!val) return;
    appendMsg(val, 'user');
    input.value = '';

    if (wsConnected && ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'command', prompt: val, speak: true }));
      return;
    }

    // HTTP Fallback
    try {
      const res = await fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: val })
      });
      const data = await res.json();
      appendMsg(data.response || 'Directive acknowledged, sir.', 'jarvis');
      playStarkChime();
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
        elif self.path == "/manifest.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/manifest+json; charset=utf-8")
            self.end_headers()
            self.wfile.write(MANIFEST_JSON.encode("utf-8"))
        elif self.path == "/sw.js":
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.end_headers()
            self.wfile.write(SERVICE_WORKER_JS.encode("utf-8"))
        elif self.path == "/assets/icon-192.png":
            icon_data = get_pwa_icon(192)
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(icon_data)))
            self.end_headers()
            self.wfile.write(icon_data)
        elif self.path == "/assets/icon-512.png":
            icon_data = get_pwa_icon(512)
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(icon_data)))
            self.end_headers()
            self.wfile.write(icon_data)
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            status_payload = {
                "status": "ONLINE",
                "assistant": config.ASSISTANT_NAME,
                "ws_port": getattr(config, "WEB_PORTAL_WS_PORT", 5051),
                "pwa": True
            }
            self.wfile.write(json.dumps(status_payload).encode("utf-8"))
        elif self.path == "/api/telemetry":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_telemetry_snapshot()).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/command":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode("utf-8"))
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
        elif self.path == "/api/notify":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode("utf-8"))
                title = data.get("title", "J.A.R.V.I.S. Alert")
                message = data.get("message", "")
                web_portal.broadcast_notification(title, message)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "broadcast_dispatched"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

class WebPortalServer:
    def __init__(self, port: int = config.WEB_PORTAL_PORT, ws_port: int = getattr(config, "WEB_PORTAL_WS_PORT", 5051)):
        self.port = port
        self.ws_port = ws_port
        self.ip = get_local_ip()
        self.server: Optional[socketserver.TCPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._ws_server = None
        self._ws_thread: Optional[threading.Thread] = None
        self._ws_clients: Set = set()
        self._ws_telemetry_subscribers: Set = set()
        self._ws_lock = threading.Lock()
        self._running = False
        self._telemetry_thread: Optional[threading.Thread] = None

    def start(self):
        socketserver.TCPServer.allow_reuse_address = True
        self._running = True

        # 1. Launch HTTP Server
        try:
            self.server = socketserver.TCPServer(("0.0.0.0", self.port), PortalHandler)
            self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self._thread.start()
            print(f"[Web Portal]: Online at http://localhost:{self.port} (Network: http://{self.ip}:{self.port})")
        except Exception as e:
            print(f"[Web Portal Warning]: Unable to bind HTTP port {self.port}: {e}")

        # 2. Launch Full-Duplex WebSocket Server
        if ws_serve:
            try:
                self._ws_server = ws_serve(self._handle_ws_client, "0.0.0.0", self.ws_port)
                self._ws_thread = threading.Thread(target=self._ws_server.serve_forever, daemon=True)
                self._ws_thread.start()
                print(f"[Web Portal WS]: Full-Duplex WebSocket online on port {self.ws_port}")
            except Exception as e:
                print(f"[Web Portal WS Warning]: Unable to bind WebSocket port {self.ws_port}: {e}")
        else:
            print("[Web Portal WS]: 'websockets' library unavailable. Continuing with HTTP fallback.")

        # 3. Launch Telemetry Streamer Thread
        self._telemetry_thread = threading.Thread(target=self._telemetry_broadcast_loop, daemon=True)
        self._telemetry_thread.start()

    def _handle_ws_client(self, websocket):
        with self._ws_lock:
            self._ws_clients.add(websocket)
        try:
            # Handshake greeting
            websocket.send(json.dumps({
                "type": "connected",
                "message": "J.A.R.V.I.S. Full-Duplex WebSocket Uplink Synchronized.",
                "status": "ONLINE",
                "assistant": config.ASSISTANT_NAME
            }))

            for raw_msg in websocket:
                try:
                    payload = json.loads(raw_msg)
                    action = payload.get("action", "command")
                    req_id = payload.get("id", "")

                    if action == "command":
                        prompt = payload.get("prompt") or payload.get("command") or payload.get("text") or ""
                        resp = brain.think(prompt)
                        if payload.get("speak", True):
                            threading.Thread(target=speak, args=(resp,), daemon=True).start()
                        websocket.send(json.dumps({
                            "type": "response",
                            "id": req_id,
                            "response": resp
                        }))
                    elif action == "subscribe_telemetry":
                        with self._ws_lock:
                            self._ws_telemetry_subscribers.add(websocket)
                        websocket.send(json.dumps({
                            "type": "telemetry",
                            "data": get_telemetry_snapshot()
                        }))
                    elif action == "telemetry":
                        websocket.send(json.dumps({
                            "type": "telemetry",
                            "data": get_telemetry_snapshot()
                        }))
                    elif action == "ping":
                        websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": time.time()
                        }))
                except Exception as inner_e:
                    websocket.send(json.dumps({"type": "error", "error": str(inner_e)}))
        except (ConnectionClosed, Exception):
            pass
        finally:
            with self._ws_lock:
                self._ws_clients.discard(websocket)
                self._ws_telemetry_subscribers.discard(websocket)

    def _telemetry_broadcast_loop(self):
        while self._running:
            time.sleep(2.0)
            with self._ws_lock:
                if not self._ws_telemetry_subscribers:
                    continue
                subscribers = list(self._ws_telemetry_subscribers)
            
            telemetry_data = json.dumps({
                "type": "telemetry",
                "data": get_telemetry_snapshot()
            })

            dead = []
            for client in subscribers:
                try:
                    client.send(telemetry_data)
                except Exception:
                    dead.append(client)
            
            if dead:
                with self._ws_lock:
                    for d in dead:
                        self._ws_clients.discard(d)
                        self._ws_telemetry_subscribers.discard(d)

    def broadcast_event(self, event_type: str, data: dict):
        """Broadcasts real-time events to all connected clients."""
        payload = json.dumps({"type": event_type, "data": data})
        with self._ws_lock:
            clients = list(self._ws_clients)
        dead = []
        for c in clients:
            try:
                c.send(payload)
            except Exception:
                dead.append(c)
        if dead:
            with self._ws_lock:
                for d in dead:
                    self._ws_clients.discard(d)
                    self._ws_telemetry_subscribers.discard(d)

    def broadcast_notification(self, title: str, message: str):
        """Pushes real-time alerts to all connected browsers and PWA devices."""
        payload = json.dumps({"type": "notification", "title": title, "message": message})
        with self._ws_lock:
            clients = list(self._ws_clients)
        dead = []
        for c in clients:
            try:
                c.send(payload)
            except Exception:
                dead.append(c)
        if dead:
            with self._ws_lock:
                for d in dead:
                    self._ws_clients.discard(d)
                    self._ws_telemetry_subscribers.discard(d)

    def is_running(self) -> bool:
        return self._running

    def stop(self):
        self._running = False
        if self._ws_server:
            try:
                self._ws_server.shutdown()
            except Exception:
                pass
            self._ws_server = None
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass
            self.server = None

web_portal = WebPortalServer()
