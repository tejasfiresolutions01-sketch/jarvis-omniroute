"""
J.A.R.V.I.S. Single Notification Guard & Unprompted Speech Sentinel.
Enforces the strict rule:
1. Jarvis NEVER notifies or speaks unprompted without an explicit user command.
2. Any notification or alert must be delivered STRICTLY ONCE and never repeated
   unless the user explicitly asks for it again (e.g., 'what was that notification?',
   'repeat notification', 'repeat that', 'tell me again').
"""

import time
import re
import threading
from typing import Dict, List, Optional, Any
from pathlib import Path
import config

_LOCK = threading.Lock()


class NotificationGuard:
    """Registry and gatekeeper ensuring notifications are delivered only once unless asked again."""

    def __init__(self):
        # Maps notification_id -> {message, timestamp, category, repeat_requested}
        self._notified_registry: Dict[str, Dict[str, Any]] = {}
        # List of silent notifications awaiting user inquiry
        self._unprompted_log: List[Dict[str, Any]] = []
        # Last notification spoken or queued
        self._last_notification: Optional[str] = None
        self._last_notification_time: float = 0.0

    def can_notify(self, notification_id: str) -> bool:
        """Returns True if the notification has NOT been delivered yet, or if user explicitly asked for a repeat."""
        with _LOCK:
            if notification_id not in self._notified_registry:
                return True
            entry = self._notified_registry[notification_id]
            return bool(entry.get("repeat_requested", False))

    def notify_once(
        self,
        notification_id: str,
        message: str,
        category: str = "general",
        is_user_command: bool = False,
        allow_unprompted: bool = False
    ) -> bool:
        """
        Attempts to deliver a notification.
        - If already notified and user didn't ask again: SUPPRESSED (returns False).
        - If unprompted without user command and allow_unprompted is False:
          Silently logs notification for later user inquiry without vocalizing (returns False).
        - If allowed: Vocalizes once, records delivery, updates last_notification (returns True).
        """
        if not message or not message.strip():
            return False

        clean_msg = message.strip()
        now = time.time()

        with _LOCK:
            # 1. Check if already notified
            if notification_id in self._notified_registry:
                entry = self._notified_registry[notification_id]
                # If user explicitly asked for repeat, allow it this one time
                if entry.get("repeat_requested", False):
                    entry["repeat_requested"] = False
                    entry["last_notified"] = now
                    entry["times_notified"] = entry.get("times_notified", 1) + 1
                    self._last_notification = clean_msg
                    self._last_notification_time = now
                    self._vocalize(clean_msg)
                    return True
                else:
                    # Already notified once! Suppress completely.
                    print(f"[Notification Guard]: Suppressed duplicate notification '{notification_id}'. Rule: notify only once unless asked again.")
                    return False

            # 2. Check unprompted gate: if not triggered by a user command, do not speak aloud
            unprompted_ok = is_user_command or allow_unprompted or getattr(config, "UNPROMPTED_NOTIFICATIONS_ENABLED", False)
            if not unprompted_ok:
                # Log silently so user can ask "what was that notification?"
                self._notified_registry[notification_id] = {
                    "message": clean_msg,
                    "timestamp": now,
                    "category": category,
                    "vocalized": False,
                    "times_notified": 0,
                    "repeat_requested": False
                }
                self._unprompted_log.append({
                    "id": notification_id,
                    "message": clean_msg,
                    "timestamp": now,
                    "category": category
                })
                self._last_notification = clean_msg
                self._last_notification_time = now
                print(f"[Notification Guard]: Logged silent notification '{notification_id}'. Vocalization suppressed until user asks.")
                return False

            # 3. Deliver notification once
            self._notified_registry[notification_id] = {
                "message": clean_msg,
                "timestamp": now,
                "category": category,
                "vocalized": True,
                "times_notified": 1,
                "repeat_requested": False
            }
            self._last_notification = clean_msg
            self._last_notification_time = now
            self._vocalize(clean_msg)
            return True

    def _vocalize(self, text: str):
        """Dispatches voice synthesis safely."""
        try:
            from core.voice import speak
            speak(text)
        except Exception:
            pass

    def request_repeat(self, notification_id: Optional[str] = None) -> Optional[str]:
        """
        Called when user explicitly asks 'what was that notification?', 'repeat notification',
        or 'tell me again'. Marks notification as eligible for repeat delivery.
        """
        with _LOCK:
            if notification_id and notification_id in self._notified_registry:
                self._notified_registry[notification_id]["repeat_requested"] = True
                return self._notified_registry[notification_id]["message"]

            if self._last_notification:
                # Mark last notification for repeat
                for nid, entry in self._notified_registry.items():
                    if entry.get("message") == self._last_notification:
                        entry["repeat_requested"] = True
                        break
                return self._last_notification
            return None

    def get_last_notification(self) -> Optional[str]:
        """Returns the text of the most recent notification."""
        with _LOCK:
            return self._last_notification

    def get_recent_notifications(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Returns the most recent notifications for user inquiry."""
        with _LOCK:
            items = sorted(
                self._notified_registry.items(),
                key=lambda x: x[1].get("timestamp", 0),
                reverse=True
            )
            return [{"id": k, **v} for k, v in items[:limit]]

    def clear_registry(self):
        """Clears all notification history (for testing or reset)."""
        with _LOCK:
            self._notified_registry.clear()
            self._unprompted_log.clear()
            self._last_notification = None
            self._last_notification_time = 0.0


# Global singleton
notification_guard = NotificationGuard()
