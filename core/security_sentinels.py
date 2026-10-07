import os
import re
import secrets
from typing import Tuple, Optional, Dict, Any

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
    Device Lock Sentinel.
    Allows unlocking ONLY when the user explicitly speaks:
    "hey Jarvis, unlock my device"
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

    def evaluate_unlock_directive(self, prompt: str) -> Tuple[bool, bool, str]:
        clean = prompt.lower().strip(" \t\n\r\"'.,!?")
        norm = re.sub(r"[^\w\s]", "", clean)

        # Exact match pattern: "hey jarvis unlock my device"
        is_unlock_phrase = bool(re.search(r"\bhey\s+jarvis\b.*?\bunlock\s+(?:my\s+)?device\b", norm)) or norm == "unlock my device"

        if is_unlock_phrase:
            self.is_locked = False
            return True, True, "Authentication verified, sir. Device unlocked and full administrative authority restored."

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
