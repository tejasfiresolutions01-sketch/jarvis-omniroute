"""
J.A.R.V.I.S. Live Audio FFT Reactive Visualizer.
Streams real-time microphone input into a Fast Fourier Transform (FFT) pipeline.
Extracts spectral bands (bass, speech formants, treble) and multi-channel equalizer bars
to drive the holographic Arc-Reactor HUD with true acoustic resonance.
"""

import threading
import time
import math
from typing import Dict, List, Optional
import numpy as np

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except Exception:
    HAS_SOUNDDEVICE = False

class AudioVisualizer:
    """
    Real-Time Acoustic FFT Spectrum Processor.
    Computes RMS energy, low/mid/high frequency bands, and multi-band equalizer heights.
    Seamlessly falls back to simulated ambient harmonics if no input device is detected.
    """

    SAMPLERATE = 16000
    BLOCKSIZE = 512
    NUM_BARS = 16
    DECAY = 0.65 # Smoothing filter: 65% previous, 35% new

    def __init__(self):
        self.running = False
        self.stream: Optional[Any] = None
        self.lock = threading.Lock()

        # Smoothed values normalized to [0.0, 1.0]
        self.rms = 0.0
        self.low_band = 0.0   # 60 - 250 Hz (bass/chest resonance)
        self.mid_band = 0.0   # 250 - 2000 Hz (speech formants)
        self.high_band = 0.0  # 2000 - 6000 Hz (treble/consonants)
        self.bars = [0.08] * self.NUM_BARS

        # Butler state: 'idle', 'listening', 'speaking'
        self.state = "idle"
        self._t0 = time.time()

    def start(self):
        """Starts real-time microphone capture in background thread."""
        if self.running:
            return

        self.running = True
        if HAS_SOUNDDEVICE:
            try:
                self.stream = sd.InputStream(
                    channels=1,
                    samplerate=self.SAMPLERATE,
                    blocksize=self.BLOCKSIZE,
                    callback=self._audio_callback
                )
                self.stream.start()
                return
            except Exception as e:
                # Fallback to simulated harmonic resonance if audio device is unavailable
                self.stream = None

    def _audio_callback(self, indata, frames, time_info, status):
        """Processes audio frame with FFT."""
        if not self.running:
            return

        audio = indata[:, 0]
        # 1. RMS Loudness
        raw_rms = float(np.sqrt(np.mean(audio**2))) * 12.0
        norm_rms = min(1.0, max(0.0, raw_rms))

        # 2. Windowed Fast Fourier Transform
        window = np.hanning(len(audio))
        windowed = audio * window
        spectrum = np.abs(np.fft.rfft(windowed))
        freqs = np.fft.rfftfreq(len(audio), 1.0 / self.SAMPLERATE)

        # 3. Frequency bands
        low_mask = (freqs >= 60) & (freqs < 250)
        mid_mask = (freqs >= 250) & (freqs < 2000)
        high_mask = (freqs >= 2000) & (freqs < 6000)

        raw_low = float(np.mean(spectrum[low_mask])) * 3.5 if np.any(low_mask) else 0.0
        raw_mid = float(np.mean(spectrum[mid_mask])) * 8.0 if np.any(mid_mask) else 0.0
        raw_high = float(np.mean(spectrum[high_mask])) * 14.0 if np.any(high_mask) else 0.0

        n_low = min(1.0, max(0.0, raw_low))
        n_mid = min(1.0, max(0.0, raw_mid))
        n_high = min(1.0, max(0.0, raw_high))

        # 4. Multi-bar equalizer heights
        new_bars = []
        step = len(spectrum) // self.NUM_BARS
        for i in range(self.NUM_BARS):
            chunk = spectrum[i * step : (i + 1) * step]
            b_val = float(np.mean(chunk)) * (4.0 + (i * 0.4)) if len(chunk) > 0 else 0.0
            new_bars.append(min(1.0, max(0.08, b_val)))

        with self.lock:
            # Exponential smoothing
            self.rms = (self.DECAY * self.rms) + ((1.0 - self.DECAY) * norm_rms)
            self.low_band = (self.DECAY * self.low_band) + ((1.0 - self.DECAY) * n_low)
            self.mid_band = (self.DECAY * self.mid_band) + ((1.0 - self.DECAY) * n_mid)
            self.high_band = (self.DECAY * self.high_band) + ((1.0 - self.DECAY) * n_high)

            for i in range(self.NUM_BARS):
                self.bars[i] = (self.DECAY * self.bars[i]) + ((1.0 - self.DECAY) * new_bars[i])

    def set_state(self, new_state: str):
        """Updates butler state: 'idle', 'listening', 'speaking'."""
        with self.lock:
            self.state = new_state

    def get_bands(self) -> Dict[str, float]:
        """Returns normalized low, mid, high, and rms values."""
        with self.lock:
            if not self.running or self.stream is None:
                # Synthetic gentle ambient harmonic breathing if stream inactive
                t = time.time() - self._t0
                sim_pulse = (math.sin(t * 2.5) + 1.0) * 0.15 + 0.08
                return {
                    "rms": sim_pulse,
                    "low": sim_pulse * 1.1,
                    "mid": sim_pulse * 0.9,
                    "high": sim_pulse * 0.7,
                    "state": self.state
                }
            return {
                "rms": round(self.rms, 4),
                "low": round(self.low_band, 4),
                "mid": round(self.mid_band, 4),
                "high": round(self.high_band, 4),
                "state": self.state
            }

    def get_bars(self) -> List[float]:
        """Returns list of normalized equalizer bar amplitudes [0.05, 1.0]."""
        with self.lock:
            if not self.running or self.stream is None:
                t = time.time() - self._t0
                return [
                    max(0.08, min(1.0, 0.15 + 0.25 * math.sin(t * 3.0 + i * 0.4)))
                    for i in range(self.NUM_BARS)
                ]
            return list(self.bars)

    def stop(self):
        """Stops background audio streaming."""
        self.running = False
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

# Global singleton
audio_visualizer = AudioVisualizer()
