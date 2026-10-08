import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk
from tkinter import ttk
import threading
import math
import time
from datetime import datetime
import psutil

from core.brain import brain
from core.voice import speak, stop_speaking
from core.listener import listener
from core.audio_visualizer import audio_visualizer
from tools.global_hotkey import global_hotkey
from ui.hud_telemetry_matrix import hud_telemetry
import config

def _attach_to_interactive_desktop():
    """Attaches current thread to interactive user desktop (Default) on Windows."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass


class TacticalHUD:
    """
    Mark-LXXXV Stark Industries Holographic Tactical Display.
    Features:
    - 3D Gyroscopic Arc Reactor Core & Quantum Particle Orbit Simulation
    - Real-Time 28-Band Acoustic FFT Spectrum Equalizer
    - Live Hardware & Sentinel Telemetry Arc Gauges (CPU, RAM, Security Sentinels)
    - Avionics Cyber Terminal with High-Tech Syntax Stream
    - Quick-Fire Tactical Directive Deck with Iron Man Sound FX
    - Dynamic Holographic Theme Matrix (Stark Cyan, War Machine Crimson, Quantum Emerald)
    - Hands-Free Wake-Word Toggle, Continuous Conversation, and Barge-In Silencing
    - System-Wide Global Win32 Hotkey Summoning (Ctrl+Alt+J / Ctrl+Shift+J)
    """

    # Sci-Fi Theme Palettes
    THEMES = {
        "stark_cyan": {
            "name": "STARK MARK-LXXXV",
            "bg": "#020814",
            "panel_bg": "#041126",
            "card_bg": "#061838",
            "primary": "#00f0ff",      # Holographic Cyan
            "secondary": "#ffd700",    # Arc Gold
            "glow": "#00d4ff",
            "accent": "#00a2ff",
            "danger": "#ff2a55",
            "text": "#e0f6ff",
            "dim": "#3a6899",
            "border": "#0e3a6c",
            "active_border": "#00f0ff",
            "console_bg": "#020c1d",
            "console_text": "#7eeeff"
        },
        "war_machine": {
            "name": "MARK-VII CRIMSON",
            "bg": "#0f0307",
            "panel_bg": "#1c060e",
            "card_bg": "#2b0a16",
            "primary": "#ff2a55",      # Laser Crimson
            "secondary": "#ffb700",    # Amber Gold
            "glow": "#ff446b",
            "accent": "#ff6b8b",
            "danger": "#ff1133",
            "text": "#ffe0e8",
            "dim": "#8c3b4e",
            "border": "#5c1324",
            "active_border": "#ff2a55",
            "console_bg": "#140409",
            "console_text": "#ffa8b8"
        },
        "quantum_emerald": {
            "name": "QUANTUM EMERALD",
            "bg": "#010f0b",
            "panel_bg": "#031c15",
            "card_bg": "#062b20",
            "primary": "#00ff9d",      # Quantum Emerald
            "secondary": "#00e5ff",    # Cyan Secondary
            "glow": "#33ffb5",
            "accent": "#00cc7a",
            "danger": "#ff3355",
            "text": "#e0fff2",
            "dim": "#2d7a5e",
            "border": "#0d4d38",
            "active_border": "#00ff9d",
            "console_bg": "#02140e",
            "console_text": "#9effd5"
        }
    }

    def __init__(self):
        _attach_to_interactive_desktop()
        self.root = tk.Tk()
        self.root.title(config.HUD_WINDOW_TITLE)

        # Center Tactical HUD dynamically on display with widescreen sci-fi dimensions
        w, h = 1160, 760
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(1040, 700)

        # Set application icon if available
        try:
            if config.IRONMAN_ICO_PATH.exists():
                self.root.iconbitmap(str(config.IRONMAN_ICO_PATH))
            else:
                self.root.iconbitmap("assets/ironman.ico")
        except Exception:
            pass

        # Active Theme
        self.theme_keys = list(self.THEMES.keys())
        self.current_theme_idx = 0
        self.theme = self.THEMES[self.theme_keys[self.current_theme_idx]]

        # State Variables
        self.wake_active = True
        self.conversation_active = False
        self._last_vitals_update = 0.0
        self._cached_cpu = 0.0
        self._cached_ram = 0.0
        self._cached_ram_used = 0
        self._cached_ram_total = 0

        # Quantum Particle Simulation
        self.particles = []
        for i in range(12):
            self.particles.append({
                "angle": (i * (math.pi * 2 / 12)),
                "speed": 0.03 + (i % 3) * 0.015,
                "radius": 55 + (i % 4) * 12,
                "size": 2 + (i % 3)
            })

        self._build_ui()
        self._animate_reactor()

        # Keyboard Shortcut: Escape to immediately interrupt speech
        self.root.bind("<Escape>", lambda e: self.silence_vocalizer())

        # Intercept window close (X button): minimize to background stealth mode instead of exiting
        self.root.protocol("WM_DELETE_WINDOW", self.enter_stealth_mode)

        # Start system-wide global hotkey listener (Ctrl+Alt+J / Ctrl+Shift+J)
        global_hotkey.start(callback=self.summon_from_hotkey)

        # Start Live Audio FFT Reactive Visualizer
        audio_visualizer.start()

        # Elevate Tactical HUD to foreground upon opening
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(600, lambda: self.root.attributes("-topmost", False))
        self.root.focus_force()

        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, config.HUD_WINDOW_TITLE)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9) # SW_RESTORE
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

    def _play_fx(self, name: str = "target_lock"):
        """Plays non-blocking tactical audio feedback."""
        def _th():
            try:
                hud_telemetry.play_tactical_sound_fx(name)
            except Exception:
                pass
        threading.Thread(target=_th, daemon=True).start()

    def cycle_theme(self):
        """Cycles through high-tech holographic visual palettes in real-time."""
        self.current_theme_idx = (self.current_theme_idx + 1) % len(self.theme_keys)
        self.theme = self.THEMES[self.theme_keys[self.current_theme_idx]]
        self._play_fx("target_lock")
        self._apply_theme()
        self.append_log("SYSTEM", f"Holographic visual palette shifted to: {self.theme['name']}.")

    def _apply_theme(self):
        """Re-applies active theme styling to widgets."""
        t = self.theme
        self.root.configure(bg=t["bg"])
        self.hdr_frame.configure(bg=t["bg"])
        self.hdr_title.configure(fg=t["primary"], bg=t["bg"])
        self.hdr_sub.configure(fg=t["secondary"], bg=t["bg"])
        self.btn_theme.configure(fg=t["primary"], bg=t["card_bg"], activebackground=t["primary"])

        # Decks
        self.left_deck.configure(bg=t["panel_bg"], highlightbackground=t["border"])
        self.center_deck.configure(bg=t["panel_bg"], highlightbackground=t["border"])
        self.right_deck.configure(bg=t["panel_bg"], highlightbackground=t["border"])
        self.footer_frame.configure(bg=t["bg"])
        self.lbl_footer.configure(fg=t["dim"], bg=t["bg"])

        # Console
        self.console.configure(bg=t["console_bg"], fg=t["console_text"], insertbackground=t["primary"])
        self.input_entry.configure(bg=t["card_bg"], fg=t["text"], insertbackground=t["primary"])
        self.input_prompt_lbl.configure(fg=t["primary"], bg=t["card_bg"])

        # Canvas backgrounds
        self.canvas_reactor.configure(bg=t["bg"])
        self.canvas_cpu.configure(bg=t["card_bg"])

    def _build_ui(self):
        t = self.theme
        self.root.configure(bg=t["bg"])

        # ─────────────────────────────────────────────────────────────────────
        # TOP DECK: HOLOGRAPHIC HEADER & TELEMETRY STRIP
        # ─────────────────────────────────────────────────────────────────────
        self.hdr_frame = tk.Frame(self.root, bg=t["bg"], padx=16, pady=6)
        self.hdr_frame.pack(fill="x")

        # Top Bar: Title & Dynamic Clock
        top_bar = tk.Frame(self.hdr_frame, bg=t["bg"])
        top_bar.pack(fill="x")

        self.hdr_title = tk.Label(
            top_bar,
            text="⫸ J.A.R.V.I.S. // STARK QUANTUM HOLOGRAPHIC INTERFACE",
            font=("Segoe UI", 13, "bold"),
            fg=t["primary"],
            bg=t["bg"]
        )
        self.hdr_title.pack(side="left")

        # Top Right Badges & Controls
        ctrl_frame = tk.Frame(top_bar, bg=t["bg"])
        ctrl_frame.pack(side="right")

        self.btn_theme = tk.Button(
            ctrl_frame,
            text=f"🎨 PALETTE: {t['name']}",
            font=("Segoe UI", 8, "bold"),
            fg=t["primary"],
            bg=t["card_bg"],
            activebackground=t["primary"],
            activeforeground="#000",
            relief="flat",
            padx=8,
            pady=2,
            command=self.cycle_theme
        )
        self.btn_theme.pack(side="left", padx=4)

        self.btn_wake = tk.Button(
            ctrl_frame,
            text="🔔 WAKE: ON",
            font=("Segoe UI", 8, "bold"),
            fg=t["primary"],
            bg=t["card_bg"],
            relief="flat",
            padx=8,
            pady=2,
            command=self.toggle_wake_word
        )
        self.btn_wake.pack(side="left", padx=4)

        self.btn_conversation = tk.Button(
            ctrl_frame,
            text="💬 CONVERSATION",
            font=("Segoe UI", 8, "bold"),
            fg=t["secondary"],
            bg="#261b04",
            relief="flat",
            padx=8,
            pady=2,
            command=self.toggle_conversation_mode
        )
        self.btn_conversation.pack(side="left", padx=4)

        # Telemetry Sub-strip
        sub_bar = tk.Frame(self.hdr_frame, bg=t["bg"])
        sub_bar.pack(fill="x", pady=(2, 0))

        self.hdr_sub = tk.Label(
            sub_bar,
            text="LAT 34.0522° N // LON 118.2437° W // ELEV 148M // GLOBAL SUMMON: Ctrl+Alt+J // BARGE-IN: ESC",
            font=("Consolas", 8),
            fg=t["secondary"],
            bg=t["bg"]
        )
        self.hdr_sub.pack(side="left")

        self.lbl_clock = tk.Label(
            sub_bar,
            text=datetime.now().strftime("STARDATE %Y.%j // %H:%M:%S UTC"),
            font=("Consolas", 8, "bold"),
            fg=t["primary"],
            bg=t["bg"]
        )
        self.lbl_clock.pack(side="right")

        # ─────────────────────────────────────────────────────────────────────
        # MAIN 3-DECK LAYOUT
        # ─────────────────────────────────────────────────────────────────────
        decks_frame = tk.Frame(self.root, bg=t["bg"], padx=14, pady=4)
        decks_frame.pack(fill="both", expand=True)

        # LEFT DECK: System Vitals & Sentinel Telemetry (Width: 260px)
        self.left_deck = tk.Frame(
            decks_frame,
            bg=t["panel_bg"],
            highlightbackground=t["border"],
            highlightthickness=1,
            padx=12,
            pady=10,
            width=260
        )
        self.left_deck.pack(side="left", fill="y", padx=(0, 8))
        self.left_deck.pack_propagate(False)
        self._build_left_deck()

        # CENTER DECK: Holographic Projection Core & Cyber Console
        self.center_deck = tk.Frame(
            decks_frame,
            bg=t["panel_bg"],
            highlightbackground=t["border"],
            highlightthickness=1,
            padx=12,
            pady=10
        )
        self.center_deck.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self._build_center_deck()

        # RIGHT DECK: Tactical Protocols & Directives (Width: 260px)
        self.right_deck = tk.Frame(
            decks_frame,
            bg=t["panel_bg"],
            highlightbackground=t["border"],
            highlightthickness=1,
            padx=12,
            pady=10,
            width=260
        )
        self.right_deck.pack(side="right", fill="y")
        self.right_deck.pack_propagate(False)
        self._build_right_deck()

        # ─────────────────────────────────────────────────────────────────────
        # BOTTOM STATUS BAR
        # ─────────────────────────────────────────────────────────────────────
        self.footer_frame = tk.Frame(self.root, bg=t["bg"], padx=16, pady=4)
        self.footer_frame.pack(fill="x")

        self.lbl_footer = tk.Label(
            self.footer_frame,
            text="[STATUS: NOMINAL] [ASIMOV GUARD: ENFORCED] [DEVICE LOCK: ARMED] [OFF-GRID PERSISTENCE: ON] [STRICT ENGLISH]",
            font=("Consolas", 8),
            fg=t["dim"],
            bg=t["bg"]
        )
        self.lbl_footer.pack(side="left")

        self.lbl_status_mode = tk.Label(
            self.footer_frame,
            text="● QUANTUM MATRIX ONLINE",
            font=("Consolas", 8, "bold"),
            fg=t["primary"],
            bg=t["bg"]
        )
        self.lbl_status_mode.pack(side="right")

    def _build_left_deck(self):
        """Constructs Left Telemetry & Sentinel Deck."""
        t = self.theme
        lbl_head = tk.Label(
            self.left_deck,
            text="◆ SYSTEM TELEMETRY ◆",
            font=("Segoe UI", 9, "bold"),
            fg=t["primary"],
            bg=t["panel_bg"]
        )
        lbl_head.pack(anchor="w", pady=(0, 6))

        # CPU Radial Gauge Canvas
        self.canvas_cpu = tk.Canvas(
            self.left_deck,
            width=230,
            height=110,
            bg=t["card_bg"],
            highlightthickness=1,
            highlightbackground=t["border"]
        )
        self.canvas_cpu.pack(fill="x", pady=(0, 8))

        # Hardware Info Labels
        self.lbl_cpu_text = tk.Label(
            self.left_deck,
            text="CPU LOAD: CALIBRATING...",
            font=("Consolas", 8, "bold"),
            fg=t["text"],
            bg=t["panel_bg"]
        )
        self.lbl_cpu_text.pack(anchor="w")

        self.lbl_ram_text = tk.Label(
            self.left_deck,
            text="RAM LOAD: CALIBRATING...",
            font=("Consolas", 8),
            fg=t["text"],
            bg=t["panel_bg"]
        )
        self.lbl_ram_text.pack(anchor="w", pady=(2, 8))

        # Sentinel Defense Matrix Section
        lbl_sentinels = tk.Label(
            self.left_deck,
            text="◆ DEFENSE SENTINELS ◆",
            font=("Segoe UI", 9, "bold"),
            fg=t["secondary"],
            bg=t["panel_bg"]
        )
        lbl_sentinels.pack(anchor="w", pady=(8, 4))

        sentinel_items = [
            ("🛡 ASIMOV VETO", "ENFORCED"),
            ("🔒 DEVICE LOCK", "ARMED"),
            ("🎙 BIOMETRIC SENTINEL", "ACTIVE"),
            ("🔑 CREDENTIAL VAULT", "PROTECTED"),
            ("🛸 CLOUD AWAY DRONE", "ENGAGED"),
            ("🌐 INTERNET REPAIR", "MONITORING")
        ]
        self.sentinel_labels = []
        for name, status in sentinel_items:
            f = tk.Frame(self.left_deck, bg=t["panel_bg"])
            f.pack(fill="x", pady=1)
            l_n = tk.Label(f, text=name, font=("Consolas", 8), fg=t["dim"], bg=t["panel_bg"])
            l_n.pack(side="left")
            l_s = tk.Label(f, text=f"[{status}]", font=("Consolas", 8, "bold"), fg=t["primary"], bg=t["panel_bg"])
            l_s.pack(side="right")
            self.sentinel_labels.append((l_n, l_s))

        # Acoustic Spectrum Vitals
        lbl_audio_head = tk.Label(
            self.left_deck,
            text="◆ ACOUSTIC SPECTRUM ◆",
            font=("Segoe UI", 9, "bold"),
            fg=t["primary"],
            bg=t["panel_bg"]
        )
        lbl_audio_head.pack(anchor="w", pady=(12, 4))

        self.lbl_audio_low = tk.Label(self.left_deck, text="BASS (60-250Hz): 0.00", font=("Consolas", 8), fg=t["text"], bg=t["panel_bg"])
        self.lbl_audio_low.pack(anchor="w")
        self.lbl_audio_mid = tk.Label(self.left_deck, text="SPEECH (250-2kHz): 0.00", font=("Consolas", 8), fg=t["text"], bg=t["panel_bg"])
        self.lbl_audio_mid.pack(anchor="w")
        self.lbl_audio_high = tk.Label(self.left_deck, text="TREBLE (2k-6kHz): 0.00", font=("Consolas", 8), fg=t["text"], bg=t["panel_bg"])
        self.lbl_audio_high.pack(anchor="w")

    def _build_center_deck(self):
        """Constructs Center Holographic Projection Core and Cyber Console."""
        t = self.theme

        # Holographic Arc Reactor Canvas (Width: auto, Height: 260px)
        self.canvas_reactor = tk.Canvas(
            self.center_deck,
            height=250,
            bg=t["bg"],
            highlightthickness=1,
            highlightbackground=t["border"]
        )
        self.canvas_reactor.pack(fill="x", pady=(0, 8))

        # Cyber Avionics Console
        console_frame = tk.Frame(self.center_deck, bg=t["panel_bg"])
        console_frame.pack(fill="both", expand=True, pady=(0, 8))

        self.console = tk.Text(
            console_frame,
            bg=t["console_bg"],
            fg=t["console_text"],
            font=("Consolas", 9),
            insertbackground=t["primary"],
            relief="flat",
            padx=10,
            pady=8,
            highlightthickness=1,
            highlightbackground=t["border"]
        )
        self.console.pack(fill="both", expand=True)
        self.console.insert("end", "[J.A.R.V.I.S. Mark-LXXXV]: Quantum core initialized. Full offline & online subroutines armed.\n")
        self.console.insert("end", "[Sentinel Network]: Auditory wake-word active. Speak 'Hey Jarvis' or summon via Ctrl+Alt+J.\n\n")
        self.console.config(state="disabled")

        # Command Input Dock
        dock_frame = tk.Frame(self.center_deck, bg=t["panel_bg"])
        dock_frame.pack(fill="x")

        # Push-to-Talk Mic
        self.btn_mic = tk.Button(
            dock_frame,
            text="🎤",
            font=("Segoe UI", 11, "bold"),
            fg=t["secondary"],
            bg=t["card_bg"],
            activebackground=t["secondary"],
            activeforeground="#000",
            relief="flat",
            padx=10,
            command=self.trigger_mic
        )
        self.btn_mic.pack(side="left", padx=(0, 6))

        # Text input wrapper
        input_wrap = tk.Frame(dock_frame, bg=t["card_bg"], highlightthickness=1, highlightbackground=t["border"])
        input_wrap.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.input_prompt_lbl = tk.Label(input_wrap, text="⫸", font=("Segoe UI", 11, "bold"), fg=t["primary"], bg=t["card_bg"])
        self.input_prompt_lbl.pack(side="left", padx=(8, 4))

        self.entry = tk.Entry(
            input_wrap,
            font=("Segoe UI", 11),
            bg=t["card_bg"],
            fg=t["text"],
            insertbackground=t["primary"],
            relief="flat"
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.send_directive())
        self.input_entry = self.entry

        # Transmit Button
        self.btn_send = tk.Button(
            dock_frame,
            text="⚡ TRANSMIT",
            font=("Segoe UI", 9, "bold"),
            fg=t["primary"],
            bg=t["card_bg"],
            activebackground=t["primary"],
            activeforeground="#000",
            relief="flat",
            padx=12,
            pady=6,
            command=self.send_directive
        )
        self.btn_send.pack(side="left", padx=(0, 4))

        # Silence / Barge-In
        self.btn_silence = tk.Button(
            dock_frame,
            text="⏹ SILENCE",
            font=("Segoe UI", 9, "bold"),
            fg=t["danger"],
            bg="#2b0a12",
            activebackground=t["danger"],
            activeforeground="#fff",
            relief="flat",
            padx=10,
            pady=6,
            command=self.silence_vocalizer
        )
        self.btn_silence.pack(side="left", padx=(0, 4))

        # Stealth Mode
        self.btn_stealth = tk.Button(
            dock_frame,
            text="👁 STEALTH",
            font=("Segoe UI", 9, "bold"),
            fg=t["secondary"],
            bg=t["card_bg"],
            activebackground=t["secondary"],
            activeforeground="#000",
            relief="flat",
            padx=10,
            pady=6,
            command=self.enter_stealth_mode
        )
        self.btn_stealth.pack(side="left")

    def _build_right_deck(self):
        """Constructs Right Tactical Directives & Protocols Deck."""
        t = self.theme
        lbl_head = tk.Label(
            self.right_deck,
            text="◆ TACTICAL DIRECTIVES ◆",
            font=("Segoe UI", 9, "bold"),
            fg=t["primary"],
            bg=t["panel_bg"]
        )
        lbl_head.pack(anchor="w", pady=(0, 6))

        # Quick Fire Action Buttons
        quick_actions = [
            ("📋 DAILY BRIEFING", "daily briefing"),
            ("⚡ SYSTEM VITALS", "system vitals"),
            ("📅 TODAY'S AGENDA", "what is on my schedule today"),
            ("🔒 LOCK WORKSTATION", "lock my device"),
            ("🔓 UNLOCK SYSTEM", "unlock my device"),
            ("🧹 OPTIMIZE SYSTEM", "optimize system"),
            ("🌐 NETWORK STATUS", "network status"),
            ("🔊 IRON MAN AUDIO FX", "__SOUND_FX__")
        ]

        self.tactical_buttons = []
        for label, cmd in quick_actions:
            btn = tk.Button(
                self.right_deck,
                text=label,
                font=("Segoe UI", 8, "bold"),
                fg=t["text"],
                bg=t["card_bg"],
                activebackground=t["primary"],
                activeforeground="#000",
                relief="flat",
                pady=5,
                anchor="w",
                padx=8,
                command=lambda c=cmd: self._trigger_quick_action(c)
            )
            btn.pack(fill="x", pady=2)
            self.tactical_buttons.append(btn)

        # Autonomous Butler Protocols
        lbl_protocols = tk.Label(
            self.right_deck,
            text="◆ ACTIVE PROTOCOLS ◆",
            font=("Segoe UI", 9, "bold"),
            fg=t["secondary"],
            bg=t["panel_bg"]
        )
        lbl_protocols.pack(anchor="w", pady=(12, 4))

        protocols = [
            ("PROTOCOL SUNRISE", "08:00 ARMED"),
            ("VOICE PAUSE SENTINEL", f"{config.VOICE_PAUSE_THRESHOLD}s"),
            ("HYBRID VECTOR STORE", "SYNCHRONIZED"),
            ("SPEAKER BIOMETRICS", "NOMINAL"),
            ("SECURITY AUDITOR", "STANDBY")
        ]
        for p_name, p_val in protocols:
            f = tk.Frame(self.right_deck, bg=t["panel_bg"])
            f.pack(fill="x", pady=1)
            tk.Label(f, text=p_name, font=("Consolas", 8), fg=t["dim"], bg=t["panel_bg"]).pack(side="left")
            tk.Label(f, text=p_val, font=("Consolas", 8, "bold"), fg=t["primary"], bg=t["panel_bg"]).pack(side="right")

    def _trigger_quick_action(self, cmd: str):
        if cmd == "__SOUND_FX__":
            self._play_fx("repulsor_charge")
            self.append_log("SYSTEM", "Acoustic tactical audio FX synthesized.")
            return

        self._play_fx("target_lock")
        self.entry.delete(0, "end")
        self.entry.insert(0, cmd)
        self.send_directive()

    def _update_hardware_telemetry(self):
        """Refreshes hardware telemetry gauges every 1.5s."""
        now = time.time()
        if now - self._last_vitals_update < 1.5:
            return

        self._last_vitals_update = now
        try:
            self._cached_cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            self._cached_ram = mem.percent
            self._cached_ram_used = mem.used // (1024 * 1024)
            self._cached_ram_total = mem.total // (1024 * 1024)

            self.lbl_cpu_text.config(text=f"CPU LOAD: {self._cached_cpu:.1f}%")
            self.lbl_ram_text.config(text=f"RAM: {self._cached_ram:.1f}% ({self._cached_ram_used}MB / {self._cached_ram_total}MB)")
            self.lbl_clock.config(text=datetime.now().strftime("STARDATE %Y.%j // %H:%M:%S UTC"))
        except Exception:
            pass

        # Draw CPU Radial Arc Gauge on canvas_cpu
        self._draw_cpu_gauge()

    def _draw_cpu_gauge(self):
        c = self.canvas_cpu
        c.delete("all")
        t = self.theme
        w = c.winfo_width() or 230
        h = c.winfo_height() or 110

        cx, cy = 60, 55
        r = 38

        # Background track
        c.create_arc(cx - r, cy - r, cx + r, cy + r, start=-30, extent=240, style="arc", outline=t["border"], width=6)

        # Active fill arc
        cpu_pct = min(100.0, max(0.0, self._cached_cpu))
        fill_extent = (cpu_pct / 100.0) * 240
        arc_color = t["primary"] if cpu_pct < 65 else (t["secondary"] if cpu_pct < 85 else t["danger"])
        c.create_arc(cx - r, cy - r, cx + r, cy + r, start=-30, extent=fill_extent, style="arc", outline=arc_color, width=6)

        # Center Percentage Text
        c.create_text(cx, cy, text=f"{int(cpu_pct)}%", font=("Segoe UI", 11, "bold"), fill=t["text"])

        # RAM Horizontal Bar on right side of gauge
        rx, ry = 120, 30
        rw, rh = 95, 12
        c.create_text(rx, ry - 10, text="RAM UTILIZATION", font=("Consolas", 7, "bold"), fill=t["dim"], anchor="w")
        c.create_rectangle(rx, ry, rx + rw, ry + rh, fill=t["panel_bg"], outline=t["border"])
        ram_w = int((self._cached_ram / 100.0) * rw)
        ram_color = t["primary"] if self._cached_ram < 80 else t["secondary"]
        c.create_rectangle(rx, ry, rx + ram_w, ry + rh, fill=ram_color, outline="")

        # Disk/Network Indicator
        c.create_text(rx, ry + rh + 16, text=f"DISPATCH: 0.8ms // SYNCD", font=("Consolas", 7), fill=t["secondary"], anchor="w")
        c.create_text(rx, ry + rh + 28, text=f"SEC_LEVEL: TIER-5 OMEGA", font=("Consolas", 7, "bold"), fill=t["primary"], anchor="w")

    def _animate_reactor(self):
        """
        Renders 3D Gyroscopic Arc Reactor, Orbital Particles, 360° Radar Sweep,
        and 28-Band Audio FFT Equalizer at ~25 FPS.
        """
        self._update_hardware_telemetry()

        c = self.canvas_reactor
        c.delete("all")
        t_style = self.theme

        w = c.winfo_width() or 560
        h = c.winfo_height() or 250
        cx = w // 2
        cy = (h // 2) - 8

        now = time.time()
        t = now * 1.8

        # Live Audio Telemetry
        bands = audio_visualizer.get_bands()
        bars = audio_visualizer.get_bars()

        energy = bands.get("rms", 0.0)
        low = bands.get("low", 0.0)
        mid = bands.get("mid", 0.0)
        high = bands.get("high", 0.0)
        state = bands.get("state", "idle")

        # Update text telemetry in left deck
        self.lbl_audio_low.config(text=f"BASS (60-250Hz): {low:.2f}")
        self.lbl_audio_mid.config(text=f"SPEECH (250-2kHz): {mid:.2f}")
        self.lbl_audio_high.config(text=f"TREBLE (2k-6kHz): {high:.2f}")

        # Active Palette Modulated by State
        if state == "listening" or energy > 0.18:
            core_glow = t_style["secondary"]
            ring_col = t_style["secondary"]
            arc_col = "#ffaa00"
            status_text = "ACOUSTIC LISTENING"
        elif state == "speaking":
            core_glow = t_style["primary"]
            ring_col = t_style["glow"]
            arc_col = t_style["primary"]
            status_text = "VOCALIZING RESPONSE"
        else:
            core_glow = t_style["primary"]
            ring_col = t_style["border"]
            arc_col = t_style["primary"]
            status_text = "STANDBY // AMBIENT"

        # 1. Subtle Holographic Background Grid & Concentric Reticles
        c.create_line(cx - 160, cy, cx + 160, cy, fill="#051c38", dash=(2, 4))
        c.create_line(cx, cy - 90, cx, cy + 90, fill="#051c38", dash=(2, 4))
        c.create_oval(cx - 130, cy - 85, cx + 130, cy + 85, outline="#051c38", dash=(1, 5))

        # 2. Outer Segmented Containment Shield (8 Rotating Arc Segments)
        outer_r = 78 + (low * 22.0)
        num_segs = 8
        for i in range(num_segs):
            seg_start = math.degrees(t * 0.4) + (i * (360 / num_segs))
            c.create_arc(
                cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
                start=seg_start,
                extent=26,
                style="arc",
                outline=ring_col,
                width=2
            )

        # 3. 3D Gyroscopic Orbit Ellipse (Perspective Tilt in Space)
        tilt_t = t * 0.6
        gyro_rx = 95 + (mid * 15.0)
        gyro_ry = 36 + (math.sin(tilt_t) * 12.0)
        c.create_oval(
            cx - gyro_rx, cy - gyro_ry, cx + gyro_rx, cy + gyro_ry,
            outline=arc_col,
            width=1,
            dash=(4, 4)
        )

        # 4. Concentric Azimuth Degree Dial (Middle Gear)
        mid_r = 52
        c.create_oval(cx - mid_r, cy - mid_r, cx + mid_r, cy + mid_r, outline=t_style["border"], width=1)
        for i in range(12):
            ang = (t * -0.6) + (i * (math.pi * 2 / 12))
            x1 = cx + (mid_r - 5) * math.cos(ang)
            y1 = cy + (mid_r - 5) * math.sin(ang)
            x2 = cx + mid_r * math.cos(ang)
            y2 = cy + mid_r * math.sin(ang)
            c.create_line(x1, y1, x2, y2, fill=ring_col, width=1)

        # 5. Inner Core Rotating Spoke Matrix
        inner_r = 34
        for i in range(6):
            ang = (t * 1.2) + (i * (math.pi / 3))
            x1 = cx + 14 * math.cos(ang)
            y1 = cy + 14 * math.sin(ang)
            x2 = cx + (inner_r + (mid * 10.0)) * math.cos(ang)
            y2 = cy + (inner_r + (mid * 10.0)) * math.sin(ang)
            c.create_line(x1, y1, x2, y2, fill=arc_col, width=2)

        # 6. Quantum Particles Orbiting Around Reactor
        for p in self.particles:
            p["angle"] += p["speed"]
            px = cx + (p["radius"] + (energy * 15.0)) * math.cos(p["angle"])
            py = cy + ((p["radius"] * 0.55) + (energy * 8.0)) * math.sin(p["angle"])
            sz = p["size"]
            c.create_oval(px - sz, py - sz, px + sz, py + sz, fill=t_style["secondary"], outline="")

        # 7. Singularity Core (Multi-stage Radial Plasma Glow)
        core_r = 14 + int(energy * 16)
        c.create_oval(cx - core_r - 8, cy - core_r - 8, cx + core_r + 8, cy + core_r + 8, outline=core_glow, width=1)
        c.create_oval(cx - core_r, cy - core_r, cx + core_r, cy + core_r, fill=core_glow, outline="#ffffff", width=1)

        # 8. 360° Radar Sweep Beam
        sweep_ang = t * 1.5
        sweep_r = outer_r + 14
        sx = cx + sweep_r * math.cos(sweep_ang)
        sy = cy + sweep_r * math.sin(sweep_ang)
        c.create_line(cx, cy, sx, sy, fill=t_style["primary"], width=1)

        # 9. Corner HUD Telemetry Overlays on Canvas
        c.create_text(14, 14, text="[MK-LXXXV QUANTUM CORE]", font=("Consolas", 8, "bold"), fill=t_style["primary"], anchor="nw")
        c.create_text(14, 28, text="FREQ: 142.85 GHz // HARMONICS: NOMINAL", font=("Consolas", 7), fill=t_style["dim"], anchor="nw")

        c.create_text(w - 14, 14, text=f"MODE: {status_text}", font=("Consolas", 8, "bold"), fill=core_glow, anchor="ne")
        c.create_text(w - 14, 28, text=f"ENERGY RMS: {energy:.3f}", font=("Consolas", 7), fill=t_style["dim"], anchor="ne")

        # 10. 28-Band Real-Time Audio Equalizer Bars along Base of Canvas
        num_bars = 28
        bar_w = 10
        spacing = 6
        total_eq_w = num_bars * (bar_w + spacing) - spacing
        start_x = max(10, (w - total_eq_w) // 2)
        base_y = h - 10

        # Resample or pad bars from audio_visualizer
        raw_bars = bars if bars else [0.08] * num_bars
        for i in range(num_bars):
            val = raw_bars[i % len(raw_bars)]
            bx = start_x + i * (bar_w + spacing)
            bh = int(val * 36.0) + int(math.sin(t + i * 0.4) * 2)
            bh = max(3, min(48, bh))

            bar_color = t_style["secondary"] if (i % 5 == 0 or energy > 0.22) else t_style["primary"]
            c.create_rectangle(bx, base_y - bh, bx + bar_w, base_y, fill=bar_color, outline="")
            # Glowing tip on bar
            c.create_rectangle(bx, base_y - bh, bx + bar_w, base_y - bh + 2, fill="#ffffff", outline="")

        self.root.after(40, self._animate_reactor)

    def append_log(self, sender: str, msg: str):
        """Appends formatted message to cyber console."""
        t_str = datetime.now().strftime("%H:%M:%S")
        self.console.config(state="normal")
        self.console.insert("end", f"[{t_str}] [{sender}] >> {msg}\n\n")
        self.console.see("end")
        self.console.config(state="disabled")

    def silence_vocalizer(self):
        """Halts all active speech immediately."""
        stop_speaking()
        self._play_fx("target_lock")
        self.append_log("SYSTEM", "Acoustic vocalization halted via barge-in silence command.")

    def toggle_wake_word(self):
        self.wake_active = not self.wake_active
        t = self.theme
        if self.wake_active:
            self.btn_wake.config(text="🔔 WAKE: ON", fg=t["primary"], bg=t["card_bg"])
            listener.start_wake_word_daemon(self.handle_voice_directive)
            self.append_log("SYSTEM", "Auditory wake-word daemon armed ('Hey Jarvis').")
        else:
            self.btn_wake.config(text="🔕 WAKE: OFF", fg=t["danger"], bg="#26080b")
            listener.stop_wake_word_daemon()
            self.append_log("SYSTEM", "Auditory wake-word daemon disarmed.")

    def trigger_mic(self):
        self._play_fx("target_lock")
        def _listen():
            self.append_log("SYSTEM", "Acoustic sensor opened. Listening for directive...")
            txt = listener.listen("Directive, sir: ")
            if txt:
                self.handle_voice_directive(txt)
        threading.Thread(target=_listen, daemon=True).start()

    def handle_voice_directive(self, text: str):
        audio_visualizer.set_state("listening")
        self.root.after(0, lambda: self.append_log("USER (Voice)", text))
        res = brain.think(text)
        self.root.after(0, lambda: self.append_log("J.A.R.V.I.S.", res))
        audio_visualizer.set_state("speaking")
        speak(res)
        audio_visualizer.set_state("idle")

    def toggle_conversation_mode(self):
        """Toggles continuous multi-turn hands-free voice conversation."""
        self.conversation_active = not self.conversation_active
        t = self.theme
        if self.conversation_active:
            self.btn_conversation.config(text="💬 TALK: ACTIVE", fg="#000000", bg=t["secondary"])
            self.append_log("SYSTEM", "Continuous voice conversation mode engaged. Speak naturally with Jarvis.")
            speak("Continuous voice conversation mode engaged, sir. I am listening continuously.")

            def _conv_worker():
                listener.start_conversation_session(self._handle_conversation_turn)
                self.conversation_active = False
                self.root.after(0, lambda: self.btn_conversation.config(text="💬 CONVERSATION", fg=t["secondary"], bg="#261b04"))
                self.root.after(0, lambda: self.append_log("SYSTEM", "Voice conversation session concluded. Reverting to ambient standby."))

            threading.Thread(target=_conv_worker, daemon=True).start()
        else:
            listener.in_conversation_mode = False
            self.btn_conversation.config(text="💬 CONVERSATION", fg=t["secondary"], bg="#261b04")
            speak("Standing down continuous conversation mode, sir.")
            self.append_log("SYSTEM", "Voice conversation disengaged.")

    def _handle_conversation_turn(self, user_text: str) -> bool:
        if not user_text:
            return True
        audio_visualizer.set_state("listening")
        self.root.after(0, lambda: self.append_log("USER (Voice)", user_text))
        res = brain.think(user_text)
        self.root.after(0, lambda: self.append_log("J.A.R.V.I.S.", res))
        audio_visualizer.set_state("speaking")
        from core.voice import speak_sync
        speak_sync(res)
        audio_visualizer.set_state("idle")
        lower = user_text.lower()
        if any(w in lower for w in listener.EXIT_CONVERSATION_WORDS):
            return False
        return True

    def send_directive(self):
        cmd = self.entry.get().strip()
        if not cmd:
            return
        self.entry.delete(0, "end")
        self._play_fx("target_lock")
        self.append_log("USER", cmd)

        def _proc():
            audio_visualizer.set_state("listening")
            res = brain.think(cmd)
            self.root.after(0, lambda: self.append_log("J.A.R.V.I.S.", res))
            audio_visualizer.set_state("speaking")
            speak(res)
            audio_visualizer.set_state("idle")

        threading.Thread(target=_proc, daemon=True).start()

    def enter_stealth_mode(self):
        """Hides Tactical HUD to background stealth mode while services remain active."""
        self.root.withdraw()
        print("[Stealth Mode]: J.A.R.V.I.S. Tactical HUD minimized. Press Ctrl+Alt+J or say 'Hey Jarvis' to summon.")

    def summon_from_hotkey(self):
        """Callback triggered by Win32 global hotkey thread (Ctrl+Alt+J / Ctrl+Shift+J)."""
        self.root.after(0, self.restore_hud)

    def restore_hud(self):
        """Restores and brings Tactical HUD to the foreground."""
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(600, lambda: self.root.attributes("-topmost", False))
        self.root.focus_force()
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, config.HUD_WINDOW_TITLE)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9) # SW_RESTORE
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        self.entry.focus_set()
        self.append_log("SYSTEM", "Tactical HUD summoned from stealth mode.")

    def run(self):
        # Start voice daemon on launch
        listener.start_wake_word_daemon(self.handle_voice_directive)
        try:
            self.root.mainloop()
        finally:
            global_hotkey.stop()
            audio_visualizer.stop()


def launch_hud():
    hud = TacticalHUD()
    hud.run()

if __name__ == "__main__":
    launch_hud()
