"""
J.A.R.V.I.S. Proactive Butler Autonomy & Event Daemon.
Transforms J.A.R.V.I.S. from a passive listener into an attentive proactive butler:
1. Spoken Agenda Reminders (10 minutes prior and at event start).
2. Protocol Sunrise (Automated morning executive briefing at scheduled wake-up time).
3. Ambient Hardware Vitals Guardian (Discreet notifications for critical RAM/CPU load).
"""

import os
import time
import threading
from datetime import datetime, date, timedelta
from typing import Set, Dict, Any, Optional

from core.schedule_manager import schedule_manager
from core.voice import speak, is_speaking
from core.chimes import play_wake_chime, play_boot_chime
from tools.system_controller import system_controller
from tools.briefing_tools import generate_executive_briefing
import config

class ProactiveButlerAgent:
    """
    Background daemon for proactive autonomous notifications,
    scheduled briefings, and hardware alerts.
    """

    def __init__(self):
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

        # Protocol Sunrise (Default: 08:00 AM, customizable)
        self.sunrise_enabled = os.getenv("SUNRISE_ENABLED", "true").lower() in ("true", "1", "yes")
        self.sunrise_time = os.getenv("SUNRISE_TIME", "08:00") # "HH:MM" 24-hr format
        self._last_sunrise_date: Optional[str] = None

        # Tracking notified schedule IDs for today: "task_id:10min" and "task_id:now"
        self._notified_events: Set[str] = set()
        self._last_schedule_reset_date = datetime.now().strftime("%Y-%m-%d")

        # Hardware health threshold warnings cooldown
        self._last_vitals_alert_time: float = 0.0
        self._high_load_counter = 0

    def set_sunrise_time(self, time_str: str) -> str:
        """Sets sunrise morning briefing time (e.g. '07:30' or '7:30 AM')."""
        try:
            # Parse time string
            clean = time_str.strip().upper()
            if "AM" in clean or "PM" in clean:
                t = datetime.strptime(clean, "%I:%M %p")
            else:
                t = datetime.strptime(clean, "%H:%M")
            self.sunrise_time = t.strftime("%H:%M")
            self.sunrise_enabled = True
            return f"Protocol Sunrise morning briefing set for {t.strftime('%I:%M %p')}, sir."
        except Exception:
            return f"Unable to parse sunrise time '{time_str}', sir. Please specify format like '08:00 AM'."

    def check_schedule_reminders(self):
        """
        Scans today's agenda and proactively vocalizes reminders
        10 minutes prior to start time, and at the event start time.
        """
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        # Reset notified event cache at midnight
        if today_str != self._last_schedule_reset_date:
            self._notified_events.clear()
            self._last_schedule_reset_date = today_str

        events = schedule_manager.get_events_for_date(today_str)
        if not events:
            return

        for ev in events:
            ev_id = str(ev.get("id"))
            ev_title = ev.get("title", "Scheduled Event")
            start_str = ev.get("event_time") or ev.get("start_time") # e.g. "17:30" or "09:00"
            if not start_str:
                continue

            try:
                # Parse event start time for today
                parts = start_str.split(":")
                ev_time = now.replace(hour=int(parts[0]), minute=int(parts[1]), second=0, microsecond=0)
                if (ev_time - now).total_seconds() < -43200:
                    ev_time += timedelta(days=1)
                elif (ev_time - now).total_seconds() > 43200:
                    ev_time -= timedelta(days=1)
                diff_minutes = (ev_time - now).total_seconds() / 60.0

                # 1. Ten-minute advance warning (8.0 to 10.5 mins)
                pre_key = f"{ev_id}:10min"
                if 8.0 <= diff_minutes <= 10.5 and pre_key not in self._notified_events:
                    self._notified_events.add(pre_key)
                    formatted_time = ev_time.strftime("%I:%M %p")
                    msg = (
                        f"Pardon the interruption, sir. You have '{ev_title}' "
                        f"scheduled in ten minutes at {formatted_time}."
                    )
                    self._deliver_proactive_alert(msg, alert_id=f"schedule:{ev_id}:10min")

                # 2. On-time start alert (0.0 to 1.5 mins)
                now_key = f"{ev_id}:now"
                if -1.0 <= diff_minutes <= 1.5 and now_key not in self._notified_events:
                    self._notified_events.add(now_key)
                    formatted_time = ev_time.strftime("%I:%M %p")
                    msg = f"Sir, it is {formatted_time}. It is time for '{ev_title}'."
                    self._deliver_proactive_alert(msg, alert_id=f"schedule:{ev_id}:now")

            except Exception:
                continue

    def check_protocol_sunrise(self):
        """
        Executes automated Protocol Sunrise morning executive briefing
        once per day at designated wake-up time.
        """
        if not self.sunrise_enabled:
            return

        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_hm = now.strftime("%H:%M")

        if current_hm == self.sunrise_time and self._last_sunrise_date != today_str:
            self._last_sunrise_date = today_str
            play_boot_chime()
            time.sleep(1.0)
            briefing = generate_executive_briefing()
            announcement = (
                f"Good morning, sir. Protocol Sunrise initiated. "
                f"{briefing} All subroutines stand ready for your command."
            )
            from core.notification_guard import notification_guard
            notification_guard.notify_once(f"sunrise:{today_str}", announcement, category="sunrise", allow_unprompted=True)
            speak(announcement)

    def check_hardware_health(self):
        """
        Proactively notifies user if RAM or CPU is under sustained critical strain.
        """
        now_ts = time.time()
        # Minimum 25-minute cooldown between health alerts
        if now_ts - self._last_vitals_alert_time < 1500:
            return

        vitals = system_controller.get_vitals()
        try:
            cpu_val = float(vitals.get("cpu_usage", "0%").replace("%", ""))
            ram_val = float(vitals.get("ram_usage", "0%").replace("%", ""))

            if ram_val > 94.0 or cpu_val > 96.0:
                self._high_load_counter += 1
                if self._high_load_counter >= 3: # 3 consecutive intervals (~1.5 mins)
                    self._last_vitals_alert_time = now_ts
                    self._high_load_counter = 0
                    alert = (
                        f"Pardon the intrusion, sir. System resources are experiencing elevated strain: "
                        f"RAM load is at {ram_val:.1f}% and CPU utilization is at {cpu_val:.1f}%. "
                        f"Would you like me to inspect active tasks?"
                    )
                    self._deliver_proactive_alert(alert, alert_id=f"hardware_strain:{int(now_ts // 1800)}")
            else:
                self._high_load_counter = 0
        except Exception:
            pass

    def _deliver_proactive_alert(self, message: str, alert_id: Optional[str] = None):
        """Discreetly plays an acoustic chime and vocalizes proactive message strictly once."""
        from core.notification_guard import notification_guard
        key = alert_id or f"proactive:{hash(message)}"
        if not notification_guard.can_notify(key):
            return
        notification_guard.notify_once(
            notification_id=key,
            message=message,
            category="proactive_reminder",
            allow_unprompted=True
        )

        def _worker():
            # Wait if currently speaking
            while is_speaking:
                time.sleep(0.5)
            play_wake_chime()
            time.sleep(0.6)
            speak(message)

        threading.Thread(target=_worker, daemon=True).start()

    def start(self):
        """Launches the background proactive butler daemon loop."""
        if self.is_running:
            return
        self.is_running = True

        def _daemon_loop():
            print("[Proactive Sentinel]: Autonomous Butler event & reminder daemon active...")
            while self.is_running:
                try:
                    self.check_schedule_reminders()
                    self.check_protocol_sunrise()
                    self.check_hardware_health()
                except Exception as e:
                    print(f"[Proactive Butler Notice]: {e}")
                time.sleep(30.0) # Check cycle every 30 seconds

        self._thread = threading.Thread(target=_daemon_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False

# Global singleton
proactive_agent = ProactiveButlerAgent()
