"""
J.A.R.V.I.S. Windows System Notification Sentinel.
Delivers native Windows desktop toast and balloon tip notifications,
chimes, and HUD status alerts when tasks complete or urgent events occur.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional
import config

PS_SCRIPT_PATH = config.BASE_DIR / "tools" / "send_notification.ps1"

class NotificationSentinel:
    """Delivers native Windows desktop notifications for completed tasks and alerts."""

    def __init__(self):
        self.script_path = PS_SCRIPT_PATH

    def notify(self, title: str, message: str) -> bool:
        """Sends a native Windows balloon tip / toast notification."""
        if not self.script_path.exists():
            return False

        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", str(self.script_path),
                "-Title", str(title),
                "-Message", str(message)
            ]
            subprocess.Popen(cmd)
            return True
        except Exception as e:
            print(f"[Notification Error]: {e}")
            return False

    def notify_task_completed(self, task_id: int, task_title: str, pdf_path: Optional[str] = None) -> bool:
        """
        Notifies completion of a task via voice (not by PDF).
        As instructed by user: completed tasks are announced via voice.
        """
        try:
            from core.voice import speak
            speak(f"Sir, I have completed task number {task_id}: {task_title}.")
        except Exception:
            pass

        title = f"J.A.R.V.I.S. Task #{task_id} Completed"
        msg = f"'{task_title}' completed with full precision, sir."
        return self.notify(title, msg)

# Global singleton
notification_sentinel = NotificationSentinel()
