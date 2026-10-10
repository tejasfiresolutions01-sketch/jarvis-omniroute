"""
J.A.R.V.I.S. High-Performance 3D Holographic Mesh Engine & Neon Bloom Shader Matrix.
Features:
1. OBJ & STL 3D Asset Loader: Programmatic parsing of standard Wavefront .obj and Stereolithography .stl files.
2. Procedural Sci-Fi 3D Meshes: Iron Man Mark-85 Helmet, Arc Reactor, Celestial Globe, 4D Tesseract, Stark Jet Drone.
3. Multi-Pass Neon Bloom & Laser Core Shader Simulation: Creates authentic Stark holographic glow on pitch-black canvas.
4. Depth-Buffered Perspective Projection (Z-sorted edges with atmospheric depth fading).
5. Rotational Physics & Momentum Engine: Smooth 60 FPS interpolation with mouse fling inertia damping.
6. Audio Energy Modulation: Dynamic neon pulse amplitude linked to J.A.R.V.I.S. speech/listening resonance.
7. 100% Free, zero cloud dependency, vectorized NumPy 3D transforms.
"""

import math
import os
import re
import struct
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


class Mesh3D:
    """Represents a 3D wireframe mesh comprising vertices, edges, and optional feature highlights."""

    def __init__(self, name: str, vertices: np.ndarray, edges: List[Tuple[int, int]], highlight_nodes: Optional[List[int]] = None):
        self.name = name
        self.vertices = vertices.astype(np.float32)  # Shape (N, 3)
        self.edges = edges
        self.highlight_nodes = set(highlight_nodes or [])

    def normalize(self, target_radius: float = 65.0):
        """Centers vertices around origin and scales bounding sphere to target radius."""
        if len(self.vertices) == 0:
            return
        center = np.mean(self.vertices, axis=0)
        self.vertices -= center
        dists = np.linalg.norm(self.vertices, axis=1)
        max_dist = np.max(dists) if len(dists) > 0 else 1.0
        if max_dist > 1e-5:
            self.vertices = (self.vertices / max_dist) * target_radius


class MeshLoader:
    """Parses standard 3D mesh formats and generates procedural Stark models."""

    @staticmethod
    def load_obj(file_path: str) -> Optional[Mesh3D]:
        """Parses a Wavefront .obj file into a normalized wireframe Mesh3D."""
        path = Path(file_path)
        if not path.is_file():
            return None

        vertices = []
        edges = set()

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("v "):
                        parts = line.split()
                        if len(parts) >= 4:
                            vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    elif line.startswith("f "):
                        parts = line.split()[1:]
                        face_indices = []
                        for p in parts:
                            idx_str = p.split("/")[0]
                            if idx_str:
                                idx = int(idx_str) - 1  # 1-indexed to 0-indexed
                                face_indices.append(idx)
                        for i in range(len(face_indices)):
                            i1 = face_indices[i]
                            i2 = face_indices[(i + 1) % len(face_indices)]
                            if i1 != i2:
                                edges.add(tuple(sorted((i1, i2))))

            if vertices:
                mesh = Mesh3D(path.stem, np.array(vertices), list(edges))
                mesh.normalize()
                return mesh
        except Exception:
            pass
        return None

    @staticmethod
    def load_stl(file_path: str) -> Optional[Mesh3D]:
        """Parses an ASCII or Binary STL file into a normalized wireframe Mesh3D."""
        path = Path(file_path)
        if not path.is_file():
            return None

        vertices = []
        edges = set()
        v_map = {}

        def get_v_idx(vx, vy, vz):
            key = (round(vx, 3), round(vy, 3), round(vz, 3))
            if key not in v_map:
                v_map[key] = len(vertices)
                vertices.append([vx, vy, vz])
            return v_map[key]

        try:
            # Check if binary STL
            with open(path, "rb") as f:
                header = f.read(80)
                if len(header) == 80:
                    num_triangles_bytes = f.read(4)
                    if len(num_triangles_bytes) == 4:
                        num_triangles = struct.unpack("<I", num_triangles_bytes)[0]
                        expected_size = 84 + num_triangles * 50
                        if path.stat().st_size == expected_size:
                            # Binary STL
                            for _ in range(num_triangles):
                                f.read(12)  # normal
                                v1 = struct.unpack("<3f", f.read(12))
                                v2 = struct.unpack("<3f", f.read(12))
                                v3 = struct.unpack("<3f", f.read(12))
                                f.read(2)  # attribute byte count

                                i1 = get_v_idx(*v1)
                                i2 = get_v_idx(*v2)
                                i3 = get_v_idx(*v3)
                                edges.add(tuple(sorted((i1, i2))))
                                edges.add(tuple(sorted((i2, i3))))
                                edges.add(tuple(sorted((i3, i1))))

                            if vertices:
                                mesh = Mesh3D(path.stem, np.array(vertices), list(edges))
                                mesh.normalize()
                                return mesh

            # Fallback ASCII STL
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                tri = []
                for line in f:
                    line = line.strip().lower()
                    if line.startswith("vertex"):
                        parts = line.split()
                        if len(parts) >= 4:
                            tri.append(get_v_idx(float(parts[1]), float(parts[2]), float(parts[3])))
                    elif line.startswith("endfacet"):
                        if len(tri) == 3:
                            edges.add(tuple(sorted((tri[0], tri[1]))))
                            edges.add(tuple(sorted((tri[1], tri[2]))))
                            edges.add(tuple(sorted((tri[2], tri[0]))))
                        tri = []

            if vertices:
                mesh = Mesh3D(path.stem, np.array(vertices), list(edges))
                mesh.normalize()
                return mesh
        except Exception:
            pass
        return None

    @classmethod
    def get_procedural_mesh(cls, model_name: str) -> Mesh3D:
        """Constructs high-definition procedural sci-fi holographic wireframe models."""
        m = model_name.lower().strip()

        if m == "helmet":
            # High-definition Mark-85 Iron Man Helmet Wireframe
            nodes = [
                # Forehead / Crest (0..3)
                (-40, 60, 20), (40, 60, 20), (25, 75, 10), (-25, 75, 10),
                # Brow / Temple (4..7)
                (-55, 30, 25), (55, 30, 25), (35, 35, 45), (-35, 35, 45),
                # Left Eye (8..11)
                (-32, 22, 48), (-12, 20, 52), (-14, 12, 50), (-30, 14, 46),
                # Right Eye (12..15)
                (12, 20, 52), (32, 22, 48), (30, 14, 46), (14, 12, 50),
                # Nose Bridge & Mouth Plate (16..19)
                (-10, 8, 54), (10, 8, 54), (8, -25, 52), (-8, -25, 52),
                # Cheeks (20..23)
                (-50, -5, 35), (50, -5, 35), (-45, -35, 25), (45, -35, 25),
                # Jaw & Chin (24..27)
                (-25, -55, 38), (25, -55, 38), (15, -65, 42), (-15, -65, 42),
                # Back Cranium (28..31)
                (-45, 50, -45), (45, 50, -45), (40, -40, -45), (-40, -40, -45),
                # Ear Pods (32..35)
                (-60, 10, 0), (-60, -15, 0), (60, 10, 0), (60, -15, 0)
            ]
            edges = [
                (0, 1), (1, 2), (2, 3), (3, 0),
                (0, 4), (1, 5), (4, 7), (5, 6), (7, 6),
                (7, 8), (7, 9), (6, 12), (6, 13),
                (8, 9), (9, 10), (10, 11), (11, 8),
                (12, 13), (13, 14), (14, 15), (15, 12),
                (9, 16), (12, 17), (16, 17), (16, 19), (17, 18), (19, 18),
                (4, 20), (5, 21), (20, 22), (21, 23),
                (22, 24), (23, 25), (24, 27), (25, 26), (27, 26),
                (0, 28), (1, 29), (28, 29), (29, 30), (30, 31), (31, 28), (22, 31), (23, 30),
                (4, 32), (20, 33), (32, 33), (5, 34), (21, 35), (34, 35)
            ]
            eye_nodes = [8, 9, 10, 11, 12, 13, 14, 15]
            mesh = Mesh3D("Mark-85 Helmet", np.array(nodes), edges, highlight_nodes=eye_nodes)
            mesh.normalize(65.0)
            return mesh

        elif m == "reactor":
            # Multi-layer Concentric Arc Reactor with Core Emitter
            nodes = []
            edges = []
            # 5 Outer & Mid Energy Rings
            for r_rad, r_y in [(62, 0), (50, 15), (50, -15), (32, 28), (32, -28), (18, 0)]:
                start_idx = len(nodes)
                for seg in range(16):
                    ang = seg * (math.pi * 2 / 16)
                    nodes.append([r_rad * math.cos(ang), r_y, r_rad * math.sin(ang)])
                for seg in range(16):
                    edges.append((start_idx + seg, start_idx + ((seg + 1) % 16)))

            # Radial Energy Spokes
            for s in range(8):
                ang = s * (math.pi * 2 / 8)
                idx_inner = len(nodes)
                nodes.append([18 * math.cos(ang), 0, 18 * math.sin(ang)])
                nodes.append([62 * math.cos(ang), 0, 62 * math.sin(ang)])
                edges.append((idx_inner, idx_inner + 1))

            mesh = Mesh3D("Arc Reactor", np.array(nodes), edges)
            mesh.normalize(65.0)
            return mesh

        elif m == "tesseract":
            # 4D Hypercube / Tesseract
            nodes = []
            s_out = 58
            s_in = 30
            for z in [-s_out, s_out]:
                for y in [-s_out, s_out]:
                    for x in [-s_out, s_out]:
                        nodes.append([x, y, z])
            for z in [-s_in, s_in]:
                for y in [-s_in, s_in]:
                    for x in [-s_in, s_in]:
                        nodes.append([x, y, z])

            cube_edges = [
                (0, 1), (1, 3), (3, 2), (2, 0),
                (4, 5), (5, 7), (7, 6), (6, 4),
                (0, 4), (1, 5), (2, 6), (3, 7)
            ]
            edges = list(cube_edges)
            for e1, e2 in cube_edges:
                edges.append((e1 + 8, e2 + 8))
            for i in range(8):
                edges.append((i, i + 8))

            mesh = Mesh3D("4D Tesseract", np.array(nodes), edges)
            mesh.normalize(65.0)
            return mesh

        elif m in ["drone", "jet", "stark_jet"]:
            # Stark Industries Hypersonic Drone Wireframe
            nodes = [
                # Nose & Cockpit (0..3)
                (0, 75, 5), (0, 35, 18), (-12, 20, 10), (12, 20, 10),
                # Fuselage Main (4..7)
                (-18, -20, 8), (18, -20, 8), (-12, -60, 5), (12, -60, 5),
                # Left Delta Wing (8..11)
                (-75, -45, 0), (-65, -55, 0), (-35, -20, 4), (-25, -10, 6),
                # Right Delta Wing (12..15)
                (75, -45, 0), (65, -55, 0), (35, -20, 4), (25, -10, 6),
                # Twin Vertical Stabilizers (16..19)
                (-15, -65, 25), (-18, -45, 18), (15, -65, 25), (18, -45, 18),
                # Twin Turbines / Thrusters (20..23)
                (-8, -68, 2), (-14, -68, 2), (8, -68, 2), (14, -68, 2)
            ]
            edges = [
                (0, 1), (1, 2), (1, 3), (2, 0), (3, 0), (2, 4), (3, 5), (4, 6), (5, 7), (6, 7),
                (2, 11), (11, 10), (10, 8), (8, 9), (9, 6),
                (3, 15), (15, 14), (14, 12), (12, 13), (13, 7),
                (6, 16), (16, 17), (17, 4), (7, 18), (18, 19), (19, 5),
                (20, 21), (22, 23)
            ]
            mesh = Mesh3D("Stark Drone", np.array(nodes), edges, highlight_nodes=[0, 1, 20, 21, 22, 23])
            mesh.normalize(65.0)
            return mesh

        elif m in ["neural_mesh", "neural", "network", "constellation"]:
            # J.A.R.V.I.S. Neural Architecture Constellation Mesh
            nodes = [
                (0, 0, 0),         # 0: Core Coordinator
                (35, 20, 25),      # 1: VAD Subsystem
                (-35, 20, 25),     # 2: Local SLM
                (0, 48, -20),      # 3: Cognitive Memory
                (-38, -20, 20),    # 4: Vision Copilot
                (38, -20, 20),     # 5: Autonomous Device Control
                (0, -42, 28),      # 6: Hologram Sentinel
                (28, 32, -35),     # 7: Consensus Reviewer
                (-28, 32, -35),    # 8: Business Automation
                (42, 0, -15),      # 9: System Orchestrator
                (-42, 0, -15),     # 10: Hugging Face Cognitive Hub
                (0, 0, 48)         # 11: Asimov Guard Sentinel
            ]
            for i in range(8):
                ang = i * (math.pi * 2 / 8)
                nodes.append((55 * math.cos(ang), 15 * math.sin(i * 1.5), 55 * math.sin(ang)))

            edges = [
                (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (0, 9), (0, 10), (0, 11),
                (1, 2), (2, 4), (4, 6), (6, 5), (5, 1),
                (3, 7), (7, 9), (9, 5), (3, 8), (8, 10), (10, 4),
                (11, 1), (11, 2), (11, 6), (7, 8), (9, 10)
            ]
            for i in range(8):
                idx = 12 + i
                next_idx = 12 + ((i + 1) % 8)
                edges.append((idx, next_idx))
                edges.append((idx, (i % 11) + 1))

            mesh = Mesh3D("Neural Architecture Mesh", np.array(nodes), edges, highlight_nodes=[0, 11, 1, 2, 3])
            mesh.normalize(65.0)
            return mesh

        elif m in ["planetary_radar", "radar", "defense"]:
            # Planetary Defense Radar Sphere with sweep line and target blips
            nodes = []
            edges = []
            for r in [20, 40, 60]:
                start = len(nodes)
                for seg in range(16):
                    ang = seg * (math.pi * 2 / 16)
                    nodes.append([r * math.cos(ang), 0, r * math.sin(ang)])
                for seg in range(16):
                    edges.append((start + seg, start + ((seg + 1) % 16)))

            c_start = len(nodes)
            nodes.extend([(65, 0, 0), (-65, 0, 0), (0, 0, 65), (0, 0, -65)])
            edges.extend([(c_start, c_start + 1), (c_start + 2, c_start + 3)])

            for y_off in [-30, 30]:
                r = 50
                start = len(nodes)
                for seg in range(12):
                    ang = seg * (math.pi * 2 / 12)
                    nodes.append([r * math.cos(ang), y_off, r * math.sin(ang)])
                for seg in range(12):
                    edges.append((start + seg, start + ((seg + 1) % 12)))

            blips_start = len(nodes)
            nodes.extend([(30, 15, 30), (-25, 25, -20), (35, -20, -30), (0, 35, 45)])
            highlights = list(range(blips_start, blips_start + 4))

            mesh = Mesh3D("Planetary Defense Radar", np.array(nodes), edges, highlight_nodes=highlights)
            mesh.normalize(65.0)
            return mesh

        elif m in ["quantum_dna", "dna", "double_helix"]:
            # Procedural Quantum DNA Double Helix
            nodes = []
            edges = []
            num_steps = 20
            radius = 28.0
            height_span = 120.0
            highlights = []

            for i in range(num_steps):
                t = i / (num_steps - 1)
                y = (t - 0.5) * height_span
                angle = t * math.pi * 3.5

                xa = radius * math.cos(angle)
                za = radius * math.sin(angle)
                xb = radius * math.cos(angle + math.pi)
                zb = radius * math.sin(angle + math.pi)

                idx_a = len(nodes)
                nodes.append([xa, y, za])
                idx_b = len(nodes)
                nodes.append([xb, y, zb])

                edges.append((idx_a, idx_b))
                if i % 3 == 0:
                    highlights.extend([idx_a, idx_b])

                if i > 0:
                    edges.append((idx_a - 2, idx_a))
                    edges.append((idx_b - 2, idx_b))

            mesh = Mesh3D("Quantum DNA Helix", np.array(nodes), edges, highlight_nodes=highlights)
            mesh.normalize(65.0)
            return mesh

        elif m in ["acoustic_ribbon", "fft_terrain", "audio_ribbon", "ribbon", "acoustic"]:
            # 3D Acoustic FFT Ribbon Terrain Mesh: Audio-frequency spectral elevation waves
            nodes = []
            edges = []
            highlights = []
            cols = 16  # Frequency bands
            rows = 12  # Time-series decay slices
            dx = 120.0 / (cols - 1)
            dz = 100.0 / (rows - 1)

            for r in range(rows):
                z_pos = -50.0 + (r * dz)
                t_decay = math.exp(-0.16 * r)
                for c in range(cols):
                    x_pos = -60.0 + (c * dx)
                    omega1 = (c / cols) * math.pi * 2.5
                    omega2 = (r / rows) * math.pi * 1.8
                    y_val = (
                        math.sin(omega1) * 26.0 * t_decay
                        + math.sin(omega1 * 2.2 + 0.4) * 14.0 * t_decay
                        + math.cos(omega2) * 8.0
                    )
                    idx = len(nodes)
                    nodes.append([x_pos, y_val, z_pos])

                    # Highlight resonance peaks on foremost spectral ribbon
                    if r < 3 and (c in [3, 7, 11, 14]):
                        highlights.append(idx)

            for r in range(rows):
                for c in range(cols):
                    curr = (r * cols) + c
                    if c + 1 < cols:
                        edges.append((curr, curr + 1))
                    if r + 1 < rows:
                        edges.append((curr, curr + cols))
                    if c + 1 < cols and r + 1 < rows and (c % 2 == 0):
                        edges.append((curr, curr + cols + 1))

            mesh = Mesh3D("Acoustic FFT Ribbon Terrain", np.array(nodes), edges, highlight_nodes=highlights)
            mesh.normalize(65.0)
            return mesh

        else:  # "globe" default
            nodes = []
            edges = []
            # Latitude Circles
            for lat in [-50, -30, 0, 30, 50]:
                r_lat = 60 * math.cos(math.radians(lat))
                y_lat = 60 * math.sin(math.radians(lat))
                start_idx = len(nodes)
                for seg in range(16):
                    ang = seg * (math.pi * 2 / 16)
                    nodes.append([r_lat * math.cos(ang), y_lat, r_lat * math.sin(ang)])
                for seg in range(16):
                    edges.append((start_idx + seg, start_idx + ((seg + 1) % 16)))

            # Longitude Meridians
            for lon_seg in range(4):
                lon_ang = lon_seg * (math.pi / 4)
                start_idx = len(nodes)
                for seg in range(16):
                    ang = seg * (math.pi * 2 / 16)
                    nodes.append([60 * math.sin(ang) * math.cos(lon_ang), 60 * math.cos(ang), 60 * math.sin(ang) * math.sin(lon_ang)])
                for seg in range(16):
                    edges.append((start_idx + seg, start_idx + ((seg + 1) % 16)))

            mesh = Mesh3D("Celestial Globe", np.array(nodes), edges)
            mesh.normalize(65.0)
            return mesh


class HolographicInterferenceEngine:
    """
    Simulates optical laser wave interference, video transmission glitches,
    and cathodic scanline sweeps for authentic sci-fi volumetric display.
    """

    def __init__(self):
        self.enabled: bool = True
        self.interference_intensity: float = 0.45
        self.sweep_y: float = -120.0
        self.sweep_speed: float = 3.0
        self.glitch_active: bool = False
        self.glitch_dx: float = 0.0
        self._last_glitch_time: float = 0.0
        self.phase: float = 0.0

    def update(self, dt: float = 0.016, audio_energy: float = 0.0):
        """Advances scanline sweeps and calculates optical wave interference state."""
        self.phase += 0.06 + (audio_energy * 0.12)
        self.sweep_y += self.sweep_speed
        if self.sweep_y > 150.0:
            self.sweep_y = -150.0

        # Intermittent video holographic glitch interference
        now = time.time()
        if not self.glitch_active and (now - self._last_glitch_time > 2.5) and (audio_energy > 0.20 or np.random.rand() < 0.03):
            self.glitch_active = True
            self.glitch_dx = float(np.random.uniform(-12.0, 12.0))
            self._last_glitch_time = now
        elif self.glitch_active and (now - self._last_glitch_time > 0.12):
            self.glitch_active = False
            self.glitch_dx = 0.0

    def render_overlay(
        self,
        canvas: Any,
        cx: int,
        cy: int,
        width: int,
        height: int,
        primary_color: str = "#00f0ff",
        secondary_color: str = "#ff2a55",
        audio_energy: float = 0.0,
    ):
        """
        Renders optical interference fringes, laser scanline beam, and chromatic glitch slice.
        """
        if not self.enabled:
            return

        half_w = max(40, width // 2)
        half_h = max(40, height // 2)
        top = cy - half_h
        bottom = cy + half_h
        left = cx - half_w
        right = cx + half_w

        # 1. Optical Laser Sweep Beam
        beam_y = cy + int(self.sweep_y)
        if top <= beam_y <= bottom:
            pulse_w = 2 if audio_energy > 0.25 else 1
            canvas.create_line(left, beam_y, right, beam_y, fill=primary_color, width=pulse_w, dash=(8, 4))
            canvas.create_line(left + 2, beam_y + 1, right + 2, beam_y + 1, fill=secondary_color, width=1, dash=(4, 6))

        # 2. Holographic Glitch Jitter Slice
        if self.glitch_active and abs(self.glitch_dx) > 1.0:
            slice_y = cy + int(self.glitch_dx * 3) % max(1, half_h)
            slice_h = int(abs(self.glitch_dx) * 1.5) + 6
            canvas.create_rectangle(
                left + self.glitch_dx, slice_y - slice_h,
                right + self.glitch_dx, slice_y + slice_h,
                outline=secondary_color, width=1, dash=(3, 3)
            )

        # 3. Ambient Optical Wave Interference Fringes (Moiré)
        halo_radius = int(min(half_w, half_h) * (0.92 + 0.08 * math.sin(self.phase)))
        canvas.create_oval(
            cx - halo_radius, cy - halo_radius,
            cx + halo_radius, cy + halo_radius,
            outline=primary_color, width=1, dash=(2, 6)
        )


class Holographic3DRenderer:
    """
    Renders 3D meshes with multi-pass neon bloom, depth fading, and physics inertia.
    """

    def __init__(self):
        self.active_mesh: Mesh3D = MeshLoader.get_procedural_mesh("helmet")
        self.yaw: float = 0.0
        self.pitch: float = 0.2
        self.scale: float = 1.0

        # Inertia and rotation physics
        self.vel_yaw: float = 0.015
        self.vel_pitch: float = 0.0
        self.friction: float = 0.95
        self.auto_spin: bool = True
        self.bloom_enabled: bool = True
        self.interference: HolographicInterferenceEngine = HolographicInterferenceEngine()

    def set_mesh(self, mesh_or_name: Any):
        """Sets active mesh by name or Mesh3D object."""
        if isinstance(mesh_or_name, str):
            self.active_mesh = MeshLoader.get_procedural_mesh(mesh_or_name)
        elif isinstance(mesh_or_name, Mesh3D):
            self.active_mesh = mesh_or_name

    def load_custom_file(self, file_path: str) -> bool:
        """Loads .obj or .stl mesh file from disk."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".obj":
            m = MeshLoader.load_obj(file_path)
        elif ext == ".stl":
            m = MeshLoader.load_stl(file_path)
        else:
            return False

        if m:
            self.active_mesh = m
            return True
        return False

    def update_physics(self, dt: float = 0.016):
        """Updates yaw and pitch with rotational velocity and inertia damping."""
        if self.auto_spin:
            self.yaw += 0.015
        else:
            # Apply momentum inertia
            self.yaw += self.vel_yaw
            self.pitch += self.vel_pitch
            self.vel_yaw *= self.friction
            self.vel_pitch *= self.friction
            if abs(self.vel_yaw) < 1e-4:
                self.vel_yaw = 0.0
            if abs(self.vel_pitch) < 1e-4:
                self.vel_pitch = 0.0

        # Clamp pitch to avoid extreme gimbal flipping
        self.pitch = max(-1.2, min(1.2, self.pitch))

        # Advance optical interference
        if hasattr(self, "interference") and self.interference:
            self.interference.update(dt=dt)

    def project_and_render(
        self,
        canvas: Any,
        cx: int,
        cy: int,
        theme: Dict[str, str],
        audio_energy: float = 0.0,
        fov: float = 240.0,
        distance: float = 280.0,
    ):
        """
        Projects 3D mesh vertices and renders with neon bloom and depth fading.
        """
        mesh = self.active_mesh
        if mesh is None or len(mesh.vertices) == 0:
            return

        verts = mesh.vertices * self.scale

        # 3D Rotation matrices
        cos_y, sin_y = math.cos(self.yaw), math.sin(self.yaw)
        cos_p, sin_p = math.cos(self.pitch), math.sin(self.pitch)

        # Vectorized transform via NumPy
        # Yaw rotation around Y
        x = verts[:, 0]
        y = verts[:, 1]
        z = verts[:, 2]

        x1 = x * cos_y + z * sin_y
        y1 = y
        z1 = -x * sin_y + z * cos_y

        # Pitch rotation around X
        x2 = x1
        y2 = y1 * cos_p - z1 * sin_p
        z2 = y1 * sin_p + z1 * cos_p

        # Perspective projection
        depth = z2 + distance
        depth = np.maximum(depth, 10.0)
        proj_scale = fov / depth

        px = cx + x2 * proj_scale
        py = cy - y2 * proj_scale

        # Dynamic Audio Bloom Modulation
        pulse = 1.0 + min(1.5, audio_energy * 2.5)

        # Edge Depth Sorting (Painter's algorithm)
        edge_depths = []
        for i, j in mesh.edges:
            d_avg = float(depth[i] + depth[j]) / 2.0
            edge_depths.append((d_avg, i, j))

        # Sort far to near so foreground edges render sharply on top
        edge_depths.sort(key=lambda item: item[0], reverse=True)

        primary_col = theme.get("primary", "#00f0ff")
        glow_col = theme.get("glow", "#00a2ff")
        sec_col = theme.get("secondary", "#ffd700")

        for d_avg, i, j in edge_depths:
            x_a, y_a = px[i], py[i]
            x_b, y_b = px[j], py[j]

            is_highlight = (i in mesh.highlight_nodes) and (j in mesh.highlight_nodes)
            base_col = sec_col if is_highlight else primary_col

            # Multi-pass Neon Bloom:
            # Pass 1: Diffuse Outer Bloom Halo (if bloom enabled)
            if self.bloom_enabled and pulse > 1.1:
                halo_w = int(3 * pulse)
                canvas.create_line(x_a, y_a, x_b, y_b, fill=glow_col, width=halo_w)

            # Pass 2: Main Photon Filament
            main_w = 2 if is_highlight else 1
            canvas.create_line(x_a, y_a, x_b, y_b, fill=base_col, width=main_w)

            # Pass 3: White Hot Center Core on highlights or intense audio pulse
            if is_highlight or audio_energy > 0.35:
                canvas.create_line(x_a, y_a, x_b, y_b, fill="#ffffff", width=1)

        # Pass 4: Glowing Holographic Vertex Node Points
        for idx in range(len(px)):
            x_p, y_p = px[idx], py[idx]
            is_hl = idx in mesh.highlight_nodes
            node_col = sec_col if is_hl else primary_col
            canvas.create_oval(x_p - 1.5, y_p - 1.5, x_p + 1.5, y_p + 1.5, fill=node_col, outline="")

        # Pass 5: Sound-Reactive Orbital Particle Halo (Acoustic Aura)
        if audio_energy > 0.05 or self.bloom_enabled:
            halo_r = 75.0 * pulse
            num_halo_pts = 24
            ang_step = (math.pi * 2) / num_halo_pts
            for pt_idx in range(num_halo_pts):
                phi = pt_idx * ang_step + (self.yaw * 0.5)
                # 3D ring orbit in horizontal plane
                hx = halo_r * math.cos(phi)
                hz = halo_r * math.sin(phi)
                # Rotate with pitch
                hx2 = hx
                hy2 = -hz * sin_p
                hz2 = hz * cos_p
                h_depth = hz2 + distance
                h_scale = fov / max(h_depth, 10.0)
                sp_x = cx + hx2 * h_scale
                sp_y = cy - hy2 * h_scale
                dot_size = 1.0 + (pulse * 0.8)
                canvas.create_oval(
                    sp_x - dot_size, sp_y - dot_size,
                    sp_x + dot_size, sp_y + dot_size,
                    fill=glow_col, outline=""
                )

        # Pass 6: Video Holographic Interference & Laser Scanline Sweep
        self.interference.render_overlay(
            canvas=canvas,
            cx=cx,
            cy=cy,
            width=int(180 * self.scale),
            height=int(180 * self.scale),
            primary_color=primary_col,
            secondary_color=sec_col,
            audio_energy=audio_energy
        )


# Global singleton instance
holographic_3d = Holographic3DRenderer()
