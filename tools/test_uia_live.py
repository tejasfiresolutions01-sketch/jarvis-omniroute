"""
Live Windows UI Automation (UIA) Verification Harness for J.A.R.V.I.S.
Inspects active desktop windows and verifies deterministic COM tree control.
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.uia_controller import windows_uia
from tools.gui_controller import gui_controller


def run_live_uia_verification():
    print("=" * 65)
    print("J.A.R.V.I.S. Live Windows UI Automation (UIA) Verification Harness")
    print("=" * 65)

    assert windows_uia.is_available, "Windows UI Automation COM is not available!"
    print("[UIA Live]: COM interface active and bound to CUIAutomation.")

    # 1. Enumerate visible windows
    windows = windows_uia.get_open_windows()
    print(f"[UIA Live]: Discovered {len(windows)} active top-level windows.")
    if windows:
        for w in windows[:6]:
            print(f"  - {w['name']} (PID: {w['process_id']}, Class: {w['class_name']})")
    else:
        print("  - Notice: Zero interactive desktop windows in current process station (headless/service context).")

    # 2. Test gui_controller integration
    summary = gui_controller.list_active_windows()
    print(f"\n[GUI Controller Summary]:\n{summary}")
    assert "windows" in summary.lower(), "Summary should contain windows"

    # 3. Test element search on Desktop
    root = windows_uia._uia.GetRootElement()
    assert root is not None, "Failed to get UIA root element"
    print(f"\n[UIA Root]: Successfully verified Desktop Root ({root.CurrentName})")

    # 4. Graceful handling test
    ok, msg = windows_uia.click_element("NonExistentTestButton_12345")
    assert not ok, "Nonexistent button click should gracefully return False"
    print(f"[UIA Graceful Handling]: {msg}")

    print("=" * 65)
    print("Windows UI Automation Live Verification: ALL TESTS PASSED.")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_live_uia_verification()
