"""
Unit tests for VoiceListener end-of-speech silence threshold and conversational flow.
"""

import unittest
from unittest.mock import patch, MagicMock
from core.listener import VoiceListener

class TestListenerConversation(unittest.TestCase):

    def setUp(self):
        self.listener = VoiceListener()

    def test_default_pause_threshold(self):
        # Responsiveness optimization: pause_threshold calibrated for rapid conversational turn-taking (<= 1.0s)
        self.assertLessEqual(self.listener.pause_threshold, 1.0)
        self.assertGreaterEqual(self.listener.pause_threshold, 0.4)
        self.assertGreaterEqual(self.listener.phrase_time_limit, 30.0)

    def test_conversational_exit_words(self):
        self.assertIn("that will be all", self.listener.EXIT_CONVERSATION_WORDS)
        self.assertIn("thank you jarvis", self.listener.EXIT_CONVERSATION_WORDS)
        self.assertIn("goodbye", self.listener.EXIT_CONVERSATION_WORDS)

    @patch("speech_recognition.Recognizer.recognize_google")
    def test_speech_to_text(self, mock_recognize):
        mock_recognize.return_value = "Initiate system diagnostic"
        fake_pcm = b"\x00" * 3200
        text = self.listener.speech_to_text(fake_pcm)
        self.assertEqual(text, "Initiate system diagnostic")

if __name__ == "__main__":
    unittest.main()
