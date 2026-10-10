"""
J.A.R.V.I.S. Stark Acoustic Core 2.0: Native Windows Audio Ducking & Affective Vocal Modulation.
Features:
1. Native Windows Core Audio Ducking via IAudioEndpointVolume COM Interface:
   - Temporarily ducks background system audio and media playback while J.A.R.V.I.S. speaks.
   - Restores original audio level upon completion with thread-safe reference counting.
2. Context-Aware Affective Vocal Modulation:
   - Dynamically modifies speech synthesis rate and pitch parameters to match emotional tone:
     ALERT (urgent/fast), CALM (measured/deep), TECHNICAL (precise/crisp), TRIUMPH (energetic).
3. 100% Free Plan, zero cloud dependency, native Win32/COM execution.
"""

import logging
import threading
from contextlib import contextmanager
from enum import Enum
from typing import Dict, Optional, Tuple

logger = logging.getLogger("AudioDucking")

# COM and Windows Types
HAS_COM = False
try:
    import comtypes
    from comtypes import GUID, IUnknown, COMMETHOD, HRESULT
    from ctypes import POINTER, c_bool, c_float, c_int
    from ctypes.wintypes import DWORD

    CLSID_MMDeviceEnumerator = GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}")

    class IAudioEndpointVolume(IUnknown):
        _iid_ = GUID("{5CDF2C82-841E-4546-9722-0CF74078229A}")
        _methods_ = [
            COMMETHOD([], HRESULT, "RegisterControlChangeNotify"),
            COMMETHOD([], HRESULT, "UnregisterControlChangeNotify"),
            COMMETHOD([], HRESULT, "GetChannelCount"),
            COMMETHOD([], HRESULT, "SetMasterVolumeLevel"),
            COMMETHOD([], HRESULT, "SetMasterVolumeLevelScalar", (["in"], c_float, "fLevel"), (["in"], POINTER(GUID), "pguidEventContext")),
            COMMETHOD([], HRESULT, "GetMasterVolumeLevel"),
            COMMETHOD([], HRESULT, "GetMasterVolumeLevelScalar", (["out"], POINTER(c_float), "pfLevel")),
            COMMETHOD([], HRESULT, "SetMute", (["in"], c_bool, "bMute"), (["in"], POINTER(GUID), "pguidEventContext")),
            COMMETHOD([], HRESULT, "GetMute", (["out"], POINTER(c_bool), "pbMute")),
        ]

    class IMMDevice(IUnknown):
        _iid_ = GUID("{D666063F-1587-4E43-81F1-B948E807363F}")
        _methods_ = [
            COMMETHOD([], HRESULT, "Activate", (["in"], POINTER(GUID), "iid"), (["in"], DWORD, "dwClsCtx"), (["in"], POINTER(c_int), "pActivationParams"), (["out"], POINTER(POINTER(IUnknown)), "ppInterface")),
        ]

    class IMMDeviceEnumerator(IUnknown):
        _iid_ = GUID("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
        _methods_ = [
            COMMETHOD([], HRESULT, "EnumAudioEndpoints"),
            COMMETHOD([], HRESULT, "GetDefaultAudioEndpoint", (["in"], c_int, "dataFlow"), (["in"], c_int, "role"), (["out"], POINTER(POINTER(IMMDevice)), "ppEndpoint")),
        ]

    HAS_COM = True
except Exception:
    HAS_COM = False


class AffectiveTone(Enum):
    DEFAULT = "default"
    ALERT = "alert"
    CALM = "calm"
    TECHNICAL = "technical"
    TRIUMPH = "triumph"


class AffectiveVocalModulator:
    """
    Computes context-adapted rate and pitch parameters for TTS speech synthesis.
    """

    TONE_PRESETS: Dict[AffectiveTone, Tuple[str, str]] = {
        AffectiveTone.DEFAULT: ("+0%", "+0Hz"),
        AffectiveTone.ALERT: ("+16%", "+6Hz"),
        AffectiveTone.CALM: ("-8%", "-3Hz"),
        AffectiveTone.TECHNICAL: ("+6%", "+0Hz"),
        AffectiveTone.TRIUMPH: ("+10%", "+8Hz"),
    }

    @classmethod
    def get_voice_params(cls, tone: AffectiveTone = AffectiveTone.DEFAULT, base_rate: str = "+0%", base_pitch: str = "+0Hz") -> Tuple[str, str]:
        """Calculates modulated rate and pitch based on affective context."""
        delta_rate, delta_pitch = cls.TONE_PRESETS.get(tone, ("+0%", "+0Hz"))
        if tone == AffectiveTone.DEFAULT:
            return base_rate, base_pitch
        return delta_rate, delta_pitch


class AudioDuckingEngine:
    """
    Native Windows Master Audio Ducking Controller with safe reentrant nesting.
    """

    def __init__(self, duck_factor: float = 0.28):
        self.duck_factor = duck_factor  # Lowers system volume to ~28% of original
        self._lock = threading.RLock()
        self._duck_count = 0
        self._saved_volume: Optional[float] = None
        self._endpoint_vol = None
        self._initialized = False

    def _get_volume_interface(self):
        if not HAS_COM:
            return None
        try:
            comtypes.CoInitialize()
            enumerator = comtypes.CoCreateInstance(
                CLSID_MMDeviceEnumerator,
                IMMDeviceEnumerator,
                comtypes.CLSCTX_INPROC_SERVER
            )
            endpoint = enumerator.GetDefaultAudioEndpoint(0, 1)  # eRender=0, eMultimedia=1
            vol_interface = endpoint.Activate(
                IAudioEndpointVolume._iid_,
                comtypes.CLSCTX_INPROC_SERVER,
                None
            )
            return vol_interface.QueryInterface(IAudioEndpointVolume)
        except Exception as e:
            logger.debug(f"Unable to access Windows MMDevice audio endpoint: {e}")
            return None

    def duck(self) -> bool:
        """Lowers system audio level for speech vocalization."""
        with self._lock:
            if self._duck_count == 0:
                vol_iface = self._get_volume_interface()
                if vol_iface is not None:
                    try:
                        current = vol_iface.GetMasterVolumeLevelScalar()
                        self._saved_volume = current
                        ducked_val = max(0.05, min(1.0, current * self.duck_factor))
                        vol_iface.SetMasterVolumeLevelScalar(ducked_val, None)
                        logger.debug(f"Audio ducked: {current:.2f} -> {ducked_val:.2f}")
                    except Exception as e:
                        logger.debug(f"Error applying audio duck: {e}")
            self._duck_count += 1
            return True

    def unduck(self) -> bool:
        """Restores original system audio level after speech vocalization."""
        with self._lock:
            if self._duck_count > 0:
                self._duck_count -= 1
                if self._duck_count == 0 and self._saved_volume is not None:
                    vol_iface = self._get_volume_interface()
                    if vol_iface is not None:
                        try:
                            vol_iface.SetMasterVolumeLevelScalar(self._saved_volume, None)
                            logger.debug(f"Audio restored to: {self._saved_volume:.2f}")
                        except Exception as e:
                            logger.debug(f"Error restoring audio: {e}")
                    self._saved_volume = None
            return True

    @contextmanager
    def ducked(self):
        """Context manager for scoped audio ducking during speech synthesis."""
        try:
            self.duck()
            yield
        finally:
            self.unduck()


# Global Singleton Instance
audio_ducking = AudioDuckingEngine()
