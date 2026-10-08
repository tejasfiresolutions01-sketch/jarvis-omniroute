import sqlite3
from contextlib import contextmanager
import re
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import config

class ButlerScheduleManager:
    """
    Advanced Butler Schedule & Agenda Management Core.
    Operates 100% OFFLINE via local SQLite database with natural language parsing,
    proactive daily briefings, conflict detection, and agenda coordination.
    """

    def __init__(self, db_path: Path = config.SCHEDULE_DB_PATH):
        self.db_path = str(db_path)
        self._shared_conn = None
        if self.db_path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._shared_conn.row_factory = sqlite3.Row
        self._init_db()

    @contextmanager
    def _get_connection(self):
        if self._shared_conn is not None:
            yield self._shared_conn
            return
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schedule_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    event_date TEXT NOT NULL,      -- YYYY-MM-DD
                    event_time TEXT,               -- HH:MM (24-hour)
                    duration_minutes INTEGER DEFAULT 60,
                    category TEXT DEFAULT 'general', -- meeting, reminder, task, personal
                    priority TEXT DEFAULT 'normal',   -- low, normal, high, urgent
                    notes TEXT,
                    is_completed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_event_date ON schedule_events(event_date)")
            conn.commit()

    # ─────────────────────────────────────────────────────────────────────────
    # Core Operations
    # ─────────────────────────────────────────────────────────────────────────
    def add_event(
        self,
        title: str,
        event_date: str,
        event_time: Optional[str] = None,
        duration: int = 60,
        category: str = "general",
        priority: str = "normal",
        notes: str = ""
    ) -> Dict[str, Any]:
        """Adds a calendar event/reminder to the local butler schedule."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO schedule_events (title, event_date, event_time, duration_minutes, category, priority, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title.strip(), event_date, event_time, duration, category, priority, notes))
            event_id = cur.lastrowid
            conn.commit()

        return {
            "id": event_id,
            "title": title.strip(),
            "date": event_date,
            "time": event_time,
            "priority": priority
        }

    def get_events_for_date(self, target_date: str) -> List[Dict[str, Any]]:
        """Retrieves all scheduled events for a specific date (YYYY-MM-DD)."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM schedule_events
                WHERE event_date = ? AND is_completed = 0
                ORDER BY event_time ASC NULLS LAST, id ASC
            """, (target_date,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def get_upcoming_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Retrieves all upcoming events for the next N days."""
        today = date.today().strftime("%Y-%m-%d")
        limit_date = (date.today() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM schedule_events
                WHERE event_date >= ? AND event_date <= ? AND is_completed = 0
                ORDER BY event_date ASC, event_time ASC NULLS LAST
            """, (today, limit_date))
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def delete_or_cancel_event(self, search_term: str) -> Tuple[bool, str]:
        """Cancels an event matching the given title or search keyword."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, title, event_date FROM schedule_events
                WHERE title LIKE ? AND is_completed = 0
                LIMIT 1
            """, (f"%{search_term.strip()}%",))
            row = cur.fetchone()
            if not row:
                return False, f"No active appointment found matching '{search_term}', sir."

            cur.execute("DELETE FROM schedule_events WHERE id = ?", (row["id"],))
            conn.commit()
            return True, f"Cancelled appointment '{row['title']}' on {row['event_date']}, sir."

    def clear_schedule_for_date(self, target_date: str) -> str:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM schedule_events WHERE event_date = ?", (target_date,))
            conn.commit()
        return f"All agenda entries for {target_date} have been cleared, sir."

    def cancel_all_pending_events(self) -> int:
        """Cancels all uncompleted calendar events and reminders."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM schedule_events WHERE is_completed = 0")
            count = cur.fetchone()[0]
            conn.execute("UPDATE schedule_events SET is_completed = 1 WHERE is_completed = 0")
            conn.commit()
        return count

    # ─────────────────────────────────────────────────────────────────────────
    # Butler Natural Language Parsers
    # ─────────────────────────────────────────────────────────────────────────
    def parse_and_handle(self, prompt: str) -> Tuple[bool, str]:
        """
        Evaluates natural language prompt for schedule actions.
        Returns: (is_schedule_command, butler_response)
        """
        clean = prompt.lower().strip()

        # 1. Daily Morning Briefing
        if any(p in clean for p in ["daily briefing", "morning briefing", "what does my day look like", "brief me on my day", "itinerary"]) and not any(k in clean for k in ["set ", "schedule ", "configure "]):
            return True, self.generate_daily_briefing()

        # 2. Query Schedule (Today / Tomorrow / Upcoming)
        if any(p in clean for p in ["what is on my schedule", "whats on my schedule", "check my schedule", "show my schedule", "my appointments", "my agenda", "do i have anything planned"]):
            if "tomorrow" in clean:
                target = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
                return True, self.format_day_schedule(target, label="tomorrow")
            else:
                target = date.today().strftime("%Y-%m-%d")
                return True, self.format_day_schedule(target, label="today")

        if any(p in clean for p in ["upcoming events", "upcoming schedule", "upcoming appointments", "this week's schedule"]):
            return True, self.format_upcoming_schedule()

        # 3. Cancel / Remove event
        cancel_match = re.search(r"\b(?:cancel|remove|delete)\s+(?:(?:the\s+)?(?:meeting|appointment|reminder|event|task)\s+)?(?:with|for|called\s+)?(.+)$", clean)
        if cancel_match and not re.search(r"\b(?:file|folder|window|app|application|pending task|pending tasks|all tasks|all pending tasks|command execution)\b", clean):
            target_title = cancel_match.group(1).strip()
            # Clean filler words
            target_title = re.sub(r"\b(?:from my schedule|today|tomorrow)\b", "", target_title).strip()
            if target_title:
                success, msg = self.delete_or_cancel_event(target_title)
                return True, msg

        # 4. Schedule / Add Event or Reminder
        # e.g., "schedule meeting with Tony at 3pm tomorrow"
        # e.g., "add appointment dentist on Friday at 10:00"
        # e.g., "remind me to call Mom at 5 PM"
        add_match = re.search(r"\b(?:schedule|add\s+(?:an?\s+)?(?:appointment|event|meeting|task)|remind\s+me\s+to|set\s+a\s+reminder\s+to)\s+(.+)$", clean)
        if add_match:
            raw_text = add_match.group(1).strip()
            return True, self._parse_and_insert_event(raw_text)

        return False, ""

    def _parse_and_insert_event(self, raw_text: str) -> str:
        """Parses event title, date, and time from natural text."""
        # Detect relative date
        today = date.today()
        target_date = today.strftime("%Y-%m-%d")
        date_label = "today"

        if "tomorrow" in raw_text:
            target_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            raw_text = re.sub(r"\btomorrow\b", "", raw_text)
            date_label = "tomorrow"
        elif "today" in raw_text:
            raw_text = re.sub(r"\btoday\b", "", raw_text)
            date_label = "today"

        # Check for weekday (e.g. "on friday")
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for idx, w in enumerate(weekdays):
            if w in raw_text:
                days_ahead = (idx - today.weekday() + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7
                target_date = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
                date_label = w.title()
                raw_text = re.sub(rf"\b(?:on\s+)?{w}\b", "", raw_text)
                break

        # Extract Time (e.g., "3pm", "3:30 pm", "15:00", "at 4 o'clock")
        event_time = None
        time_display = "at unspecified time"
        time_match = re.search(r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", raw_text, re.IGNORECASE)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            meridiem = (time_match.group(3) or "").lower()

            if meridiem == "pm" and hour < 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0

            event_time = f"{hour:02d}:{minute:02d}"
            meridiem_display = "AM" if hour < 12 else "PM"
            disp_hour = hour if 1 <= hour <= 12 else (hour - 12 if hour > 12 else 12)
            time_display = f"at {disp_hour}:{minute:02d} {meridiem_display}"
            raw_text = raw_text[:time_match.start()] + raw_text[time_match.end():]

        # Remaining text is the title
        clean_title = re.sub(r"\s+", " ", raw_text).strip(" \t\n\r.,!?:")
        # Remove trailing prepositions
        clean_title = re.sub(r"\b(?:at|on|for)\s*$", "", clean_title).strip()
        if not clean_title:
            clean_title = "Scheduled appointment"

        ev = self.add_event(title=clean_title.title(), event_date=target_date, event_time=event_time)
        return (
            f"Very good, sir. I have scheduled '{ev['title']}' for {date_label} ({target_date}) {time_display}. "
            f"It has been committed to your agenda."
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Butler Briefing Generators
    # ─────────────────────────────────────────────────────────────────────────
    def generate_daily_briefing(self) -> str:
        """Generates the signature Stark Butler morning/daily itinerary briefing."""
        today_str = date.today().strftime("%Y-%m-%d")
        today_formatted = date.today().strftime("%A, %B %d")
        now_time = datetime.now().strftime("%I:%M %p")

        events = self.get_events_for_date(today_str)
        hour = datetime.now().hour
        greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")

        lines = [f"{greeting}, sir. The current time is {now_time} on {today_formatted}."]

        if not events:
            lines.append("Your agenda for today is entirely clear. No conflicting engagements require your attention, sir.")
        else:
            lines.append(f"You have {len(events)} engagement{'s' if len(events) > 1 else ''} scheduled for today:")
            for idx, e in enumerate(events, 1):
                t_str = self._format_time_display(e["event_time"])
                lines.append(f"  {idx}. {e['title']} {t_str}")

        return "\n".join(lines)

    def format_day_schedule(self, target_date: str, label: str = "today") -> str:
        events = self.get_events_for_date(target_date)
        if not events:
            return f"You have nothing scheduled on your agenda for {label} ({target_date}), sir. Your schedule is clear."

        lines = [f"Here is your itinerary for {label} ({target_date}), sir:"]
        for idx, e in enumerate(events, 1):
            t_str = self._format_time_display(e["event_time"])
            lines.append(f"  • {e['title']} {t_str}")
        return "\n".join(lines)

    def format_upcoming_schedule(self) -> str:
        events = self.get_upcoming_events(days_ahead=7)
        if not events:
            return "You have no upcoming appointments over the next seven days, sir."

        lines = ["Here are your upcoming engagements for the week, sir:"]
        current_d = None
        for e in events:
            if e["event_date"] != current_d:
                current_d = e["event_date"]
                dt = datetime.strptime(current_d, "%Y-%m-%d").strftime("%A (%b %d)")
                lines.append(f"\n{dt}:")
            t_str = self._format_time_display(e["event_time"])
            lines.append(f"  • {e['title']} {t_str}")
        return "\n".join(lines)

    @staticmethod
    def _format_time_display(t_str: Optional[str]) -> str:
        if not t_str:
            return "(time flexible)"
        try:
            h, m = map(int, t_str.split(":"))
            mer = "AM" if h < 12 else "PM"
            disp_h = h if 1 <= h <= 12 else (h - 12 if h > 12 else 12)
            return f"at {disp_h}:{m:02d} {mer}"
        except Exception:
            return f"at {t_str}"

# Global singleton
schedule_manager = ButlerScheduleManager()
