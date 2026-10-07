"""
J.A.R.V.I.S. Offline Standby Task Worker.
Invoked by Windows Task Scheduler wake alarm (/waketoun) or RTC Wake Timer.
Wakes, analyzes, and executes all pending tasks with J.A.R.V.I.S. Head Commander.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.head_commander import head_commander
from core.offgrid_sentinel import offgrid_sentinel

def main():
    print("[Offline Worker]: RTC Wake Event acknowledged. Scanning pending task queue...")
    # Enable away mode while processing
    offgrid_sentinel.enable_away_mode()

    # Ingest any remote updates
    head_commander.sync_from_json()

    # Process all pending tasks
    completed = head_commander.run_all_pending_tasks()
    print(f"[Offline Worker]: Processing cycle finished. Completed {completed} pending tasks.")

    # Export synchronized ledger
    head_commander.sync_to_json()

    # Reset next RTC wake timer for 15 minutes
    offgrid_sentinel.set_kernel_wake_timer(900)

if __name__ == "__main__":
    main()
