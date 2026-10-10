"""
J.A.R.V.I.S. Holographic Tactical HUD Controller & IPC Bridge.
Enables programmatic, voice-driven, and cross-process control of the 
Stark Holographic Display:
- Toggling borderless projector fullscreen mode (F11)
- Switching 3D wireframe models (Helmet, Arc Reactor, Globe, Tesseract)
- Manipulating 3D rotation (yaw/pitch) and auto-spin
- Cycling visual holographic color palettes
- Bi-directional IPC state synchronization
"""

import os
import sys
import json
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

IPC_FILE = config.DATA_DIR / "hud_ipc_commands.json"
STATE_FILE = config.DATA_DIR / "hud_state.json"
_LOCK = threading.Lock()


class HUDController:
    """Controls and synchronizes the J.A.R.V.I.S. Tactical Holographic HUD."""

    VALID_MODELS = [
        "helmet", "reactor", "globe", "tesseract", "drone",
        "gauntlet", "emitter", "neural_mesh", "planetary_radar", "quantum_dna",
        "custom"
    ]

    def __init__(self):
        self._active_hud = None
        self._ensure_ipc_storage()

    def _ensure_ipc_storage(self):
        try:
            config.DATA_DIR.mkdir(parents=True, exist_ok=True)
            if not IPC_FILE.exists():
                IPC_FILE.write_text("[]", encoding="utf-8")
            if not STATE_FILE.exists():
                init_state = {
                    "is_fullscreen": False,
                    "active_model": "helmet",
                    "yaw": 0.0,
                    "pitch": 0.2,
                    "scale": 1.0,
                    "auto_spin": True,
                    "theme": "STARK HOLOGRAPHIC CYAN",
                    "timestamp": time.time()
                }
                STATE_FILE.write_text(json.dumps(init_state, indent=2), encoding="utf-8")
        except Exception:
            pass

    def register_hud_instance(self, hud_instance):
        """Registers in-memory TacticalHUD instance for in-process direct control."""
        self._active_hud = hud_instance

    def unregister_hud_instance(self):
        self._active_hud = None

    def send_command(self, action: str, **kwargs) -> bool:
        """
        Dispatches a command to the Tactical HUD.
        Handles both direct in-memory invocation and inter-process file IPC.
        """
        cmd_payload = {"action": action, "timestamp": time.time(), **kwargs}

        # 1. Direct in-memory dispatch if HUD is running in the same process
        if self._active_hud is not None:
            try:
                root = getattr(self._active_hud, "root", None)
                if root and root.winfo_exists():
                    root.after(0, lambda: self._execute_direct_command(cmd_payload))
            except Exception:
                pass

        # 2. File-based IPC dispatch for cross-process communication
        with _LOCK:
            try:
                cmds = []
                if IPC_FILE.exists():
                    try:
                        cmds = json.loads(IPC_FILE.read_text(encoding="utf-8"))
                        if not isinstance(cmds, list):
                            cmds = []
                    except Exception:
                        cmds = []
                cmds.append(cmd_payload)
                # Keep last 50 commands max
                cmds = cmds[-50:]
                IPC_FILE.write_text(json.dumps(cmds, indent=2), encoding="utf-8")
                return True
            except Exception:
                return False

    def poll_pending_commands(self) -> List[Dict[str, Any]]:
        """
        Called by TacticalHUD in its animation loop to retrieve and clear
        pending commands from external processes.
        """
        with _LOCK:
            try:
                if not IPC_FILE.exists():
                    return []
                content = IPC_FILE.read_text(encoding="utf-8").strip()
                if not content or content == "[]":
                    return []
                cmds = json.loads(content)
                if not isinstance(cmds, list):
                    cmds = []
                # Clear queue
                IPC_FILE.write_text("[]", encoding="utf-8")
                return cmds
            except Exception:
                return []

    def _execute_direct_command(self, cmd: Dict[str, Any]):
        """Executes a command directly on the registered HUD instance."""
        if not self._active_hud:
            return
        action = cmd.get("action")
        try:
            if action == "toggle_fullscreen":
                req_state = cmd.get("state")
                if req_state is not None:
                    if self._active_hud.is_fullscreen != req_state:
                        self._active_hud.toggle_fullscreen_mode()
                else:
                    self._active_hud.toggle_fullscreen_mode()

            elif action == "set_model":
                m = cmd.get("model", "helmet").lower()
                if m in self.VALID_MODELS:
                    self._active_hud.set_3d_model(m)

            elif action == "rotate":
                dy = cmd.get("delta_yaw", 0.5)
                dp = cmd.get("delta_pitch", 0.0)
                self._active_hud.model_yaw += dy
                self._active_hud.model_pitch += dp
                self._active_hud.auto_spin = False

            elif action == "reset_view":
                self._active_hud.model_yaw = 0.0
                self._active_hud.model_pitch = 0.2
                self._active_hud.model_scale = 1.0
                self._active_hud.auto_spin = True

            elif action == "toggle_spin":
                sp = cmd.get("spin")
                if sp is not None:
                    self._active_hud.auto_spin = bool(sp)
                else:
                    self._active_hud.auto_spin = not self._active_hud.auto_spin

            elif action == "cycle_palette":
                self._active_hud.cycle_theme()

            elif action == "load_mesh":
                p = cmd.get("path")
                if p:
                    from ui.mesh_3d_engine import holographic_3d
                    if holographic_3d.load_custom_file(p):
                        self._active_hud.set_3d_model("custom")
        except Exception:
            pass

    def update_state(self, is_fullscreen: bool, active_model: str, yaw: float, pitch: float, scale: float, auto_spin: bool, theme_name: str):
        """Called by TacticalHUD to broadcast its current live state."""
        state = {
            "is_fullscreen": bool(is_fullscreen),
            "active_model": str(active_model),
            "yaw": float(yaw),
            "pitch": float(pitch),
            "scale": float(scale),
            "auto_spin": bool(auto_spin),
            "theme": str(theme_name),
            "timestamp": time.time()
        }
        try:
            STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except Exception:
            pass

    def get_hud_status(self) -> Dict[str, Any]:
        """Returns the current state of the holographic display."""
        if self._active_hud is not None:
            try:
                return {
                    "is_fullscreen": self._active_hud.is_fullscreen,
                    "active_model": self._active_hud.active_3d_model,
                    "yaw": self._active_hud.model_yaw,
                    "pitch": self._active_hud.model_pitch,
                    "scale": self._active_hud.model_scale,
                    "auto_spin": self._active_hud.auto_spin,
                    "theme": self._active_hud.theme.get("name", "STARK HOLOGRAPHIC CYAN"),
                    "live": True
                }
            except Exception:
                pass

        try:
            if STATE_FILE.exists():
                st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                st["live"] = (time.time() - st.get("timestamp", 0) < 5.0)
                return st
        except Exception:
            pass

        return {
            "is_fullscreen": False,
            "active_model": "helmet",
            "yaw": 0.0,
            "pitch": 0.2,
            "scale": 1.0,
            "auto_spin": True,
            "theme": "STARK HOLOGRAPHIC CYAN",
            "live": False
        }

    # High-level convenience methods
    def toggle_fullscreen(self, state: Optional[bool] = None) -> bool:
        return self.send_command("toggle_fullscreen", state=state)

    def set_3d_model(self, model_name: str) -> bool:
        model_name = model_name.strip().lower()
        if model_name in self.VALID_MODELS:
            return self.send_command("set_model", model=model_name)
        return False

    def rotate_model(self, delta_yaw: float = 0.5, delta_pitch: float = 0.0) -> bool:
        return self.send_command("rotate", delta_yaw=delta_yaw, delta_pitch=delta_pitch)

    def update_spatial_orientation(self, delta_yaw: float = 0.5, delta_pitch: float = 0.0) -> bool:
        """Streams real-time continuous 6-DoF spatial velocity or orientation changes."""
        return self.rotate_model(delta_yaw=delta_yaw, delta_pitch=delta_pitch)

    def reset_3d_view(self) -> bool:
        return self.send_command("reset_view")

    def toggle_auto_spin(self, enabled: Optional[bool] = None) -> bool:
        return self.send_command("toggle_spin", spin=enabled)

    def cycle_palette(self) -> bool:
        return self.send_command("cycle_palette")

    def load_custom_mesh(self, file_path: str) -> bool:
        return self.send_command("load_mesh", path=str(file_path))


hud_controller = HUDController()
