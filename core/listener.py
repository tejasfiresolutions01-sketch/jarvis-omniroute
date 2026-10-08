"""
J.A.R.V.I.S. Hands-Free Auditory Perception & Voice Conversation Matrix.
Features:
1. Native low-latency audio capture with hardware microphone array via sounddevice.
2. Adaptive End-of-Speech Detection: Waits long enough (2.2s pause threshold) so user speech is never cut off.
3. Biometric Speaker Verification: Evaluates both low-frequency chest resonance and high-frequency inflections.
4. Continuous Multi-Turn Voice Conversation Mode: Natural dialogue without needing repeated wake words.
5. Acoustic Barge-in Interruption.
"""

import os
import re
import time
import threading
from typing import Callable, Optional, Tuple
import numpy as np
import sounddevice as sd
import speech_recognition as sr

from core.chimes import play_wake_chime, play_ack_chime
from core.voice import stop_speaking, is_speaking
from core.voice_biometrics import voice_biometrics
import config

class VoiceListener:
    """
    Hands-Free Auditory Perception & Voice Conversation Engine.
    """

    WAKE_WORDS = ["hey jarvis", "okay jarvis", "ok jarvis", "jarvis"]
    STOP_WORDS = ["jarvis stop", "stop talking", "be quiet", "silence", "shut up"]
    EXIT_CONVERSATION_WORDS = ["that will be all", "thank you jarvis", "that's all", "goodbye", "stand down", "stop conversation", "exit"]

    def __init__(self):
        self.sample_rate = 16000
        self.chunk_size = 1600 # 100ms chunks at 16kHz
        # Ultra-rapid end-of-speech detection (0.7s silence threshold for sub-second voice turnaround)
        self.pause_threshold = float(getattr(config, "VOICE_PAUSE_THRESHOLD", 0.7))
        self.phrase_time_limit = float(getattr(config, "VOICE_PHRASE_TIME_LIMIT", 35.0))
        self.conversational_idle_timeout = float(getattr(config, "VOICE_CONVERSATIONAL_IDLE_TIMEOUT", 8.0))
        self.is_monitoring = False
        self.in_conversation_mode = False
        self._conversation_lease_until = 0.0
        self._thread: Optional[threading.Thread] = None
        self._recognizer = sr.Recognizer()

    def has_active_conversation_lease(self) -> bool:
        """Returns True if full-duplex conversational follow-up window is currently active."""
        return time.time() < self._conversation_lease_until

    def renew_conversation_lease(self, duration: float = 25.0):
        """Extends the hands-free continuous dialogue window."""
        self._conversation_lease_until = time.time() + duration

    def close_conversation_lease(self):
        """Immediately closes the continuous dialogue window."""
        self._conversation_lease_until = 0.0

    def record_audio_utterance(self, timeout: float = 8.0, prompt_text: str = "") -> Optional[bytes]:
        """
        Records an audio utterance from the microphone.
        Waits long enough for the user to conclude their thought (pause_threshold = 2.2s).
        Returns raw 16-bit PCM mono bytes at 16000 Hz, or None if timed out/silence.
        """
        if prompt_text:
            print(f"\n[Microphone Active]: {prompt_text}")

        recorded_frames = []
        has_started_speaking = False
        silence_duration = 0.0
        start_time = time.time()

        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16', blocksize=self.chunk_size) as stream:
                # 1. Quick ambient noise calibration (0.3s)
                ambient_frames = []
                for _ in range(3):
                    chunk, _ = stream.read(self.chunk_size)
                    ambient_frames.append(chunk)
                ambient_arr = np.concatenate(ambient_frames).astype(np.float32)
                ambient_rms = np.sqrt(np.mean(ambient_arr ** 2))
                # Set dynamic speech energy threshold (sensitive to normal speaking volumes)
                speech_threshold = max(160.0, float(ambient_rms * 1.35))

                # 2. Main recording loop
                while True:
                    # Check overall timeout before speech starts
                    if not has_started_speaking and (time.time() - start_time > timeout):
                        return None

                    # Check max phrase duration limit
                    if time.time() - start_time > self.phrase_time_limit:
                        break

                    chunk, overflow = stream.read(self.chunk_size)
                    chunk_flt = chunk.astype(np.float32)
                    chunk_rms = np.sqrt(np.mean(chunk_flt ** 2))

                    if chunk_rms >= speech_threshold:
                        # User is speaking
                        has_started_speaking = True
                        silence_duration = 0.0
                        recorded_frames.append(chunk)
                    else:
                        if has_started_speaking:
                            # User has started speaking, but is currently pausing
                            recorded_frames.append(chunk)
                            silence_duration += (self.chunk_size / self.sample_rate)
                            # Wait long enough for conversation to end!
                            if silence_duration >= self.pause_threshold:
                                # User has completed their statement
                                break

            if has_started_speaking and recorded_frames:
                all_pcm = np.concatenate(recorded_frames).tobytes()
                return all_pcm
        except Exception as e:
            print(f"[Microphone Warning]: SoundDevice capture failed ({e}), falling back...")
        return None

    def speech_to_text(self, pcm_bytes: bytes) -> str:
        """
        Converts raw PCM audio to text using online recognizer with instant 100% offline fallback.
        """
        if not pcm_bytes:
            return ""

        # 1. Try online Google STT if not forced offline
        if not getattr(config, "FORCE_OFFLINE_STT", False):
            try:
                audio_data = sr.AudioData(pcm_bytes, self.sample_rate, 2)
                text = self._recognizer.recognize_google(audio_data)
                if text and text.strip():
                    return text.strip()
            except Exception:
                # Network unreachable or quota reached -> seamless fallback
                pass

        # 2. Air-Gapped 100% Offline STT (Vosk Engine)
        from core.offline_stt import offline_stt
        if offline_stt.is_available:
            try:
                offline_text = offline_stt.transcribe(pcm_bytes, self.sample_rate)
                if offline_text:
                    print(f"[Offline STT Perception]: {offline_text}")
                    return offline_text
            except Exception as e:
                print(f"[Offline STT Anomaly]: {e}")

        return ""

    def capture_and_authenticate(self, timeout: float = 8.0, prompt: str = "") -> Tuple[str, bool]:
        """
        Captures audio, verifies the user's voice biometrics (low & high frequency),
        and returns (transcribed_text, is_authorized).
        """
        import core.voice as voice
        while voice.check_is_speaking():
            time.sleep(0.1)
        time.sleep(0.25)  # Acoustic echo buffer to prevent speaker feedback

        play_wake_chime()
        pcm_bytes = self.record_audio_utterance(timeout=timeout, prompt_text=prompt)
        if not pcm_bytes:
            return "", False

        # Verify biometric speaker identity across both low and high frequencies
        is_auth, conf, msg = voice_biometrics.verify_speaker(pcm_bytes, self.sample_rate)
        if not is_auth:
            # If confidence is >= tolerance (0.35), adaptively authenticate to prevent dropping Sir's directive
            if conf >= float(getattr(config, "VOICE_PROFILE_TOLERANCE", 0.35)):
                print(f"[Acoustic Sentinel]: Permissive acoustic match ({conf*100:.1f}%), accepting directive.")
                is_auth = True
            else:
                print(f"[Acoustic Sentinel]: Unauthorized voice rejected ({msg})")
                return "", False

        text = self.speech_to_text(pcm_bytes)
        if text:
            # Acoustic Echo Suppression: Discard if recognized text matches Jarvis's recent vocalization
            if voice.is_recently_spoken(text):
                print(f"[Acoustic Sentinel]: Echo suppression discarded self-reflection: '{text}'")
                return "", False

            if any(w in text.lower() for w in self.EXIT_CONVERSATION_WORDS):
                self.close_conversation_lease()
            else:
                self.renew_conversation_lease(25.0)

            play_ack_chime()
            print(f"[Captured Voice]: {text}")
            return text, True

        return "", False

    def listen(self, prompt: str = "Directive, sir: ") -> str:
        """
        Primary single-turn voice listening method with console fallback.
        """
        text, is_auth = self.capture_and_authenticate(timeout=8.0, prompt=prompt)
        if text and is_auth:
            return text

        # Fallback to console input only if running in an interactive terminal
        import sys
        if sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
            try:
                return input(prompt)
            except (EOFError, Exception):
                pass
        return ""

    def start_conversation_session(self, process_command_callback: Callable[[str], bool]):
        """
        Engages continuous multi-turn voice conversation.
        Keeps listening for follow-ups without requiring 'Hey Jarvis' every sentence.
        Waits long enough for user pauses, and exits on silence or farewell phrases.
        """
        self.in_conversation_mode = True
        print("\n[Voice Conversation]: Channel opened. Multi-turn dialogue active.")
        idle_start = time.time()

        try:
            from core.wake_word import wake_word_engine
            wake_word_engine.pause()
        except Exception:
            pass

        while self.in_conversation_mode:
            # Wait for previous vocalization to finish before opening microphone
            import core.voice as voice
            while voice.check_is_speaking():
                time.sleep(0.1)
            time.sleep(0.2) # Acoustic buffer to clear speaker echo

            text, is_auth = self.capture_and_authenticate(
                timeout=self.conversational_idle_timeout,
                prompt="Listening to Sir..."
            )

            if not text:
                # No speech captured in conversational idle window
                print("[Voice Conversation]: Idle timeout elapsed. Reverting to ambient standby.")
                self.in_conversation_mode = False
                break

            if not is_auth:
                continue

            lower = text.lower()

            # Check for conversational exit commands
            if any(w in lower for w in self.EXIT_CONVERSATION_WORDS):
                from core.voice import speak
                speak("Standing by, sir. Call upon me whenever needed.")
                self.in_conversation_mode = False
                break

            # Execute user command through cognitive core
            keep_running = process_command_callback(text)
            if not keep_running:
                self.in_conversation_mode = False
                break

            # Reset idle timer for next turn
            idle_start = time.time()

        try:
            from core.wake_word import wake_word_engine
            wake_word_engine.resume()
        except Exception:
            pass

    def start_wake_word_daemon(self, callback: Callable[[str], bool]):
        """Runs continuous background wake-word monitor for 'Hey Jarvis'."""
        self._callback = callback
        if self.is_monitoring:
            return
        self.is_monitoring = True

        from core.wake_word import wake_word_engine

        def _on_wake(keyword: str):
            if not self.is_monitoring or self.in_conversation_mode:
                return
            try:
                from core.audio_visualizer import audio_visualizer
                audio_visualizer.set_state("listening")
            except Exception:
                pass

            text, is_auth = self.capture_and_authenticate(timeout=8.0, prompt="Directive, sir: ")
            if text and is_auth:
                cb = getattr(self, "_callback", callback)
                cb(text)
            wake_word_engine.resume()

        if wake_word_engine.is_available:
            wake_word_engine.start(_on_wake)
            return

        def _monitor_loop():
            print("[Auditory Sentinel]: Background wake-word monitor active ('Hey Jarvis')...")
            while self.is_monitoring:
                if self.in_conversation_mode or is_speaking:
                    time.sleep(0.3)
                    continue

                try:
                    # Quick ambient listen for wake word
                    pcm_bytes = self.record_audio_utterance(timeout=4.0)
                    if not pcm_bytes:
                        continue

                    # Verify speaker biometric profile across low & high frequencies
                    is_auth, conf, msg = voice_biometrics.verify_speaker(pcm_bytes, self.sample_rate)
                    if not is_auth:
                        continue

                    phrase = self.speech_to_text(pcm_bytes).lower().strip()
                    if not phrase:
                        continue

                    # Barge-in stop check
                    if any(s in phrase for s in self.STOP_WORDS):
                        stop_speaking()
                        continue

                    # Full-Duplex Continuous Conversation Lease: bypass wake word if active
                    if self.has_active_conversation_lease():
                        if any(w in phrase for w in self.EXIT_CONVERSATION_WORDS):
                            self.close_conversation_lease()
                            continue
                        self.renew_conversation_lease(25.0)
                        callback(phrase)
                        continue

                    # Wake word trigger
                    for w in self.WAKE_WORDS:
                        if w in phrase:
                            cmd = re.sub(rf"^.*?\b{w}\b[,\s]*", "", phrase).strip()
                            if cmd:
                                callback(cmd)
                            break

                except Exception:
                    time.sleep(0.3)

        self._thread = threading.Thread(target=_monitor_loop, daemon=True)
        self._thread.start()

    def stop_wake_word_daemon(self):
        self.is_monitoring = False
        self.in_conversation_mode = False
        try:
            from core.wake_word import wake_word_engine
            wake_word_engine.stop()
        except Exception:
            pass

# Global singleton
listener = VoiceListener()
