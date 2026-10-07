# J.A.R.V.I.S. Architecture & Safety Rules

## 1. Dual-Core Offline/Online Execution Invariant
- **Local Autonomy First**: System controls (app launch/close, audio volume, desktop minimization, vitals, date/time, local math) and Butler Schedule operations (itinerary, briefing, appointment additions/cancellations) MUST execute deterministically via local Python modules with 0ms latency.
- **Decoupled Cloud AI**: External AI (OmniRoute, Gemini, OpenAI) must strictly be reserved for open-ended conversation and deep reasoning. A strict timeout (<= 6.0s) must be enforced so offline operation never hangs.

## 2. Windows System Control Invariants
- **Non-Blocking Launch**: GUI applications must be launched detached via:
  `subprocess.Popen(["cmd.exe", "/c", "start", "", resolved_path], shell=True)`
- **Multi-Path Resolution**: Resolve application paths using candidates across `Program Files`, `Program Files (x86)`, `%LOCALAPPDATA%`, and Windows `System32`. Never rely solely on `shutil.which()` for applications like Chrome or VS Code.

## 3. Strict Security & Protocol Sentinels
- **Asimov's Prime Directive**: Absolute zero harm to humans; refuse all weapons, self-harm, or malicious digital wiping directives.
- **Financial Gatekeeper**: Intercept any task involving money and require explicit single-use token confirmation (`CONFIRM-<token>`).
- **Credential Privacy Shield**: Auto-redact API keys, tokens, and passwords; require explicit confirmation before publishing or transmitting secrets.
- **Device Lock Sentinel**: Workstation unlocks ONLY upon: *"hey Jarvis, unlock my device"*.
- **Power Sentinel**: Workstation shutdown triggered ONLY upon: *"Lets Sleep Jarvis"*.
- **Single-Question Protocol**: Any response from J.A.R.V.I.S. must contain at most ONE question (`?`).
- **Monthly Maintenance**: Check for the 1st of the month on startup to run diagnostic and integrity scans.

## 4. API & Test Robustness
- **Payload Invariance**: Directive endpoints (`/api/command`) must accept `prompt`, `command`, `text`, or `query` keys.
- **SQLite Test Isolation**: Unit tests must use `:memory:` or close SQLite connections prior to test directory cleanup.
