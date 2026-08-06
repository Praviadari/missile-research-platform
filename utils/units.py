"""
utils/units.py
==============
Unit conversion utilities and physical constants for missile research.

All conversions tested against SI standards. Constants from NIST and
ICAO International Standard Atmosphere (ISO 2533).
"""

import math


# ── Physical constants ─────────────────────────────────────────────────────────
G0          = 9.80665   # Standard gravity (m/s²) — NIST
R_EARTH     = 6_371_000 # Mean Earth radius (m) — WGS84 spherical approx
R_GAS       = 287.05    # Specific gas constant for dry air (J/kg·K)
GAMMA_AIR   = 1.4       # Ratio of specific heats for dry air (dimensionless)
RHO_SL      = 1.225     # ISA sea-level air density (kg/m³)
T_SL        = 288.15    # ISA sea-level temperature (K)
P_SL        = 101325.0  # ISA sea-level pressure (Pa)
MU_SL       = 1.81e-5   # Dynamic viscosity at 15°C (Pa·s)
KT_PER_MS   = 1.94384   # Knots per m/s
MACH_SL     = 340.29    # Speed of sound at sea level, ISA (m/s)


# ── Length ─────────────────────────────────────────────────────────────────────

def km_to_m(km: float) -> float:
    return km * 1000.0

def m_to_km(m: float) -> float:
    return m / 1000.0

def nm_to_km(nm: float) -> float:
    """Nautical miles to kilometres. 1 NM = 1.852 km exactly."""
    return nm * 1.852

def km_to_nm(km: float) -> float:
    return km / 1.852

def mi_to_km(mi: float) -> float:
    """Statute miles to kilometres."""
    return mi * 1.60934

def km_to_mi(km: float) -> float:
    return km / 1.60934

def ft_to_m(ft: float) -> float:
    return ft * 0.3048

def m_to_ft(m: float) -> float:
    return m / 0.3048

def inches_to_m(inches: float) -> float:
    return inches * 0.0254


# ── Mass ────────────────────────────────────────────────────────────────────────

def kg_to_lb(kg: float) -> float:
    return kg / 0.453592

def lb_to_kg(lb: float) -> float:
    return lb * 0.453592

def tonne_to_kg(t: float) -> float:
    return t * 1000.0

def kg_to_tonne(kg: float) -> float:
    return kg / 1000.0


# ── Force ───────────────────────────────────────────────────────────────────────

def kn_to_n(kn: float) -> float:
    """Kilonewtons to Newtons."""
    return kn * 1000.0

def lbf_to_n(lbf: float) -> float:
    """Pounds-force to Newtons."""
    return lbf * 4.44822

def n_to_lbf(n: float) -> float:
    return n / 4.44822


# ── Speed ───────────────────────────────────────────────────────────────────────

def ms_to_kmh(ms: float) -> float:
    return ms * 3.6

def kmh_to_ms(kmh: float) -> float:
    return kmh / 3.6

def ms_to_knots(ms: float) -> float:
    return ms * KT_PER_MS

def knots_to_ms(kts: float) -> float:
    return kts / KT_PER_MS

def mach_to_ms(mach: float, altitude_m: float = 0.0) -> float:
    """Convert Mach number to m/s at given ISA altitude."""
    sos = speed_of_sound_isa(altitude_m)
    return mach * sos

def ms_to_mach(velocity_ms: float, altitude_m: float = 0.0) -> float:
    """Convert m/s to Mach number at given ISA altitude."""
    sos = speed_of_sound_isa(altitude_m)
    return velocity_ms / sos if sos > 0 else 0.0


# ── Temperature ─────────────────────────────────────────────────────────────────

def celsius_to_kelvin(c: float) -> float:
    return c + 273.15

def kelvin_to_celsius(k: float) -> float:
    return k - 273.15

def fahrenheit_to_celsius(f: float) -> float:
    return (f - 32) * 5 / 9


# ── Pressure ─────────────────────────────────────────────────────────────────────

def pa_to_kpa(pa: float) -> float:
    return pa / 1000.0

def kpa_to_pa(kpa: float) -> float:
    return kpa * 1000.0

def pa_to_bar(pa: float) -> float:
    return pa / 100_000.0

def atm_to_pa(atm: float) -> float:
    return atm * 101_325.0

def psi_to_pa(psi: float) -> float:
    return psi * 6894.76


# ── Energy ───────────────────────────────────────────────────────────────────────

def kj_to_j(kj: float) -> float:
    return kj * 1000.0

def mj_to_j(mj: float) -> float:
    return mj * 1_000_000.0

def joules_to_tnt_equivalent(joules: float) -> float:
    """Convert joules to kg-TNT equivalent. 1 kg TNT = 4.184 MJ."""
    return joules / 4_184_000.0

def tnt_kg_to_joules(tnt_kg: float) -> float:
    return tnt_kg * 4_184_000.0


# ── Angles ───────────────────────────────────────────────────────────────────────

def deg_to_rad(deg: float) -> float:
    return math.radians(deg)

def rad_to_deg(rad: float) -> float:
    return math.degrees(rad)


# ── ISA atmosphere functions ──────────────────────────────────────────────────────

def isa_temperature(altitude_m: float) -> float:
    """
    ISA temperature at altitude (K).
    Source: ICAO Doc 7488 / ISO 2533:1975
    """
    if altitude_m <= 11_000:
        return T_SL - 0.0065 * altitude_m
    elif altitude_m <= 20_000:
        return 216.65
    elif altitude_m <= 32_000:
        return 216.65 + 0.001 * (altitude_m - 20_000)
    elif altitude_m <= 47_000:
        return 228.65 + 0.0028 * (altitude_m - 32_000)
    else:
        return 270.65  # approximate for high altitudes

def speed_of_sound_isa(altitude_m: float) -> float:
    """Speed of sound (m/s) at ISA altitude. a = sqrt(γ R T)"""
    T = max(isa_temperature(altitude_m), 1.0)
    return math.sqrt(GAMMA_AIR * R_GAS * T)

def isa_density(altitude_m: float) -> float:
    """
    ISA air density (kg/m³) at altitude.
    Uses exponential approximation for altitudes above 20 km.
    """
    h = max(0.0, altitude_m)
    if h <= 11_000:
        T  = T_SL - 0.0065 * h
        return RHO_SL * (T / T_SL) ** 4.256
    elif h <= 20_000:
        rho11 = RHO_SL * (216.65 / T_SL) ** 4.256
        return rho11 * math.exp(-0.0001577 * (h - 11_000))
    else:
        return RHO_SL * math.exp(-h / 8_500) * 0.05  # approximate


# ── Missile-specific utility functions ────────────────────────────────────────────

def dynamic_pressure(velocity_ms: float, altitude_m: float) -> float:
    """
    Dynamic pressure q = 0.5 * ρ * v² (Pa).
    Used in drag force calculation: F_drag = q * C_D * A_ref
    """
    rho = isa_density(altitude_m)
    return 0.5 * rho * velocity_ms ** 2

def haversine_range(lat1_deg: float, lon1_deg: float,
                    lat2_deg: float, lon2_deg: float) -> float:
    """
    Great-circle distance between two points (km).
    Uses Haversine formula — accurate for missile range calculations.
    """
    lat1, lon1 = math.radians(lat1_deg), math.radians(lon1_deg)
    lat2, lon2 = math.radians(lat2_deg), math.radians(lon2_deg)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 2 * R_EARTH * math.asin(math.sqrt(a)) / 1000.0

def tsiolkovsky_delta_v(isp_s: float, m_initial_kg: float, m_final_kg: float) -> float:
    """
    Tsiolkovsky rocket equation: Δv = Isp × g₀ × ln(m₀/mf)
    Returns delta-V in m/s.
    Reference: Sutton & Biblarz, Rocket Propulsion Elements, 9th ed.
    """
    if m_final_kg <= 0 or m_initial_kg <= m_final_kg:
        return 0.0
    return isp_s * G0 * math.log(m_initial_kg / m_final_kg)

def propellant_mass_fraction(delta_v_ms: float, isp_s: float) -> float:
    """
    Mass fraction consumed: ζ = 1 - exp(-Δv / (Isp × g₀))
    Returns fraction 0.0–1.0.
    """
    if isp_s <= 0:
        return 0.0
    return 1.0 - math.exp(-delta_v_ms / (isp_s * G0))

def format_range(km: float) -> str:
    """Human-readable range string."""
    if km >= 5500: return f"{km:,.0f} km (ICBM class)"
    if km >= 3000: return f"{km:,.0f} km (IRBM class)"
    if km >= 1000: return f"{km:,.0f} km (MRBM class)"
    return f"{km:,.0f} km (SRBM class)"

def format_mach(mach: float) -> str:
    """Human-readable Mach string with regime label."""
    if mach >= 5:  return f"Mach {mach:.1f} (Hypersonic)"
    if mach >= 1:  return f"Mach {mach:.1f} (Supersonic)"
    return f"Mach {mach:.2f} (Subsonic)"
