"""
J.A.R.V.I.S. 3-Dimensional Holographic Projector Display Window.
Interactive, fullscreen-capable optical projection window for desktop,
secondary monitors, and physical holographic prism displays.
"""

import argparse
import json
import logging
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk
from tkinter import ttk

import config
from core.audio_visualizer import audio_visualizer
from core.projector_system import PROJECTOR_IPC_FILE, projector_system
from ui.projector_3d import Projector3DEngine, ProjectorMeshLibrary, projector_3d_engine

logger = logging.getLogger("ProjectorWindow")


def _attach_to_interactive_desktop():
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
        except Exception:
            pass


def _enable_dwm_acrylic(hwnd: int, dark_mode: bool = True):
    """Applies native Windows DWM Acrylic Blur-Behind and immersive dark composition."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes
        dwmapi = ctypes.windll.dwmapi
        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        dark = wintypes.BOOL(dark_mode)
        dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), ctypes.sizeof(dark))
        # DWMWA_SYSTEMBACKDROP_TYPE = 38 (3 = Acrylic)
        acrylic_type = wintypes.DWORD(3)
        dwmapi.DwmSetWindowAttribute(hwnd, 38, ctypes.byref(acrylic_type), ctypes.sizeof(acrylic_type))
    except Exception:
        pass


class ProjectorWindow:
    """
    Dedicated 3D Holographic Optical Projector Interface.
    """

    WINDOW_TITLE = getattr(config, "PROJECTOR_WINDOW_TITLE", "J.A.R.V.I.S. // 3D HOLOGRAPHIC PROJECTOR SYSTEM")

    def __init__(
        self,
        mode: str = "standard",
        model: str = "helmet",
        monitor_index: int = 0,
        fullscreen: bool = False,
    ):
        _attach_to_interactive_desktop()
        self.root = tk.Tk()
        self.root.title(self.WINDOW_TITLE)
        self.root.configure(bg="#000000")

        self.engine: Projector3DEngine = projector_3d_engine
        self.mode: str = mode.lower()
        self.active_model_name: str = model.lower()
        self.engine.set_mesh(self.active_model_name)
        self.palette_key: str = "stark_cyan"
        self.is_fullscreen: bool = fullscreen
        self.monitor_index: int = monitor_index
        self.is_transparent: bool = (self.mode == "floating")
        self.show_osd: bool = True
        self.last_ipc_timestamp: float = time.time()
        self._is_running: bool = True

        # Mouse interaction state
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Position window on targeted display
        self._setup_window_geometry()

        # Build rendering canvas and OSD controls
        self._build_viewport()

        # Keyboard & mouse event bindings
        self._bind_events()

        # Register instance with system controller
        projector_system.register_window_instance(self)

        # Start animation and IPC polling loops
        self.root.after(20, self._render_loop)
        self.root.after(50, self._poll_ipc)

    def _setup_window_geometry(self):
        """Calculates window bounds on target monitor."""
        monitors = projector_system.enumerate_monitors()
        target_mon = monitors[self.monitor_index] if 0 <= self.monitor_index < len(monitors) else monitors[0]

        mx = target_mon["x"]
        my = target_mon["y"]
        mw = target_mon["width"]
        mh = target_mon["height"]

        if self.is_fullscreen:
            self.root.geometry(f"{mw}x{mh}+{mx}+{my}")
            self.root.attributes("-fullscreen", True)
        else:
            w, h = min(1200, mw - 100), min(800, mh - 100)
            x = mx + max(0, (mw - w) // 2)
            y = my + max(0, (mh - h) // 2)
            self.root.geometry(f"{w}x{h}+{x}+{y}")

        try:
            self.root.update_idletasks()
            _enable_dwm_acrylic(self.root.winfo_id())
        except Exception:
            pass

        if self.is_transparent:
            self._apply_transparency(True)

    def _apply_transparency(self, enable: bool):
        """Applies Windows chromakey / layered transparency for desktop hologram overlay."""
        self.is_transparent = enable
        if sys.platform == "win32":
            try:
                if enable:
                    self.root.wm_attributes("-transparentcolor", "#000000")
                    self.root.overrideredirect(True)
                else:
                    self.root.wm_attributes("-transparentcolor", "")
                    self.root.overrideredirect(False)
            except Exception as e:
                logger.warning(f"Failed to set transparent attributes: {e}")

    def _build_viewport(self):
        """Creates the projection viewport and tactical OSD HUD elements."""
        self.canvas = tk.Canvas(self.root, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # OSD Telemetry Bar (Top)
        self.osd_frame = tk.Frame(self.canvas, bg="#000000")
        self.osd_lbl_title = tk.Label(
            self.osd_frame,
            text="⫸ 3D HOLOGRAPHIC PROJECTOR // OPTICAL BEAM ONLINE",
            font=("Consolas", 10, "bold"),
            fg="#00f0ff",
            bg="#000000",
        )
        self.osd_lbl_title.pack(side="left", padx=8, pady=4)

        self.osd_lbl_meta = tk.Label(
            self.osd_frame,
            text="",
            font=("Consolas", 9),
            fg="#ffd700",
            bg="#000000",
        )
        self.osd_lbl_meta.pack(side="right", padx=8, pady=4)

        # Floating Bottom Quick Action Dock
        self.dock_frame = tk.Frame(self.canvas, bg="#000000")
        modes = [
            ("DIRECT BEAM", "standard"),
            ("4-WAY PYRAMID", "pyramid"),
            ("ANAGLYPH 3D", "anaglyph"),
            ("FLOATING DESKTOP", "floating"),
        ]
        for label, m_key in modes:
            btn = tk.Button(
                self.dock_frame,
                text=label,
                font=("Consolas", 8, "bold"),
                fg="#00f0ff",
                bg="#011024",
                activebackground="#00f0ff",
                activeforeground="#000000",
                relief="flat",
                padx=6,
                pady=2,
                command=lambda m=m_key: self.set_mode(m),
            )
            btn.pack(side="left", padx=3)

        btn_fs = tk.Button(
            self.dock_frame,
            text="⛶ FULLSCREEN (F11)",
            font=("Consolas", 8, "bold"),
            fg="#ffd700",
            bg="#1a1400",
            relief="flat",
            padx=6,
            pady=2,
            command=self.toggle_fullscreen,
        )
        btn_fs.pack(side="left", padx=3)

        btn_mesh = tk.Button(
            self.dock_frame,
            text="🔄 CYCLE MODEL (M)",
            font=("Consolas", 8, "bold"),
            fg="#00ff9d",
            bg="#001a10",
            relief="flat",
            padx=6,
            pady=2,
            command=self.cycle_model,
        )
        btn_mesh.pack(side="left", padx=3)

        btn_keystone = tk.Button(
            self.dock_frame,
            text="📐 KEYSTONE (K)",
            font=("Consolas", 8, "bold"),
            fg="#bb44ff",
            bg="#180424",
            relief="flat",
            padx=6,
            pady=2,
            command=self.toggle_keystone_calibration,
        )
        btn_keystone.pack(side="left", padx=3)

        btn_interf = tk.Button(
            self.dock_frame,
            text="⚡ INTERFERENCE (I)",
            font=("Consolas", 8, "bold"),
            fg="#ff2a55",
            bg="#24050d",
            relief="flat",
            padx=6,
            pady=2,
            command=self.toggle_interference,
        )
        btn_interf.pack(side="left", padx=3)

        self._update_osd_positions()

    def _update_osd_positions(self):
        """Positions OSD frames over the canvas."""
        w = max(400, self.root.winfo_width())
        h = max(300, self.root.winfo_height())
        if self.show_osd and not self.is_transparent:
            self.canvas.create_window(w // 2, 20, window=self.osd_frame, width=w - 40, tags="osd")
            self.canvas.create_window(w // 2, h - 25, window=self.dock_frame, tags="osd")

    def _bind_events(self):
        """Sets up mouse and keyboard event bindings."""
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_release)
        self.canvas.bind("<MouseWheel>", self._on_scroll_zoom)
        self.canvas.bind("<Button-3>", lambda e: self.cycle_model())
        self.canvas.bind("<Button-2>", lambda e: self.cycle_mode())

        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Escape>", lambda e: self.close_window())
        self.root.bind("<space>", lambda e: self.toggle_auto_spin())
        self.root.bind("<p>", lambda e: self.cycle_mode())
        self.root.bind("<P>", lambda e: self.cycle_mode())
        self.root.bind("<m>", lambda e: self.cycle_model())
        self.root.bind("<M>", lambda e: self.cycle_model())
        self.root.bind("<c>", lambda e: self.cycle_palette())
        self.root.bind("<C>", lambda e: self.cycle_palette())
        self.root.bind("<t>", lambda e: self.toggle_transparency())
        self.root.bind("<T>", lambda e: self.toggle_transparency())
        self.root.bind("<h>", lambda e: self.toggle_osd())
        self.root.bind("<H>", lambda e: self.toggle_osd())
        self.root.bind("<plus>", lambda e: self.adjust_depth(1.0))
        self.root.bind("<minus>", lambda e: self.adjust_depth(-1.0))
        self.root.bind("<equal>", lambda e: self.adjust_depth(1.0))
        self.root.bind("<k>", lambda e: self.toggle_keystone_calibration())
        self.root.bind("<K>", lambda e: self.toggle_keystone_calibration())
        self.root.bind("<i>", lambda e: self.toggle_interference())
        self.root.bind("<I>", lambda e: self.toggle_interference())
        self.root.bind("<Tab>", lambda e: self.cycle_keystone_corner())
        self.root.bind("<r>", lambda e: self.reset_keystone())
        self.root.bind("<R>", lambda e: self.reset_keystone())
        self.root.bind("<Up>", lambda e: self.adjust_active_keystone(0.0, -0.015))
        self.root.bind("<Down>", lambda e: self.adjust_active_keystone(0.0, 0.015))
        self.root.bind("<Left>", lambda e: self.adjust_active_keystone(-0.015, 0.0))
        self.root.bind("<Right>", lambda e: self.adjust_active_keystone(0.015, 0.0))

        self.root.bind("<Configure>", lambda e: self._on_resize())
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

    def _on_drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self.engine.auto_spin = False
        self.engine.vel_yaw = 0.0
        self.engine.vel_pitch = 0.0

    def _on_drag_motion(self, event):
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        self.engine.yaw = (self.engine.yaw + dx * 0.008) % (2 * math.pi)
        self.engine.pitch = max(-1.2, min(1.2, self.engine.pitch - dy * 0.008))
        self.engine.vel_yaw = dx * 0.003
        self.engine.vel_pitch = -dy * 0.003
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag_release(self, event):
        pass

    def _on_scroll_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.engine.scale = max(0.2, min(4.0, self.engine.scale * factor))

    def _on_resize(self):
        self._update_osd_positions()

    def set_mode(self, mode_name: str):
        """Switches projection mode."""
        m = mode_name.lower().strip()
        if m in projector_system.PROJECTION_MODES:
            self.mode = m
            if m == "floating":
                self._apply_transparency(True)
            else:
                if self.is_transparent:
                    self._apply_transparency(False)
            projector_system.update_state({"mode": self.mode})

    def cycle_mode(self):
        """Cycles to the next projection optical mode."""
        modes = projector_system.PROJECTION_MODES
        curr_idx = modes.index(self.mode) if self.mode in modes else 0
        new_mode = modes[(curr_idx + 1) % len(modes)]
        self.set_mode(new_mode)

    def set_model(self, model_name: str):
        """Switches active 3D model."""
        m = model_name.lower().strip()
        if m in projector_system.SUPPORTED_MODELS:
            self.active_model_name = m
            self.engine.set_mesh(m)
            projector_system.update_state({"model": self.active_model_name})

    def cycle_model(self):
        """Cycles to the next procedural 3D model."""
        models = projector_system.SUPPORTED_MODELS
        curr_idx = models.index(self.active_model_name) if self.active_model_name in models else 0
        new_model = models[(curr_idx + 1) % len(models)]
        self.set_model(new_model)

    def cycle_palette(self):
        """Cycles color palette."""
        pals = list(self.engine.PALETTE_COLORS.keys())
        curr_idx = pals.index(self.palette_key) if self.palette_key in pals else 0
        self.palette_key = pals[(curr_idx + 1) % len(pals)]
        projector_system.update_state({"palette": self.palette_key})

    def toggle_fullscreen(self):
        """Toggles fullscreen projector display."""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        projector_system.update_state({"fullscreen": self.is_fullscreen})
        self._update_osd_positions()

    def toggle_transparency(self):
        """Toggles floating transparent overlay."""
        self._apply_transparency(not self.is_transparent)
        projector_system.update_state({"transparent": self.is_transparent})

    def toggle_auto_spin(self):
        """Pauses/resumes rotation."""
        self.engine.auto_spin = not self.engine.auto_spin
        projector_system.update_state({"auto_spin": self.engine.auto_spin})

    def toggle_osd(self):
        """Toggles on-screen telemetry overlay."""
        self.show_osd = not self.show_osd
        if not self.show_osd:
            self.canvas.delete("osd")
        else:
            self._update_osd_positions()

    def adjust_depth(self, delta: float):
        """Increases or decreases stereoscopic parallax."""
        self.engine.parallax_offset = max(0.0, min(25.0, self.engine.parallax_offset + delta))
        projector_system.update_state({"parallax": self.engine.parallax_offset})

    def toggle_keystone_calibration(self):
        """Toggles 4-corner bilinear keystone calibration mode."""
        self.engine.calibration_mode = not self.engine.calibration_mode
        projector_system.update_state({"keystone_calibration": self.engine.calibration_mode})

    def cycle_keystone_corner(self):
        """Cycles active keystone calibration corner (TL, TR, BR, BL)."""
        self.engine.cycle_keystone_corner()

    def reset_keystone(self):
        """Resets keystone calibration warp to rectangle."""
        self.engine.reset_keystone()

    def adjust_active_keystone(self, dx: float, dy: float):
        """Nudges the active keystone corner."""
        if self.engine.calibration_mode:
            self.engine.adjust_keystone_corner(self.engine.active_corner, dx, dy)

    def toggle_interference(self):
        """Toggles video holographic optical wave interference."""
        if hasattr(self.engine, "interference") and self.engine.interference:
            self.engine.interference.enabled = not self.engine.interference.enabled
            projector_system.update_state({"interference_enabled": self.engine.interference.enabled})

    def close_window(self):
        """Exits the projector window."""
        self._is_running = False
        projector_system.unregister_window_instance()
        try:
            self.root.destroy()
        except Exception:
            pass

    def _poll_ipc(self):
        """Reads IPC command file and processes external directives."""
        if not self._is_running:
            return

        try:
            if PROJECTOR_IPC_FILE.exists():
                cmds = json.loads(PROJECTOR_IPC_FILE.read_text(encoding="utf-8"))
                new_cmds = [c for c in cmds if c.get("timestamp", 0) > self.last_ipc_timestamp]
                for c in new_cmds:
                    action = c.get("action", "")
                    params = c.get("params", {})
                    self.execute_command(action, **params)
                    self.last_ipc_timestamp = max(self.last_ipc_timestamp, c.get("timestamp", 0))
        except Exception:
            pass

        if self._is_running:
            self.root.after(60, self._poll_ipc)

    def execute_command(self, action: str, **kwargs):
        """Handles IPC command actions."""
        if action == "set_mode":
            self.set_mode(kwargs.get("mode", "standard"))
        elif action == "set_model":
            self.set_model(kwargs.get("model", "helmet"))
        elif action == "set_palette":
            pal = kwargs.get("palette", "stark_cyan")
            if pal in self.engine.PALETTE_COLORS:
                self.palette_key = pal
        elif action == "set_fullscreen":
            if bool(kwargs.get("fullscreen", False)) != self.is_fullscreen:
                self.toggle_fullscreen()
        elif action == "set_transparency":
            self._apply_transparency(bool(kwargs.get("transparent", False)))
        elif action == "set_auto_spin":
            self.engine.auto_spin = bool(kwargs.get("auto_spin", True))
        elif action == "set_parallax":
            self.engine.parallax_offset = float(kwargs.get("parallax", 6.0))
        elif action == "toggle_keystone":
            self.toggle_keystone_calibration()
        elif action == "toggle_interference":
            self.toggle_interference()
        elif action == "reset_keystone":
            self.reset_keystone()
        elif action == "set_keystone_corner":
            self.engine.set_keystone_corner(kwargs.get("corner", "TL"), kwargs.get("x", 0.0), kwargs.get("y", 0.0))
        elif action == "rotate":
            self.engine.yaw = float(kwargs.get("yaw", self.engine.yaw))
            self.engine.pitch = float(kwargs.get("pitch", self.engine.pitch))
            self.engine.auto_spin = False
        elif action == "elevate":
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(300, lambda: self.root.attributes("-topmost", False))
        elif action == "close":
            self.close_window()

    def _render_loop(self):
        """High-performance 50-60 FPS optical rendering loop."""
        if not self._is_running:
            return

        try:
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()

            if w > 50 and h > 50:
                # Clear frame canvas
                self.canvas.delete("all")

                # Advance rotational physics
                self.engine.update_physics()

                # Sample audio spectrum energy for reactive neon laser bloom
                audio_energy = 0.0
                try:
                    bands = audio_visualizer.get_frequency_bands()
                    audio_energy = sum(bands) / len(bands) if bands else 0.0
                except Exception:
                    pass

                cx, cy = w // 2, h // 2

                # Dispatch rendering based on active optical projection mode
                if self.mode == "pyramid":
                    self.engine.render_pyramid_4way(self.canvas, w, h, self.palette_key, audio_energy)
                elif self.mode == "anaglyph":
                    self.engine.render_anaglyph_3d(self.canvas, cx, cy, self.palette_key, audio_energy)
                else:
                    # standard & floating modes
                    self.engine.render_standard(self.canvas, cx, cy, self.palette_key, audio_energy)

                # Update metadata OSD
                if self.show_osd and not self.is_transparent:
                    interf_str = "ON" if (hasattr(self.engine, "interference") and self.engine.interference.enabled) else "OFF"
                    keystone_str = "CALIB" if self.engine.calibration_mode else ("WARP" if (self.engine.keystone_corners["TL"] != (0.0, 0.0) or self.engine.keystone_corners["TR"] != (1.0, 0.0)) else "FLAT")
                    meta_text = (
                        f"MODE: [{self.mode.upper()}] | "
                        f"MODEL: [{self.active_model_name.upper()}] | "
                        f"KEYSTONE: [{keystone_str}] | "
                        f"INTERF: [{interf_str}] | "
                        f"PARALLAX: {self.engine.parallax_offset:.1f}px | "
                        f"YAW: {math.degrees(self.engine.yaw):.0f}°"
                    )
                    self.osd_lbl_meta.config(text=meta_text)
                    self._update_osd_positions()

        except Exception as e:
            logger.warning(f"Projector render loop error: {e}")

        if self._is_running:
            self.root.after(20, self._render_loop)

    def run(self):
        """Runs the Tkinter event loop."""
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="J.A.R.V.I.S. 3D Holographic Projector System")
    parser.add_argument("--mode", default="standard", help="standard | pyramid | anaglyph | floating")
    parser.add_argument("--model", default="helmet", help="helmet | reactor | globe | tesseract | drone | gauntlet | emitter | neural_mesh | planetary_radar | quantum_dna")
    parser.add_argument("--monitor", type=int, default=0, help="Target monitor index (0=primary)")
    parser.add_argument("--fullscreen", action="store_true", help="Launch in borderless fullscreen mode")
    args = parser.parse_args()

    win = ProjectorWindow(
        mode=args.mode,
        model=args.model,
        monitor_index=args.monitor,
        fullscreen=args.fullscreen,
    )
    win.run()


if __name__ == "__main__":
    main()
