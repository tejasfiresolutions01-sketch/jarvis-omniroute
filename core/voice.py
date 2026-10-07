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
    with _speak_lock:
        is_speaking = True
        # 1. Try edge-tts (High Fidelity British Butler)
        try:
            import edge_tts
            import pygame

            async def _synthesize():
                communicate = edge_tts.Communicate(
                    text=text,
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
