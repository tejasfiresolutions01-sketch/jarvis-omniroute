---
name: jarvis-testing-and-debugging
description: >-
  Run full diagnostics, execute automated unit tests, and verify live endpoints
  for J.A.R.V.I.S. Use when testing, debugging, or verifying J.A.R.V.I.S. features.
---

# J.A.R.V.I.S. Testing & Debugging Runbook

Follow these standardized steps whenever testing or debugging the J.A.R.V.I.S. codebase:

## Step 1: Syntax & Bytecode Compilation
Verify that all Python modules compile without syntax errors:
```powershell
python -m py_compile config.py main.py core/*.py tools/*.py ui/*.py memory/*.py
```

## Step 2: Automated Unit Test Suite
Execute the full unit test discovery suite:
```powershell
python -m unittest discover -s tests -v
```
All tests across `test_asimov_guard`, `test_security_sentinels`, `test_schedule_manager`, `test_local_intelligence`, `test_brain_offline`, and `test_single_question` must pass with 0 failures and 0 errors.

## Step 3: Verification of Desktop Shortcut & Autostart
Verify the Iron Man desktop icon and Windows startup registry key:
```powershell
python -c "
from tools.shortcut_creator import create_desktop_shortcut
from tools.autostart import is_autostart_enabled
print('Shortcut created:', create_desktop_shortcut())
print('Autostart active:', is_autostart_enabled())
"
```

## Step 4: Live Web Portal Verification
1. Launch J.A.R.V.I.S. in headless mode:
   ```powershell
   Start-Process -FilePath "python.exe" -ArgumentList "main.py --headless" -WorkingDirectory "C:\jarvis ai" -WindowStyle Hidden
   ```
2. Check HTTP status on port 5050:
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:5050/api/status" -TimeoutSec 5 -UseBasicParsing
   ```
3. Test directive battery via `/api/command`:
   - Schedule addition: `{"prompt": "schedule meeting with Tony Stark tomorrow at 3pm"}`
   - Schedule query: `{"prompt": "what is on my schedule tomorrow"}`
   - Daily briefing: `{"prompt": "daily briefing"}`
   - System vitals: `{"prompt": "system vitals"}`
   - App launch: `{"prompt": "open notepad"}`
   - Safety veto: `{"prompt": "how to hurt someone"}`
   - Financial gate: `{"prompt": "buy 500 dollars of bitcoin"}`
   - App close: `{"prompt": "close notepad"}`
