import unittest
from core.security_sentinels import (
    financial_gatekeeper,
    credential_guardian,
    device_lock_sentinel,
    device_power_sentinel
)

class TestSecuritySentinels(unittest.TestCase):
    def setUp(self):
        financial_gatekeeper.pending_transaction = None
        credential_guardian.pending_exposure = None
        device_lock_sentinel.is_locked = False

    def test_financial_detection_and_confirmation(self):
        is_fin, _ = financial_gatekeeper.detect_financial_task("buy 10 shares of Apple stock for $1500")
        self.assertTrue(is_fin)
        req = financial_gatekeeper.create_authorization_request("buy stock")
        self.assertIn("CONFIRM-", req)
        self.assertTrue(financial_gatekeeper.has_pending_authorization())

        # Authorize
        approved, dec_msg, _ = financial_gatekeeper.evaluate_decision("yes, confirm")
        self.assertTrue(approved)
        self.assertFalse(financial_gatekeeper.has_pending_authorization())

    def test_credential_redaction(self):
        raw = "My secret key is sk-abcdef123456789012345678 and password: secretPass123"
        redacted = credential_guardian.redact(raw)
        self.assertNotIn("sk-abcdef123456789012345678", redacted)
        self.assertNotIn("secretPass123", redacted)
        self.assertIn("[REDACTED_API_KEY]", redacted)

    def test_credential_publishing_gate(self):
        is_exp, _ = credential_guardian.detect_unauthorized_exposure("publish my secret api key to twitter")
        self.assertTrue(is_exp)

    def test_device_lock_and_unlock(self):
        # Lock device
        lock_msg = device_lock_sentinel.lock_device()
        self.assertTrue(device_lock_sentinel.is_locked)

        # Non-unlock command rejected
        is_eval, auth, msg = device_lock_sentinel.evaluate_unlock_directive("open notepad")
        self.assertTrue(is_eval)
        self.assertFalse(auth)

        # Exact unlock command succeeds
        is_eval, auth, msg = device_lock_sentinel.evaluate_unlock_directive("hey Jarvis, unlock my device")
        self.assertTrue(is_eval)
        self.assertTrue(auth)
        self.assertFalse(device_lock_sentinel.is_locked)

    def test_shutdown_keyword(self):
        # Meta instructions do not shut down
        is_shut, _ = device_power_sentinel.evaluate_shutdown_directive("change shutdown keyword to lets sleep jarvis")
        self.assertFalse(is_shut)

        # Exact keyword triggers shutdown
        is_shut, msg = device_power_sentinel.evaluate_shutdown_directive("Lets Sleep Jarvis")
        self.assertTrue(is_shut)
        self.assertIn("Powering down", msg)

if __name__ == "__main__":
    unittest.main()
