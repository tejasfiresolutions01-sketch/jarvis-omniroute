"""
J.A.R.V.I.S. Windows Application Error & Crash Dialog Dismissal Utility.
Enumerates and clears any Windows Application Error / Access Violation dialogs,
WerFault processes, and orphaned python crash handlers.
"""

import os
import sys
import time
import ctypes
import subprocess

def clear_windows_error_dialogs():
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Disable hard error popups for future processes
    # SEM_FAILCRITICALERRORS (0x0001) | SEM_NOGPFAULTERRORBOX (0x0002) | SEM_NOOPENFILEERRORBOX (0x8000)
    kernel32.SetErrorMode(0x0001 | 0x0002 | 0x8000)

    # Attach to interactive desktop
    hdesk = user32.OpenInputDesktop(0, False, 0x01FF) or user32.OpenDesktopW("Default", 0, False, 0x01FF)
    if hdesk:
        user32.SetThreadDesktop(hdesk)

    dismissed = []

    def enum_windows_callback(hwnd, lparam):
        if not user32.IsWindow(hwnd):
            return True
        cls_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buf, 256)
        cname = cls_buf.value

        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value

        lower_t = title.lower()
        # Check for crash dialogs
        if (
            "application error" in lower_t
            or "python" in lower_t
            or "werfault" in lower_t
            or cname == "#32770"
            or "error" in lower_t
        ):
            # Inspect child controls (static text) to confirm error message
            child_texts = []
            def enum_child_callback(child_hwnd, _):
                c_len = user32.GetWindowTextLengthW(child_hwnd)
                if c_len > 0:
                    c_buf = ctypes.create_unicode_buffer(c_len + 1)
                    user32.GetWindowTextW(child_hwnd, c_buf, c_len + 1)
                    child_texts.append((child_hwnd, c_buf.value))
                return True

            CHILD_CMP = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            user32.EnumChildWindows(hwnd, CHILD_CMP(enum_child_callback), 0)

            full_dialog_text = " ".join([t for _, t in child_texts]).lower()

            if (
                "could not be written" in full_dialog_text
                or "0x00007fff" in full_dialog_text
                or "0x00000000" in full_dialog_text
                or "application error" in lower_t
                or "memory" in full_dialog_text
            ):
                print(f"[FOUND ERROR DIALOG]: HWND={hwnd}, Title='{title}', Class='{cname}'")
                print(f"  Dialog text: {full_dialog_text[:120]}...")

                # Click OK (IDOK = 1) or Cancel (IDCANCEL = 2) or send WM_CLOSE (0x0010)
                user32.PostMessageW(hwnd, 0x0111, 1, 0) # WM_COMMAND with IDOK
                user32.PostMessageW(hwnd, 0x0111, 2, 0) # WM_COMMAND with IDCANCEL
                user32.PostMessageW(hwnd, 0x0010, 0, 0) # WM_CLOSE
                dismissed.append((hwnd, title))

        return True

    CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(CMPFUNC(enum_windows_callback), 0)

    # Also kill any WerFault (Windows Error Reporting) processes that might be displaying dialogs
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "WerFault.exe"],
            capture_output=True,
            text=True
        )
    except Exception:
        pass

    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "WerFaultSecure.exe"],
            capture_output=True,
            text=True
        )
    except Exception:
        pass

    return len(dismissed)

if __name__ == "__main__":
    count = clear_windows_error_dialogs()
    print(f"[Result]: Successfully processed and cleared error dialogs (Count: {count}).")
