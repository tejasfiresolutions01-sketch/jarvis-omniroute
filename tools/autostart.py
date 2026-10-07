import os
import sys
import winreg
from pathlib import Path

# Ensure project root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config

REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "JARVIS_AI_ASSISTANT"

def enable_autostart() -> bool:
    """Configures J.A.R.V.I.S. to launch automatically on Windows boot."""
    try:
        run_bat = config.BASE_DIR / "run_jarvis.bat"
        cmd = f'"{run_bat}"'

        # 1. Windows Registry HKCU\Software\Microsoft\Windows\CurrentVersion\Run
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)

        # 2. Windows Startup Folder Shortcut
        startup_dir = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"))
        if startup_dir.exists():
            vbs_script = startup_dir / "jarvis_autostart.vbs"
            vbs_content = f'CreateObject("Wscript.Shell").Run """{run_bat}""", 0, False\n'
            vbs_script.write_text(vbs_content, encoding="utf-8")

        return True
    except Exception:
        return False

def is_autostart_enabled() -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return bool(val)
    except Exception:
        return False
