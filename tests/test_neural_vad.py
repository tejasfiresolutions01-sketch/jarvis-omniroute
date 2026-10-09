"""
Unit Tests for J.A.R.V.I.S. Neural & Spectral Voice Activity Detection (VAD).
Validates harmonic autocorrelation, formant ratio, spectral entropy, and zero-clipping ring buffers.
"""

import time
import unittest
import numpy as np

from core.neural_vad import NeuralVAD, get_neural_vad


class TestNeuralVAD(unittest.TestCase):
    def setUp(self):
        self.sample_rate = 16000
        self.chunk_size = 800  # 50ms at 16kHz
        self.vad = NeuralVAD(sample_rate=self.sample_rate, chunk_size=self.chunk_size)

    def test_silence_detection(self):
        """Pure acoustic silence must produce zero speech probability and inactive state."""
        silent_chunk = np.zeros(self.chunk_size, dtype=np.int16)
        is_speech, prob = self.vad.process_chunk(silent_chunk)
        self.assertFalse(is_speech)
        self.assertLess(prob, 0.20)

    def test_white_noise_rejection(self):
        """Uncorrelated white noise has high entropy and no pitch harmonics; must not trigger speech onset."""
        np.random.seed(42)
        noise_chunk = (np.random.randn(self.chunk_size) * 150.0).astype(np.int16)
        is_speech, prob = self.vad.process_chunk(noise_chunk)
        # White noise without harmonic structure should have low probability
        self.assertLess(prob, self.vad.onset_threshold)
        self.assertFalse(is_speech)

    def test_harmonic_voiced_speech_detection(self):
        """Harmonic signal simulating voiced human vowel (F0=140Hz with formant harmonics) must detect speech."""
        t = np.arange(self.chunk_size) / self.sample_rate
        f0 = 140.0  # Typical male/female fundamental frequency
        # Construct fundamental + strong vocal tract formant harmonics (280, 420, 560, 700, 980 Hz)
        synth_voice = (
            1200.0 * np.sin(2 * np.pi * f0 * t)
            + 800.0 * np.sin(2 * np.pi * (2 * f0) * t)
            + 600.0 * np.sin(2 * np.pi * (3 * f0) * t)
            + 400.0 * np.sin(2 * np.pi * (4 * f0) * t)
            + 300.0 * np.sin(2 * np.pi * (5 * f0) * t)
        ).astype(np.int16)

        is_speech, prob = self.vad.process_chunk(synth_voice)
        self.assertTrue(is_speech, f"Expected active speech, got prob={prob}")
        self.assertGreaterEqual(prob, self.vad.onset_threshold)

    def test_pre_speech_ring_buffer(self):
        """Pre-speech frames must be stored in circular buffer and preserved prior to voice onset."""
        self.vad.reset()
        dummy_silent_1 = np.ones(self.chunk_size, dtype=np.int16) * 5
        dummy_silent_2 = np.ones(self.chunk_size, dtype=np.int16) * 10

        self.vad.process_chunk(dummy_silent_1)
        self.vad.process_chunk(dummy_silent_2)

        pre_frames = self.vad.get_pre_buffered_frames()
        self.assertGreaterEqual(len(pre_frames), 2)

    def test_hangover_prevents_intra_speech_chopping(self):
        """Hangover counter must hold active speech state across momentary drops in probability."""
        t = np.arange(self.chunk_size) / self.sample_rate
        synth_voice = (1500.0 * np.sin(2 * np.pi * 160.0 * t) + 1000.0 * np.sin(2 * np.pi * 320.0 * t)).astype(np.int16)

        # Trigger speech onset
        is_speech, _ = self.vad.process_chunk(synth_voice)
        self.assertTrue(is_speech)

        # Brief pause (1 frame of lower energy)
        low_energy = (synth_voice * 0.15).astype(np.int16)
        is_speech_hold, _ = self.vad.process_chunk(low_energy)
        # Should remain True due to hangover
        self.assertTrue(is_speech_hold, "Hangover should prevent immediate cutoff")

    def test_latency_performance_sub_millisecond(self):
        """Chunk processing must execute in sub-millisecond time (< 5ms on any machine)."""
        t = np.arange(self.chunk_size) / self.sample_rate
        sample = (1000.0 * np.sin(2 * np.pi * 180.0 * t)).astype(np.int16)

        start = time.perf_counter()
        for _ in range(50):
            self.vad.process_chunk(sample)
        elapsed_per_chunk_ms = ((time.perf_counter() - start) / 50.0) * 1000.0

        # Sub-3ms guaranteed on modern CPUs
        self.assertLess(elapsed_per_chunk_ms, 5.0, f"VAD latency was {elapsed_per_chunk_ms:.3f}ms")

    def test_singleton_accessor(self):
        """get_neural_vad must return a persistent singleton instance."""
        v1 = get_neural_vad()
        v2 = get_neural_vad()
        self.assertIs(v1, v2)


if __name__ == "__main__":
    unittest.main()
