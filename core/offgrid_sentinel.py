"""
J.A.R.V.I.S. Off-Grid & Hardware Standby Autonomy Sentinel.
Enables J.A.R.V.I.S. to operate even when the device appears off or enters standby/sleep:
1. Windows Away Mode (ES_AWAYMODE_REQUIRED): Keeps CPU execution active while display is off.
2. Windows ACPI Hardware Wake Timers (/waketoun): Schedules periodic wake alarms in Task Scheduler.
3. Kernel RTC Wake Timer: Win32 SetWaitableTimer with fResume=True.
4. Cloud Off-Grid Runner: Coordinates serverless/GitHub Actions autonomous workers when PC is fully powered down.
"""

import os
import sys
import time
import ctypes
import subprocess
import threading
from pathlib import Path
from typing import Dict, Any, Optional

import config
from core.head_commander import head_commander

# Win32 Execution State Flags
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
ES_USER_PRESENT = 0x00000004
ES_AWAYMODE_REQUIRED = 0x00000040
ES_CONTINUOUS = 0x80000000

class OffgridSentinel:
    """
    Guarantees J.A.R.V.I.S. continues processing pending tasks even when the
    user locks the workstation, display turns off, or computer sleeps.
    """

    def __init__(self):
        self.away_mode_active = False
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

    def enable_away_mode(self) -> bool:
        """
        Enables Windows Away Mode.
        The display will power down, but the CPU and network stack remain operational
        at full speed to execute J.A.R.V.I.S. background tasks.
        """
        try:
            kernel32 = ctypes.windll.kernel32
            # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED
            res = kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED)
            if res != 0:
                self.away_mode_active = True
                print("[Offgrid Sentinel]: Windows Away Mode enabled. Background task execution persistent.")
                return True
        except Exception as e:
            print(f"[Offgrid Sentinel]: Unable to set Away Mode ({e}).")
        return False

    def disable_away_mode(self) -> bool:
        """Restores default system power execution state."""
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            self.away_mode_active = False
            return True
        except Exception:
            return False

    def setup_hardware_wake_task(self) -> bool:
        """
        Registers a Windows Scheduled Task with the /waketoun flag.
        Wakes the physical computer from sleep or modern standby every 15 minutes
        to process any pending tasks in the queue.
        """
        python_exe = sys.executable
        script_path = str(config.BASE_DIR / "tools" / "run_pending_offline.py")

        ps_cmd = (
            f"$action = New-ScheduledTaskAction -Execute '{python_exe}' -Argument '\"{script_path}\"'; "
            f"$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 15); "
            f"$settings = New-ScheduledTaskSettingsSet -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; "
            f"Register-ScheduledTask -TaskName 'JARVIS_OFFLINE_AUTONOMY' -Action $action -Trigger $trigger -Settings $settings -Force"
        )

        try:
            result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
            if result.returncode == 0:
                print("[Offgrid Sentinel]: Hardware ACPI Wake Task registered (-WakeToRun).")
                return True
            else:
                print(f"[Offgrid Sentinel Notice]: Task registration notice: {result.stderr.strip() or result.stdout.strip()}")
                return False
        except Exception as e:
            print(f"[Offgrid Sentinel Anomaly]: {e}")
            return False

    def set_kernel_wake_timer(self, seconds_from_now: int = 900) -> bool:
        """
        Sets a low-level Win32 RTC Wakeable Timer with fResume=True.
        Hardware RTC generates a resume interrupt to wake device from sleep.
        """
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.CreateWaitableTimerW(None, True, "JARVIS_RTC_WAKE_TIMER")
            if not handle:
                return False

            # Time in 100-nanosecond intervals (negative for relative time)
            due_time = ctypes.c_longlong(-int(seconds_from_now * 10000000))
            # fResume = True (arg 5) instructs kernel to wake computer
            res = kernel32.SetWaitableTimer(
                handle,
                ctypes.byref(due_time),
                0,
                None,
                None,
                True  # fResume
            )
            return bool(res)
        except Exception:
            return False

    def ensure_cloud_drone_workflow(self):
        """
        Ensures the GitHub Actions workflow file exists so J.A.R.V.I.S. tasks
        continue executing in the cloud when physical PC is totally powered off.
        """
        workflow_dir = config.BASE_DIR / ".github" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        workflow_file = workflow_dir / "jarvis_offgrid_worker.yml"

        if not workflow_file.exists():
            content = (
                "name: J.A.R.V.I.S. Off-Grid Autonomous Cloud Worker\n\n"
                "on:\n"
                "  schedule:\n"
                "    - cron: '*/30 * * * *' # Runs every 30 minutes in the cloud\n"
                "  workflow_dispatch: # Can be triggered manually\n"
                "  push:\n"
                "    paths:\n"
                "      - 'memory/pending_tasks.json'\n\n"
                "jobs:\n"
                "  offgrid_worker:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - name: Checkout Repository\n"
                "        uses: actions/checkout@v4\n"
                "        with:\n"
                "          token: ${{ secrets.GITHUB_TOKEN }}\n\n"
                "      - name: Set up Python\n"
                "        uses: actions/setup-python@v5\n"
                "        with:\n"
                "          python-version: '3.11'\n\n"
                "      - name: Install Dependencies\n"
                "        run: pip install requests\n\n"
                "      - name: Execute Autonomous Pending Tasks\n"
                "        run: python tools/offgrid_cloud_worker.py\n\n"
                "      - name: Commit & Push Completed Deliverables\n"
                "        run: |\n"
                "          git config --global user.name 'J.A.R.V.I.S. Cloud Drone'\n"
                "          git config --global user.email 'jarvis-drone@stark.industries'\n"
                "          git add memory/pending_tasks.json data/completed_tasks/\n"
                "          git diff --quiet && git diff --staged --quiet || (git commit -m 'feat(tasks): offgrid cloud autonomous completion' && git push)\n"
            )
            with open(workflow_file, "w", encoding="utf-8") as f:
                f.write(content)
            # Also persist in templates/workflows
            template_dir = config.BASE_DIR / "templates" / "workflows"
            template_dir.mkdir(parents=True, exist_ok=True)
            with open(template_dir / "jarvis_offgrid_worker.yml", "w", encoding="utf-8") as f:
                f.write(content)
            print("[Offgrid Sentinel]: Cloud Off-Grid Autonomous Drone workflow created.")

    def start(self):
        """Initializes full off-grid and device-off persistence."""
        if config.AWAY_MODE_ENABLED:
            self.enable_away_mode()

        self.setup_hardware_wake_task()
        self.ensure_cloud_drone_workflow()

        # Check for unbriefed tasks completed while device was away; cache silently without unprompted speech
        debrief = head_commander.generate_offline_debrief()
        if debrief:
            head_commander.cached_offline_debrief = debrief
            from core.notification_guard import notification_guard
            notification_guard.notify_once("offline_debrief", debrief, category="task_debrief", allow_unprompted=False)

# Global singleton
offgrid_sentinel = OffgridSentinel()
