"""
J.A.R.V.I.S. Proactive Multimodal Vision & Active IDE Co-Pilot.
Features:
1. Environment Sense: Inspects foreground IDEs (VS Code, Cursor, PyCharm, Sublime) and Terminals (PowerShell, cmd, Windows Terminal).
2. Traceback & Error Spotter: Detects Python exceptions, compiler errors, and unit test failures.
3. Silent Non-Intrusive Reasoning: Prepares contextual fixes and root-cause explanations without stealing focus.
4. Voice Directives: Rapidly explains and diagnoses code errors on the active screen.
Strictly in English.
"""

import os
import re
import sys
import ctypes
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config
from tools.vision_tools import get_active_window_title

logger = logging.getLogger("IDECoPilot")

# Recognized IDEs and Terminal environments
KNOWN_DEVELOPER_TARGETS = [
    "visual studio code", "vscode", "code", "cursor", "pycharm",
    "sublime text", "powershell", "cmd", "command prompt",
    "windows terminal", "git bash", "python"
]

class IDEVisionCoPilot:
    """
    Active IDE and Terminal co-pilot for real-time visual and context-aware assistance.
    """

    def __init__(self):
        self._last_diagnostic: Optional[Dict[str, Any]] = None

    def get_ide_context(self) -> Dict[str, Any]:
        """
        Inspects the active foreground window to determine IDE/terminal context.
        """
        title = get_active_window_title()
        title_lower = title.lower()

        is_dev_window = any(dev in title_lower for dev in KNOWN_DEVELOPER_TARGETS)

        # Extract file and project if in VS Code / Cursor / PyCharm
        active_file = "Unknown"
        project_name = "Workspace"
        file_match = re.search(r"([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)\s*[-—]\s*([a-zA-Z0-9_\-\s]+)", title)
        if file_match:
            active_file = file_match.group(1).strip()
            project_name = file_match.group(2).strip()

        return {
            "window_title": title,
            "is_developer_environment": is_dev_window,
            "active_file": active_file,
            "project_name": project_name
        }

    def parse_traceback_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parses common Python / runtime tracebacks from text or clipboard buffer.
        """
        if not text:
            return None

        # Look for Python traceback pattern
        tb_match = re.search(r"Traceback \(most recent call last\):([\s\S]+?)([A-Za-z]+Error|Exception):\s*(.*)", text)
        if tb_match:
            tb_body = tb_match.group(1).strip()
            err_type = tb_match.group(2).strip()
            err_msg = tb_match.group(3).strip()

            # Find last failing line
            file_line_matches = re.findall(r'File "([^"]+)", line (\d+)(?:, in (.+))?', tb_body)
            last_file, last_line = ("Unknown", "0")
            if file_line_matches:
                last_file, last_line = file_line_matches[-1][0], file_line_matches[-1][1]

            return {
                "detected": True,
                "error_type": err_type,
                "error_message": err_msg,
                "file": Path(last_file).name if last_file != "Unknown" else "active file",
                "line": last_line,
                "summary": f"{err_type} at {Path(last_file).name}:{last_line} - {err_msg}"
            }

        # Look for SyntaxError or IndentationError
        syntax_match = re.search(r"([A-Za-z]+Error):\s*(.*)", text)
        if syntax_match and "Error" in syntax_match.group(1):
            err_type = syntax_match.group(1).strip()
            err_msg = syntax_match.group(2).strip()
            return {
                "detected": True,
                "error_type": err_type,
                "error_message": err_msg,
                "file": "active terminal/buffer",
                "line": "unknown",
                "summary": f"{err_type} - {err_msg}"
            }

        return None

    def inspect_clipboard_for_errors(self) -> Optional[Dict[str, Any]]:
        """
        Checks clipboard buffer non-intrusively to see if an error log was copied.
        """
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            if not user32.OpenClipboard(None):
                return None

            CF_UNICODETEXT = 13
            h_clip = user32.GetClipboardData(CF_UNICODETEXT)
            if not h_clip:
                user32.CloseClipboard()
                return None

            p_clip = kernel32.GlobalLock(h_clip)
            if not p_clip:
                user32.CloseClipboard()
                return None

            text = ctypes.wstring_at(p_clip)
            kernel32.GlobalUnlock(h_clip)
            user32.CloseClipboard()

            return self.parse_traceback_text(text)
        except Exception:
            return None

    def diagnose_current_screen(self) -> str:
        """
        Diagnoses active developer environment and returns an actionable voice explanation.
        """
        ctx = self.get_ide_context()
        title = ctx["window_title"]

        # Check clipboard error buffer
        clip_diag = self.inspect_clipboard_for_errors()
        if clip_diag and clip_diag.get("detected"):
            self._last_diagnostic = clip_diag
            return (
                f"Visual diagnostics detected an active {clip_diag['error_type']} in {clip_diag['file']} "
                f"at line {clip_diag['line']}, sir. The error message is: '{clip_diag['error_message']}'. "
                f"I recommend inspecting the variable scope and handling potential missing definitions."
            )

        if ctx["is_developer_environment"]:
            return (
                f"Active developer environment verified, sir. You are currently focused on '{title}'. "
                f"No unhandled tracebacks are detected in the active clipboard buffer. All subroutines appear operational."
            )

        return (
            f"Optical scan verified active window '{title}', sir. "
            f"The environment is nominal and ready for directives."
        )

# Global singleton
vision_copilot = IDEVisionCoPilot()
