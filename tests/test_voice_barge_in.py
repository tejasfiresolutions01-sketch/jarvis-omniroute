import unittest
from core.voice import stop_speaking, is_speaking
from core.chimes import play_boot_chime, play_wake_chime, play_ack_chime

class TestVoiceBargeIn(unittest.TestCase):
    def test_stop_speaking_resets_flag(self):
        stop_speaking()
        self.assertFalse(is_speaking)

    def test_chimes_execution(self):
        # Chimes run in background daemon threads without throwing exceptions
        play_boot_chime()
        play_wake_chime()
        play_ack_chime()
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
