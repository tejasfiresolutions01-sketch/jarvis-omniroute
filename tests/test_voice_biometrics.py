"""
Unit tests for J.A.R.V.I.S. Dual-Frequency Voice Biometrics & Speaker Verification.
"""

import unittest
import numpy as np
from core.voice_biometrics import VoiceBiometrics

class TestVoiceBiometrics(unittest.TestCase):

    def setUp(self):
        self.biometrics = VoiceBiometrics()
        self.biometrics.enabled = True
        self.sample_rate = 16000

    def _generate_synthetic_tone(self, freq: float, duration: float = 1.0) -> bytes:
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        # Fundamental tone + harmonic
        wave = 0.6 * np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * (freq * 2) * t)
        return (wave * 32767).astype(np.int16).tobytes()

    def test_low_frequency_feature_extraction(self):
        # 105 Hz deep chest register
        pcm = self._generate_synthetic_tone(105.0)
        feats = self.biometrics.extract_features(pcm, self.sample_rate)
        self.assertIsNotNone(feats)
        self.assertIsNotNone(feats["f0"])
        # Should detect F0 near 105 Hz within 10%
        self.assertAlmostEqual(feats["f0"], 105.0, delta=12.0)
        self.assertGreater(feats["spectral_centroid"], 0)

    def test_high_frequency_feature_extraction(self):
        # 260 Hz elevated voice / pitch inflection
        pcm = self._generate_synthetic_tone(260.0)
        feats = self.biometrics.extract_features(pcm, self.sample_rate)
        self.assertIsNotNone(feats)
        self.assertIsNotNone(feats["f0"])
        # Should detect F0 near 260 Hz within 10%
        self.assertAlmostEqual(feats["f0"], 260.0, delta=25.0)

    def test_dual_frequency_speaker_verification(self):
        # Auto-calibrates / enrolls on initial samples
        self.biometrics.profile["enrolled"] = False
        low_pcm = self._generate_synthetic_tone(115.0)
        high_pcm = self._generate_synthetic_tone(240.0)

        # Calibrate with both low and high pitch
        self.biometrics.calibrate(low_pcm, self.sample_rate)
        self.biometrics.calibrate(high_pcm, self.sample_rate)

        # Verify low frequency response
        auth_low, conf_low, msg_low = self.biometrics.verify_speaker(low_pcm, self.sample_rate)
        self.assertTrue(auth_low)
        self.assertGreaterEqual(conf_low, 0.60)

        # Verify high frequency response
        auth_high, conf_high, msg_high = self.biometrics.verify_speaker(high_pcm, self.sample_rate)
        self.assertTrue(auth_high)
        self.assertGreaterEqual(conf_high, 0.60)

    def test_empty_or_silence_handling(self):
        empty_pcm = b""
        feats = self.biometrics.extract_features(empty_pcm, self.sample_rate)
        self.assertIsNone(feats)

        # Whisper or low amplitude permits pass-through for STT
        auth, conf, msg = self.biometrics.verify_speaker(empty_pcm, self.sample_rate)
        self.assertTrue(auth)

if __name__ == "__main__":
    unittest.main()
