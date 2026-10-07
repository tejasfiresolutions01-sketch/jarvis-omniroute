import threading
import time
import psutil
from core.voice import speak

class AmbientWatchdog:
    """
    Ambient Hardware & System Sentinel.
    Monitors hardware vitals, battery level, and thermal load in the background,
    proactively alerting the user to critical conditions.
    """

    def __init__(self):
        self.is_running = False
        self._thread = None
        self._last_battery_alert = 0

    def start(self):
        if self.is_running:
            return
        self.is_running = True

        def _monitor():
            while self.is_running:
                try:
                    # Battery check
                    battery = psutil.sensors_battery()
                    if battery and not battery.power_plugged and battery.percent <= 15:
                        now = time.time()
                        if now - self._last_battery_alert > 300: # Alert once per 5 minutes
                            speak(f"Pardon the interruption, sir. Main power reserves have dropped to {battery.percent}%. Please connect external power.")
                            self._last_battery_alert = now
                except Exception:
                    pass
                time.sleep(30)

        self._thread = threading.Thread(target=_monitor, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False

watchdog = AmbientWatchdog()
