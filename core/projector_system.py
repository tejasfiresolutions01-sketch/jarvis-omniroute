"""
J.A.R.V.I.S. 3-Dimensional Holographic Projector System & Spatial Optics Engine.
Features:
1. Multi-Mode Volumetric Optical Projection:
   - Standard Direct Beam: High-lux focused Stark holographic wireframe projection.
   - 4-Way Holographic Pyramid: Quad-perspective Pepper's Ghost projection for physical glass/acrylic prism pyramids.
   - Stereoscopic Anaglyph 3D: Real-time dual-eye chromatic parallax (Red/Cyan) for 3D glasses depth perception.
   - Floating Desktop Holo-Beam: Transparent, borderless desktop overlay with optional click-through.
2. Multi-Display & External Projector Enumeration:
   - Automatic detection of primary and secondary displays/projectors via Win32 Monitor APIs.
   - Targeted single-click or voice-directed output routing to any connected display.
3. Procedural & Custom 3D Models:
   - Mark-85 Helmet, Arc Reactor, Celestial Globe, 4D Tesseract, Stark Drone, Repulsor Gauntlet, Holo-Emitter.
   - Custom OBJ and STL mesh asset loading.
4. Cross-Process Zero-Latency IPC Command Pipeline:
   - Synchronizes state, rotation, zoom, mode switching, and palette across HUD, Voice, and Projector Window.
5. 100% Free Plan, zero cloud dependency, vectorized local mathematics.
"""

import json
import logging
import math
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

logger = logging.getLogger("ProjectorSystem")

PROJECTOR_IPC_FILE = config.DATA_DIR / "projector_ipc.json"
PROJECTOR_STATE_FILE = config.DATA_DIR / "projector_state.json"
_LOCK = threading.Lock()


class ProjectorSystem:
    """
    Central Controller and State Manager for the J.A.R.V.I.S. 3D Holographic Projector System.
    """

    PROJECTION_MODES = ["standard", "pyramid", "anaglyph", "floating"]
    SUPPORTED_MODELS = [
        "helmet", "reactor", "globe", "tesseract", "drone",
        "gauntlet", "emitter", "neural_mesh", "planetary_radar", "quantum_dna"
    ]
    PALETTES = ["stark_cyan", "mark_crimson", "quantum_emerald", "plasma_amber", "ultraviolet_violet"]

    def __init__(self):
        self._projector_proc: Optional[subprocess.Popen] = None
        self._active_window_instance = None
        self._last_spawn_time = 0.0
        self._ensure_storage()

    def _ensure_storage(self):
        """Initializes state and IPC files in data directory."""
        try:
            config.DATA_DIR.mkdir(parents=True, exist_ok=True)
            with _LOCK:
                if not PROJECTOR_IPC_FILE.exists():
                    PROJECTOR_IPC_FILE.write_text("[]", encoding="utf-8")
                if not PROJECTOR_STATE_FILE.exists():
                    initial_state = {
                        "is_active": False,
                        "mode": "standard",
                        "model": "helmet",
                        "palette": "stark_cyan",
                        "fullscreen": False,
                        "monitor_index": 0,
                        "yaw": 0.0,
                        "pitch": 0.2,
                        "scale": 1.0,
                        "auto_spin": True,
                        "parallax": 6.0,
                        "transparent": False,
                        "click_through": False,
                        "beam_lux": 100,
                        "timestamp": time.time(),
                    }
                    PROJECTOR_STATE_FILE.write_text(json.dumps(initial_state, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Error initializing projector storage: {e}")

    def get_state(self) -> Dict[str, Any]:
        """Returns the current state dictionary of the 3D Projector System."""
        try:
            with _LOCK:
                if PROJECTOR_STATE_FILE.exists():
                    return json.loads(PROJECTOR_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {
            "is_active": False,
            "mode": "standard",
            "model": "helmet",
            "palette": "stark_cyan",
            "fullscreen": False,
            "monitor_index": 0,
            "yaw": 0.0,
            "pitch": 0.2,
            "scale": 1.0,
            "auto_spin": True,
            "parallax": 6.0,
            "transparent": False,
            "click_through": False,
            "beam_lux": 100,
            "timestamp": time.time(),
        }

    def update_state(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Atomically updates the projector state file."""
        state = self.get_state()
        state.update(updates)
        state["timestamp"] = time.time()
        try:
            with _LOCK:
                PROJECTOR_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to write projector state: {e}")
        return state

    def enumerate_monitors(self) -> List[Dict[str, Any]]:
        """
        Enumerates all physical monitors and external projectors attached to the machine.
        Returns list of monitor descriptors with geometry and primary flag.
        """
        monitors = []
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes

                user32 = ctypes.windll.user32

                class MONITORINFOEXW(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", wintypes.DWORD),
                        ("rcMonitor", wintypes.RECT),
                        ("rcWork", wintypes.RECT),
                        ("dwFlags", wintypes.DWORD),
                        ("szDevice", wintypes.WCHAR * 32),
                    ]

                def monitor_enum_proc(hmonitor, hdc, lprect, lparam):
                    info = MONITORINFOEXW()
                    info.cbSize = ctypes.sizeof(MONITORINFOEXW)
                    if user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
                        rect = info.rcMonitor
                        x = rect.left
                        y = rect.top
                        w = rect.right - rect.left
                        h = rect.bottom - rect.top
                        is_primary = bool(info.dwFlags & 1)  # MONITORINFOF_PRIMARY = 1
                        monitors.append({
                            "index": len(monitors),
                            "name": info.szDevice,
                            "x": x,
                            "y": y,
                            "width": w,
                            "height": h,
                            "is_primary": is_primary,
                            "type": "Primary Display" if is_primary else "External Projector / Secondary Display"
                        })
                    return True

                MONITORENUMPROC = ctypes.WINFUNCTYPE(
                    ctypes.c_int,
                    wintypes.HMONITOR,
                    wintypes.HDC,
                    ctypes.POINTER(wintypes.RECT),
                    wintypes.LPARAM,
                )
                user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(monitor_enum_proc), 0)
            except Exception as e:
                logger.warning(f"Failed to enumerate Win32 monitors: {e}")

        if not monitors:
            # Fallback default monitor
            monitors.append({
                "index": 0,
                "name": "DISPLAY1",
                "x": 0,
                "y": 0,
                "width": 1920,
                "height": 1080,
                "is_primary": True,
                "type": "Primary Display"
            })
        return monitors

    def register_window_instance(self, window_instance):
        """Registers an active in-process Tkinter ProjectorWindow instance."""
        self._active_window_instance = window_instance
        self.update_state({"is_active": True})

    def unregister_window_instance(self):
        """Unregisters the projector window instance."""
        self._active_window_instance = None
        self.update_state({"is_active": False})

    def is_projector_open(self) -> bool:
        """Checks if the 3D Projector Window is currently running either in-process or via subprocess."""
        if self._active_window_instance is not None:
            try:
                return bool(self._active_window_instance.root.winfo_exists())
            except Exception:
                return False

        if self._projector_proc is not None and self._projector_proc.poll() is None:
            return True

        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = ctypes.windll.user32.FindWindowW(None, getattr(config, "PROJECTOR_WINDOW_TITLE", "J.A.R.V.I.S. // 3D HOLOGRAPHIC PROJECTOR SYSTEM"))
                return bool(hwnd)
            except Exception:
                pass
        return False

    def send_ipc_command(self, action: str, **kwargs) -> bool:
        """Dispatches an IPC command to the active projector window."""
        cmd = {"action": action, "timestamp": time.time(), "params": kwargs}

        # If in-process window is available, dispatch directly
        if self._active_window_instance is not None:
            try:
                handler = getattr(self._active_window_instance, f"handle_ipc_{action}", None)
                if callable(handler):
                    handler(**kwargs)
                    return True
                elif hasattr(self._active_window_instance, "execute_command"):
                    self._active_window_instance.execute_command(action, **kwargs)
                    return True
            except Exception as e:
                logger.warning(f"Error dispatching in-process IPC command '{action}': {e}")

        # Otherwise queue into IPC file
        try:
            with _LOCK:
                cmds = []
                if PROJECTOR_IPC_FILE.exists():
                    try:
                        cmds = json.loads(PROJECTOR_IPC_FILE.read_text(encoding="utf-8"))
                    except Exception:
                        cmds = []
                cmds.append(cmd)
                # Keep last 20 commands max
                cmds = cmds[-20:]
                PROJECTOR_IPC_FILE.write_text(json.dumps(cmds, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            logger.warning(f"Failed to queue projector IPC command '{action}': {e}")
            return False

    def activate_projector(
        self,
        mode: str = "standard",
        model: str = "helmet",
        monitor_index: int = 0,
        fullscreen: bool = False,
    ) -> bool:
        """
        Activates and displays the 3D Holographic Projector System.
        If already open, elevates it and updates mode/model. If closed, launches it.
        """
        mode = mode.lower().strip()
        if mode not in self.PROJECTION_MODES:
            mode = "standard"

        model = model.lower().strip()
        if model not in self.SUPPORTED_MODELS:
            model = "helmet"

        self.update_state({
            "is_active": True,
            "mode": mode,
            "model": model,
            "monitor_index": monitor_index,
            "fullscreen": fullscreen,
        })

        if self.is_projector_open():
            self.send_ipc_command("set_mode", mode=mode)
            self.send_ipc_command("set_model", model=model)
            self.send_ipc_command("set_monitor", monitor_index=monitor_index)
            if fullscreen:
                self.send_ipc_command("set_fullscreen", fullscreen=True)
            self.send_ipc_command("elevate")
            return True

        # In headless or mock test modes, do not spawn physical subprocess
        if "--headless" in sys.argv or os.environ.get("JARVIS_HEADLESS") == "1":
            return False

        # Throttle process spawning
        now = time.time()
        if now - self._last_spawn_time < 3.0:
            return False
        self._last_spawn_time = now

        try:
            cmd = [
                sys.executable,
                "-m",
                "ui.projector_window",
                "--mode", mode,
                "--model", model,
                "--monitor", str(monitor_index),
            ]
            if fullscreen:
                cmd.append("--fullscreen")

            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000008  # DETACHED_PROCESS

            self._projector_proc = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                creationflags=creationflags,
                close_fds=True,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to launch projector subprocess: {e}")
            return False

    def deactivate_projector(self) -> bool:
        """Deactivates and closes or hides the 3D Projector Window."""
        self.update_state({"is_active": False})
        success = self.send_ipc_command("close")
        if self._projector_proc is not None:
            try:
                self._projector_proc.terminate()
                self._projector_proc = None
            except Exception:
                pass
        return success

    def set_projection_mode(self, mode: str) -> bool:
        """
        Switches projection mode:
        - 'standard': Direct single viewport
        - 'pyramid': 4-angle Pepper's ghost prism projection
        - 'anaglyph': Stereoscopic Red/Cyan 3D glasses projection
        - 'floating': Transparent desktop overlay
        """
        mode = mode.lower().strip()
        if mode not in self.PROJECTION_MODES:
            return False
        self.update_state({"mode": mode})
        return self.send_ipc_command("set_mode", mode=mode)

    def set_3d_model(self, model: str) -> bool:
        """Switches active 3D wireframe mesh model."""
        model = model.lower().strip()
        if model not in self.SUPPORTED_MODELS:
            return False
        self.update_state({"model": model})
        return self.send_ipc_command("set_model", model=model)

    def set_target_monitor(self, monitor_index: int) -> bool:
        """Routes projector output to a specific display or external projector."""
        monitors = self.enumerate_monitors()
        if not (0 <= monitor_index < len(monitors)):
            return False
        self.update_state({"monitor_index": monitor_index})
        return self.send_ipc_command("set_monitor", monitor_index=monitor_index)

    def toggle_fullscreen(self, state: Optional[bool] = None) -> bool:
        """Toggles borderless fullscreen projector mode."""
        curr = self.get_state().get("fullscreen", False)
        new_state = (not curr) if state is None else bool(state)
        self.update_state({"fullscreen": new_state})
        return self.send_ipc_command("set_fullscreen", fullscreen=new_state)

    def toggle_transparency(self, state: Optional[bool] = None) -> bool:
        """Toggles transparent floating desktop mode."""
        curr = self.get_state().get("transparent", False)
        new_state = (not curr) if state is None else bool(state)
        self.update_state({"transparent": new_state})
        return self.send_ipc_command("set_transparency", transparent=new_state)

    def adjust_parallax(self, delta: float) -> float:
        """Adjusts stereoscopic anaglyph parallax offset (depth level)."""
        curr = float(self.get_state().get("parallax", 6.0))
        new_val = max(0.0, min(25.0, curr + delta))
        self.update_state({"parallax": new_val})
        self.send_ipc_command("set_parallax", parallax=new_val)
        return new_val

    def rotate_model(self, delta_yaw: float = 0.5, delta_pitch: float = 0.0) -> bool:
        """Rotates the 3D model orientation."""
        curr = self.get_state()
        new_yaw = (curr.get("yaw", 0.0) + delta_yaw) % (2 * math.pi)
        new_pitch = max(-1.2, min(1.2, curr.get("pitch", 0.2) + delta_pitch))
        self.update_state({"yaw": new_yaw, "pitch": new_pitch, "auto_spin": False})
        return self.send_ipc_command("rotate", yaw=new_yaw, pitch=new_pitch)

    def update_spatial_orientation(self, delta_yaw: float = 0.5, delta_pitch: float = 0.0) -> bool:
        """Continuously streams 6-DoF spatial yaw and pitch orientation deltas."""
        return self.rotate_model(delta_yaw=delta_yaw, delta_pitch=delta_pitch)

    def toggle_auto_spin(self, state: Optional[bool] = None) -> bool:
        """Pauses or resumes automated 360-degree rotation."""
        curr = self.get_state().get("auto_spin", True)
        new_state = (not curr) if state is None else bool(state)
        self.update_state({"auto_spin": new_state})
        return self.send_ipc_command("set_auto_spin", auto_spin=new_state)

    def cycle_mode(self) -> str:
        """Cycles to the next projection optical mode."""
        curr = self.get_state().get("mode", "standard")
        idx = (self.PROJECTION_MODES.index(curr) + 1) % len(self.PROJECTION_MODES) if curr in self.PROJECTION_MODES else 0
        new_mode = self.PROJECTION_MODES[idx]
        self.set_projection_mode(new_mode)
        return new_mode

    def cycle_model(self) -> str:
        """Cycles to the next 3D model."""
        curr = self.get_state().get("model", "helmet")
        idx = (self.SUPPORTED_MODELS.index(curr) + 1) % len(self.SUPPORTED_MODELS) if curr in self.SUPPORTED_MODELS else 0
        new_model = self.SUPPORTED_MODELS[idx]
        self.set_3d_model(new_model)
        return new_model

    def cycle_palette(self) -> str:
        """Cycles to the next holographic color palette."""
        curr = self.get_state().get("palette", "stark_cyan")
        idx = (self.PALETTES.index(curr) + 1) % len(self.PALETTES) if curr in self.PALETTES else 0
        new_pal = self.PALETTES[idx]
        self.update_state({"palette": new_pal})
        self.send_ipc_command("set_palette", palette=new_pal)
        return new_pal

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive diagnostic telemetry of the 3D Projector System."""
        state = self.get_state()
        monitors = self.enumerate_monitors()
        target_mon = monitors[state["monitor_index"]] if 0 <= state["monitor_index"] < len(monitors) else monitors[0]

        return {
            "active": self.is_projector_open(),
            "mode": state.get("mode", "standard").upper(),
            "model": state.get("model", "helmet").upper(),
            "palette": state.get("palette", "stark_cyan"),
            "fullscreen": state.get("fullscreen", False),
            "target_display": f"Monitor #{target_mon['index']} ({target_mon['width']}x{target_mon['height']}) - {target_mon['type']}",
            "available_monitors_count": len(monitors),
            "parallax_depth_px": state.get("parallax", 6.0),
            "auto_spin": state.get("auto_spin", True),
            "beam_lux": state.get("beam_lux", 100),
            "transparent_overlay": state.get("transparent", False),
        }


# Global Singleton Instance
projector_system = ProjectorSystem()
