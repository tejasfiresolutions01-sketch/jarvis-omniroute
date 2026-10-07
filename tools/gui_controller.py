"""
J.A.R.V.I.S. Autonomous Desktop GUI Automation Matrix.
Provides physical computer-use capabilities:
1. Mouse clicks, double clicks, scrolls, drags, and movement.
2. Keyboard typing, key presses, and multi-key combinations (hotkeys).
3. Fast clipboard pasting for code and long documents.
4. Window management (snap left/right, maximize, minimize, restore).
5. High-level compound desktop automation routines (e.g. open app, type, save).
6. Computer vision template button clicking via OpenCV.
"""

import time
import subprocess
from typing import Tuple, Optional, List
import pyautogui
import pyperclip

# Configure PyAutoGUI timings
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

class GUIController:
    """
    Autonomous controller for physical Windows desktop UI navigation.
    """

    def get_screen_resolution(self) -> Tuple[int, int]:
        """Returns (width, height) of primary display."""
        w, h = pyautogui.size()
        return int(w), int(h)

    def mouse_click(self, x: Optional[int] = None, y: Optional[int] = None, clicks: int = 1, button: str = "left") -> str:
        """Clicks at coordinates or at the current mouse position."""
        try:
            if x is not None and y is not None:
                pyautogui.click(x=x, y=y, clicks=clicks, button=button)
                return f"Mouse {button}-clicked at ({x}, {y}) {clicks} time(s), sir."
            else:
                pyautogui.click(clicks=clicks, button=button)
                cur_x, cur_y = pyautogui.position()
                return f"Mouse {button}-clicked at current position ({cur_x}, {cur_y}), sir."
        except Exception as e:
            return f"Error executing mouse click: {str(e)}"

    def mouse_move(self, x: int, y: int, duration: float = 0.2) -> str:
        """Smoothly moves mouse cursor to designated coordinates."""
        try:
            pyautogui.moveTo(x=x, y=y, duration=duration)
            return f"Mouse cursor repositioned to ({x}, {y}), sir."
        except Exception as e:
            return f"Error moving cursor: {str(e)}"

    def mouse_scroll(self, clicks: int) -> str:
        """
        Scrolls the active window.
        Positive integer scrolls up, negative integer scrolls down.
        """
        try:
            pyautogui.scroll(clicks)
            direction = "up" if clicks > 0 else "down"
            return f"Scrolled active viewport {direction} by {abs(clicks)} units, sir."
        except Exception as e:
            return f"Error executing scroll: {str(e)}"

    def keyboard_type(self, text: str, press_enter: bool = False, use_clipboard: bool = False) -> str:
        """
        Types text into the currently focused input field.
        Uses clipboard paste for long text/code to avoid typing delays.
        """
        try:
            if not text:
                return "No text provided to type, sir."

            if use_clipboard or len(text) > 40:
                # Fast clipboard paste
                pyperclip.copy(text)
                time.sleep(0.05)
                pyautogui.hotkey('ctrl', 'v')
            else:
                pyautogui.write(text, interval=0.015)

            if press_enter:
                time.sleep(0.05)
                pyautogui.press('enter')

            snippet = text[:40] + "..." if len(text) > 40 else text
            return f"Typed '{snippet}' into active field, sir."
        except Exception as e:
            return f"Error typing text: {str(e)}"

    def keyboard_hotkey(self, *keys) -> str:
        """
        Executes keyboard shortcut combination (e.g. ['ctrl', 's'], ['alt', 'tab'], ['win', 'd']).
        """
        try:
            if not keys:
                return "No keys specified, sir."
            pyautogui.hotkey(*keys)
            combo = "+".join(keys)
            return f"Keyboard hotkey '{combo}' executed, sir."
        except Exception as e:
            return f"Error executing hotkey: {str(e)}"

    def keyboard_press(self, key: str) -> str:
        """Presses a single key (e.g. 'enter', 'esc', 'tab', 'space', 'backspace')."""
        try:
            pyautogui.press(key)
            return f"Key '{key}' pressed, sir."
        except Exception as e:
            return f"Error pressing key: {str(e)}"

    def window_snap(self, direction: str) -> str:
        """
        Snaps or controls active window layout:
        - 'left': snap left (Win+Left)
        - 'right': snap right (Win+Right)
        - 'maximize': maximize window (Win+Up)
        - 'minimize': minimize window (Win+Down)
        - 'desktop': show desktop (Win+D)
        """
        try:
            clean = direction.lower().strip()
            if clean in ["left", "snap left"]:
                pyautogui.hotkey('win', 'left')
                return "Active window snapped to left split, sir."
            elif clean in ["right", "snap right"]:
                pyautogui.hotkey('win', 'right')
                return "Active window snapped to right split, sir."
            elif clean in ["maximize", "max", "up"]:
                pyautogui.hotkey('win', 'up')
                return "Active window maximized, sir."
            elif clean in ["minimize", "min", "down"]:
                pyautogui.hotkey('win', 'down')
                return "Active window minimized, sir."
            elif clean in ["desktop", "show desktop"]:
                pyautogui.hotkey('win', 'd')
                return "Desktop revealed, sir."
            else:
                return f"Unrecognized window direction '{direction}', sir."
        except Exception as e:
            return f"Error controlling window: {str(e)}"

    def browser_action(self, action: str) -> str:
        """
        Controls common browser navigation:
        - 'new_tab': Ctrl+T
        - 'close_tab': Ctrl+W
        - 'reopen_tab': Ctrl+Shift+T
        - 'refresh': F5
        - 'search_bar' / 'address_bar': Ctrl+L
        """
        try:
            clean = action.lower().strip()
            if clean in ["new_tab", "new tab"]:
                pyautogui.hotkey('ctrl', 't')
                return "Opened new browser tab, sir."
            elif clean in ["close_tab", "close tab"]:
                pyautogui.hotkey('ctrl', 'w')
                return "Closed current browser tab, sir."
            elif clean in ["reopen_tab", "reopen tab"]:
                pyautogui.hotkey('ctrl', 'shift', 't')
                return "Reopened previously closed tab, sir."
            elif clean in ["refresh", "reload"]:
                pyautogui.hotkey('ctrl', 'r')
                return "Refreshed browser viewport, sir."
            elif clean in ["address_bar", "search_bar", "url"]:
                pyautogui.hotkey('ctrl', 'l')
                return "Navigated cursor to browser address bar, sir."
            else:
                return f"Unrecognized browser action '{action}', sir."
        except Exception as e:
            return f"Error executing browser action: {str(e)}"

    def open_and_type(self, app_name: str, text: str, save_filename: Optional[str] = None) -> str:
        """
        High-level compound automation:
        1. Launches application (e.g. notepad, calc).
        2. Waits for window focus.
        3. Pastes/types text.
        4. If save_filename provided, triggers Ctrl+S, types name, and saves.
        """
        try:
            # 1. Launch application
            from tools.system_controller import system_controller
            system_controller.launch(app_name)
            time.sleep(1.2) # Allow window to spawn and take focus

            # 2. Type text
            self.keyboard_type(text, use_clipboard=True)
            time.sleep(0.3)

            # 3. Optional Save File
            if save_filename:
                pyautogui.hotkey('ctrl', 's')
                time.sleep(0.6)
                pyperclip.copy(save_filename)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.2)
                pyautogui.press('enter')
                return f"Launched {app_name}, typed content, and saved document as '{save_filename}', sir."

            return f"Launched {app_name} and typed content into active window, sir."
        except Exception as e:
            return f"Error executing open_and_type routine: {str(e)}"

# Global singleton
gui_controller = GUIController()
