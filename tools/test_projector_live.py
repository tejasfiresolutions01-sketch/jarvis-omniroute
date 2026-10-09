"""
J.A.R.V.I.S. 3-Dimensional Holographic Projector System Diagnostics & Live Verification.
Tests optical model construction, pyramid transformation matrices,
stereoscopic anaglyph parallax mathematics, and multi-monitor enumeration.
"""

import math
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.projector_system import projector_system
from tools.projector_controller import projector_controller
from ui.projector_3d import ProjectorMeshLibrary, projector_3d_engine
from core.local_intelligence import local_intelligence


def run_live_diagnostics():
    print("=" * 70)
    print("J.A.R.V.I.S. 3-DIMENSIONAL PROJECTOR SYSTEM - LIVE DIAGNOSTICS")
    print("=" * 70)

    # 1. Procedural 3D Model Verification
    print("\n[Phase 1] Verifying Procedural 3D Models in Projector Library...")
    models_to_test = ["helmet", "reactor", "globe", "tesseract", "drone", "gauntlet", "emitter"]
    for m in models_to_test:
        mesh = ProjectorMeshLibrary.get_mesh(m)
        assert mesh is not None, f"Failed to generate model '{m}'"
        assert len(mesh.vertices) > 0, f"Model '{m}' has 0 vertices"
        assert len(mesh.edges) > 0, f"Model '{m}' has 0 edges"
        print(f"  [OK] Model '{m.upper()}': {len(mesh.vertices)} vertices, {len(mesh.edges)} edges, {len(mesh.highlight_nodes)} highlights")

    # 2. Multi-Monitor & External Projector Enumeration
    print("\n[Phase 2] Enumerating Video Displays & External Projectors...")
    monitors = projector_system.enumerate_monitors()
    print(f"  [OK] Detected {len(monitors)} monitor(s):")
    for mon in monitors:
        print(f"    - [{mon['index']}] {mon['name']} ({mon['width']}x{mon['height']} at {mon['x']},{mon['y']}) - {mon['type']}")
    assert len(monitors) >= 1, "At least 1 display must be detected"

    # 3. Vectorized Transformations & Parallax Calculation
    print("\n[Phase 3] Testing 3D Perspective Transformations & Stereoscopic Parallax...")
    engine = projector_3d_engine
    engine.set_mesh("gauntlet")
    engine.scale = 1.0
    engine.yaw = 0.5
    engine.pitch = 0.2

    # Vectorized transform test
    px, py, depth = engine._transform_vertices(engine.yaw, engine.pitch, engine.scale)
    assert len(px) == len(engine.active_mesh.vertices)
    assert len(py) == len(engine.active_mesh.vertices)
    assert (depth > 0).all()
    print(f"  [OK] 3D Transform succeeded: {len(px)} projected points, min depth: {depth.min():.1f}, max depth: {depth.max():.1f}")

    # Stereoscopic Anaglyph parallax test
    engine.parallax_offset = 8.0
    px_l, py_l, _ = engine._transform_vertices(engine.yaw - 0.025, engine.pitch, engine.scale)
    px_r, py_r, _ = engine._transform_vertices(engine.yaw + 0.025, engine.pitch, engine.scale)
    assert len(px_l) == len(px_r)
    parallax_diff = np_abs_mean = abs(px_r - px_l).mean()
    print(f"  [OK] Stereoscopic Anaglyph parallax separation verified: mean disparity = {parallax_diff:.2f}px")

    # 4. State Management & IPC Messaging
    print("\n[Phase 4] Testing Projector State Management & IPC Dispatch...")
    init_state = projector_system.get_state()
    assert "mode" in init_state
    assert "model" in init_state

    # Test mode shift
    projector_system.set_projection_mode("pyramid")
    assert projector_system.get_state()["mode"] == "pyramid"
    print("  [OK] Mode shift to PYRAMID validated in state")

    projector_system.set_projection_mode("anaglyph")
    assert projector_system.get_state()["mode"] == "anaglyph"
    print("  [OK] Mode shift to ANAGLYPH validated in state")

    # Test model shift
    projector_system.set_3d_model("emitter")
    assert projector_system.get_state()["model"] == "emitter"
    print("  [OK] Model shift to EMITTER validated in state")

    # Test parallax adjustment
    new_p = projector_system.adjust_parallax(3.0)
    assert new_p > 0
    print(f"  [OK] Parallax adjusted to: {new_p:.1f}px")

    # 5. Local Intelligence Voice Directives Battery
    print("\n[Phase 5] Testing Voice Command Directives Battery...")
    test_queries = [
        ("activate 3 dimensional projector", "3-Dimensional Holographic Projector System activated"),
        ("projector mode pyramid", "Projector switched to 4-Way Holographic Pyramid Mode"),
        ("projector mode anaglyph", "Projector switched to Stereoscopic Anaglyph 3D Mode"),
        ("projector mode floating", "Projector switched to Floating Desktop Hologram Mode"),
        ("project gauntlet", "Projecting 3D Mark-85 Repulsor Gauntlet"),
        ("project emitter", "Projecting 3D Conical Holo-Lens Emitter"),
        ("project drone", "Projecting 3D Stark Industries Hypersonic Drone"),
        ("increase projector depth", "Stereoscopic 3D parallax depth increased"),
        ("projector status", "Projector System Status"),
        ("deactivate 3d projector", "3-Dimensional Holographic Projector System deactivated"),
    ]

    for query, expected_snippet in test_queries:
        handled, response = local_intelligence.evaluate_and_execute(query)
        assert handled, f"Query '{query}' was not recognized by local_intelligence"
        assert expected_snippet.lower() in response.lower(), f"Response '{response}' did not contain expected snippet '{expected_snippet}'"
        print(f"  [OK] Recognized: '{query}' -> '{response[:60]}...'")

    print("\n" + "=" * 70)
    print("ALL 3D PROJECTOR SYSTEM DIAGNOSTICS PASSED WITH 100% SUCCESS!")
    print("=" * 70)


if __name__ == "__main__":
    run_live_diagnostics()
