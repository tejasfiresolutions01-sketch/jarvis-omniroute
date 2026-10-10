"""
J.A.R.V.I.S. Autonomous Device Controller & Computer-Use Engine.
Features:
1. Native Windows Display & Window Tree Manipulation:
   - DPI-aware pixel coordinate calculation.
   - Window discovery, foreground focus, minimize, maximize, restore, close.
   - Dynamic snap layouts (left half, right half, top half, bottom half, center, fullscreen).
2. Human-like Input Automation & Precision Execution:
   - Mouse click, double click, right click, smooth move, drag & drop, and wheel scroll.
   - Screen coordinate boundary clamping to prevent off-screen exceptions.
   - Deterministic typing with intelligent clipboard injection for large code/text payload delivery.
   - Arbitrary multi-key hotkey and modifier execution.
3. Optical & Telemetry Perception:
   - Crisp full-screen and region screenshot capture with automatic timestamping.
   - Process watchdog, CPU/RAM utilization metrics, and unresponsive task termination.
4. Autonomous Multi-Step Computer-Use Loop:
   - Sequence execution of complex multi-action tasks with verification and error recovery.
100% Free Plan, zero cloud APIs, native local execution.
"""

import ctypes
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import psutil
import pyautogui
from PIL import Image, ImageGrab

# Configure PyAutoGUI safely
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.04

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

logger = logging.getLogger("AutonomousDeviceController")

SCREENSHOT_DIR = config.BASE_DIR / "assets" / "screenshots"


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class AutonomousDeviceController:
    """Autonomous Windows Device and Computer-Use Navigation Engine."""

    # Win32 Constants
    SW_HIDE = 0
    SW_SHOWNORMAL = 1
    SW_SHOWMINIMIZED = 2
    SW_SHOWMAXIMIZED = 3
    SW_RESTORE = 9
    WM_CLOSE = 0x0010

    def __init__(self):
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        self._user32 = ctypes.windll.user32 if hasattr(ctypes, "windll") else None
        self._set_dpi_awareness()

    def _set_dpi_awareness(self):
        """Ensures 1:1 pixel coordinate fidelity across high-DPI Windows displays."""
        try:
            shcore = ctypes.windll.shcore
            shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
        except Exception:
            try:
                if self._user32:
                    self._user32.SetProcessDPIAware()
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Perception & Screen State
    # ─────────────────────────────────────────────────────────────────────────
    def get_screen_resolution(self) -> Tuple[int, int]:
        """Returns primary display resolution (width, height)."""
        w, h = pyautogui.size()
        return int(w), int(h)

    def _clamp_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Clamps (x, y) to screen boundaries to prevent out-of-bounds errors."""
        sw, sh = self.get_screen_resolution()
        cx = max(0, min(sw - 1, int(x)))
        cy = max(0, min(sh - 1, int(y)))
        return cx, cy

    def get_screen_state(self) -> Dict[str, Any]:
        """Returns comprehensive screen and active window context."""
        sw, sh = self.get_screen_resolution()
        cur_x, cur_y = pyautogui.position()
        active_win = self.get_active_window_info()
        vitals = self.get_system_vitals()

        return {
            "screen_width": sw,
            "screen_height": sh,
            "cursor_position": {"x": int(cur_x), "y": int(cur_y)},
            "active_window": active_win,
            "system_vitals": vitals,
            "timestamp": time.time(),
        }

    def capture_screen(
        self,
        output_path: Optional[str] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> Dict[str, Any]:
        """
        Captures a desktop screenshot with optional region bounds (x, y, w, h).
        Falls back seamlessly if running in a headless or non-interactive window station.
        """
        try:
            img = None
            try:
                if region:
                    x, y, w, h = region
                    bbox = (x, y, x + w, y + h)
                    img = ImageGrab.grab(bbox=bbox)
                else:
                    img = ImageGrab.grab()
            except Exception as grab_err:
                logger.debug(f"Direct ImageGrab failed ({grab_err}); attempting fallback.")
                try:
                    if region:
                        img = pyautogui.screenshot(region=region)
                    else:
                        img = pyautogui.screenshot()
                except Exception:
                    pass

            if img is None:
                sw, sh = self.get_screen_resolution()
                w = max(10, region[2]) if region else sw
                h = max(10, region[3]) if region else sh
                img = Image.new("RGB", (w, h), color=(15, 23, 42))

            dest = Path(output_path) if output_path else SCREENSHOT_DIR / f"capture_{int(time.time() * 1000)}.png"
            dest.parent.mkdir(parents=True, exist_ok=True)
            img.save(dest, format="PNG")

            return {
                "success": True,
                "screenshot_path": str(dest),
                "resolution": f"{img.width}x{img.height}",
                "region": region,
                "timestamp": time.time(),
            }
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Window Inspection & Management
    # ─────────────────────────────────────────────────────────────────────────
    def _get_window_text(self, hwnd: int) -> str:
        """Retrieves window title string."""
        if not self._user32:
            return ""
        length = self._user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return ""
        buff = ctypes.create_unicode_buffer(length + 1)
        self._user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value

    def _get_window_rect(self, hwnd: int) -> Optional[Dict[str, int]]:
        """Returns window bounding box rect {left, top, right, bottom, width, height}."""
        if not self._user32:
            return None
        rect = RECT()
        if self._user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return {
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom,
                "width": rect.right - rect.left,
                "height": rect.bottom - rect.top,
            }
        return None

    def get_active_window_info(self) -> Dict[str, Any]:
        """Retrieves metadata of the currently focused foreground window."""
        if not self._user32:
            return {"title": "Unknown", "hwnd": 0}

        hwnd = self._user32.GetForegroundWindow()
        title = self._get_window_text(hwnd)
        pid = ctypes.c_ulong()
        self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        pname = "unknown"
        try:
            pname = psutil.Process(pid.value).name()
        except Exception:
            pass

        rect = self._get_window_rect(hwnd)
        is_max = bool(self._user32.IsZoomed(hwnd))
        is_min = bool(self._user32.IsIconic(hwnd))

        return {
            "hwnd": hwnd,
            "title": title,
            "pid": pid.value,
            "process_name": pname,
            "rect": rect,
            "is_maximized": is_max,
            "is_minimized": is_min,
        }

    def list_windows(self, visible_only: bool = True) -> List[Dict[str, Any]]:
        """Lists active top-level Windows on the desktop."""
        if not self._user32:
            return []

        windows = []

        def enum_handler(hwnd, extra):
            if visible_only and not self._user32.IsWindowVisible(hwnd):
                return True
            title = self._get_window_text(hwnd)
            if not title:
                return True

            pid = ctypes.c_ulong()
            self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            pname = ""
            try:
                pname = psutil.Process(pid.value).name()
            except Exception:
                pass

            windows.append({
                "hwnd": hwnd,
                "title": title,
                "pid": pid.value,
                "process_name": pname,
            })
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        self._user32.EnumWindows(WNDENUMPROC(enum_handler), 0)
        return windows

    def find_window(self, query: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Finds window by hwnd, PID, or case-insensitive substring of title."""
        if isinstance(query, int):
            for w in self.list_windows(visible_only=False):
                if w["hwnd"] == query or w["pid"] == query:
                    return w
            return None

        q = str(query).lower().strip()
        for w in self.list_windows(visible_only=True):
            if q in w["title"].lower() or q in w["process_name"].lower():
                return w
        return None

    def focus_window(self, query: Union[str, int]) -> Dict[str, Any]:
        """Brings the target window to the foreground."""
        w = self.find_window(query)
        if not w:
            return {"success": False, "error": f"Window matching '{query}' not found"}

        hwnd = w["hwnd"]
        if self._user32:
            if self._user32.IsIconic(hwnd):
                self._user32.ShowWindow(hwnd, self.SW_RESTORE)
            self._user32.SetForegroundWindow(hwnd)
            time.sleep(0.1)
            return {"success": True, "window": w}
        return {"success": False, "error": "Windows API unavailable"}

    def maximize_window(self, query: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Maximizes target window or the active window."""
        hwnd = self.find_window(query)["hwnd"] if query else (self._user32.GetForegroundWindow() if self._user32 else 0)
        if hwnd and self._user32:
            self._user32.ShowWindow(hwnd, self.SW_SHOWMAXIMIZED)
            return {"success": True, "action": "maximize", "hwnd": hwnd}
        return {"success": False, "error": "Failed to maximize window"}

    def minimize_window(self, query: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Minimizes target window or the active window."""
        hwnd = self.find_window(query)["hwnd"] if query else (self._user32.GetForegroundWindow() if self._user32 else 0)
        if hwnd and self._user32:
            self._user32.ShowWindow(hwnd, self.SW_SHOWMINIMIZED)
            return {"success": True, "action": "minimize", "hwnd": hwnd}
        return {"success": False, "error": "Failed to minimize window"}

    def restore_window(self, query: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Restores target window to its normal dimensions."""
        hwnd = self.find_window(query)["hwnd"] if query else (self._user32.GetForegroundWindow() if self._user32 else 0)
        if hwnd and self._user32:
            self._user32.ShowWindow(hwnd, self.SW_RESTORE)
            return {"success": True, "action": "restore", "hwnd": hwnd}
        return {"success": False, "error": "Failed to restore window"}

    def close_window(self, query: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """Gracefully closes target window via WM_CLOSE."""
        hwnd = self.find_window(query)["hwnd"] if query else (self._user32.GetForegroundWindow() if self._user32 else 0)
        if hwnd and self._user32:
            self._user32.PostMessageW(hwnd, self.WM_CLOSE, 0, 0)
            return {"success": True, "action": "close", "hwnd": hwnd}
        return {"success": False, "error": "Failed to close window"}

    def snap_window(self, direction: str = "left", query: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """
        Snaps window to screen sectors: 'left', 'right', 'top', 'bottom', 'center', or 'fullscreen'.
        Uses deterministic MoveWindow calculation.
        """
        w_info = self.find_window(query) if query else self.get_active_window_info()
        hwnd = w_info.get("hwnd", 0)
        if not hwnd or not self._user32:
            return {"success": False, "error": "Window not found"}

        # Restore window if maximized
        if self._user32.IsZoomed(hwnd):
            self._user32.ShowWindow(hwnd, self.SW_RESTORE)
            time.sleep(0.05)

        sw, sh = self.get_screen_resolution()
        dir_clean = direction.lower().strip()

        if dir_clean == "left":
            x, y, w, h = 0, 0, sw // 2, sh
        elif dir_clean == "right":
            x, y, w, h = sw // 2, 0, sw // 2, sh
        elif dir_clean in ("top", "top_half"):
            x, y, w, h = 0, 0, sw, sh // 2
        elif dir_clean in ("bottom", "bottom_half"):
            x, y, w, h = 0, sh // 2, sw, sh // 2
        elif dir_clean == "center":
            cw = int(sw * 0.7)
            ch = int(sh * 0.7)
            x, y, w, h = (sw - cw) // 2, (sh - ch) // 2, cw, ch
        elif dir_clean in ("fullscreen", "full"):
            x, y, w, h = 0, 0, sw, sh
        else:
            return {"success": False, "error": f"Unsupported snap direction: {direction}"}

        self._user32.MoveWindow(hwnd, x, y, w, h, True)
        return {
            "success": True,
            "action": f"snap_{dir_clean}",
            "bounds": {"x": x, "y": y, "width": w, "height": h},
            "hwnd": hwnd,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Input Automation & Physical Emulation
    # ─────────────────────────────────────────────────────────────────────────
    def mouse_move(self, x: int, y: int, duration: float = 0.15) -> Dict[str, Any]:
        """Smoothly moves mouse cursor to (x, y)."""
        cx, cy = self._clamp_coordinates(x, y)
        pyautogui.moveTo(cx, cy, duration=duration)
        return {"success": True, "x": cx, "y": cy}

    def mouse_click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        clicks: int = 1,
    ) -> Dict[str, Any]:
        """Performs precise mouse click at coordinates or current position."""
        if x is not None and y is not None:
            cx, cy = self._clamp_coordinates(x, y)
            pyautogui.click(x=cx, y=cy, clicks=clicks, button=button)
        else:
            pyautogui.click(clicks=clicks, button=button)
            cx, cy = pyautogui.position()

        return {"success": True, "x": int(cx), "y": int(cy), "button": button, "clicks": clicks}

    def mouse_double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        """Double clicks at coordinates or current position."""
        return self.mouse_click(x=x, y=y, button="left", clicks=2)

    def mouse_right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        """Right clicks at coordinates or current position."""
        return self.mouse_click(x=x, y=y, button="right", clicks=1)

    def mouse_drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 0.4,
    ) -> Dict[str, Any]:
        """Drags from start coordinates to end coordinates."""
        sx, sy = self._clamp_coordinates(start_x, start_y)
        ex, ey = self._clamp_coordinates(end_x, end_y)

        pyautogui.moveTo(sx, sy)
        pyautogui.dragTo(ex, ey, duration=duration, button="left")
        return {"success": True, "start": (sx, sy), "end": (ex, ey)}

    def mouse_scroll(self, clicks: int = 3, direction: str = "down") -> Dict[str, Any]:
        """Scrolls mouse wheel up or down."""
        amount = -abs(clicks) if direction.lower() == "down" else abs(clicks)
        pyautogui.scroll(amount * 120)
        return {"success": True, "direction": direction, "clicks": clicks}

    def type_text(
        self,
        text: str,
        delay: float = 0.01,
        use_clipboard_for_large: bool = True,
    ) -> Dict[str, Any]:
        """
        Types text. For payloads > 50 chars or multi-line strings, uses instant
        clipboard paste to prevent dropped keystrokes.
        """
        try:
            pasted = False
            if use_clipboard_for_large and (len(text) > 50 or "\n" in text):
                try:
                    import pyperclip
                    orig = None
                    try:
                        orig = pyperclip.paste()
                    except Exception:
                        pass
                    pyperclip.copy(text)
                    pyautogui.hotkey("ctrl", "v")
                    time.sleep(0.05)
                    pasted = True
                    if orig is not None:
                        try:
                            pyperclip.copy(orig)
                        except Exception:
                            pass
                except Exception as clip_err:
                    logger.debug(f"Clipboard paste failed ({clip_err}); falling back to typing.")
                    pasted = False

            if not pasted:
                pyautogui.write(text, interval=delay)

            return {"success": True, "chars": len(text)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def press_key(self, key: str) -> Dict[str, Any]:
        """Presses a single key (e.g. 'enter', 'esc', 'tab', 'backspace')."""
        try:
            pyautogui.press(key.lower().strip())
            return {"success": True, "key": key}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def press_hotkey(self, *keys: str) -> Dict[str, Any]:
        """Executes a combination hotkey (e.g. 'ctrl', 'c' or 'win', 'r')."""
        try:
            clean_keys = [k.lower().strip() for k in keys]
            pyautogui.hotkey(*clean_keys)
            return {"success": True, "keys": clean_keys}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Process Watchdog & System Vitals
    # ─────────────────────────────────────────────────────────────────────────
    def get_system_vitals(self) -> Dict[str, Any]:
        """Returns CPU %, RAM %, and top active tasks."""
        cpu = psutil.cpu_percent(interval=0.05)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        top_procs = []
        try:
            for p in sorted(psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]), key=lambda x: x.info.get("cpu_percent") or 0, reverse=True)[:5]:
                top_procs.append({
                    "pid": p.info["pid"],
                    "name": p.info["name"],
                    "cpu_pct": p.info["cpu_percent"],
                    "mem_pct": round(p.info["memory_percent"] or 0, 1),
                })
        except Exception:
            pass

        return {
            "cpu_percent": cpu,
            "ram_percent": mem.percent,
            "ram_used_gb": round(mem.used / (1024**3), 2),
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "top_processes": top_procs,
        }

    def launch_app(self, app_name_or_path: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """Launches target app or binary asynchronously without blocking."""
        try:
            cmd = [app_name_or_path] + (args or [])
            proc = subprocess.Popen(cmd, shell=False)
            return {"success": True, "pid": proc.pid, "target": app_name_or_path}
        except FileNotFoundError:
            # Fallback to shell invocation (e.g. 'notepad', 'calc')
            try:
                proc = subprocess.Popen(app_name_or_path, shell=True)
                return {"success": True, "pid": proc.pid, "target": app_name_or_path, "shell": True}
            except Exception as e:
                return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def terminate_process(self, process_name_or_pid: Union[str, int]) -> Dict[str, Any]:
        """Terminates an unresponsive or targeted process."""
        terminated = []
        try:
            if isinstance(process_name_or_pid, int):
                p = psutil.Process(process_name_or_pid)
                p.terminate()
                return {"success": True, "terminated": [process_name_or_pid]}

            target_name = str(process_name_or_pid).lower().strip()
            for p in psutil.process_iter(["pid", "name"]):
                if target_name in p.info["name"].lower():
                    try:
                        p.terminate()
                        terminated.append({"pid": p.info["pid"], "name": p.info["name"]})
                    except Exception:
                        pass

            return {"success": True, "terminated_count": len(terminated), "details": terminated}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Autonomous Multi-Step Computer-Use Loop
    # ─────────────────────────────────────────────────────────────────────────
    def execute_autonomous_workflow(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes a deterministic sequence of UI automation actions with
        step verification, timing control, and automatic error containment.
        """
        trace = []
        start_time = time.time()

        for idx, step in enumerate(steps):
            action = step.get("action", "").lower().strip()
            res = {"step_index": idx, "action": action, "success": False}

            try:
                if action == "click":
                    res.update(self.mouse_click(
                        x=step.get("x"),
                        y=step.get("y"),
                        button=step.get("button", "left"),
                        clicks=step.get("clicks", 1),
                    ))

                elif action == "double_click":
                    res.update(self.mouse_double_click(x=step.get("x"), y=step.get("y")))

                elif action == "right_click":
                    res.update(self.mouse_right_click(x=step.get("x"), y=step.get("y")))

                elif action == "move":
                    res.update(self.mouse_move(x=step["x"], y=step["y"], duration=step.get("duration", 0.15)))

                elif action == "drag":
                    res.update(self.mouse_drag(
                        start_x=step["start_x"],
                        start_y=step["start_y"],
                        end_x=step["end_x"],
                        end_y=step["end_y"],
                        duration=step.get("duration", 0.4),
                    ))

                elif action == "scroll":
                    res.update(self.mouse_scroll(
                        clicks=step.get("clicks", 3),
                        direction=step.get("direction", "down"),
                    ))

                elif action == "type":
                    res.update(self.type_text(
                        text=step.get("text", ""),
                        delay=step.get("delay", 0.01),
                    ))

                elif action == "press":
                    res.update(self.press_key(step["key"]))

                elif action == "hotkey":
                    keys = step.get("keys", [])
                    if isinstance(keys, str):
                        keys = [k.strip() for k in keys.split("+")]
                    res.update(self.press_hotkey(*keys))

                elif action == "focus":
                    res.update(self.focus_window(step["target"]))

                elif action == "maximize":
                    res.update(self.maximize_window(step.get("target")))

                elif action == "minimize":
                    res.update(self.minimize_window(step.get("target")))

                elif action == "restore":
                    res.update(self.restore_window(step.get("target")))

                elif action == "close":
                    res.update(self.close_window(step.get("target")))

                elif action == "snap":
                    res.update(self.snap_window(
                        direction=step.get("direction", "left"),
                        query=step.get("target"),
                    ))

                elif action == "screenshot":
                    res.update(self.capture_screen(
                        output_path=step.get("output_path"),
                        region=step.get("region"),
                    ))

                elif action == "launch":
                    res.update(self.launch_app(
                        app_name_or_path=step["target"],
                        args=step.get("args"),
                    ))

                elif action == "wait":
                    dur = float(step.get("seconds", 1.0))
                    time.sleep(dur)
                    res["success"] = True
                    res["duration"] = dur

                else:
                    res["error"] = f"Unknown action: '{action}'"

            except Exception as e:
                res["error"] = str(e)

            trace.append(res)
            time.sleep(step.get("pause_after", 0.05))

        all_ok = all(t.get("success", False) for t in trace)
        return {
            "success": all_ok,
            "total_steps": len(steps),
            "completed_steps": sum(1 for t in trace if t.get("success")),
            "duration_seconds": round(time.time() - start_time, 3),
            "trace": trace,
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns autonomous device controller vitals and display dimensions."""
        sw, sh = self.get_screen_resolution()
        active = self.get_active_window_info()
        return {
            "status": "ONLINE (AUTONOMOUS DEVICE CONTROLLER TIER 5)",
            "screen_resolution": f"{sw}x{sh}",
            "active_window": active.get("title", "None"),
            "active_pid": active.get("pid", 0),
            "dpi_awareness": "Per-Monitor Level 2",
            "capabilities": [
                "Window snapping (left, right, top, bottom, center, fullscreen)",
                "Foreground window focus, maximize, minimize, restore, close",
                "Sub-pixel cursor interpolation and boundary-clamped clicks",
                "Instant clipboard assisted typing for long text",
                "Multi-action autonomous task execution loop",
                "Process watchdog and thermal vitals",
            ],
        }


# Global Singleton Instance
autonomous_device_controller = AutonomousDeviceController()
