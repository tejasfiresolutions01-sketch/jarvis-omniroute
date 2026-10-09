"""
J.A.R.V.I.S. Live Vision Perception & Screen Comprehension Verification Harness.
Performs end-to-end live testing across window geometry, display capture,
OpenCV layout telemetry, UIA hierarchy, and voice directives.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tools.vision_tools import (
    get_active_window_title,
    get_active_window_geometry,
    capture_screen,
    analyze_visual_layout,
    extract_screen_ui_hierarchy,
    comprehend_screen,
    capture_and_inspect_display
)
from core.local_intelligence import local_intelligence


def run_live_vision_diagnostic():
    print("=" * 65)
    print("J.A.R.V.I.S. MULTI-MODAL VISION PERCEPTION LIVE VERIFICATION")
    print("=" * 65)

    # 1. Window Geometry
    print("\n[1/6] Querying Foreground Window Geometry...")
    geom = get_active_window_geometry()
    title = geom.get("title", "Desktop")
    proc = geom.get("process_name", "explorer.exe")
    rect = geom.get("rect", {})
    state = geom.get("state", "normal")
    print(f"  -> Title       : {title}")
    print(f"  -> Process     : {proc} (PID: {geom.get('pid', 0)})")
    print(f"  -> Class       : {geom.get('class_name', 'N/A')}")
    print(f"  -> Geometry    : {rect.get('width', 0)}x{rect.get('height', 0)} at ({rect.get('left', 0)}, {rect.get('top', 0)})")
    print(f"  -> State       : {state}")
    assert isinstance(title, str), "Window title must be a string"
    assert "width" in rect and rect["width"] >= 0, "Window rect must have valid width"

    # 2. Display Capture
    print("\n[2/6] Capturing Display via modern mss.MSS...")
    img, (w, h), shot_path = capture_screen()
    print(f"  -> Resolution  : {w}x{h}")
    print(f"  -> File Saved  : {shot_path}")
    assert img is not None, "Display capture must produce an image"
    assert w > 0 and h > 0, "Display resolution must be non-zero"
    assert Path(shot_path).exists(), "Saved screenshot file must exist"

    # 3. OpenCV Visual Layout Analysis
    print("\n[3/6] Analyzing Computer Vision Layout & Theme...")
    layout = analyze_visual_layout(img=img)
    theme = layout.get("theme")
    lum = layout.get("luminance", 0.0)
    hex_col = layout.get("dominant_color_hex", "#000000")
    quads = layout.get("quadrant_density", {})
    modal = layout.get("modal_dialog_detected", False)
    print(f"  -> Detected Theme: {theme} (Luminance: {lum:.1f})")
    print(f"  -> Primary Color : {hex_col}")
    print(f"  -> Modal Dialog  : {'Detected' if modal else 'None'}")
    print(f"  -> Quadrants     : TL={quads.get('top_left',0)}, TR={quads.get('top_right',0)}, BL={quads.get('bottom_left',0)}, BR={quads.get('bottom_right',0)}, Center={quads.get('center',0)}")
    assert theme in ["dark_mode", "light_mode"], "Theme must be dark_mode or light_mode"

    # 4. UIA Semantic Control Hierarchy
    print("\n[4/6] Inspecting UIA Semantic Control Tree...")
    ui_tree = extract_screen_ui_hierarchy()
    b_count = len(ui_tree.get("buttons", []))
    i_count = len(ui_tree.get("inputs", []))
    t_count = len(ui_tree.get("text_elements", []))
    print(f"  -> Buttons Found : {b_count}")
    print(f"  -> Inputs Found  : {i_count}")
    print(f"  -> Text Elements : {t_count}")
    print(f"  -> Summary       : {ui_tree.get('summary')}")
    assert "buttons" in ui_tree and "inputs" in ui_tree, "Hierarchy must contain control lists"

    # 5. Multi-Modal Screen Comprehension Queries
    print("\n[5/6] Executing Comprehension Battery...")
    queries = [
        "what is on my screen?",
        "is screen dark mode",
        "screen vitals",
        "find button OK",
        "read text on screen"
    ]
    for q in queries:
        res = comprehend_screen(q)
        assert res.get("success"), f"Comprehension query failed for '{q}'"
        speech = res.get("speech", "")
        print(f"  [Q: '{q}']")
        print(f"  -> J.A.R.V.I.S.: \"{speech}\"")
        assert len(speech) > 10, f"Spoken response too short for '{q}'"

    # 6. End-to-End Directive Dispatch via Local Intelligence
    print("\n[6/6] Verifying Local Intelligence Directive Integration...")
    directives = [
        "what is on my screen",
        "screen theme",
        "display vitals"
    ]
    for d in directives:
        handled, resp = local_intelligence.evaluate_and_execute(d)
        assert handled, f"Directive '{d}' was not handled by local intelligence"
        print(f"  [Directive: '{d}'] Handled: {handled}")
        print(f"  -> Response: \"{resp[:85]}...\"")

    print("\n" + "=" * 65)
    print("ALL 6 LIVE VISION PERCEPTION VERIFICATIONS PASSED WITH 100% SUCCESS")
    print("=" * 65)
    return True


if __name__ == "__main__":
    success = run_live_vision_diagnostic()
    sys.exit(0 if success else 1)
