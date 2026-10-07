"""
Unit tests for J.A.R.V.I.S. Live Audio FFT Reactive Visualizer.
"""

import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from core.audio_visualizer import AudioVisualizer

class TestAudioVisualizer(unittest.TestCase):

    def setUp(self):
        self.viz = AudioVisualizer()

    def tearDown(self):
        self.viz.stop()

    def test_initialization(self):
        self.assertFalse(self.viz.running)
        self.assertIsNone(self.viz.stream)
        self.assertEqual(len(self.viz.bars), AudioVisualizer.NUM_BARS)
        self.assertEqual(self.viz.state, "idle")
        self.assertEqual(self.viz.rms, 0.0)

    def test_state_transition(self):
        self.viz.set_state("listening")
        self.assertEqual(self.viz.state, "listening")
        self.viz.set_state("speaking")
        self.assertEqual(self.viz.state, "speaking")
        self.viz.set_state("idle")
        self.assertEqual(self.viz.state, "idle")

    def test_fallback_bands_and_bars(self):
        # When not running, get_bands and get_bars provide synthetic breathing harmonics
        bands = self.viz.get_bands()
        self.assertIn("rms", bands)
        self.assertIn("low", bands)
        self.assertIn("mid", bands)
        self.assertIn("high", bands)
        self.assertIn("state", bands)
        self.assertGreaterEqual(bands["rms"], 0.0)

        bars = self.viz.get_bars()
        self.assertEqual(len(bars), AudioVisualizer.NUM_BARS)
        for b in bars:
            self.assertGreaterEqual(b, 0.05)
            self.assertLessEqual(b, 1.0)

    def test_audio_callback_fft_computation(self):
        self.viz.running = True
        # Generate 512 samples of a 440 Hz tone (within speech/mid band)
        t = np.linspace(0, 512 / 16000, 512, endpoint=False)
        tone = np.sin(2 * np.pi * 440 * t).astype(np.float32)
        indata = tone.reshape(-1, 1)

        # Execute callback
        self.viz._audio_callback(indata, 512, None, None)

        self.assertGreater(self.viz.rms, 0.0)
        self.assertGreater(self.viz.mid_band, 0.0)
        self.assertEqual(len(self.viz.bars), AudioVisualizer.NUM_BARS)
        self.assertTrue(any(b > 0.08 for b in self.viz.bars))

        # Check get_bands and get_bars with active values
        self.viz.stream = MagicMock() # simulate active stream
        bands = self.viz.get_bands()
        self.assertEqual(bands["state"], "idle")
        self.assertAlmostEqual(bands["rms"], round(self.viz.rms, 4))

        bars = self.viz.get_bars()
        self.assertEqual(len(bars), AudioVisualizer.NUM_BARS)

    @patch("core.audio_visualizer.sd.InputStream")
    def test_start_and_stop_lifecycle(self, mock_input_stream):
        mock_instance = MagicMock()
        mock_input_stream.return_value = mock_instance

        self.viz.start()
        self.assertTrue(self.viz.running)
        mock_instance.start.assert_called_once()

        self.viz.stop()
        self.assertFalse(self.viz.running)
        mock_instance.stop.assert_called_once()
        mock_instance.close.assert_called_once()
        self.assertIsNone(self.viz.stream)

if __name__ == "__main__":
    unittest.main()
