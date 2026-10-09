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
from tools.weather_tools import get_weather
from tools.hud_controller import hud_controller
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
    J.A.R.V.I.S. Open-Source Holographic Display & Projector HUD.
    Inspired by MateoTechLab / Stark Industries:
    - Pitch-black background (#000000) for floating projection on glass, acrylic, or wall
    - Interactive 3D Holographic Wireframe Engine (Helmet, Arc Reactor, Globe, Tesseract)
    - Mouse drag 3D rotation (yaw/pitch) and scroll zoom
    - Date, Time, and Real-Time Weather Holographic Module
    - Interactive To-Do List & Project Task Matrix with instant task tracking
    - Live Audio Waveform & Multi-Band Acoustic Equalizer
    - Hardware Telemetry Gauges (CPU circular arc gauge, RAM matrix, Sentinel defense)
    - Borderless Fullscreen Projector Mode (F11 toggle)
    - Integrated Iron Man acoustic feedback sound effects
    """

    THEMES = {
        "stark_cyan": {
            "name": "STARK HOLOGRAPHIC CYAN",
            "bg": "#000000",           # Pure black for true floating hologram
            "panel_bg": "#00050d",
            "card_bg": "#010e1f",
            "primary": "#00f0ff",      # Glowing Cyan
            "secondary": "#ffd700",    # Stark Gold
            "glow": "#00d4ff",
            "accent": "#00a2ff",
            "danger": "#ff2a55",
            "text": "#e0f6ff",
            "dim": "#2d577a",
            "border": "#07294d",
            "active_border": "#00f0ff",
            "console_bg": "#010814",
            "console_text": "#7eeeff"
        },
        "war_machine": {
            "name": "MARK-VII CRIMSON",
            "bg": "#000000",
            "panel_bg": "#0d0205",
            "card_bg": "#1f060c",
            "primary": "#ff2a55",
            "secondary": "#ffb700",
            "glow": "#ff446b",
            "accent": "#ff6b8b",
            "danger": "#ff1133",
            "text": "#ffe0e8",
            "dim": "#6e2938",
            "border": "#420e1a",
            "active_border": "#ff2a55",
            "console_bg": "#0d0205",
            "console_text": "#ffa8b8"
        },
        "quantum_emerald": {
            "name": "QUANTUM EMERALD",
            "bg": "#000000",
            "panel_bg": "#000a06",
            "card_bg": "#02170f",
            "primary": "#00ff9d",
            "secondary": "#00e5ff",
            "glow": "#33ffb5",
            "accent": "#00cc7a",
            "danger": "#ff3355",
            "text": "#e0fff2",
            "dim": "#1e5c46",
            "border": "#073b2a",
            "active_border": "#00ff9d",
            "console_bg": "#000a06",
            "console_text": "#9effd5"
        }
    }

    def __init__(self):
        _attach_to_interactive_desktop()
        self.root = tk.Tk()
        self.root.title(config.HUD_WINDOW_TITLE)

        # Center HUD on display
        w, h = 1200, 780
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(1080, 700)
        self.root.configure(bg="#000000")

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

        # Projection & Fullscreen State
        self.is_fullscreen = False

        # State Variables
        self.wake_active = True
        self.conversation_active = False
        self._last_vitals_update = 0.0
        self._cached_cpu = 0.0
        self._cached_ram = 0.0
        self._cached_weather = "SCANNING ATMOSPHERE..."
        self._weather_last_fetch = 0.0

        # Interactive 3D Model Parameters
        self.active_3d_model = "helmet"  # "helmet", "reactor", "globe", "tesseract"
        self.model_yaw = 0.0
        self.model_pitch = 0.2
        self.model_scale = 1.0
        self.auto_spin = True
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Task Ledger (To-Do List items)
        self.tasks = [
            {"text": "Neural Core Online", "done": True},
            {"text": "Device Lock Sentinel Active", "done": True},
            {"text": "Holographic Display Synchronized", "done": True},
            {"text": "Protocol Sunrise 08:00 Sweep", "done": False},
            {"text": "Continuous Sentence Sentinel", "done": True},
            {"text": "Zero-Cost Cloud Off-Grid Sync", "done": False}
        ]

        self._build_ui()
        self._animate_reactor()

        # Keyboard Shortcuts
        self.root.bind("<Escape>", lambda e: self._handle_escape_key())
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen_mode())

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
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

        # Register instance with HUD controller IPC bridge
        hud_controller.register_hud_instance(self)

    def _play_fx(self, name: str = "target_lock"):
        """Plays non-blocking tactical audio feedback."""
        def _th():
            try:
                hud_telemetry.play_tactical_sound_fx(name)
            except Exception:
                pass
        threading.Thread(target=_th, daemon=True).start()

    def _handle_escape_key(self):
        if self.is_fullscreen:
            self.toggle_fullscreen_mode()
        else:
            self.silence_vocalizer()

    def toggle_fullscreen_mode(self):
        """Toggles borderless projector / holographic fullscreen mode (F11)."""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        self._play_fx("target_lock")
        if self.is_fullscreen:
            self.btn_fullscreen.config(text="⛶ EXIT FULLSCREEN")
            self.append_log("SYSTEM", "Borderless Projector Holographic Mode engaged (F11/ESC to toggle).")
        else:
            self.btn_fullscreen.config(text="⛶ PROJECTOR MODE")
            self.append_log("SYSTEM", "Windowed Holographic Display Mode restored.")

    def set_3d_model(self, model_name: str):
        """Switches the active rotating 3D wireframe object."""
        self.active_3d_model = model_name
        from ui.mesh_3d_engine import holographic_3d
        holographic_3d.set_mesh(model_name)
        self._play_fx("target_lock")
        self.append_log("SYSTEM", f"Holographic 3D projection model shifted to: {model_name.upper()}.")

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
        self.root.configure(bg="#000000")
        self.hdr_frame.configure(bg="#000000")
        self.hdr_title.configure(fg=t["primary"], bg="#000000")
        self.btn_theme.configure(fg=t["primary"], bg=t["card_bg"], activebackground=t["primary"])

        self.left_deck.configure(bg="#000000", highlightbackground=t["border"])
        self.center_deck.configure(bg="#000000", highlightbackground=t["border"])
        self.right_deck.configure(bg="#000000", highlightbackground=t["border"])
        self.footer_frame.configure(bg="#000000")
        self.lbl_footer.configure(fg=t["dim"], bg="#000000")

        self.console.configure(bg=t["console_bg"], fg=t["console_text"], insertbackground=t["primary"])
        self.input_entry.configure(bg=t["card_bg"], fg=t["text"], insertbackground=t["primary"])
        self.input_prompt_lbl.configure(fg=t["primary"], bg=t["card_bg"])

        self.canvas_3d.configure(bg="#000000")
        self.canvas_cpu.configure(bg="#000000")
        self.canvas_spectrum.configure(bg="#000000")

    def _build_ui(self):
        t = self.theme

        # ─────────────────────────────────────────────────────────────────────
        # TOP HEADER: STARK TITLE & CONTROLS
        # ─────────────────────────────────────────────────────────────────────
        self.hdr_frame = tk.Frame(self.root, bg="#000000", padx=16, pady=6)
        self.hdr_frame.pack(fill="x")

        top_bar = tk.Frame(self.hdr_frame, bg="#000000")
        top_bar.pack(fill="x")

        self.hdr_title = tk.Label(
            top_bar,
            text="⫸ J.A.R.V.I.S. // HOLOGRAPHIC DISPLAY SYSTEM",
            font=("Consolas", 13, "bold"),
            fg=t["primary"],
            bg="#000000"
        )
        self.hdr_title.pack(side="left")

        ctrl_frame = tk.Frame(top_bar, bg="#000000")
        ctrl_frame.pack(side="right")

        self.btn_fullscreen = tk.Button(
            ctrl_frame,
            text="⛶ PROJECTOR MODE",
            font=("Consolas", 8, "bold"),
            fg=t["primary"],
            bg=t["card_bg"],
            activebackground=t["primary"],
            activeforeground="#000",
            relief="flat",
            padx=8,
            pady=2,
            command=self.toggle_fullscreen_mode
        )
        self.btn_fullscreen.pack(side="left", padx=4)

        self.btn_theme = tk.Button(
            ctrl_frame,
            text=f"🎨 PALETTE",
            font=("Consolas", 8, "bold"),
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
            font=("Consolas", 8, "bold"),
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
            font=("Consolas", 8, "bold"),
            fg=t["secondary"],
            bg="#1f1402",
            relief="flat",
            padx=8,
            pady=2,
            command=self.toggle_conversation_mode
        )
        self.btn_conversation.pack(side="left", padx=4)

        # ─────────────────────────────────────────────────────────────────────
        # MAIN 3-COLUMN HOLOGRAPHIC VIEWPORT
        # ─────────────────────────────────────────────────────────────────────
        decks_frame = tk.Frame(self.root, bg="#000000", padx=14, pady=4)
        decks_frame.pack(fill="both", expand=True)

        # LEFT DECK: Clock, Weather, Media & Audio Spectrum
        self.left_deck = tk.Frame(
            decks_frame,
            bg="#000000",
            highlightbackground=t["border"],
            highlightthickness=1,
            padx=12,
            pady=10,
            width=290
        )
        self.left_deck.pack(side="left", fill="y", padx=(0, 8))
        self.left_deck.pack_propagate(False)
        self._build_left_deck()

        # CENTER DECK: 3D Hologram Projection Core & Console
        self.center_deck = tk.Frame(
            decks_frame,
            bg="#000000",
            highlightbackground=t["border"],
            highlightthickness=1,
            padx=12,
            pady=10
        )
        self.center_deck.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self._build_center_deck()

        # RIGHT DECK: To-Do / Task Matrix & Hardware Telemetry
        self.right_deck = tk.Frame(
            decks_frame,
            bg="#000000",
            highlightbackground=t["border"],
            highlightthickness=1,
            padx=12,
            pady=10,
            width=290
        )
        self.right_deck.pack(side="right", fill="y")
        self.right_deck.pack_propagate(False)
        self._build_right_deck()

        # ─────────────────────────────────────────────────────────────────────
        # BOTTOM STATUS BAR
        # ─────────────────────────────────────────────────────────────────────
        self.footer_frame = tk.Frame(self.root, bg="#000000", padx=16, pady=4)
        self.footer_frame.pack(fill="x")

        self.lbl_footer = tk.Label(
            self.footer_frame,
            text="[HOLOGRAPHIC PROJECTION: ONLINE] [ESC: BARGE-IN] [F11: FULLSCREEN PROJECTOR] [SUMMON: CTRL+ALT+J]",
            font=("Consolas", 8),
            fg=t["dim"],
            bg="#000000"
        )
        self.lbl_footer.pack(side="left")

        self.lbl_status_mode = tk.Label(
            self.footer_frame,
            text="● HOLOGRAPHIC CORE ACTIVE",
            font=("Consolas", 8, "bold"),
            fg=t["primary"],
            bg="#000000"
        )
        self.lbl_status_mode.pack(side="right")

    def _build_left_deck(self):
        """Constructs Left Deck: Time, Date, Weather & Audio Spectrum."""
        t = self.theme

        # 1. Date & Time Block
        lbl_head = tk.Label(self.left_deck, text="◆ CHRONO & ATMOSPHERE ◆", font=("Consolas", 9, "bold"), fg=t["primary"], bg="#000000")
        lbl_head.pack(anchor="w", pady=(0, 4))

        self.lbl_time_large = tk.Label(self.left_deck, text="12:00:00 AM", font=("Consolas", 22, "bold"), fg=t["primary"], bg="#000000")
        self.lbl_time_large.pack(anchor="w")

        self.lbl_date_sub = tk.Label(self.left_deck, text="FRIDAY, OCTOBER 9, 2026", font=("Consolas", 8, "bold"), fg=t["secondary"], bg="#000000")
        self.lbl_date_sub.pack(anchor="w", pady=(0, 8))

        # 2. Weather Widget
        weather_frame = tk.Frame(self.left_deck, bg=t["card_bg"], highlightbackground=t["border"], highlightthickness=1, padx=8, pady=8)
        weather_frame.pack(fill="x", pady=(0, 10))

        tk.Label(weather_frame, text="ATMOSPHERIC TELEMETRY", font=("Consolas", 8, "bold"), fg=t["primary"], bg=t["card_bg"]).pack(anchor="w")
        self.lbl_weather_info = tk.Label(
            weather_frame,
            text="FETCHING SATELLITE RADAR...",
            font=("Consolas", 8),
            fg=t["text"],
            bg=t["card_bg"],
            wraplength=250,
            justify="left"
        )
        self.lbl_weather_info.pack(anchor="w", pady=(4, 0))

        # 3. Audio Spectrum Equalizer (Canvas)
        tk.Label(self.left_deck, text="◆ ACOUSTIC WAVE SPECTRUM ◆", font=("Consolas", 9, "bold"), fg=t["primary"], bg="#000000").pack(anchor="w", pady=(4, 4))

        self.canvas_spectrum = tk.Canvas(
            self.left_deck,
            height=120,
            bg="#000000",
            highlightthickness=1,
            highlightbackground=t["border"]
        )
        self.canvas_spectrum.pack(fill="x", pady=(0, 8))

        # Spectral readout values
        self.lbl_audio_stats = tk.Label(
            self.left_deck,
            text="RMS: 0.000 // LOW: 0.00 // MID: 0.00",
            font=("Consolas", 8),
            fg=t["dim"],
            bg="#000000"
        )
        self.lbl_audio_stats.pack(anchor="w")

        # 4. Quick Action Directive Buttons
        tk.Label(self.left_deck, text="◆ QUICK DIRECTIVES ◆", font=("Consolas", 9, "bold"), fg=t["secondary"], bg="#000000").pack(anchor="w", pady=(10, 4))
        actions = [
            ("📋 DAILY BRIEFING", "daily briefing"),
            ("⚡ SYSTEM VITALS", "system vitals"),
            ("🔒 LOCK WORKSTATION", "lock my device"),
            ("🔓 UNLOCK SYSTEM", "unlock my device")
        ]
        for l, cmd in actions:
            btn = tk.Button(
                self.left_deck,
                text=l,
                font=("Consolas", 8, "bold"),
                fg=t["text"],
                bg=t["card_bg"],
                activebackground=t["primary"],
                activeforeground="#000",
                relief="flat",
                pady=4,
                anchor="w",
                padx=8,
                command=lambda c=cmd: self._trigger_quick_action(c)
            )
            btn.pack(fill="x", pady=2)

    def _build_center_deck(self):
        """Constructs Center Deck: 3D Holographic Wireframe Model & Console."""
        t = self.theme

        # 3D Model Selector Header
        model_ctrls = tk.Frame(self.center_deck, bg="#000000")
        model_ctrls.pack(fill="x", pady=(0, 4))

        tk.Label(model_ctrls, text="3D HOLOGRAPHIC OBJECT:", font=("Consolas", 8, "bold"), fg=t["dim"], bg="#000000").pack(side="left")

        models = [
            ("🎭 HELMET", "helmet"),
            ("⚛ REACTOR", "reactor"),
            ("🌍 GLOBE", "globe"),
            ("🧊 TESSERACT", "tesseract"),
            ("✈ DRONE", "drone")
        ]
        for lbl, mid in models:
            b = tk.Button(
                model_ctrls,
                text=lbl,
                font=("Consolas", 8, "bold"),
                fg=t["primary"],
                bg=t["card_bg"],
                activebackground=t["primary"],
                activeforeground="#000",
                relief="flat",
                padx=6,
                pady=1,
                command=lambda m=mid: self.set_3d_model(m)
            )
            b.pack(side="left", padx=3)

        # 3D Holographic Canvas (Pitch Black #000000)
        self.canvas_3d = tk.Canvas(
            self.center_deck,
            height=280,
            bg="#000000",
            highlightthickness=1,
            highlightbackground=t["border"]
        )
        self.canvas_3d.pack(fill="x", pady=(0, 8))

        # Mouse Drag Binding for 3D Rotation
        self.canvas_3d.bind("<ButtonPress-1>", self._on_3d_drag_start)
        self.canvas_3d.bind("<B1-Motion>", self._on_3d_drag_motion)
        self.canvas_3d.bind("<MouseWheel>", self._on_3d_zoom)

        # Cyber Terminal Console
        console_frame = tk.Frame(self.center_deck, bg="#000000")
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
        self.console.insert("end", "[J.A.R.V.I.S. Hologram Engine]: Projection matrix active. Pitch-black backdrop primed.\n")
        self.console.insert("end", "[Interactive 3D]: Drag mouse to rotate 3D wireframe. Press F11 for Projector mode.\n\n")
        self.console.config(state="disabled")

        # Command Input Dock
        dock_frame = tk.Frame(self.center_deck, bg="#000000")
        dock_frame.pack(fill="x")

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

        self.btn_send = tk.Button(
            dock_frame,
            text="⚡ TRANSMIT",
            font=("Consolas", 9, "bold"),
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

        self.btn_silence = tk.Button(
            dock_frame,
            text="⏹ SILENCE",
            font=("Consolas", 9, "bold"),
            fg=t["danger"],
            bg="#1f060c",
            activebackground=t["danger"],
            activeforeground="#fff",
            relief="flat",
            padx=10,
            pady=6,
            command=self.silence_vocalizer
        )
        self.btn_silence.pack(side="left", padx=(0, 4))

        self.btn_stealth = tk.Button(
            dock_frame,
            text="👁 STEALTH",
            font=("Consolas", 9, "bold"),
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
        """Constructs Right Deck: Interactive Tasks / To-Do List & Hardware Vitals."""
        t = self.theme

        # 1. Interactive To-Do List / Task Matrix
        lbl_head = tk.Label(self.right_deck, text="◆ PROJECT TASKS & TO-DO ◆", font=("Consolas", 9, "bold"), fg=t["primary"], bg="#000000")
        lbl_head.pack(anchor="w", pady=(0, 4))

        # Task Entry Form
        task_add_wrap = tk.Frame(self.right_deck, bg="#000000")
        task_add_wrap.pack(fill="x", pady=(0, 6))

        self.entry_new_task = tk.Entry(
            task_add_wrap,
            font=("Consolas", 9),
            bg=t["card_bg"],
            fg=t["text"],
            insertbackground=t["primary"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=t["border"]
        )
        self.entry_new_task.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.entry_new_task.bind("<Return>", lambda e: self._add_ui_task())

        btn_add = tk.Button(
            task_add_wrap,
            text="+ ADD",
            font=("Consolas", 8, "bold"),
            fg=t["primary"],
            bg=t["card_bg"],
            relief="flat",
            command=self._add_ui_task
        )
        btn_add.pack(side="right")

        # Scrollable Task Items Container
        self.tasks_container = tk.Frame(self.right_deck, bg="#000000")
        self.tasks_container.pack(fill="both", expand=True, pady=(0, 8))
        self._refresh_task_items()

        # 2. Hardware Vitals Arc Gauges
        tk.Label(self.right_deck, text="◆ SYSTEM HARDWARE VITALS ◆", font=("Consolas", 9, "bold"), fg=t["secondary"], bg="#000000").pack(anchor="w", pady=(8, 4))

        self.canvas_cpu = tk.Canvas(
            self.right_deck,
            height=110,
            bg="#000000",
            highlightthickness=1,
            highlightbackground=t["border"]
        )
        self.canvas_cpu.pack(fill="x", pady=(0, 6))

        self.lbl_cpu_text = tk.Label(self.right_deck, text="CPU: 0.0%", font=("Consolas", 8), fg=t["text"], bg="#000000")
        self.lbl_cpu_text.pack(anchor="w")
        self.lbl_ram_text = tk.Label(self.right_deck, text="RAM: 0.0%", font=("Consolas", 8), fg=t["text"], bg="#000000")
        self.lbl_ram_text.pack(anchor="w")

    def _refresh_task_items(self):
        """Renders interactive To-Do checkboxes in Right Deck."""
        for child in self.tasks_container.winfo_children():
            child.destroy()

        t = self.theme
        for idx, item in enumerate(self.tasks):
            f = tk.Frame(self.tasks_container, bg="#000000")
            f.pack(fill="x", pady=2)

            check_mark = "☑" if item["done"] else "☐"
            col = t["dim"] if item["done"] else t["text"]

            btn_toggle = tk.Button(
                f,
                text=check_mark,
                font=("Consolas", 9, "bold"),
                fg=t["primary"] if item["done"] else t["secondary"],
                bg="#000000",
                activebackground="#000000",
                relief="flat",
                bd=0,
                command=lambda i=idx: self._toggle_task(i)
            )
            btn_toggle.pack(side="left", padx=(0, 4))

            lbl_txt = tk.Label(
                f,
                text=item["text"],
                font=("Consolas", 8),
                fg=col,
                bg="#000000",
                anchor="w",
                wraplength=220,
                justify="left"
            )
            lbl_txt.pack(side="left", fill="x", expand=True)

            btn_del = tk.Button(
                f,
                text="✕",
                font=("Consolas", 7),
                fg=t["danger"],
                bg="#000000",
                relief="flat",
                bd=0,
                command=lambda i=idx: self._delete_task(i)
            )
            btn_del.pack(side="right")

    def _toggle_task(self, idx: int):
        if 0 <= idx < len(self.tasks):
            self.tasks[idx]["done"] = not self.tasks[idx]["done"]
            self._play_fx("target_lock")
            self._refresh_task_items()

    def _delete_task(self, idx: int):
        if 0 <= idx < len(self.tasks):
            del self.tasks[idx]
            self._refresh_task_items()

    def _add_ui_task(self):
        txt = self.entry_new_task.get().strip()
        if txt:
            self.tasks.append({"text": txt, "done": False})
            self.entry_new_task.delete(0, "end")
            self._play_fx("target_lock")
            self._refresh_task_items()
            self.append_log("TASK", f"Added to-do item: '{txt}'.")

    # ─────────────────────────────────────────────────────────────────────────
    # 3D MOUSE MANIPULATION
    # ─────────────────────────────────────────────────────────────────────────
    def _on_3d_drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self.auto_spin = False

    def _on_3d_drag_motion(self, event):
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        self.model_yaw += dx * 0.015
        self.model_pitch += dy * 0.015
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_3d_zoom(self, event):
        if event.delta > 0:
            self.model_scale = min(2.5, self.model_scale * 1.1)
        else:
            self.model_scale = max(0.4, self.model_scale * 0.9)

    # ─────────────────────────────────────────────────────────────────────────
    # 3D WIREFRAME PROJECTION ENGINE
    # ─────────────────────────────────────────────────────────────────────────
    def _project_3d(self, x, y, z, cx, cy, fov=240, dist=260):
        # Scale
        s = self.model_scale
        x, y, z = x * s, y * s, z * s

        # Rotate Yaw (around Y)
        cos_y, sin_y = math.cos(self.model_yaw), math.sin(self.model_yaw)
        x1 = x * cos_y + z * sin_y
        y1 = y
        z1 = -x * sin_y + z * cos_y

        # Rotate Pitch (around X)
        cos_p, sin_p = math.cos(self.model_pitch), math.sin(self.model_pitch)
        x2 = x1
        y2 = y1 * cos_p - z1 * sin_p
        z2 = y1 * sin_p + z1 * cos_p

        # Perspective
        depth = z2 + dist
        if depth < 10:
            depth = 10
        proj_scale = fov / depth
        px = cx + x2 * proj_scale
        py = cy - y2 * proj_scale
        return px, py, depth

    def _draw_3d_wireframe(self, canvas, cx, cy, t_style):
        from ui.mesh_3d_engine import holographic_3d
        holographic_3d.yaw = self.model_yaw
        holographic_3d.pitch = self.model_pitch
        holographic_3d.scale = self.model_scale
        holographic_3d.auto_spin = self.auto_spin
        if holographic_3d.active_mesh.name.lower() != self.active_3d_model.lower():
            holographic_3d.set_mesh(self.active_3d_model)

        energy = 0.0
        try:
            energy = audio_visualizer.get_energy()
        except Exception:
            pass

        holographic_3d.project_and_render(canvas, cx, cy, t_style, audio_energy=energy)

    # ─────────────────────────────────────────────────────────────────────────
    # ANIMATION LOOP (~25 FPS)
    # ─────────────────────────────────────────────────────────────────────────
    def _animate_reactor(self):
        c3 = self.canvas_3d
        c3.delete("all")
        t_style = self.theme

        w = c3.winfo_width() or 560
        h = c3.winfo_height() or 280
        cx = w // 2
        cy = h // 2

        now = time.time()
        if self.auto_spin:
            self.model_yaw += 0.02

        # 1. Holographic Targeting Reticles & Distance Rings
        c3.create_oval(cx - 130, cy - 130, cx + 130, cy + 130, outline=t_style["border"], width=1, dash=(2, 6))
        c3.create_line(cx - 150, cy, cx + 150, cy, fill=t_style["border"], dash=(1, 5))
        c3.create_line(cx, cy - 130, cx, cy + 130, fill=t_style["border"], dash=(1, 5))

        # Corner Telemetry Brackets ⌜ ⌝ ⌞ ⌟
        brk_len = 16
        c3.create_line(20, 20, 20 + brk_len, 20, fill=t_style["primary"], width=2)
        c3.create_line(20, 20, 20, 20 + brk_len, fill=t_style["primary"], width=2)
        c3.create_line(w - 20, 20, w - 20 - brk_len, 20, fill=t_style["primary"], width=2)
        c3.create_line(w - 20, 20, w - 20, 20 + brk_len, fill=t_style["primary"], width=2)
        c3.create_line(20, h - 20, 20 + brk_len, h - 20, fill=t_style["primary"], width=2)
        c3.create_line(20, h - 20, 20, h - 20 - brk_len, fill=t_style["primary"], width=2)
        c3.create_line(w - 20, h - 20, w - 20 - brk_len, h - 20, fill=t_style["primary"], width=2)
        c3.create_line(w - 20, h - 20, w - 20, h - 20 - brk_len, fill=t_style["primary"], width=2)

        # 2. Render Active 3D Wireframe Model
        self._draw_3d_wireframe(c3, cx, cy, t_style)

        # 3. Floating Hologram Telemetry Data Text
        c3.create_text(26, 26, text=f"MODEL: {self.active_3d_model.upper()}", font=("Consolas", 8, "bold"), fill=t_style["primary"], anchor="nw")
        c3.create_text(26, 38, text=f"YAW: {math.degrees(self.model_yaw) % 360:.1f}° // PITCH: {math.degrees(self.model_pitch) % 360:.1f}°", font=("Consolas", 7), fill=t_style["dim"], anchor="nw")

        # 4. Render Audio Spectrum (Left Deck)
        self._animate_spectrum()

        # 5. Hardware Vitals Update
        self._update_hardware_telemetry()

        # 6. Poll IPC commands and broadcast state
        try:
            for ipc_cmd in hud_controller.poll_pending_commands():
                hud_controller._execute_direct_command(ipc_cmd)
        except Exception:
            pass

        if now - getattr(self, "_last_state_broadcast", 0.0) > 1.0:
            self._last_state_broadcast = now
            try:
                hud_controller.update_state(
                    is_fullscreen=self.is_fullscreen,
                    active_model=self.active_3d_model,
                    yaw=self.model_yaw,
                    pitch=self.model_pitch,
                    scale=self.model_scale,
                    auto_spin=self.auto_spin,
                    theme_name=self.theme.get("name", "STARK HOLOGRAPHIC CYAN")
                )
            except Exception:
                pass

        self.root.after(16, self._animate_reactor)

    def _animate_spectrum(self):
        """Renders 24-Band Equalizer in Left Deck."""
        cs = self.canvas_spectrum
        cs.delete("all")
        t_style = self.theme
        w = cs.winfo_width() or 260
        h = cs.winfo_height() or 120

        bands = audio_visualizer.get_bands()
        bars = audio_visualizer.get_bars()
        energy = bands.get("rms", 0.0)
        low = bands.get("low", 0.0)
        mid = bands.get("mid", 0.0)

        self.lbl_audio_stats.config(text=f"RMS: {energy:.3f} // LOW: {low:.2f} // MID: {mid:.2f}")

        num_bars = 24
        bar_w = 7
        spacing = 3
        total_w = num_bars * (bar_w + spacing) - spacing
        start_x = max(6, (w - total_w) // 2)
        base_y = h - 6

        raw_bars = bars if bars else [0.08] * num_bars
        t = time.time() * 3
        for i in range(num_bars):
            val = raw_bars[i % len(raw_bars)]
            bx = start_x + i * (bar_w + spacing)
            bh = int(val * 48.0) + int(math.sin(t + i * 0.5) * 2)
            bh = max(3, min(h - 12, bh))

            col = t_style["secondary"] if (i % 6 == 0 or energy > 0.22) else t_style["primary"]
            cs.create_rectangle(bx, base_y - bh, bx + bar_w, base_y, fill=col, outline="")
            cs.create_rectangle(bx, base_y - bh, bx + bar_w, base_y - bh + 2, fill="#ffffff", outline="")

    def _update_hardware_telemetry(self):
        """Refreshes hardware telemetry and weather every 1.5s."""
        now = time.time()
        # Update clock every frame
        self.lbl_time_large.config(text=datetime.now().strftime("%I:%M:%S %p"))
        self.lbl_date_sub.config(text=datetime.now().strftime("%A, %B %d, %Y").upper())

        if now - self._last_vitals_update < 1.5:
            return

        self._last_vitals_update = now
        try:
            self._cached_cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            self._cached_ram = mem.percent

            self.lbl_cpu_text.config(text=f"CPU LOAD: {self._cached_cpu:.1f}%")
            self.lbl_ram_text.config(text=f"RAM: {self._cached_ram:.1f}% ({mem.used // (1024*1024)}MB / {mem.total // (1024*1024)}MB)")
        except Exception:
            pass

        # Fetch Weather every 10 minutes
        if now - self._weather_last_fetch > 600 or self._weather_last_fetch == 0:
            self._weather_last_fetch = now
            def _fetch_w():
                try:
                    w_str = get_weather()
                    self._cached_weather = w_str
                    self.root.after(0, lambda: self.lbl_weather_info.config(text=self._cached_weather))
                except Exception:
                    pass
            threading.Thread(target=_fetch_w, daemon=True).start()

        self._draw_cpu_gauge()

    def _draw_cpu_gauge(self):
        c = self.canvas_cpu
        c.delete("all")
        t = self.theme

        cx, cy = 60, 55
        r = 38
        c.create_arc(cx - r, cy - r, cx + r, cy + r, start=-30, extent=240, style="arc", outline=t["border"], width=6)

        cpu_pct = min(100.0, max(0.0, self._cached_cpu))
        fill_extent = (cpu_pct / 100.0) * 240
        arc_color = t["primary"] if cpu_pct < 65 else (t["secondary"] if cpu_pct < 85 else t["danger"])
        c.create_arc(cx - r, cy - r, cx + r, cy + r, start=-30, extent=fill_extent, style="arc", outline=arc_color, width=6)
        c.create_text(cx, cy, text=f"{int(cpu_pct)}%", font=("Consolas", 11, "bold"), fill=t["text"])

        rx, ry = 120, 30
        rw, rh = 95, 12
        c.create_text(rx, ry - 10, text="RAM LOAD", font=("Consolas", 7, "bold"), fill=t["dim"], anchor="w")
        c.create_rectangle(rx, ry, rx + rw, ry + rh, fill="#000000", outline=t["border"])
        ram_w = int((self._cached_ram / 100.0) * rw)
        c.create_rectangle(rx, ry, rx + ram_w, ry + rh, fill=t["primary"], outline="")
        c.create_text(rx, ry + rh + 16, text="LINK: 0.8ms // SYNCD", font=("Consolas", 7), fill=t["secondary"], anchor="w")

    # ─────────────────────────────────────────────────────────────────────────
    # CONSOLE & DIRECTIVES
    # ─────────────────────────────────────────────────────────────────────────
    def _trigger_quick_action(self, cmd: str):
        self._play_fx("target_lock")
        self.entry.delete(0, "end")
        self.entry.insert(0, cmd)
        self.send_directive()

    def append_log(self, sender: str, msg: str):
        t_str = datetime.now().strftime("%H:%M:%S")
        self.console.config(state="normal")
        self.console.insert("end", f"[{t_str}] [{sender}] >> {msg}\n\n")
        self.console.see("end")
        self.console.config(state="disabled")

    def silence_vocalizer(self):
        stop_speaking()
        self._play_fx("target_lock")
        self.append_log("SYSTEM", "Acoustic vocalization silenced via barge-in command.")

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
            self.append_log("SYSTEM", "Microphone listening for directive...")
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
        self.conversation_active = not self.conversation_active
        t = self.theme
        if self.conversation_active:
            self.btn_conversation.config(text="💬 TALK: ACTIVE", fg="#000000", bg=t["secondary"])
            self.append_log("SYSTEM", "Continuous voice conversation mode engaged. Speak naturally with Jarvis.")
            speak("Continuous voice conversation mode engaged, sir. I am listening continuously.")

            def _conv_worker():
                listener.start_conversation_session(self._handle_conversation_turn)
                self.conversation_active = False
                self.root.after(0, lambda: self.btn_conversation.config(text="💬 CONVERSATION", fg=t["secondary"], bg="#1f1402"))
                self.root.after(0, lambda: self.append_log("SYSTEM", "Voice conversation session concluded. Reverting to ambient standby."))

            threading.Thread(target=_conv_worker, daemon=True).start()
        else:
            listener.in_conversation_mode = False
            self.btn_conversation.config(text="💬 CONVERSATION", fg=t["secondary"], bg="#1f1402")
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
        self.root.withdraw()
        print("[Stealth Mode]: J.A.R.V.I.S. Tactical HUD minimized. Press Ctrl+Alt+J or say 'Hey Jarvis' to summon.")

    def summon_from_hotkey(self):
        self.root.after(0, self.restore_hud)

    def restore_hud(self):
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(600, lambda: self.root.attributes("-topmost", False))
        self.root.focus_force()
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, config.HUD_WINDOW_TITLE)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        self.entry.focus_set()
        self.append_log("SYSTEM", "Tactical HUD summoned from stealth mode.")

    def run(self):
        listener.start_wake_word_daemon(self.handle_voice_directive)
        try:
            self.root.mainloop()
        finally:
            hud_controller.unregister_hud_instance()
            global_hotkey.stop()
            audio_visualizer.stop()


def launch_hud():
    hud = TacticalHUD()
    hud.run()

if __name__ == "__main__":
    launch_hud()
