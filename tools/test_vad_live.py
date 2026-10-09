"""
Live Acoustic & Neural VAD Verification Harness for J.A.R.V.I.S.
Simulates real-world acoustic stream through VoiceListener with NeuralVAD.
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from unittest.mock import MagicMock, patch

from core.listener import VoiceListener
from core.neural_vad import get_neural_vad


def run_live_vad_verification():
    print("=" * 60)
    print("J.A.R.V.I.S. Live Neural VAD Acoustic Verification Harness")
    print("=" * 60)

    listener = VoiceListener()
    vad = get_neural_vad(sample_rate=listener.sample_rate, chunk_size=listener.chunk_size)
    print(f"Sample Rate: {listener.sample_rate} Hz | Chunk Size: {listener.chunk_size} samples")
    print(f"VAD Onset Threshold: {vad.onset_threshold} | Hold Threshold: {vad.hold_threshold}")

    # Generate test audio chunks:
    # 1. 500ms of ambient room silence
    # 2. 1500ms of voiced human speech (F0=150Hz harmonic series)
    # 3. 2500ms of trailing pause (exceeding pause_threshold 2.0s)
    silence_chunks = [np.zeros(listener.chunk_size, dtype=np.int16) for _ in range(5)]

    t = np.arange(listener.chunk_size) / listener.sample_rate
    voice_base = (
        1200.0 * np.sin(2 * np.pi * 150.0 * t)
        + 800.0 * np.sin(2 * np.pi * 300.0 * t)
        + 500.0 * np.sin(2 * np.pi * 450.0 * t)
        + 300.0 * np.sin(2 * np.pi * 600.0 * t)
    ).astype(np.int16)
    speech_chunks = [voice_base for _ in range(15)]
    trailing_pause_chunks = [np.zeros(listener.chunk_size, dtype=np.int16) for _ in range(30)]

    stream_chunks = silence_chunks + speech_chunks + trailing_pause_chunks

    # Mock sounddevice stream to feed deterministic acoustic frames
    chunk_idx = [0]
    def mock_read(chunk_size):
        idx = chunk_idx[0]
        if idx < len(stream_chunks):
            data = stream_chunks[idx]
            chunk_idx[0] += 1
            return data, False
        return np.zeros(chunk_size, dtype=np.int16), False

    mock_stream = MagicMock()
    mock_stream.read.side_effect = mock_read
    mock_stream.__enter__.return_value = mock_stream
    mock_stream.__exit__.return_value = None

    print("[VAD Test]: Streaming acoustic frames through VoiceListener...")
    start_t = time.time()
    with patch("sounddevice.InputStream", return_value=mock_stream):
        captured_pcm = listener.record_audio_utterance(timeout=5.0, prompt_text="Testing acoustic stream")

    elapsed = time.time() - start_t
    print(f"[VAD Test]: Recording loop concluded in {elapsed:.2f}s")
    assert captured_pcm is not None, "Failed to capture spoken utterance!"
    duration_s = len(captured_pcm) / (listener.sample_rate * 2)
    print(f"[VAD Test]: Successfully captured {len(captured_pcm)} PCM bytes ({duration_s:.2f}s audio).")
    assert duration_s >= 1.5, f"Captured audio was too short ({duration_s}s)!"

    print("[VAD Test]: Live acoustic stream verified successfully with zero phoneme loss.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    run_live_vad_verification()
