"""
Unit tests for Phase 5: Stark Air-Gapped Simulation Sandbox & Polyglot Runtime Matrix.
Verifies:
1. Structural stress & yield safety factors across aerospace materials.
2. Kinetic projectile ballistic penetration & De Marre armor defeat.
3. Hypersonic aerodynamics (stagnation temperature, shock angle, thermal flux).
4. Arc Reactor toroidal MHD & combat power surge dynamics.
5. Keplerian orbital mechanics & atmospheric re-entry deceleration g-forces.
6. IS 2190 compliant fire suppression agent mass and oxygen depletion.
7. PolyglotRuntime sandboxed execution and benchmarking.
"""

import unittest
from tools.stark_simulation_sandbox import (
    AEROSPACE_MATERIALS,
    StructuralStressSimulator,
    HypersonicAerodynamicsSimulator,
    ArcReactorDynamicsSimulator,
    OrbitalTrajectorySimulator,
    FireSuppressionDynamicsSimulator,
    stark_sim_sandbox,
)
from tools.polyglot_runtime import polyglot_runtime


class TestStarkSimulationSandbox(unittest.TestCase):

    def test_aerospace_materials_catalog(self):
        self.assertIn("gold_titanium", AEROSPACE_MATERIALS)
        self.assertIn("ti_6al_4v", AEROSPACE_MATERIALS)
        self.assertIn("carbon_nanotube_composite", AEROSPACE_MATERIALS)
        self.assertGreater(AEROSPACE_MATERIALS["gold_titanium"]["yield_strength_mpa"], 1000)

    def test_structural_stress_profile(self):
        res = StructuralStressSimulator.calculate_stress_profile(
            material_key="gold_titanium",
            load_force_newtons=60000.0,
            cross_section_area_m2=0.001,
            safety_factor_target=1.5
        )
        self.assertEqual(res["applied_stress_mpa"], 60.0)
        self.assertEqual(res["yield_strength_mpa"], 1200.0)
        self.assertAlmostEqual(res["safety_factor_yield"], 20.0, places=1)
        self.assertTrue(res["is_safe"])
        self.assertEqual(res["status"], "OPTIMAL_STRUCTURAL_MARGIN")

    def test_kinetic_ballistic_impact(self):
        # Deflected impact
        res_deflect = StructuralStressSimulator.simulate_kinetic_impact(
            projectile_mass_kg=0.2,
            projectile_velocity_mps=800.0,
            armor_material_key="gold_titanium",
            armor_thickness_mm=30.0
        )
        self.assertFalse(res_deflect["breached"])
        self.assertEqual(res_deflect["defeat_status"], "PROJECTILE_DEFLECTED_AND_ABSORBED")
        self.assertEqual(res_deflect["residual_energy_kj"], 0.0)

        # High-velocity kinetic penetrator breach
        res_breach = StructuralStressSimulator.simulate_kinetic_impact(
            projectile_mass_kg=15.0,
            projectile_velocity_mps=3500.0,
            armor_material_key="structural_steel_4130",
            armor_thickness_mm=10.0
        )
        self.assertTrue(res_breach["breached"])
        self.assertEqual(res_breach["defeat_status"], "ARMOR_BREACHED")
        self.assertGreater(res_breach["residual_energy_kj"], 0.0)

    def test_hypersonic_aerodynamics(self):
        # Mach 5 at 20,000 meters
        res = HypersonicAerodynamicsSimulator.simulate_hypersonic_profile(
            mach_number=5.0,
            altitude_m=20000.0
        )
        self.assertEqual(res["mach_number"], 5.0)
        self.assertGreater(res["velocity_kmh"], 5000.0)
        self.assertGreater(res["stagnation_temp_c"], 900.0)
        self.assertLess(res["mach_cone_angle_deg"], 15.0)
        self.assertGreater(res["stagnation_heat_flux_mw_m2"], 0.5)
        self.assertIn("COOLING", res["thermal_protection_protocol"])

    def test_arc_reactor_dynamics(self):
        # Nominal steady-state
        res = ArcReactorDynamicsSimulator.simulate_power_output(
            core_magnetic_flux_tesla=14.5,
            plasma_current_ma=2.4
        )
        self.assertAlmostEqual(res["gross_power_gw"], 2.955, places=2)
        self.assertEqual(res["status"], "MAGNETIC_CONFINEMENT_STABLE")
        self.assertGreater(res["magnetic_pressure_atm"], 500.0)

        # Combat surge (2.5x)
        surge = ArcReactorDynamicsSimulator.simulate_surge_load(
            surge_factor=2.5,
            surge_duration_s=5.0,
            baseline_gw=3.0
        )
        self.assertAlmostEqual(surge["peak_surge_gw"], 7.5, places=1)
        self.assertEqual(surge["tactical_assessment"], "SURGE_SUSTAINABLE")

    def test_orbital_mechanics(self):
        # ISS altitude orbit ~400km
        orbit = OrbitalTrajectorySimulator.simulate_circular_orbit(altitude_km=400.0)
        self.assertAlmostEqual(orbit["orbital_period_minutes"], 92.5, delta=1.0)
        self.assertAlmostEqual(orbit["orbital_velocity_mps"], 7668.0, delta=50.0)
        self.assertGreater(orbit["orbits_per_day"], 15.0)

        # Reentry deceleration
        reentry = OrbitalTrajectorySimulator.simulate_atmospheric_reentry(
            entry_velocity_mps=7850.0,
            flight_path_angle_deg=-1.5
        )
        self.assertGreater(reentry["peak_deceleration_g"], 3.0)
        self.assertLess(reentry["peak_deceleration_g"], 20.0)

    def test_fire_suppression_is_2190(self):
        fire_res = FireSuppressionDynamicsSimulator.simulate_total_flooding(
            enclosure_volume_m3=200.0,
            hazard_type="electrical_server_room",
            agent_type="co2"
        )
        self.assertTrue(fire_res["is_2190_standard_compliance"])
        self.assertGreater(fire_res["required_agent_mass_kg"], 100.0)
        self.assertLess(fire_res["residual_oxygen_pct"], 15.0)
        self.assertFalse(fire_res["atmosphere_breathable"])

    def test_unified_sandbox_dispatcher(self):
        # Test dispatcher through stark_sim_sandbox singleton
        stress = stark_sim_sandbox.run_simulation("stress", material_key="ti_6al_4v")
        self.assertIn("safety_factor_yield", stress)
        self.assertIn("execution_time_ms", stress)

        aero = stark_sim_sandbox.run_simulation("hypersonic", mach_number=3.0, altitude_m=10000.0)
        self.assertIn("stagnation_temp_c", aero)

        err = stark_sim_sandbox.run_simulation("unknown_physics_dimension")
        self.assertIn("error", err)

    def test_polyglot_runtime_integration(self):
        # In-process call through polyglot_runtime
        sim_res = polyglot_runtime.run_stark_simulation("arc_reactor")
        self.assertEqual(sim_res["status"], "MAGNETIC_CONFINEMENT_STABLE")

        # Subprocess benchmark through polyglot_runtime
        benchmark = polyglot_runtime.benchmark_stark_simulation("hypersonic", iterations=2, mach_number=4.0)
        self.assertTrue(benchmark["success"])
        self.assertEqual(benchmark["successful_passes"], 2)
        self.assertGreater(benchmark["mean_ms"], 0.0)


if __name__ == "__main__":
    unittest.main()
