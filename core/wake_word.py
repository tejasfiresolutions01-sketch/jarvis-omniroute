"""
J.A.R.V.I.S. Autonomous Streaming Wake-Word Engine.
Provides ultra-low latency, zero-cloud, 100% offline keyword spotting
for 'Jarvis' and 'Hey Jarvis' using grammar-constrained acoustic modeling.
"""

import os
import json
import time
import math
import threading
from typing import Callable, Optional, List
import numpy as np

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except Exception:
    HAS_SOUNDDEVICE = False

try:
    import vosk
    HAS_VOSK = True
except Exception:
    HAS_VOSK = False

from core.chimes import play_wake_chime
import core.voice as voice

class WakeWordEngine:
    """
    Sub-100ms Autonomous Wake-Word Spotter.
    Operates on streaming audio chunks with an energy gate and grammar-constrained
    Kaldi search graph to detect wake words with near-zero CPU footprint.
    """

    SAMPLE_RATE = 16000
    CHUNK_SIZE = 1600  # 100ms chunks at 16kHz
    KEYPHRASES = ["hey jarvis", "jarvis", "okay jarvis", "ok jarvis"]

    def __init__(self, energy_threshold: float = 280.0):
        self.energy_threshold = energy_threshold
        self.running = False
        self.paused = False
        self.callback: Optional[Callable[[str], None]] = None
        self._thread: Optional[threading.Thread] = None
        self._stream: Optional[Any] = None
        self._lock = threading.Lock()
        self._last_trigger_time = 0.0
        self._cooldown = 1.5 # seconds between triggers

        self._model = None
        self._recognizer = None
        self._init_recognizer()

    def _init_recognizer(self):
        """Initializes grammar-constrained Kaldi recognizer via Vosk."""
        if not HAS_VOSK:
            return

        try:
            from core.offline_stt import offline_stt
            if offline_stt.is_available and offline_stt._vosk_model:
                self._model = offline_stt._vosk_model
            else:
                vosk.SetLogLevel(-1)
                self._model = vosk.Model(lang="en-us")

            # Grammar limits search space to only our wake words + unknown noise
            grammar = json.dumps(self.KEYPHRASES + ["[unk]"])
            self._recognizer = vosk.KaldiRecognizer(self._model, self.SAMPLE_RATE, grammar)
            self._recognizer.SetWords(False)
        except Exception as e:
            print(f"[WakeWord Engine Warning]: Kaldi recognizer initialization deferred: {e}")
            self._recognizer = None

    @property
    def is_available(self) -> bool:
        """Returns True if the underlying acoustic recognizer is ready."""
        return self._recognizer is not None

    def pause(self):
        """Pauses wake word listening (e.g. while J.A.R.V.I.S. is speaking or recording)."""
        with self._lock:
            self.paused = True

    def resume(self):
        """Resumes wake word listening."""
        with self._lock:
            self.paused = False
            if self._recognizer:
                try:
                    self._recognizer.Reset()
                except Exception:
                    pass

    def check_audio_chunk(self, chunk_bytes: bytes) -> Optional[str]:
        """
        Processes a single raw 16-bit PCM mono audio chunk.
        Returns the detected keyword if recognized, otherwise None.
        """
        if not chunk_bytes or not self._recognizer:
            return None

        # 1. Energy Gate: check RMS to skip silent frames
        samples = np.frombuffer(chunk_bytes, dtype=np.int16).astype(np.float32)
        if len(samples) == 0:
            return None

        rms = float(np.sqrt(np.mean(samples ** 2)))
        if rms < self.energy_threshold:
            return None

        # 2. Kaldi Streaming Decoding
        now = time.time()
        if now - self._last_trigger_time < self._cooldown:
            return None

        try:
            matched_phrase = None
            if self._recognizer.AcceptWaveform(chunk_bytes):
                res = json.loads(self._recognizer.Result())
                text = res.get("text", "").lower().strip()
                for kw in self.KEYPHRASES:
                    if kw in text:
                        matched_phrase = kw
                        break
            else:
                part = json.loads(self._recognizer.PartialResult())
                ptext = part.get("partial", "").lower().strip()
                for kw in self.KEYPHRASES:
                    if kw in ptext:
                        matched_phrase = kw
                        break

            if matched_phrase:
                self._last_trigger_time = now
                self._recognizer.Reset()
                return matched_phrase

        except Exception:
            pass

        return None

    def _worker_loop(self):
        """Streaming audio capture loop using sounddevice."""
        if not HAS_SOUNDDEVICE:
            return

        print("[WakeWord Engine]: Ultra-low latency acoustic monitoring active ('Hey Jarvis')...")

        try:
            with sd.RawInputStream(
                samplerate=self.SAMPLE_RATE,
                blocksize=self.CHUNK_SIZE,
                dtype='int16',
                channels=1
            ) as stream:
                self._stream = stream
                while self.running:
                    # Skip if paused or Jarvis is actively vocalizing
                    if self.paused or voice.is_speaking:
                        time.sleep(0.08)
                        continue

                    data, overflowed = stream.read(self.CHUNK_SIZE)
                    if not data:
                        continue

                    chunk_bytes = bytes(data)

                    # Full-Duplex Continuous Dialogue: check active conversational lease
                    try:
                        from core.listener import listener
                        from core.voice_biometrics import voice_biometrics
                        if listener.has_active_conversation_lease():
                            samples = np.frombuffer(chunk_bytes, dtype=np.int16).astype(np.float32)
                            if len(samples) > 0:
                                rms = float(np.sqrt(np.mean(samples ** 2)))
                                if rms >= self.energy_threshold and voice_biometrics.is_owner_speaking(chunk_bytes, self.SAMPLE_RATE):
                                    print("\n[WakeWord Engine]: Active conversational lease follow-up triggered.")
                                    self.pause()
                                    if self.callback:
                                        threading.Thread(target=self.callback, args=("followup",), daemon=True).start()
                                    continue
                    except Exception:
                        pass

                    detected = self.check_audio_chunk(chunk_bytes)
                    if detected:
                        print(f"\n[WakeWord Engine]: Wake phrase spotted: '{detected}'")
                        self.pause()
                        try:
                            play_wake_chime()
                        except Exception:
                            pass

                        if self.callback:
                            threading.Thread(target=self.callback, args=(detected,), daemon=True).start()

        except Exception as e:
            print(f"[WakeWord Engine Notice]: Audio stream paused or closed: {e}")
        finally:
            self._stream = None

    def start(self, callback: Callable[[str], None]):
        """Starts real-time wake word monitoring thread."""
        if self.running:
            return

        self.callback = callback
        self.running = True
        self.paused = False
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the wake word monitoring thread and closes audio stream."""
        self.running = False
        self.paused = True
        self._stream = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

# Global singleton
wake_word_engine = WakeWordEngine()
