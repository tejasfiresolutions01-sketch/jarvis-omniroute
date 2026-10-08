import os
import sys
import time
import queue
import re
import asyncio
import tempfile
import threading
from typing import Optional, Dict
from pathlib import Path
import config

_speak_lock = threading.Lock()
_current_process = None
is_speaking = False

# Deduplication and single-voice tracking
_recent_spoken: Dict[str, float] = {}
_DEDUP_WINDOW_SECONDS = 4.5
_last_spoken_text: str = ""
_speech_queue: queue.Queue = queue.Queue(maxsize=16)
_worker_running = False

def check_is_speaking() -> bool:
    """Returns True if J.A.R.V.I.S. is currently producing acoustic speech."""
    global is_speaking
    return is_speaking

def stop_speaking():
    """Acoustic Barge-in: immediately halts any in-progress vocalization."""
    global is_speaking
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass
    is_speaking = False

def is_recently_spoken(text: str, window: float = 6.0) -> bool:
    """
    Checks if given text matches anything recently vocalized by J.A.R.V.I.S.
    Used for acoustic echo cancellation to prevent microphone feedback loops.
    """
    global _last_spoken_text
    if not text or not text.strip():
        return False
    clean_q = re.sub(r"[^a-zA-Z0-9\s]", "", text.lower()).strip()
    if not clean_q:
        return False

    now = time.time()
    # Check exact normalized cache
    for phrase, ts in list(_recent_spoken.items()):
        if now - ts <= window:
            if clean_q in phrase or phrase in clean_q:
                return True
    return False

def clean_for_speech(text: str) -> str:
    """
    Transforms raw response text into natural, melodic human speech.
    Strips raw markdown, code blocks, bullet points, headers, and emojis.
    Expands tech abbreviations and units into smooth spoken British phonetics.
    """
    if not text:
        return ""

    s = text.strip()
    # Normalize unicode curly quotes and dashes
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("—", ", ").replace("–", ", ")

    # 1. Remove code blocks
    s = re.sub(r"```[\s\S]*?```", " I have executed the requested code block, sir. ", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)

    # 2. Remove markdown links [Label](url) -> Label
    s = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", s)

    # 3. Remove URLs
    s = re.sub(r"https?://\S+", "the link", s)

    # 4. Remove markdown headers, bold, italics, dividers
    s = re.sub(r"^#{1,6}\s*", "", s, flags=re.MULTILINE)
    s = re.sub(r"\*\*([^\*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^\*]+)\*", r"\1", s)
    s = re.sub(r"__([^_]+)__", r"\1", s)
    s = re.sub(r"~~([^~]+)~~", r"\1", s)
    s = re.sub(r"^[\-\*]\s+", "", s, flags=re.MULTILINE)
    s = re.sub(r"^\d+\.\s+", "", s, flags=re.MULTILINE)
    s = re.sub(r"[-─=]{3,}", "", s)

    # 5. Remove symbols, bullets, emojis, box characters
    s = re.sub(r"[◆▶►■●•★☆✔✖❌✓—–]", ", ", s)
    s = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27bf\u2b00-\u2bff\u2300-\u23ff\u200d\ufe0f]", "", s) # Emojis and dingbats

    # 6. Expand abbreviations and spoken measurements
    replacements = [
        (r"(?<=\d|\s)°C\b|°C", " degrees Celsius", 0),
        (r"(?<=\d|\s)°F\b|°F", " degrees Fahrenheit", 0),
        (r"(?<=\d|\s)(?:TB|tb)\b", " terabytes", 0),
        (r"(?<=\d|\s)(?:GB|gb)\b", " gigabytes", 0),
        (r"(?<=\d|\s)(?:MB|mb)\b", " megabytes", 0),
        (r"(?<=\d|\s)(?:KB|kb)\b", " kilobytes", 0),
        (r"(?<=\d|\s)(?:GHz|ghz)\b", " gigahertz", 0),
        (r"(?<=\d|\s)(?:MHz|mhz)\b", " megahertz", 0),
        (r"(?<=\d|\s)(?:kHz|khz)\b", " kilohertz", 0),
        (r"(?<=\d|\s)(?:km/h|kmph)\b", " kilometers per hour", re.IGNORECASE),
        (r"(?<=\d|\s)mph\b", " miles per hour", re.IGNORECASE),
        (r"%", " percent", 0),
        (r"\s*&\s*", " and ", 0),
        (r"\bCPU\b", "C P U", 0),
        (r"\bRAM\b", "R A M", 0),
        (r"\bGPU\b", "G P U", 0),
        (r"\bOS\b", "O S", 0),
        (r"\bAI\b", "A I", 0),
        (r"\bUI\b", "U I", 0),
        (r"\bAPI\b", "A P I", 0),
        (r"\bvs\.\b", "versus", re.IGNORECASE),
        (r"\be\.g\.\b", "for example", re.IGNORECASE),
        (r"\bi\.e\.\b", "that is", re.IGNORECASE),
        (r"\betc\.\b", "and so forth", re.IGNORECASE),
        (r"\bw/\b", "with", re.IGNORECASE),
        (r"\bw/o\b", "without", re.IGNORECASE),
    ]
    for pat, rep, flags in replacements:
        s = re.sub(pat, rep, s, flags=flags)

    # 7. Clean up whitespace and punctuation
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+([,\.!\?])", r"\1", s)
    s = re.sub(r",\s*,+", ",", s)

    return s

def _get_os_speech_lock() -> Optional[Any]:
    """Cross-process lock to guarantee only ONE process speaks across Windows."""
    try:
        lock_file = Path(config.BASE_DIR) / "logs" / "jarvis_speech.lock"
        lock_file.parent.mkdir(parents=True, exist_ok=True)
        f = open(lock_file, "a+")
        return f
    except Exception:
        return None

def _release_os_speech_lock(lock_handle):
    try:
        if lock_handle:
            lock_handle.close()
    except Exception:
        pass

def _process_speech_queue():
    """Single serialized speech worker ensuring exactly ONE voice speaks at any time."""
    global _worker_running
    while True:
        try:
            item = _speech_queue.get()
            if item is None:
                break
            text, sync_event = item
            _speak_worker(text)
            if sync_event:
                sync_event.set()
            _speech_queue.task_done()
        except Exception as e:
            time.sleep(0.1)

def _ensure_worker_started():
    global _worker_running
    with _speak_lock:
        if not _worker_running:
            _worker_running = True
            t = threading.Thread(target=_process_speech_queue, daemon=True, name="JarvisSingleVoiceWorker")
            t.start()

def speak(text: str):
    """
    Synthesizes speech using British Butler persona asynchronously.
    Enforces strict single-voice output:
    - Automatically deduplicates and suppresses repeated vocalizations within 4.5 seconds.
    - Serializes all speech into a single worker thread to prevent overlapping or 3x voices.
    - Supports acoustic barge-in / interruption.
    """
    if not text or not text.strip():
        return

    clean_text = text.strip()
    spoken_text = clean_for_speech(clean_text)
    if not spoken_text:
        return

    # 1. Deduplication Gate: reject identical phrases spoken within 4.5 seconds
    norm_key = re.sub(r"[^a-zA-Z0-9\s]", "", spoken_text.lower()).strip()
    now = time.time()
    
    with _speak_lock:
        # Prune old keys
        for k in list(_recent_spoken.keys()):
            if now - _recent_spoken[k] > 15.0:
                del _recent_spoken[k]

        if norm_key in _recent_spoken and (now - _recent_spoken[norm_key] < _DEDUP_WINDOW_SECONDS):
            return

        _recent_spoken[norm_key] = now

    # 2. If a new utterance arrives while previous is speaking, interrupt the old one
    if is_speaking:
        stop_speaking()

    # 3. Clear pending redundant items from queue
    while not _speech_queue.empty():
        try:
            _speech_queue.get_nowait()
            _speech_queue.task_done()
        except Exception:
            break

    _ensure_worker_started()
    try:
        _speech_queue.put_nowait((clean_text, None))
    except queue.Full:
        pass

def speak_sync(text: str):
    """Synchronous speech synthesis; blocks until playback completes or barged-in."""
    if not text or not text.strip():
        return

    clean_text = text.strip()
    spoken_text = clean_for_speech(clean_text)
    if not spoken_text:
        return

    norm_key = re.sub(r"[^a-zA-Z0-9\s]", "", spoken_text.lower()).strip()
    now = time.time()
    with _speak_lock:
        if norm_key in _recent_spoken and (now - _recent_spoken[norm_key] < _DEDUP_WINDOW_SECONDS):
            return
        _recent_spoken[norm_key] = now

    _speak_worker(clean_text)

def _speak_worker(text: str):
    global is_speaking, _last_spoken_text
    spoken_text = clean_for_speech(text)
    if not spoken_text:
        return

    lock_handle = _get_os_speech_lock()
    try:
        with _speak_lock:
            is_speaking = True
            _last_spoken_text = spoken_text

            # 1. Try edge-tts (High Fidelity British Butler)
            try:
                import edge_tts
                import pygame

                async def _synthesize():
                    communicate = edge_tts.Communicate(
                        text=spoken_text,
                        voice=config.TTS_VOICE,
                        rate=config.TTS_RATE,
                        pitch=config.TTS_PITCH
                    )
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                        temp_path = f.name
                    await communicate.save(temp_path)
                    return temp_path

                temp_audio = asyncio.run(_synthesize())

                # Play with pygame
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.music.load(temp_audio)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and is_speaking:
                    pygame.time.Clock().tick(10)
                pygame.mixer.music.unload()
                try:
                    os.remove(temp_audio)
                except Exception:
                    pass
                is_speaking = False
                return
            except Exception:
                pass

            # 2. Offline Fallback: Windows SAPI5 (pyttsx3)
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', 175)
                voices = engine.getProperty('voices')
                for v in voices:
                    if any(k in v.name.lower() for k in ["george", "uk", "british", "english"]):
                        engine.setProperty('voice', v.id)
                        break
                engine.say(spoken_text)
                engine.runAndWait()
                is_speaking = False
                return
            except Exception:
                pass

            # 3. Terminal fallback
            print(f"\n[J.A.R.V.I.S.]: {spoken_text}\n")
            is_speaking = False
    finally:
        is_speaking = False
        _release_os_speech_lock(lock_handle)
