import os
import sys
import ctypes
import argparse
import threading
from core.brain import brain
from core.voice import speak
from core.listener import listener
from core.learning_matrix import learning_matrix
from tools.autostart import enable_autostart
from tools.shortcut_creator import create_desktop_shortcut
from ui.web_portal import web_portal
import config

_singleton_mutex = None

def _attach_to_interactive_desktop():
    """Attaches current thread to interactive user desktop (Default) on Windows."""
    try:
        user32 = ctypes.windll.user32
        hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
    except Exception:
        pass

def ensure_single_instance() -> bool:
    """Guarantees only one J.A.R.V.I.S. process runs concurrently."""
    global _singleton_mutex
    _attach_to_interactive_desktop()
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    MUTEX_NAME = "Local\\JARVIS_ULTIMATE_MUTEX"
    _singleton_mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    ERROR_ALREADY_EXISTS = 183

    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        hwnd = user32.FindWindowW(None, config.HUD_WINDOW_TITLE)
        if hwnd:
            user32.ShowWindow(hwnd, 9) # SW_RESTORE
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            try:
                user32.SwitchToThisWindow(hwnd, True)
            except Exception:
                pass
            print("[Single Instance]: J.A.R.V.I.S. Tactical HUD is already active. Elevating display to foreground.")
            return False
        else:
            print("[Single Instance]: Background instance detected without active display. Initializing HUD display.")
            return True
    return True

def process_command(user_input: str) -> bool:
    clean = user_input.strip()
    if not clean:
        return True

    lower = clean.lower()
    if any(cmd in lower for cmd in ["exit", "quit", "power down", "stand down", "sleep"]):
        farewell = "Standing down secondary subroutines, sir. Have a pleasant day."
        speak(farewell)
        return False

    if any(cmd in lower for cmd in ["start voice conversation", "voice conversation mode", "let's talk", "lets chat"]):
        greeting = "Continuous voice conversation mode engaged, sir. I am listening continuously and will wait patiently for you to finish your statements."
        speak(greeting)
        threading.Thread(target=lambda: listener.start_conversation_session(process_command), daemon=True).start()
        return True

    response = brain.think(clean)
    speak(response)
    return True

def run_cli():
    print("=" * 65)
    print(f" J.A.R.V.I.S. // STARK INDUSTRIES BUTLER & AUTONOMY MATRIX")
    print(f" Status: Operational (Both Offline & Online) | Persona: {config.ASSISTANT_NAME}")
    print(f" Web Portal: http://localhost:{config.WEB_PORTAL_PORT}")
    print("=" * 65 + "\n")

    speak("J.A.R.V.I.S. is online, sir. Standing ready for your directive or schedule inquiry.")

    # Stop background wake daemon so it doesn't compete for the microphone
    listener.stop_wake_word_daemon()

    while True:
        try:
            user_input = listener.listen(prompt="Directive, sir (or 'what is my schedule?'): ")
            if not process_command(user_input):
                break
        except KeyboardInterrupt:
            print("\nInterrupt signal acknowledged. Standing down.")
            break
        except Exception as e:
            print(f"[Execution Anomaly]: {e}")

def main():
    if not ensure_single_instance():
        sys.exit(0)

    # 1. Guarantee Autostart on Device Boot
    try:
        enable_autostart()
    except Exception:
        pass

    # 2. Guarantee Desktop Shortcut with Iron Man Icon
    try:
        create_desktop_shortcut()
    except Exception:
        pass

    # 3. Monthly Diagnostic & Upgrade Scan (1st day of month)
    try:
        if learning_matrix.is_starting_day_of_month() and not learning_matrix.has_run_maintenance_this_month():
            threading.Thread(target=lambda: learning_matrix.run_self_maintenance_scan(), daemon=True).start()
    except Exception:
        pass

    # 4. Start Mobile Web Portal on Port 5050
    try:
        web_portal.start()
    except Exception:
        pass

    # 5. Start Hands-Free Voice Daemon
    try:
        listener.start_wake_word_daemon(process_command)
    except Exception:
        pass

    # 6. Start Ambient Hardware Watchdog & Play Boot Chime
    try:
        from core.watchdog import watchdog
        from core.chimes import play_boot_chime
        play_boot_chime()
        watchdog.start()
    except Exception:
        pass

    # 7. Start Proactive Butler Agenda & Sunrise Daemon
    try:
        from core.proactive_agent import proactive_agent
        proactive_agent.start()
    except Exception:
        pass

    # 8. Start Autonomous Display Wake Greeting Sentinel
    try:
        from core.display_sentinel import display_sentinel
        display_sentinel.start()
    except Exception:
        pass

    # 9. Start Autonomous Holographic Interface Sentinel & App Lifecycle Daemon
    try:
        from core.hologram_sentinel import hologram_sentinel
        hologram_sentinel.start()
        hologram_sentinel.display_hologram(reason="device_startup")
    except Exception:
        pass

    # 10. Start Supreme Head Commander & 24/7 Multi-Agent Syndicate
    try:
        from core.head_commander import head_commander
        head_commander.start()
    except Exception:
        pass

    # 11. Start Off-Grid & Hardware Standby Autonomy Sentinel
    try:
        from core.offgrid_sentinel import offgrid_sentinel
        offgrid_sentinel.start()
    except Exception:
        pass

    # 12. Start Monthly Business Scanner & 3rd-Night Evolution Sentinel
    try:
        from core.business_scanner import business_scanner
        threading.Thread(target=business_scanner.run_monthly_check, daemon=True).start()
    except Exception:
        pass

    try:
        from core.self_evolver import self_evolver
        threading.Thread(target=self_evolver.run_nightly_check, daemon=True).start()
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="J.A.R.V.I.S. Artificial Intelligence System")
    parser.add_argument("--cli", action="store_true", help="Launch in Interactive Command Line mode")
    parser.add_argument("--voice", action="store_true", help="Launch in Hands-Free Continuous Voice Conversation mode")
    parser.add_argument("--headless", action="store_true", help="Run background services and web portal silently")
    args = parser.parse_args()

    if args.voice:
        speak("J.A.R.V.I.S. voice conversation matrix activated, sir. I am standing by.")
        listener.start_conversation_session(process_command)
    elif args.cli:
        run_cli()
    elif args.headless:
        print("[J.A.R.V.I.S.]: Running in headless background mode. Press Ctrl+C to stop.")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            print("\nStanding down.")
    else:
        try:
            from ui.hud import launch_hud
            launch_hud()
        except Exception as e:
            print(f"[Display Server Notice]: Running in background matrix ({e})...")
            try:
                threading.Event().wait()
            except KeyboardInterrupt:
                print("\nStanding down.")

if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        import traceback
        with open("logs/main_exit.log", "a", encoding="utf-8") as f:
            f.write(f"EXITED WITH EXCEPTION: {type(e).__name__}: {e}\n{traceback.format_exc()}\n")
        raise
    else:
        with open("logs/main_exit.log", "a", encoding="utf-8") as f:
            f.write("MAIN FINISHED NORMALLY\n")
