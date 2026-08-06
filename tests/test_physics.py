"""
tests/test_physics.py
======================
Tests for utils/physics.py — trajectory integration, propulsion, reentry, hypersonic.
All expected values independently derived from textbook equations.
"""

import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from utils.physics import (
    cd_sphere, cd_cone_cylinder,
    BallisticTrajectory, TrajectoryPoint,
    Stage, staging_analysis, isp_curve,
    stagnation_heat_flux, radiative_equilibrium_temp,
    ballistic_deceleration, newtonian_pressure_coeff,
    modified_newtonian, scramjet_specific_impulse,
    closing_velocity, engagement_window_s,
)
from utils.units import G0


# ── Drag models ───────────────────────────────────────────────────────────────

class TestDragModels:
    def test_sphere_subsonic(self):
        assert abs(cd_sphere(0.5) - 0.47) < 0.01

    def test_sphere_increases_transonic(self):
        assert cd_sphere(0.9) > cd_sphere(0.5)

    def test_sphere_decreases_supersonic(self):
        assert cd_sphere(5.0) < cd_sphere(1.0)

    def test_sphere_always_positive(self):
        for m in [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]:
            assert cd_sphere(m) > 0

    def test_cone_subsonic_low(self):
        cd = cd_cone_cylinder(0.5)
        assert 0.0 < cd < 0.5

    def test_cone_wave_drag_increases_with_half_angle(self):
        """At fixed Mach, blunter cones produce higher Cd."""
        assert cd_cone_cylinder(2.0, 20.0) > cd_cone_cylinder(2.0, 5.0)

    def test_cone_transonic_not_below_floor(self):
        assert cd_cone_cylinder(1.0) > 0.05

    def test_cone_always_positive(self):
        for m in [0.3, 1.0, 3.0, 8.0]:
            assert cd_cone_cylinder(m) > 0

    def test_cone_half_angle_increases_cd(self):
        assert cd_cone_cylinder(3.0, 20.0) > cd_cone_cylinder(3.0, 5.0)


# ── Trajectory simulation ─────────────────────────────────────────────────────

class TestBallisticTrajectory:
    def _sim(self, angle=45, v0=3000, h0=80000, drag="none", dt=2.0):
        sim = BallisticTrajectory(angle, v0, h0, drag, dt=dt)
        return sim, sim.simulate(max_time=4000)

    def test_returns_points(self):
        _, pts = self._sim()
        assert len(pts) > 10

    def test_starts_at_burnout_altitude(self):
        _, pts = self._sim(h0=80000)
        assert abs(pts[0].y - 80000) < 1.0

    def test_starts_at_x_zero(self):
        _, pts = self._sim()
        assert pts[0].x == 0.0

    def test_altitude_rises_then_falls(self):
        _, pts = self._sim()
        alts = [p.y for p in pts]
        peak_idx = alts.index(max(alts))
        # Altitude increases before peak and decreases after
        assert alts[0] < max(alts)
        assert alts[-1] < max(alts)
        assert peak_idx > 0

    def test_range_positive(self):
        _, pts = self._sim()
        assert pts[-1].x > 0

    def test_impacts_at_zero_altitude(self):
        _, pts = self._sim()
        assert abs(pts[-1].y) < 100  # within 100 m of ground

    def test_45_degree_max_range(self):
        """45° should give near-maximum range in vacuum."""
        _, pts30 = self._sim(angle=30, drag="none")
        _, pts45 = self._sim(angle=45, drag="none")
        _, pts60 = self._sim(angle=60, drag="none")
        r30 = pts30[-1].x
        r45 = pts45[-1].x
        r60 = pts60[-1].x
        # 45 should have max or near-max range
        assert r45 >= r30 * 0.95
        assert r45 >= r60 * 0.95

    def test_higher_velocity_longer_range(self):
        _, pts1 = self._sim(v0=2000, drag="none")
        _, pts2 = self._sim(v0=4000, drag="none")
        assert pts2[-1].x > pts1[-1].x

    def test_drag_reduces_range(self):
        _, pts_no_drag   = self._sim(drag="none")
        _, pts_with_drag = self._sim(drag="cone")
        assert pts_with_drag[-1].x < pts_no_drag[-1].x

    def test_drag_uses_mass_and_area(self):
        """Heavier mass (same Cd·A) → less deceleration → longer range."""
        light = BallisticTrajectory(
            45, 3000, 80_000, "cone",
            reference_area_m2=0.3, mass_kg=200.0, dt=1.0,
        )
        heavy = BallisticTrajectory(
            45, 3000, 80_000, "cone",
            reference_area_m2=0.3, mass_kg=2000.0, dt=1.0,
        )
        r_light = light.simulate()[-1].x
        r_heavy = heavy.simulate()[-1].x
        assert r_heavy > r_light

    def test_ballistic_coeff_overrides_mass_area(self):
        a = BallisticTrajectory(
            45, 2500, 60_000, "cone",
            ballistic_coeff_kg_m2=800.0, mass_kg=100.0, dt=1.0,
        )
        b = BallisticTrajectory(
            45, 2500, 60_000, "cone",
            ballistic_coeff_kg_m2=800.0, mass_kg=9000.0, dt=1.0,
        )
        assert abs(a.simulate()[-1].x - b.simulate()[-1].x) < 1.0

    def test_velocity_always_positive(self):
        _, pts = self._sim()
        for p in pts:
            assert p.v >= 0

    def test_mach_positive(self):
        _, pts = self._sim()
        for p in pts:
            assert p.mach >= 0

    def test_summary_keys(self):
        sim, pts = self._sim()
        s = sim.summary(pts)
        for key in ["range_km","flight_time_s","apogee_km","peak_mach"]:
            assert key in s

    def test_summary_range_positive(self):
        sim, pts = self._sim()
        assert sim.summary(pts)["range_km"] > 0

    def test_summary_apogee_above_burnout(self):
        sim, pts = self._sim(h0=80000)
        s = sim.summary(pts)
        assert s["apogee_km"] >= 80.0

    def test_trajectory_point_properties(self):
        p = TrajectoryPoint(t=10, x=5000, y=80000, vx=2000, vy=500)
        assert p.v == pytest.approx(math.sqrt(2000**2 + 500**2), rel=1e-6)
        assert p.range_km == pytest.approx(5.0, rel=1e-6)
        assert p.altitude_km == pytest.approx(80.0, rel=1e-6)
        assert p.dynamic_pressure_pa > 0


# ── Staging analysis ──────────────────────────────────────────────────────────

class TestStagingAnalysis:
    def _two_stage(self):
        s1 = Stage("S1", 280, 15000, 1200, 600)
        s2 = Stage("S2",  280, 8000,  640, 250)
        return [s1, s2], 500

    def test_returns_total_dv(self):
        stages, payload = self._two_stage()
        result = staging_analysis(stages, payload)
        assert "total_delta_v_ms" in result

    def test_total_dv_positive(self):
        stages, payload = self._two_stage()
        result = staging_analysis(stages, payload)
        assert result["total_delta_v_ms"] > 0

    def test_stage_count_matches(self):
        stages, payload = self._two_stage()
        result = staging_analysis(stages, payload)
        assert len(result["stages"]) == 2

    def test_cumulative_dv_increases(self):
        stages, payload = self._two_stage()
        result = staging_analysis(stages, payload)
        cumulative = [s["cumulative_dv_ms"] for s in result["stages"]]
        assert cumulative[-1] > cumulative[0]

    def test_three_stages_more_dv_than_one(self):
        s1 = Stage("S1", 280, 15000, 1200, 600)
        result1 = staging_analysis([s1], 500)
        s2 = Stage("S2", 280, 8000, 640, 250)
        s3 = Stage("S3", 280, 3000, 240, 100)
        result3 = staging_analysis([s1, s2, s3], 500)
        assert result3["total_delta_v_ms"] > result1["total_delta_v_ms"]

    def test_stage_burn_time_positive(self):
        s = Stage("S1", 280, 15000, 1200, 600)
        assert s.burn_time_s > 0

    def test_stage_propellant_mass(self):
        s = Stage("S1", 280, 15000, 1200, 600)
        assert s.propellant_kg == pytest.approx(15000 - 1200, rel=1e-9)

    def test_stage_mass_fraction(self):
        s = Stage("S1", 280, 15000, 1200, 600)
        assert 0 < s.mass_fraction < 1

    def test_isp_curve_returns_data(self):
        curve = isp_curve(280)
        assert len(curve) > 0
        assert all("isp_s" in c for c in curve)

    def test_isp_curve_increases_with_altitude(self):
        curve = isp_curve(280)
        # Isp at higher altitude should be >= Isp at sea level
        isp_sl  = curve[0]["isp_s"]
        isp_vac = curve[-1]["isp_s"]
        assert isp_vac >= isp_sl


# ── Reentry heating ───────────────────────────────────────────────────────────

class TestReentryHeating:
    def test_heat_flux_positive(self):
        q = stagnation_heat_flux(7000, 60000, 0.20)
        assert q > 0

    def test_heat_flux_increases_with_velocity(self):
        q1 = stagnation_heat_flux(5000, 40000, 0.20)
        q2 = stagnation_heat_flux(7000, 40000, 0.20)
        assert q2 > q1

    def test_heat_flux_decreases_with_altitude(self):
        # Higher altitude → less density → less heating
        q1 = stagnation_heat_flux(7000, 30000, 0.20)
        q2 = stagnation_heat_flux(7000, 60000, 0.20)
        assert q1 > q2

    def test_heat_flux_zero_at_zero_velocity(self):
        assert stagnation_heat_flux(0, 40000, 0.20) == 0.0

    def test_heat_flux_decreases_with_nose_radius(self):
        # Larger nose → lower heat flux per unit area
        q_sharp = stagnation_heat_flux(7000, 40000, 0.05)
        q_blunt = stagnation_heat_flux(7000, 40000, 1.00)
        assert q_sharp > q_blunt

    def test_wall_temp_positive(self):
        T = radiative_equilibrium_temp(1e6)
        assert T > 0

    def test_wall_temp_increases_with_flux(self):
        T1 = radiative_equilibrium_temp(1e5)
        T2 = radiative_equilibrium_temp(1e7)
        assert T2 > T1

    def test_wall_temp_baseline_at_zero_flux(self):
        T = radiative_equilibrium_temp(0)
        assert T == pytest.approx(300.0, abs=1.0)

    def test_ballistic_decel_returns_data(self):
        data = ballistic_deceleration(5000, 10.0, 7000)
        assert len(data) > 10

    def test_ballistic_decel_altitude_decreasing(self):
        data = ballistic_deceleration(5000, 10.0, 7000)
        alts = [d["altitude_km"] for d in data]
        assert alts[0] > alts[-1]

    def test_ballistic_decel_velocity_positive(self):
        data = ballistic_deceleration(5000, 10.0, 7000)
        for d in data:
            assert d["velocity_ms"] >= 0


# ── Newtonian aerodynamics ────────────────────────────────────────────────────

class TestNewtonianAero:
    def test_newtonian_zero_at_zero_angle(self):
        assert newtonian_pressure_coeff(0) == pytest.approx(0.0, abs=1e-9)

    def test_newtonian_max_at_90(self):
        assert newtonian_pressure_coeff(90) == pytest.approx(2.0, rel=1e-4)

    def test_newtonian_increases_with_angle(self):
        assert newtonian_pressure_coeff(60) > newtonian_pressure_coeff(30)

    def test_modified_newtonian_positive(self):
        for angle in [10, 30, 45, 60, 90]:
            assert modified_newtonian(angle, 10) >= 0

    def test_modified_newtonian_less_than_newtonian_at_finite_mach(self):
        # Modified Newtonian uses Cp_max < 2 at finite Mach
        mn_pure = newtonian_pressure_coeff(45)
        mn_mod  = modified_newtonian(45, 8)
        assert mn_mod <= mn_pure + 0.01  # allow floating point

    def test_scramjet_isp_positive(self):
        for mach in [5, 8, 10, 15, 20]:
            assert scramjet_specific_impulse(mach) > 0

    def test_scramjet_min_mach_5(self):
        # Below Mach 5, scramjet doesn't function — function still returns a value but
        # the valid regime starts at 5
        isp5  = scramjet_specific_impulse(5)
        isp10 = scramjet_specific_impulse(10)
        assert isp5 > 0 and isp10 > 0


# ── Intercept kinematics ──────────────────────────────────────────────────────

class TestInterceptKinematics:
    def test_closing_velocity_positive(self):
        vc = closing_velocity(2500, 45, 2000, 135)
        assert vc > 0

    def test_closing_velocity_head_on_max(self):
        vc_head_on  = closing_velocity(2500,  0, 2500, 180)
        vc_parallel = closing_velocity(2500,  0, 2500,   0)
        assert vc_head_on > vc_parallel

    def test_engagement_window_positive(self):
        t = engagement_window_s(100, 3000, 10)
        assert t > 0

    def test_engagement_window_decreases_with_closing_speed(self):
        t_slow = engagement_window_s(100, 1000, 10)
        t_fast = engagement_window_s(100, 5000, 10)
        assert t_slow > t_fast

    def test_engagement_window_zero_when_range_equals_min(self):
        t = engagement_window_s(10, 2000, 10)
        assert t == pytest.approx(0.0, abs=0.01)

    def test_engagement_window_increases_with_range(self):
        t1 = engagement_window_s(50,  2000, 10)
        t2 = engagement_window_s(200, 2000, 10)
        assert t2 > t1
