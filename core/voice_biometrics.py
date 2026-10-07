"""
J.A.R.V.I.S. Biometric Voice Verification & Frequency Analysis Engine.
Handles dual-spectrum acoustic profiling:
- Analyzes low-frequency fundamental chest resonance (65 Hz - 180 Hz)
- Analyzes high-frequency harmonic formants, fricatives, and elevated pitch (180 Hz - 7500 Hz)
- Provides speaker authentication so J.A.R.V.I.S. only responds to the authorized owner.
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import config

PROFILE_PATH = config.MEMORY_DIR / "voice_profile.json"

class VoiceBiometrics:
    """
    Biometric Speaker Verification across both low and high voice frequencies.
    """

    def __init__(self, profile_path: Path = PROFILE_PATH):
        self.profile_path = profile_path
        self.profile: Dict[str, Any] = self._load_profile()
        # By default, voice verification is active; auto-learns if uncalibrated
        self.enabled = os.getenv("VOICE_VERIFICATION_ENABLED", "true").lower() in ("true", "1", "yes")
        self.tolerance = float(os.getenv("VOICE_PROFILE_TOLERANCE", "0.65"))

    def _default_profile(self) -> Dict[str, Any]:
        return {
            "enrolled": False,
            "speaker_name": config.USER_NAME,
            "sample_count": 0,
            # Dual frequency spectrum envelope:
            # Low register: 65 Hz - 180 Hz (chest resonance, calm speech)
            # High register: 180 Hz - 450 Hz (pitch elevation, inflections)
            "f0_low_min": 65.0,
            "f0_low_max": 180.0,
            "f0_high_min": 180.0,
            "f0_high_max": 480.0,
            "avg_f0": 140.0,
            "spectral_centroid_min": 500.0,
            "spectral_centroid_max": 3800.0,
            "avg_spectral_centroid": 1750.0,
            "low_energy_ratio": 0.35,   # Energy in 60-350 Hz
            "mid_energy_ratio": 0.45,   # Energy in 350-2500 Hz
            "high_energy_ratio": 0.20,  # Energy in 2500-7500 Hz
        }

    def _load_profile(self) -> Dict[str, Any]:
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    base = self._default_profile()
                    base.update(data)
                    return base
            except Exception:
                pass
        return self._default_profile()

    def save_profile(self):
        try:
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, indent=2)
        except Exception as e:
            print(f"[Voice Biometrics Error]: Unable to save profile: {e}")

    def extract_features(self, pcm_bytes: bytes, sample_rate: int = 16000) -> Optional[Dict[str, float]]:
        """
        Extracts pitch (F0 across low & high bands), spectral centroid,
        and multi-band energy distribution from raw 16-bit PCM mono audio.
        """
        if not pcm_bytes or len(pcm_bytes) < 1600: # Need at least 50-100ms
            return None

        # Convert to float numpy array normalized between -1.0 and 1.0
        audio = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        # Remove DC offset
        audio = audio - np.mean(audio)

        # Apply pre-emphasis filter to boost high frequency sibilants & harmonics
        audio_preemph = np.append(audio[0], audio[1:] - 0.95 * audio[:-1])

        # 1. Fundamental Frequency (F0) Estimation via Normalized Autocorrelation
        # Searching between 65 Hz (deep bass) and 500 Hz (high register)
        min_lag = int(sample_rate / 500.0)
        max_lag = int(sample_rate / 65.0)

        # Autocorrelation
        corr = np.correlate(audio, audio, mode='full')
        corr = corr[len(corr)//2:]

        f0 = None
        if len(corr) > max_lag:
            window = corr[min_lag:max_lag]
            if len(window) > 0 and np.max(window) > 0:
                peak_idx = np.argmax(window) + min_lag
                peak_val = corr[peak_idx]
                if peak_val > 0.15 * corr[0]: # Voiced speech threshold
                    f0 = float(sample_rate / peak_idx)

        # 2. FFT Spectral Analysis
        fft_data = np.abs(np.fft.rfft(audio_preemph))
        freqs = np.fft.rfftfreq(len(audio_preemph), 1.0 / sample_rate)

        total_energy = np.sum(fft_data ** 2)
        if total_energy <= 1e-9:
            return None

        # Spectral Centroid (frequency center of mass)
        spectral_centroid = float(np.sum(freqs * fft_data) / (np.sum(fft_data) + 1e-9))

        # Band Energy Ratios (Low, Mid, High)
        low_band = (freqs >= 60) & (freqs <= 350)
        mid_band = (freqs > 350) & (freqs <= 2500)
        high_band = (freqs > 2500) & (freqs <= 7500)

        low_energy = np.sum(fft_data[low_band] ** 2) / total_energy
        mid_energy = np.sum(fft_data[mid_band] ** 2) / total_energy
        high_energy = np.sum(fft_data[high_band] ** 2) / total_energy

        return {
            "f0": f0,
            "spectral_centroid": spectral_centroid,
            "low_energy_ratio": float(low_energy),
            "mid_energy_ratio": float(mid_energy),
            "high_energy_ratio": float(high_energy),
            "rms_energy": float(np.sqrt(np.mean(audio ** 2)))
        }

    def calibrate(self, pcm_bytes: bytes, sample_rate: int = 16000) -> bool:
        """
        Calibrates/enrolls the user's voice, adapting to both low chest voice
        and high pitch registers.
        """
        feats = self.extract_features(pcm_bytes, sample_rate)
        if not feats or feats["rms_energy"] < 0.01:
            return False

        count = self.profile.get("sample_count", 0)

        # Update F0 bounds
        f0 = feats.get("f0")
        if f0:
            if not self.profile.get("enrolled"):
                self.profile["f0_low_min"] = max(55.0, min(self.profile["f0_low_min"], f0 * 0.75))
                self.profile["f0_high_max"] = min(600.0, max(self.profile["f0_high_max"], f0 * 1.35))
                self.profile["avg_f0"] = f0
            else:
                self.profile["f0_low_min"] = min(self.profile["f0_low_min"], max(55.0, f0 * 0.8))
                self.profile["f0_high_max"] = max(self.profile["f0_high_max"], min(600.0, f0 * 1.25))
                self.profile["avg_f0"] = (self.profile["avg_f0"] * count + f0) / (count + 1)

        # Update spectral centroid & band energies
        sc = feats["spectral_centroid"]
        self.profile["spectral_centroid_min"] = min(self.profile["spectral_centroid_min"], sc * 0.75)
        self.profile["spectral_centroid_max"] = max(self.profile["spectral_centroid_max"], sc * 1.3)
        self.profile["avg_spectral_centroid"] = (self.profile["avg_spectral_centroid"] * count + sc) / (count + 1)

        # Moving average of band energies
        self.profile["low_energy_ratio"] = (self.profile["low_energy_ratio"] * count + feats["low_energy_ratio"]) / (count + 1)
        self.profile["mid_energy_ratio"] = (self.profile["mid_energy_ratio"] * count + feats["mid_energy_ratio"]) / (count + 1)
        self.profile["high_energy_ratio"] = (self.profile["high_energy_ratio"] * count + feats["high_energy_ratio"]) / (count + 1)

        self.profile["sample_count"] = count + 1
        self.profile["enrolled"] = True
        self.save_profile()
        return True

    def verify_speaker(self, pcm_bytes: bytes, sample_rate: int = 16000) -> Tuple[bool, float, str]:
        """
        Verifies if incoming speech belongs to the enrolled user.
        Accepts speech across both low frequency (bass/chest) and high frequency (treble/inflections).
        Returns: (is_authorized, confidence_score, explanation)
        """
        if not self.enabled:
            return True, 1.0, "Voice verification disabled."

        # If uncalibrated, automatically calibrate and enroll first interactions
        if not self.profile.get("enrolled") or self.profile.get("sample_count", 0) < 2:
            success = self.calibrate(pcm_bytes, sample_rate)
            return True, 0.95, "Voice profile auto-calibrated for owner."

        feats = self.extract_features(pcm_bytes, sample_rate)
        if not feats:
            # If silence or unvoiced whispering, permit standard speech recognition
            return True, 0.70, "Unvoiced whisper or low amplitude; passing to recognizer."

        # Compute match score across acoustic properties
        scores = []

        # 1. Frequency (F0) Match: Accepts either low register or high register
        f0 = feats.get("f0")
        if f0 is not None:
            # Check if within low register (e.g. 65 - 180 Hz) or high register (e.g. 180 - 480 Hz)
            in_low = self.profile["f0_low_min"] <= f0 <= self.profile["f0_low_max"]
            in_high = self.profile["f0_high_min"] <= f0 <= self.profile["f0_high_max"]
            in_overall = self.profile["f0_low_min"] <= f0 <= self.profile["f0_high_max"]

            if in_low or in_high or in_overall:
                scores.append(1.0)
            else:
                # Margin calculation
                dist = min(abs(f0 - self.profile["f0_low_min"]), abs(f0 - self.profile["f0_high_max"]))
                penalty = max(0.0, 1.0 - (dist / 120.0))
                scores.append(penalty)

        # 2. Spectral Centroid Match
        sc = feats["spectral_centroid"]
        sc_min = self.profile["spectral_centroid_min"]
        sc_max = self.profile["spectral_centroid_max"]
        if sc_min <= sc <= sc_max:
            scores.append(1.0)
        else:
            sc_dist = min(abs(sc - sc_min), abs(sc - sc_max))
            scores.append(max(0.2, 1.0 - (sc_dist / 2000.0)))

        # 3. Energy Distribution Match (Low vs Mid vs High)
        energy_diff = (
            abs(feats["low_energy_ratio"] - self.profile["low_energy_ratio"]) +
            abs(feats["mid_energy_ratio"] - self.profile["mid_energy_ratio"]) +
            abs(feats["high_energy_ratio"] - self.profile["high_energy_ratio"])
        )
        energy_score = max(0.1, 1.0 - (energy_diff / 1.5))
        scores.append(energy_score)

        if not scores:
            return True, 0.70, "Insufficient harmonic markers; permitted."

        confidence = float(np.mean(scores))
        is_authorized = confidence >= self.tolerance

        if is_authorized:
            # Adaptively update user profile with successful matches
            self.calibrate(pcm_bytes, sample_rate)
            return True, confidence, f"Authorized speaker verified ({confidence*100:.1f}% confidence across low/high spectrum)."
        else:
            return False, confidence, f"Voice profile mismatch ({confidence*100:.1f}% confidence below threshold {self.tolerance*100:.1f}%)."

# Global singleton
voice_biometrics = VoiceBiometrics()
