import threading
import time
import re
from typing import Callable, Optional
from core.chimes import play_wake_chime, play_ack_chime
from core.voice import stop_speaking

class VoiceListener:
    """
    Hands-Free Auditory Perception & Wake-Word Interceptor.
    Continuously monitors microphone for 'Hey Jarvis' or 'Jarvis',
    provides acoustic chime feedback, and supports acoustic barge-in.
    """

    WAKE_WORDS = ["hey jarvis", "okay jarvis", "ok jarvis", "jarvis"]
    STOP_WORDS = ["jarvis stop", "stop talking", "be quiet", "silence", "shut up"]

    def __init__(self):
        self.is_monitoring = False
        self._thread: Optional[threading.Thread] = None
        self._recognizer = None
        self._microphone = None

    def _init_sr(self):
        if self._recognizer is None:
            try:
                import speech_recognition as sr
                self._recognizer = sr.Recognizer()
                self._recognizer.energy_threshold = 280
                self._recognizer.dynamic_energy_threshold = True
                self._recognizer.pause_threshold = 0.8
                self._microphone = sr.Microphone()
            except Exception:
                pass

    def listen(self, prompt: str = "Directive, sir: ") -> str:
        """Captures voice input via microphone with acoustic prompt."""
        self._init_sr()
        if self._recognizer and self._microphone:
            try:
                import speech_recognition as sr
                print(f"\n[Microphone Active] {prompt}")
                play_wake_chime()
                with self._microphone as source:
                    self._recognizer.adjust_for_ambient_noise(source, duration=0.4)
                    audio = self._recognizer.listen(source, timeout=6, phrase_time_limit=10)
                text = self._recognizer.recognize_google(audio)
                print(f"[Captured Voice]: {text}")
                play_ack_chime()
                return text
            except Exception:
                pass

        # Fallback to console input if mic times out or unavailable
        try:
            return input(prompt)
        except (EOFError, Exception):
            time.sleep(1)
            return ""

    def start_wake_word_daemon(self, callback: Callable[[str], None]):
        """Runs continuous background wake-word monitor for 'Hey Jarvis'."""
        if self.is_monitoring:
            return
        self.is_monitoring = True
        self._init_sr()

        def _monitor_loop():
            print("[Auditory Sentinel]: Background wake-word detection active ('Hey Jarvis')...")
            while self.is_monitoring:
                if not self._recognizer or not self._microphone:
                    time.sleep(2)
                    continue
                try:
                    import speech_recognition as sr
                    with self._microphone as source:
                        self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                        audio = self._recognizer.listen(source, timeout=4, phrase_time_limit=8)

                    # Recognize audio phrase
                    phrase = self._recognizer.recognize_google(audio).lower().strip()

                    # Check for Barge-In Stop Directive
                    if any(s in phrase for s in self.STOP_WORDS):
                        stop_speaking()
                        continue

                    # Check for Wake Word
                    for w in self.WAKE_WORDS:
                        if w in phrase:
                            play_wake_chime()
                            # Extract command if spoken in same breath (e.g. "Hey Jarvis, what is my schedule?")
                            cmd = re.sub(rf"^.*?\b{w}\b[,\s]*", "", phrase).strip()
                            if cmd:
                                play_ack_chime()
                                callback(cmd)
                            else:
                                # Prompt user for directive
                                play_wake_chime()
                                with self._microphone as sub_source:
                                    sub_audio = self._recognizer.listen(sub_source, timeout=5, phrase_time_limit=8)
                                sub_cmd = self._recognizer.recognize_google(sub_audio)
                                play_ack_chime()
                                callback(sub_cmd)
                            break
                except Exception:
                    time.sleep(0.3)

        self._thread = threading.Thread(target=_monitor_loop, daemon=True)
        self._thread.start()

    def stop_wake_word_daemon(self):
        self.is_monitoring = False

# Global singleton
listener = VoiceListener()
