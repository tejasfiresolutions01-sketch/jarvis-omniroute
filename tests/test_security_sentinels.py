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

    def test_unlock_directive_variations(self):
        variations = [
            "unlock my device",
            "unlock device",
            "unlock the device",
            "unlock this device",
            "unlock screen",
            "unlock workstation",
            "unlock computer",
            "unlock pc",
            "unlock system",
            "hey jarvis, unlock my device",
            "hey jarvis unlock screen",
            "please unlock workstation",
            "also make jarvis unlock my device"
        ]
        for phrase in variations:
            device_lock_sentinel.is_locked = True
            is_eval, auth, msg = device_lock_sentinel.evaluate_unlock_directive(phrase)
            self.assertTrue(is_eval, f"Failed evaluation for: {phrase}")
            self.assertTrue(auth, f"Failed authorization for: {phrase}")
            self.assertFalse(device_lock_sentinel.is_locked)
            self.assertIn("Authentication verified", msg)

    def test_negative_unlock_rejection(self):
        negatives = [
            "don't unlock my device",
            "do not unlock screen",
            "never unlock workstation",
            "cancel unlock my device"
        ]
        for neg in negatives:
            device_lock_sentinel.is_locked = True
            is_eval, auth, msg = device_lock_sentinel.evaluate_unlock_directive(neg)
            # Should not be authorized as an unlock action
            self.assertFalse(auth, f"Should reject negative command: {neg}")

    def test_hardware_unlock_routine(self):
        from unittest.mock import patch, MagicMock
        import config

        # Test with PIN
        with patch.object(config, "DEVICE_UNLOCK_PIN", "4321"):
            with patch("ctypes.windll") as mock_windll:
                msg = device_lock_sentinel.unlock_device(simulate_hardware=True)
                self.assertFalse(device_lock_sentinel.is_locked)
                self.assertIn("credentials submitted", msg)
                self.assertTrue(mock_windll.kernel32.SetThreadExecutionState.called)
                self.assertTrue(mock_windll.user32.SendMessageW.called)
                self.assertTrue(mock_windll.user32.keybd_event.called)

        # Test without PIN
        with patch.object(config, "DEVICE_UNLOCK_PIN", ""):
            with patch("ctypes.windll") as mock_windll:
                msg = device_lock_sentinel.unlock_device(simulate_hardware=True)
                self.assertFalse(device_lock_sentinel.is_locked)
                self.assertIn("Device display awakened", msg)


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
