"""
Live Interactive Test Script for Holographic Tactical HUD.
Exercises:
1. Holographic HUD display summoning and status check
2. 3D Wireframe Iron Man Mark-85 Helmet selection
3. Stepwise rotation of the 3D Helmet around Yaw & Pitch axes
4. Toggling Borderless Fullscreen Projector Mode (F11)
5. Reverting to Windowed Mode and resetting 3D model orientation
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.hud_controller import hud_controller
from core.hologram_sentinel import hologram_sentinel


def run_live_hud_test():
    print("=" * 65)
    print("  J.A.R.V.I.S. // HOLOGRAPHIC HUD & 3D ROTATION TEST HARNESS")
    print("=" * 65)

    # 1. Ensure HUD is displayed on desktop
    print("\n[Step 1]: Ensuring Holographic Tactical HUD is visible on desktop...")
    hologram_sentinel.display_hologram(reason="manual")
    time.sleep(1.0)

    status = hud_controller.get_hud_status()
    print(f"  Current HUD Status: Model={status.get('active_model')}, Fullscreen={status.get('is_fullscreen')}, Live={status.get('live')}")

    # 2. Select 3D Wireframe Helmet
    print("\n[Step 2]: Selecting 3D Wireframe Iron Man Mark-85 Helmet...")
    hud_controller.set_3d_model("helmet")
    time.sleep(0.8)

    # 3. Rotate 3D Helmet through 4 directional quadrant steps
    print("\n[Step 3]: Exercising 3D Wireframe Helmet rotation (Yaw & Pitch)...")
    for step in range(1, 5):
        print(f"  Rotating Helmet: Step {step}/4 (+45° Yaw, +10° Pitch)...")
        hud_controller.rotate_model(delta_yaw=0.785, delta_pitch=0.174)
        time.sleep(0.5)

    # 4. Toggle Borderless Fullscreen Projector Mode
    print("\n[Step 4]: Engaging Borderless Fullscreen Projector Mode (F11)...")
    hud_controller.toggle_fullscreen(state=True)
    time.sleep(1.2)
    print("  Projector mode engaged. Pitch-black canvas active for optical projection.")

    # 5. Revert back to Windowed Mode
    print("\n[Step 5]: Reverting to Windowed Holographic Mode...")
    hud_controller.toggle_fullscreen(state=False)
    time.sleep(0.8)

    # 6. Reset 3D View to center
    print("\n[Step 6]: Resetting 3D View to default center orientation...")
    hud_controller.reset_3d_view()
    time.sleep(0.5)

    final_status = hud_controller.get_hud_status()
    print("\n[Summary]: Live HUD rotation & fullscreen test completed successfully!")
    print(f"  Final Active Model: {final_status.get('active_model')}")
    print(f"  Fullscreen: {final_status.get('is_fullscreen')}")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_live_hud_test()
