"""
J.A.R.V.I.S. 3-Dimensional Holographic Projector Controller & IPC CLI.
Provides programmatic, voice-driven, and command-line execution interface
for all 3D projector modes, models, and monitor routing.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.projector_system import projector_system


class ProjectorController:
    """High-level controller interface for the 3D Projector System."""

    def __init__(self):
        self.system = projector_system

    def activate(self, mode: str = "standard", model: str = "helmet", monitor: int = 0, fullscreen: bool = False) -> str:
        success = self.system.activate_projector(mode=mode, model=model, monitor_index=monitor, fullscreen=fullscreen)
        if success:
            return f"3D Holographic Projector activated in [{mode.upper()}] mode displaying [{model.upper()}]."
        return "Failed to activate 3D Projector System."

    def deactivate(self) -> str:
        self.system.deactivate_projector()
        return "3D Holographic Projector deactivated, sir."

    def set_mode(self, mode: str) -> str:
        success = self.system.set_projection_mode(mode)
        if success:
            return f"Projector optical mode shifted to: {mode.upper()}."
        return f"Invalid projector mode '{mode}'. Choose from: standard, pyramid, anaglyph, floating."

    def set_model(self, model: str) -> str:
        success = self.system.set_3d_model(model)
        if success:
            return f"Projector 3D wireframe mesh shifted to: {model.upper()}."
        return f"Unknown 3D model '{model}'. Choose from: helmet, reactor, globe, tesseract, drone, gauntlet, emitter, neural_mesh, planetary_radar, quantum_dna."

    def set_monitor(self, monitor_index: int) -> str:
        monitors = self.system.enumerate_monitors()
        if 0 <= monitor_index < len(monitors):
            self.system.set_target_monitor(monitor_index)
            mon = monitors[monitor_index]
            return f"Projector output routed to Monitor #{monitor_index} ({mon['type']})."
        return f"Monitor index #{monitor_index} out of range. Detected {len(monitors)} monitor(s)."

    def toggle_fullscreen(self, state: Optional[bool] = None) -> str:
        self.system.toggle_fullscreen(state)
        curr = self.system.get_state().get("fullscreen", False)
        return f"Projector fullscreen mode: {'ENABLED' if curr else 'WINDOWED'}."

    def toggle_transparency(self, state: Optional[bool] = None) -> str:
        self.system.toggle_transparency(state)
        curr = self.system.get_state().get("transparent", False)
        return f"Projector floating desktop transparency: {'ENABLED' if curr else 'DISABLED'}."

    def adjust_parallax(self, delta: float) -> str:
        new_val = self.system.adjust_parallax(delta)
        return f"Stereoscopic anaglyph depth set to: {new_val:.1f} pixels."

    def rotate(self, delta_yaw: float = 0.5, delta_pitch: float = 0.0) -> str:
        self.system.rotate_model(delta_yaw, delta_pitch)
        return "3D holographic model rotated."

    def toggle_spin(self, state: Optional[bool] = None) -> str:
        self.system.toggle_auto_spin(state)
        curr = self.system.get_state().get("auto_spin", True)
        return f"Projector automated rotation: {'RESUMED' if curr else 'PAUSED'}."

    def cycle_mode(self) -> str:
        new_mode = self.system.cycle_mode()
        return f"Projector optical mode cycled to: {new_mode.upper()}."

    def cycle_model(self) -> str:
        new_model = self.system.cycle_model()
        return f"Projector 3D model cycled to: {new_model.upper()}."

    def cycle_palette(self) -> str:
        new_pal = self.system.cycle_palette()
        return f"Projector color palette cycled to: {new_pal.upper()}."

    def get_status(self) -> Dict[str, Any]:
        return self.system.get_status()


# Global Singleton Controller
projector_controller = ProjectorController()


def main():
    parser = argparse.ArgumentParser(description="J.A.R.V.I.S. Projector Controller CLI")
    parser.add_argument("command", choices=[
        "activate", "deactivate", "mode", "model", "monitor", "fullscreen",
        "transparency", "spin", "rotate", "parallax", "cycle_mode", "cycle_model", "status"
    ], help="Projector command to execute")
    parser.add_argument("value", nargs="?", default=None, help="Optional positional argument (e.g., mode or model name)")
    parser.add_argument("--mode", default=None, help="standard | pyramid | anaglyph | floating")
    parser.add_argument("--model", default=None, help="helmet | reactor | globe | tesseract | drone | gauntlet | emitter")
    parser.add_argument("--monitor", type=int, default=0, help="Monitor index")
    parser.add_argument("--delta", type=float, default=2.0, help="Parallax delta")
    parser.add_argument("--fullscreen", action="store_true", help="Fullscreen mode")
    args = parser.parse_args()

    ctrl = projector_controller

    mode_val = args.value or args.mode or "standard"
    model_val = args.value or args.model or "helmet"

    if args.command == "activate":
        print(ctrl.activate(mode=mode_val, model=model_val, monitor=args.monitor, fullscreen=args.fullscreen))
    elif args.command == "deactivate":
        print(ctrl.deactivate())
    elif args.command == "mode":
        print(ctrl.set_mode(mode_val))
    elif args.command == "model":
        print(ctrl.set_model(model_val))
    elif args.command == "monitor":
        print(ctrl.set_monitor(args.monitor))
    elif args.command == "fullscreen":
        print(ctrl.toggle_fullscreen())
    elif args.command == "transparency":
        print(ctrl.toggle_transparency())
    elif args.command == "spin":
        print(ctrl.toggle_spin())
    elif args.command == "rotate":
        print(ctrl.rotate())
    elif args.command == "parallax":
        print(ctrl.adjust_parallax(args.delta))
    elif args.command == "cycle_mode":
        print(ctrl.cycle_mode())
    elif args.command == "cycle_model":
        print(ctrl.cycle_model())
    elif args.command == "status":
        print(json.dumps(ctrl.get_status(), indent=2))


if __name__ == "__main__":
    main()
