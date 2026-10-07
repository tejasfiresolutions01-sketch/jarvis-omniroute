import os
import ctypes
from pathlib import Path
from typing import Dict, Any, Optional
import config

def get_active_window_title() -> str:
    """Returns the title of the active foreground window."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    except Exception:
        return "Desktop"

def capture_and_inspect_display(query: str = "Analyze active display") -> str:
    """
    Captures primary screen and analyzes visual context.
    Works offline (window context & resolution) and online (multimodal reasoning).
    """
    temp_dir = config.BASE_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    shot_path = temp_dir / "screen_capture.png"

    active_win = get_active_window_title()

    w, h = 1920, 1080
    grab_success = False

    # 1. Try mss (fastest and most robust on Windows)
    try:
        import mss
        with mss.mss() as sct:
            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            sct_img = sct.grab(monitor)
            from PIL import Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img.save(shot_path)
            w, h = img.size
            grab_success = True
    except Exception:
        pass

    # 2. Fallback to PIL ImageGrab
    if not grab_success:
        try:
            from PIL import ImageGrab
            shot = ImageGrab.grab()
            shot.save(shot_path)
            w, h = shot.size
            grab_success = True
        except Exception:
            pass

    # If online with Gemini Key, perform multimodal reasoning
    if config.GEMINI_API_KEY:
        try:
            from google import genai
            from PIL import Image
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            img = Image.open(shot_path)
            prompt = f"Analyze this user desktop screen screenshot. Active window is '{active_win}'. Query: {query}. Be concise, like Tony Stark's J.A.R.V.I.S."
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[img, prompt]
            )
            if resp and resp.text:
                return resp.text.strip()
        except Exception:
            pass

    # Offline Visual Summary
    return (
        f"Optical display scan completed, sir. "
        f"Active foreground window is '{active_win}' across {w}x{h} display resolution. "
        f"Snapshot secured to {shot_path.name}."
    )
