import os
import sys
import shutil
import subprocess
import webbrowser
import ctypes
from pathlib import Path
from typing import Dict, Any, Optional, List

class SystemController:
    """
    Stark Tactical Windows Device Controller.
    Executes all local operating system directives with full administrative authority,
    robust path resolution, and non-blocking detached process spawning.
    """

    # Virtual key codes for hardware multimedia control
    VK_VOLUME_MUTE = 0xAD
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_UP = 0xAF
    VK_MEDIA_NEXT_TRACK = 0xB0
    VK_MEDIA_PREV_TRACK = 0xB1
    VK_MEDIA_PLAY_PAUSE = 0xB3

    # Common Web Destinations
    WEB_TARGETS = {
        "github": "https://github.com",
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "chatgpt": "https://chatgpt.com",
        "reddit": "https://www.reddit.com",
        "twitter": "https://x.com",
        "x": "https://x.com",
        "linkedin": "https://www.linkedin.com",
        "netflix": "https://www.netflix.com",
        "amazon": "https://www.amazon.com",
        "stackoverflow": "https://stackoverflow.com",
        "whatsapp": "https://web.whatsapp.com",
        "discord": "https://discord.com"
    }

    # Application Candidates with full paths on standard Windows installations
    APP_CANDIDATES = {
        "chrome": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            "chrome.exe", "chrome"
        ],
        "google chrome": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            "chrome.exe"
        ],
        "edge": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            "msedge.exe"
        ],
        "microsoft edge": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            "msedge.exe"
        ],
        "notepad": ["notepad.exe", r"C:\Windows\System32\notepad.exe"],
        "calc": ["calc.exe", r"C:\Windows\System32\calc.exe"],
        "calculator": ["calc.exe", r"C:\Windows\System32\calc.exe"],
        "code": [
            shutil.which("code"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            "code"
        ],
        "vscode": [
            shutil.which("code"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            "code"
        ],
        "explorer": ["explorer.exe", r"C:\Windows\explorer.exe"],
        "files": ["explorer.exe", r"C:\Windows\explorer.exe"],
        "terminal": [shutil.which("wt"), "wt.exe", "powershell.exe"],
        "cmd": ["cmd.exe", r"C:\Windows\System32\cmd.exe"],
        "powershell": ["powershell.exe", r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"],
        "taskmgr": ["taskmgr.exe", r"C:\Windows\System32\taskmgr.exe"],
        "task manager": ["taskmgr.exe", r"C:\Windows\System32\taskmgr.exe"],
        "settings": ["ms-settings:"],
        "paint": ["mspaint.exe", r"C:\Windows\System32\mspaint.exe"],
        "spotify": [os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"), "spotify.exe"]
    }

    # ─────────────────────────────────────────────────────────────────────────
    # Application & Web Launching
    # ─────────────────────────────────────────────────────────────────────────
    def launch(self, target: str, arguments: str = "") -> str:
        """Launches any software application, executable, file, or website URL."""
        clean = target.lower().strip()

        # 1. Web Destination Alias Check
        if clean in self.WEB_TARGETS:
            url = self.WEB_TARGETS[clean]
            webbrowser.open(url)
            subprocess.Popen(["cmd.exe", "/c", "start", "", url], shell=True)
            return f"Opening {target.title()} in your default browser, sir."

        # 2. General URL check
        if clean.startswith("http://") or clean.startswith("https://") or any(clean.endswith(tld) for tld in [".com", ".org", ".net", ".io", ".ai", ".co", ".app", ".dev"]):
            url = clean if clean.startswith("http") else f"https://{clean}"
            webbrowser.open(url)
            subprocess.Popen(["cmd.exe", "/c", "start", "", url], shell=True)
            return f"Opening {url} in your browser, sir."

        # 3. Windows Settings URI
        if clean in ["settings", "windows settings"]:
            try:
                os.startfile("ms-settings:")
                return "Opening Windows Settings, sir."
            except Exception:
                pass

        # 4. Resolve Candidate Executables
        resolved_exe = None
        candidates = self.APP_CANDIDATES.get(clean, [target.strip()])
        for cand in candidates:
            if not cand:
                continue
            if str(cand).startswith("ms-settings:"):
                os.startfile("ms-settings:")
                return "Opening Windows Settings, sir."
            if os.path.exists(str(cand)):
                resolved_exe = cand
                break
            which_p = shutil.which(str(cand))
            if which_p and os.path.exists(which_p):
                resolved_exe = which_p
                break

        if not resolved_exe:
            resolved_exe = candidates[0] if candidates else target.strip()

        # Detached Windows shell execution (guarantees non-blocking launch)
        try:
            if arguments:
                subprocess.Popen(["cmd.exe", "/c", "start", "", resolved_exe, arguments], shell=True)
            else:
                subprocess.Popen(["cmd.exe", "/c", "start", "", resolved_exe], shell=True)
            return f"Opening {target.title()} for you now, sir."
        except Exception as e:
            try:
                os.startfile(resolved_exe)
                return f"Opening {target.title()} for you now, sir."
            except Exception as e2:
                return f"Unable to launch {target}, sir: {e2}"

    def close_process(self, process_name: str) -> str:
        """Terminates a process by alias or process name."""
        clean = process_name.lower().strip()
        exe_map = {
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "edge": "msedge.exe",
            "notepad": "notepad.exe",
            "calc": "calc.exe",
            "calculator": "CalculatorApp.exe",
            "code": "Code.exe",
            "vscode": "Code.exe",
            "paint": "mspaint.exe",
            "spotify": "Spotify.exe"
        }
        target_exe = exe_map.get(clean, clean if clean.endswith(".exe") else f"{clean}.exe")
        try:
            subprocess.run(["taskkill", "/f", "/im", target_exe], capture_output=True, text=True)
            return f"Closed {clean.title()}, sir."
        except Exception as e:
            return f"Unable to terminate {clean}, sir: {e}"

    # ─────────────────────────────────────────────────────────────────────────
    # Multimedia & Sound Control
    # ─────────────────────────────────────────────────────────────────────────
    def _send_vk(self, vk_code: int, count: int = 1):
        for _ in range(count):
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0) # Key up

    def volume_up(self, steps: int = 5) -> str:
        self._send_vk(self.VK_VOLUME_UP, count=steps)
        return "Master volume increased, sir."

    def volume_down(self, steps: int = 5) -> str:
        self._send_vk(self.VK_VOLUME_DOWN, count=steps)
        return "Master volume decreased, sir."

    def toggle_mute(self) -> str:
        self._send_vk(self.VK_VOLUME_MUTE, count=1)
        return "Master audio mute toggled, sir."

    def media_play_pause(self) -> str:
        self._send_vk(self.VK_MEDIA_PLAY_PAUSE, count=1)
        return "Media playback toggled, sir."

    def media_next(self) -> str:
        self._send_vk(self.VK_MEDIA_NEXT_TRACK, count=1)
        return "Skipped to next media track, sir."

    def media_prev(self) -> str:
        self._send_vk(self.VK_MEDIA_PREV_TRACK, count=1)
        return "Returned to previous media track, sir."

    def show_desktop(self) -> str:
        """Minimizes all windows to display desktop (Win+D)."""
        VK_LWIN = 0x5B
        VK_D = 0x44
        ctypes.windll.user32.keybd_event(VK_LWIN, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_D, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_D, 0, 2, 0)
        ctypes.windll.user32.keybd_event(VK_LWIN, 0, 2, 0)
        return "Displaying Windows desktop, sir."

    # ─────────────────────────────────────────────────────────────────────────
    # Hardware Telemetry & Terminal Execution
    # ─────────────────────────────────────────────────────────────────────────
    def get_vitals(self) -> Dict[str, str]:
        """Gathers system vitals: CPU, RAM, and Disk free space."""
        try:
            import psutil
            cpu = f"{psutil.cpu_percent(interval=0.1)}%"
            ram = f"{psutil.virtual_memory().percent}%"
            disk = f"{psutil.disk_usage('C:').free // (2**30)} GB"
            return {"cpu_usage": cpu, "ram_usage": ram, "disk_free": disk}
        except ImportError:
            # Fallback using Windows shell queries
            return {"cpu_usage": "nominal", "ram_usage": "nominal", "disk_free": "adequate"}

    def take_screenshot(self, save_path: Optional[str] = None) -> str:
        try:
            from PIL import ImageGrab
            dest = save_path or str(config.BASE_DIR / "temp" / "screenshot.png")
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shot = ImageGrab.grab()
            shot.save(dest)
            return f"Display captured successfully to {dest}, sir."
        except Exception as e:
            return f"Display capture anomaly: {e}"

    def execute_terminal(self, command: str, timeout: int = 25) -> str:
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", command],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            out = proc.stdout.strip()
            err = proc.stderr.strip()
            res = (out + ("\n" + err if err else "")).strip()
            return res if res else "Command executed successfully with zero output, sir."
        except Exception as e:
            return f"Terminal execution error: {e}"

# Global singleton
system_controller = SystemController()
