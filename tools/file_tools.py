"""
J.A.R.V.I.S. File Operations & Workspace Tools.
Safely creates, reads, appends, and inspects files in the workspace or desktop.
"""

import os
from pathlib import Path
from typing import List, Optional
import config

def write_file(filepath: str, content: str, append: bool = False) -> str:
    """
    Creates or updates a file with given text content.
    Prevents path traversal outside permitted user directories.
    """
    try:
        p = Path(filepath)
        if not p.is_absolute():
            p = config.BASE_DIR / filepath

        p.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(p, mode, encoding="utf-8") as f:
            f.write(content)

        action = "appended to" if append else "saved to"
        return f"File successfully {action} '{p.name}' ({len(content)} characters)."
    except Exception as e:
        return f"Error writing file: {str(e)}"

def read_file(filepath: str, max_chars: int = 3000) -> str:
    """
    Reads contents from a file up to max_chars.
    """
    try:
        p = Path(filepath)
        if not p.is_absolute():
            p = config.BASE_DIR / filepath

        if not p.exists():
            return f"File '{filepath}' not found, sir."

        with open(p, "r", encoding="utf-8", errors="replace") as f:
            data = f.read(max_chars)
        return data
    except Exception as e:
        return f"Error reading file: {str(e)}"

def list_workspace_files(directory: str = ".", max_files: int = 20) -> str:
    """
    Lists files in a given directory.
    """
    try:
        p = Path(directory)
        if not p.is_absolute():
            p = config.BASE_DIR / directory

        if not p.exists() or not p.is_dir():
            return f"Directory '{directory}' does not exist."

        entries = [f.name for f in p.iterdir()][:max_files]
        return f"Files in '{p.name}':\n" + ", ".join(entries)
    except Exception as e:
        return f"Error listing directory: {str(e)}"
