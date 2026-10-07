import tkinter as tk
from tkinter import ttk
import threading
import math
import time
from core.brain import brain
from core.voice import speak, stop_speaking
from core.listener import listener
import config

class TacticalHUD:
    """
    Mark-III Stark Industries Holographic Tactical HUD.
    Features glowing arc reactor audio visualizer, live console,
    hands-free voice wake-word toggle, barge-in silence controls, and directive transmitter.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(config.HUD_WINDOW_TITLE)
        self.root.geometry("920x680")
        self.root.configure(bg="#020813")

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

    def _build_ui(self):
        # Header Frame
        hdr = tk.Frame(self.root, bg="#020813", pady=10)
        hdr.pack(fill="x")

        lbl = tk.Label(hdr, text="◆ J.A.R.V.I.S. // STARK TACTICAL INTERFACE ◆", font=("Segoe UI", 14, "bold"), fg=self.cyan, bg="#020813")
        lbl.pack()

        sub_frame = tk.Frame(hdr, bg="#020813")
        sub_frame.pack(pady=4)

        sub = tk.Label(sub_frame, text="BUTLER AGENDA, AUTONOMY & MULTIMODAL PERCEPTION", font=("Segoe UI", 9), fg=self.gold, bg="#020813")
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

        # Canvas for Arc Reactor Visualizer
        self.canvas = tk.Canvas(self.root, width=220, height=220, bg="#020813", highlightthickness=0)
        self.canvas.pack(pady=6)

        # Output Console
        self.console = tk.Text(self.root, height=12, bg=self.dark_blue, fg="#ffffff", font=("Consolas", 10), insertbackground=self.cyan, relief="flat", padx=10, pady=10)
        self.console.pack(fill="both", expand=True, padx=20, pady=8)
        self.console.insert("end", "[J.A.R.V.I.S. Mark-III]: Core initialized. All offline and online subroutines armed.\n")
        self.console.insert("end", "[Audio Sentinel]: Hands-free wake word active. Say 'Hey Jarvis' or click 🎤.\n\n")
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

        # Silence / Barge-In Button
        btn_silence = tk.Button(inp_frame, text="⏹ SILENCE", font=("Segoe UI", 9, "bold"), fg=self.red, bg="#26080b", activebackground=self.red, activeforeground="#fff", relief="flat", padx=10, command=self.silence_vocalizer)
        btn_silence.pack(side="right")

    def _animate_reactor(self):
        self.canvas.delete("all")
        cx, cy, r = 110, 110, 80
        t = time.time() * 2

        # Outer pulsing rings
        pulse = math.sin(t) * 6
        self.canvas.create_oval(cx - r - pulse, cy - r - pulse, cx + r + pulse, cy + r + pulse, outline=self.cyan, width=2)
        self.canvas.create_oval(cx - 50, cy - 50, cx + 50, cy + 50, outline=self.gold, width=3)
        self.canvas.create_oval(cx - 20, cy - 20, cx + 20, cy + 20, fill=self.cyan, outline="#ffffff")

        # Rotating spokes
        for i in range(8):
            ang = t + i * (math.pi / 4)
            x1 = cx + 55 * math.cos(ang)
            y1 = cy + 55 * math.sin(ang)
            x2 = cx + 75 * math.cos(ang)
            y2 = cy + 75 * math.sin(ang)
            self.canvas.create_line(x1, y1, x2, y2, fill=self.cyan, width=2)

        self.root.after(50, self._animate_reactor)

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
        self.root.after(0, lambda: self.append_log("USER (Voice)", text))
        res = brain.think(text)
        self.root.after(0, lambda: self.append_log("J.A.R.V.I.S.", res))
        speak(res)

    def send_directive(self):
        cmd = self.entry.get().strip()
        if not cmd:
            return
        self.entry.delete(0, "end")
        self.append_log("USER", cmd)

        def _proc():
            res = brain.think(cmd)
            self.root.after(0, lambda: self.append_log("J.A.R.V.I.S.", res))
            speak(res)

        threading.Thread(target=_proc, daemon=True).start()

    def run(self):
        # Start voice daemon on launch
        listener.start_wake_word_daemon(self.handle_voice_directive)
        self.root.mainloop()

def launch_hud():
    hud = TacticalHUD()
    hud.run()

if __name__ == "__main__":
    launch_hud()
