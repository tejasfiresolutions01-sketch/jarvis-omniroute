import os
import sys
import winreg
from pathlib import Path
import subprocess

# Ensure project root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config

def add_to_user_path() -> bool:
    """Adds J.A.R.V.I.S. installation directory to User PATH so 'jarvis' works anywhere."""
    try:
        install_dir = str(config.BASE_DIR)
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current_path = ""
        paths = [p for p in current_path.split(";") if p]
        if install_dir not in paths:
            paths.append(install_dir)
            new_path = ";".join(paths)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            # Broadcast environment update to Windows
            try:
                import ctypes
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                SMTO_ABORTIFHUNG = 0x0002
                ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", SMTO_ABORTIFHUNG, 5000, None
                )
            except Exception:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def create_desktop_shortcut() -> bool:
    """Creates Desktop & Start Menu shortcuts for J.A.R.V.I.S. Core & Voice Mode."""
    try:
        desktop_dir = Path(os.path.expandvars(r"%USERPROFILE%\Desktop"))
        start_menu_dir = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"))
        
        main_bat = config.BASE_DIR / "run_jarvis.bat"
        voice_bat = config.BASE_DIR / "run_jarvis_voice.bat"
        icon_path = config.IRONMAN_ICO_PATH

        shortcuts_to_create = [
            # Desktop Shortcuts
            (desktop_dir / "J.A.R.V.I.S..lnk", main_bat, "J.A.R.V.I.S. Holographic Tactical HUD"),
            (desktop_dir / "J.A.R.V.I.S. Voice Mode.lnk", voice_bat, "J.A.R.V.I.S. Hands-Free Voice Conversation Mode"),
            # Start Menu Shortcuts
            (start_menu_dir / "J.A.R.V.I.S..lnk", main_bat, "J.A.R.V.I.S. Artificial Intelligence System"),
            (start_menu_dir / "J.A.R.V.I.S. Voice Mode.lnk", voice_bat, "J.A.R.V.I.S. Voice Conversation Mode"),
        ]

        commands = []
        commands.append("$WshShell = New-Object -comObject WScript.Shell")
        for sc_path, target, desc in shortcuts_to_create:
            commands.append(f"""
$sc = $WshShell.CreateShortcut('{sc_path}')
$sc.TargetPath = '{target}'
$sc.WorkingDirectory = '{config.BASE_DIR}'
$sc.Description = '{desc}'
$sc.IconLocation = '{icon_path},0'
$sc.Save()
""")
        ps_script = "\n".join(commands)
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)

        # Also register in user PATH
        add_to_user_path()

        return (desktop_dir / "J.A.R.V.I.S..lnk").exists()
    except Exception:
        return False

if __name__ == "__main__":
    success = create_desktop_shortcut()
    print("Desktop & Start Menu shortcuts created:", success)
