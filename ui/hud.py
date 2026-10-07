import tkinter as tk
from tkinter import ttk
import threading
import math
import time
from core.brain import brain
from core.voice import speak, stop_speaking
from core.listener import listener
from core.audio_visualizer import audio_visualizer
from tools.global_hotkey import global_hotkey
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
    Mark-III Stark Industries Holographic Tactical HUD.
    Features glowing arc reactor audio visualizer, live console,
    hands-free voice wake-word toggle, barge-in silence controls, stealth mode,
    and system-wide global hotkey summoning (Ctrl+Alt+J / Ctrl+Shift+J).
    """

    def __init__(self):
        _attach_to_interactive_desktop()
        self.root = tk.Tk()
        self.root.title(config.HUD_WINDOW_TITLE)
        # Center Tactical HUD dynamically on display
        w, h = 920, 680
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.configure(bg="#020813")

        # Set application icon if available
        try:
            if config.IRONMAN_ICO_PATH.exists():
                self.root.iconbitmap(str(config.IRONMAN_ICO_PATH))
            else:
                self.root.iconbitmap("assets/ironman.ico")
        except Exception:
            pass

        # Visual styling
        self.cyan = "#00e5ff"
        self.gold = "#d4af37"
        self.red = "#ff3344"
        self.dark_blue = "#061326"

        self.wake_active = True

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

    def _build_ui(self):
        # Header Frame
        hdr = tk.Frame(self.root, bg="#020813", pady=10)
        hdr.pack(fill="x")

        lbl = tk.Label(hdr, text="◆ J.A.R.V.I.S. // STARK TACTICAL INTERFACE ◆", font=("Segoe UI", 14, "bold"), fg=self.cyan, bg="#020813")
        lbl.pack()

        sub_frame = tk.Frame(hdr, bg="#020813")
        sub_frame.pack(pady=4)

        sub = tk.Label(sub_frame, text="BUTLER AGENDA, AUTONOMY & GLOBAL SUMMON (Ctrl+Alt+J)", font=("Segoe UI", 9), fg=self.gold, bg="#020813")
        sub.pack(side="left", padx=10)

        # Wake Word Toggle Button
        self.btn_wake = tk.Button(
            sub_frame,
            text="🔔 WAKE: ON",
            font=("Segoe UI", 8, "bold"),
            fg=self.cyan,
            bg="#0c254c",
            relief="flat",
            padx=8,
            command=self.toggle_wake_word
        )
        self.btn_wake.pack(side="right", padx=10)

        # Voice Conversation Mode Button
        self.conversation_active = False
        self.btn_conversation = tk.Button(
            sub_frame,
            text="💬 CONVERSATION",
            font=("Segoe UI", 8, "bold"),
            fg=self.gold,
            bg="#261b04",
            relief="flat",
            padx=8,
            command=self.toggle_conversation_mode
        )
        self.btn_conversation.pack(side="right", padx=6)

        # Canvas for Arc Reactor Visualizer & 16-Band Real-Time Audio Equalizer
        self.canvas = tk.Canvas(self.root, width=280, height=245, bg="#020813", highlightthickness=0)
        self.canvas.pack(pady=4)

        # Output Console
        self.console = tk.Text(self.root, height=12, bg=self.dark_blue, fg="#ffffff", font=("Consolas", 10), insertbackground=self.cyan, relief="flat", padx=10, pady=10)
        self.console.pack(fill="both", expand=True, padx=20, pady=8)
        self.console.insert("end", "[J.A.R.V.I.S. Mark-III]: Core initialized. All offline and online subroutines armed.\n")
        self.console.insert("end", "[Audio Sentinel]: Hands-free wake word active. Say 'Hey Jarvis' or press Ctrl+Alt+J.\n\n")
        self.console.config(state="disabled")

        # Controls & Input Frame
        inp_frame = tk.Frame(self.root, bg="#020813", padx=20, pady=10)
        inp_frame.pack(fill="x")

        # Voice Push-To-Talk Button
        btn_mic = tk.Button(inp_frame, text="🎤", font=("Segoe UI", 12), fg=self.gold, bg="#1a1202", activebackground=self.gold, activeforeground="#000", relief="flat", padx=10, command=self.trigger_mic)
        btn_mic.pack(side="left", padx=(0, 8))

        self.entry = tk.Entry(inp_frame, font=("Segoe UI", 12), bg="#091b36", fg="#ffffff", insertbackground=self.cyan, relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.send_directive())

        # Transmit Button
        btn_send = tk.Button(inp_frame, text="TRANSMIT", font=("Segoe UI", 10, "bold"), fg=self.cyan, bg="#0c254c", activebackground=self.cyan, activeforeground="#000", relief="flat", padx=14, command=self.send_directive)
        btn_send.pack(side="left", padx=(0, 8))

        # Stealth Mode Button (Minimizes HUD to background)
        btn_stealth = tk.Button(
            inp_frame,
            text="👁 STEALTH",
            font=("Segoe UI", 9, "bold"),
            fg=self.gold,
            bg="#1a1402",
            activebackground=self.gold,
            activeforeground="#000",
            relief="flat",
            padx=10,
            command=self.enter_stealth_mode
        )
        btn_stealth.pack(side="right", padx=(0, 6))

        # Silence / Barge-In Button
        btn_silence = tk.Button(inp_frame, text="⏹ SILENCE", font=("Segoe UI", 9, "bold"), fg=self.red, bg="#26080b", activebackground=self.red, activeforeground="#fff", relief="flat", padx=10, command=self.silence_vocalizer)
        btn_silence.pack(side="right")

    def _animate_reactor(self):
        self.canvas.delete("all")
        cx, cy, r = 140, 100, 72
        t = time.time() * 2

        bands = audio_visualizer.get_bands()
        bars = audio_visualizer.get_bars()

        energy = bands["rms"]
        low = bands["low"]
        mid = bands["mid"]
        state = bands.get("state", "idle")

        # Color shifting based on butler state & acoustic energy
        if state == "listening" or energy > 0.18:
            core_fill = self.gold
            spoke_color = self.gold
            ring_outline = "#ffaa00"
            ring_width = 3
        elif state == "speaking":
            core_fill = "#ffaa00"
            spoke_color = self.cyan
            ring_outline = self.cyan
            ring_width = 3
        else:
            core_fill = self.cyan
            spoke_color = self.cyan
            ring_outline = self.cyan
            ring_width = 2

        # Outer pulsing rings dynamically expanded by bass frequencies
        pulse = (low * 20.0) + (math.sin(t) * 3)
        self.canvas.create_oval(cx - r - pulse, cy - r - pulse, cx + r + pulse, cy + r + pulse, outline=ring_outline, width=ring_width)
        self.canvas.create_oval(cx - 45, cy - 45, cx + 45, cy + 45, outline=self.gold, width=3)

        # Core reactor dot expanded by loudness
        core_r = 18 + int(energy * 10)
        self.canvas.create_oval(cx - core_r, cy - core_r, cx + core_r, cy + core_r, fill=core_fill, outline="#ffffff")

        # Rotating spokes dynamically stretched by speech mid frequencies
        spoke_stretch = mid * 26.0
        for i in range(8):
            ang = t + i * (math.pi / 4)
            x1 = cx + 50 * math.cos(ang)
            y1 = cy + 50 * math.sin(ang)
            x2 = cx + (70 + spoke_stretch) * math.cos(ang)
            y2 = cy + (70 + spoke_stretch) * math.sin(ang)
            self.canvas.create_line(x1, y1, x2, y2, fill=spoke_color, width=2)

        # 16-Band Real-Time Audio Equalizer Bars at base of Arc-Reactor
        bar_w = 8
        spacing = 6
        num_bars = len(bars)
        total_w = num_bars * (bar_w + spacing) - spacing
        start_x = cx - (total_w // 2)
        base_y = 236

        for i, val in enumerate(bars):
            bx = start_x + i * (bar_w + spacing)
            bh = int(val * 32.0)
            b_color = self.gold if (i % 4 == 0 or energy > 0.22) else self.cyan
            self.canvas.create_rectangle(bx, base_y - bh, bx + bar_w, base_y, fill=b_color, outline="")

        self.root.after(45, self._animate_reactor)

    def append_log(self, sender: str, msg: str):
        self.console.config(state="normal")
        self.console.insert("end", f"[{sender}]: {msg}\n\n")
        self.console.see("end")
        self.console.config(state="disabled")

    def silence_vocalizer(self):
        stop_speaking()
        self.append_log("SYSTEM", "Acoustic vocalization silenced.")

    def toggle_wake_word(self):
        self.wake_active = not self.wake_active
        if self.wake_active:
            self.btn_wake.config(text="🔔 WAKE: ON", fg=self.cyan, bg="#0c254c")
            listener.start_wake_word_daemon(self.handle_voice_directive)
            self.append_log("SYSTEM", "Auditory wake-word daemon armed ('Hey Jarvis').")
        else:
            self.btn_wake.config(text="🔕 WAKE: OFF", fg=self.red, bg="#26080b")
            listener.stop_wake_word_daemon()
            self.append_log("SYSTEM", "Auditory wake-word daemon disarmed.")

    def trigger_mic(self):
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
        """Toggles continuous multi-turn hands-free voice conversation."""
        self.conversation_active = not self.conversation_active
        if self.conversation_active:
            self.btn_conversation.config(text="💬 TALK: ACTIVE", fg="#000000", bg=self.gold)
            self.append_log("SYSTEM", "Continuous voice conversation mode engaged. Speak naturally with Jarvis.")
            speak("Continuous voice conversation mode engaged, sir. I am listening continuously.")

            def _conv_worker():
                listener.start_conversation_session(self._handle_conversation_turn)
                self.conversation_active = False
                self.root.after(0, lambda: self.btn_conversation.config(text="💬 CONVERSATION", fg=self.gold, bg="#261b04"))
                self.root.after(0, lambda: self.append_log("SYSTEM", "Voice conversation session concluded. Reverting to ambient standby."))

            threading.Thread(target=_conv_worker, daemon=True).start()
        else:
            listener.in_conversation_mode = False
            self.btn_conversation.config(text="💬 CONVERSATION", fg=self.gold, bg="#261b04")
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
