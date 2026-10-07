"""
J.A.R.V.I.S. Context-Aware Screen Reader & Optical Intelligence.
Uses Windows Native WinRT OCR and Win32 Window Inspection to read and analyze
on-screen text, active windows, code snippets, and error dialogs without external API cost.
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import psutil
from PIL import Image, ImageGrab

try:
    import win32gui
    import win32process
    HAS_WIN32 = True
except Exception:
    HAS_WIN32 = False

try:
    import mss
    HAS_MSS = True
except Exception:
    HAS_MSS = False

import config
from core.online_intelligence import online_intelligence

class ScreenReader:
    """
    Stark Optical Screen Reading & OCR Sentinel.
    Extracts text from active foreground windows or the full desktop,
    enabling vision-augmented reasoning, code explanations, and error inspection.
    """

    def __init__(self):
        self.temp_dir = config.BASE_DIR / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.ocr_script = Path(__file__).parent / "winrt_ocr.ps1"

    def get_active_window_info(self) -> Dict[str, Any]:
        """Returns metadata about the active foreground window."""
        info = {
            "title": "Desktop",
            "process": "unknown",
            "pid": 0,
            "rect": (0, 0, 1920, 1080),
            "width": 1920,
            "height": 1080
        }
        if not HAS_WIN32:
            return info

        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return info

            title = win32gui.GetWindowText(hwnd).strip()
            if title:
                info["title"] = title

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            info["pid"] = pid
            try:
                proc = psutil.Process(pid)
                info["process"] = proc.name()
            except Exception:
                pass

            rect = win32gui.GetWindowRect(hwnd) # (left, top, right, bottom)
            info["rect"] = rect
            w = max(0, rect[2] - rect[0])
            h = max(0, rect[3] - rect[1])
            info["width"] = w
            info["height"] = h
        except Exception:
            pass

        return info

    def capture_fullscreen(self, save_path: Optional[Path] = None) -> Path:
        """Captures full display screen snapshot."""
        target = save_path or (self.temp_dir / "screen_capture.png")

        if HAS_MSS:
            try:
                with mss.mss() as sct:
                    monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    img.save(target)
                    return target
            except Exception:
                pass

        img = ImageGrab.grab()
        img.save(target)
        return target

    def capture_active_window(self, save_path: Optional[Path] = None) -> Path:
        """Captures only the active foreground window boundary."""
        target = save_path or (self.temp_dir / "window_capture.png")
        info = self.get_active_window_info()
        rect = info["rect"]

        # If window dimensions are reasonable, crop
        if rect and info["width"] > 100 and info["height"] > 100:
            try:
                full = self.capture_fullscreen()
                img = Image.open(full)
                # Crop to window rectangle
                cropped = img.crop(rect)
                cropped.save(target)
                return target
            except Exception:
                pass

        # Fallback to full screen
        return self.capture_fullscreen(target)

    def extract_text_ocr(self, image_path: Path) -> str:
        """
        Executes Windows WinRT OCR on an image file.
        Operates 100% locally with zero cloud API keys or external costs.
        """
        if not image_path.exists():
            return ""

        if not self.ocr_script.exists():
            return ""

        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", str(self.ocr_script),
                "-ImagePath", str(image_path)
            ]
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=12,
                encoding="utf-8",
                errors="replace"
            )
            raw_text = res.stdout.strip() if res.returncode == 0 else ""
            return raw_text
        except Exception:
            return ""

    def read_screen_text(self) -> str:
        """Captures full screen and extracts all legible text via OCR."""
        shot = self.capture_fullscreen()
        return self.extract_text_ocr(shot)

    def read_active_window_text(self) -> str:
        """Captures foreground window and extracts all legible text via OCR."""
        shot = self.capture_active_window()
        return self.extract_text_ocr(shot)

    def analyze_screen(self, query: str = "Explain what is visible on my screen") -> str:
        """
        Optical reasoning analysis of active screen or window.
        Extracts foreground text and context, then synthesizes an articulate response.
        """
        info = self.get_active_window_info()
        win_title = info["title"]
        proc_name = info["process"]

        # 1. First attempt OCR on active window
        ocr_text = self.read_active_window_text()
        if not ocr_text or len(ocr_text.strip()) < 20:
            # Fall back to full screen OCR if active window text is sparse
            ocr_text = self.read_screen_text()

        context = (
            f"Active Foreground Window: '{win_title}'\n"
            f"Process: {proc_name} (PID: {info['pid']})\n"
            f"Screen Resolution: {info['width']}x{info['height']}\n"
            f"Extracted Screen Text (OCR):\n"
            f"---\n"
            f"{ocr_text[:3500] if ocr_text else '[No legible text detected on screen]'}\n"
            f"---"
        )

        # 2. Online reasoning query via OmniRoute
        if online_intelligence.is_online_available():
            prompt = (
                f"The user is asking: '{query}'\n\n"
                f"Context from their current screen:\n{context}\n\n"
                f"Answer concisely as J.A.R.V.I.S., Tony Stark's British butler. "
                f"Address user as sir. Highlight key details, code, or errors directly."
            )
            resp = online_intelligence.query(prompt=prompt)
            if resp:
                return resp

        # 3. Local offline butler analysis fallback
        if not ocr_text or not ocr_text.strip():
            return (
                f"Optical scan of the active display shows foreground application '{proc_name}' "
                f"('{win_title}'), sir, though no legible text elements could be resolved."
            )

        # Detect stack traces, errors, or code
        preview = " ".join(ocr_text.split()[:45])
        lower_ocr = ocr_text.lower()
        if any(err in lower_ocr for err in ["traceback", "error", "exception", "failed", "fatal"]):
            return (
                f"Optical inspection indicates an error or diagnostic alert in '{proc_name}' ('{win_title}'), sir. "
                f"The display presents: \"{preview}...\""
            )

        return (
            f"Optical inspection of '{win_title}' ({proc_name}) reveals the following content, sir: "
            f"\"{preview}...\""
        )

# Global singleton
screen_reader = ScreenReader()
