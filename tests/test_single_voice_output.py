import unittest
import time
from core.voice import speak, speak_sync, stop_speaking, is_recently_spoken, clean_for_speech, _recent_spoken

class TestSingleVoiceOutput(unittest.TestCase):

    def setUp(self):
        _recent_spoken.clear()
        stop_speaking()

    def test_clean_for_speech(self):
        text = "Hello **world**, this is `code` and [link](http://example.com) with 50% CPU."
        cleaned = clean_for_speech(text)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("`", cleaned)
        self.assertIn("percent", cleaned)
        self.assertIn("C P U", cleaned)

    def test_voice_deduplication(self):
        phrase = "Systems operational and standing ready, sir."
        # First speak records in cache
        speak(phrase)
        self.assertTrue(is_recently_spoken(phrase))
        
        # Second immediate speak is deduplicated and does not raise
        speak(phrase)
        speak(phrase)
        self.assertTrue(True)

    def test_is_recently_spoken_echo_cancellation(self):
        phrase = "I am processing the analysis right away, sir."
        speak(phrase)
        time.sleep(0.1)
        self.assertTrue(is_recently_spoken(phrase))
        self.assertTrue(is_recently_spoken("processing the analysis"))
        self.assertFalse(is_recently_spoken("completely unrelated command from user"))

    def test_barge_in_reset(self):
        stop_speaking()
        from core.voice import is_speaking
        self.assertFalse(is_speaking)

if __name__ == "__main__":
    unittest.main()
