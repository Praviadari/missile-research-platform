"""
modules/hypersonic_lab.py
==========================
Hypersonic aerodynamics and propulsion deep-dive.

Topics: Mach regimes, HGV vs ballistic trajectory comparison,
        scramjet performance, Newtonian pressure, shock relations.

References:
  - Anderson, "Hypersonic and High Temperature Gas Dynamics", AIAA 2006
  - Heiser & Pratt, "Hypersonic Airbreathing Propulsion", AIAA 1994
  - Bertin & Cummings, "Fifty Years of Hypersonics", Progress in Aerospace Sciences 2003

Pro-gated page.
"""

import math
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.theme import card, section_header, sub_header, badge
from ui.charts import apply_theme, COLORS
from utils.physics import (
    newtonian_pressure_coeff, modified_newtonian, scramjet_specific_impulse,
    BallisticTrajectory, speed_of_sound_isa, stagnation_heat_flux,
    radiative_equilibrium_temp,
)
from utils.units import G0

# ── Mach regime reference ─────────────────────────────────────────────────────
MACH_REGIMES = [
    (0,    0.8,  "Subsonic",       "#3498DB", "Incompressible (M<0.3) to compressible flow"),
    (0.8,  1.2,  "Transonic",      "#2ECC71", "Mixed subsonic/supersonic regions, shock formation"),
    (1.2,  5.0,  "Supersonic",     "#F39C12", "Oblique shocks, Mach cone, supersonic expansion"),
    (5.0,  10.0, "Hypersonic",     "#E74C3C", "High-temperature effects, shock-layer chemistry"),
    (10.0, 25.0, "High Hypersonic","#9B59B6", "Radiation heating, real-gas effects, ablation"),
]

# ── Real hypersonic systems (public data) ─────────────────────────────────────
HYPERSONIC_SYSTEMS = {
    "DF-ZF / WU-14 (China)": {
        "type": "HGV", "mach": 10, "range_km": 2000,
        "alt_km": 60, "mass_kg": 2000, "source": "US DoD China Military Power 2023",
    },
    "Avangard (Russia)": {
        "type": "HGV", "mach": 27, "range_km": 6000,
        "alt_km": 100, "mass_kg": 2000, "source": "IISS Strategic Survey 2022",
    },
    "Kinzhal (Russia)": {
        "type": "Air-launched ballistic", "mach": 10, "range_km": 2000,
        "alt_km": 40, "mass_kg": 480, "source": "IISS Military Balance 2023",
    },
    "Zircon (Russia)": {
        "type": "Scramjet cruise", "mach": 9, "range_km": 1000,
        "alt_km": 30, "mass_kg": 400, "source": "IISS Military Balance 2023",
    },
    "ARRW AGM-183A (USA)": {
        "type": "HGV (TBGB)", "mach": 20, "range_km": 925,
        "alt_km": 60, "mass_kg": 900, "source": "USAF Programme Acquisition, FY2024",
    },
    "Fattah-2 (Iran)": {
        "type": "Hypersonic ballistic", "mach": 15, "range_km": 1500,
        "alt_km": 80, "mass_kg": 500, "source": "CSIS Missile Threat, 2023",
    },
}


def render():
    st.title("⚡ Hypersonic Lab")
    st.caption(
        "Hypersonic aerodynamics, propulsion, and vehicle comparison. "
        "Anderson (2006), Heiser & Pratt (1994), Bertin & Cummings (2003)."
    )

    tabs = st.tabs([
        "🌡️ Mach Regimes",
        "✈️ HGV vs Ballistic",
        "🔥 Scramjet Performance",
        "📐 Newtonian Aerodynamics",
        "🚀 Vehicle Reference",
    ])
    with tabs[0]: _mach_regimes()
    with tabs[1]: _hgv_vs_ballistic()
    with tabs[2]: _scramjet()
    with tabs[3]: _newtonian()
    with tabs[4]: _vehicle_reference()


def _mach_regimes():
    st.markdown(section_header("🌡️ Mach Flight Regimes"), unsafe_allow_html=True)

    # Regime band chart
    import numpy as np
    machs = np.linspace(0, 25, 500)
    fig = go.Figure()

    for m_lo, m_hi, name, color, desc in MACH_REGIMES:
        mask = (machs >= m_lo) & (machs <= m_hi)
        # Show a filled band
        fig.add_vrect(x0=m_lo, x1=m_hi,
                      fillcolor=color, opacity=0.15,
                      layer="below", line_width=0,
                      annotation_text=name,
                      annotation_position="top left",
                      annotation_font_color=color,
                      annotation_font_size=11)

    # Stagnation temperature line
    def T_stag(mach):
        return 216.65 * (1 + 0.2 * mach**2)  # ISA stratosphere stagnation

    T_vals = [T_stag(m) for m in machs]
    fig.add_trace(go.Scatter(
        x=list(machs), y=T_vals, name="Stagnation temp (K)",
        mode="lines", line=dict(color="#E74C3C", width=2),
        hovertemplate="Mach %{x:.1f}<br>T_stag = %{y:.0f} K<extra></extra>",
    ))

    # Known system markers
    for name, s in HYPERSONIC_SYSTEMS.items():
        T_s = T_stag(s["mach"])
        fig.add_trace(go.Scatter(
            x=[s["mach"]], y=[T_s],
            mode="markers+text", marker=dict(size=10, color="#FFD700"),
            text=[name.split("(")[0].strip()],
            textposition="top center",
            textfont=dict(size=9, color="#FFD700"),
            showlegend=False,
            hovertemplate=f"{name}<br>Mach {s['mach']}<br>T_stag={T_s:.0f} K<extra></extra>",
        ))

    fig.update_layout(**apply_theme(title="Stagnation Temperature vs Mach Number"),
                      height=380, showlegend=True)
    fig.update_xaxes(title_text="Mach Number", gridcolor="#1E2235", zeroline=False, range=[0,25])
    fig.update_yaxes(title_text="Stagnation Temperature (K)", gridcolor="#1E2235", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)

    # Regime cards
    for m_lo, m_hi, name, color, desc in MACH_REGIMES:
        phenomena = _regime_phenomena(name)
        st.markdown(
            card(
                f"<span style='color:{color};font-weight:700'>{name}</span>  "
                f"<span style='color:#6B6F84'>Mach {m_lo}–{m_hi}</span><br>"
                f"{desc}<br>"
                f"<span style='font-size:0.82rem;color:#8B9AC7'>{phenomena}</span>",
                variant="plain",
            ),
            unsafe_allow_html=True,
        )


def _regime_phenomena(name: str) -> str:
    return {
        "Subsonic":       "Bernoulli applicable. Lift/drag well-described by potential flow.",
        "Transonic":      "Shock-induced separation. Wave drag onset. Buffeting.",
        "Supersonic":     "Oblique shocks. Mach cone. Area rule design. Drag divergence.",
        "Hypersonic":     "Viscous interaction. Shock-shock interference. Ablation begins.",
        "High Hypersonic":"Radiative heating dominant. Ionisation. Plasma sheath (comms blackout).",
    }.get(name, "")


def _hgv_vs_ballistic():
    st.markdown(section_header("✈️ HGV vs Ballistic Trajectory"), unsafe_allow_html=True)
    st.markdown(
        "A Hypersonic Glide Vehicle (HGV) skips along the upper atmosphere using "
        "aerodynamic lift to extend range and vary trajectory. A ballistic reentry "
        "vehicle follows a classical parabolic arc. This illustrates the differences "
        "in altitude profile and radar detection geometry."
    )

    col1, col2 = st.columns(2)
    with col1:
        v0   = st.slider("Burnout velocity (m/s)", 3000, 7500, 5500, step=100, key="hgv_v0")
        ang  = st.slider("Launch angle (°)", 15, 60, 30, key="hgv_ang")
    with col2:
        glide_factor = st.slider("HGV lift factor (L/D ratio)", 1.0, 6.0, 3.5, step=0.5)
        st.caption("L/D = 0 → pure ballistic. L/D ≈ 3–5 for practical HGVs.")

    # Ballistic trajectory
    sim_b = BallisticTrajectory(
        launch_angle_deg=ang, burnout_velocity_ms=v0,
        burnout_altitude_m=80_000, cd_model="cone", dt=2.0,
    )
    pts_b = sim_b.simulate(max_time=4000)
    sum_b = sim_b.summary(pts_b)

    # HGV approximation: boost-glide with lift extending range
    # Simplified: scale downrange by L/D factor, reduce max altitude by glide pull
    glide_range_mult = 1.0 + glide_factor * 0.25
    pts_hgv = []
    for p in pts_b:
        # HGV maintains lower sustained altitude during glide phase
        if p.altitude_km > 20 and p.t > 60:
            # During glide phase, altitude is modulated by lift
            glide_alt = p.altitude_km * (1 - glide_factor * 0.04)
            glide_alt = max(20, glide_alt)
        else:
            glide_alt = p.altitude_km
        from utils.physics import TrajectoryPoint
        pts_hgv.append(TrajectoryPoint(
            p.t, p.x * glide_range_mult, glide_alt * 1000, p.vx, p.vy
        ))

    hgv_range = pts_hgv[-1].range_km if pts_hgv else sum_b["range_km"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ballistic range",  f"{sum_b['range_km']:.0f} km")
    col2.metric("HGV range (est.)", f"{hgv_range:.0f} km",
                delta=f"+{hgv_range-sum_b['range_km']:.0f} km")
    col3.metric("Ballistic apogee", f"{sum_b['apogee_km']:.0f} km")
    col4.metric("HGV glide alt",    "20–60 km")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[p.range_km for p in pts_b],
        y=[p.altitude_km for p in pts_b],
        name="Ballistic RV", mode="lines",
        line=dict(color=COLORS[0], width=2, dash="solid"),
    ))
    fig.add_trace(go.Scatter(
        x=[p.range_km for p in pts_hgv],
        y=[p.altitude_km for p in pts_hgv],
        name="HGV (estimated)", mode="lines",
        line=dict(color=COLORS[4], width=2, dash="dash"),
    ))
    # Radar horizon band (illustrative)
    fig.add_hrect(y0=0, y1=30, fillcolor="rgba(231,76,60,0.05)",
                  line_width=0, annotation_text="Below-horizon threat window",
                  annotation_font_size=9, annotation_font_color="#E74C3C")

    fig.update_layout(**apply_theme(title="Altitude Profile Comparison"), height=360, showlegend=True)
    fig.update_xaxes(title_text="Downrange (km)", gridcolor="#1E2235", zeroline=False)
    fig.update_yaxes(title_text="Altitude (km)", gridcolor="#1E2235", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        card(
            "📌 <strong>Why HGVs are challenging for interceptors:</strong> "
            "Their sustained lower altitude (20–60 km) compared to ICBM apogee (1,000+ km) "
            "reduces radar detection time. The variable trajectory makes trajectory prediction "
            "harder. Most existing interceptors are optimised for the higher-altitude "
            "exo-atmospheric phase that HGVs avoid. "
            "<em>Source: RAND PE-243 (2017); Gubrud, 'Hypersonic Weapons and Strategic Stability'</em>",
            variant="info",
        ),
        unsafe_allow_html=True,
    )


def _scramjet():
    st.markdown(section_header("🔥 Scramjet Performance"), unsafe_allow_html=True)
    st.markdown(
        "A scramjet (supersonic combustion ramjet) combusts fuel in a supersonic airstream, "
        "making it viable only above ~Mach 5. Below that speed, a turbojet or rocket "
        "accelerator is required. Reference: Heiser & Pratt (1994)."
    )

    fuels = ["H2", "JP7", "CH4"]
    mach_range = [m/2 for m in range(10, 51)]  # Mach 5–25

    fig = go.Figure()
    for i, fuel in enumerate(fuels):
        isps = [scramjet_specific_impulse(m, fuel) for m in mach_range]
        fig.add_trace(go.Scatter(
            x=mach_range, y=isps, name=f"Scramjet ({fuel})",
            mode="lines", line=dict(color=COLORS[i], width=2),
        ))

    # Solid rocket reference line
    fig.add_hline(y=280, line_dash="dot", line_color="#6B6F84",
                  annotation_text="Solid rocket Isp (~280 s)", annotation_font_size=9)
    fig.add_hline(y=450, line_dash="dot", line_color="#3498DB",
                  annotation_text="LOX/LH₂ Isp (~450 s)", annotation_font_size=9)
    fig.add_vline(x=5, line_dash="dash", line_color="#E74C3C",
                  annotation_text="Scramjet lower limit", annotation_font_size=9)

    fig.update_layout(**apply_theme(title="Scramjet Specific Impulse vs Mach Number"),
                      height=360, showlegend=True)
    fig.update_xaxes(title_text="Flight Mach Number", gridcolor="#1E2235", zeroline=False)
    fig.update_yaxes(title_text="Specific Impulse (s)", gridcolor="#1E2235", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        mach_q = st.slider("Query Mach", 5.0, 25.0, 8.0, step=0.5)
        fuel_q = st.selectbox("Fuel", fuels)
        isp_q  = scramjet_specific_impulse(mach_q, fuel_q)
        st.metric(f"Isp at Mach {mach_q} ({fuel_q})", f"{isp_q:.0f} s")

    with col2:
        st.markdown(
            card(
                "📌 <strong>Why hydrogen scramjets dominate research:</strong> "
                "H₂ has the highest heating value (120 MJ/kg vs 43.5 MJ/kg for JP-7) "
                "and ignites reliably in supersonic flow. However, cryogenic storage and "
                "volume requirements make it impractical for most missile applications, "
                "which favour hydrocarbon fuels (JP-7, syntin) despite lower Isp.",
                variant="info",
            ),
            unsafe_allow_html=True,
        )


def _newtonian():
    st.markdown(section_header("📐 Newtonian Pressure Theory"), unsafe_allow_html=True)
    st.latex(r"C_p = 2\sin^2\theta \quad \text{(Newtonian)}")
    st.latex(r"C_p = C_{p,max}\sin^2\theta \quad \text{(Modified Newtonian)}")

    angles = list(range(0, 91, 2))
    machs_plot = [5, 10, 15, 20]

    fig = go.Figure()
    for i, m in enumerate(machs_plot):
        cps = [modified_newtonian(a, m) for a in angles]
        fig.add_trace(go.Scatter(
            x=angles, y=cps, name=f"Mach {m}", mode="lines",
            line=dict(color=COLORS[i], width=2),
        ))
    # Pure Newtonian
    fig.add_trace(go.Scatter(
        x=angles,
        y=[newtonian_pressure_coeff(a) for a in angles],
        name="Pure Newtonian",
        mode="lines", line=dict(color="#6B6F84", width=1, dash="dot"),
    ))

    fig.update_layout(**apply_theme(title="Pressure Coefficient vs Surface Incidence"),
                      height=360, showlegend=True)
    fig.update_xaxes(title_text="Incidence Angle θ (°)", gridcolor="#1E2235", zeroline=False)
    fig.update_yaxes(title_text="Pressure Coefficient Cp", gridcolor="#1E2235", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        "Newtonian theory assumes all momentum normal to the surface is transferred to the body. "
        "Modified Newtonian replaces the constant '2' with Cp_max from normal shock relations, "
        "giving better accuracy at finite Mach numbers. Both are valid only for M > ~5."
    )


def _vehicle_reference():
    st.markdown(section_header("🚀 Hypersonic Vehicle Reference"), unsafe_allow_html=True)
    st.caption("All data from public sources: US DoD annual reports, IISS Military Balance, CSIS Missile Threat.")

    import pandas as pd
    rows = []
    for name, s in HYPERSONIC_SYSTEMS.items():
        rows.append({
            "System":     name,
            "Type":       s["type"],
            "Peak Mach":  s["mach"],
            "Range (km)": s["range_km"],
            "Alt (km)":   s["alt_km"],
            "Mass (kg)":  s["mass_kg"],
            "Source":     s["source"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # Mach vs range scatter
    fig = go.Figure()
    for i, (name, s) in enumerate(HYPERSONIC_SYSTEMS.items()):
        fig.add_trace(go.Scatter(
            x=[s["range_km"]], y=[s["mach"]],
            mode="markers+text",
            marker=dict(size=14, color=COLORS[i % len(COLORS)]),
            text=[name.split("(")[0].strip()],
            textposition="top center",
            textfont=dict(size=9),
            name=name,
        ))
    fig.update_layout(**apply_theme(title="Mach vs Range — Hypersonic Systems"),
                      height=380, showlegend=False)
    fig.update_xaxes(title_text="Range (km)", gridcolor="#1E2235", zeroline=False)
    fig.update_yaxes(title_text="Peak Mach", gridcolor="#1E2235", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)
