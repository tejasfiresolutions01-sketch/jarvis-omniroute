"""
J.A.R.V.I.S. Display & User Presence Sentinel.
Autonomously monitors device display wake, workstation session unlocks,
and user return from idle to greet Sir whenever the device display is activated.
"""

import time
import ctypes
from ctypes import wintypes
import threading
from datetime import datetime
from typing import Optional

from core.voice import speak
from core.cognitive_memory import cognitive_memory

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD)
    ]

class DisplaySentinel:
    """
    Monitors Windows display activity, session status, and user return from standby/idle.
    Autonomously vocalizes an articulate butler greeting whenever the display turns on.
    """

    IDLE_THRESHOLD_SECONDS = 90.0  # Time away considered standby/display sleep
    GREETING_COOLDOWN_SECONDS = 120.0 # Prevent redundant greetings

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._last_greeting_time = 0.0
        self._was_idle = False
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32

    def get_idle_seconds(self) -> float:
        """Returns the number of seconds since the last physical input event on Windows."""
        try:
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if self.user32.GetLastInputInfo(ctypes.byref(lii)):
                uptime_ms = self.kernel32.GetTickCount()
                idle_ms = max(0, uptime_ms - lii.dwTime)
                return idle_ms / 1000.0
        except Exception:
            pass
        return 0.0

    def is_display_active(self) -> bool:
        """
        Determines if the Windows interactive desktop display is unlocked and active.
        """
        try:
            # Check if desktop can be accessed interactively
            hdesk = self.user32.OpenDesktopW("Default", 0, False, 0x01FF)
            if hdesk:
                self.user32.CloseDesktop(hdesk)
                return True
            return False
        except Exception:
            return True

    def generate_display_greeting(self) -> str:
        """Generates a contextual, time-aware British butler greeting."""
        hour = datetime.now().hour
        period = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
        
        # Check if Sir's name is known in cognitive memory
        facts = cognitive_memory.recall_facts(category="user_profile", limit=5)
        user_name = "sir"
        for f in facts:
            if f["predicate"].lower() == "name" and f["object_value"]:
                user_name = f["object_value"]
                break

        title = f"{user_name}" if user_name != "sir" else "sir"
        greetings = [
            f"{period}, {title}. Display online. All internal subroutines are primed and standing ready.",
            f"Welcome back, {title}. Neural matrices are active and at your command.",
            f"{period}, {title}. Systems operational and standing by for your directive."
        ]
        # Alternate naturally based on minute
        idx = datetime.now().minute % len(greetings)
        return greetings[idx]

    def trigger_greeting(self, reason: str = "display_on"):
        """Vocalizes the greeting through J.A.R.V.I.S. speech engine."""
        now = time.time()
        if now - self._last_greeting_time < self.GREETING_COOLDOWN_SECONDS:
            return

        self._last_greeting_time = now
        greeting_text = self.generate_display_greeting()
        print(f"[Display Sentinel]: Display active ({reason}). Vocalizing greeting: '{greeting_text}'")
        speak(greeting_text)

    def _monitor_loop(self):
        """Background daemon polling user presence and display status."""
        while self._running:
            try:
                idle_secs = self.get_idle_seconds()
                display_ok = self.is_display_active()

                if idle_secs >= self.IDLE_THRESHOLD_SECONDS or not display_ok:
                    self._was_idle = True
                else:
                    # User was away or display was sleeping, and has now returned!
                    if self._was_idle and display_ok:
                        self._was_idle = False
                        self.trigger_greeting(reason="user_returned_to_display")

            except Exception:
                pass
            time.sleep(2.5)

    def start(self):
        """Starts display presence monitoring daemon."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="DisplaySentinelThread")
        self._thread.start()
        print("[Display Sentinel]: Autonomous display presence & wake-greeting daemon active.")

    def stop(self):
        self._running = False

# Global singleton
display_sentinel = DisplaySentinel()
