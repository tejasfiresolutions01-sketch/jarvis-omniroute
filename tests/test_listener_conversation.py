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
        # Conversational tolerance: pause_threshold allows natural human speech pauses (1.5s - 2.5s) without premature cutoff
        self.assertGreaterEqual(self.listener.pause_threshold, 1.5)
        self.assertLessEqual(self.listener.pause_threshold, 2.5)
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

    def test_is_sentence_incomplete_partial_phrases(self):
        # Trailing prepositions, conjunctions, determiners, incomplete phrases
        self.assertTrue(self.listener.is_sentence_incomplete("Jarvis I want you to"))
        self.assertTrue(self.listener.is_sentence_incomplete("Can you please check"))
        self.assertTrue(self.listener.is_sentence_incomplete("Open the"))
        self.assertTrue(self.listener.is_sentence_incomplete("What is the"))
        self.assertTrue(self.listener.is_sentence_incomplete("Schedule a meeting with"))
        self.assertTrue(self.listener.is_sentence_incomplete("Tell me about"))
        self.assertTrue(self.listener.is_sentence_incomplete("Hey Jarvis"))

    def test_is_sentence_incomplete_complete_phrases(self):
        # Full complete directives should not be marked as incomplete
        self.assertFalse(self.listener.is_sentence_incomplete("What is the weather in Chennai?"))
        self.assertFalse(self.listener.is_sentence_incomplete("Open notepad"))
        self.assertFalse(self.listener.is_sentence_incomplete("Turn off the lights"))
        self.assertFalse(self.listener.is_sentence_incomplete("Schedule a meeting with Tony at 3 PM"))
        self.assertFalse(self.listener.is_sentence_incomplete("Stop"))
        self.assertFalse(self.listener.is_sentence_incomplete("Exit"))

if __name__ == "__main__":
    unittest.main()
