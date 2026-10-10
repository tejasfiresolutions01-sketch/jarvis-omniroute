"""
J.A.R.V.I.S. High-Definition 3D Holographic Projector Optical Rendering Engine.
Features:
1. 4-Way Holographic Pyramid Matrix (Pepper's Ghost Quad-View Projection).
2. Stereoscopic Anaglyph 3D Engine (Red/Cyan Dual-Parallax Binocular Depth).
3. Direct Focused Holo-Beam & Floating Desktop Projector Views.
4. Procedural Sci-Fi 3D Meshes:
   - Mark-85 Helmet, Arc Reactor, Celestial Globe, 4D Tesseract, Stark Drone, Repulsor Gauntlet, Holo-Emitter.
5. Real-Time Vectorized NumPy Spatial Transformations with 60 FPS inertia physics.
"""

import math
import os
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np

from ui.mesh_3d_engine import Mesh3D, MeshLoader, HolographicInterferenceEngine


class ProjectorMeshLibrary:
    """Provides expanded procedural 3D models tailored for optical projection."""

    @classmethod
    def get_mesh(cls, model_name: str) -> Mesh3D:
        name = model_name.lower().strip()

        if name == "gauntlet":
            # Repulsor Gauntlet 3D Wireframe
            nodes = [
                # Palm & Repulsor Emitter (0..5)
                (0, 0, 10), (-15, -10, 8), (15, -10, 8), (15, 20, 8), (-15, 20, 8), (0, 5, 12),
                # Repulsor Core Ring (6..13)
            ]
            for i in range(8):
                ang = i * (math.pi * 2 / 8)
                nodes.append((8 * math.cos(ang), 5 + 8 * math.sin(ang), 14))

            # Wrist & Forearm Cuff (14..21)
            for z in [-25, -60]:
                for ang_idx in range(4):
                    a = ang_idx * (math.pi / 2) + (math.pi / 4)
                    nodes.append((22 * math.cos(a), 22 * math.sin(a), z))

            # 5 Articulated Fingers (Thumb, Index, Middle, Ring, Pinky)
            # Thumb (22..24)
            nodes.extend([(-22, 10, 6), (-32, 18, 4), (-40, 24, 2)])
            # Index (25..27)
            nodes.extend([(-12, 32, 6), (-14, 46, 4), (-15, 58, 2)])
            # Middle (28..30)
            nodes.extend([(0, 34, 6), (0, 50, 4), (0, 64, 2)])
            # Ring (31..33)
            nodes.extend([(12, 32, 6), (14, 46, 4), (15, 58, 2)])
            # Pinky (34..36)
            nodes.extend([(22, 28, 6), (26, 40, 4), (28, 50, 2)])

            edges = [
                # Palm plate
                (1, 2), (2, 3), (3, 4), (4, 1), (0, 1), (0, 2), (0, 3), (0, 4),
                # Repulsor emitter circle
                (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 12), (12, 13), (13, 6),
                (5, 6), (5, 8), (5, 10), (5, 12),
                # Wrist cuffs
                (14, 15), (15, 16), (16, 17), (17, 14),
                (18, 19), (19, 20), (20, 21), (21, 18),
                (14, 18), (15, 19), (16, 20), (17, 21),
                (1, 14), (2, 15), (3, 16), (4, 17),
                # Fingers
                (1, 22), (22, 23), (23, 24),
                (4, 25), (25, 26), (26, 27),
                (3, 28), (28, 29), (29, 30),
                (3, 31), (31, 32), (32, 33),
                (2, 34), (34, 35), (35, 36)
            ]
            highlights = [5, 6, 7, 8, 9, 10, 11, 12, 13, 24, 27, 30, 33, 36]
            mesh = Mesh3D("Repulsor Gauntlet", np.array(nodes), edges, highlight_nodes=highlights)
            mesh.normalize(65.0)
            return mesh

        elif name == "emitter":
            # Conical Holo-Projector Emitter Base & Laser Lenses
            nodes = []
            edges = []
            # Base Platform Rings
            for r, z in [(55, -45), (45, -30), (30, -10), (15, 15), (5, 45)]:
                start_i = len(nodes)
                for seg in range(12):
                    ang = seg * (math.pi * 2 / 12)
                    nodes.append([r * math.cos(ang), r * math.sin(ang), z])
                for seg in range(12):
                    edges.append((start_i + seg, start_i + ((seg + 1) % 12)))

            # Vertical Emitter Ribs
            for rib in range(6):
                idx0 = rib * 2
                idx1 = 12 + rib * 2
                idx2 = 24 + rib * 2
                idx3 = 36 + rib * 2
                idx4 = 48 + rib * 2
                edges.extend([(idx0, idx1), (idx1, idx2), (idx2, idx3), (idx3, idx4)])

            # Holographic Apex Crystal
            apex_idx = len(nodes)
            nodes.append([0, 0, 65])
            for i in range(48, 60):
                edges.append((i, apex_idx))

            highlights = [apex_idx] + list(range(48, 60))
            mesh = Mesh3D("Holo-Lens Emitter", np.array(nodes), edges, highlight_nodes=highlights)
            mesh.normalize(65.0)
            return mesh

        # Fallback to standard procedural meshes from MeshLoader
        return MeshLoader.get_procedural_mesh(name)


class Projector3DEngine:
    """
    Core Optical 3D Rendering and Projection Pipeline.
    """

    PALETTE_COLORS = {
        "stark_cyan": {
            "name": "Stark Cyan",
            "primary": "#00f0ff",
            "glow": "#00a2ff",
            "secondary": "#ffd700",
            "bg": "#000000",
            "white": "#ffffff",
        },
        "mark_crimson": {
            "name": "Mark Crimson",
            "primary": "#ff2a55",
            "glow": "#ff5577",
            "secondary": "#ffb700",
            "bg": "#000000",
            "white": "#ffffff",
        },
        "quantum_emerald": {
            "name": "Quantum Emerald",
            "primary": "#00ff9d",
            "glow": "#00cc7a",
            "secondary": "#00e5ff",
            "bg": "#000000",
            "white": "#ffffff",
        },
        "plasma_amber": {
            "name": "Plasma Amber",
            "primary": "#ffaa00",
            "glow": "#ff7700",
            "secondary": "#ffff55",
            "bg": "#000000",
            "white": "#ffffff",
        },
        "ultraviolet_violet": {
            "name": "Ultraviolet",
            "primary": "#bb44ff",
            "glow": "#8822ee",
            "secondary": "#00f0ff",
            "bg": "#000000",
            "white": "#ffffff",
        },
    }

    def __init__(self):
        self.active_mesh: Mesh3D = ProjectorMeshLibrary.get_mesh("helmet")
        self.yaw: float = 0.0
        self.pitch: float = 0.2
        self.scale: float = 1.0
        self.auto_spin: bool = True
        self.spin_speed: float = 0.015

        # Parallax for stereoscopic 3D
        self.parallax_offset: float = 6.0

        # Physical Momentum & Damping
        self.vel_yaw: float = 0.0
        self.vel_pitch: float = 0.0
        self.friction: float = 0.94

        # 4-Corner Bilinear Keystone Correction & Calibration
        self.keystone_corners: Dict[str, Tuple[float, float]] = {
            "TL": (0.0, 0.0),
            "TR": (1.0, 0.0),
            "BR": (1.0, 1.0),
            "BL": (0.0, 1.0),
        }
        self.keystone_enabled: bool = True
        self.calibration_mode: bool = False
        self.active_corner: str = "TL"

        # Holographic Optical Wave & Video Interference Engine
        self.interference: HolographicInterferenceEngine = HolographicInterferenceEngine()

    def set_mesh(self, mesh_or_name: Any):
        """Sets active mesh by name or Mesh3D object."""
        if isinstance(mesh_or_name, str):
            self.active_mesh = ProjectorMeshLibrary.get_mesh(mesh_or_name)
        elif isinstance(mesh_or_name, Mesh3D):
            self.active_mesh = mesh_or_name

    def set_keystone_corner(self, corner: str, x_norm: float, y_norm: float):
        """Sets normalized position [0..1] of a keystone corner."""
        c = corner.upper().strip()
        if c in self.keystone_corners:
            self.keystone_corners[c] = (max(0.0, min(1.0, float(x_norm))), max(0.0, min(1.0, float(y_norm))))

    def adjust_keystone_corner(self, corner: str, dx: float, dy: float):
        """Nudges the coordinates of a keystone corner."""
        c = corner.upper().strip()
        if c in self.keystone_corners:
            ox, oy = self.keystone_corners[c]
            self.keystone_corners[c] = (max(0.0, min(1.0, ox + dx)), max(0.0, min(1.0, oy + dy)))

    def cycle_keystone_corner(self) -> str:
        """Cycles active keystone calibration corner: TL -> TR -> BR -> BL."""
        corners = ["TL", "TR", "BR", "BL"]
        idx = (corners.index(self.active_corner) + 1) % len(corners) if self.active_corner in corners else 0
        self.active_corner = corners[idx]
        return self.active_corner

    def reset_keystone(self):
        """Resets keystone calibration warp to standard rectangle."""
        self.keystone_corners = {
            "TL": (0.0, 0.0),
            "TR": (1.0, 0.0),
            "BR": (1.0, 1.0),
            "BL": (0.0, 1.0),
        }

    def apply_keystone(
        self,
        screen_x: np.ndarray,
        screen_y: np.ndarray,
        w: int,
        h: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Applies 4-corner bilinear warp interpolation to pre-distort projection
        for non-perpendicular surfaces, glass prisms, and trapezoidal screens.
        """
        if not self.keystone_enabled or len(screen_x) == 0:
            return screen_x, screen_y

        u = np.clip(screen_x / max(w, 1), 0.0, 1.0)
        v = np.clip(screen_y / max(h, 1), 0.0, 1.0)

        tl_x, tl_y = self.keystone_corners["TL"][0] * w, self.keystone_corners["TL"][1] * h
        tr_x, tr_y = self.keystone_corners["TR"][0] * w, self.keystone_corners["TR"][1] * h
        br_x, br_y = self.keystone_corners["BR"][0] * w, self.keystone_corners["BR"][1] * h
        bl_x, bl_y = self.keystone_corners["BL"][0] * w, self.keystone_corners["BL"][1] * h

        top_x = (1.0 - u) * tl_x + u * tr_x
        top_y = (1.0 - u) * tl_y + u * tr_y
        bot_x = (1.0 - u) * bl_x + u * br_x
        bot_y = (1.0 - u) * bl_y + u * br_y

        warped_x = (1.0 - v) * top_x + v * bot_x
        warped_y = (1.0 - v) * top_y + v * bot_y

        return warped_x, warped_y

    def render_keystone_calibration_overlay(
        self,
        canvas: Any,
        w: int,
        h: int,
        primary_color: str = "#00f0ff",
        secondary_color: str = "#ffd700",
    ):
        """Renders interactive 4-corner keystone bounding grid and handles."""
        if not self.calibration_mode:
            return

        corners_px = {
            c: (int(self.keystone_corners[c][0] * w), int(self.keystone_corners[c][1] * h))
            for c in ["TL", "TR", "BR", "BL"]
        }

        # Quad Outline
        pts = [
            corners_px["TL"][0], corners_px["TL"][1],
            corners_px["TR"][0], corners_px["TR"][1],
            corners_px["BR"][0], corners_px["BR"][1],
            corners_px["BL"][0], corners_px["BL"][1],
        ]
        canvas.create_polygon(*pts, outline=primary_color, fill="", width=2, dash=(6, 4))

        # Diagonal Crosshair lines
        canvas.create_line(corners_px["TL"][0], corners_px["TL"][1], corners_px["BR"][0], corners_px["BR"][1], fill=primary_color, dash=(2, 6))
        canvas.create_line(corners_px["TR"][0], corners_px["TR"][1], corners_px["BL"][0], corners_px["BL"][1], fill=primary_color, dash=(2, 6))

        # Corner calibration handles
        for c, (px, py) in corners_px.items():
            is_active = (c == self.active_corner)
            h_col = secondary_color if is_active else primary_color
            r = 10 if is_active else 6
            canvas.create_oval(px - r, py - r, px + r, py + r, outline=h_col, width=2 if is_active else 1, fill="#000000")
            canvas.create_text(px + (14 if "L" in c else -14), py + (14 if "T" in c else -14), text=f"[{c}]", font=("Consolas", 9, "bold"), fill=h_col)

        # Center Status Banner
        canvas.create_text(
            w // 2, 45,
            text=f"⫸ KEYSTONE CALIBRATION MODE: ACTIVE [{self.active_corner}] (ARROWS: WARP | TAB: CYCLE | R: RESET | K: EXIT)",
            font=("Consolas", 10, "bold"),
            fill=secondary_color,
        )

    def update_physics(self):
        """Advances rotational physics, momentum, and optical wave interference."""
        if self.auto_spin:
            self.yaw = (self.yaw + self.spin_speed) % (2 * math.pi)
        else:
            self.yaw = (self.yaw + self.vel_yaw) % (2 * math.pi)
            self.pitch += self.vel_pitch
            self.vel_yaw *= self.friction
            self.vel_pitch *= self.friction
            if abs(self.vel_yaw) < 1e-4:
                self.vel_yaw = 0.0
            if abs(self.vel_pitch) < 1e-4:
                self.vel_pitch = 0.0

        self.pitch = max(-1.2, min(1.2, self.pitch))

        if hasattr(self, "interference") and self.interference:
            self.interference.update(dt=0.016)

    def _transform_vertices(
        self,
        yaw: float,
        pitch: float,
        scale: float,
        fov: float = 260.0,
        distance: float = 290.0,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Rotates and projects 3D vertices using vectorized trigonometry.
        Returns: (proj_x, proj_y, depths)
        """
        mesh = self.active_mesh
        if mesh is None or len(mesh.vertices) == 0:
            return np.array([]), np.array([]), np.array([])

        verts = mesh.vertices * scale

        cos_y, sin_y = math.cos(yaw), math.sin(yaw)
        cos_p, sin_p = math.cos(pitch), math.sin(pitch)

        x = verts[:, 0]
        y = verts[:, 1]
        z = verts[:, 2]

        # Rotate around Y (Yaw)
        x1 = x * cos_y + z * sin_y
        y1 = y
        z1 = -x * sin_y + z * cos_y

        # Rotate around X (Pitch)
        x2 = x1
        y2 = y1 * cos_p - z1 * sin_p
        z2 = y1 * sin_p + z1 * cos_p

        # Perspective Projection
        depth = z2 + distance
        depth = np.maximum(depth, 10.0)
        proj_scale = fov / depth

        px = x2 * proj_scale
        py = -y2 * proj_scale

        return px, py, depth

    def render_standard(
        self,
        canvas: Any,
        cx: int,
        cy: int,
        palette_key: str = "stark_cyan",
        audio_energy: float = 0.0,
        scale_mod: float = 1.0,
    ):
        """
        Renders standard high-lux holographic beam with multi-pass bloom and depth sorting.
        """
        colors = self.PALETTE_COLORS.get(palette_key, self.PALETTE_COLORS["stark_cyan"])
        mesh = self.active_mesh
        if mesh is None or len(mesh.vertices) == 0:
            return

        px, py, depth = self._transform_vertices(self.yaw, self.pitch, self.scale * scale_mod)
        if len(px) == 0:
            return

        screen_x = cx + px
        screen_y = cy + py

        w = max(100, cx * 2)
        h = max(100, cy * 2)
        if self.keystone_enabled:
            screen_x, screen_y = self.apply_keystone(screen_x, screen_y, w, h)

        # Z-Sort Edges (Painter's algorithm)
        edge_depths = []
        for i, j in mesh.edges:
            d_avg = float(depth[i] + depth[j]) / 2.0
            edge_depths.append((d_avg, i, j))
        edge_depths.sort(key=lambda item: item[0], reverse=True)

        pulse = 1.0 + min(1.5, audio_energy * 2.5)

        for d_avg, i, j in edge_depths:
            x_a, y_a = screen_x[i], screen_y[i]
            x_b, y_b = screen_x[j], screen_y[j]

            is_hl = (i in mesh.highlight_nodes) and (j in mesh.highlight_nodes)
            base_col = colors["secondary"] if is_hl else colors["primary"]

            # Bloom halo pass
            if pulse > 1.15:
                canvas.create_line(x_a, y_a, x_b, y_b, fill=colors["glow"], width=int(3 * pulse))

            # Main filament
            canvas.create_line(x_a, y_a, x_b, y_b, fill=base_col, width=2 if is_hl else 1)

            # Core white hot laser pass
            if is_hl or audio_energy > 0.3:
                canvas.create_line(x_a, y_a, x_b, y_b, fill=colors["white"], width=1)

        # Highlight vertex points
        for idx in range(len(screen_x)):
            is_hl = idx in mesh.highlight_nodes
            col = colors["secondary"] if is_hl else colors["primary"]
            canvas.create_oval(
                screen_x[idx] - 1.5, screen_y[idx] - 1.5,
                screen_x[idx] + 1.5, screen_y[idx] + 1.5,
                fill=col, outline=""
            )

        # Video Holographic Interference & Laser Scanline Sweep
        if hasattr(self, "interference") and self.interference:
            self.interference.render_overlay(
                canvas=canvas,
                cx=cx,
                cy=cy,
                width=int(240 * self.scale * scale_mod),
                height=int(240 * self.scale * scale_mod),
                primary_color=colors["primary"],
                secondary_color=colors["secondary"],
                audio_energy=audio_energy,
            )

        # Keystone Calibration Overlay
        if self.calibration_mode:
            self.render_keystone_calibration_overlay(canvas, w, h, colors["primary"], colors["secondary"])

    def render_pyramid_4way(
        self,
        canvas: Any,
        w: int,
        h: int,
        palette_key: str = "stark_cyan",
        audio_energy: float = 0.0,
    ):
        """
        Renders Pepper's Ghost 4-Way Holographic Pyramid projection.
        Divides display into North, South, East, West quadrants rotated 90 degrees each.
        """
        colors = self.PALETTE_COLORS.get(palette_key, self.PALETTE_COLORS["stark_cyan"])
        mesh = self.active_mesh
        if mesh is None or len(mesh.vertices) == 0:
            return

        cx, cy = w // 2, h // 2
        quad_radius = min(w, h) * 0.28
        quad_scale = 0.72

        # Draw Center Diamond Apex Marker
        diamond_s = min(w, h) * 0.08
        canvas.create_polygon(
            cx, cy - diamond_s,
            cx + diamond_s, cy,
            cx, cy + diamond_s,
            cx - diamond_s, cy,
            outline=colors["glow"], fill="#000000", width=1
        )
        canvas.create_line(cx - 10, cy, cx + 10, cy, fill=colors["glow"], width=1)
        canvas.create_line(cx, cy - 10, cx, cy + 10, fill=colors["glow"], width=1)

        # 4 Quadrants: (Angle offset in radians, Center X, Center Y)
        # North (0 rad), East (PI/2 rad), South (PI rad), West (3PI/2 rad)
        quadrants = [
            (0.0, cx, cy - quad_radius),               # North: Upright
            (math.pi / 2, cx + quad_radius, cy),      # East: Rotated 90 deg clockwise
            (math.pi, cx, cy + quad_radius),          # South: Rotated 180 deg
            (3 * math.pi / 2, cx - quad_radius, cy),  # West: Rotated 270 deg
        ]

        px, py, depth = self._transform_vertices(self.yaw, self.pitch, self.scale * quad_scale)
        if len(px) == 0:
            return

        for quad_rot, q_cx, q_cy in quadrants:
            cos_q, sin_q = math.cos(quad_rot), math.sin(quad_rot)
            # 2D screen coordinate rotation around quadrant center
            rot_px = px * cos_q - py * sin_q
            rot_py = px * sin_q + py * cos_q

            screen_x = q_cx + rot_px
            screen_y = q_cy + rot_py

            if self.keystone_enabled:
                screen_x, screen_y = self.apply_keystone(screen_x, screen_y, w, h)

            # Render wireframe edges
            for i, j in mesh.edges:
                is_hl = (i in mesh.highlight_nodes) and (j in mesh.highlight_nodes)
                col = colors["secondary"] if is_hl else colors["primary"]
                canvas.create_line(
                    screen_x[i], screen_y[i],
                    screen_x[j], screen_y[j],
                    fill=col, width=1
                )

        # Optical Wave Interference Fringes
        if hasattr(self, "interference") and self.interference:
            self.interference.render_overlay(
                canvas=canvas,
                cx=cx,
                cy=cy,
                width=int(diamond_s * 4),
                height=int(diamond_s * 4),
                primary_color=colors["primary"],
                secondary_color=colors["secondary"],
                audio_energy=audio_energy,
            )

        if self.calibration_mode:
            self.render_keystone_calibration_overlay(canvas, w, h, colors["primary"], colors["secondary"])

    def render_anaglyph_3d(
        self,
        canvas: Any,
        cx: int,
        cy: int,
        palette_key: str = "stark_cyan",
        audio_energy: float = 0.0,
    ):
        """
        Renders real stereoscopic Anaglyph 3D projection for Red/Cyan 3D glasses.
        Dual perspective cameras offset by +/- parallax_offset.
        """
        mesh = self.active_mesh
        if mesh is None or len(mesh.vertices) == 0:
            return

        parallax = self.parallax_offset

        # Left Eye (Red) Camera
        left_yaw = self.yaw - 0.025
        px_l, py_l, _ = self._transform_vertices(left_yaw, self.pitch, self.scale)

        # Right Eye (Cyan) Camera
        right_yaw = self.yaw + 0.025
        px_r, py_r, _ = self._transform_vertices(right_yaw, self.pitch, self.scale)

        if len(px_l) == 0 or len(px_r) == 0:
            return

        # Screen coordinates with lateral ocular displacement
        scr_xl = (cx - parallax) + px_l
        scr_yl = cy + py_l

        scr_xr = (cx + parallax) + px_r
        scr_yr = cy + py_r

        w = max(100, cx * 2)
        h = max(100, cy * 2)
        if self.keystone_enabled:
            scr_xl, scr_yl = self.apply_keystone(scr_xl, scr_yl, w, h)
            scr_xr, scr_yr = self.apply_keystone(scr_xr, scr_yr, w, h)

        # Pass 1: Left Eye Red Channel (#ff0044)
        for i, j in mesh.edges:
            canvas.create_line(
                scr_xl[i], scr_yl[i],
                scr_xl[j], scr_yl[j],
                fill="#ff0044", width=2
            )

        # Pass 2: Right Eye Cyan Channel (#00f0ff)
        for i, j in mesh.edges:
            canvas.create_line(
                scr_xr[i], scr_yr[i],
                scr_xr[j], scr_yr[j],
                fill="#00f0ff", width=2
            )

        # Pass 3: Optical Synthesis Center White Hot Nodes
        for idx in range(len(px_l)):
            if idx in mesh.highlight_nodes:
                mid_x = (scr_xl[idx] + scr_xr[idx]) / 2.0
                mid_y = (scr_yl[idx] + scr_yr[idx]) / 2.0
                canvas.create_oval(mid_x - 2, mid_y - 2, mid_x + 2, mid_y + 2, fill="#ffffff", outline="")

        # Video Holographic Interference
        if hasattr(self, "interference") and self.interference:
            self.interference.render_overlay(
                canvas=canvas,
                cx=cx,
                cy=cy,
                width=int(240 * self.scale),
                height=int(240 * self.scale),
                primary_color="#00f0ff",
                secondary_color="#ff2a55",
                audio_energy=audio_energy,
            )

        if self.calibration_mode:
            self.render_keystone_calibration_overlay(canvas, w, h, "#00f0ff", "#ffd700")


# Global singleton instance
projector_3d_engine = Projector3DEngine()
