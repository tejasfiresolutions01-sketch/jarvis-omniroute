"""
Live 3D Holographic Rendering & OBJ/STL Engine Verification Harness.
Simulates live 60 FPS rotation, multi-pass neon bloom, and model switching.
"""

import os
import sys
import time
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui.mesh_3d_engine import holographic_3d, MeshLoader
from tools.hud_controller import hud_controller
from unittest.mock import MagicMock


def run_live_hud_3d_verification():
    print("=" * 65)
    print("J.A.R.V.I.S. Live 3D Holographic Rendering & Mesh Engine Harness")
    print("=" * 65)

    # 1. Verify Procedural Models
    models = ["helmet", "reactor", "globe", "tesseract", "drone"]
    for m in models:
        mesh = MeshLoader.get_procedural_mesh(m)
        print(f" [PASS] Loaded Procedural Model '{m.upper()}': {len(mesh.vertices)} vertices, {len(mesh.edges)} edges")
        assert len(mesh.vertices) > 0
        assert len(mesh.edges) > 0

    # 2. Verify Wavefront .obj Dynamic Loading
    cube_obj = """v -1 -1 -1
v 1 -1 -1
v 1 1 -1
v -1 1 -1
f 1 2 3 4
"""
    with tempfile.NamedTemporaryFile("w", suffix=".obj", delete=False) as f:
        f.write(cube_obj)
        obj_file = f.name

    try:
        ok = holographic_3d.load_custom_file(obj_file)
        assert ok, "Failed to load custom .obj file"
        print(f" [PASS] Loaded Custom OBJ Model: {len(holographic_3d.active_mesh.vertices)} vertices")
    finally:
        if os.path.exists(obj_file):
            os.remove(obj_file)

    # 3. Simulate 60 FPS Neon Bloom Rendering
    holographic_3d.set_mesh("helmet")
    mock_canvas = MagicMock()
    theme = {"primary": "#00f0ff", "glow": "#00a2ff", "secondary": "#ffd700"}

    t_start = time.perf_counter()
    frames = 60
    for _ in range(frames):
        holographic_3d.update_physics()
        holographic_3d.project_and_render(mock_canvas, cx=280, cy=140, theme=theme, audio_energy=0.25)
    elapsed = time.perf_counter() - t_start
    fps = frames / elapsed
    print(f" [PASS] Rendered {frames} frames with multi-pass neon bloom in {elapsed:.3f}s (~{fps:.1f} FPS)")
    assert fps >= 60.0, f"Renderer did not achieve target 60 FPS (was {fps:.1f} FPS)"

    # 4. Verify HUD Controller IPC Integration
    ok_set = hud_controller.set_3d_model("drone")
    assert ok_set, "Failed to send set_3d_model command via hud_controller"
    print(" [PASS] Dispatched set_3d_model('drone') via IPC queue")

    print("=" * 65)
    print("3D Holographic Rendering Live Verification: ALL TESTS PASSED.")
    print("=" * 65)
    return True


if __name__ == "__main__":
    run_live_hud_3d_verification()
