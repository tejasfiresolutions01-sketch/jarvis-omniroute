import os
from pathlib import Path
from typing import Optional
import config

def capture_webcam_frame(save_path: Optional[Path] = None) -> Optional[Path]:
    """Captures a single optical frame from the primary webcam."""
    temp_dir = config.BASE_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    dest = save_path or (temp_dir / "webcam_snapshot.jpg")

    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None
        # Warm up sensor
        for _ in range(3):
            cap.read()
        ret, frame = cap.read()
        cap.release()
        if ret:
            cv2.imwrite(str(dest), frame)
            return dest
    except Exception:
        pass
    return None

def inspect_physical_camera(query: str = "What do you see through the camera?") -> str:
    """
    Captures physical camera feed and analyzes visual environment.
    Supports both offline telemetry and online multimodal reasoning.
    """
    img_path = capture_webcam_frame()
    if not img_path or not img_path.exists():
        return "Optical camera sensors are currently unreachable or disabled, sir."

    # If online with Gemini Key, perform multimodal reasoning
    if config.GEMINI_API_KEY:
        try:
            from google import genai
            from PIL import Image
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            img = Image.open(img_path)
            prompt = f"Analyze this physical camera image. User asks: '{query}'. Answer concisely like Tony Stark's J.A.R.V.I.S."
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[img, prompt]
            )
            if resp and resp.text:
                return resp.text.strip()
        except Exception:
            pass

    return f"Optical webcam frame captured successfully, sir. Snapshot secured to {img_path.name}."

def start_gesture_control(camera_index: int = 0) -> str:
    """
    Activates background real-time optical hand gesture tracking for mid-air HUD manipulation.
    """
    try:
        from tools.gesture_controller import spatial_gesture_engine
        spatial_gesture_engine.start_tracking_daemon(camera_index=camera_index)
        return "Optical hand gesture tracking matrix active, sir. You may now control the holographic display with mid-air hand motions."
    except Exception as e:
        return f"Error activating optical gesture tracking: {e}"

def stop_gesture_control() -> str:
    """
    Disarms background hand gesture tracking.
    """
    try:
        from tools.gesture_controller import spatial_gesture_engine
        spatial_gesture_engine.stop_tracking_daemon()
        return "Optical hand gesture tracking disarmed, sir."
    except Exception as e:
        return f"Error stopping optical gesture tracking: {e}"

def is_gesture_tracking_active() -> bool:
    """Returns True if hand tracking daemon is active."""
    try:
        from tools.gesture_controller import spatial_gesture_engine
        return spatial_gesture_engine._is_tracking
    except Exception:
        return False
