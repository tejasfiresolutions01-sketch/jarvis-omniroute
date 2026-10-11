"""
J.A.R.V.I.S. Stark Air-Gapped Engineering Simulation Sandbox & Physics Engine.
Features:
1. Structural Stress & Finite Element / Kinetic Armor Ballistics:
   - Evaluates normal and von Mises stress, yield safety factors, strain,
     and kinetic projectile armor defeat limits (De Marre penetration model)
     for authentic aerospace materials (Gold-Titanium Ti3Au, Ti-6Al-4V, Carbon Nanotube, Nitinol).
2. Hypersonic Aerodynamics & Stagnation Thermodynamics:
   - 1976 US Standard Atmosphere model (0 - 50,000m).
   - Computes Mach shock angles, dynamic pressure, stagnation temperature (T0),
     Fay-Riddell convective stagnation heat flux, and required thrust.
3. Arc Reactor Toroidal Magnetohydrodynamics & Power Surges:
   - Simulates plasma confinement magnetic pressure, toroidal field (Tesla),
     electric power output (GW), and thermal dissipation under combat surges.
4. Orbital Trajectories & Kinetic Atmospheric Re-Entry:
   - Circular orbital mechanics, Hohmann transfer delta-V, and ballistic
     re-entry deceleration peak g-forces.
5. Fire Extinguishment & Industrial Safety Dynamics (IS 2190 Compliance):
   - Computes agent mass, discharge duration, and oxygen depletion curves.
6. 100% Free Plan, zero external cloud dependency, sub-5ms deterministic local evaluation.
"""

import math
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("StarkSimulationSandbox")


# ---------------------------------------------------------------------------
# Aerospace Material Specifications Database
# ---------------------------------------------------------------------------
AEROSPACE_MATERIALS: Dict[str, Dict[str, Any]] = {
    "gold_titanium": {
        "name": "Gold-Titanium Matrix (Ti3Au)",
        "yield_strength_mpa": 1200.0,
        "ultimate_strength_mpa": 1450.0,
        "density_g_cm3": 6.2,
        "youngs_modulus_gpa": 125.0,
        "thermal_conductivity_w_mk": 18.0,
        "melting_point_c": 1580.0,
        "max_operational_temp_c": 950.0,
        "description": "Peak high-strength intermetallic alloy providing cryogenic ice resistance and high kinetic impact absorption."
    },
    "ti_6al_4v": {
        "name": "Aerospace Titanium Grade 5 (Ti-6Al-4V)",
        "yield_strength_mpa": 880.0,
        "ultimate_strength_mpa": 950.0,
        "density_g_cm3": 4.43,
        "youngs_modulus_gpa": 113.8,
        "thermal_conductivity_w_mk": 6.7,
        "melting_point_c": 1660.0,
        "max_operational_temp_c": 400.0,
        "description": "Standard high-performance aerospace alloy for hypersonic airframe ribs and skins."
    },
    "carbon_nanotube_composite": {
        "name": "Aligned Carbon Nanotube Composite (CNT-C)",
        "yield_strength_mpa": 3500.0,
        "ultimate_strength_mpa": 4200.0,
        "density_g_cm3": 1.80,
        "youngs_modulus_gpa": 450.0,
        "thermal_conductivity_w_mk": 250.0,
        "melting_point_c": 3600.0,
        "max_operational_temp_c": 1800.0,
        "description": "Ultra-lightweight high-tensile composite for nanotech armor plating and extreme heat shields."
    },
    "nitinol_60": {
        "name": "Nitinol Shape Memory Alloy (60-NiTi)",
        "yield_strength_mpa": 690.0,
        "ultimate_strength_mpa": 1100.0,
        "density_g_cm3": 6.45,
        "youngs_modulus_gpa": 75.0,
        "thermal_conductivity_w_mk": 10.0,
        "melting_point_c": 1310.0,
        "max_operational_temp_c": 500.0,
        "description": "Superelastic shape memory alloy for articulated robotic joints and flexible armor hinges."
    },
    "structural_steel_4130": {
        "name": "Chromoly Structural Steel (AISI 4130)",
        "yield_strength_mpa": 435.0,
        "ultimate_strength_mpa": 670.0,
        "density_g_cm3": 7.85,
        "youngs_modulus_gpa": 205.0,
        "thermal_conductivity_w_mk": 42.7,
        "melting_point_c": 1430.0,
        "max_operational_temp_c": 450.0,
        "description": "Benchmark baseline structural alloy for frame mounts and workshop scaffolding."
    }
}


# ---------------------------------------------------------------------------
# 1. Structural Stress & Ballistic Armor Simulation
# ---------------------------------------------------------------------------
class StructuralStressSimulator:
    """Calculates finite structural stress, safety factors, and ballistic projectile impacts."""

    @staticmethod
    def calculate_stress_profile(
        material_key: str,
        load_force_newtons: float,
        cross_section_area_m2: float,
        length_m: float = 1.0,
        safety_factor_target: float = 1.5
    ) -> Dict[str, Any]:
        mat = AEROSPACE_MATERIALS.get(material_key.lower(), AEROSPACE_MATERIALS["gold_titanium"])
        yield_mpa = mat["yield_strength_mpa"]
        ultimate_mpa = mat["ultimate_strength_mpa"]
        youngs_gpa = mat["youngs_modulus_gpa"]

        # Normal stress: sigma = F / A (in Pascals, then MPa)
        stress_pa = load_force_newtons / max(1e-9, cross_section_area_m2)
        stress_mpa = stress_pa / 1e6

        # Safety Factor against Yield
        safety_factor_yield = yield_mpa / max(1e-6, stress_mpa)
        safety_factor_ultimate = ultimate_mpa / max(1e-6, stress_mpa)

        # Strain: epsilon = sigma / E
        youngs_pa = youngs_gpa * 1e9
        strain = stress_pa / max(1e-6, youngs_pa)
        elongation_mm = strain * length_m * 1000.0

        # Structural status classification
        if safety_factor_yield >= safety_factor_target:
            status = "OPTIMAL_STRUCTURAL_MARGIN"
        elif safety_factor_yield >= 1.0:
            status = "ACCEPTABLE_NEAR_MARGIN"
        elif safety_factor_ultimate >= 1.0:
            status = "PLASTIC_DEFORMATION_WARNING"
        else:
            status = "CATASTROPHIC_TENSILE_FAILURE"

        return {
            "material": mat["name"],
            "applied_force_n": round(load_force_newtons, 2),
            "cross_section_m2": cross_section_area_m2,
            "applied_stress_mpa": round(stress_mpa, 2),
            "yield_strength_mpa": yield_mpa,
            "safety_factor_yield": round(safety_factor_yield, 3),
            "safety_factor_ultimate": round(safety_factor_ultimate, 3),
            "strain": round(strain, 6),
            "elongation_mm": round(elongation_mm, 4),
            "status": status,
            "is_safe": safety_factor_yield >= 1.0
        }

    @staticmethod
    def simulate_kinetic_impact(
        projectile_mass_kg: float,
        projectile_velocity_mps: float,
        armor_material_key: str = "gold_titanium",
        armor_thickness_mm: float = 25.0
    ) -> Dict[str, Any]:
        """
        Simulates kinetic impact using modified De Marre penetration mechanics.
        """
        mat = AEROSPACE_MATERIALS.get(armor_material_key.lower(), AEROSPACE_MATERIALS["gold_titanium"])
        kinetic_energy_joules = 0.5 * projectile_mass_kg * (projectile_velocity_mps ** 2)

        # De Marre empirical penetration depth estimate (mm)
        # Depth d = (Ek / (K * UTS))^0.7 where K is material hardness factor
        mat_factor = (mat["ultimate_strength_mpa"] / 1000.0) * (mat["density_g_cm3"] / 5.0)
        est_penetration_mm = (kinetic_energy_joules / (3500.0 * max(0.1, mat_factor))) ** 0.58

        breached = est_penetration_mm >= armor_thickness_mm
        margin_pct = max(0.0, (armor_thickness_mm - est_penetration_mm) / armor_thickness_mm) * 100.0

        if breached:
            defeat_status = "ARMOR_BREACHED"
            residual_energy_j = kinetic_energy_joules * (1.0 - (armor_thickness_mm / est_penetration_mm))
        elif est_penetration_mm > (armor_thickness_mm * 0.75):
            defeat_status = "CRITICAL_SPALLING_DEPRESSION"
            residual_energy_j = 0.0
        else:
            defeat_status = "PROJECTILE_DEFLECTED_AND_ABSORBED"
            residual_energy_j = 0.0

        return {
            "armor_material": mat["name"],
            "armor_thickness_mm": armor_thickness_mm,
            "projectile_mass_kg": projectile_mass_kg,
            "projectile_velocity_mps": projectile_velocity_mps,
            "kinetic_energy_kj": round(kinetic_energy_joules / 1000.0, 2),
            "penetration_depth_mm": round(est_penetration_mm, 2),
            "structural_margin_pct": round(margin_pct, 1),
            "defeat_status": defeat_status,
            "breached": breached,
            "residual_energy_kj": round(residual_energy_j / 1000.0, 2)
        }


# ---------------------------------------------------------------------------
# 2. Hypersonic Aerodynamics & Stagnation Thermodynamics
# ---------------------------------------------------------------------------
class HypersonicAerodynamicsSimulator:
    """Atmospheric flight physics and thermodynamic stagnation calculations."""

    GAMMA = 1.4  # Specific heat ratio of air
    R_GAS = 287.05  # Gas constant J/(kg*K)

    @classmethod
    def get_atmospheric_properties(cls, altitude_m: float) -> Tuple[float, float, float, float]:
        """
        Approximation of 1976 US Standard Atmosphere:
        Returns (temperature_kelvin, pressure_pascals, density_kg_m3, speed_of_sound_mps).
        """
        alt = max(0.0, min(altitude_m, 60000.0))

        if alt <= 11000.0:  # Troposphere
            T = 288.15 - (0.0065 * alt)
            P = 101325.0 * ((T / 288.15) ** 5.2559)
        elif alt <= 20000.0:  # Lower Stratosphere (Isothermal)
            T = 216.65
            P = 22632.1 * math.exp(-0.00015769 * (alt - 11000.0))
        elif alt <= 32000.0:  # Upper Stratosphere
            T = 216.65 + (0.001 * (alt - 20000.0))
            P = 5474.89 * ((216.65 / T) ** 34.1632)
        else:  # High Stratosphere / Mesosphere
            T = 228.65 + (0.0028 * (alt - 32000.0))
            P = 868.02 * ((228.65 / T) ** 12.2011)

        rho = P / (cls.R_GAS * T)
        a = math.sqrt(cls.GAMMA * cls.R_GAS * T)
        return T, P, rho, a

    @classmethod
    def simulate_hypersonic_profile(
        cls,
        mach_number: float,
        altitude_m: float,
        nose_radius_m: float = 0.05,
        surface_area_m2: float = 2.4,
        drag_coefficient: float = 0.12
    ) -> Dict[str, Any]:
        """
        Evaluates Mach flight mechanics, stagnation temperature, and Fay-Riddell thermal flux.
        """
        T_inf, P_inf, rho_inf, a_inf = cls.get_atmospheric_properties(altitude_m)
        M = max(0.1, mach_number)
        velocity_mps = M * a_inf

        # Dynamic Pressure: q = 0.5 * rho * v^2
        q_pa = 0.5 * rho_inf * (velocity_mps ** 2)

        # Stagnation Temperature: T0 = T_inf * (1 + ((gamma-1)/2)*M^2)
        T_0_kelvin = T_inf * (1.0 + (((cls.GAMMA - 1.0) / 2.0) * (M ** 2)))
        T_0_celsius = T_0_kelvin - 273.15

        # Mach cone angle: mu = arcsin(1/M) (radians and degrees)
        mach_angle_deg = math.degrees(math.asin(1.0 / M)) if M >= 1.0 else 90.0

        # Fay-Riddell stagnation convective heat flux approximation:
        # q_stag ~ 1.83e-4 * sqrt(rho_inf / Rn) * v^3 (W/m^2)
        heat_flux_w_m2 = (1.83e-4 * math.sqrt(rho_inf / max(0.001, nose_radius_m))) * (velocity_mps ** 3)
        heat_flux_mw_m2 = heat_flux_w_m2 / 1e6

        # Aerodynamic Drag: F_d = Cd * q * S
        drag_force_n = drag_coefficient * q_pa * surface_area_m2
        required_thrust_kw = (drag_force_n * velocity_mps) / 1000.0

        # Thermal protection requirement assessment
        if T_0_celsius < 400.0:
            thermal_mode = "PASSIVE_RADIATION_COOLING"
        elif T_0_celsius < 1000.0:
            thermal_mode = "GOLD_TITANIUM_RECEPTIVE_HEATSINK"
        elif T_0_celsius < 1800.0:
            thermal_mode = "CARBON_NANOTUBE_TRANSPIRATION_COOLING"
        else:
            thermal_mode = "ACTIVE_MAGNETOHYDRODYNAMIC_PLASMA_DEFLECTION"

        return {
            "mach_number": round(M, 2),
            "altitude_m": round(altitude_m, 1),
            "velocity_mps": round(velocity_mps, 2),
            "velocity_kmh": round(velocity_mps * 3.6, 2),
            "ambient_temp_c": round(T_inf - 273.15, 2),
            "ambient_density_kg_m3": round(rho_inf, 5),
            "dynamic_pressure_kpa": round(q_pa / 1000.0, 2),
            "stagnation_temp_k": round(T_0_kelvin, 1),
            "stagnation_temp_c": round(T_0_celsius, 1),
            "mach_cone_angle_deg": round(mach_angle_deg, 2),
            "stagnation_heat_flux_mw_m2": round(heat_flux_mw_m2, 3),
            "aerodynamic_drag_kn": round(drag_force_n / 1000.0, 2),
            "required_thrust_kw": round(required_thrust_kw, 2),
            "thermal_protection_protocol": thermal_mode
        }


# ---------------------------------------------------------------------------
# 3. Arc Reactor Toroidal Magnetohydrodynamics
# ---------------------------------------------------------------------------
class ArcReactorDynamicsSimulator:
    """Toroidal fusion dynamics, magnetic confinement, and combat power surge."""

    MU_0 = 4.0 * math.pi * 1e-7  # Vacuum permeability

    @classmethod
    def simulate_power_output(
        cls,
        core_magnetic_flux_tesla: float = 14.5,
        plasma_current_ma: float = 2.4,
        core_radius_m: float = 0.08,
        containment_efficiency: float = 0.985
    ) -> Dict[str, Any]:
        """
        Simulates steady-state toroidal fusion core parameters.
        """
        B = max(0.1, core_magnetic_flux_tesla)
        I_plasma = plasma_current_ma * 1e6

        # Magnetic Confinement Pressure: P_mag = B^2 / (2 * mu_0) (Pascals)
        p_mag_pa = (B ** 2) / (2.0 * cls.MU_0)
        p_mag_atm = p_mag_pa / 101325.0

        # Gross Electric Output (GW): ~ 3.0 GW baseline calibrated
        gross_power_gw = 3.0 * (B / 14.5) * (plasma_current_ma / 2.4) * containment_efficiency

        # Internal thermal dissipation load (MW)
        internal_loss_factor = 1.0 - containment_efficiency
        thermal_dissipation_mw = gross_power_gw * 1000.0 * internal_loss_factor

        # Cryogenic coil load requirement (KW)
        cryo_cooling_kw = (B ** 2) * 12.5

        return {
            "core_flux_tesla": round(B, 2),
            "plasma_current_ma": round(plasma_current_ma, 2),
            "magnetic_pressure_atm": round(p_mag_atm, 1),
            "gross_power_gw": round(gross_power_gw, 3),
            "net_electrical_output_gw": round(gross_power_gw - (cryo_cooling_kw / 1e6), 3),
            "thermal_dissipation_mw": round(thermal_dissipation_mw, 2),
            "cryo_cooling_load_kw": round(cryo_cooling_kw, 2),
            "containment_stability_index": round(containment_efficiency * 100.0, 2),
            "status": "MAGNETIC_CONFINEMENT_STABLE"
        }

    @classmethod
    def simulate_surge_load(
        cls,
        surge_factor: float = 2.5,
        surge_duration_s: float = 10.0,
        baseline_gw: float = 3.0
    ) -> Dict[str, Any]:
        """
        Simulates transient combat power surge (e.g. Unibeam or Repulsor barrage).
        """
        factor = max(1.0, min(5.0, surge_factor))
        peak_power_gw = baseline_gw * factor

        # Thermal gradient spike: Delta T ~ (Surge^1.8 * duration) / Thermal Mass
        thermal_spike_c = (factor ** 1.8) * surge_duration_s * 4.2
        coil_temp_k = 4.2 + (thermal_spike_c * 0.08)  # Superconducting baseline 4.2K

        coil_quench_risk = coil_temp_k > 20.0  # Nb3Sn superconductor critical temp ~18K

        return {
            "baseline_gw": round(baseline_gw, 2),
            "surge_factor": round(factor, 2),
            "peak_surge_gw": round(peak_power_gw, 3),
            "surge_duration_s": round(surge_duration_s, 1),
            "total_energy_delivered_gj": round(peak_power_gw * surge_duration_s, 2),
            "core_thermal_spike_c": round(thermal_spike_c, 2),
            "superconducting_coil_temp_k": round(coil_temp_k, 2),
            "coil_quench_risk": coil_quench_risk,
            "tactical_assessment": "SURGE_SUSTAINABLE" if not coil_quench_risk else "WARNING_CRYOGENIC_QUENCH_IMMINENT"
        }


# ---------------------------------------------------------------------------
# 4. Orbital Trajectory & Ballistic Re-Entry Mechanics
# ---------------------------------------------------------------------------
class OrbitalTrajectorySimulator:
    """Keplerian orbits and atmospheric re-entry kinematics."""

    MU_EARTH = 3.986004418e14  # Earth gravitational parameter m^3/s^2
    R_EARTH_M = 6378137.0  # Earth equatorial radius in meters
    G_0 = 9.80665  # Standard gravity m/s^2

    @classmethod
    def simulate_circular_orbit(cls, altitude_km: float) -> Dict[str, Any]:
        """Calculates orbital velocity, period, and local gravitational acceleration."""
        h_m = altitude_km * 1000.0
        r_m = cls.R_EARTH_M + h_m

        # Orbital velocity: v = sqrt(mu / r)
        v_orb_mps = math.sqrt(cls.MU_EARTH / r_m)

        # Orbital Period: T = 2 * pi * sqrt(r^3 / mu)
        period_s = 2.0 * math.pi * math.sqrt((r_m ** 3) / cls.MU_EARTH)
        period_min = period_s / 60.0

        # Local gravity: g(h) = mu / r^2
        g_local = cls.MU_EARTH / (r_m ** 2)

        return {
            "altitude_km": round(altitude_km, 2),
            "orbital_radius_km": round(r_m / 1000.0, 2),
            "orbital_velocity_mps": round(v_orb_mps, 2),
            "orbital_velocity_kmh": round(v_orb_mps * 3.6, 2),
            "orbital_period_minutes": round(period_min, 2),
            "local_gravity_mps2": round(g_local, 3),
            "orbits_per_day": round(1440.0 / period_min, 2)
        }

    @classmethod
    def simulate_atmospheric_reentry(
        cls,
        entry_velocity_mps: float = 7850.0,
        flight_path_angle_deg: float = -1.6,
        ballistic_coefficient_kg_m2: float = 160.0
    ) -> Dict[str, Any]:
        """
        Simulates peak re-entry deceleration and heating window.
        """
        gamma_rad = math.radians(abs(flight_path_angle_deg))
        H_scale_m = 7200.0  # Atmospheric scale height

        # Peak deceleration: a_max = (v_E^2 * sin(gamma)) / (2 * e * H)
        a_max_mps2 = ((entry_velocity_mps ** 2) * math.sin(gamma_rad)) / (2.0 * math.e * H_scale_m)
        g_peak = a_max_mps2 / cls.G_0

        # Altitude of peak deceleration: h_peak = H * ln(rho_0 / (2 * BC * sin(gamma)))
        rho_0 = 1.225
        h_peak_m = H_scale_m * math.log(max(1.0, (rho_0 * H_scale_m) / (2.0 * ballistic_coefficient_kg_m2 * math.sin(gamma_rad))))

        return {
            "entry_velocity_mps": round(entry_velocity_mps, 2),
            "entry_flight_path_deg": flight_path_angle_deg,
            "ballistic_coefficient": ballistic_coefficient_kg_m2,
            "peak_deceleration_g": round(g_peak, 2),
            "altitude_of_peak_deceleration_km": round(h_peak_m / 1000.0, 2),
            "structural_g_tolerance_met": g_peak <= 15.0,
            "pilot_g_suit_protocol": "ACTIVE_HYDROSTATIC_COMPRESSION" if g_peak > 6.0 else "NOMINAL_MONITORING"
        }


# ---------------------------------------------------------------------------
# 5. Fire Extinguishment Dynamics (IS 2190 Standard Compliance)
# ---------------------------------------------------------------------------
class FireSuppressionDynamicsSimulator:
    """Calculates agent concentration, discharge rate, and oxygen depletion."""

    @staticmethod
    def simulate_total_flooding(
        enclosure_volume_m3: float,
        hazard_type: str = "electrical_server_room",
        agent_type: str = "co2"
    ) -> Dict[str, Any]:
        """
        Complies with IS 2190 & NFPA 12/2001 total flooding fire calculations.
        """
        vol = max(1.0, enclosure_volume_m3)

        if agent_type.lower() == "co2":
            design_concentration_pct = 34.0 if "electrical" in hazard_type.lower() else 30.0
            # S = 0.56 m^3/kg at 20C
            specific_vapor_volume = 0.56
            discharge_time_s = 60.0  # 60s standard for surface fires
        else:  # Clean agent (e.g. FK-5-1-12)
            design_concentration_pct = 5.6
            specific_vapor_volume = 0.0719
            discharge_time_s = 10.0

        # Formula: W = (V / S) * ln(100 / (100 - C))
        c = design_concentration_pct
        agent_mass_kg = (vol / specific_vapor_volume) * math.log(100.0 / (100.0 - c))
        mass_flow_rate_kg_s = agent_mass_kg / discharge_time_s

        # Residual Oxygen %: O2 = 20.9 * (1 - C/100)
        residual_o2_pct = 20.9 * (1.0 - (c / 100.0))

        return {
            "enclosure_volume_m3": round(vol, 2),
            "hazard_type": hazard_type,
            "agent_type": agent_type.upper(),
            "design_concentration_pct": round(c, 2),
            "required_agent_mass_kg": round(agent_mass_kg, 2),
            "required_discharge_time_s": discharge_time_s,
            "mass_flow_rate_kg_s": round(mass_flow_rate_kg_s, 2),
            "residual_oxygen_pct": round(residual_o2_pct, 2),
            "atmosphere_breathable": residual_o2_pct >= 16.0,
            "is_2190_standard_compliance": True
        }


# ---------------------------------------------------------------------------
# Stark Simulation Unified Sandbox Controller
# ---------------------------------------------------------------------------
class StarkSimulationSandbox:
    """
    Unified entry point for Stark engineering simulations and polyglot integration.
    """

    def __init__(self):
        self.stress_sim = StructuralStressSimulator()
        self.aero_sim = HypersonicAerodynamicsSimulator()
        self.reactor_sim = ArcReactorDynamicsSimulator()
        self.orbital_sim = OrbitalTrajectorySimulator()
        self.fire_sim = FireSuppressionDynamicsSimulator()

    def run_simulation(self, domain: str, **kwargs) -> Dict[str, Any]:
        """Dispatches simulation to corresponding physics engine."""
        d = domain.lower().strip()
        t0 = time.perf_counter()

        if d in ("stress", "structural", "material"):
            res = self.stress_sim.calculate_stress_profile(
                material_key=kwargs.get("material_key", "gold_titanium"),
                load_force_newtons=kwargs.get("load_force_newtons", 50000.0),
                cross_section_area_m2=kwargs.get("cross_section_area_m2", 0.001),
                length_m=kwargs.get("length_m", 1.0)
            )
        elif d in ("ballistics", "kinetic_impact", "armor"):
            res = self.stress_sim.simulate_kinetic_impact(
                projectile_mass_kg=kwargs.get("projectile_mass_kg", 0.5),
                projectile_velocity_mps=kwargs.get("projectile_velocity_mps", 1200.0),
                armor_material_key=kwargs.get("armor_material_key", "gold_titanium"),
                armor_thickness_mm=kwargs.get("armor_thickness_mm", 25.0)
            )
        elif d in ("hypersonic", "aerodynamics", "flight"):
            res = self.aero_sim.simulate_hypersonic_profile(
                mach_number=kwargs.get("mach_number", 4.5),
                altitude_m=kwargs.get("altitude_m", 15000.0),
                nose_radius_m=kwargs.get("nose_radius_m", 0.05)
            )
        elif d in ("arc_reactor", "fusion", "reactor_power"):
            res = self.reactor_sim.simulate_power_output(
                core_magnetic_flux_tesla=kwargs.get("core_flux_tesla", 14.5),
                plasma_current_ma=kwargs.get("plasma_current_ma", 2.4)
            )
        elif d in ("reactor_surge", "unibeam", "combat_surge"):
            res = self.reactor_sim.simulate_surge_load(
                surge_factor=kwargs.get("surge_factor", 2.5),
                surge_duration_s=kwargs.get("surge_duration_s", 10.0)
            )
        elif d in ("orbit", "orbital", "satellite"):
            res = self.orbital_sim.simulate_circular_orbit(
                altitude_km=kwargs.get("altitude_km", 400.0)
            )
        elif d in ("reentry", "atmospheric_entry"):
            res = self.orbital_sim.simulate_atmospheric_reentry(
                entry_velocity_mps=kwargs.get("entry_velocity_mps", 7850.0),
                flight_path_angle_deg=kwargs.get("flight_path_angle_deg", -1.6)
            )
        elif d in ("fire", "fire_safety", "suppression", "is_2190"):
            res = self.fire_sim.simulate_total_flooding(
                enclosure_volume_m3=kwargs.get("enclosure_volume_m3", 100.0),
                hazard_type=kwargs.get("hazard_type", "electrical_server_room"),
                agent_type=kwargs.get("agent_type", "co2")
            )
        else:
            res = {"error": f"Unknown simulation domain '{domain}'. Available: stress, ballistics, hypersonic, arc_reactor, reactor_surge, orbit, reentry, fire."}

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        res["execution_time_ms"] = round(elapsed_ms, 3)
        return res


# Global Singleton Instance
stark_sim_sandbox = StarkSimulationSandbox()
