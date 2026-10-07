"""
J.A.R.V.I.S. Global Hotkey & Stealth Mode Controller.
Registers system-wide Windows hotkeys (Ctrl+Alt+J and Ctrl+Shift+J) via Win32 User32 API.
Allows instant summoning of J.A.R.V.I.S. from anywhere across Windows, even from full-screen apps or games.
"""

import ctypes
from ctypes import wintypes
import threading
import time
from typing import Callable, Optional, List, Tuple
import config

class GlobalHotkeyManager:
    """
    Background Windows Global Hotkey Sentinel.
    Maintains a Win32 message queue in a daemon thread listening for WM_HOTKEY events.
    """

    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_WIN = 0x0008
    MOD_NOREPEAT = 0x4000

    VK_J = 0x4A       # 'J' key
    VK_SPACE = 0x20   # Spacebar

    def __init__(self, callback: Optional[Callable[[], None]] = None):
        self.callback = callback
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._user32 = ctypes.windll.user32
        self.registered_ids: List[int] = []

    def start(self, callback: Optional[Callable[[], None]] = None):
        """Starts the global hotkey message loop in a background daemon thread."""
        if self.running:
            return

        if callback:
            self.callback = callback

        self.running = True
        self.thread = threading.Thread(target=self._message_loop, daemon=True, name="JarvisGlobalHotkeyThread")
        self.thread.start()

    def _message_loop(self):
        """Win32 thread message loop for RegisterHotKey / PeekMessageW."""
        try:
            hdesk = self._user32.OpenDesktopW("Default", 0, False, 0x01FF)
            if hdesk:
                self._user32.SetThreadDesktop(hdesk)
        except Exception:
            pass

        combos = [
            # ID 101: Ctrl + Alt + J
            (101, self.MOD_CONTROL | self.MOD_ALT | self.MOD_NOREPEAT, self.VK_J),
            # ID 102: Ctrl + Shift + J
            (102, self.MOD_CONTROL | self.MOD_SHIFT | self.MOD_NOREPEAT, self.VK_J)
        ]

        self.registered_ids = []
        for hid, mods, vk in combos:
            res = self._user32.RegisterHotKey(None, hid, mods, vk)
            if res:
                self.registered_ids.append(hid)

        msg = wintypes.MSG()
        while self.running:
            # Peek and remove waiting hotkey messages
            while self._user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1): # PM_REMOVE = 1
                if msg.message == 0x0312: # WM_HOTKEY
                    if msg.wParam in self.registered_ids and self.callback:
                        try:
                            self.callback()
                        except Exception as e:
                            print(f"[Hotkey Callback Anomaly]: {e}")
                self._user32.TranslateMessage(ctypes.byref(msg))
                self._user32.DispatchMessageW(ctypes.byref(msg))
            time.sleep(0.05)

        # Clean unregistration
        for hid in self.registered_ids:
            self._user32.UnregisterHotKey(None, hid)
        self.registered_ids = []

    def stop(self):
        """Stops the hotkey loop and unregisters all system hooks."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.5)

    def is_active(self) -> bool:
        """Returns True if the hotkey daemon is currently armed."""
        return self.running and len(self.registered_ids) > 0

# Global singleton
global_hotkey = GlobalHotkeyManager()
