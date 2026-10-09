"""
J.A.R.V.I.S. Autonomous Multi-Modal Vision Perception & Screen Comprehension Matrix.
Features:
1. Zero-Warning High-Speed Screen Capture via mss.MSS with PIL ImageGrab fallback.
2. Native Win32 Window Geometry, Process Attribution, and Bounding Rectangle Inspection.
3. Microsoft UI Automation (UIA) COM Tree Semantic Control Discovery.
4. OpenCV & Computer Vision Layout Analysis (Theme, Luminance, Saliency, Quadrant Density, Modal Detection).
5. Multi-Modal Screen Comprehension Engine with articulate British Butler phrasing.
6. 100% Local, offline-first execution with zero cloud dependencies; optional Gemini multimodal enhancement.
"""

import os
import re
import sys
import ctypes
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import psutil
from PIL import Image

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except Exception:
    HAS_CV2 = False

try:
    import mss
    HAS_MSS = True
except Exception:
    HAS_MSS = False

import config

logger = logging.getLogger("VisionPerception")

# Win32 Structures
class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def get_active_window_title() -> str:
    """Returns the title of the active foreground window."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "Desktop"
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return "Desktop"
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value or "Desktop"
    except Exception:
        return "Desktop"


def get_active_window_geometry() -> Dict[str, Any]:
    """
    Returns full window geometry, class name, process name, and PID
    for the active foreground window.
    """
    info = {
        "title": "Desktop",
        "class_name": "Progman",
        "process_name": "explorer.exe",
        "pid": 0,
        "hwnd": 0,
        "state": "normal",
        "rect": {"left": 0, "top": 0, "right": 1920, "bottom": 1080, "width": 1920, "height": 1080}
    }

    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return info

        info["hwnd"] = hwnd

        # Window Title
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if buf.value:
                info["title"] = buf.value

        # Class Name
        cls_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buf, 256)
        if cls_buf.value:
            info["class_name"] = cls_buf.value

        # Process ID & Name
        pid_val = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_val))
        info["pid"] = pid_val.value
        if pid_val.value > 0:
            try:
                proc = psutil.Process(pid_val.value)
                info["process_name"] = proc.name()
            except Exception:
                pass

        # Window Bounding Rectangle
        rect = RECT()
        if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            w = max(0, rect.right - rect.left)
            h = max(0, rect.bottom - rect.top)
            if w > 0 and h > 0:
                info["rect"] = {
                    "left": rect.left,
                    "top": rect.top,
                    "right": rect.right,
                    "bottom": rect.bottom,
                    "width": w,
                    "height": h
                }

        # Window State
        if user32.IsIconic(hwnd):
            info["state"] = "minimized"
        elif user32.IsZoomed(hwnd):
            info["state"] = "maximized"
        else:
            info["state"] = "normal"

    except Exception as e:
        logger.debug(f"Window geometry query notice: {e}")

    return info


def capture_screen(save_path: Optional[Path] = None) -> Tuple[Optional[Image.Image], Tuple[int, int], str]:
    """
    Captures primary screen using modern mss.MSS context manager.
    Falls back to PIL ImageGrab if mss fails.
    Returns: (PIL.Image, (width, height), file_path_str)
    """
    temp_dir = config.BASE_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    target_path = save_path or (temp_dir / "screen_capture.png")

    w, h = 1920, 1080
    pil_img: Optional[Image.Image] = None

    # 1. Try mss (Modern context manager)
    if HAS_MSS:
        try:
            with mss.MSS() as sct:
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                sct_img = sct.grab(monitor)
                pil_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                w, h = pil_img.size
                pil_img.save(target_path)
                return pil_img, (w, h), str(target_path)
        except Exception as e:
            logger.debug(f"mss capture fallback triggered: {e}")

    # 2. Fallback to PIL ImageGrab
    try:
        from PIL import ImageGrab
        pil_img = ImageGrab.grab()
        w, h = pil_img.size
        pil_img.save(target_path)
        return pil_img, (w, h), str(target_path)
    except Exception as e:
        logger.debug(f"ImageGrab fallback error: {e}")

    # 3. Create minimal placeholder image if screen capture completely unavailable
    if pil_img is None:
        pil_img = Image.new("RGB", (w, h), color=(20, 25, 35))
        try:
            pil_img.save(target_path)
        except Exception:
            pass

    return pil_img, (w, h), str(target_path)


def extract_screen_ui_hierarchy(window_title: Optional[str] = None, max_items: int = 50) -> Dict[str, Any]:
    """
    Extracts structured UI control tree (buttons, input fields, text elements)
    from the target or active window using Microsoft UI Automation (UIA) COM.
    """
    hierarchy: Dict[str, Any] = {
        "buttons": [],
        "inputs": [],
        "text_elements": [],
        "menus": [],
        "tabs": [],
        "all_controls": [],
        "summary": "No interactive UIA controls discovered."
    }

    try:
        from tools.uia_controller import windows_uia
        if not windows_uia.is_available:
            return hierarchy

        target_title = window_title or get_active_window_title()
        controls = windows_uia.inspect_window_controls(target_title, max_items=max_items)
        if not controls and target_title != "Desktop":
            # Try inspecting open windows generally
            for win in windows_uia.get_open_windows()[:3]:
                w_controls = windows_uia.inspect_window_controls(win["name"], max_items=15)
                if w_controls:
                    controls.extend(w_controls)
                    break

        hierarchy["all_controls"] = controls

        for c in controls:
            ct = c.get("control_type", "").lower()
            name = c.get("name", "").strip()
            aid = c.get("automation_id", "").strip()
            item_label = name or aid

            if not item_label:
                continue

            if ct in ["button"]:
                hierarchy["buttons"].append({"name": item_label, "enabled": c.get("enabled", True)})
            elif ct in ["edit", "input"]:
                hierarchy["inputs"].append({"name": item_label, "aid": aid})
            elif ct in ["text"]:
                hierarchy["text_elements"].append({"name": item_label})
            elif ct in ["menu", "menubar", "menuitem"]:
                hierarchy["menus"].append({"name": item_label})
            elif ct in ["tab", "tabitem"]:
                hierarchy["tabs"].append({"name": item_label})

        # Generate summary
        b_count = len(hierarchy["buttons"])
        i_count = len(hierarchy["inputs"])
        t_count = len(hierarchy["text_elements"])
        hierarchy["summary"] = (
            f"Detected {len(controls)} UI elements: "
            f"{b_count} button(s), {i_count} input field(s), and {t_count} text element(s)."
        )
    except Exception as e:
        logger.debug(f"UIA hierarchy extraction notice: {e}")

    return hierarchy


def analyze_visual_layout(
    image_path: Optional[Path] = None,
    img: Optional[Image.Image] = None
) -> Dict[str, Any]:
    """
    Applies OpenCV and computer vision analytics to inspect screen layout:
    - Dominant Color & Perceived Luminance
    - Dark Mode vs Light Mode classification
    - UI Bounding Boxes, Saliency & Contour Quadrant Density
    - Modal Dialog Detection
    """
    layout: Dict[str, Any] = {
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "theme": "dark_mode",
        "luminance": 40.0,
        "dominant_color_hex": "#1a1f2c",
        "regions_detected": 0,
        "modal_dialog_detected": False,
        "modal_bounds": None,
        "quadrant_density": {
            "top_left": 0,
            "top_right": 0,
            "bottom_left": 0,
            "bottom_right": 0,
            "center": 0
        }
    }

    # Load or convert image to cv2 numpy array
    cv_img = None
    if img is not None:
        try:
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) if HAS_CV2 else None
            layout["width"], layout["height"] = img.size
        except Exception:
            pass
    elif image_path is not None and HAS_CV2:
        try:
            cv_img = cv2.imread(str(image_path))
            if cv_img is not None:
                h, w = cv_img.shape[:2]
                layout["width"], layout["height"] = w, h
        except Exception:
            pass

    if cv_img is None or not HAS_CV2:
        # Fallback using PIL if cv2 is not available
        if img is not None:
            try:
                w, h = img.size
                layout["width"], layout["height"] = w, h
                # Sample small thumbnail for luminance
                thumb = img.resize((32, 32))
                pixels = list(thumb.getdata())
                avg_r = sum(p[0] for p in pixels) / len(pixels)
                avg_g = sum(p[1] for p in pixels) / len(pixels)
                avg_b = sum(p[2] for p in pixels) / len(pixels)
                lum = 0.299 * avg_r + 0.587 * avg_g + 0.114 * avg_b
                layout["luminance"] = round(lum, 1)
                layout["theme"] = "dark_mode" if lum < 128 else "light_mode"
                layout["dominant_color_hex"] = f"#{int(avg_r):02x}{int(avg_g):02x}{int(avg_b):02x}"
            except Exception:
                pass
        return layout

    h, w = cv_img.shape[:2]
    layout["width"] = w
    layout["height"] = h
    layout["aspect_ratio"] = f"{round(w / max(1, h), 2)}:1"

    # 1. Color and Luminance Analysis
    try:
        # Downscale for instant processing (< 2ms)
        small = cv2.resize(cv_img, (64, 64))
        avg_b, avg_g, avg_r = np.mean(small, axis=(0, 1))
        luminance = 0.299 * avg_r + 0.587 * avg_g + 0.114 * avg_b
        layout["luminance"] = round(float(luminance), 1)
        layout["theme"] = "dark_mode" if luminance < 128 else "light_mode"
        layout["dominant_color_hex"] = f"#{int(avg_r):02x}{int(avg_g):02x}{int(avg_b):02x}"
    except Exception as e:
        logger.debug(f"Luminance calculation notice: {e}")

    # 2. Contour & Visual Saliency / Modal Detection
    try:
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        # Dilate edges to bridge gaps in window frames and buttons
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        min_area = (w * h) * 0.005  # minimum 0.5% of screen area
        significant_boxes = []

        half_w, half_h = w / 2, h / 2
        quad_counts = {"top_left": 0, "top_right": 0, "bottom_left": 0, "bottom_right": 0, "center": 0}

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                bx, by, bw, bh = cv2.boundingRect(cnt)
                significant_boxes.append((bx, by, bw, bh, area))

                cx, cy = bx + bw / 2, by + bh / 2
                
                # Check center region (middle 40% of screen)
                if (0.3 * w <= cx <= 0.7 * w) and (0.3 * h <= cy <= 0.7 * h):
                    quad_counts["center"] += 1
                elif cx < half_w and cy < half_h:
                    quad_counts["top_left"] += 1
                elif cx >= half_w and cy < half_h:
                    quad_counts["top_right"] += 1
                elif cx < half_w and cy >= half_h:
                    quad_counts["bottom_left"] += 1
                else:
                    quad_counts["bottom_right"] += 1

        layout["regions_detected"] = len(significant_boxes)
        layout["quadrant_density"] = quad_counts

        # Modal Dialog Detection: look for bounded rectangle centered on screen covering 8% to 75% screen area
        for bx, by, bw, bh, area in significant_boxes:
            ratio = area / (w * h)
            if 0.08 <= ratio <= 0.75:
                cx, cy = bx + bw / 2, by + bh / 2
                # Check if approximately centered
                if abs(cx - half_w) < (w * 0.2) and abs(cy - half_h) < (h * 0.2):
                    layout["modal_dialog_detected"] = True
                    layout["modal_bounds"] = {"x": bx, "y": by, "width": bw, "height": bh}
                    break

    except Exception as e:
        logger.debug(f"OpenCV contour layout analysis notice: {e}")

    return layout


def comprehend_screen(query: str = "what is on my screen?") -> Dict[str, Any]:
    """
    Unified multi-modal vision perception and screen comprehension pipeline.
    Combines:
    - Screen capture
    - Win32 window geometry & process attribution
    - UIA interactive control hierarchy
    - OpenCV layout, theme, and saliency analysis
    - Articulate British Butler spoken response
    """
    clean_q = query.strip().lower()

    # 1. Capture screen
    pil_img, (w, h), shot_path = capture_screen()

    # 2. Window Geometry
    win_info = get_active_window_geometry()
    active_win = win_info.get("title", "Desktop")
    proc_name = win_info.get("process_name", "explorer.exe")
    rect = win_info.get("rect", {})

    # 3. UIA Semantic Controls
    ui_tree = extract_screen_ui_hierarchy(window_title=active_win)

    # 4. Computer Vision Layout & Theme
    layout = analyze_visual_layout(img=pil_img)
    theme = layout.get("theme", "dark_mode")
    lum = layout.get("luminance", 50.0)

    # 5. Specialized intent routing
    speech = ""

    # Check for "find button" intent
    btn_match = re.search(r"(?:find|locate|where is|search for)\s+(?:the\s+)?button\s+['\"]?([a-zA-Z0-9_\-\s]+)['\"]?", clean_q)
    if not btn_match:
        btn_match = re.search(r"(?:button)\s+['\"]?([a-zA-Z0-9_\-\s]+)['\"]?", clean_q)

    if btn_match:
        target_btn = btn_match.group(1).strip().lower()
        found_btn = None
        for b in ui_tree.get("buttons", []):
            if target_btn in b["name"].lower():
                found_btn = b
                break

        if found_btn:
            status = "enabled" if found_btn.get("enabled", True) else "disabled"
            speech = (
                f"Button '{found_btn['name']}' located on the active window '{active_win}', sir. "
                f"Its status is currently {status} and accessible for interaction."
            )
        else:
            # Check all controls
            for c in ui_tree.get("all_controls", []):
                if target_btn in c.get("name", "").lower():
                    ct = c.get("control_type", "control")
                    speech = (
                        f"Found UI element '{c.get('name')}' as a {ct} in '{active_win}', sir."
                    )
                    break

        if not speech:
            speech = f"I scanned the active window '{active_win}', sir, but could not locate a button labeled '{target_btn}'."

    # Check for theme / dark mode inquiry
    elif any(k in clean_q for k in ["dark mode", "light mode", "screen theme", "visual theme", "theme of screen"]):
        theme_str = "Dark Mode" if theme == "dark_mode" else "Light Mode"
        speech = (
            f"The active display is configured in {theme_str}, sir, "
            f"with an average perceived luminance of {lum:.1f} and primary tone {layout.get('dominant_color_hex', '#000000')}."
        )

    # Check for screen vitals / resolution inquiry
    elif any(k in clean_q for k in ["screen vitals", "display vitals", "resolution", "display resolution"]):
        modal_text = "with a modal dialog overlay" if layout.get("modal_dialog_detected") else "with no blocking dialogs"
        speech = (
            f"Optical screen vitals confirmed, sir: Resolution is {w}x{h} ({layout.get('aspect_ratio')}), "
            f"active foreground window '{active_win}' ({proc_name}) spans {rect.get('width', w)}x{rect.get('height', h)} pixels, {modal_text}."
        )

    # Check for reading text on screen
    elif any(k in clean_q for k in ["read text", "read screen", "text on screen", "screen text", "what text"]):
        text_samples = [t["name"] for t in ui_tree.get("text_elements", [])[:5]]
        if not text_samples and ui_tree.get("buttons"):
            text_samples = [b["name"] for b in ui_tree.get("buttons", [])[:5]]

        if text_samples:
            items_str = ", ".join(f"'{s}'" for s in text_samples)
            speech = (
                f"Scanning active interface '{active_win}', sir. "
                f"Prominent UI text elements include: {items_str}."
            )
        else:
            speech = (
                f"Optical scan of '{active_win}' completed, sir. "
                f"No prominent standard text controls were isolated via the UIA hierarchy; graphical contents are active."
            )

    # General "what is on my screen" / "inspect display" synthesis
    else:
        # If online with Gemini API Key, perform multimodal reasoning
        if config.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=config.GEMINI_API_KEY)
                prompt = (
                    f"Analyze this user desktop screen screenshot. Active window is '{active_win}' ({proc_name}). "
                    f"Query: {query}. Be concise, like Tony Stark's J.A.R.V.I.S."
                )
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[pil_img, prompt]
                )
                if resp and resp.text:
                    speech = resp.text.strip()
            except Exception as e:
                logger.debug(f"Gemini multimodal reasoning notice: {e}")

        if not speech:
            # Articulate butler offline synthesis
            theme_str = "dark-themed" if theme == "dark_mode" else "light-themed"
            modal_notice = " A modal popup appears centered on display." if layout.get("modal_dialog_detected") else ""
            ctrl_notice = f" {ui_tree.get('summary')}" if ui_tree.get("all_controls") else ""

            speech = (
                f"Visual telemetry acquired, sir. "
                f"Active application is '{active_win}' under process '{proc_name}', "
                f"rendering across a {w}x{h} {theme_str} display.{modal_notice}{ctrl_notice}"
            )

    return {
        "success": True,
        "speech": speech,
        "active_window": win_info,
        "visual_layout": layout,
        "ui_controls": ui_tree,
        "screenshot_path": shot_path
    }


def capture_and_inspect_display(query: str = "Analyze active display") -> str:
    """
    Backwards-compatible interface for display inspection.
    Returns articulate spoken butler response.
    """
    result = comprehend_screen(query)
    return result.get("speech", "Optical scan completed, sir.")
