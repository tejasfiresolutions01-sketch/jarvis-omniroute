import os
import asyncio
import tempfile
import threading
from typing import Optional
from pathlib import Path
import config

_speak_lock = threading.Lock()
_current_process = None
is_speaking = False

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

import re

def clean_for_speech(text: str) -> str:
    """
    Transforms raw response text into natural, melodic human speech.
    Strips raw markdown, code blocks, bullet points, headers, and emojis.
    Expands tech abbreviations and units into smooth spoken British phonetics.
    """
    if not text:
        return ""

    s = text.strip()

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

def speak(text: str):
    """
    Synthesizes speech using British Butler persona asynchronously.
    Uses edge-tts (en-GB-RyanNeural) when online, with instant offline fallback
    to Windows native SAPI5 (pyttsx3) so voice always functions offline!
    Supports acoustic barge-in / interruption.
    """
    if not text or not text.strip():
        return

    clean_text = text.strip()
    threading.Thread(target=_speak_worker, args=(clean_text,), daemon=True).start()

def speak_sync(text: str):
    """Synchronous speech synthesis; blocks until playback completes or barged-in."""
    if not text or not text.strip():
        return
    _speak_worker(text.strip())

def _speak_worker(text: str):
    global is_speaking
    spoken_text = clean_for_speech(text)
    if not spoken_text:
        return

    with _speak_lock:
        is_speaking = True
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
            engine.say(text)
            engine.runAndWait()
            is_speaking = False
            return
        except Exception:
            pass

        # 3. Terminal fallback
        print(f"\n[J.A.R.V.I.S.]: {text}\n")
        is_speaking = False
