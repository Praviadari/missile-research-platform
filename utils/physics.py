"""
utils/physics.py
=================
Core physics engine for the Missile Analysis & Research Platform.

All equations from standard aerospace engineering references:
  - Sutton & Biblarz: Rocket Propulsion Elements, 9th ed. (2017)
  - Tewari: Atmospheric and Space Flight Dynamics (2007)
  - Anderson: Introduction to Flight, 8th ed. (2015)
  - ICAO Doc 7488 / ISO 2533: International Standard Atmosphere

Used by: trajectory_simulator, propulsion_analysis, reentry_analysis,
         hypersonic_lab, defense_lab
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from utils.units import (
    G0, R_EARTH, RHO_SL, T_SL, R_GAS, GAMMA_AIR,
    isa_temperature, isa_density, speed_of_sound_isa,
    tsiolkovsky_delta_v,
)


# ── Drag coefficient models ────────────────────────────────────────────────────

def cd_sphere(mach: float) -> float:
    """Approximate drag coefficient for a sphere vs Mach number."""
    if mach < 0.8:   return 0.47
    if mach < 1.0:   return 0.47 + (mach - 0.8) / 0.2 * 0.53
    if mach < 1.2:   return 1.00 - (mach - 1.0) / 0.2 * 0.35
    if mach < 3.0:   return 0.65 - (mach - 1.2) / 1.8 * 0.25
    return max(0.2, 0.40 - (mach - 3.0) * 0.02)


def cd_cone_cylinder(mach: float, half_angle_deg: float = 10.0) -> float:
    """
    Approximate drag coefficient for a cone-cylinder body (missile shape).
    Based on empirical correlations from USAF Stability & Control DATCOM.
    half_angle_deg: cone half-angle in degrees
    """
    theta = math.radians(half_angle_deg)
    if mach < 0.8:
        cd_wave = 0.0
    elif mach < 1.5:
        cd_wave = 2 * (math.sin(theta)) ** 2 * (mach - 0.8) / 0.7
    else:
        # Newtonian: Cd_wave = 2 sin²θ
        cd_wave = 2 * (math.sin(theta)) ** 2
    cd_friction = 0.008   # skin friction estimate
    cd_base     = 0.10 / max(mach, 0.3)   # base drag
    return cd_wave + cd_friction + cd_base


# ── Trajectory state ───────────────────────────────────────────────────────────

@dataclass
class TrajectoryPoint:
    t:      float   # time (s)
    x:      float   # downrange (m)
    y:      float   # altitude (m)
    vx:     float   # horizontal velocity (m/s)
    vy:     float   # vertical velocity (m/s)

    @property
    def v(self) -> float:
        return math.sqrt(self.vx**2 + self.vy**2)

    @property
    def mach(self) -> float:
        sos = speed_of_sound_isa(max(0, self.y))
        return self.v / sos if sos > 0 else 0.0

    @property
    def altitude_km(self) -> float:
        return self.y / 1000.0

    @property
    def range_km(self) -> float:
        return self.x / 1000.0

    @property
    def flight_path_angle_deg(self) -> float:
        if self.v < 1e-6:
            return 0.0
        return math.degrees(math.atan2(self.vy, self.vx))

    @property
    def dynamic_pressure_pa(self) -> float:
        rho = isa_density(max(0, self.y))
        return 0.5 * rho * self.v ** 2


# ── Ballistic trajectory integrator ──────────────────────────────────────────

class BallisticTrajectory:
    """
    2-DOF point-mass trajectory integrator in a rotating-Earth-ignored
    flat-Earth frame. Includes ISA atmosphere and aerodynamic drag.

    Reference: Tewari, "Atmospheric and Space Flight Dynamics", Ch. 4
    """

    def __init__(
        self,
        launch_angle_deg: float = 45.0,
        burnout_velocity_ms: float = 3000.0,
        burnout_altitude_m: float = 80_000.0,
        cd_model: str = "cone",        # "cone" | "sphere" | "none"
        reference_area_m2: float = 0.3,  # πr² for ~30 cm radius
        ballistic_coeff_kg_m2: Optional[float] = None,  # overrides cd+area+mass
        mass_kg: float = 500.0,        # used when beta is not provided
        dt: float = 0.5,              # integration timestep (s)
    ):
        self.launch_angle    = math.radians(launch_angle_deg)
        self.v0              = burnout_velocity_ms
        self.y0              = burnout_altitude_m
        self.cd_model        = cd_model
        self.A_ref           = reference_area_m2
        self.beta            = ballistic_coeff_kg_m2  # β = m/(Cd*A)
        self.mass            = max(float(mass_kg), 1e-6)
        self.dt              = dt

    def _cd(self, mach: float) -> float:  # noqa: D401
        if self.cd_model == "none":    return 0.0
        if self.cd_model == "sphere":  return cd_sphere(mach)
        return cd_cone_cylinder(mach)

    def _accel(self, x: float, y: float, vx: float, vy: float
               ) -> Tuple[float, float]:
        """Return (ax, ay) accelerations at given state."""
        v     = math.sqrt(vx**2 + vy**2)
        alt   = max(0.0, y)
        rho   = isa_density(alt)
        sos   = speed_of_sound_isa(alt)
        mach  = v / sos if sos > 0 else 0.0
        cd    = self._cd(mach)

        # Drag deceleration a = D/m = ½ ρ v² Cd A / m  (or ½ ρ v² / β)
        if self.beta is not None:
            a_drag = 0.5 * rho * v**2 / self.beta
        elif cd <= 0.0:
            a_drag = 0.0
        else:
            a_drag = 0.5 * rho * v**2 * cd * self.A_ref / self.mass

        if v > 1e-6:
            ax = -a_drag * vx / v
            ay = -a_drag * vy / v - G0
        else:
            ax, ay = 0.0, -G0
        return ax, ay

    def simulate(self, max_time: float = 3000.0) -> List[TrajectoryPoint]:
        """
        Integrate from burnout to impact. Returns list of TrajectoryPoint.
        Uses RK4 integration.
        """
        vx = self.v0 * math.cos(self.launch_angle)
        vy = self.v0 * math.sin(self.launch_angle)
        x, y, t = 0.0, self.y0, 0.0

        points = [TrajectoryPoint(t, x, y, vx, vy)]

        while t < max_time:
            # RK4
            def f(state):
                sx, sy, svx, svy = state
                ax, ay = self._accel(sx, sy, svx, svy)
                return svx, svy, ax, ay

            s = (x, y, vx, vy)
            k1 = f(s)
            k2 = f(tuple(s[i] + self.dt/2*k1[i] for i in range(4)))
            k3 = f(tuple(s[i] + self.dt/2*k2[i] for i in range(4)))
            k4 = f(tuple(s[i] + self.dt*k3[i]   for i in range(4)))

            x  += self.dt/6 * (k1[0]+2*k2[0]+2*k3[0]+k4[0])
            y  += self.dt/6 * (k1[1]+2*k2[1]+2*k3[1]+k4[1])
            vx += self.dt/6 * (k1[2]+2*k2[2]+2*k3[2]+k4[2])
            vy += self.dt/6 * (k1[3]+2*k2[3]+2*k3[3]+k4[3])
            t  += self.dt

            points.append(TrajectoryPoint(t, x, y, vx, vy))

            if y < 0:
                # Linear interpolation to y=0
                p_prev = points[-2]
                frac   = p_prev.y / (p_prev.y - y)
                x_imp  = p_prev.x + frac * (x - p_prev.x)
                t_imp  = p_prev.t + frac * self.dt
                points[-1] = TrajectoryPoint(t_imp, x_imp, 0.0, vx, vy)
                break

        return points

    def summary(self, points: List[TrajectoryPoint]) -> dict:
        if not points:
            return {}
        peak_alt = max(p.y for p in points)
        peak_v   = max(p.v for p in points)
        peak_mach= max(p.mach for p in points)
        impact   = points[-1]
        apogee_t = next((p for p in points if p.y == peak_alt), points[0])
        return {
            "range_km":          impact.range_km,
            "flight_time_s":     impact.t,
            "apogee_km":         peak_alt / 1000,
            "apogee_time_s":     apogee_t.t,
            "impact_velocity_ms": impact.v,
            "impact_angle_deg":  abs(impact.flight_path_angle_deg),
            "peak_mach":         peak_mach,
            "peak_velocity_ms":  peak_v,
        }


# ── Propulsion calculations ────────────────────────────────────────────────────

@dataclass
class Stage:
    name:            str
    isp_s:           float       # vacuum Isp (seconds)
    mass_total_kg:   float       # total stage mass (structure + propellant)
    mass_structure_kg: float     # dry mass of stage
    thrust_kn:       float       # vacuum thrust

    @property
    def propellant_kg(self) -> float:
        return self.mass_total_kg - self.mass_structure_kg

    @property
    def mass_fraction(self) -> float:
        return self.propellant_kg / self.mass_total_kg

    @property
    def burn_time_s(self) -> float:
        if self.thrust_kn <= 0:
            return 0.0
        mdot = self.thrust_kn * 1000 / (self.isp_s * G0)
        return self.propellant_kg / mdot if mdot > 0 else 0.0

    @property
    def mass_flow_kg_s(self) -> float:
        return (self.thrust_kn * 1000) / (self.isp_s * G0)

    def delta_v(self, payload_kg: float) -> float:
        """Delta-V this stage contributes carrying given payload."""
        m0 = self.mass_total_kg + payload_kg
        mf = self.mass_structure_kg + payload_kg
        return tsiolkovsky_delta_v(self.isp_s, m0, mf)


def staging_analysis(stages: List[Stage], payload_kg: float) -> dict:
    """
    Compute total delta-V and per-stage performance for a multi-stage vehicle.
    Stages listed from first (boost) to last (upper).
    Reference: Sutton & Biblarz Ch. 4
    """
    results = []
    remaining_mass = sum(s.mass_total_kg for s in stages) + payload_kg

    cumulative_dv = 0.0
    for i, stage in enumerate(stages):
        dv = stage.delta_v(remaining_mass - stage.mass_total_kg)
        cumulative_dv += dv
        results.append({
            "stage":         stage.name,
            "isp_s":         stage.isp_s,
            "thrust_kn":     stage.thrust_kn,
            "burn_time_s":   stage.burn_time_s,
            "mass_fraction": stage.mass_fraction,
            "delta_v_ms":    dv,
            "cumulative_dv_ms": cumulative_dv,
        })
        remaining_mass -= stage.mass_total_kg

    return {
        "total_delta_v_ms":  cumulative_dv,
        "total_delta_v_kms": cumulative_dv / 1000,
        "payload_kg":        payload_kg,
        "gross_mass_kg":     sum(s.mass_total_kg for s in stages) + payload_kg,
        "stages":            results,
    }


def isp_curve(isp_vacuum: float, chamber_pressure_mpa: float = 7.0,
              altitudes_m: List[float] = None) -> List[dict]:
    """
    Compute Isp at various altitudes accounting for nozzle exit pressure.
    Uses simplified nozzle expansion model.
    Reference: Sutton & Biblarz, Chapter 3
    """
    if altitudes_m is None:
        altitudes_m = [h * 1000 for h in range(0, 85, 5)]

    # Approximate exit pressure for optimum expansion at ~10 km
    p_exit_mpa = 0.040   # typical optimised nozzle exit pressure (MPa)

    results = []
    for h in altitudes_m:
        p_amb = isa_density(h) * R_GAS * isa_temperature(h) / 1e6
        # Isp correction for ambient pressure
        # Isp_actual = Isp_vac - (p_amb - p_exit)*A_exit / (m_dot * g0)
        # Simplified: linear correction factor
        correction = max(0.0, (p_amb - p_exit_mpa) / chamber_pressure_mpa * 0.15)
        isp_actual = isp_vacuum * (1 - correction)
        results.append({
            "altitude_km": h / 1000,
            "isp_s":       max(isp_actual, isp_vacuum * 0.80),
            "ambient_mpa": p_amb,
        })
    return results


# ── Reentry heating ───────────────────────────────────────────────────────────

def stagnation_heat_flux(velocity_ms: float, altitude_m: float,
                          nose_radius_m: float = 0.15) -> float:
    """
    Stagnation-point convective heat flux (W/m²).
    Detra-Kemp-Riddell (DKR) correlation — standard reentry reference.
    Reference: Anderson, "Hypersonic and High Temperature Gas Dynamics", Ch. 6

    q_s = C * sqrt(rho/R_n) * v^3.15

    where C is an empirical constant calibrated to Apollo/Shuttle data.
    """
    rho = isa_density(altitude_m)
    if rho <= 0 or velocity_ms <= 0 or nose_radius_m <= 0:
        return 0.0
    # DKR constant (SI units)
    C = 1.83e-4
    return C * math.sqrt(rho / nose_radius_m) * velocity_ms ** 3.15


def radiative_equilibrium_temp(heat_flux_w_m2: float,
                                emissivity: float = 0.85) -> float:
    """
    Radiative equilibrium wall temperature (K).
    q = ε * σ * T^4  →  T = (q / εσ)^0.25
    Reference: Anderson, Hypersonic Gas Dynamics, Ch. 7
    """
    sigma = 5.67e-8   # Stefan-Boltzmann constant
    if heat_flux_w_m2 <= 0:
        return 300.0
    return (heat_flux_w_m2 / (emissivity * sigma)) ** 0.25


def ballistic_deceleration(beta_kg_m2: float, entry_angle_deg: float,
                            entry_velocity_ms: float,
                            altitudes_m: List[float] = None) -> List[dict]:
    """
    Chapman entry analysis — deceleration and heat rate vs altitude.
    β = m/(Cd*A) — ballistic coefficient (kg/m²)
    Reference: Chapman, "An Approximate Analytical Method for Studying Entry
    into Planetary Atmospheres" (NASA TR R-11, 1959)
    """
    if altitudes_m is None:
        altitudes_m = list(range(120_000, -1_000, -1_000))

    sin_gamma = math.sin(math.radians(abs(entry_angle_deg)))
    results = []

    for h in altitudes_m:
        h = max(0.0, h)
        rho  = isa_density(h)
        # Chapman velocity ratio: u = v/v_entry
        # Simplified: exponential atmosphere deceleration
        H    = 7_100.0   # scale height (m)
        rho0 = RHO_SL
        xi   = rho / (2 * beta_kg_m2 * sin_gamma)
        u    = math.exp(-xi)   # velocity ratio
        v    = entry_velocity_ms * u

        mach = v / max(speed_of_sound_isa(h), 1.0)
        q    = stagnation_heat_flux(v, h)
        T_w  = radiative_equilibrium_temp(q)
        a_g  = 0.5 * rho * v**2 / beta_kg_m2 / G0  # deceleration in g

        results.append({
            "altitude_km":   h / 1000,
            "velocity_ms":   v,
            "mach":          mach,
            "heat_flux_mw":  q / 1e6,
            "wall_temp_k":   T_w,
            "decel_g":       a_g,
        })

    return results


# ── Hypersonic aerodynamics ────────────────────────────────────────────────────

def newtonian_pressure_coeff(incidence_deg: float) -> float:
    """
    Newtonian impact theory: Cp = 2 sin²θ
    Valid for Mach > ~5. θ = local surface incidence angle.
    Reference: Anderson, Introduction to Flight Ch. 11
    """
    theta = math.radians(incidence_deg)
    return 2.0 * math.sin(theta) ** 2


def modified_newtonian(incidence_deg: float, mach: float) -> float:
    """
    Modified Newtonian: Cp = Cp_max * sin²θ
    Cp_max from Pitot pressure behind normal shock.
    Reference: Lees (1955), Anderson Hypersonic Ch. 3
    """
    gamma = GAMMA_AIR
    # Pitot pressure ratio (normal shock + isentropic)
    if mach < 1:
        return newtonian_pressure_coeff(incidence_deg)
    term1 = ((gamma + 1)**2 * mach**2 / (4*gamma*mach**2 - 2*(gamma-1)))**(gamma/(gamma-1))
    term2 = (1 - gamma + 2*gamma*mach**2) / (gamma + 1)
    cp_max = 2 / (gamma * mach**2) * (term1 * term2 - 1)
    theta  = math.radians(incidence_deg)
    return cp_max * math.sin(theta) ** 2


def scramjet_specific_impulse(mach_flight: float, fuel: str = "H2") -> float:
    """
    Theoretical Isp estimate for scramjet at given flight Mach.
    Based on Heiser & Pratt, "Hypersonic Airbreathing Propulsion" (1994).

    fuel: "H2" | "JP7" | "CH4"
    Returns Isp in seconds.
    """
    eta_combustion = 0.90
    eta_nozzle     = 0.95
    eta_inlet      = max(0.50, 1.0 - 0.075 * (mach_flight - 1) ** 1.35)

    # Fuel heating values (MJ/kg)
    Hf = {"H2": 120.0, "JP7": 43.5, "CH4": 50.0}.get(fuel, 43.5)

    # Available kinetic energy per kg of air
    q_flight = 0.5 * speed_of_sound_isa(25_000)**2 * mach_flight**2

    # Thermal efficiency of cycle
    eta_thermal = eta_inlet * eta_combustion * eta_nozzle
    Isp_theoretical = eta_thermal * Hf * 1e6 / (G0 * q_flight) * mach_flight
    return max(500, min(5000, Isp_theoretical * 30))  # empirically scaled


# ── Intercept geometry (educational) ─────────────────────────────────────────

def closing_velocity(target_v_ms: float, target_angle_deg: float,
                      interceptor_v_ms: float, interceptor_angle_deg: float) -> float:
    """
    Closing speed between two bodies (m/s).
    Used to illustrate why terminal intercept windows are short.
    No targeting or guidance equations — pure kinematics.
    Reference: Zarchan, "Tactical and Strategic Missile Guidance", Ch. 1
    """
    t_vx = target_v_ms * math.cos(math.radians(target_angle_deg))
    t_vy = target_v_ms * math.sin(math.radians(target_angle_deg))
    i_vx = interceptor_v_ms * math.cos(math.radians(interceptor_angle_deg))
    i_vy = interceptor_v_ms * math.sin(math.radians(interceptor_angle_deg))
    rel_vx = t_vx - i_vx
    rel_vy = t_vy - i_vy
    return math.sqrt(rel_vx**2 + rel_vy**2)


def engagement_window_s(slant_range_km: float, closing_speed_ms: float,
                         min_range_km: float = 5.0) -> float:
    """
    Time available for intercept (seconds) given current range, closing
    speed, and minimum engagement range.
    """
    if closing_speed_ms <= 0:
        return 0.0
    return max(0.0, (slant_range_km - min_range_km) * 1000 / closing_speed_ms)
