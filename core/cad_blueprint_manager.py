"""
J.A.R.V.I.S. Holographic 3D CAD Blueprint & Engineering Asset Matrix.
Features:
1. High-Polygon 3D Asset Management (Wavefront .obj & Stereolithography .stl):
   - Catalogs and stores authentic Stark suit designs, Arc Reactor assemblies,
     aerospace airframes, and robotic kinematics under models/cad_3d/.
2. Procedural Sci-Fi CAD Synthesis Engine:
   - Programmatically synthesizes detailed 3D Wavefront meshes:
     - Mark 85 Full Tactical Armor
     - Arc Reactor Concentric Exploded Assembly
     - Stark Industries Hypersonic Drone Airframe
     - High-Definition Repulsor Gauntlet
     - Dum-E Robotic Arm Manipulator
3. Real-Time Mesh3D Converter:
   - Converts standard CAD OBJ/STL files into normalized, edge-buffered Mesh3D
     wireframe objects for the 3D Holographic Projector and Tactical HUD.
4. Engineering Bill of Materials (BOM) & Technical Dossiers:
   - Computes structural mass, alloy composition, thermal limits, and power requirements.
5. 100% Free Plan, zero cloud dependency, offline local filesystem storage.
"""

import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np

import config
from ui.mesh_3d_engine import Mesh3D

logger = logging.getLogger("CADBlueprintManager")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CAD_DIR = PROJECT_ROOT / "models" / "cad_3d"
CATALOG_FILE = CAD_DIR / "cad_catalog.json"


@dataclass
class CADBlueprint:
    """Metadata descriptor for a 3D CAD holographic blueprint asset."""
    blueprint_id: str
    name: str
    category: str  # "armor_suit", "power_core", "avionics", "weaponry", "robotics"
    file_path: str
    file_format: str
    vertex_count: int
    face_count: int
    materials: List[str]
    power_draw_kw: float
    mass_kg: float
    description: str


class CADBlueprintManager:
    """
    Controller for J.A.R.V.I.S. 3D Holographic CAD Blueprints.
    """

    def __init__(self, cad_dir: Optional[Path] = None):
        self.cad_dir = cad_dir or CAD_DIR
        self.cad_dir.mkdir(parents=True, exist_ok=True)
        self.catalog: Dict[str, CADBlueprint] = {}
        self._ensure_default_blueprints()

    def _ensure_default_blueprints(self):
        """Generates procedural 3D models if cad_3d directory is empty."""
        needed_models = [
            ("mark85_armor_full", self._generate_mark85_obj),
            ("arc_reactor_exploded", self._generate_arc_reactor_obj),
            ("stark_hypersonic_drone", self._generate_drone_obj),
            ("repulsor_gauntlet_hd", self._generate_gauntlet_obj),
            ("dume_robotic_arm", self._generate_dume_arm_obj),
        ]

        for model_id, gen_fn in needed_models:
            file_path = self.cad_dir / f"{model_id}.obj"
            if not file_path.exists():
                logger.info(f"Generating procedural 3D CAD blueprint: {model_id}...")
                gen_fn(file_path)

        self._refresh_catalog()

    def _refresh_catalog(self):
        """Scans directory and populates catalog with technical specifications."""
        meta_table = {
            "mark85_armor_full": {
                "name": "Iron Man Mark 85 Full Tactical Armor",
                "category": "armor_suit",
                "materials": ["Gold-Titanium Matrix (Ti3Au)", "Carbon Nanotube Composite", "Nitinol Smart Memory Alloy"],
                "power_draw_kw": 1200.0,
                "mass_kg": 92.5,
                "description": "Peak nanotech combat suit featuring enhanced structural integrity, integrated flight repulsors, and nano-particle energy redirection."
            },
            "arc_reactor_exploded": {
                "name": "Mark 50 Toroidal Arc Reactor (Exploded View)",
                "category": "power_core",
                "materials": ["Palladium-Gold Core Ring", "Superconducting Toroidal Coils", "Beryllium Reflective Shield"],
                "power_draw_kw": -3000000.0,  # Negative indicating power generation (3 GW)
                "mass_kg": 18.4,
                "description": "Multi-layer exploded schematic of the clean magnetic pinch confinement fusion reactor core."
            },
            "stark_hypersonic_drone": {
                "name": "Stark Industries Hypersonic Surveillance Drone",
                "category": "avionics",
                "materials": ["Ti-6Al-4V Grade 5 Titanium", "Inconel 718 High-Temp Skin", "Radar-Absorbent Ferrite Coating"],
                "power_draw_kw": 450.0,
                "mass_kg": 340.0,
                "description": "High-altitude Mach 6.2 reconnaissance platform with variable vectoring scramjet thrust nozzles."
            },
            "repulsor_gauntlet_hd": {
                "name": "Mark 85 Articulated Repulsor Gauntlet",
                "category": "weaponry",
                "materials": ["Aerospace Gold-Titanium", "High-Torque Micro-Hydraulics", "Crystalline Focus Lenses"],
                "power_draw_kw": 350.0,
                "mass_kg": 8.2,
                "description": "Five-digit kinematic gauntlet with palm-mounted electrogravitic repulsor coil and micro-missile hardpoints."
            },
            "dume_robotic_arm": {
                "name": "Dum-E Hydraulic Laboratory Manipulator",
                "category": "robotics",
                "materials": ["Structural Aluminum 7075-T6", "Cast Steel Joint Collars", "High-Pressure Hydraulic Lines"],
                "power_draw_kw": 45.0,
                "mass_kg": 185.0,
                "description": "Autonomous workshop articulate manipulator with dual-finger pneumatic grabber and safety fire-extinguisher mount."
            }
        }

        self.catalog.clear()
        for obj_file in self.cad_dir.glob("*.obj"):
            bid = obj_file.stem
            v_count, f_count = self._count_obj_elements(obj_file)
            defaults = meta_table.get(bid, {
                "name": bid.replace("_", " ").title(),
                "category": "mechanical",
                "materials": ["Titanium Alloy"],
                "power_draw_kw": 100.0,
                "mass_kg": 50.0,
                "description": "Standard 3D CAD engineering model."
            })

            self.catalog[bid] = CADBlueprint(
                blueprint_id=bid,
                name=defaults["name"],
                category=defaults["category"],
                file_path=str(obj_file),
                file_format="obj",
                vertex_count=v_count,
                face_count=f_count,
                materials=defaults["materials"],
                power_draw_kw=defaults["power_draw_kw"],
                mass_kg=defaults["mass_kg"],
                description=defaults["description"]
            )

        # Write catalog JSON index
        try:
            cat_dict = {
                k: {
                    "blueprint_id": v.blueprint_id,
                    "name": v.name,
                    "category": v.category,
                    "file_path": v.file_path,
                    "file_format": v.file_format,
                    "vertex_count": v.vertex_count,
                    "face_count": v.face_count,
                    "materials": v.materials,
                    "power_draw_kw": v.power_draw_kw,
                    "mass_kg": v.mass_kg,
                    "description": v.description
                }
                for k, v in self.catalog.items()
            }
            CATALOG_FILE.write_text(json.dumps(cat_dict, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to write CAD catalog cache: {e}")

    @staticmethod
    def _count_obj_elements(file_path: Path) -> Tuple[int, int]:
        """Counts vertex and face entries in an OBJ file."""
        v = 0
        f = 0
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
                for line in fp:
                    if line.startswith("v "):
                        v += 1
                    elif line.startswith("f "):
                        f += 1
        except Exception:
            pass
        return v, f

    def list_blueprints(self, category: Optional[str] = None) -> List[CADBlueprint]:
        """Returns all cataloged 3D CAD blueprints, optionally filtered by category."""
        bps = list(self.catalog.values())
        if category:
            bps = [b for b in bps if b.category == category]
        return bps

    def get_blueprint(self, blueprint_id: str) -> Optional[CADBlueprint]:
        """Retrieves a blueprint by its identifier."""
        return self.catalog.get(blueprint_id.lower().strip())

    def load_wireframe_mesh(self, blueprint_id: str) -> Optional[Mesh3D]:
        """
        Parses an OBJ CAD blueprint and returns a normalized Mesh3D object
        for live holographic rendering in the projector or HUD.
        """
        bp = self.get_blueprint(blueprint_id)
        if not bp:
            return None

        p = Path(bp.file_path)
        if not p.is_file():
            return None

        vertices: List[List[float]] = []
        edges: Set[Tuple[int, int]] = set()

        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("v "):
                        parts = line.split()
                        if len(parts) >= 4:
                            vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    elif line.startswith("f "):
                        parts = line.split()[1:]
                        idx_list = []
                        for part in parts:
                            idx_str = part.split("/")[0]
                            if idx_str:
                                # OBJ indices are 1-based
                                idx_list.append(int(idx_str) - 1)
                        # Add polygon perimeter edges
                        for i in range(len(idx_list)):
                            v1 = idx_list[i]
                            v2 = idx_list[(i + 1) % len(idx_list)]
                            if 0 <= v1 < len(vertices) and 0 <= v2 < len(vertices):
                                edges.add(tuple(sorted((v1, v2))))

            if not vertices:
                return None

            mesh = Mesh3D(bp.name, np.array(vertices, dtype=np.float32), list(edges))
            mesh.normalize(65.0)
            return mesh
        except Exception as e:
            logger.error(f"Error parsing CAD wireframe mesh {blueprint_id}: {e}")
            return None

    def generate_engineering_dossier(self, blueprint_id: str) -> Dict[str, Any]:
        """Computes comprehensive engineering dossier and bill of materials."""
        bp = self.get_blueprint(blueprint_id)
        if not bp:
            return {"error": f"Blueprint '{blueprint_id}' not found."}

        density_alloy_g_cm3 = 4.43 if "Titanium" in str(bp.materials) else 2.70
        estimated_volume_cm3 = round(bp.mass_kg * 1000.0 / density_alloy_g_cm3, 1)

        return {
            "blueprint_id": bp.blueprint_id,
            "designation": bp.name,
            "category": bp.category.upper(),
            "structural_specifications": {
                "dry_mass_kg": bp.mass_kg,
                "displacement_volume_cm3": estimated_volume_cm3,
                "primary_alloys": bp.materials,
                "geometric_mesh_vertices": bp.vertex_count,
                "geometric_mesh_polygons": bp.face_count,
            },
            "energetics_and_power": {
                "nominal_power_kw": bp.power_draw_kw,
                "source": "Stark Toroidal Arc Reactor Sub-Grid" if bp.power_draw_kw > 0 else "Self-Sustaining Fusion Generator",
            },
            "operational_clearance": "CLASS-IV STARK TACTICAL DEFENSE ASSET",
            "description": bp.description
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Procedural 3D OBJ Synthesis Engines
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _generate_mark85_obj(path: Path):
        """Generates comprehensive Iron Man Mark 85 armor OBJ mesh."""
        lines = ["# J.A.R.V.I.S. Mark 85 Full Tactical Armor Wireframe", "o Mark85_Armor"]
        verts: List[Tuple[float, float, float]] = []
        faces: List[List[int]] = []

        def add_v(x, y, z):
            verts.append((round(x, 2), round(y, 2), round(z, 2)))
            return len(verts)

        # 1. Helmet & Eyes (Y: 55 to 78)
        h0 = add_v(-10, 78, 10); h1 = add_v(10, 78, 10); h2 = add_v(12, 62, 14); h3 = add_v(-12, 62, 14)
        h4 = add_v(-16, 56, 8); h5 = add_v(16, 56, 8); h6 = add_v(10, 52, 10); h7 = add_v(-10, 52, 10)
        # Eye slit cutouts
        e0 = add_v(-9, 64, 15); e1 = add_v(-3, 63, 16); e2 = add_v(3, 63, 16); e3 = add_v(9, 64, 15)
        faces.extend([[h0, h1, h2, h3], [h3, h2, h5, h4], [h4, h5, h6, h7], [e0, e1, h3], [e2, e3, h2]])

        # 2. Chest & Unibeam (Y: 25 to 52)
        c0 = add_v(-24, 52, 12); c1 = add_v(24, 52, 12); c2 = add_v(20, 26, 14); c3 = add_v(-20, 26, 14)
        # Circular Unibeam Core in chest center
        u0 = add_v(-6, 42, 16); u1 = add_v(0, 47, 16); u2 = add_v(6, 42, 16); u3 = add_v(0, 37, 16)
        faces.extend([[c0, c1, c2, c3], [u0, u1, u2, u3]])

        # 3. Shoulder Pauldrons & Arms
        # Left Arm
        la0 = add_v(-34, 48, 8); la1 = add_v(-32, 28, 6); la2 = add_v(-30, 8, 8); la3 = add_v(-28, -6, 10)
        # Right Arm
        ra0 = add_v(34, 48, 8); ra1 = add_v(32, 28, 6); ra2 = add_v(30, 8, 8); ra3 = add_v(28, -6, 10)
        faces.extend([[c0, la0, la1, c3], [c1, ra0, ra1, c2], [la1, la2, la3], [ra1, ra2, ra3]])

        # 4. Pelvis & Waist (Y: 5 to 25)
        p0 = add_v(-18, 25, 10); p1 = add_v(18, 25, 10); p2 = add_v(14, 6, 8); p3 = add_v(-14, 6, 8)
        faces.append([p0, p1, p2, p3])

        # 5. Thighs & Calves (Y: -75 to 5)
        # Left Leg
        ll0 = add_v(-14, 4, 6); ll1 = add_v(-12, -25, 6); ll2 = add_v(-10, -55, 4); ll3 = add_v(-12, -75, 10)
        # Right Leg
        rl0 = add_v(14, 4, 6); rl1 = add_v(12, -25, 6); rl2 = add_v(10, -55, 4); rl3 = add_v(12, -75, 10)
        faces.extend([[p3, p2, rl0, ll0], [ll0, ll1, ll2, ll3], [rl0, rl1, rl2, rl3]])

        # Back Armor Plates (Z: -12 to -16)
        b0 = add_v(-20, 52, -12); b1 = add_v(20, 52, -12); b2 = add_v(16, 26, -14); b3 = add_v(-16, 26, -14)
        faces.append([b0, b1, b2, b3])

        for v in verts:
            lines.append(f"v {v[0]} {v[1]} {v[2]}")
        for f in faces:
            lines.append("f " + " ".join(str(idx) for idx in f))

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def _generate_arc_reactor_obj(path: Path):
        """Generates exploded concentric Arc Reactor assembly OBJ mesh."""
        lines = ["# J.A.R.V.I.S. Arc Reactor Exploded Assembly", "o Arc_Reactor_Core"]
        verts: List[Tuple[float, float, float]] = []
        faces: List[List[int]] = []

        def add_v(x, y, z):
            verts.append((round(x, 2), round(y, 2), round(z, 2)))
            return len(verts)

        # Concentric rings along Z axis (exploded view)
        z_layers = [(-35.0, 55.0, 16), (-15.0, 45.0, 12), (5.0, 32.0, 10), (25.0, 18.0, 8), (45.0, 8.0, 6)]
        ring_starts = []

        for z_off, radius, segments in z_layers:
            start_i = len(verts) + 1
            ring_starts.append((start_i, segments))
            for seg in range(segments):
                ang = seg * (math.pi * 2 / segments)
                add_v(radius * math.cos(ang), radius * math.sin(ang), z_off)
            for seg in range(segments):
                v1 = start_i + seg
                v2 = start_i + ((seg + 1) % segments)
                faces.append([v1, v2])

        # Central Triangular Emitter Plate
        tri0 = add_v(0, 16, 30); tri1 = add_v(14, -10, 30); tri2 = add_v(-14, -10, 30)
        faces.append([tri0, tri1, tri2])

        # Radial Interconnecting Flux Spoke Rods
        for spoke in range(8):
            ang = spoke * (math.pi * 2 / 8)
            spk_in = add_v(12 * math.cos(ang), 12 * math.sin(ang), 0)
            spk_out = add_v(52 * math.cos(ang), 52 * math.sin(ang), 0)
            faces.append([spk_in, spk_out])

        for v in verts:
            lines.append(f"v {v[0]} {v[1]} {v[2]}")
        for f in faces:
            lines.append("f " + " ".join(str(idx) for idx in f))

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def _generate_drone_obj(path: Path):
        """Generates hypersonic stealth drone airframe OBJ mesh."""
        lines = ["# J.A.R.V.I.S. Stark Industries Hypersonic Drone", "o Hypersonic_Drone"]
        verts: List[Tuple[float, float, float]] = []
        faces: List[List[int]] = []

        def add_v(x, y, z):
            verts.append((round(x, 2), round(y, 2), round(z, 2)))
            return len(verts)

        # Fuselage
        nose = add_v(0, 85, 4); mid_f = add_v(0, 35, 14); tail_f = add_v(0, -55, 6)
        # Chined Wingtips
        lw = add_v(-85, -35, 2); rw = add_v(85, -35, 2)
        # Canards
        lc = add_v(-28, 42, 6); rc = add_v(28, 42, 6)
        # Twin Fins
        lf_t = add_v(-18, -60, 24); rf_t = add_v(18, -60, 24)
        lf_b = add_v(-14, -50, 4); rf_b = add_v(14, -50, 4)

        faces.extend([
            [nose, lc, mid_f], [nose, rc, mid_f],
            [mid_f, lw, tail_f], [mid_f, rw, tail_f],
            [tail_f, lf_b, lf_t], [tail_f, rf_b, rf_t],
            [lw, tail_f, rw]
        ])

        for v in verts:
            lines.append(f"v {v[0]} {v[1]} {v[2]}")
        for f in faces:
            lines.append("f " + " ".join(str(idx) for idx in f))

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def _generate_gauntlet_obj(path: Path):
        """Generates articulated repulsor gauntlet OBJ mesh."""
        lines = ["# J.A.R.V.I.S. Articulated Repulsor Gauntlet", "o Repulsor_Gauntlet"]
        verts: List[Tuple[float, float, float]] = []
        faces: List[List[int]] = []

        def add_v(x, y, z):
            verts.append((round(x, 2), round(y, 2), round(z, 2)))
            return len(verts)

        # Palm center & repulsor circle
        p_c = add_v(0, 0, 8)
        circ_idx = []
        for i in range(8):
            ang = i * (math.pi * 2 / 8)
            circ_idx.append(add_v(12 * math.cos(ang), 12 * math.sin(ang), 8))
        for i in range(8):
            faces.append([p_c, circ_idx[i], circ_idx[(i + 1) % 8]])

        # Forearm Cuffs
        c0 = add_v(-16, -35, 4); c1 = add_v(16, -35, 4); c2 = add_v(18, -65, 2); c3 = add_v(-18, -65, 2)
        faces.append([c0, c1, c2, c3])

        # 5 Articulated Fingers
        finger_offsets = [(-18, 14), (-10, 24), (0, 28), (10, 25), (18, 18)]
        for fx, fy in finger_offsets:
            j0 = add_v(fx, fy, 6); j1 = add_v(fx * 1.15, fy + 14, 5); j2 = add_v(fx * 1.25, fy + 26, 4)
            faces.append([j0, j1, j2])

        for v in verts:
            lines.append(f"v {v[0]} {v[1]} {v[2]}")
        for f in faces:
            lines.append("f " + " ".join(str(idx) for idx in f))

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @staticmethod
    def _generate_dume_arm_obj(path: Path):
        """Generates Dum-E hydraulic workshop arm OBJ mesh."""
        lines = ["# J.A.R.V.I.S. Dum-E Robotic Arm Manipulator", "o DUM_E_Arm"]
        verts: List[Tuple[float, float, float]] = []
        faces: List[List[int]] = []

        def add_v(x, y, z):
            verts.append((round(x, 2), round(y, 2), round(z, 2)))
            return len(verts)

        # Base Turntable
        b0 = add_v(-25, -60, -25); b1 = add_v(25, -60, -25); b2 = add_v(25, -60, 25); b3 = add_v(-25, -60, 25)
        b_c = add_v(0, -45, 0)
        faces.extend([[b0, b1, b2, b3], [b0, b_c], [b1, b_c], [b2, b_c], [b3, b_c]])

        # Shoulder & Lower Boom
        sh = add_v(0, -25, 0); elbow = add_v(15, 15, 0)
        # Hydraulic Ram Cylinder
        cyl = add_v(8, -5, 12)
        faces.extend([[b_c, sh, elbow], [sh, cyl, elbow]])

        # Forearm & Wrist
        wrist = add_v(45, 30, 0)
        faces.append([elbow, wrist])

        # Dual Gripper Claws
        c_left = add_v(58, 40, -8); c_right = add_v(58, 40, 8)
        faces.extend([[wrist, c_left], [wrist, c_right]])

        for v in verts:
            lines.append(f"v {v[0]} {v[1]} {v[2]}")
        for f in faces:
            lines.append("f " + " ".join(str(idx) for idx in f))

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# Global Singleton Instance
cad_blueprint_manager = CADBlueprintManager()
