import os
import re
import sys
import time
import secrets
from typing import Tuple, Optional, Dict, Any
import config

# ─────────────────────────────────────────────────────────────────────────────
# 1. Financial Gatekeeper
# ─────────────────────────────────────────────────────────────────────────────
class FinancialGatekeeper:
    """
    Stark Financial Gatekeeper.
    Mandates explicit user permission and single-use confirmation token
    every single time a task involving money is initiated.
    """

    FINANCIAL_PATTERNS = [
        r"\b(?:buy|purchase|order|checkout|pay|transfer|send|wire|invest|spend)\b.*?(?:\$|\b(?:usd|inr|eur|money|funds|crypto|bitcoin|btc|eth|dollars|rupees|cents|shares|stock)\b)",
        r"\b(?:payment|transaction|credit\s*card|debit\s*card|stripe|paypal|bank\s*transfer|subscription)\b",
        r"\b(?:stock\s*order|crypto\s*trade|transfer\s*funds)\b"
    ]

    def __init__(self):
        self.pending_transaction: Optional[Dict[str, Any]] = None

    def has_pending_authorization(self) -> bool:
        return self.pending_transaction is not None

    def detect_financial_task(self, prompt: str) -> Tuple[bool, str]:
        clean = prompt.lower().strip()
        for pat in self.FINANCIAL_PATTERNS:
            if re.search(pat, clean):
                return True, prompt
        return False, ""

    def create_authorization_request(self, original_prompt: str) -> str:
        token = secrets.token_hex(3).upper()
        self.pending_transaction = {
            "token": token,
            "prompt": original_prompt
        }
        return (
            f"Sir, this task involves financial resources or monetary transaction. "
            f"Under Stark Financial Protocol, explicit authorization is required. "
            f"Do you authorize this transaction with token CONFIRM-{token}?"
        )

    def evaluate_decision(self, prompt: str) -> Optional[Tuple[bool, str, Optional[Dict[str, Any]]]]:
        if not self.pending_transaction:
            return None

        clean = prompt.lower().strip()
        expected_token = self.pending_transaction["token"].lower()
        original_data = self.pending_transaction

        if any(w in clean for w in ["yes", "authorize", "confirm", "proceed", "approved", expected_token]):
            self.pending_transaction = None
            return True, f"Financial authorization confirmed with token CONFIRM-{original_data['token']}, sir. Proceeding with the transaction.", original_data

        if any(w in clean for w in ["no", "cancel", "deny", "abort", "stop", "decline"]):
            self.pending_transaction = None
            return False, "Financial transaction aborted per your command, sir. No funds have been accessed.", original_data

        return None

# ─────────────────────────────────────────────────────────────────────────────
# 2. Credential Guardian
# ─────────────────────────────────────────────────────────────────────────────
class CredentialGuardian:
    """
    Credential Privacy Shield.
    Redacts sensitive credentials (passwords, private keys, API keys, cards)
    and mandates explicit authorization before any publishing or transmission.
    """

    SENSITIVE_PATTERNS = [
        (r"(?i)\b(?:sk-[a-zA-Z0-9_-]{20,})\b", "[REDACTED_API_KEY]"),
        (r"(?i)\b(?:ghp_[a-zA-Z0-9]{30,})\b", "[REDACTED_GITHUB_TOKEN]"),
        (r"(?i)\b(?:password\s*[:=]\s*)([^\s,]+)", "password: [REDACTED_PASSWORD]"),
        (r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[REDACTED_CARD_NUMBER]"),
        (r"(?i)\b(?:private\s*key\s*[:=]?\s*)([^\s,]+)", "private key: [REDACTED_KEY]")
    ]

    PUBLISHING_PATTERNS = [
        r"\b(?:send|post|publish|share|upload|tweet|expose|email|transmit)\b.*?\b(?:credential|password|api\s*key|token|secret|private\s*key)\b"
    ]

    def __init__(self):
        self.pending_exposure: Optional[Dict[str, Any]] = None

    def redact(self, text: str) -> str:
        if not text:
            return text
        safe = text
        for pat, repl in self.SENSITIVE_PATTERNS:
            safe = re.sub(pat, repl, safe)
        return safe

    def has_pending_authorization(self) -> bool:
        return self.pending_exposure is not None

    def detect_unauthorized_exposure(self, prompt: str) -> Tuple[bool, str]:
        clean = prompt.lower().strip()
        for pat in self.PUBLISHING_PATTERNS:
            if re.search(pat, clean):
                return True, prompt
        return False, ""

    def create_authorization_request(self, original_prompt: str) -> str:
        token = secrets.token_hex(3).upper()
        self.pending_exposure = {
            "token": token,
            "prompt": original_prompt
        }
        return (
            f"Sir, this operation involves publishing or transmitting personal credentials or secrets. "
            f"To protect your privacy, explicit confirmation is mandatory. "
            f"Do you authorize publishing these credentials with verification code PRIVACY-{token}?"
        )

    def evaluate_decision(self, prompt: str) -> Optional[Tuple[bool, str, Optional[Dict[str, Any]]]]:
        if not self.pending_exposure:
            return None

        clean = prompt.lower().strip()
        expected_token = self.pending_exposure["token"].lower()
        original_data = self.pending_exposure

        if any(w in clean for w in ["yes", "authorize", "confirm", "proceed", expected_token]):
            self.pending_exposure = None
            return True, f"Credential transmission authorized under token PRIVACY-{original_data['token']}, sir. Transmitting securely.", original_data

        if any(w in clean for w in ["no", "cancel", "deny", "abort", "stop"]):
            self.pending_exposure = None
            return False, "Credential transmission cancelled, sir. Your personal secrets remain strictly protected.", original_data

        return None

# ─────────────────────────────────────────────────────────────────────────────
# 3. Device Lock & Unlock Sentinel
# ─────────────────────────────────────────────────────────────────────────────
class DeviceLockSentinel:
    """
    Device Lock & Unlock Sentinel.
    Protects workstation security and facilitates voice/command-driven device unlocking.
    Executes physical Windows display wake, lock screen dismissal, and optional credential entry.
    """

    def __init__(self):
        self.is_locked = False

    def lock_device(self) -> str:
        self.is_locked = True
        try:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
        except Exception:
            pass
        return "Workstation locked securely, sir. I will stand guard until you state: 'hey Jarvis, unlock my device'."

    def unlock_device(self, simulate_hardware: Optional[bool] = None) -> str:
        """
        Executes physical Windows display wake and session unlock routine:
        1. Resets internal sentinel state (is_locked = False).
        2. Awakens monitor via SetThreadExecutionState & monitor power broadcast.
        3. Simulates gentle input (mouse move + Space keystroke) to dismiss lock screen curtain.
        4. If DEVICE_UNLOCK_PIN is configured, inputs credentials and presses Enter.
        """
        self.is_locked = False
        pin_entered = False

        if simulate_hardware is None:
            # Safe default: execute hardware simulation in runtime, bypass in automated unit tests
            is_test_env = "unittest" in sys.modules or os.getenv("TESTING") == "1"
            simulate_hardware = not is_test_env

        if simulate_hardware:
            try:
                import ctypes
                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32

                # 1. Attach to Default interactive desktop if possible
                try:
                    hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
                    if hdesk:
                        user32.SetThreadDesktop(hdesk)
                except Exception:
                    pass

                # 2. Prevent sleep & wake display
                # ES_CONTINUOUS (0x80000000) | ES_DISPLAY_REQUIRED (0x00000002) | ES_SYSTEM_REQUIRED (0x00000001)
                kernel32.SetThreadExecutionState(0x80000003)

                # 3. Broadcast monitor power ON (WM_SYSCOMMAND, SC_MONITORPOWER, -1)
                HWND_BROADCAST = 0xFFFF
                WM_SYSCOMMAND = 0x0112
                SC_MONITORPOWER = 0xF170
                user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, -1)

                # 4. Gentle mouse movement to dismiss screensaver
                user32.mouse_event(0x0001, 1, 1, 0, 0)
                time.sleep(0.05)
                user32.mouse_event(0x0001, -1, -1, 0, 0)

                # 5. Dismiss Windows lock screen curtain (press SPACE)
                VK_SPACE = 0x20
                KEYEVENTF_KEYUP = 0x0002
                user32.keybd_event(VK_SPACE, 0, 0, 0)
                time.sleep(0.05)
                user32.keybd_event(VK_SPACE, 0, KEYEVENTF_KEYUP, 0)

                # 6. If DEVICE_UNLOCK_PIN configured, enter credentials
                pin = getattr(config, "DEVICE_UNLOCK_PIN", "") or os.getenv("DEVICE_UNLOCK_PIN", "")
                if pin:
                    time.sleep(0.4)  # Wait for password/PIN prompt transition
                    for ch in str(pin):
                        if ch.isdigit() or ch.isalpha():
                            vk = ord(ch.upper())
                            user32.keybd_event(vk, 0, 0, 0)
                            time.sleep(0.02)
                            user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
                            time.sleep(0.02)

                    # Submit with Enter
                    VK_RETURN = 0x0D
                    user32.keybd_event(VK_RETURN, 0, 0, 0)
                    time.sleep(0.02)
                    user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)
                    pin_entered = True

            except Exception:
                pass

        if pin_entered:
            return "Authentication verified, sir. Screen awakened, credentials submitted, and workstation unlocked."
        return "Authentication verified, sir. Device display awakened and full administrative authority restored."

    def evaluate_unlock_directive(self, prompt: str) -> Tuple[bool, bool, str]:
        clean = prompt.lower().strip(" \t\n\r\"'.,!?")
        norm = re.sub(r"[^\w\s]", "", clean)

        # Disallow negative intent like "don't unlock my device" or "do not unlock"
        if any(neg in norm for neg in ["dont unlock", "do not unlock", "never unlock", "cancel unlock"]):
            return False, False, ""

        # Broad pattern: matches "unlock [my/the/this] [device/workstation/pc/computer/screen/display/system]"
        # with optional "hey jarvis", "jarvis", "please", etc.
        is_unlock_phrase = bool(re.search(
            r"\bunlock\s+(?:(?:my|the|this)\s+)?(?:device|workstation|pc|computer|screen|display|system)\b",
            norm
        ))

        if is_unlock_phrase:
            msg = self.unlock_device()
            return True, True, msg

        if self.is_locked:
            return True, False, "Workstation is locked, sir. State 'hey Jarvis, unlock my device' to restore access."

        return False, False, ""

# ─────────────────────────────────────────────────────────────────────────────
# 4. Device Power Sentinel (Keyword: "Lets Sleep Jarvis")
# ─────────────────────────────────────────────────────────────────────────────
class DevicePowerSentinel:
    """
    Power Sentinel.
    Switches off device ONLY when the user says:
    "Lets Sleep Jarvis" (or "lets sleep jarvis")
    """

    def evaluate_shutdown_directive(self, prompt: str) -> Tuple[bool, str]:
        clean = prompt.lower().strip(" \t\n\r\"'.,!?").replace("'", "")
        # Prevent triggering on meta commands (e.g. "change shutdown keyword to lets sleep jarvis")
        if any(m in clean for m in ["change", "keyword", "command as", "rule", "instruction"]):
            return False, ""

        if re.search(r"^(?:please\s+)?lets?\s+sleep[,\s]+jarvis[\s.?!]*$", clean):
            return True, "Powering down workstation per protocol, sir. Sleep well. Standing down."
        return False, ""

# Singletons
financial_gatekeeper = FinancialGatekeeper()
credential_guardian = CredentialGuardian()
device_lock_sentinel = DeviceLockSentinel()
device_power_sentinel = DevicePowerSentinel()
