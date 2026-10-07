"""
J.A.R.V.I.S. Adaptive System Display & Ambient Night Shield Controller.
Provides hardware backlight brightness adjustments (via WMI/CIM) and
hardware gamma ramp blue-light filtering (via Win32 GDI32) with zero external dependencies.
"""

import os
import subprocess
from datetime import datetime
from typing import Dict, Any, Tuple
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

class DisplayController:
    """
    Stark Optical Environmental Sentinel.
    Protects visual acuity during extended lab sessions via hardware backlight
    controls and real-time blue light gamma filtration.
    """

    def __init__(self):
        self.night_shield_enabled = False
        self.current_warmth = 1.0 # 1.0 = standard daylight, <1.0 = warm amber
        self.current_brightness = 100
        self._last_mode = "daylight"

    def _apply_gamma_ramp(self, r_scale: float = 1.0, g_scale: float = 1.0, b_scale: float = 1.0) -> bool:
        """Applies hardware RGB gamma ramp scaling via GDI32."""
        try:
            hdc = user32.GetDC(0)
            if not hdc:
                return False

            ramp_array = (wintypes.WORD * 256 * 3)()

            for i in range(256):
                # Standard linear mapping scaled to 16-bit WORD [0..65535]
                base_val = min(65535, max(0, int((i * 65535) / 255)))
                # Red channel (offset 0)
                ramp_array[0][i] = min(65535, max(0, int(base_val * r_scale)))
                # Green channel (offset 1)
                ramp_array[1][i] = min(65535, max(0, int(base_val * g_scale)))
                # Blue channel (offset 2)
                ramp_array[2][i] = min(65535, max(0, int(base_val * b_scale)))

            res = gdi32.SetDeviceGammaRamp(hdc, ctypes.byref(ramp_array))
            user32.ReleaseDC(0, hdc)
            return bool(res)
        except Exception:
            return False

    def enable_night_shield(self, warmth: float = 0.70) -> str:
        """
        Activates optical blue-light filtration with warm amber spectrum.
        warmth: 0.50 (very deep amber) to 0.90 (subtle warm).
        """
        warmth = max(0.40, min(0.95, float(warmth)))
        r_scale = 1.0
        g_scale = 0.85 + (0.15 * warmth)
        b_scale = warmth

        success = self._apply_gamma_ramp(r_scale, g_scale, b_scale)
        self.night_shield_enabled = True
        self.current_warmth = warmth
        self._last_mode = "night_shield"

        pct_filtered = int((1.0 - warmth) * 100)
        return (
            f"Night Shield engaged, sir. Blue light emissions attenuated by {pct_filtered}%. "
            f"Optical spectrum shifted to warm amber for retina protection."
        )

    def disable_night_shield(self) -> str:
        """Restores crisp 6500K standard daylight display spectrum."""
        self._apply_gamma_ramp(1.0, 1.0, 1.0)
        self.night_shield_enabled = False
        self.current_warmth = 1.0
        self._last_mode = "daylight"

        return "Night Shield disengaged, sir. Display calibrated back to standard 6500K daylight spectrum."

    def set_brightness(self, percent: int) -> str:
        """Sets hardware display brightness percentage (10% to 100%)."""
        clamped = max(10, min(100, int(percent)))
        self.current_brightness = clamped

        # 1. Attempt hardware WMI/CIM brightness
        wmi_success = False
        try:
            ps_cmd = (
                f"(Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightnessMethods "
                f"-ErrorAction SilentlyContinue).WmiSetBrightness(1, {clamped})"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                timeout=4
            )
            wmi_success = (res.returncode == 0)
        except Exception:
            wmi_success = False

        # 2. If WMI was unavailable, apply brightness via gamma ramp scaling
        if not wmi_success and not self.night_shield_enabled:
            scale = clamped / 100.0
            self._apply_gamma_ramp(scale, scale, scale)

        return f"Display brightness calibrated to {clamped}%, sir."

    def get_brightness(self) -> int:
        """Retrieves current hardware brightness level."""
        try:
            ps_cmd = "(Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightness -ErrorAction SilentlyContinue).CurrentBrightness"
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=4
            )
            if res.returncode == 0 and res.stdout.strip().isdigit():
                self.current_brightness = int(res.stdout.strip())
        except Exception:
            pass
        return self.current_brightness

    def apply_adaptive_ambient(self) -> str:
        """
        Automatically calibrates display warmth and brightness based on local time.
        - Late Night (22:00 - 06:00): Deep Night Shield (60% warmth, 50% brightness)
        - Evening (19:00 - 22:00): Moderate Night Shield (75% warmth, 75% brightness)
        - Daytime (06:00 - 19:00): Crisp Daylight (100% warmth, 100% brightness)
        """
        hour = datetime.now().hour

        if hour >= 22 or hour < 6:
            self.set_brightness(50)
            self.enable_night_shield(0.60)
            self._last_mode = "late_night"
            return (
                "Adaptive Night Protocol activated for late-night lab session, sir. "
                "Brightness set to 50% with deep amber Night Shield protection."
            )
        elif 19 <= hour < 22:
            self.set_brightness(75)
            self.enable_night_shield(0.75)
            self._last_mode = "evening"
            return (
                "Adaptive Evening Protocol activated, sir. "
                "Brightness balanced to 75% with moderate warm blue-light filtration."
            )
        else:
            self.set_brightness(100)
            self.disable_night_shield()
            self._last_mode = "daylight"
            return (
                "Adaptive Daylight Protocol engaged, sir. "
                "Brightness calibrated to 100% with full 6500K color fidelity."
            )

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive display telemetry."""
        return {
            "night_shield_enabled": self.night_shield_enabled,
            "warmth": self.current_warmth,
            "brightness": self.current_brightness,
            "mode": self._last_mode
        }

    def format_status_summary(self) -> str:
        """Formats articulate butler report of display settings."""
        shield_str = (
            f"Active (attenuated by {int((1.0 - self.current_warmth) * 100)}%)"
            if self.night_shield_enabled else "Disengaged"
        )
        return (
            f"Display telemetry, sir: Brightness is holding at {self.current_brightness}%, "
            f"Night Shield is {shield_str}, operating under '{self._last_mode}' profile."
        )

# Global singleton
display_controller = DisplayController()
