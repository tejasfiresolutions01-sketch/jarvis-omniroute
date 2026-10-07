"""
Unit tests for J.A.R.V.I.S. 100% Offline Speech-to-Text Engine.
"""

import unittest
import numpy as np
from core.offline_stt import OfflineSTTEngine

class TestOfflineSTT(unittest.TestCase):

    def setUp(self):
        self.engine = OfflineSTTEngine()

    def test_offline_stt_initialization(self):
        # Should initialize and detect Vosk model
        self.assertTrue(self.engine.is_available)

    def test_transcribe_empty_or_silence(self):
        # Empty bytes should return empty string
        res = self.engine.transcribe(b"")
        self.assertEqual(res, "")

        # 0.5s of silence
        silence_pcm = (np.zeros(8000, dtype=np.int16)).tobytes()
        res_silence = self.engine.transcribe(silence_pcm)
        self.assertIsInstance(res_silence, str)

if __name__ == "__main__":
    unittest.main()
