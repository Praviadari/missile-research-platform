"""
tests/test_units.py — Unit conversion and physics constant tests.
All assertions verified against SI standards and ICAO ISA (ISO 2533).
"""
import math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from utils.units import (
    km_to_m, m_to_km, nm_to_km, km_to_nm, mi_to_km, ft_to_m, m_to_ft,
    kg_to_lb, lb_to_kg, ms_to_kmh, kmh_to_ms, ms_to_knots, knots_to_ms,
    mach_to_ms, ms_to_mach, celsius_to_kelvin, kelvin_to_celsius,
    fahrenheit_to_celsius, pa_to_kpa, atm_to_pa, psi_to_pa,
    joules_to_tnt_equivalent, tnt_kg_to_joules,
    isa_temperature, speed_of_sound_isa, isa_density,
    dynamic_pressure, haversine_range,
    tsiolkovsky_delta_v, propellant_mass_fraction,
    format_range, format_mach,
    G0, RHO_SL, T_SL, P_SL, MACH_SL, R_EARTH,
)

class TestConstants:
    def test_standard_gravity(self):       assert abs(G0 - 9.80665) < 1e-5
    def test_sea_level_density(self):      assert abs(RHO_SL - 1.225) < 0.001
    def test_sea_level_temperature(self):  assert abs(T_SL - 288.15) < 0.01
    def test_sea_level_pressure(self):     assert abs(P_SL - 101325) < 1
    def test_speed_of_sound_sl(self):      assert abs(MACH_SL - 340.29) < 0.5
    def test_earth_radius(self):           assert 6_350_000 < R_EARTH < 6_400_000

class TestLength:
    def test_km_to_m(self):         assert km_to_m(1.0) == 1000.0
    def test_m_to_km(self):         assert m_to_km(1000.0) == 1.0
    def test_nm_to_km(self):        assert abs(nm_to_km(1.0) - 1.852) < 1e-10
    def test_roundtrip_nm(self):    assert abs(km_to_nm(nm_to_km(500.0)) - 500.0) < 1e-8
    def test_mi_to_km(self):        assert abs(mi_to_km(1.0) - 1.60934) < 0.0001
    def test_ft_to_m(self):         assert abs(ft_to_m(1.0) - 0.3048) < 1e-10
    def test_roundtrip_ft(self):    assert abs(m_to_ft(ft_to_m(10000.0)) - 10000.0) < 1e-6

class TestMass:
    def test_kg_to_lb(self):        assert abs(kg_to_lb(1.0) - 2.20462) < 0.001
    def test_lb_to_kg(self):        assert abs(lb_to_kg(1.0) - 0.453592) < 0.0001
    def test_roundtrip_mass(self):  assert abs(lb_to_kg(kg_to_lb(1000.0)) - 1000.0) < 1e-6

class TestSpeed:
    def test_ms_to_kmh(self):           assert abs(ms_to_kmh(1.0) - 3.6) < 1e-10
    def test_kmh_to_ms(self):           assert abs(kmh_to_ms(3.6) - 1.0) < 1e-10
    def test_ms_to_knots(self):         assert abs(ms_to_knots(1.0) - 1.94384) < 0.0001
    def test_roundtrip_kmh(self):       assert abs(kmh_to_ms(ms_to_kmh(300.0)) - 300.0) < 1e-8
    def test_roundtrip_knots(self):     assert abs(knots_to_ms(ms_to_knots(300.0)) - 300.0) < 1e-8
    def test_mach1_sea_level(self):     v = mach_to_ms(1.0, 0.0); assert 338 < v < 342
    def test_mach_increases(self):      assert mach_to_ms(2.0, 0) > mach_to_ms(1.0, 0)
    def test_roundtrip_mach(self):
        mach = ms_to_mach(1000.0, 10000)
        assert abs(mach_to_ms(mach, 10000) - 1000.0) < 0.1

class TestTemperature:
    def test_0c_in_kelvin(self):            assert abs(celsius_to_kelvin(0) - 273.15) < 1e-10
    def test_absolute_zero(self):           assert abs(celsius_to_kelvin(-273.15) - 0) < 1e-10
    def test_kelvin_to_c(self):             assert abs(kelvin_to_celsius(273.15) - 0) < 1e-10
    def test_fahrenheit_freezing(self):     assert abs(fahrenheit_to_celsius(32) - 0) < 1e-10
    def test_fahrenheit_boiling(self):      assert abs(fahrenheit_to_celsius(212) - 100) < 1e-10
    def test_fahrenheit_minus40(self):      assert abs(fahrenheit_to_celsius(-40) - (-40)) < 1e-10

class TestISA:
    def test_temperature_sea_level(self):       assert abs(isa_temperature(0) - 288.15) < 0.01
    def test_temperature_tropopause(self):      assert abs(isa_temperature(11_000) - 216.65) < 0.01
    def test_stratosphere_isothermal(self):     assert abs(isa_temperature(15_000) - 216.65) < 0.1
    def test_temperature_decreases_troposphere(self):
        assert isa_temperature(0) > isa_temperature(5_000) > isa_temperature(11_000)
    def test_density_sea_level(self):           assert abs(isa_density(0) - 1.225) < 0.005
    def test_density_decreases(self):           assert isa_density(0) > isa_density(10_000) > isa_density(50_000)
    def test_density_always_positive(self):
        for alt in [0, 10_000, 50_000, 80_000]: assert isa_density(alt) > 0
    def test_sos_sea_level(self):               assert 338 < speed_of_sound_isa(0) < 343
    def test_sos_lower_at_altitude(self):       assert speed_of_sound_isa(0) > speed_of_sound_isa(10_000)
    def test_sos_isothermal_stratosphere(self):
        assert abs(speed_of_sound_isa(12_000) - speed_of_sound_isa(18_000)) < 2.0

class TestDynamicPressure:
    def test_increases_with_velocity(self):     assert dynamic_pressure(500, 0) > dynamic_pressure(300, 0)
    def test_decreases_with_altitude(self):     assert dynamic_pressure(1000, 0) > dynamic_pressure(1000, 20_000)
    def test_zero_at_zero_velocity(self):       assert dynamic_pressure(0, 0) == 0.0
    def test_formula_correct(self):
        v, h = 500.0, 0.0
        rho = isa_density(h)
        assert abs(dynamic_pressure(v, h) - 0.5 * rho * v**2) < 1e-6

class TestHaversine:
    def test_same_point_zero(self):             assert haversine_range(35.0, 35.0, 35.0, 35.0) < 0.01
    def test_london_to_paris(self):
        d = haversine_range(51.5, -0.1, 48.9, 2.3)
        assert 330 < d < 360
    def test_symmetric(self):
        assert abs(haversine_range(35, 36, 32, 35) - haversine_range(32, 35, 35, 36)) < 0.1
    def test_positive(self):                    assert haversine_range(0, 0, 10, 10) > 0

class TestRocketEquation:
    def test_positive_dv(self):                 assert tsiolkovsky_delta_v(280, 10000, 3000) > 0
    def test_higher_isp_more_dv(self):
        assert tsiolkovsky_delta_v(350, 10000, 3000) > tsiolkovsky_delta_v(250, 10000, 3000)
    def test_higher_mass_ratio_more_dv(self):
        assert tsiolkovsky_delta_v(280, 10000, 3000) > tsiolkovsky_delta_v(280, 5000, 3000)
    def test_no_propellant_zero_dv(self):       assert tsiolkovsky_delta_v(280, 5000, 5000) == 0.0
    def test_invalid_final_mass_zero_dv(self):  assert tsiolkovsky_delta_v(280, 5000, 6000) == 0.0
    def test_known_value(self):
        # Isp=280s, mass ratio=4 → Δv = 280 * 9.80665 * ln(4) ≈ 3,802 m/s
        assert abs(tsiolkovsky_delta_v(280, 4000, 1000) - 3802) < 50
    def test_pmf_between_0_and_1(self):
        pmf = propellant_mass_fraction(3000, 280)
        assert 0 < pmf < 1
    def test_pmf_increases_with_dv(self):
        assert propellant_mass_fraction(4000, 280) > propellant_mass_fraction(2000, 280)
    def test_pmf_decreases_with_isp(self):
        assert propellant_mass_fraction(3000, 350) < propellant_mass_fraction(3000, 250)
    def test_roundtrip_consistency(self):
        isp, m0, mf = 280, 10000, 3000
        dv = tsiolkovsky_delta_v(isp, m0, mf)
        pmf_expected = (m0 - mf) / m0
        assert abs(propellant_mass_fraction(dv, isp) - pmf_expected) < 0.01

class TestFormatters:
    def test_srbm(self):            assert "SRBM" in format_range(500)
    def test_mrbm(self):            assert "MRBM" in format_range(1500)
    def test_irbm(self):            assert "IRBM" in format_range(4000)
    def test_icbm(self):            assert "ICBM" in format_range(8000)
    def test_subsonic(self):        assert "Subsonic" in format_mach(0.8)
    def test_supersonic(self):      assert "Supersonic" in format_mach(3.0)
    def test_hypersonic(self):      assert "Hypersonic" in format_mach(7.0)
    def test_hypersonic_boundary(self): assert "Hypersonic" in format_mach(5.0)
