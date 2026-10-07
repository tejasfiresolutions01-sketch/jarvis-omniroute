import threading
import winsound

def play_boot_chime():
    """Plays Stark boot-up chord progression (low to high harmonics)."""
    def _play():
        try:
            winsound.Beep(523, 100) # C5
            winsound.Beep(659, 100) # E5
            winsound.Beep(784, 150) # G5
            winsound.Beep(1046, 250) # C6
        except Exception:
            pass
    threading.Thread(target=_play, daemon=True).start()

def play_wake_chime():
    """Plays double-tone prompt indicating J.A.R.V.I.S. is listening."""
    def _play():
        try:
            winsound.Beep(880, 80)  # A5
            winsound.Beep(1320, 120) # E6
        except Exception:
            pass
    threading.Thread(target=_play, daemon=True).start()

def play_ack_chime():
    """Plays subtle acknowledgement frequency."""
    def _play():
        try:
            winsound.Beep(987, 80) # B5
            winsound.Beep(1318, 100) # E6
        except Exception:
            pass
    threading.Thread(target=_play, daemon=True).start()
