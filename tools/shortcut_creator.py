import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config

def create_desktop_shortcut() -> bool:
    """Creates desktop shortcut with Iron Man icon for J.A.R.V.I.S."""
    try:
        desktop_dir = Path(os.path.expandvars(r"%USERPROFILE%\Desktop"))
        shortcut_path = desktop_dir / "J.A.R.V.I.S..lnk"
        target_path = config.BASE_DIR / "run_jarvis.bat"
        icon_path = config.IRONMAN_ICO_PATH

        ps_script = f"""
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
$Shortcut.TargetPath = '{target_path}'
$Shortcut.WorkingDirectory = '{config.BASE_DIR}'
$Shortcut.Description = 'J.A.R.V.I.S. Artificial Intelligence System'
$Shortcut.IconLocation = '{icon_path},0'
$Shortcut.Save()
"""
        import subprocess
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
        return shortcut_path.exists()
    except Exception:
        return False

if __name__ == "__main__":
    success = create_desktop_shortcut()
    print("Desktop shortcut created:", success)
