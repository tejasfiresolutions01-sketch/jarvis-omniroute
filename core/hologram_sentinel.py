"""
J.A.R.V.I.S. Holographic Interface Sentinel & App Lifecycle Daemon.
Autonomously displays the Stark Tactical Holographic HUD on screen whenever:
1. The device display turns on / session unlocks / user returns from standby.
2. Any application window is closed across the Windows desktop environment.
"""

import os
import sys
import time
import ctypes
from ctypes import wintypes
import threading
import subprocess
from typing import Dict, Tuple, Optional
import config

def _attach_to_interactive_desktop():
    """Attaches current thread to interactive user desktop (Default) on Windows."""
    try:
        user32 = ctypes.windll.user32
        hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass

class HologramSentinel:
    """
    Monitors Windows display state and application lifecycle.
    Summons the holographic interface on device wake or app termination.
    """

    TRIGGER_COOLDOWN_SECONDS = 1.8  # Prevent rapid re-triggers if multiple child windows close
    MIN_WINDOW_LIFETIME = 1.0      # Ignore fleeting popups/splash screens shorter than 1s

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_trigger_time = 0.0
        self._last_manual_summon_time = 0.0
        self._app_focus_streak = 0
        self._tracked_windows: Dict[int, Tuple[str, float]] = {}  # hwnd -> (title, first_seen_timestamp)
        self.always_on = getattr(config, "HUD_ALWAYS_ON", True)
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32

    def set_always_on(self, enabled: bool = True) -> str:
        """Configures holographic interface to run on screen all the time."""
        self.always_on = enabled
        if enabled:
            self.display_hologram(reason="always_on_activated")
            return "Holographic interface is now set to run continuously at all times on screen, sir."
        else:
            return "Adaptive holographic background mode restored, sir."

    def get_hud_hwnd(self) -> Optional[int]:
        """Finds the native Win32 window handle for J.A.R.V.I.S. Tactical HUD."""
        _attach_to_interactive_desktop()
        hwnd = self.user32.FindWindowW(None, config.HUD_WINDOW_TITLE)
        if hwnd and self.user32.IsWindow(hwnd):
            return hwnd

        # Fallback search across all top-level windows
        found_hwnd = None
        def enum_cb(h, lparam):
            nonlocal found_hwnd
            length = self.user32.GetWindowTextLengthW(h)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(h, buf, length + 1)
                if config.HUD_WINDOW_TITLE in buf.value:
                    found_hwnd = h
                    return False
            return True

        CMPFUNC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        self.user32.EnumWindows(CMPFUNC(enum_cb), 0)
        return found_hwnd

    def is_hologram_visible(self) -> bool:
        """Returns True if the Holographic HUD is currently visible on screen."""
        hwnd = self.get_hud_hwnd()
        if hwnd:
            return bool(self.user32.IsWindowVisible(hwnd))
        return False

    def display_hologram(self, reason: str = "manual") -> bool:
        """
        Guarantees the Holographic Tactical HUD is displayed prominently on screen.
        If already running, restores from stealth/minimized state and brings to foreground.
        If not yet launched, spawns ui/hud.py in detached interactive desktop mode.
        """
        now = time.time()
        if reason in ["manual", "voice_command"]:
            self._last_manual_summon_time = now

        if now - self._last_trigger_time < self.TRIGGER_COOLDOWN_SECONDS and reason not in ["manual", "voice_command"]:
            return False

        self._last_trigger_time = now
        print(f"[Holographic Sentinel]: Summoning Tactical HUD (Reason: {reason})")

        _attach_to_interactive_desktop()
        hwnd = self.get_hud_hwnd()

        if hwnd:
            try:
                # Restore window if minimized / withdrawn
                self.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                self.user32.BringWindowToTop(hwnd)
                self.user32.SetForegroundWindow(hwnd)

                # Briefly enforce topmost to ensure HUD renders above all other applications
                HWND_TOPMOST = -1
                HWND_NOTOPMOST = -2
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_SHOWWINDOW = 0x0040
                self.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)

                # Release topmost after 0.5s so user can still switch to other windows freely
                threading.Timer(
                    0.5,
                    lambda: self.user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
                ).start()
                return True
            except Exception as e:
                print(f"[Holographic Sentinel Warning]: Error elevating HUD window: {e}")

        # If not running or window could not be found, spawn HUD process
        try:
            hud_script = str(config.BASE_DIR / "ui" / "hud.py")
            subprocess.Popen(
                [sys.executable, hud_script],
                cwd=str(config.BASE_DIR),
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )

            # Wait briefly and elevate newly spawned window
            def _elevate_after_spawn():
                for _ in range(12):
                    time.sleep(0.25)
                    h = self.get_hud_hwnd()
                    if h:
                        self.user32.ShowWindow(h, 9)
                        self.user32.BringWindowToTop(h)
                        self.user32.SetForegroundWindow(h)
                        break

            threading.Thread(target=_elevate_after_spawn, daemon=True).start()
            return True
        except Exception as e:
            print(f"[Holographic Sentinel Error]: Failed to spawn HUD process: {e}")
            return False

    def hide_hologram(self, force: bool = False) -> bool:
        """Hides the Holographic HUD into background stealth mode."""
        if self.always_on and not force:
            return False
        hwnd = self.get_hud_hwnd()
        if hwnd:
            self.user32.ShowWindow(hwnd, 0)  # SW_HIDE
            return True
        return False

    def _get_active_application_windows(self) -> Dict[int, str]:
        """
        Enumerates all legitimate, visible, top-level application windows on Windows.
        Filters out system tray, background workers, tooltips, dialog owners, and J.A.R.V.I.S. itself.
        """
        _attach_to_interactive_desktop()
        app_windows: Dict[int, str] = {}

        def enum_cb(hwnd, lparam):
            if not self.user32.IsWindowVisible(hwnd):
                return True
            # Main windows do not have owners (GW_OWNER == 0)
            if self.user32.GetWindow(hwnd, 4) != 0:
                return True

            length = self.user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True

            buf = ctypes.create_unicode_buffer(length + 1)
            self.user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value.strip()

            # Exclude standard Windows OS shells
            cls_buf = ctypes.create_unicode_buffer(256)
            self.user32.GetClassNameW(hwnd, cls_buf, 256)
            cls_name = cls_buf.value
            if cls_name in ["Progman", "Shell_TrayWnd", "WorkerW", "Shell_SecondaryTrayWnd"]:
                return True

            # Exclude J.A.R.V.I.S. itself
            if config.HUD_WINDOW_TITLE in title:
                return True

            # Exclude toolwindows
            ex_style = self.user32.GetWindowLongW(hwnd, -20)
            if (ex_style & 0x00000080) and not (ex_style & 0x00040000):
                return True

            app_windows[hwnd] = title
            return True

        CMPFUNC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        self.user32.EnumWindows(CMPFUNC(enum_cb), 0)
        return app_windows

    def _monitor_loop(self):
        """
        Background monitoring daemon.
        1. When user is working in an app or on a website, hides HUD into background.
        2. When user is on Desktop or closes an app, displays the holographic interface.
        """
        # Initial population
        current = self._get_active_application_windows()
        now = time.time()
        for hwnd, title in current.items():
            self._tracked_windows[hwnd] = (title, now)

        while self._running:
            try:
                time.sleep(0.35)
                now = time.time()
                _attach_to_interactive_desktop()

                # Inspect current foreground window
                fg = self.user32.GetForegroundWindow()
                cls_buf = ctypes.create_unicode_buffer(256)
                self.user32.GetClassNameW(fg, cls_buf, 256)
                cls_name = cls_buf.value

                hud_hwnd = self.get_hud_hwnd()
                is_desktop_or_idle = (
                    fg == 0 or
                    cls_name in ["Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"]
                )
                is_hud_focused = (fg == hud_hwnd and hud_hwnd is not None)

                # Check manual summon grace period
                in_manual_grace = (now - self._last_manual_summon_time < 8.0)

                # Always-On Mode: User requested holographic interface run all time on screen
                if self.always_on:
                    if not self.is_hologram_visible():
                        self.display_hologram(reason="always_on_persistence")
                    continue

                # Behavior A: User is working with an external application or website
                if not is_desktop_or_idle and not is_hud_focused and not in_manual_grace:
                    self._app_focus_streak += 1
                    # After 0.7s of steady interaction in the external application, slip to background
                    if self._app_focus_streak >= 2:
                        if self.is_hologram_visible():
                            self.hide_hologram()
                            print(f"[Holographic Sentinel]: User active in '{cls_name}'. Running in background.")
                elif is_desktop_or_idle:
                    self._app_focus_streak = 0
                    # Behavior B: User is on Desktop (otherwise), ensure Holographic Interface is displayed!
                    if not self.is_hologram_visible():
                        self.display_hologram(reason="idle_on_desktop")
                else:
                    self._app_focus_streak = 0

                # Track app window closures
                current_active = self._get_active_application_windows()
                closed_hwnds = []
                for hwnd, (title, first_seen) in list(self._tracked_windows.items()):
                    if hwnd not in current_active:
                        closed_hwnds.append((hwnd, title, first_seen))

                # Add newly opened windows to tracked set
                for hwnd, title in current_active.items():
                    if hwnd not in self._tracked_windows:
                        self._tracked_windows[hwnd] = (title, now)

                for hwnd, title, first_seen in closed_hwnds:
                    del self._tracked_windows[hwnd]
                    lifetime = now - first_seen

                    # Confirm genuine application close
                    if lifetime >= self.MIN_WINDOW_LIFETIME and not self.user32.IsWindow(hwnd):
                        print(f"[Holographic Sentinel]: Application closed: '{title}'. Displaying holographic HUD.")
                        self.display_hologram(reason=f"app_closed_{title}")
                        break

            except Exception as e:
                time.sleep(1.0)

    def start(self):
        """Starts the holographic monitoring daemon in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="JarvisHologramSentinelThread")
        self._thread.start()
        print("[Holographic Sentinel]: Autonomous holographic interface daemon active.")

    def stop(self):
        """Stops the holographic monitoring daemon."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

# Global singleton
hologram_sentinel = HologramSentinel()
