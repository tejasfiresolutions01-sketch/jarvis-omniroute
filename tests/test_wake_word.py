"""
Unit tests for J.A.R.V.I.S. Autonomous Streaming Wake-Word Engine.
"""

import json
import time
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from core.wake_word import WakeWordEngine

class TestWakeWordEngine(unittest.TestCase):

    def setUp(self):
        self.engine = WakeWordEngine(energy_threshold=200.0)

    def tearDown(self):
        self.engine.stop()

    def test_initialization(self):
        self.assertFalse(self.engine.running)
        self.assertFalse(self.engine.paused)
        self.assertIn("jarvis", self.engine.KEYPHRASES)
        self.assertIn("hey jarvis", self.engine.KEYPHRASES)

    def test_pause_and_resume(self):
        self.engine.pause()
        self.assertTrue(self.engine.paused)
        self.engine.resume()
        self.assertFalse(self.engine.paused)

    def test_energy_gate_silence_rejection(self):
        # 3200 zero bytes (1600 samples of pure silence, RMS = 0)
        silent_chunk = b"\x00" * 3200
        detected = self.engine.check_audio_chunk(silent_chunk)
        self.assertIsNone(detected)

    def test_check_audio_chunk_full_match(self):
        # Create non-silent audio chunk (high RMS)
        arr = np.full(1600, 1000, dtype=np.int16)
        chunk = arr.tobytes()

        mock_rec = MagicMock()
        mock_rec.AcceptWaveform.return_value = True
        mock_rec.Result.return_value = json.dumps({"text": "hey jarvis"})
        self.engine._recognizer = mock_rec

        # Reset trigger time
        self.engine._last_trigger_time = 0.0
        detected = self.engine.check_audio_chunk(chunk)
        self.assertEqual(detected, "hey jarvis")
        mock_rec.Reset.assert_called_once()

    def test_check_audio_chunk_partial_match(self):
        arr = np.full(1600, 1000, dtype=np.int16)
        chunk = arr.tobytes()

        mock_rec = MagicMock()
        mock_rec.AcceptWaveform.return_value = False
        mock_rec.PartialResult.return_value = json.dumps({"partial": "jarvis"})
        self.engine._recognizer = mock_rec

        self.engine._last_trigger_time = 0.0
        detected = self.engine.check_audio_chunk(chunk)
        self.assertEqual(detected, "jarvis")

    def test_cooldown_rejection(self):
        arr = np.full(1600, 1000, dtype=np.int16)
        chunk = arr.tobytes()

        # Set last trigger time to right now
        self.engine._last_trigger_time = time.time()
        detected = self.engine.check_audio_chunk(chunk)
        self.assertIsNone(detected)

    @patch("sounddevice.RawInputStream")
    def test_start_and_stop(self, mock_stream_cls):
        mock_stream = MagicMock()
        mock_stream_cls.return_value.__enter__.return_value = mock_stream

        callback = MagicMock()
        self.engine.start(callback)
        self.assertTrue(self.engine.running)

        self.engine.stop()
        self.assertFalse(self.engine.running)
        self.assertTrue(self.engine.paused)

if __name__ == "__main__":
    unittest.main()
