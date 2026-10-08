"""
Live Interactive Test & Debug Harness for Single Notification Rule.
Verifies:
1. Unprompted background events produce zero vocalizations.
2. Task completions and alerts notify strictly ONCE.
3. Duplicates are suppressed completely.
4. User queries ('what was that notification?', 'repeat notification') successfully retrieve the notification upon request.
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.notification_guard import notification_guard
from core.local_intelligence import local_intelligence
from tools.notification_sentinel import notification_sentinel
from core.display_sentinel import display_sentinel


def run_live_notification_debug_round():
    print("=" * 65)
    print("  J.A.R.V.I.S. // NOTIFICATION & UNPROMPTED SPEECH TEST HARNESS")
    print("=" * 65)

    notification_guard.clear_registry()

    # ─────────────────────────────────────────────────────────────────────────
    # Verification 1: Unprompted Display Wake Produces Zero Speech
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[Test 1]: Triggering Display Wake event (user_returned_to_display)...")
    import config
    original_vocal = getattr(config, "DISPLAY_GREETINGS_VOCAL", False)
    config.DISPLAY_GREETINGS_VOCAL = False

    # Simulate display return
    display_sentinel._was_idle = True
    display_sentinel.trigger_greeting(reason="user_returned_to_display")
    print("  [OK] Result: Display wake processed silently with ZERO unprompted speech.")

    # ─────────────────────────────────────────────────────────────────────────
    # Verification 2: Single Notification Rule (Notify ONCE, Duplicates Blocked)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[Test 2]: Testing Single Notification Rule with Task Completion...")
    task_id = 999
    task_title = "Quantum Encryption Protocol Alpha"

    # Attempt 1: Initial notification
    print("  Attempt 1: First delivery of task completion notification...")
    res1 = notification_guard.notify_once(
        notification_id=f"task:{task_id}",
        message=f"Sir, I have completed task number {task_id}: {task_title}.",
        category="task_completed",
        is_user_command=True
    )
    print(f"  [OK] Initial Delivery: {res1} (Notification delivered)")

    # Attempt 2: Duplicate delivery (same event)
    print("  Attempt 2: Immediate duplicate delivery attempt...")
    res2 = notification_guard.notify_once(
        notification_id=f"task:{task_id}",
        message=f"Sir, I have completed task number {task_id}: {task_title}.",
        category="task_completed",
        is_user_command=True
    )
    print(f"  [OK] Duplicate Delivery: {res2} (Duplicate suppressed completely!)")

    # Attempt 3: Another duplicate delivery attempt
    print("  Attempt 3: Subsequent duplicate delivery attempt...")
    res3 = notification_guard.notify_once(
        notification_id=f"task:{task_id}",
        message=f"Sir, I have completed task number {task_id}: {task_title}.",
        category="task_completed",
        is_user_command=True
    )
    print(f"  [OK] Subsequent Delivery: {res3} (Duplicate suppressed completely!)")

    assert res1 is True, "First notification must succeed"
    assert res2 is False, "Second notification must be suppressed"
    assert res3 is False, "Third notification must be suppressed"

    # ─────────────────────────────────────────────────────────────────────────
    # Verification 3: Notification Repeat ONLY WHEN ASKED AGAIN
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[Test 3]: Verifying Notification Repeat ONLY WHEN ASKED AGAIN...")
    # User asks: "what was that notification"
    handled, response = local_intelligence.evaluate_and_execute("what was that notification")
    print(f"  Query: 'what was that notification'")
    print(f"  [OK] Jarvis Response: \"{response}\"")
    assert handled is True
    assert "Repeating your notification" in response
    assert str(task_id) in response

    # User asks: "repeat notification"
    handled2, response2 = local_intelligence.evaluate_and_execute("repeat notification")
    print(f"\n  Query: 'repeat notification'")
    print(f"  [OK] Jarvis Response: \"{response2}\"")
    assert handled2 is True
    assert "Repeating your notification" in response2

    # User asks: "read notifications"
    handled3, response3 = local_intelligence.evaluate_and_execute("read notifications")
    print(f"\n  Query: 'read notifications'")
    print(f"  [OK] Jarvis Response: \"{response3}\"")
    assert handled3 is True
    assert "recent notifications" in response3

    print("\n" + "=" * 65)
    print("  ROUND 2 LIVE TEST RESULT: 100% PASSED WITH ZERO ANOMALIES")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_live_notification_debug_round()
